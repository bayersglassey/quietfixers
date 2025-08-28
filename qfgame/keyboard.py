import sys

from os import get_blocking, set_blocking
from termios import tcsetattr, TCSAFLUSH
from tty import setraw, setcbreak
from contextlib import contextmanager


class Keyboard:

    def __init__(self, file=None):
        self.file = sys.stdin if file is None else file
        self.fileno = self.file.fileno()

    def getch(self) -> str:
        return self.file.read(1)

    def gets(self) -> str:
        s = ''
        while c := self.file.read(1):
            s += c
        return s

    @contextmanager
    def raw(self):
        tcattrs = setraw(self.file)
        try:
            yield
        finally:
            tcsetattr(self.file, TCSAFLUSH, tcattrs)

    @contextmanager
    def cbreak(self):
        tcattrs = setcbreak(self.file)
        try:
            yield
        finally:
            tcsetattr(self.file, TCSAFLUSH, tcattrs)

    @contextmanager
    def no_block(self):
        was_blocking = get_blocking(self.fileno)
        if not was_blocking:
            return
        set_blocking(self.fileno, False)
        try:
            yield
        finally:
            set_blocking(self.fileno, True)
