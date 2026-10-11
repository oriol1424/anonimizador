import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # tests de la ventana sin pantalla
sys.path.insert(0, str(Path(__file__).parent / "corpus"))

from generar_corpus import build_demanda_ca, build_demanda_es, build_demanda_pdf_ca  # noqa: E402

_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture(autouse=True, scope="session")
def no_network():
    """Regla 1: nada sale del equipo. Cualquier conexión de red fuera del propio
    ordenador hace fallar el test (p. ej. RapidOCR intentando descargar un modelo)."""
    import socket

    original = socket.socket.connect

    def guarded(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if self.family in (socket.AF_INET, socket.AF_INET6) and host not in _LOCAL_HOSTS:
            raise AssertionError(f"Intent de connexió de xarxa bloquejat: {host}")
        return original(self, address, *args, **kwargs)

    patch = pytest.MonkeyPatch()
    patch.setattr(socket.socket, "connect", guarded)
    patch.setattr(socket.socket, "connect_ex", guarded)
    yield
    patch.undo()


@pytest.fixture
def demanda(tmp_path: Path) -> Path:
    """Demanda en castellano."""
    return build_demanda_es(tmp_path / "demanda_es.docx")


@pytest.fixture
def demanda_ca(tmp_path: Path) -> Path:
    """Demanda en catalán (el caso habitual)."""
    return build_demanda_ca(tmp_path / "demanda_ca.docx")


@pytest.fixture
def demanda_pdf(tmp_path: Path) -> Path:
    """PDF en catalán: página de texto + página escaneada."""
    return build_demanda_pdf_ca(tmp_path / "demanda_ca.pdf")
