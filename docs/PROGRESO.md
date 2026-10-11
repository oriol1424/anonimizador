# Progreso

## ▶ DÓNDE NOS QUEDAMOS (2026-10-10) — empezar por aquí
Estábamos haciendo **robustez con documentos largos (80+ páginas)**. Todo lo anterior está
hecho, probado (141 tests) y publicado. No hay código a medias: lo de abajo es lo medido
y el plan, aún SIN implementar.

### Medición (`scripts/bench_documents_grans.py <carpeta> <págs_escaneadas>`)
| Documento | Análisis | Anonimizar + verificar | Problema |
|---|---|---|---|
| Word 80 págs | 39 s | 6,5 s | detector de nombres lento |
| PDF texto 80 págs | 43 s | 34 s | ídem |
| PDF escaneado 10 págs | 74 s | 178 s | ~35 min a 80 págs **y quedó un nombre sin borrar** |

### Causas encontradas
1. **Fuga en escaneados (GRAVE):** el OCR leyó mal una línea entera ("2 a 02s") porque el
   clasificador de orientación (`use_cls`) la giró 180°. Esa línea no se borró (nombre + DNI).
   La verificación final SÍ lo detectó (aviso "leftovers"). Con `Global.use_cls: False`
   las 3 líneas mal leídas pasan a leerse bien y no es más lento.
2. **Detector de nombres:** ~0,6 ms/token en esta CPU (no depende del tamaño del trozo).
   8 s extra en `ner._clean` por recalcular conjuntos `fold(...)` en cada llamada.
   Ejecutar trozos en paralelo (4–8 hilos × 1 thread de onnxruntime) → ~1,4× más rápido.
3. **Escaneados lentos:** OCR ~5–7 s/pág en páginas densas; la verificación hace un 2º OCR
   de cada página; además `_anonymize_image_page` tarda ~3 s/pág sin contar OCR
   (pendiente de perfilar: sospechosos `pix.set_rect`, capa invisible `insert_text`, JPEG).

### Plan para la próxima sesión (en este orden)
1. [x] `ocr.py`: `Global.use_cls: False` + test (`tests/test_ocr.py`, párrafo 24 del bench
   que antes perdía nombre + DNI). Hecho 2026-10-11.
2. **Verificación que se autocorrige** en escaneados: si el OCR de la página resultante
   encuentra datos, borrar esas cajas en la imagen de salida y volver a verificar
   (máx. 2 vueltas). Si aún quedan → aviso destacado con nº de página.
3. Verificar solo las páginas escaneadas que han cambiado (las que no tenían datos quedan
   idénticas: un 2º OCR no aporta) → casi la mitad de tiempo.
4. Aviso de **líneas con baja confianza del OCR** (score bajo / texto raro) con nº de página.
5. `ner.py`: precalcular conjuntos, trozos en paralelo, no repetir líneas idénticas
   (cabeceras/pies de cada página).
6. Perfilar y acelerar `_anonymize_image_page`.
7. Si una página falla, no abortar todo: sustituirla por una página "[Pàgina N no
   processada]" + aviso (nunca dejarla sin anonimizar).
