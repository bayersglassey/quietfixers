import re
import sys

from enum import StrEnum
from os import get_blocking, set_blocking
from termios import tcgetattr, tcsetattr, TCSAFLUSH
from tty import setraw, setcbreak
from contextlib import contextmanager


class Key(StrEnum):
    up = 'up'
    down = 'down'
    left = 'left'
    right = 'right'
    shift_up = 'shift_up'
    shift_down = 'shift_down'
    shift_left = 'shift_left'
    shift_right = 'shift_right'
    ctrl_up = 'ctrl_up'
    ctrl_down = 'ctrl_down'
    ctrl_left = 'ctrl_left'
    ctrl_right = 'ctrl_right'


class KeyMod(StrEnum):
    none = 'none'
    shift = 'shift'
    ctrl = 'ctrl'


def parse_key(key: str) -> tuple[str, KeyMod]:
    """

        >>> parse_key('a')
        ('a', <KeyMod.none: 'none'>)

        >>> parse_key('A')
        ('a', <KeyMod.shift: 'shift'>)

        >>> parse_key(Key.up)
        (<Key.up: 'up'>, <KeyMod.none: 'none'>)

        >>> parse_key(Key.shift_up)
        (<Key.up: 'up'>, <KeyMod.shift: 'shift'>)

        >>> parse_key(Key.ctrl_up)
        (<Key.up: 'up'>, <KeyMod.ctrl: 'ctrl'>)

    """
    if len(key) == 1 and key.isupper():
        return key.lower(), KeyMod.shift
    if key in Key:
        if 'shift_' in key:
            return Key(key[len('shift_'):]), KeyMod.shift
        elif 'ctrl_' in key:
            return Key(key[len('ctrl_'):]), KeyMod.ctrl
    return key, KeyMod.none


# Detects e.g. arrow keys
KEY_REGEX = re.compile(r'\x1b\[[0-9;]*.|.')
KEY_MAP = {
    '\x1b[A': Key.up,
    '\x1b[B': Key.down,
    '\x1b[D': Key.left,
    '\x1b[C': Key.right,
    '\x1b[1;2A': Key.shift_up,
    '\x1b[1;2B': Key.shift_down,
    '\x1b[1;2D': Key.shift_left,
    '\x1b[1;2C': Key.shift_right,
    '\x1b[1;5A': Key.ctrl_up,
    '\x1b[1;5B': Key.ctrl_down,
    '\x1b[1;5D': Key.ctrl_left,
    '\x1b[1;5C': Key.ctrl_right,
}


class Keyboard:

    def __init__(self, file=None):
        self.file = sys.stdin if file is None else file
        self.fileno = self.file.fileno()
        self.original_tcattrs = None

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
        if self.original_tcattrs is not None:
            raise Exception("Can't nest cbreak, raw, etc")
        self.original_tcattrs = setraw(self.file)
        try:
            yield
        finally:
            tcsetattr(self.file, TCSAFLUSH, self.original_tcattrs)
            self.original_tcattrs = None

    @contextmanager
    def cbreak(self):
        if self.original_tcattrs is not None:
            raise Exception("Can't nest cbreak, raw, etc")
        self.original_tcattrs = setcbreak(self.file)
        try:
            yield
        finally:
            tcsetattr(self.file, TCSAFLUSH, self.original_tcattrs)
            self.original_tcattrs = None

    @contextmanager
    def cooked(self):
        """Temporarily breaks out of raw or cbreak"""
        if self.original_tcattrs is None:
            return
        noncooked_tcattrs = tcgetattr(self.file)
        tcsetattr(self.file, TCSAFLUSH, self.original_tcattrs)
        try:
            yield
        finally:
            tcsetattr(self.file, TCSAFLUSH, noncooked_tcattrs)

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


def getkey() -> str:
    """For testing purposes, seeing what a given keypress returns, etc"""
    k = Keyboard()
    with k.cbreak(), k.no_block():
        while not (keys := k.get_keys()): pass
        return keys
