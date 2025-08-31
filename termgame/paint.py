import os

from .bitmap import Bitmap, get_colour_code
from .screen import Screen
from .keyboard import Keyboard, Key, KeyMod, parse_key
from .game import Game


KEYS_TO_COLOURS = {
    **{str(i): i for i in range(8)},
    ')': 8 + 0,
    '!': 8 + 1,
    '@': 8 + 2,
    '#': 8 + 3,
    '$': 8 + 4,
    '%': 8 + 5,
    '^': 8 + 6,
    '&': 8 + 7,
}


def main(filename=os.path.join('scratch', 'drawtest.dat')):
    """A simple "paint" program"""
    screen = Screen(64, 32)
    keyboard = Keyboard()
    game = Game(screen=screen, keyboard=keyboard)
    tick = 0
    x = 0
    y = 0
    colour = 7
    autodraw = False

    for event in game.run():
        for key in event.keys:
            key, mod = parse_key(key)

            move_amount = 1
            if mod == KeyMod.shift:
                move_amount = 5
            elif mod == KeyMod.shift:
                move_amount = 10

            if key == Key.up:
                y1 = y - move_amount
                if y1 < 0: y1 = 0
                if autodraw:
                    for _y in range(y1, y + 1):
                        screen.set_pixel(x, _y, colour)
                y = y1
            elif key == Key.down:
                y1 = y + move_amount
                if y1 >= screen.h: y1 = screen.h - 1
                if autodraw:
                    for _y in range(y, y1 + 1):
                        screen.set_pixel(x, _y, colour)
                y = y1
            elif key == Key.left:
                x1 = x - move_amount
                if x1 < 0: x1 = 0
                if autodraw:
                    for _x in range(x1, x + 1):
                        screen.set_pixel(_x, y, colour)
                x = x1
            elif key == Key.right:
                x1 = x + move_amount
                if x1 >= screen.w: x1 = screen.w - 1
                if autodraw:
                    for _x in range(x, x1 + 1):
                        screen.set_pixel(_x, y, colour)
                x = x1
            elif key == 'q':
                return
            elif key == 's':
                screen.save(filename)
            elif key == 'l':
                Bitmap.load(filename).blit(screen)
            elif key == 'f':
                screen.flood_fill(x, y, colour)
            elif key == 'F':
                filename = game.get_text_input(f"Change filename (was {filename}): ")
            elif key in KEYS_TO_COLOURS:
                colour = KEYS_TO_COLOURS[key]
            elif key == ' ':
                screen.set_pixel(x, y, colour)
            elif key == 'a':
                autodraw = not autodraw
        screen.set_highlight((x, y))
        screen.print(f"Tick: {tick!r}")
        def to_ansi(c: int) -> str:
            return f'\033[{get_colour_code(c)}m█\033[0m'
        screen.print(
            ('[AUTO] ' if autodraw else '') +
            f"Selected colour: \033[{get_colour_code(colour)}m{colour:2}\033[0m")
        screen.print(''.join(to_ansi(c) for c in range(8)))
        screen.print(''.join(to_ansi(c + 8) for c in range(8)))
        tick += 1


if __name__ == '__main__':
    main()
