from qfgame.screen import Screen
from qfgame.keyboard import Keyboard
from time import monotonic


class Game:

    def __init__(
            self,
            screen: Screen = None,
            keyboard: Keyboard = None,
            fps: float = 60,
            ):
        self.screen = screen or Screen(64, 32)
        self.keyboard = keyboard or Keyboard()
        self.fps = fps
        self.spf = 1 / fps

    def main(self):
        with self.keyboard:
            delay = 0
            self.screen.clear()
            while True:
                t0 = monotonic()
                self.screen.reset_cursor()
                key = self.keyboard.getch(delay)
                while key:
                    print(f"Got: {key}")
                    key = self.keyboard.getch(0)
                self.screen.print()
                t1 = monotonic()
                took = t1 - t0
                delay = self.spf - took
                if delay < 0:
                    delay = 0
