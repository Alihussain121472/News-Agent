# Executed only INSIDE the WASI guest. No host Python executes learner code.
import builtins
import io
import json
import os
import posixpath
import sys
import traceback

_payload = json.loads(PAYLOAD)
def file_name(file):
    return posixpath.normpath('/work/' + os.fspath(file)) if not os.fspath(file).startswith('/') else posixpath.normpath(os.fspath(file))


_files = {file_name(name): bytearray(value.encode('utf-8')) for name, value in _payload['files'].items()}
_real_open = builtins.open


class VirtualFile(io.RawIOBase):
    def __init__(self, name, mode):
        super().__init__()
        self.name, self.mode = name, mode
        self.position = len(_files[name]) if 'a' in mode else 0

    def readable(self):
        return 'r' in self.mode or '+' in self.mode

    def writable(self):
        return any(c in self.mode for c in 'wax+')

    def seekable(self):
        return True

    def tell(self):
        self._checkClosed()
        return self.position

    def seek(self, offset, whence=0):
        self._checkClosed()
        if whence not in (0, 1, 2):
            raise ValueError('invalid whence')
        position = offset + (self.position if whence == 1 else len(_files[self.name]) if whence == 2 else 0)
        if position < 0:
            raise ValueError('negative seek position')
        self.position = position
        return position

    def readinto(self, buffer):
        self._checkClosed()
        if not self.readable():
            raise io.UnsupportedOperation('not readable')
        chunk = _files[self.name][self.position:self.position + len(buffer)]
        buffer[:len(chunk)] = chunk
        self.position += len(chunk)
        return len(chunk)

    def write(self, value):
        self._checkClosed()
        if not self.writable():
            raise io.UnsupportedOperation('not writable')
        if 'a' in self.mode:
            self.position = len(_files[self.name])
        end = self.position + len(value)
        if end > 1_000_000:
            raise OSError('Virtual file limit: 1 MB')
        content = _files[self.name]
        if end > len(content):
            content.extend(b'\0' * (end - len(content)))
        content[self.position:end] = value
        self.position = end
        return len(value)

    def truncate(self, size=None):
        self._checkClosed()
        if not self.writable():
            raise io.UnsupportedOperation('not writable')
        size = self.position if size is None else size
        if size < 0:
            raise ValueError('negative size')
        if size > 1_000_000:
            raise OSError('Virtual file limit: 1 MB')
        content = _files[self.name]
        if size > len(content):
            content.extend(b'\0' * (size - len(content)))
        else:
            del content[size:]
        return size


def virtual_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    name = file_name(file)
    if name.startswith('/packages/') or name.startswith('/usr/'):
        return _real_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
    if not isinstance(mode, str) or len(set(mode)) != len(mode) or any(c not in 'rwax+tb' for c in mode) or sum(c in mode for c in 'rwax') != 1 or ('t' in mode and 'b' in mode):
        raise ValueError('invalid file mode')
    if 'b' in mode:
        raise OSError('Exercise files support text mode; binary files are unavailable.')
    if buffering == 0:
        raise ValueError("can't have unbuffered text I/O")
    if opener is not None or not closefd:
        raise OSError('Custom file descriptors are unavailable.')
    if 'x' in mode and name in _files:
        raise FileExistsError(name)
    if name not in _files and 'r' in mode:
        raise FileNotFoundError(name)
    if len(_files) >= 32 and name not in _files:
        raise OSError('Virtual file limit: 32 files')
    if 'w' in mode or name not in _files:
        _files[name] = bytearray()
    result = io.TextIOWrapper(VirtualFile(name, mode), encoding=encoding or 'utf-8', errors=errors, newline=newline, write_through=True)
    result.mode = mode
    return result


builtins.open = virtual_open
io.open = virtual_open
sys.stdin = io.StringIO(_payload['stdin'])
sys.argv = ['main.py'] + _payload['argv']
try:
    exec(compile(_payload['code'], 'main.py', 'exec'), {'__name__': '__main__'})
except SystemExit:
    raise
except BaseException:
    traceback.print_exc(limit=8)
    sys.exit(1)
