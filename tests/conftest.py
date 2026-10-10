import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "corpus"))

from generar_corpus import build_demanda  # noqa: E402


@pytest.fixture
def demanda(tmp_path: Path) -> Path:
    return build_demanda(tmp_path / "demanda.docx")
