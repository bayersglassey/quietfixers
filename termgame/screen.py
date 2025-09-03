import sys

from contextlib import contextmanager

from .bitmap import Bitmap


class Screen(Bitmap):

    def __init__(self, w: int, h: int, file=None):
        Bitmap.__init__(self, w, h)
        self.file = sys.stdout if file is None else file
        self.flush = self.file.flush
        self.messages = []
        self.highlights = ()

    def set_highlight(self, *highlights):
        # Each highlight should be a pair (x, y)
        self.highlights = highlights

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
        # NOTE: make sure to use '\r\n', because we assume we're in a
        # Keyboard.raw() block!
        w = self.w
        colour_codes = self.colour_codes
        chars = self.chars
        highlights = {self.get_index(x, y) for x, y in self.highlights}
        parts = []
        for i in range(self.size):
            part = '\033['
            in_highlights = i in highlights
            if in_highlights:
                part += '7;'
            part += str(colour_codes[i])
            if in_highlights:
                part += ';0'
            part += 'm'
            part += chars[i] * 2
            if (i + 1) % w == 0:
                part += '\033[0m\r\n'
            parts.append(part)
        for message in self.messages:
            parts.append(message.replace('\n', '\r\n') + '\r\n')
        self.file.write(''.join(parts))
