"""Evita que el ordenador entre en reposo durante un proceso largo (80 págs escaneadas
pueden ser 10 minutos). La pantalla sí puede apagarse.

Windows: `SetThreadExecutionState` en el hilo que trabaja. macOS: `caffeinate -i -w <pid>`
(se cierra solo si la app termina de golpe). Si no se puede, el proceso sigue igual.
"""

import contextlib
import ctypes
import os
import subprocess
import sys
from collections.abc import Iterator

_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001


@contextlib.contextmanager
def keep_awake() -> Iterator[None]:
    if sys.platform == "win32":
        with _windows():
            yield
    elif sys.platform == "darwin":
        with _macos():
            yield
    else:
        yield


@contextlib.contextmanager
def _windows() -> Iterator[None]:
    try:
        set_state = ctypes.windll.kernel32.SetThreadExecutionState
        set_state(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)
    except (AttributeError, OSError):
        set_state = None
    try:
        yield
    finally:
        if set_state is not None:
            set_state(_ES_CONTINUOUS)


@contextlib.contextmanager
def _macos() -> Iterator[None]:
    try:
        process = subprocess.Popen(
            ["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        process = None
    try:
        yield
    finally:
        if process is not None:
            process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=2)
