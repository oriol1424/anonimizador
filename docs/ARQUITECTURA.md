# Arquitectura (propuesta inicial)

## Stack
- **Python 3.11** + **PySide6** (Qt: mismo código en macOS y Windows).
- **python-docx** (+ manipulación XML directa para runs partidos) → Word.
- **PyMuPDF (fitz)** → lectura y redacción real de PDF.
- **OCR**: RapidOCR (ONNX, modelos incluidos en el paquete pip, Mac y Windows, catalán).
- **Detección en capas**:
  1. Lista del usuario + generador de variantes (rapidfuzz para coincidencias aproximadas).
  2. Reglas/regex españolas: DNI, NIE, CIF, IBAN, teléfonos, emails, matrículas,
     nº de procedimiento/autos, códigos postales, direcciones.
  3. NER — **debe rendir bien en catalán**. Candidatos a evaluar con el corpus catalán:
     - GLiNER multilingüe orientado a PII (rápido en CPU, cubre catalán).
     - Modelos NER catalanes del Projecte AINA / BSC (RoBERTa-ca entrenados en NER).
     - spaCy `ca_core_news_*`.
  4. Revisión con **LLM local** vía `llama-cpp-python` + GGUF pequeño. Candidatos:
     **Salamandra** (BSC, entrenado con mucho catalán) o Qwen 3–4B; elegir por calidad en
     catalán con el corpus. Solo propone. Se desactiva si la RAM es insuficiente.
- **Empaquetado**: PyInstaller por plataforma. **No se puede compilar el .app de Mac
  desde Windows** → se construye con **GitHub Actions** (runners macos + windows).
  - Mac: sin firma/notarización (Apple Developer, 99 €/año) el usuario debe abrir con
    clic derecho → Abrir la primera vez.
  - Windows: sin firma, SmartScreen avisará.

