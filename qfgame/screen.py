import sys

from contextlib import contextmanager

from .bitmap import Bitmap


class Screen(Bitmap):

    def __init__(self, w: int, h: int, file=None):
        Bitmap.__init__(self, w, h)
        self.file = sys.stdout if file is None else file
        self.flush = self.file.flush
        self.messages = []

    def print(self, message: str):
        self.messages.append(message)

    def clear_messages(self):
        self.messages.clear()

    def clear(self):
        self.file.write('\033[2J')

    def reset_cursor(self):
        self.file.write('\033[H')

    @contextmanager
    def hide_cursor(self):
        self.file.write('\033[?25l')
        try:
            yield
        finally:
            self.file.write('\033[?25h')

    def display(self):
        w = self.w
        colour_codes = self.colour_codes
        chars = self.chars
        parts = []
        add_part = parts.append
        for i in range(self.size):
            add_part('\033[')
            add_part(str(colour_codes[i]))
            add_part('m')
            add_part(chars[i])
            if (i + 1) % w == 0:
                add_part('\033[0m\r\n')
        for message in self.messages:
            add_part(message.replace('\n', '\r\n') + '\r\n')
        self.file.write(''.join(parts))
