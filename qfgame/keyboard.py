import sys
from select import select
from termios import tcsetattr, TCSAFLUSH
from tty import setcbreak


class Keyboard:

    def __init__(self, file=None):
        self.file = sys.stdin if file is None else file
        self.tcattrs = None

    def getch(self, timeout: float = None) -> str:
        file = self.file
        if timeout is None:
            return file.read(1)
        rlist, _, _ = select((file,), (), (), timeout)
        if rlist:
            return file.read(1)
        else:
            return ''

    def __enter__(self):
        self.tcattrs = setcbreak(self.file)
        return self

    def __exit__(self, *args):
        tcsetattr(self.file, TCSAFLUSH, self.tcattrs)
        self.tcattrs = None
