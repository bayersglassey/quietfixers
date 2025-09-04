import os
import cProfile
from argparse import ArgumentParser

from termgame.bitmap import Bitmap, get_colour_code
from termgame.screen import Screen
from termgame.keyboard import Keyboard, Key, KeyMod, parse_key
from termgame.game import Game

from .transitions import slow_rotate


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


def main(args):
    """A simple "paint" program"""
    filename = args.filename
    w = args.width
    screen = Screen(w, w)
    keyboard = Keyboard()
    game = Game(screen=screen, keyboard=keyboard)
    bitmap = Bitmap(w, w)
    tick = 0
    x = 0
    y = 0
    rot = 0
    target_rot = 0
    colour = 7
    autodraw = False

    for event in game.run():
        for key in event.keys:
            key, mod = parse_key(key)

            move_amount = 1
            if mod == KeyMod.shift:
                move_amount = 5
            elif mod == KeyMod.ctrl:
                move_amount = 10

            if key == Key.up:
                y1 = y - move_amount
                if y1 < 0: y1 = 0
                if autodraw:
                    for _y in range(y1, y + 1):
                        bitmap.set_pixel(x, _y, colour)
                y = y1
            elif key == Key.down:
                y1 = y + move_amount
                if y1 >= bitmap.h: y1 = bitmap.h - 1
                if autodraw:
                    for _y in range(y, y1 + 1):
                        bitmap.set_pixel(x, _y, colour)
                y = y1
            elif key == Key.left:
                x1 = x - move_amount
                if x1 < 0: x1 = 0
                if autodraw:
                    for _x in range(x1, x + 1):
                        bitmap.set_pixel(_x, y, colour)
                x = x1
            elif key == Key.right:
                x1 = x + move_amount
                if x1 >= bitmap.w: x1 = bitmap.w - 1
                if autodraw:
                    for _x in range(x, x1 + 1):
                        bitmap.set_pixel(_x, y, colour)
                x = x1
            elif key == 'q':
                return
            elif key == 's':
                bitmap.save(filename)
            elif key == 'l':
                new_bitmap = Bitmap.load(filename)
                if new_bitmap.w != w or new_bitmap.h != w:
                    game.get_text_input(
                        f"Can't load bitmap of dims {(new_bitmap.w, new_bitmap.h)}, need {(w, w)}. Press a key: ")
                else:
                    bitmap = new_bitmap
            elif key == 'f':
                bitmap.flood_fill(x, y, colour)
            elif key == 'F':
                filename = game.get_text_input(f"Change filename (was {filename}): ")
            elif key in KEYS_TO_COLOURS:
                colour = KEYS_TO_COLOURS[key]
            elif key == ' ':
                bitmap.set_pixel(x, y, colour)
            elif key == 'a':
                autodraw = not autodraw
            elif key == '[':
                target_rot -= 5
            elif key == '{':
                target_rot -= w - 1 # 90 degrees
            elif key == ']':
                target_rot += 5
            elif key == '}':
                target_rot += w - 1 # 90 degrees
            elif key == '`':
                # Reset all transformations
                rot = target_rot = 0

        if rot < target_rot:
            rot += 1
        elif rot > target_rot:
            rot -= 1

        bitmap_copy = bitmap.copy()
        slow_rotate(bitmap_copy, rot)
        bitmap_copy.blit(screen)

        screen.set_highlight((x, y))

        screen.print(f"Tick: {tick!r}")

        screen.print(
            ('[AUTO] ' if autodraw else '') +
            f"Selected colour: \033[{get_colour_code(colour)}m{colour:2}\033[0m")

        def to_ansi(c: int) -> str:
            return f'\033[{get_colour_code(c)}m█\033[0m'
        screen.print(''.join(to_ansi(c) for c in range(8)))
        screen.print(''.join(to_ansi(c + 8) for c in range(8)))

        tick += 1


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-f', '--filename',
        default=os.path.join('scratch', 'drawtest.dat'),
        help="Filename for saving & loading")
    parser.add_argument('-w', '--width', type=int, default=32)
    parser.add_argument('-P', '--profile', default=False, action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.profile:
        cProfile.run('main(args)')
    else:
        main(args)
