"""Lista de nombres y datos que no se anonimizan nunca (la abogada, el despacho...).

Se guarda en un JSON en la carpeta de configuración del usuario, en este ordenador. Son
datos del propio despacho, no de clientes: no se cifra (ver docs/DECISIONES.md).
"""

import json
from pathlib import Path

KEY = "no_anonimitzar"


def load(path: Path) -> list[str]:
    """Textos guardados; lista vacía si el fichero no existe o está dañado."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data[KEY]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    return clean(i for i in items if isinstance(i, str))


def save(path: Path, items: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {KEY: clean(items)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean(items) -> list[str]:
    """Sin vacíos ni repetidos (se conserva el orden)."""
    return list(dict.fromkeys(i.strip() for i in items if i and i.strip()))
