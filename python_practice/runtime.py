"""Real CPython in a capability-restricted WASI instance; never host exec()."""
import json
import os
import re
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.getenv('PRACTICE_RUNTIME_DIR', ROOT / '.practice-runtime'))
LIMIT_SECONDS = 10
OUTPUT_LIMIT = 16384
MEMORY_LIMIT = 128 * 1024 * 1024
_LOCAL = threading.local()


def available():
    try:
        import wasmtime
        return (hasattr(wasmtime, 'Config') and (RUNTIME / 'python.wasm').is_file()
                and (RUNTIME / 'packages' / 'pytest' / '__init__.py').is_file())
    except (ImportError, OSError):
        return False


def _runtime():
    import wasmtime
    # Each executor thread runs one job at a time. Reuse its compiled interpreter
    # but never share the engine between threads: epochs are engine-wide, so
    # another learner's Stop must not interrupt this thread's execution.
    if hasattr(_LOCAL, 'runtime'):
        return _LOCAL.runtime
    config = wasmtime.Config()
    config.epoch_interruption = True
    config.consume_fuel = True
    engine = wasmtime.Engine(config)
    module = wasmtime.Module.from_file(engine, str(RUNTIME / 'python.wasm'))
    _LOCAL.runtime = wasmtime, engine, module
    return _LOCAL.runtime


def execute(code, stdin='', files=None, argv=None, cancel=None):
    """No inherited env, descriptors, network, or writable host directories.

    Virtual exercise files live in guest memory. WASI itself grants no filesystem
    write capabilities, so bypassing Python's open wrapper cannot escape it.
    """
    wasmtime, engine, module = _runtime()
    output, errors = bytearray(), bytearray()
    stopped = threading.Event()
    reason = []
    start = time.monotonic()

    def sink(target):
        def write(chunk):
            remaining = OUTPUT_LIMIT - len(output) - len(errors)
            target.extend(chunk[:max(0, remaining)])
            if len(chunk) > remaining and not reason:
                reason.append('output_limit')
                engine.increment_epoch()
            return len(chunk)
        return write

    def watchdog():
        while not stopped.wait(0.025):
            if cancel and cancel.is_set():
                reason.append('stopped')
            elif time.monotonic() - start >= LIMIT_SECONDS:
                reason.append('timeout')
            if reason:
                engine.increment_epoch()
                break

    bootstrap = (Path(__file__).with_name('guest.py')).read_text(encoding='utf-8')
    payload = json.dumps({'code': code, 'stdin': stdin, 'files': files or {}, 'argv': argv or []})
    source = 'PAYLOAD = ' + repr(payload) + '\n' + bootstrap
    with wasmtime.Store(engine) as store:
        store.set_limits(memory_size=MEMORY_LIMIT, instances=1, memories=1, tables=2)
        store.set_fuel(10_000_000_000)
        store.set_epoch_deadline(1)
        wasi = wasmtime.WasiConfig()
        # A trap skips CPython shutdown: flush each write so Stop, a timeout,
        # or an output limit cannot discard output already produced.
        wasi.argv = ['python', '-u', '-B', '-c', source]
        wasi.stdout_custom = sink(output)
        wasi.stderr_custom = sink(errors)
        packages = RUNTIME / 'packages'
        if packages.is_dir():
            # Wasmtime 37 exposes explicit permission enums; newer bindings use
            # the simpler mutable flag. Keep the runtime compatible with both so
            # a deploy does not silently lose the read-only package mount.
            try:
                wasi.preopen_dir(str(packages), '/packages', wasmtime.DirPerms.READ_ONLY, wasmtime.FilePerms.READ_ONLY)
            except (AttributeError, TypeError):
                wasi.preopen_dir(str(packages), '/packages', fs_mutable=False)
            wasi.env = [('PYTHONPATH', '/packages'), ('PYTHONDONTWRITEBYTECODE', '1')]
        store.set_wasi(wasi)
        with wasmtime.Linker(engine) as linker:
            linker.define_wasi()
            watcher = threading.Thread(target=watchdog, daemon=True)
            watcher.start()
            status = 'ok'
            try:
                instance = linker.instantiate(store, module)
                instance.exports(store)['_start'](store)
            except wasmtime.ExitTrap as exc:
                if exc.code:
                    status = 'runtime_error'
            except wasmtime.Trap as exc:
                status = reason[0] if reason else ('timeout' if 'fuel' in str(exc) else 'memory_limit')
            finally:
                stopped.set()
                watcher.join()
    stderr = errors.decode('utf-8', 'replace')
    if status == 'runtime_error':
        last_line = stderr.rstrip().split('\n')[-1]
        if re.match(r'^(SyntaxError|IndentationError|TabError):', last_line):
            status = 'syntax_error'
        elif re.match(r'^MemoryError(?::|$)', last_line):
            status = 'memory_limit'
    if reason:
        status = reason[0]
    return {'status': status, 'stdout': output.decode('utf-8', 'replace'), 'stderr': stderr,
            'duration_ms': round((time.monotonic() - start) * 1000)}
