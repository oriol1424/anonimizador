# Progreso

## ▶ DÓNDE NOS QUEDAMOS (2026-10-12) — empezar por aquí
Todo hecho, probado (**337 tests** + 2 lentos con `pytest -m slow`) y publicado. No hay código a medias.

### ⏳ PENDIENTE — lo que falta para entregar el USB (en este orden)
**A. GitHub** — hecho el 2026-10-12. `gh` instalado y con sesión (`C:\Program Files\GitHub CLI\gh.exe`).
- [x] Flujo **tests** en verde en Windows y Mac (fallaba un test en Windows por `relpath`
      entre unidades C:/D: del runner; arreglado).
- [x] **Build** en verde (run 38229421358, ~5 min con el modelo en caché): «RESULTAT: OK»
      en Windows y Mac. Zips en `dist/`.

**B. Montar el USB (en este PC)**
- [x] `fer_usb.py --windows dist/Anonimitzador-Windows.zip --mac dist/Anonimitzador-Mac.zip`
      → `dist/USB/` (702 MB). Autoprueba del .exe del USB en este PC: OK.
- [ ] Copiar el contenido de `dist/USB/` al USB (formato exFAT para que vaya en Windows y Mac).

**C. Probar desde el USB**
- [ ] **MacBook Air M2 (8 GB)**: descomprimir, mover a Aplicaciones, abrir con clic derecho >
      Obre; autoprueba (`--prova`); caso completo con un PDF escaneado; medir tiempos;
      comprobar que no entra en reposo durante un proceso largo (`caffeinate`).
- [ ] **Versión de macOS**: el paquete pide macOS 12+ (`LSMinimumSystemVersion` en el
      .spec), pero Qt/PySide6 6.12 podría exigir 13+: confirmarlo con el build y con la
      versión de los Mac del bufete ( > Quant a aquest Mac). Vale para M1 y M2 (arm64);
      **no para Mac Intel** (haría falta otro build si el bufete tiene alguno).
- [ ] **Windows sin nada instalado**: aviso de SmartScreen, autoprueba, caso completo.
- [ ] Revisar en ambos: tipografía, diálogos de abrir/guardar, botones «Sí/No» traducidos.

**D. Con el bufete**
- [ ] Prueba en local con documentos reales (por el bufete, nunca en este repo) y anotar
      los fallos del detector para ampliar el corpus inventado.
- [ ] Responder `docs/PENDIENTES_BUFETE.md` (formatos CASS, residencia, causas Batllia...).
- [ ] Rellenar en cada equipo la lista «No anonimitzar» (abogados, despacho).

**E. Opcional, más adelante**
- [ ] Tema oscuro; exportar/importar la lista «No anonimitzar»; historial de nombres (9b).
- [ ] Publicar una versión con etiqueta (`git tag v0.2.0 && git push --tags`) para que el
      build quede asociado a la versión.

### Hecho el 2026-10-11 (noche): empaquetado (paso 10)
- **Licencia AGPL-3.0** para el código propio (`LICENSE`; decisión del usuario).
- `packaging/anonimitzador.spec` (PyInstaller `--onedir`): Windows construido y probado
  aquí (473 MB: modelo de nombres 125, OpenCV 114, Qt 96...). Fuera Qml/Quick/teclado
  virtual/visor PDF/red de Qt y OpenGL por software. Traducciones de Qt ca/es (botones «Sí/No»).
- **Autoprueba** `Anonimitzador --prova [resultat.txt]` (`core/selftest.py`): Word y PDF
  inventados (con página escaneada), comprueba OCR, detector de nombres y ventana.
- `.github/workflows/build.yml`: construye y prueba **Windows y Mac (Apple Silicon)** a mano
  o con una etiqueta `v*`; el modelo se convierte allí (caché) y los zip quedan en Artifacts.
- `packaging/fer_usb.py`: carpeta del USB (Windows listo, Mac en zip, código fuente,
  licencias, `LLEGEIX-ME.txt` en catalán con los avisos de Windows/Mac y la autoprueba).
- Pendiente: lanzar el build en GitHub (Actions > build > Run workflow), descargar
  `Anonimitzador-Mac.zip` a `dist/`, volver a ejecutar `fer_usb.py` y **probar en el MacBook
  Air M2** y en un Windows limpio desde el USB.

### Hecho el 2026-10-11 (noche): progreso y salida Markdown (petición del usuario)
- **Progreso global** (%), **tiempo restante** recalibrado con la velocidad real del equipo,
  **tiempo transcurrido** que avanza cada segundo, indicador «Treballant ●●●» y aviso
  tranquilizador si una parte tarda >40 s sin noticias. Estimación previa por fase en
  `core/estimate.py` (tiempos medidos en este PC) y estimación total en el paso 1.
