import re
import sys

from enum import StrEnum
from os import get_blocking, set_blocking
from termios import tcsetattr, TCSAFLUSH
from tty import setraw, setcbreak
from contextlib import contextmanager


class Key(StrEnum):
    up = 'up'
    down = 'down'
    left = 'left'
    right = 'right'


# Detects e.g. arrow keys
KEY_REGEX = re.compile(r'\x1b\[.|.')
KEY_MAP = {
    '\x1b[A': Key.up,
    '\x1b[B': Key.down,
    '\x1b[D': Key.left,
    '\x1b[C': Key.right,
}


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

    def get_keys(self) -> list[str]:
        keys = []
        for key in KEY_REGEX.findall(self.gets()):
            keys.append(KEY_MAP.get(key, key))
        return keys

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