## Módulos
```
src/anonimizador/
  app.py              # arranque de la app                               [hecho]
  i18n.py             # TODOS los textos visibles, ca/es                  [hecho]
  ui/main_window.py   # ventana única: asistente de 4 pasos + navegación  [hecho]
  ui/sidebar.py       # barra lateral: pasos, idioma, «100% local»        [hecho]
  ui/pages.py         # pasos 1 (documento), 2 (lista) y 4 (guardar)      [hecho]
  ui/suggestions.py   # paso 3: sugerencias con buscador y filtros        [hecho]
  ui/status_pages.py  # progreso por fases + Cancel·la; resultado         [hecho]
  ui/style.py         # colores, hoja de estilos e iconos (propuesta B)   [hecho]
  ui/widgets.py       # desplegable de alias, avisos, filtros, segmentos  [hecho]
  ui/worker.py        # tareas en segundo plano, progreso y cancelación   [hecho]
  ui/keep_dialog.py   # editar la lista «No anonimitzar»                  [hecho]
  __main__.py         # CLI de pruebas                                  [hecho]
  core/
    lang.py           # idiomas (ca por defecto, es): alias y presets   [hecho]
    text.py           # normalización sin tildes que conserva offsets   [hecho]
    progress.py       # progreso por fases y cancelación (Cancelled)    [hecho]
    keep_list.py      # lista «No anonimitzar» (JSON en la config local) [hecho]
    keep_awake.py     # el equipo no entra en reposo durante las tareas [hecho]
    matcher.py        # términos del usuario + variantes + ambigüedad    [hecho]
    regex_es.py       # DNI, NIE, CIF, IBAN, tel., email, matrícula...   [hecho]
    docx_io.py        # leer/anonimizar Word a nivel XML (todas las partes) [hecho]
    pipeline.py       # analyze() -> sugerencias; anonymize() -> informe  [hecho]
    result.py         # ProcessResult común a Word y PDF                 [hecho]
    pdf_io.py         # PDF con texto: redacción real (PyMuPDF)          [hecho]
    ocr.py            # OCR local (RapidOCR, catalán) con caché en memoria [hecho]
    ner.py            # personas/empresas: AINA RoBERTa-ca en ONNX int8   [hecho]
    guide.py          # guía de correspondencias (.docx confidencial)    [hecho]
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

## PDF: detalles que importan
- Texto por carácter con su caja (`rawdict`); un nombre partido entre líneas genera una
  caja por línea. Las cajas se recortan un poco para no tocar letras vecinas.
- `apply_redactions` con `images=PIXELS` (borra también imágenes debajo, p. ej. PDF
  escaneados con capa de texto) y `graphics=NONE` (no borra líneas de tablas).
- El alias se escribe en la posición del primer carácter, estrechado (`morph`) si no cabe.
- Se guarda con `garbage=4, clean=True` para no dejar copias del contenido antiguo.
- Página imagen = una imagen cubre ≥50% de la página (escaneada, o escaneada con capa
  de texto de otro OCR, o con fondo de imagen) → se trata con OCR, sin fiarse de la capa
  de texto que traiga:
  1. Se rasteriza a 200 dpi y se lee con RapidOCR (PP-OCRv6 multilingüe, incluye catalán;
     ~3 s/página en CPU). Da una caja por palabra; la de cada letra se reparte a partes iguales.
  2. Se pintan de blanco los píxeles de cada dato (+3 px de margen).
  3. Se vacía la página entera (texto, imágenes, dibujos) y se rehace con la imagen limpia
     (JPEG), el alias visible y una capa de texto invisible ya anonimizada.
  4. La verificación final vuelve a pasar OCR sobre la imagen resultante.
- El OCR se cachea en memoria (hash de la imagen) para no repetirlo entre análisis y
  anonimización; nunca se guarda en disco.
- Progreso por fases (`core/progress.py`): el núcleo llama `progress(fase, hecho, total)`
  con códigos "read", "detect", "anonymize", "verify", "export"; la interfaz los traduce y
  calcula el tiempo restante. Para cancelar, la función de progreso lanza `Cancelled`
  (hereda de BaseException: ningún `except Exception` de página la confunde con un fallo).
- El .txt se genera del original + sustituciones (el texto añadido saldría desordenado).

## Detección de personas, empresas y direcciones
- **Direcciones**: reglas (`regex_es.ADDRESS`): tipo de vía + nombre + número/km/s/n +
  piso/puerta + CP + población. 7/7 en la evaluación, sin falsos positivos.
- **Personas y empresas**: `projecte-aina/roberta-base-ca-v2-cased-ner` convertido a ONNX
  int8 (125 MB, `models/ner-ca/`, fuera de git; se genera con `scripts/preparar_models.py`).
  Se ejecuta con onnxruntime + tokenizers (sin PyTorch). Texto en trozos de ~1500
  caracteres; etiqueta por palabra = primer sub-token; esquema BIO.
- Post-proceso: apóstrofo ’ → ' antes del modelo (mismo largo), unir "d'" + apellido,
  quitar tratamientos (Sr., Sra., Don...), descartar organismos públicos (Jutjat,
  Agència Tributària, Ayuntamiento...), papeles procesales (Demandat, Actora...) y
  textos sin mayúsculas.
- No se sugiere lo ya cubierto por la lista del usuario, ni partes de esos nombres.
- `merge_variants` une "Jordi Casals i Pons" / "Sr. Casals" / "J. Casals Pons" en una
  sola sugerencia (sin IA: usa las mismas variantes que la sustitución).
- Orden en la ventana: personas, empresas, direcciones, DNI...
- Evaluación: `tests/corpus/ner_eval_ca.py` (25 frases jurídicas inventadas). Comparativa
  2026-10-10 (personas+empresas, 32): AINA 32/32 (2,7 s con PyTorch, 0,5 s en ONNX),
  GLiNER multi/PII 32/32 pero más falsos positivos y 3× más lento, spaCy 29/32,
  GLiNER knowledgator 26/32. También acierta en castellano en las pruebas.
- Sin el modelo la app funciona igual (solo reglas) y avisa.

## Guía de correspondencias
- Opción (marcada por defecto) en la ventana: `<nombre>_GUIA_CONFIDENCIAL.docx` junto al
  documento anonimizado. Tabla: alias, texto original, formas encontradas (veces), origen
  (tu lista / tipo detectado) y total. Los términos de la lista que no aparecen se marcan
  "No trobat" (ayuda a detectar errores de escritura).
- Aviso de confidencialidad destacado; autor vacío en sus metadatos.

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
