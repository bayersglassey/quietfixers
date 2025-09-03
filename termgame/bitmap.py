from typing import NamedTuple
from struct import Struct
from collections import deque
from functools import cache


SHADES = ' ░▒▓█'
UNFILLED = SHADES[0]
FILLED = SHADES[-1]


HEXDIGITS = '0123456789ABCDEF'


def get_colour(colour_code: int) -> int:
    # inverse of get_colour_code
    if colour_code < 30:
        # already a colour
        return colour_code
    return colour_code - 30 if colour_code < 90 else colour_code - 90 + 8


def get_colour_code(colour: int) -> int:
    # converts an int in range(16) to an ANSI colour code for use with '\033['
    # when colour is >=8, it's a "bright" colour
    if colour >= 30:
        # already a colour code
        return colour
    return colour + 30 if colour < 8 else colour - 8 + 90


BLACK = get_colour_code(0)
WHITE = get_colour_code(15)


class Rect(NamedTuple):
    """A rectangle within a Bitmap's pixels"""
    x: int
    y: int
    w: int
    h: int


class SquareRotation:
    """Class which memoizes calculations converting between (x, y) coordinate
    space and uhhhh let's call them "polar Chebyshev" coordinates?.. anyway,
    it lets us do rotation of concentric squares of pixels ("rings") within a
    bitmap.

        >>> w = 6
        >>> rot = SquareRotation(w)

        >>> rot.ring_lens
        [4, 12, 20]

        Here are the "ring indexes" for each pixel of a bitmap:
        >>> bmp = Bitmap(w, w)
        >>> for i, (ring_i, offset, ring_len) in enumerate(rot.indexes_to_ring_coords):
        ...     bmp.chars[i] = str(ring_i)
        >>> bmp.print()
        +------+
        |222222|
        |211112|
        |210012|
        |210012|
        |211112|
        |222222|
        +------+

        Here is an illustration of the "ring pixel offsets", i.e. the index of
        each pixel within a ring, counting clockwise from the top-left corner:
        >>> bmp = Bitmap(w, w)
        >>> for i, (ring_i, offset, ring_len) in enumerate(rot.indexes_to_ring_coords):
        ...     if ring_i % 2 == 0:
        ...         bmp.chars[i] = str(offset % 10)
        ...     else:
        ...         # Fill every second ring with '.' so it's easier to
        ...         # distinguish the digits
        ...         bmp.chars[i] = '.'
        >>> bmp.print()
        +------+
        |012345|
        |9....6|
        |8.01.7|
        |7.32.8|
        |6....9|
        |543210|
        +------+

        >>> def print_indexes(indexes):
        ...     for i, index in enumerate(indexes):
        ...         print(f'{index:3}', end='')
        ...         if (i + 1) % w == 0:
        ...             print()

        >>> print_indexes(rot.hard_rotated_indexes[0])
          0  1  2  3  4  5
          6  7  8  9 10 11
         12 13 14 15 16 17
         18 19 20 21 22 23
         24 25 26 27 28 29
         30 31 32 33 34 35

        >>> print_indexes(rot.hard_rotated_indexes[1])
         30 24 18 12  6  0
         31 25 19 13  7  1
         32 26 20 14  8  2
         33 27 21 15  9  3
         34 28 22 16 10  4
         35 29 23 17 11  5

        >>> print_indexes(rot.get_slow_rotated_indexes(1))
          6  0  1  2  3  4
         12 13  7  8  9  5
         18 19 20 14 10 11
         24 25 21 15 16 17
         30 26 27 28 22 23
         31 32 33 34 35 29

        >>> print_indexes(rot.get_slow_rotated_indexes(4))
         24 18 12  6  0  1
         30 25 19 13  7  2
         31 26 20 14  8  3
         32 27 21 15  9  4
         33 28 22 16 10  5
         34 35 29 23 17 11

        >>> rot.get_slow_rotated_indexes(5) == rot.hard_rotated_indexes[1]
        True

        >>> print_indexes(rot.get_slow_rotated_indexes(6))
         31 30 24 18 12  6
         32 26 25 19 13  0
         33 27 21 20  7  1
         34 28 15 14  8  2
         35 22 16 10  9  3
         29 23 17 11  5  4

        >>> rot.get_slow_rotated_indexes(-5) == rot.hard_rotated_indexes[-1]
        True

        >>> print_indexes(rot.get_slow_rotated_indexes(-6))
         11 17 23 29 35 34
          5 16 22 28 27 33
          4 10 21 20 26 32
          3  9 15 14 25 31
          2  8  7 13 19 30
          1  0  6 12 18 24

    """

    def __init__(self, w: int):
        if w % 2 != 0:
            raise ValueError(f"uneven width: {w}")
        half_w = w // 2

        self.w = w
        self.size = w * w
        self.n_rings = half_w
        self.ring_lens = [8 * ring_i + 4
            for ring_i in range(self.n_rings)]

        self.hard_rotated_indexes = [
            self._get_hard_rotated_indexes(rot)
            for rot in range(4)]

        # Maps bitmap pixel indexes to tuples (ring_i, offset, ring_len),
        # where:
        #   * ring_i is the index of a ring
        #   * offset is the offset of a pixel within that ring, i.e. an
        #     integer in range(ring_lens[ring_i])
        #   * ring_len is the length of the ring, i.e. ring_lens[ring_i]
        # The pixel offsets go clockwise from the top-left corner of ring,
        # like this (in this example, ring_i = 1):
        #
        #   0123
        #   B  4
        #   A  5
        #   9876
        #
        self.indexes_to_ring_coords = [None] * self.size
        for ring_i, ring_len in enumerate(self.ring_lens):

            # Here are the points a, b, c, d for ring_i in range(3):
            #   a....b
            #   .a..b.
            #   ..ab..
            #   ..dc..
            #   .d..c.
            #   d....c
            a = (half_w - ring_i - 1) * (w + 1)
            b = (half_w - ring_i - 1) * w + (half_w + ring_i)
            c = (half_w + ring_i) * (w + 1)
            d = (half_w + ring_i) * w + (half_w - ring_i - 1)

            # Number of pixels in one of the 4 sides of the ring
            ring_sidelen = ring_i * 2 + 1
            for j in range(ring_sidelen):
                self.indexes_to_ring_coords[a + j] = \
                    (ring_i, j, ring_len)
                self.indexes_to_ring_coords[b + j * w] = \
                    (ring_i, j + ring_sidelen, ring_len)
                self.indexes_to_ring_coords[c - j] = \
                    (ring_i, j + ring_sidelen * 2, ring_len)
                self.indexes_to_ring_coords[d - j * w] = \
                    (ring_i, j + ring_sidelen * 3, ring_len)

        # Maps (ring_i, offset) to bitmap pixel indexes
        self.ring_coords_to_indexes = {(ring_i, offset): i
            for i, (ring_i, offset, ring_len) in enumerate(
                self.indexes_to_ring_coords)}

        self.ring_coords_to_indexes_hard_rotated = [
            {coords: indexes[index]
                for coords, index in self.ring_coords_to_indexes.items()}
            for indexes in self.hard_rotated_indexes]

    def _get_hard_rotated_indexes(self, rot: int) -> list[int]:
        # Hard rotation: by 90 degrees at a time (clockwise)
        rot = rot % 4
        if not rot:
            return list(range(self.size))

        w = self.w
        indexes = []
        for y in range(w):
            for x in range(w):
                x1 = x
                y1 = y
                for _ in range(rot):
                    _x1 = x1
                    x1 = y1
                    y1 = w - 1 - _x1
                indexes.append(y1 * w + x1)
        return indexes

    def get_slow_rotated_indexes(self, r: int) -> list[int]:
        # Slow rotation: by 1 pixel at a time (clockwise)
        ring_mod = self.w - 1
        hard_index = (abs(r) // ring_mod) % 4
        if r < 0:
            ring_coords_to_indexes = self.ring_coords_to_indexes_hard_rotated[-hard_index]
            r = -(-r % ring_mod)
            return [
                ring_coords_to_indexes[
                    (ring_i, (offset - max(r, -ring_len // 4)) % ring_len)
                ] for (ring_i, offset, ring_len) in self.indexes_to_ring_coords]
        else:
            ring_coords_to_indexes = self.ring_coords_to_indexes_hard_rotated[hard_index]
            r = r % ring_mod
            return [
                ring_coords_to_indexes[
                    (ring_i, (offset - min(r, ring_len // 4)) % ring_len)
                ] for (ring_i, offset, ring_len) in self.indexes_to_ring_coords]


@cache
def get_square_rotation(w: int) -> SquareRotation:
    return SquareRotation(w)


BITMAP_HEADER_STRUCT = Struct('!LL') # w, h
BITMAP_PIXEL_STRUCT = Struct('!BL') # colour, char


class Bitmap:

    def __init__(
            self,
            w: int,
            h: int,
            colour_code: int = BLACK,
            char: str = FILLED,
            *,
            filename: str = None,
            colour_codes: list[int] = None,
            chars: list[str] = None,
            ):
        self.w = w
        self.h = h
        self.size = size = w * h
        self.filename = filename

        if colour_codes is None:
            colour_codes = [colour_code] * size
        if chars is None:
            chars = [char] * size
        self.colour_codes = colour_codes
        self.chars = chars

        self.get_index = lambda x, y: w * y + x

    def copy(self) -> 'Bitmap':
        return Bitmap(self.w, self.h,
            filename=self.filename,
            colour_codes=self.colour_codes.copy(),
            chars=self.chars.copy(),
        )

    def pack(self) -> bytearray:
        r"""Produces a portable binary representation of a bitmap

            >>> self = Bitmap(3, 2)
            >>> self.set_pixel(0, 0, WHITE, 'A')
            >>> self.set_pixel(1, 0, WHITE, 'B')
            >>> self.set_pixel(2, 1, WHITE, 'C')
            >>> self.print()
            +---+
            |AB█|
            |██C|
            +---+

            >>> packed = self.pack()
            >>> packed[:10]
            bytearray(b'\x00\x00\x00\x03\x00\x00\x00\x02\x0f\x00')
            >>> Bitmap.unpack(packed).print()
            +---+
            |AB█|
            |██C|
            +---+

        """
        header_size = BITMAP_HEADER_STRUCT.size
        pixel_size = BITMAP_PIXEL_STRUCT.size
        buffer_size = header_size + pixel_size * self.size
        buffer = bytearray(buffer_size)
        BITMAP_HEADER_STRUCT.pack_into(buffer, 0, self.w, self.h)
        for i, (colour_code, char) in enumerate(zip(self.colour_codes, self.chars)):
            colour = get_colour(colour_code)
            offset = header_size + pixel_size * i
            BITMAP_PIXEL_STRUCT.pack_into(buffer, offset, colour, ord(char))
        return buffer

    @staticmethod
    def unpack(buffer, **kwargs) -> 'Bitmap':
        """Inverse of pack()"""
        header_size = BITMAP_HEADER_STRUCT.size
        pixel_size = BITMAP_PIXEL_STRUCT.size
        w, h = BITMAP_HEADER_STRUCT.unpack_from(buffer, 0)
        size = w * h
        colour_codes = [None] * size
        chars = [None] * size
        for i in range(size):
            offset = header_size + pixel_size * i
            colour, char = BITMAP_PIXEL_STRUCT.unpack_from(buffer, offset)
            colour_codes[i] = get_colour_code(colour)
            chars[i] = chr(char)
        return Bitmap(w, h, colour_codes=colour_codes, chars=chars, **kwargs)

    def save(self, file):
        if isinstance(file, str):
            file = open(file, 'wb')
        buffer = self.pack()
        file.write(buffer)

    @staticmethod
    def load(file, **kwargs) -> 'Bitmap':
        if isinstance(file, str):
            kwargs['filename'] = file
            file = open(file, 'rb')
        return Bitmap.unpack(file.read(), **kwargs)

    def contains_point(self, x: int, y: int) -> bool:
        return (
            x >= 0 and
            x < self.w and
            y >= 0 and
            y < self.h
        )

    def contains_rect(self, rect: Rect) -> bool:
        x, y, w, h = rect
        return (
            x >= 0 and
            x + w <= self.w and
            y >= 0 and
            y + h <= self.h
        )

    def clip(self, rect: Rect) -> Rect:
        self_w = self.w
        self_h = self.h
        x, y, w, h = rect

        if x < 0:
            w += x
            if w < 0:
                w = 0
            x = 0
        elif x >= self_w:
            x = self_w
            w = 0
        elif x + w > self_w:
            w = self_w - x

        if y < 0:
            h += y
            if h < 0:
                h = 0
            y = 0
        elif y >= self_h:
            y = self_h
            h = 0
        elif y + h > self_h:
            h = self_h - y

        return Rect(x, y, w, h)

    def get_pixel(self, x: int, y: int) -> int:
        i = self.get_index(x, y)
        colour = get_colour(self.colour_codes[i])
        char = self.chars[i]
        return colour, char

    def set_pixel(self, x: int, y: int, colour: int, char: str = FILLED):
        i = self.get_index(x, y)
        colour_code = get_colour_code(colour)
        self.colour_codes[i] = colour_code
        self.chars[i] = char

    def flood_fill(self, x: int, y: int, colour: int, char: str = FILLED):
        """Flood fill algorithm.
        Only looks at pixel colour when determining whether to "spread".

            >>> self = Bitmap(3, 3)
            >>> self.print(use_colours=True)
            +---+
            |000|
            |000|
            |000|
            +---+
            >>> self.flood_fill(1, 1, 1)
            >>> self.print(use_colours=True)
            +---+
            |111|
            |111|
            |111|
            +---+

            >>> self = Bitmap(3, 3)
            >>> self.set_pixel(1, 0, 1)
            >>> self.set_pixel(0, 1, 1)
            >>> self.set_pixel(2, 1, 1)
            >>> self.set_pixel(1, 2, 1)
            >>> self.print(use_colours=True)
            +---+
            |010|
            |101|
            |010|
            +---+
            >>> self.flood_fill(1, 1, 1)
            >>> self.print(use_colours=True)
            +---+
            |010|
            |111|
            |010|
            +---+

            >>> self = Bitmap(6, 3)
            >>> self.set_pixel(1, 0, 9)
            >>> self.set_pixel(2, 1, 9)
            >>> self.set_pixel(3, 2, 9)
            >>> self.print(use_colours=True)
            +------+
            |090000|
            |009000|
            |000900|
            +------+
            >>> self.flood_fill(2, 1, 8)
            >>> self.print(use_colours=True)
            +------+
            |090000|
            |008000|
            |000900|
            +------+
            >>> self.flood_fill(1, 1, 1)
            >>> self.print(use_colours=True)
            +------+
            |190000|
            |118000|
            |111900|
            +------+
            >>> self.flood_fill(3, 1, 2)
            >>> self.print(use_colours=True)
            +------+
            |192222|
            |118222|
            |111922|
            +------+

        """
        colour_code = get_colour_code(colour)
        i = self.get_index(x, y)
        replace_colour_code = self.colour_codes[i]
        if replace_colour_code == colour_code:
            return
        points = deque([(x, y)])
        while points:
            x, y = points.popleft()
            self.set_pixel(x, y, colour_code, char)
            for p1 in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ):
                x1, y1 = p1
                if not self.contains_point(x1, y1):
                    continue
                i1 = self.get_index(x1, y1)
                if self.colour_codes[i1] != replace_colour_code:
                    continue
                if p1 in points:
                    continue
                points.append(p1)

    def fill(self, colour: int, char: str = FILLED):
        colour_code = get_colour_code(colour)
        self.colour_codes = [colour_code] * self.size
        self.chars = [char] * self.size

    def rotate(self, rot: int):
        if self.w != self.h:
            raise Exception(f"Can't rotate bitmap unless w == h. Have: {(self.w, self.h)}")
        if not rot:
            return
        rotation_table = get_square_rotation(self.w)
        rotated_indexes = rotation_table.get_slow_rotated_indexes(rot)
        self.colour_codes = list(map(self.colour_codes.__getitem__,
            rotated_indexes))
        self.chars = list(map(self.chars.__getitem__, rotated_indexes))

    def print(self, *, border=True, use_colours=False, doubled=False):
        """For debugging purposes, e.g. doctest"""
        lines = []
        if border:
            lines.append('+' + '-' * self.w + '+')
        for y in range(self.h):
            i = y * self.w
            if use_colours:
                colour_codes = self.colour_codes[i: i + self.w]
                _colours = [get_colour(c) for c in colour_codes]
                line = ''.join(HEXDIGITS[c] for c in _colours)
            else:
                line = ''.join(self.chars[i: i + self.w])
            if doubled:
                line = ''.join(c * 2 for c in line)
            if border:
                line = f'|{line}|'
            lines.append(line)
        if border:
            lines.append('+' + '-' * self.w + '+')
        print('\n'.join(lines))

    def blit(
            self,
            other: 'Bitmap',
            dst_x: int = 0,
            dst_y: int = 0,
            src: Rect = None,
            *,
            transparent_char: str = None,
            ):
        """

            Bitmap to be blitted onto another:
            >>> self = Bitmap(2, 2)
            >>> self.set_pixel(0, 0, WHITE, 'A')
            >>> self.set_pixel(1, 0, WHITE, 'B')
            >>> self.set_pixel(0, 1, WHITE, 'C')
            >>> self.set_pixel(1, 1, WHITE, 'D')
            >>> self.print()
            +--+
            |AB|
            |CD|
            +--+

            Bitmap onto which we will blit self:
            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> other.print()
            +---+
            |   |
            |   |
            |   |
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, 0, 0)
            >>> other.print()
            +---+
            |AB |
            |CD |
            |   |
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, 1, 1)
            >>> other.print()
            +---+
            |   |
            | AB|
            | CD|
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, -1, -1)
            >>> other.print()
            +---+
            |D  |
            |   |
            |   |
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, 2, 2)
            >>> other.print()
            +---+
            |   |
            |   |
            |  A|
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, -2, -2)
            >>> other.print()
            +---+
            |   |
            |   |
            |   |
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, 3, 3)
            >>> other.print()
            +---+
            |   |
            |   |
            |   |
            +---+

            >>> other = Bitmap(3, 3, char=UNFILLED)
            >>> self.blit(other, 1, 1, Rect(1, 1, 1, 1))
            >>> other.print()
            +---+
            |   |
            | D |
            |   |
            +---+

            You can optionally supply a transparent char:
            >>> other = Bitmap(3, 3, char='.')
            >>> self.blit(other, transparent_char='C')
            >>> other.print()
            +---+
            |AB.|
            |.D.|
            |...|
            +---+

        """
        self_w = self.w
        self_h = self.h
        other_w = other.w
        other_h = other.h

        # Figure out source rectangle
        if src is None:
            src_x = 0
            src_y = 0
            w = self_w
            h = self_h
        elif not self.contains_rect(src):
            raise ValueError(f"{src} not contained in bitmap with dims {(self_w, self_h)}")
        else:
            src_x, src_y, w, h = src

        if not w or not h:
            # Nothing to do
            return

        # Figure out destination rectangle
        dst_x_preclip = dst_x
        dst_y_preclip = dst_y
        dst_x, dst_y, w, h = other.clip((dst_x, dst_y, w, h))
        if not w or not h:
            # Nothing to do
            return

        # If clipping has moved the destination point, move the source point
        # accordingly
        if dst_x > dst_x_preclip:
            src_x += dst_x - dst_x_preclip
        if dst_y > dst_y_preclip:
            src_y += dst_y - dst_y_preclip

        # Blit!
        src_i = src_y * self_w + src_x
        dst_i = dst_y * other_w + dst_x
        for y in range(h):
            if transparent_char:
                for i in range(w):
                    src_j = src_i + i
                    dst_j = dst_i + i
                    char = self.chars[src_j]
                    if char != transparent_char:
                        other.colour_codes[dst_j] = self.colour_codes[src_j]
                        other.chars[dst_j] = char
            else:
                src_i2 = src_i + w
                dst_i2 = dst_i + w
                other.colour_codes[dst_i: dst_i2] = self.colour_codes[src_i: src_i2]
                other.chars[dst_i: dst_i2] = self.chars[src_i: src_i2]
            src_i += self_w
            dst_i += other_w
