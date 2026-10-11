"""Registro local de errores para poder diagnosticar fallos en el bufete.

Regla 3: NUNCA contiene texto del documento. Por eso no se guarda el mensaje de la
excepción (podría llevar un nombre: `KeyError('Joan Puig')`), solo su tipo, la versión, el
sistema, el paso y la cadena de llamadas (fichero, línea y función de nuestro código o de
las librerías). El fichero se queda en este ordenador; el usuario puede enviarlo si quiere.
"""

import platform
import traceback
from datetime import datetime
from pathlib import Path

from anonimizador import __version__

MAX_BYTES = 200_000  # al superarlo se conserva solo la mitad más reciente


def entry(error: BaseException, step: str = "") -> str:
    frames = traceback.extract_tb(error.__traceback__)
    lines = [
        f"=== {datetime.now():%Y-%m-%d %H:%M:%S} · v{__version__} · "
        f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
        f"pas: {step or '-'}",
        f"error: {type(error).__module__}.{type(error).__qualname__}",
    ]
    lines += [f"  {Path(f.filename).name}:{f.lineno} {f.name}" for f in frames]
    return "\n".join(lines) + "\n"


def write(path: Path, error: BaseException, step: str = "") -> Path | None:
    """Añade el error al registro. Nunca falla (un error al registrar no debe tapar el
    original)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        if len(old.encode("utf-8")) > MAX_BYTES:
            old = old[len(old) // 2 :]
            old = old[old.find("=== ") :] if "=== " in old else ""
        path.write_text(old + entry(error, step), encoding="utf-8")
        return path
    except OSError:
        return None
