import os

from typing import NamedTuple
from time import monotonic, sleep

from .bitmap import Bitmap
from .screen import Screen
from .keyboard import Keyboard, Key


class Event(NamedTuple):
    keys: list[str]


class Game:

    def __init__(
            self,
            *,
            screen: Screen = None,
            keyboard: Keyboard = None,
            fps: float = 30,
            ):
        self.screen = screen or Screen(64, 32)
        self.keyboard = keyboard or Keyboard()
        self.fps = fps
        self.spf = 1 / fps

    def run(self):
        screen = self.screen
        keyboard = self.keyboard

        screen.clear()
        with screen.hide_cursor(), keyboard.raw():
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


def drawtest(filename=os.path.join('scratch', 'drawtest.dat')):
    """A simple "paint" program"""
    screen = Screen(64, 32)
    game = Game(screen=screen)
    tick = 0
    x = 0
    y = 0

    for event in game.run():
        for key in event.keys:
            if key == Key.up:
                if y > 0: y -= 1
            elif key == Key.down:
                if y < screen.h - 1: y += 1
            elif key == Key.left:
                if x > 0: x -= 1
            elif key == Key.right:
                if x < screen.w - 1: x += 1
            elif key == 'q':
                return
            elif key == 's':
                screen.save(filename)
            elif key == 'l':
                Bitmap.load(filename).blit(screen)
        screen.set_pixel(x, y, 7)
        screen.print(f"Tick: {tick!r}")
        tick += 1
