from typing import NamedTuple
from qfgame.screen import Screen
from qfgame.keyboard import Keyboard
from time import monotonic, sleep


class Event(NamedTuple):
    keys: str


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
                    keys = keyboard.gets()
                yield Event(keys=keys)

                # Render
                screen.reset_cursor()
                screen.display()
                screen.flush()

                # Delay
                t1 = monotonic()
                took = t1 - t0
                delay = self.spf - took
                if delay > 0:
                    sleep(delay)


def test_logic(game):
    screen = game.screen
    tick = 0
    x = 0
    y = 0

    for event in game.run():
        for key in event.keys:
            if key == 'w':
                if y > 0: y -= 1
            elif key == 's':
                if y < screen.h - 1: y += 1
            elif key == 'a':
                if x > 0: x -= 1
            elif key == 'd':
                if x < screen.w - 1: x += 1
            elif key == 'q':
                return
        screen.set_pixel(x, y, 7)
        print(f"Tick: {tick!r}")
        tick += 1
