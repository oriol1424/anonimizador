"""Registro local de errores para poder diagnosticar fallos en el bufete.

Regla 3: NUNCA contiene texto del documento. Por eso no se guarda el mensaje de la
excepción (podría llevar un nombre: `KeyError('Joan Puig')`), solo su tipo, la versión, el
sistema, el paso y la cadena de llamadas (fichero, línea y función de nuestro código o de
las librerías). El fichero se queda en este ordenador; el usuario puede enviarlo si quiere.
"""

import errno
import platform
import traceback
from datetime import datetime
from pathlib import Path

from anonimizador import __version__

MAX_BYTES = 200_000  # al superarlo se conserva solo la mitad más reciente


_PLACES = (  # tipo de carpeta por un trozo de su ruta (el primero que coincida)
    ("/Library/Containers/", "contenidor d'una altra app (Mail, Outlook...)"),
    ("/Library/Group Containers/", "contenidor compartit d'una app (WhatsApp...)"),
    ("/Library/Mobile Documents/", "iCloud Drive"),
    ("/Library/CloudStorage/", "núvol (OneDrive, Dropbox, Google Drive...)"),
    ("/var/folders/", "carpeta temporal del sistema"),
    ("/Volumes/", "disc extern, USB o xarxa"),
    ("/Desktop", "Escriptori"),
    ("/Documents", "Documents"),
    ("/Downloads", "Baixades"),
)


def place_kind(folder: str) -> str:
    """Qué tipo de carpeta es, sin decir cuál: la ruta puede llevar el nombre del
    cliente. Para diagnosticar permisos del Mac sin incumplir la regla 3."""
    path = folder.replace("\\", "/")
    kind = next((name for part, name in _PLACES if part in path), "altra")
    if folder != folder.rstrip():
        kind += " · el nom acaba en espai"
    return kind


def entry(error: BaseException, step: str = "") -> str:
    frames = traceback.extract_tb(error.__traceback__)
    lines = [
        f"=== {datetime.now():%Y-%m-%d %H:%M:%S} · v{__version__} · "
        f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
        f"pas: {step or '-'}",
        f"error: {type(error).__module__}.{type(error).__qualname__}",
    ]
    kind = getattr(error, "kind", None)
    if isinstance(kind, str):  # AnonymizerError: código del mensaje mostrado
        lines.append(f"codi: {kind}")
    folder = getattr(error, "params", {}).get("folder")
    if isinstance(folder, str) and folder:
        lines.append(f"carpeta: {place_kind(folder)}")
    cause = error.__cause__
    if cause is not None:  # tipo y código del sistema (ENOENT, EPERM...), nunca el mensaje
        code = errno.errorcode.get(getattr(cause, "errno", None) or -1, "")
        lines.append(f"causa: {type(cause).__module__}.{type(cause).__qualname__} {code}".rstrip())
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
