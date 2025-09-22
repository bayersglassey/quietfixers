from functools import cache

from termgame.bitmap import Bitmap


class SquareTransitionTable:
    """Class which memoizes calculations converting between (x, y) coordinate
    space and uhhhh let's call them "polar Chebyshev" coordinates?.. anyway,
    it lets us do stuff like rotation of concentric squares of pixels ("rings")
    within a bitmap.

        >>> from termgame.bitmap import Bitmap

        >>> w = 6
        >>> table = SquareTransitionTable(w)

        >>> table.ring_lens
        [4, 12, 20]

        Here are the "ring indexes" for each pixel of a bitmap:
        >>> bmp = Bitmap(w, w)
        >>> for i, (ring_i, offset, ring_len) in enumerate(table.indexes_to_ring_coords):
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
        >>> for i, (ring_i, offset, ring_len) in enumerate(table.indexes_to_ring_coords):
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

        >>> print_indexes(table.hard_rotated_indexes[0])
          0  1  2  3  4  5
          6  7  8  9 10 11
         12 13 14 15 16 17
         18 19 20 21 22 23
         24 25 26 27 28 29
         30 31 32 33 34 35

        >>> print_indexes(table.hard_rotated_indexes[1])
         30 24 18 12  6  0
         31 25 19 13  7  1
         32 26 20 14  8  2
         33 27 21 15  9  3
         34 28 22 16 10  4
         35 29 23 17 11  5

        >>> print_indexes(table.get_slow_rotated_indexes(1))
          6  0  1  2  3  4
         12 13  7  8  9  5
         18 19 20 14 10 11
         24 25 21 15 16 17
         30 26 27 28 22 23
         31 32 33 34 35 29

        >>> print_indexes(table.get_slow_rotated_indexes(4))
         24 18 12  6  0  1
         30 25 19 13  7  2
         31 26 20 14  8  3
         32 27 21 15  9  4
         33 28 22 16 10  5
         34 35 29 23 17 11

        >>> table.get_slow_rotated_indexes(5) == table.hard_rotated_indexes[1]
        True

        >>> print_indexes(table.get_slow_rotated_indexes(6))
         31 30 24 18 12  6
         32 26 25 19 13  0
         33 27 21 20  7  1
         34 28 15 14  8  2
         35 22 16 10  9  3
         29 23 17 11  5  4

        >>> table.get_slow_rotated_indexes(-5) == table.hard_rotated_indexes[-1]
        True

        >>> print_indexes(table.get_slow_rotated_indexes(-6))
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
            self.get_hard_rotated_indexes(rot)
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

    def get_hard_rotated_indexes(self, rot: int) -> list[int]:
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
def get_square_transition_table(w: int) -> SquareTransitionTable:
    return SquareTransitionTable(w)


def hard_rotate(bitmap: Bitmap, rot: int):
    if bitmap.w != bitmap.h:
        raise Exception(f"Can't rotate bitmap unless w == h. Have: {(bitmap.w, bitmap.h)}")
    if not rot:
        return
    table = SquareTransitionTable(bitmap.w)
    bitmap.apply_index_mapping(table.get_hard_rotated_indexes(rot))


def slow_rotate(bitmap: Bitmap, rot: int):
    if bitmap.w != bitmap.h:
        raise Exception(f"Can't rotate bitmap unless w == h. Have: {(bitmap.w, bitmap.h)}")
    if not rot:
        return
    table = SquareTransitionTable(bitmap.w)
    bitmap.apply_index_mapping(table.get_slow_rotated_indexes(rot))