- **Salida Markdown «Per a la IA (.md)»** (recomendada): Word → títulos, listas, negritas,
  enlaces y tablas; PDF → párrafos unidos. El texto final (.md/.txt) también se verifica.
  Se mantiene «Text pla (.txt)».
- **Guía «Com funciona»** (barra lateral y paso 1): pasos, revisión final, tiempos,
  privacidad.

### Hecho el 2026-10-11 (noche): versión 0.2.0 — profesionalización antes del USB
- **Imágenes dentro de Word y PDF** (`core/images.py`): fotos de DNI, escaneados pegados,
  sellos. OCR (ampliando las pequeñas), borrado de píxeles, alias escrito en la imagen y
  verificación con otro OCR. En PDF, solo la zona del dato en páginas con texto. El análisis
  también las lee (sugiere nombres que solo están en una foto). Iconos (<40 px) se ignoran;
  EMF/WMF y objetos incrustados siguen con aviso.
- **Revisió final** (`core/review.py`, `ui/review_dialog.py`): tras anonimizar, palabras
  con mayúscula que siguen en el resultado (sin inicios de frase, alias ni palabras
  habituales de los escritos). Se ven resaltadas; las marcadas se anonimizan volviendo a
  procesar el documento (alias [PERSONA_n], origen «Revisió final» en la guía).
- **Quant a** (versión, licencias de terceros, código fuente) e icono propio de la app.
- **Registro local de errores** (`core/errlog.py`, `errors.log` en la carpeta de
  configuración): tipo de error, versión, sistema, paso y cadena de llamadas; nunca el
  mensaje (podría llevar texto del documento).
- **GitHub Actions** (`.github/workflows/tests.yml`): estilo + tests en Windows y macOS
  (M1) en cada cambio. Sin `gh` en este PC: ver el resultado en la web del repo.

### Hecho el 2026-10-11 (noche): lista «No anonimitzar» (petición del usuario)
- Nombres y datos que **no se anonimizan nunca** (la abogada, el despacho, su dirección,
  teléfono o correo) para que la IA pueda usarlos. Se guardan en este ordenador
  (`%APPDATA%/Anonimitzador/no_anonimitzar.json`; macOS: Application Support) y valen
  para todos los documentos.
- Se edita desde la barra lateral («No anonimitzar · N») o, en las sugerencias,
  seleccionando filas y pulsando «No anonimitzar mai» (se guarda la forma más completa).
- Núcleo: `Term.keep` / `keep_term()`. El matcher los encuentra para que ocupen su sitio
  (el «Soler» de «Montserrat Soler i Vidal» no se toca aunque el cliente sea «Pere
  Soler») pero no los sustituye; no se sugieren, no cuentan como «datos que quedan» y no
  salen en la guía. Se protegen el nombre completo y sus variantes de 2+ palabras; un
  apellido suelto («Sra. Soler») se sigue sugiriendo (regla 7). Si un texto está también
  en la lista del caso, gana la lista (se anonimiza).
- Cambiar la lista obliga a volver a analizar (salvo si se añade desde las sugerencias).

### Hecho el 2026-10-11 (noche): interfaz nueva (propuesta B, elegida por el usuario)
- Propuestas de diseño en un lienzo (A sobria, B asistente por pasos, C oscura):
  https://claude.ai/artifact/H16aPwRUjJ6PJp2hThijEd — el usuario eligió **la B**.
- Ventana con **barra lateral de 4 pasos** (Document → La teva llista → Suggeriments →
  Desa), idioma Català/Castellano y «100% local · sense internet». Los pasos se
  desbloquean en orden; si se cambia la lista, hay que volver a analizar.
- Paso 1: zona para arrastrar + tarjeta del documento (Word / PDF con nº de páginas y
  escaneadas). Un PDF protegido se avisa al elegirlo.
