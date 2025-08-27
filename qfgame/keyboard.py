import sys
from os import get_blocking, set_blocking
from termios import tcsetattr, TCSAFLUSH
from tty import setcbreak


class Keyboard:

    def __init__(self, file=None):
        self.file = sys.stdin if file is None else file
        self.fileno = self.file.fileno()
        self.blocking = get_blocking(self.fileno)
        self.tcattrs = None

    def getch(self) -> str:
        return self.file.read(1)

    def __enter__(self):
        self.tcattrs = setcbreak(self.file)
        set_blocking(self.fileno, False)
        return self

    def __exit__(self, *args):
        set_blocking(self.fileno, self.blocking)
        tcsetattr(self.file, TCSAFLUSH, self.tcattrs)
        self.tcattrs = None
