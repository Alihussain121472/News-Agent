"""Download the pinned, checksum-verified CPython WASI distribution."""
import hashlib
from pathlib import Path
import urllib.request
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
URL = ('https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/'
       'python/3.12.0%2B20231211-040d5a6/python-3.12.0.wasm')
SHA256 = 'e5dc5a398b07b54ea8fdb503bf68fb583d533f10ec3f930963e02b9505f7a763'

def main():
    target = ROOT / '.practice-runtime' / 'python.wasm'
    target.parent.mkdir(exist_ok=True)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == SHA256:
        print('Python practice runtime verified.')
    else:
        with urllib.request.urlopen(URL, timeout=120) as response:
            data = response.read(40_000_000)
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise RuntimeError('Runtime checksum mismatch; refusing to install.')
        target.write_bytes(data)
        print('Python practice runtime installed and verified.')
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-compile','--no-deps',
                    '--upgrade','--target',str(target.parent/'packages'),'-r',str(ROOT/'requirements-practice.txt')],check=True)

if __name__ == '__main__':
    main()
