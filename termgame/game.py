from typing import NamedTuple
from time import monotonic, sleep

from .screen import Screen
from .keyboard import Keyboard


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
            fps: float = 30,
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
