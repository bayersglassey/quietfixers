from typing import NamedTuple
from struct import Struct
from collections import deque


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

    def apply_index_mapping(self, indexes: list[int]):
        self.colour_codes = list(map(self.colour_codes.__getitem__, indexes))
        self.chars = list(map(self.chars.__getitem__, indexes))
