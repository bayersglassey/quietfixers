

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


class Bitmap:

    def __init__(self, w: int, h: int, colour_code: int = BLACK, char: str = FILLED):
        self.w = w
        self.h = h
        self.size = w * h
        self.colour_codes = [colour_code] * self.size
        self.chars = [char] * self.size
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
