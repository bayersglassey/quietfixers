from qfgame.screen import Screen
from qfgame.keyboard import Keyboard
from time import monotonic, sleep


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
            self.screen.clear()
            while True:
                t0 = monotonic()
                self.screen.reset_cursor()
                self.screen.print()
                while key := self.keyboard.getch():
                    print(f"Got: {key}")
                t1 = monotonic()
                took = t1 - t0
                delay = self.spf - took
                if delay > 0:
                    sleep(delay)
