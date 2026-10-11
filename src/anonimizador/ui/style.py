"""Aspecto de la aplicación (propuesta B: «Assistent per passos»).

Colores sobrios (verde azulado sobre gris cálido) y la tipografía del sistema (Segoe UI
en Windows, San Francisco en macOS): no hay que empaquetar fuentes. Siempre en claro,
aunque el sistema esté en modo oscuro, para que no se mezclen colores.
"""

from PySide6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

ACCENT = "#0F5C5C"
ACCENT_HOVER = "#0B4A4A"
ACCENT_SOFT = "#E1EFEC"
BG = "#F6F5F2"
SURFACE = "#FFFFFF"
BORDER = "#E2E0DA"
BORDER_STRONG = "#D6D3CC"
TEXT = "#1E2422"
MUTED = "#4D5551"
SUBTLE = "#5E6662"
SUCCESS = "#2F7A4B"
SUCCESS_SOFT = "#E3F1E6"
DANGER = "#A4262C"
DANGER_SOFT = "#FDECEC"
WARNING = "#7A5200"
WARNING_SOFT = "#FFF4D6"

# Tipografía del sistema: Windows (Segoe), macOS (San Francisco) y alternativas.
FONT_FAMILIES = ["Segoe UI Variable Text", "Segoe UI", ".AppleSystemUIFont", "Helvetica Neue",
                 "Arial"]  # fmt: skip

STYLE = f"""
QWidget {{ color: {TEXT}; font-size: 10.5pt; }}
QMainWindow, QWidget#pages, QWidget#page {{ background: {BG}; }}
QToolTip {{ background: {TEXT}; color: white; border: none; padding: 4px 8px; }}

QFrame#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
QLabel#appName {{ font-size: 12.5pt; font-weight: 700; }}
QLabel#fileName {{ color: {SUBTLE}; font-size: 9pt; }}
QLabel#localBadge {{ color: {SUBTLE}; font-size: 9pt; }}

QPushButton#step {{
    text-align: left; border: none; border-radius: 8px; padding: 0; background: transparent;
}}
QPushButton#step:hover {{ background: #F1F0EC; }}
QPushButton#step[current="true"] {{ background: {ACCENT_SOFT}; }}
QPushButton#step:disabled {{ background: transparent; }}
QLabel#stepText {{ font-size: 11pt; color: {MUTED}; }}
QLabel#stepText[current="true"] {{ color: {ACCENT}; font-weight: 700; }}
QLabel#stepText[enabled="false"] {{ color: #9AA09C; }}
QLabel#badge {{
    background: {ACCENT}; color: white; border-radius: 10px; padding: 0 8px;
    font-size: 8.5pt; font-weight: 700; min-height: 20px; max-height: 20px;
}}

QLabel#h1 {{ font-size: 18pt; font-weight: 700; }}
QLabel#h2 {{ font-size: 12pt; font-weight: 700; }}
QLabel#muted {{ color: {MUTED}; font-size: 11pt; }}
QLabel#small {{ color: {MUTED}; font-size: 9.5pt; }}
QLabel#alias {{ color: {ACCENT}; font-family: Consolas, Menlo, monospace; }}

QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
QFrame#dropzone {{
    background: {SURFACE}; border: 2px dashed {BORDER_STRONG}; border-radius: 14px;
}}
QFrame#dropzone[hover="true"] {{ border-color: {ACCENT}; background: {ACCENT_SOFT}; }}
QFrame#notice {{ border-radius: 8px; }}
QFrame#notice[level="serious"] {{ background: {DANGER_SOFT}; border: 1px solid #F3C5C7; }}
QFrame#notice[level="warning"] {{ background: {WARNING_SOFT}; border: 1px solid #F0DFA8; }}
QFrame#notice[level="info"] {{ background: #EEF0EE; border: 1px solid {BORDER}; }}
QLabel#noticeText[level="serious"] {{ color: {DANGER}; }}
QLabel#noticeText[level="warning"] {{ color: {WARNING}; }}

QPushButton {{
    background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: 8px;
    padding: 0 16px; min-height: 38px; font-weight: 600;
}}
QPushButton:hover {{ background: #F1F0EC; }}
QPushButton:disabled {{ color: #9AA09C; }}
QPushButton#primary {{ background: {ACCENT}; border: none; color: white; padding: 0 24px;
    min-height: 44px; font-size: 11pt; font-weight: 700; }}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:disabled {{ background: #9DBDBB; color: #F4F8F7; }}
QPushButton#flat {{ background: transparent; border: none; color: {MUTED}; }}
QPushButton#flat:hover {{ color: {TEXT}; background: #F1F0EC; }}
QPushButton#chip {{
    border-radius: 16px; min-height: 32px; padding: 0 14px; font-weight: 600;
}}
QPushButton#chip:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton#segment {{ border-radius: 0; min-height: 34px; padding: 0 14px; font-weight: 600; }}
QPushButton#segment:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}

QLineEdit, QComboBox {{
    background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: 8px;
    padding: 6px 10px; min-height: 26px; selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border: 2px solid {ACCENT}; padding: 5px 9px; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT}; border: 1px solid {BORDER_STRONG}; }}
QTableWidget QComboBox {{
    border: 1px solid transparent; border-radius: 6px; background: transparent;
    padding: 2px 8px; min-height: 22px; margin: 4px 6px; color: {ACCENT};
    font-family: Consolas, Menlo, monospace;
}}
QTableWidget QComboBox:hover {{ border-color: {BORDER_STRONG}; background: {SURFACE}; }}
QTableWidget QComboBox:focus {{ border: 1px solid {ACCENT}; background: {SURFACE}; }}
QTableWidget QComboBox::drop-down {{ border: none; width: 20px; }}

QTableWidget {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    gridline-color: #EFEDE8; selection-background-color: {ACCENT_SOFT}; selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 0 10px; border-bottom: 1px solid #EFEDE8; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #C9C6BF; border-radius: 4px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: #A9A59D; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: #C9C6BF; border-radius: 4px; min-width: 32px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QHeaderView::section {{
    background: #FAF9F7; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER};
    padding: 8px; font-weight: 600; font-size: 9.5pt;
}}
QCheckBox {{ spacing: 8px; }}

QProgressBar {{ background: #E7E5E0; border: none; border-radius: 5px; max-height: 10px;
    min-height: 10px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}
QFrame#phase {{ border-radius: 8px; }}
QFrame#phase[current="true"] {{ background: #EEF0EE; }}
QLabel#phaseName {{ font-size: 11pt; font-weight: 600; }}
QLabel#phaseName[pending="true"] {{ color: {SUBTLE}; font-weight: 500; }}
"""


