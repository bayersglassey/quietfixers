import sys


SHADES = ' ░▒▓█'
UNFILLED = SHADES[0]
FILLED = SHADES[-1]


def get_colour_code(colour: int) -> int:
    # converts an int in range(16) to an ANSI colour code for use with '\033['
    # when colour is >=8, it's a "bright" colour
    return 30 + colour if colour < 8 else colour + 90


BLACK = get_colour_code(0)
WHITE = get_colour_code(15)


class Screen:

    def __init__(self, w: int, h: int, file=None):
        self.file = sys.stdout if file is None else file
        self.w = w
        self.h = h
        self.size = w * h
        self.colour_codes = [BLACK] * self.size
        self.chars = [FILLED] * self.size
        get_index = lambda x, y: w * y + x

    def fill(self, colour: int, char: str = FILLED):
        colour_code = get_colour_code(colour)
        self.colour_codes = [colour_code] * self.size
        self.chars = [char] * self.size

    def clear(self):
        self.file.write('\033[2J')

    def reset_cursor(self):
        self.file.write('\033[H')

    def print(self):
        write = self.file.write
        w = self.w
        colour_codes = self.colour_codes
        chars = self.chars
        for i in range(self.size):
            write('\033[')
            write(str(colour_codes[i]))
            write('m')
            write(chars[i])
            if (i + 1) % w == 0:
                write('\033[0m\n')
