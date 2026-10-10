# Arquitectura (propuesta inicial)

## Stack
- **Python 3.11** + **PySide6** (Qt: mismo código en macOS y Windows).
- **python-docx** (+ manipulación XML directa para runs partidos) → Word.
- **PyMuPDF (fitz)** → lectura y redacción real de PDF.
- **OCR**: RapidOCR (ONNX, se instala con pip y se empaqueta fácil en Mac y Windows).
  Alternativa: Tesseract (habría que incluir el binario por plataforma).
  - PDF escaneado: OCR → localizar cajas de las palabras a anonimizar → tapar píxeles
    en la imagen → (opcional) escribir el alias encima + capa de texto.
- **Detección en capas**:
  1. Lista del usuario + generador de variantes (rapidfuzz para coincidencias aproximadas).
  2. Reglas/regex españolas: DNI, NIE, CIF, IBAN, teléfonos, emails, matrículas,
     nº de procedimiento/autos, códigos postales, direcciones.
  3. NER: **GLiNER** multilingüe orientado a PII (rápido en CPU).
  4. Revisión con **LLM local** vía `llama-cpp-python` + GGUF pequeño (Qwen 3–4B Q4).
     Solo propone. Se desactiva automáticamente si la RAM es insuficiente.
- **Empaquetado**: PyInstaller por plataforma. **No se puede compilar el .app de Mac
  desde Windows** → se construye con **GitHub Actions** (runners macos + windows).
  - Mac: sin firma/notarización (Apple Developer, 99 €/año) el usuario debe abrir con
    clic derecho → Abrir la primera vez.
  - Windows: sin firma, SmartScreen avisará.

## Módulos
```
src/anonimizador/
  app.py              # arranque
  ui/main_window.py   # ventana única
  ui/suggestions.py   # diálogo de sugerencias
  core/
    document.py       # modelo común: segmentos de texto con posición
    readers/docx.py   # docx -> segmentos (incl. cabeceras, tablas, metadatos)
    readers/pdf.py    # texto nativo u OCR según la página
    writers/docx.py   # aplica sustituciones conservando el formato
    writers/pdf.py    # redacción real + reinserción del alias
    detectors/user_terms.py
    detectors/regex_es.py
    detectors/ner.py
    detectors/llm_review.py
    merge.py          # fusiona detecciones solapadas, asigna alias consistentes
    mapping.py        # mapa original<->alias, cifrado
    report.py
tests/
  corpus/             # documentos SINTÉTICOS de prueba
.github/workflows/    # build Mac + Windows
```

## Principio clave
La detección trabaja sobre texto plano con offsets; los writers traducen los offsets a
runs (docx) o rectángulos (pdf). Así los detectores son independientes del formato.

## Formatos de salida
- Por defecto, el mismo que el de entrada.
- DOCX → PDF: sin Word/LibreOffice no hay conversión fiel multiplataforma; evaluar más adelante.
- Siempre disponible: .txt (lo más práctico para pegar en la IA).
