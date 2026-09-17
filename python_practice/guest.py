# Executed only INSIDE the WASI guest. No host Python executes learner code.
import builtins
import io
import json
import sys
import traceback

_payload = json.loads(PAYLOAD)
_files = dict(_payload['files'])
_real_open = builtins.open


class VirtualText(io.StringIO):
    def __init__(self, name, mode):
        self.filename, self.mode = name, mode
        super().__init__('' if 'w' in mode else _files.get(name, ''))
        if 'a' in mode:
            self.seek(0, 2)

    def write(self, value):
        if not any(c in self.mode for c in 'wa+'):
            raise io.UnsupportedOperation('not writable')
        if self.tell() + len(value) > 1_000_000:
            raise OSError('Virtual file limit: 1 MB')
        result = super().write(value)
        _files[self.filename] = self.getvalue()
        return result

    def close(self):
        if not self.closed and any(c in self.mode for c in 'wa+'):
            _files[self.filename] = self.getvalue()
        super().close()


def virtual_open(file, mode='r', *args, **kwargs):
    name = str(file)
    if name.startswith('/packages/') or name.startswith('/usr/'):
        return _real_open(file, mode, *args, **kwargs)
    if 'b' in mode:
        raise OSError('Exercise files support text mode; binary files are unavailable.')
    if name not in _files and not any(c in mode for c in 'wa'):
        raise FileNotFoundError(name)
    if len(_files) >= 32 and name not in _files:
        raise OSError('Virtual file limit: 32 files')
    return VirtualText(name, mode)


builtins.open = virtual_open
sys.stdin = io.StringIO(_payload['stdin'])
sys.argv = ['main.py'] + _payload['argv']
try:
    exec(compile(_payload['code'], 'main.py', 'exec'), {'__name__': '__main__'})
except SystemExit:
    raise
except BaseException:
    traceback.print_exc(limit=8)
    sys.exit(1)
