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
  __main__.py         # CLI de pruebas                                  [hecho]
  core/
    text.py           # normalización sin tildes que conserva offsets   [hecho]
    matcher.py        # términos del usuario + variantes + ambigüedad    [hecho]
    regex_es.py       # DNI, NIE, CIF, IBAN, tel., email, matrícula...   [hecho]
    docx_io.py        # leer/anonimizar Word a nivel XML (todas las partes) [hecho]
    pipeline.py       # analyze() -> sugerencias; anonymize() -> informe  [hecho]
    pdf_io.py         # texto nativo u OCR + redacción real
    ner.py            # GLiNER
    llm_review.py     # LLM local
    mapping.py        # mapa original<->alias, cifrado
tests/
  corpus/             # documentos SINTÉTICOS de prueba
.github/workflows/    # build Mac + Windows
```

## Principio clave
La detección trabaja sobre texto plano con offsets; los writers traducen los offsets a
runs (docx) o rectángulos (pdf). Así los detectores son independientes del formato.

## Flujo implementado
1. `analyze(doc, términos_usuario)` → extrae todo el texto (incl. metadatos y enlaces),
   ejecuta las reglas y devuelve `Suggestion`s de lo NO cubierto por la lista del usuario,
   con alias numerado por tipo (`[DNI_1]`, `[IBAN_1]`...) y agrupando formatos del mismo valor.
2. El usuario acepta/edita sugerencias → se convierten en `Term(expand=False)`.
3. `anonymize(src, dst, términos)` → sustituye en todas las partes del docx y después
   **verifica** releyendo la salida: si queda alguna aparición, lo avisa en el informe.

## Word: detalles que importan
- Un nombre puede estar partido en varios `w:r` con formatos distintos: se concatena el
  texto del párrafo, se busca, y el alias se escribe en el primer run (hereda su formato).
- Tabuladores y saltos entre runs cuentan como espacio para no unir palabras.
- Se procesan también `w:delText` (texto borrado del control de cambios), `w:instrText`
  (códigos de campo), atributos `author`/`initials`, `docProps` y destinos de hipervínculos.

## Formatos de salida
- Por defecto, el mismo que el de entrada.
- DOCX → PDF: sin Word/LibreOffice no hay conversión fiel multiplataforma; evaluar más adelante.
- Siempre disponible: .txt (lo más práctico para pegar en la IA).
