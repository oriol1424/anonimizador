"""Evitar el reposo durante procesos largos."""

import sys

import pytest

from anonimizador.core import keep_awake


def test_keep_awake_never_breaks_the_task():
    with keep_awake.keep_awake():
        value = 42
    assert value == 42


def test_errors_inside_still_propagate():
    with pytest.raises(ValueError), keep_awake.keep_awake():
        raise ValueError


@pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")
def test_windows_sets_and_resets_state(monkeypatch):
    calls = []

    class Kernel32:
        def SetThreadExecutionState(self, flags):  # noqa: N802 - nombre de la API
            calls.append(flags)
            return 1

    monkeypatch.setattr(keep_awake.ctypes.windll, "kernel32", Kernel32())
    with keep_awake.keep_awake():
        assert calls == [0x80000001]
    assert calls == [0x80000001, 0x80000000]
