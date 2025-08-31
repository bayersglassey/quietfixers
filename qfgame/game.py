import os

from typing import NamedTuple
from time import monotonic, sleep

from .bitmap import Bitmap, get_colour_code
from .screen import Screen
from .keyboard import Keyboard, Key, KeyMod, parse_key


class Event(NamedTuple):
    # It's up to you to iterate over this, and call parse_key on its
    # members if you want to extract key modifiers
    keys: list[str]


class Game:

    def __init__(
            self,
            *,
            screen: Screen = None,
            keyboard: Keyboard = None,
            fps: float = 15,
            ):
        self.screen = screen or Screen(64, 32)
        self.keyboard = keyboard or Keyboard()
        self.fps = fps
        self.spf = 1 / fps

    def get_text_input(self, prompt: str) -> str:
        with self.keyboard.cooked():
            text = input(prompt)
        # WARNING: "clearing" the screen ends up meaning Gnome Terminal
        # scrolls down past everything which had been drawn on it, which
        # I think maybe we want to avoid... otherwise, after quitting the
        # game, if you scroll up, you see every frame it ever rendered
        # before terminal was cleared, if that makes sense.
        #self.screen.clear()
        return text

    def run(self):
        screen = self.screen
        keyboard = self.keyboard

        with screen.hide_cursor(), keyboard.raw():
            screen.clear()
            while True:
                t0 = monotonic()

                # Handle I/O
                with keyboard.no_block():
                    keys = keyboard.get_keys()
                yield Event(keys=keys)

                # Render
                screen.reset_cursor()
                screen.display()
                screen.flush()
                screen.clear_messages()

                # Delay
                t1 = monotonic()
                took = t1 - t0
                delay = self.spf - took
                if delay > 0:
                    sleep(delay)


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


def drawtest(filename=os.path.join('scratch', 'drawtest.dat')):
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
                y -= move_amount
                if y < 0: y = 0
            elif key == Key.down:
                y += move_amount
                if y >= screen.h: y = screen.h - 1
            elif key == Key.left:
                x -= move_amount
                if x < 0: x = 0
            elif key == Key.right:
                x += move_amount
                if x >= screen.w: x = screen.w - 1
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
            elif key == 'P':
                autodraw = not autodraw
        if autodraw:
            screen.set_pixel(x, y, colour)
        screen.set_highlight((x, y))
        screen.print(f"Tick: {tick!r}")
        def to_ansi(c: int) -> str:
            return f'\033[{get_colour_code(c)}m█\033[0m'
        screen.print(f"Selected colour: \033[{get_colour_code(colour)}m{colour:2}\033[0m")
        screen.print(''.join(to_ansi(c) for c in range(8)))
        screen.print(''.join(to_ansi(c + 8) for c in range(8)))
        tick += 1
