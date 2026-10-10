import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # tests de la ventana sin pantalla
sys.path.insert(0, str(Path(__file__).parent / "corpus"))

from generar_corpus import build_demanda_ca, build_demanda_es  # noqa: E402


@pytest.fixture
def demanda(tmp_path: Path) -> Path:
    """Demanda en castellano."""
    return build_demanda_es(tmp_path / "demanda_es.docx")


@pytest.fixture
def demanda_ca(tmp_path: Path) -> Path:
    """Demanda en catalán (el caso habitual)."""
    return build_demanda_ca(tmp_path / "demanda_ca.docx")