8. Interfaz: **botón Cancel·la**, progreso por fases ("Analitzant… / Anonimitzant… /
   Verificant… pàgina 12 de 80") con tiempo estimado.
9. Evitar que el ordenador se duerma durante procesos largos (macOS: `caffeinate -i -w
   <pid>`; Windows: `SetThreadExecutionState`).
10. Ventana de sugerencias con buscador (con 80 págs salen ~500 sugerencias).
11. Repetir la medición y añadir un test "documento largo" (marcado lento).
12. Protección del original: comparar también con `os.path.samefile` (en Windows,
    `Demanda.docx` y `demanda.docx` son el mismo fichero) + test.

Después (decidido con el usuario el 2026-10-10):
- **Empaquetado USB** (paso 10).
- **Alternativas sencillas a la IA conversacional** (nuevo paso 9b):
  - Sugerir nombres ya anonimizados en casos anteriores (historial local, cifrado).
  - Revisión final: resaltar palabras con mayúscula no sustituidas para un repaso rápido.
  - Listas por cliente/caso reutilizables (ya existe cargar/guardar lista).
- **LLM local (paso 9): aplazado / opcional.** Aporta poco frente a su coste (2–5 GB,
  memoria, minutos en 80 págs, resultados no deterministas).

## Estado actual
Fase 1 — **Word, PDF, OCR, detector de nombres/empresas/direcciones y guía de
correspondencias, con interfaz en catalán** (140 tests). Ya se puede usar la app:

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
# modelo de nombres (una vez, con internet; ver el propio script):
#   scripts/preparar_models.py  -> models/ner-ca/
.venv/Scripts/python -m pytest
.venv/Scripts/ruff check src tests && .venv/Scripts/ruff format src tests
```

## Pendiente de confirmar con el bufete
- [~] Mac del bufete: **Apple M2** (arm64, Metal). Falta saber la RAM (8/16/24 GB) y los
      PCs Windows. Build de Mac: runner `macos-14` (Apple Silicon) en GitHub Actions.
- [x] Presupuesto: **coste cero** → sin firma de código (en Mac: clic derecho → Abrir la
      primera vez; en Windows: "Más información → Ejecutar igualmente"). PyMuPDF bajo AGPL.
- [ ] Tipos de documento habituales para ampliar el corpus sintético (en catalán).

## Siguientes pasos
1. [x] Estructura del proyecto: `pyproject.toml`, `src/`, venv, ruff, pytest.
2. [x] Corpus sintético (`tests/corpus/generar_corpus.py`).
3. [x] MVP DOCX: sustitución de la lista del usuario conservando el formato.
4. [x] Detector regex español + sugerencias + verificación final.
5. [x] Ventana única PySide6 en catalán (fichero + arrastrar, idioma, tabla con desplegable
       editable, cargar/guardar lista, guardar como, diálogo de sugerencias, resultado).
6. [x] PDF de texto con redacción real (+ aviso de páginas escaneadas y PDF protegidos).
7. [x] PDF escaneado con OCR (RapidOCR, catalán) + borrado de píxeles + verificación.
8. [x] Detector de personas y empresas (AINA, ONNX) + direcciones por reglas + unión de
       variantes + guía de correspondencias.
9. [ ] ~~LLM local de revisión~~ **APLAZADO/opcional** (ver «Dónde nos quedamos»);
       en su lugar 9b: historial de nombres + revisión final resaltada. (desactivable por RAM) — evaluar Salamandra (BSC) vs. Qwen3
       en catalán. ← SIGUIENTE
10. [ ] GitHub Actions: build Mac + Windows; prueba desde USB en equipos limpios. Incluir en
       el paquete `codigo_fuente/` + textos de licencias (AGPL/LGPL), ver `docs/LICENCIAS.md`.
11. [ ] Mapa cifrado y des-anonimización de respuestas (fase 2).

## Limitaciones conocidas
- El detector de nombres se ha evaluado con 25 frases inventadas + 9 de control: conviene
  probarlo con documentos reales del bufete (en local) y ampliar el corpus con los fallos.
- Imágenes incrustadas (Word y PDF) no se anonimizan: se avisa al usuario.
- OCR: puede fallar con letra manuscrita, sellos o imágenes de mala calidad (se avisa).
  Páginas giradas 90° dentro de la imagen (no mediante /Rotate) no se leen bien.
- Imágenes pequeñas dentro de páginas con texto (p. ej. foto de un DNI) no pasan por OCR.
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
- 2026-10-10: PDF escaneado: OCR local con RapidOCR (catalán), borrado de píxeles, página
  rehecha con imagen limpia + alias + capa de texto invisible anonimizada, verificación
  con segundo OCR, progreso en la ventana, caché de OCR en memoria.
- 2026-10-10: Detector de nombres: comparativa de 5 modelos libres en catalán; elegido
  AINA (32/32) convertido a ONNX int8; direcciones por reglas (7/7); filtros de
  organismos públicos, tratamientos y papeles procesales; unión de variantes de un
  mismo nombre; guía de correspondencias confidencial (.docx) con términos no encontrados.
