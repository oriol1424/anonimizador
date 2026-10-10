# Progreso

## Estado actual
Fase 1 — **Word y PDF con texto, con interfaz en catalán** (109 tests). Ya se puede usar la app:

```
.venv/Scripts/python -m anonimizador.app
```

También hay línea de comandos para pruebas rápidas:

```
.venv/Scripts/python tests/corpus/generar_corpus.py
.venv/Scripts/python -m anonimizador tests/corpus/demanda_ficticia.docx salida.docx \
    -t "Juan Pérez García=[CLIENTE_1]" -t "Construcciones Levante SL=[EMPRESA_1]" -s
```

## Entorno de desarrollo
```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/ruff check src tests && .venv/Scripts/ruff format src tests
```

## Pendiente de confirmar con el bufete
- [ ] Modelos concretos de Mac (¿Apple Silicon M1+ o Intel?) y RAM; ídem PCs Windows.
- [ ] **Licencia PyMuPDF (AGPL-3.0)**: ¿el código será público/abierto o la app se venderá
      cerrada? Si es cerrada → licencia comercial de Artifex o cambiar de librería.
- [ ] ¿Firmar la app? (Apple Developer 99 €/año; certificado Windows ~200–400 €/año).
- [ ] Tipos de documento habituales para ampliar el corpus sintético (en catalán).

## Siguientes pasos
1. [x] Estructura del proyecto: `pyproject.toml`, `src/`, venv, ruff, pytest.
2. [x] Corpus sintético (`tests/corpus/generar_corpus.py`).
3. [x] MVP DOCX: sustitución de la lista del usuario conservando el formato.
4. [x] Detector regex español + sugerencias + verificación final.
5. [x] Ventana única PySide6 en catalán (fichero + arrastrar, idioma, tabla con desplegable
       editable, cargar/guardar lista, guardar como, diálogo de sugerencias, resultado).
6. [x] PDF de texto con redacción real (+ aviso de páginas escaneadas y PDF protegidos).
7. [ ] **PDF escaneado con OCR.** ← SIGUIENTE
8. [ ] NER para personas, empresas y direcciones no indicadas — evaluar en catalán
       (GLiNER multilingüe vs. modelos AINA/BSC vs. spaCy ca).
9. [ ] LLM local de revisión (desactivable por RAM) — evaluar Salamandra (BSC) vs. Qwen en catalán.
10. [ ] GitHub Actions: build Mac + Windows; prueba desde USB en equipos limpios.
11. [ ] Mapa cifrado y des-anonimización de respuestas (fase 2).

## Limitaciones conocidas
- Direcciones y nombres que el usuario no indica no se detectan aún (llegará con NER, paso 8).
- Imágenes incrustadas (Word y PDF) no se anonimizan: se avisa al usuario.
- PDF escaneados: de momento solo se detectan y se avisa en rojo; no se anonimizan (paso 7).
- PDF: si el alias es más largo que el nombre, se estrecha o se reduce el tamaño para que
  quepa (puede quedar pequeño). Para pasar a la IA, la salida .txt es la más limpia.
- Si dos términos comparten apellido ("Joan Puig" / "Pere Puig"), "Sr. Puig" no se
  sustituye automáticamente y se avisa.
- La CLI de pruebas muestra sus etiquetas en castellano (los avisos sí salen en el idioma elegido).
- El recuento del informe cuenta apariciones en párrafos (no en metadatos ni enlaces).

## Hecho
- 2026-10-10: Definición de la idea, requisitos y estructura de documentación.
- 2026-10-10: Respuestas del cliente: Mac + Windows, PDFs escaneados y nativos,
  sustituto con desplegable editable, interfaz de una sola ventana.
- 2026-10-10: Núcleo Word: matcher con variantes, reglas españolas (DNI, NIE, CIF, IBAN,
  teléfono, email, matrícula, nº procedimiento), cobertura de cabeceras, pies, tablas,
  comentarios, control de cambios, autores, hipervínculos y metadatos; salida .docx/.txt;
  CLI de pruebas.
- 2026-10-10: Catalán como idioma por defecto (selector ca/es): alias y desplegable por
  idioma; nombres catalanes ("Puig i Ferrer" = "Puig Ferrer", "d'Orriols" -> "l'Orriols",
  "Marcel·lí", apóstrofo ’); demanda catalana ficticia en el corpus.
- 2026-10-10: Interfaz en catalán (castellano al cambiar el idioma): ventana única,
  desplegable editable con numeración automática ([CLIENT_1], [CLIENT_2]...), arrastrar
  fichero, listas de términos por caso (.json), diálogo de sugerencias con casillas,
  proceso en segundo plano; textos en i18n.py; avisos/errores del núcleo como códigos.
- 2026-10-10: PDF con texto: borrado real con PyMuPDF (redacción del contenido + píxeles
  debajo), alias en el mismo sitio, nombres partidos entre líneas, tablas intactas,
  notas, enlaces, campos, marcadores y metadatos; páginas escaneadas detectadas y avisadas;
  PDF protegido con mensaje claro; exportación .txt en orden de lectura; el desplegable
  de formato depende de la entrada (Word -> Word/Text, PDF -> PDF/Text).