- Paso 3: **sugerencias con buscador** (sin tildes ni mayúsculas) **y filtros por tipo**
  (Persones, Empreses, Documents d'identitat...); «Marca/Desmarca-ho tot» actúa sobre lo
  visible; recuento «N de M marcades». Sustituye al diálogo.
- **Progreso por fases** con página actual, porcentaje, tiempo restante y **Cancel·la**
  (vuelve al paso sin dejar ficheros). **Pantalla de resultado** con avisos (graves
  primero, en rojo), «Obre el document», «Obre la carpeta», «Anonimitza un altre document».
- Estilo: colores sobrios (verde azulado), tipografía del sistema (Segoe UI / San
  Francisco: nada que empaquetar), siempre en claro, iconos dibujados en el código.
- Núcleo: `core/progress.py` (fases + `Cancelled`), progreso en el detector de nombres y
  en todas las páginas del PDF, `pipeline.document_info`.
- Privacidad: los tests **bloquean cualquier conexión de red** (`conftest.no_network`):
  RapidOCR importa `requests` para descargar modelos que falten; con los modelos dentro no
  se conecta, y ahora está comprobado. Consola de RapidOCR solo con errores.
- Capturas de cada pantalla generadas sin abrir ventanas (Qt `offscreen` +
  `QT_QPA_FONTDIR=C:/Windows/Fonts`).

### Hecho el 2026-10-11 (tarde)
- `docs/PENDIENTES_BUFETE.md` enlazado desde `CLAUDE.md`.
- **Demanda andorrana inventada** (`generar_corpus.build_demanda_andorra[_pdf]`, Word y
  PDF) + `tests/test_andorra.py` de extremo a extremo: pasaporte, NRT, CASS, residencia,
  +376, AD500, IBAN AD, matrícula, causa → todo desaparece; Batllia, Comú, CASS, BOPA y
  Cos de Policia se quedan.
- Encontrado con ese test y arreglado:
  - **PDF con ligaduras** ("aﬁliat", "Oﬁcial"): el texto se leía con el glifo "ﬁ" y no
    coincidía con la lista ni con los filtros. Ahora se separan las letras (+ test).
  - El detector sugería **"CASS", "D'ANDORRA", "la Vella"** y "Advocats" como empresas:
    nueva lista `ner.PUBLIC_NAMES` (solo entidad entera) y "advocats" en papeles
    procesales; se quita una " i" suelta al final de un nombre cortado.
- **Detector de nombres más rápido** (análisis Word 80 págs 23 → 14 s; PDF 23 → 17 s):
  listas del filtro normalizadas una sola vez, caché en `text._fold_char` (también acelera
  el matcher: anonimizar PDF 16 → 13 s), trozos en paralelo (`ner.WORKERS` = núcleos,
  máx. 8, 1 hilo de onnxruntime cada uno) y trozos repetidos analizados una vez.
  Resultado idéntico al de antes (1.920/1.920 entidades). Probado sin éxito: lotes de
  varios trozos (no mejora) — el modelo int8 va al límite de la CPU (~0,48 ms/token).
- **Robustez** (`tests/test_robustesa.py`, `tests/test_keep_awake.py`):
  - Una página de PDF que falla (al borrar, al verificar con OCR o al exportar a .txt) se
    sustituye por una página en blanco «[Pàgina N no processada]» y se avisa (aviso grave,
    primero y con icono de error). Nunca se deja la página original.
  - En el análisis, una página ilegible se salta con aviso grave («no s'hi han buscat dades»).
  - Si algo falla a mitad, no queda fichero de salida a medias ni sin verificar.
  - Protección del original con `os.path.samefile` (en macOS "Demanda.docx" =
    "demanda.docx"; en Windows ya lo detectaba `resolve()`); la guía tampoco puede
    sobrescribir el original.
  - El ordenador no se duerme durante las tareas (`core/keep_awake.py`: Windows
    `SetThreadExecutionState`, macOS `caffeinate -i -w`).
  - Test de documento largo (80 págs Word + 40 págs PDF), marcado `slow`.

### Hecho el 2026-10-11
- **Fuga en escaneados arreglada**: OCR sin clasificador de orientación (`use_cls: False`).
- **Verificación que se autocorrige** en escaneados (vuelve a borrar lo que el OCR aún ve,
  máx. 2 vueltas) + aviso destacado con nº de página si queda algo.
- **Escaneados más rápidos** (~12 → ~8 s/pág): borrado con numpy, OCR de 2 páginas a la
  vez, lectura por adelantado y OCR anticipado al elegir el fichero.
- **Aviso de líneas dudosas del OCR** con nº de página (en el análisis y en el resultado).
- Arreglado: una **página escaneada en blanco** rompía el proceso.
- **Andorra**: reglas de NRT, pasaporte (andorrano y de cualquier país tras la palabra
  "passaport"), nº CASS y permiso de residencia (número tras la palabra clave), teléfono
  +376, matrícula "A 1234", CP AD500 en direcciones; organismos andorranos en el filtro.
- Equipo de referencia apuntado: **MacBook Air 2022, M2, 8 GB RAM** (tiene que ir sí o sí).
- Creado **`docs/PENDIENTES_BUFETE.md`**: todo lo que hay que preguntar al bufete
  (formatos CASS/residencia/causas Batllia, países de los pasaportes, equipos Windows...).

### Siguiente (en este orden)
0. [x] Auditoría (`docs/AUDITORIA.md`): graves y medios resueltos el 2026-10-11 (la guía
   sin cifrar se mantiene por decisión del usuario). Menores 12-18 también resueltos.
1. Ver «⏳ PENDIENTE» arriba (GitHub, USB, pruebas en Mac/Windows, bufete).

### Medición (`scripts/bench_documents_grans.py <carpeta> <págs_escaneadas>`)
| Documento | Análisis | Anonimizar + verificar |
|---|---|---|
| Word 80 págs | 14 s (antes 23) | 5 s |
| PDF texto 80 págs | 17 s (antes 23) | 13 s (antes 16) |
| PDF escaneado 10 págs | 40 s | 38 s (sin datos sin borrar) |

80 págs escaneadas ≈ 10 min en este PC (i7-1065G7, 4 núcleos). En el Mac M2 probablemente
menos; falta medirlo allí y probar CoreML.

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
2. [x] **Verificación que se autocorrige** en escaneados (`pdf_io._anonymize_image_page`):
   OCR de la página rehecha, se borra lo encontrado y se repite (máx. 2 vueltas); si aún
   queda algo → aviso `leftovers_scan` con nº de página, primero y con icono de error.
3. [x] Las páginas escaneadas sin datos no se vuelven a pasar por OCR; la verificación
   final del pipeline ya no repite el OCR (revisa la capa de texto invisible).
4. [x] Aviso de **líneas dudosas del OCR** con nº de página (`OcrPage.doubtful_lines`):
   confianza de línea < 0,90 (medido: bien leídas ≥ 0,967; la mal leída 0,714; la
   confianza por palabra no sirve, palabras bien leídas dan 0,53) o línea ancha con muy
   pocas letras. Sale en el análisis (antes de anonimizar) y en el resultado. Sin falsas
   alarmas en escaneados limpios; salta en todas las líneas de un escaneado muy malo.
   Arreglado de paso: una **página escaneada en blanco** rompía el proceso.
5. [x] `ner.py`: precalcular conjuntos, trozos en paralelo, trozos repetidos una vez
   (2026-10-11). Pendiente: medir en el Mac M2 (8 núcleos, debería ganar más).
6. [x] Acelerar escaneados (2026-10-11):
   - `pix.set_rect` iba píxel a píxel desde Python (~2,4 s/pág) → numpy (`ocr.pixels`).
   - Imagen al OCR en memoria (sin PNG).
   - OCR de 2 páginas a la vez (`ocr.WORKERS`, ~0,5 GB por motor; con 4 apenas mejora y
     gasta 2 GB) + lectura por adelantado de las páginas siguientes (`_Prefetch`) + la
     verificación de una página se solapa con la siguiente.
   - OCR anticipado al elegir el fichero (`pipeline.read_ahead`), mientras el usuario
     rellena la lista; se detiene antes de analizar (PyMuPDF no admite dos hilos).
   - Pendiente de decidir: verificar solo las franjas modificadas (~-3 s/pág, pero se
     pierde la "segunda opinión" de releer la página entera). Probar CoreML en el Mac M2.
7. [x] Si una página falla, no abortar todo: sustituirla por una página "[Pàgina N no
   processada]" + aviso (nunca dejarla sin anonimizar).
8. [x] Interfaz: **botón Cancel·la**, progreso por fases ("Analitzant… / Anonimitzant… /
   Verificant… pàgina 12 de 80") con tiempo estimado.
9. [x] Evitar que el ordenador se duerma durante procesos largos (macOS: `caffeinate -i -w
   <pid>`; Windows: `SetThreadExecutionState`).
10. [x] Ventana de sugerencias con buscador (con 80 págs salen ~500 sugerencias).
11. [x] Repetir la medición y añadir un test "documento largo" (marcado lento).
12. [x] Protección del original: comparar también con `os.path.samefile` (en Windows,
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
- [x] Mac del bufete: **MacBook Air 2022, Apple M2, 8 GB RAM** (arm64, Metal). Equipo de
      referencia que tiene que funcionar sí o sí; debe ir también en otros equipos.
- [ ] PCs Windows del bufete (modelo/RAM). Build de Mac: runner `macos-14` (Apple Silicon) en GitHub Actions.
- [x] Presupuesto: **coste cero** → sin firma de código (en Mac: clic derecho → Abrir la
      primera vez; en Windows: "Más información → Ejecutar igualmente"). PyMuPDF bajo AGPL.
- [ ] Tipos de documento habituales para ampliar el corpus sintético (en catalán, Andorra).
- [ ] Otros números andorranos que aparezcan (CASS, permiso de residencia, cens) y formato
      de los números de causa de la Batllia; ¿pasaportes de qué países son habituales?

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