def apply(app: QApplication) -> None:
    """Estilo Fusion con paleta clara fija (el modo oscuro del sistema no lo cambia)."""
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, BG), (QPalette.ColorRole.Base, SURFACE),
        (QPalette.ColorRole.AlternateBase, "#FAF9F7"), (QPalette.ColorRole.Text, TEXT),
        (QPalette.ColorRole.WindowText, TEXT), (QPalette.ColorRole.Button, SURFACE),
        (QPalette.ColorRole.ButtonText, TEXT), (QPalette.ColorRole.Highlight, ACCENT),
        (QPalette.ColorRole.HighlightedText, "#FFFFFF"),
        (QPalette.ColorRole.PlaceholderText, "#7A817D"), (QPalette.ColorRole.ToolTipBase, TEXT),
        (QPalette.ColorRole.ToolTipText, "#FFFFFF"),
    ):  # fmt: skip
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    font = QFont(app.font())
    font.setFamilies(FONT_FAMILIES)
    font.setPointSizeF(10.5)
    app.setFont(font)
    app.setStyleSheet(STYLE)


# --- Iconos (dibujados aquí: sin ficheros de terceros) -----------------------------------

_SVG = {
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
    '<path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
    "upload": '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M5 20h14"/>',
    "logo": '<path d="M4 7h16M4 12h10M4 17h7"/><rect x="15" y="14" width="6" height="6" rx="1"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "alert": '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}


def icon_pixmap(name: str, color: str, size: int = 20, stroke: float = 2.0) -> QPixmap:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{_SVG[name]}</svg>'
    )
    ratio = 2  # nítido en pantallas de alta densidad
    pixmap = QPixmap(QSize(size * ratio, size * ratio))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(ratio)
    return pixmap


def icon(name: str, color: str = MUTED, size: int = 20) -> QIcon:
    return QIcon(icon_pixmap(name, color, size))


def step_marker(state: str, number: int, size: int = 24) -> QPixmap:
    """Círculo de un paso: "done" (marca), "current" (número relleno), "todo" (aro)."""
    ratio = 2
    pixmap = QPixmap(QSize(size * ratio, size * ratio))
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(ratio)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(1, 1, size - 2, size - 2)
    if state == "done":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACCENT_SOFT))
        painter.drawEllipse(rect)
        painter.drawPixmap(
            QPointF(size * 0.25, size * 0.25), icon_pixmap("check", ACCENT, size // 2, 3)
        )
    elif state == "current":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACCENT))
        painter.drawEllipse(rect)
        painter.setPen(QColor("#FFFFFF"))
    else:
        painter.setPen(QPen(QColor("#A7ADA9"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        painter.setPen(QColor(SUBTLE))
    if state != "done":
        font = QFont(painter.font())
        font.setBold(state == "current")
        font.setPixelSize(int(size * 0.5))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(number))
    painter.end()
    return pixmap


def phase_marker(state: str, size: int = 26) -> QPixmap:
    """Estado de una fase del progreso: "done", "current" o "pending"."""
    ratio = 2
    pixmap = QPixmap(QSize(size * ratio, size * ratio))
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(ratio)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if state == "done":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SUCCESS_SOFT))
        painter.drawEllipse(QRectF(1, 1, size - 2, size - 2))
        painter.drawPixmap(
            QPointF(size * 0.25, size * 0.25), icon_pixmap("check", SUCCESS, size // 2, 3)
        )
    elif state == "current":
        painter.setPen(QPen(QColor(ACCENT), 3))
        painter.drawEllipse(QRectF(2.5, 2.5, size - 5, size - 5))
    else:
        painter.setPen(QPen(QColor("#B9BEBB"), 2))
        painter.drawEllipse(QRectF(2, 2, size - 4, size - 4))
    painter.end()
    return pixmap
