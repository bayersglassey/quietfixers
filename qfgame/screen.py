import sys

from contextlib import contextmanager


SHADES = ' ░▒▓█'
UNFILLED = SHADES[0]
FILLED = SHADES[-1]


def get_colour(colour_code: int) -> int:
    # inverse of get_colour_code
    return colour_code - 30 if colour_code < 90 else colour_code - 90


def get_colour_code(colour: int) -> int:
    # converts an int in range(16) to an ANSI colour code for use with '\033['
    # when colour is >=8, it's a "bright" colour
    return colour + 30 if colour < 8 else colour + 90


BLACK = get_colour_code(0)
WHITE = get_colour_code(15)


class Screen:

    def __init__(self, w: int, h: int, file=None):
        self.file = sys.stdout if file is None else file
        self.flush = self.file.flush
        self.w = w
        self.h = h
        self.size = w * h
        self.colour_codes = [BLACK] * self.size
        self.chars = [FILLED] * self.size
        self.get_index = lambda x, y: w * y + x

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

    def fill(self, colour: int, char: str = FILLED):
        colour_code = get_colour_code(colour)
        self.colour_codes = [colour_code] * self.size
        self.chars = [char] * self.size

    def clear(self):
        self.file.write('\033[2J')

    def reset_cursor(self):
        self.file.write('\033[H')

    @contextmanager
    def hide_cursor(self):
        self.file.write('\033[?25l')
        try:
            yield
        finally:
            self.file.write('\033[?25h')

    def display(self):
        w = self.w
        colour_codes = self.colour_codes
        chars = self.chars
        parts = []
        add_part = parts.append
        for i in range(self.size):
            add_part('\033[')
            add_part(str(colour_codes[i]))
            add_part('m')
            add_part(chars[i])
            if (i + 1) % w == 0:
                add_part('\033[0m\r\n')
        self.file.write(''.join(parts))
