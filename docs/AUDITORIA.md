# Auditoría interna — 2026-10-11

Revisión del código completo (núcleo, interfaz, reglas innegociables, licencias) con
pruebas empíricas sobre documentos inventados. Marcar `[x]` al resolver cada punto.

## Lo que está bien (comprobado)
- Sin red: ningún código propio abre conexiones; los tests bloquean toda conexión externa.
- Logs: no hay `logging`/`print` con texto del documento (solo la CLI de pruebas imprime).
- Caché del OCR solo en memoria; nada temporal en disco salvo el `.tmp.pdf/.docx` de la
  exportación a texto, que ya está anonimizado y se borra siempre.
- Original nunca sobrescrito (`samefile`), sin salidas a medias, páginas que fallan
  sustituidas, cancelación segura.
- PDF: borrado real (texto eliminado del contenido + píxeles), metadatos y XMP borrados.
- Word: cuerpo, tablas, cuadros de texto, cabeceras, pies, notas, comentarios, control de
  cambios, autores, códigos de campo, hipervínculos y metadatos básicos.
- Rendimiento de la interfaz: 500 sugerencias se muestran en 0,5 s; búsqueda instantánea.
- Fusión de variantes en el flujo real («Jordi Casals i Pons» / «Sr. Casals» / «Casals»).

## Resuelto el 2026-10-11
Puntos 1-3 y 5-11 corregidos con tests en `tests/test_auditoria.py` (y el nombre del
fichero en `tests/test_ui.py`). El nombre de salida se anonimiza en el paso 4 (los "_"
cuentan como separador). El punto 4 queda así por decisión del usuario.

Menores 12-18 resueltos también el 2026-10-11: gráficos/SmartArt, bloques de creación,
customXml, docVars y códigos de campo partidos (Word); páginas con texto en trazos se leen
con OCR (PDF); apellido ambiguo aparte; la guía existente se pregunta antes de
sobrescribirla; la última carpeta ya no se guarda en la configuración del sistema (solo
mientras la app está abierta); licencias indirectas documentadas; aviso si la carpeta de
salida se sincroniza con la nube.

## Hallazgos

### Graves (posible fuga hacia la IA)
1. [x] **Nombre del fichero de salida**: copia el del original. «Demanda Joan Puig.docx» →
   «Demanda Joan Puig_anonimitzat.docx», y el nombre llega a la IA con el fichero.
   Arreglo: en el paso 4, aplicar la lista al nombre (o avisar si contiene algún término).
2. [x] **Word: propiedades personalizadas** (`docProps/custom.xml`, p. ej. «Client = …»)
   no se anonimizan ni las revisa la verificación. Comprobado.
3. [x] **Word: miniatura de la 1ª página** (`docProps/thumbnail.*`) se conserva sin aviso:
   es una imagen de la portada con los nombres. Comprobado. Arreglo: eliminarla.
4. [x] **Decidido por el usuario (2026-10-11): la guía NO se cifra y se guarda en la misma carpeta.** Antes: **Guía de correspondencias sin cifrar** junto al documento anonimizado: la regla 4
   de CLAUDE.md exige cifrado. Riesgo real: adjuntarla a la IA por error. Decidir con el
   usuario: cifrar con contraseña, guardarla en otra carpeta, o ambas.

### Medios
5. [x] **Word: texto alternativo de imágenes** (`descr`/`title`, p. ej. «Foto del DNI de
   …») se conserva. Comprobado.
6. [x] **PDF: texto fuera del recorte visible** (CropBox) se conserva y la verificación no
   lo ve (la extracción recorta). Otras herramientas sí lo leen. Comprobado.
7. [x] **PDF: ficheros adjuntos** se conservan con su contenido (solo aviso genérico de
   «objectes incrustats»). Comprobado. Arreglo: eliminarlos y avisar.
8. [x] **Apellidos de 3 letras** (Mas, Pi, Pou, Gil, Sol...) no generan variante: «el Sr.
   Mas» queda sin sustituir. Comprobado. Arreglo: aceptarlos tras tratamiento (Sr., Sra.,
   senyor, en, na...).
9. [x] **Teléfonos andorranos en parejas** («81 23 45», «+376 81 23 45») no se detectan;
   «376 612 345» (sin +) se detecta a medias y dejaría «345». Comprobado.
10. [x] **DNI/NIE con letra minúscula** («12345678z») no se detectan. Comprobado.
11. [x] **Fechas de nacimiento** no se detectan; «03/04/1980» sale como procedimiento a
    medias («04/1980»). Arreglo: fecha tras «naixement/nascut/nacimiento/nacido» y no
    tomar fechas por números de procedimiento.

### Menores / por revisar (lectura del código, sin prueba)
12. [x] Word: texto de gráficos y SmartArt (`a:t` en partes chart/diagram), bloques de
    creación (glossary), datos de controles de contenido vinculados (`customXml`) y
    variables de documento (`docVars`) no se tratan.
13. [x] Word: códigos de campo partidos en varios fragmentos (`instrText`) se tratan por
    separado; un dato partido no se encontraría.
14. [x] PDF con el texto convertido en trazos (sin texto ni imagen): no se detecta nada.
    Posible arreglo: tratar como escaneada una página con dibujos y sin texto.
15. [x] Dos personas con el mismo apellido: el «Puig» suelto se une a la primera
    sugerencia («Joan Puig») en vez de quedar aparte. No es fuga, pero confunde a la IA.
16. [x] La guía se sobrescribe sin preguntar si ya existe; `QSettings` guarda la última
    carpeta, cuyo nombre puede ser el del cliente.
17. [x] Licencias: faltan en `docs/LICENCIAS.md` las dependencias indirectas (OpenCV,
    Shapely, Pillow, requests, protobuf, omegaconf, pyclipper, tqdm, certifi...; todas
    gratuitas para uso profesional). El entorno de desarrollo tiene PySide6 completo (con
    WebEngine/Chromium): el paquete debe llevar solo PySide6-Essentials.
18. [x] Si la carpeta de salida está sincronizada (OneDrive...), la guía sube a la nube.
    Avisar o proponer otra carpeta por defecto para la guía.
