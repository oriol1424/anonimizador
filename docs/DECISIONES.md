# Registro de decisiones

| Fecha      | Decisión | Motivo |
|------------|----------|--------|
| 2026-10-10 | App de escritorio Python + PySide6, empaquetada con PyInstaller | Usuario no técnico, entrega por USB, todo local |
| 2026-10-10 | LLM embebido con llama-cpp-python (no Ollama) | Ollama requiere instalación y un servicio; llama.cpp va dentro de la app |
| 2026-10-10 | Detección en capas (usuario → regex → NER → LLM) | Un LLM pequeño solo no es fiable ni rápido; las reglas cubren lo estructurado |
| 2026-10-10 | El LLM solo sugiere, el usuario confirma | Responsabilidad profesional y errores del modelo |
| 2026-10-10 | Multiplataforma macOS + Windows | El bufete usará Mac y algún Windows |
| 2026-10-10 | Builds con GitHub Actions | No se puede generar el .app de Mac desde Windows |
| 2026-10-10 | Soporte OCR (RapidOCR propuesto) | Llegarán PDFs escaneados |
| 2026-10-10 | Ventana única; sustituto con desplegable editable | Petición del cliente: sencillez |
| 2026-10-10 | Repo: https://github.com/oriol1424/anonimizador | Publicación del progreso |
| 2026-10-10 | `.claude/` fuera del repo | Los permisos son locales; por seguridad no se publican |
| 2026-10-10 | Word se procesa a nivel XML (lxml), no con la API de párrafos de python-docx | La API no ve hipervínculos, control de cambios, comentarios ni cuadros de texto |
| 2026-10-10 | Variantes parciales ("Pérez") solo si empiezan en mayúscula | Evitar sustituir palabras comunes ("mayor de edad") |
| 2026-10-10 | Variantes compartidas entre dos personas no se aplican y se avisa | Sustituir "Sr. Pérez" con el alias equivocado sería un error grave |
| 2026-10-10 | Verificación final releyendo el documento de salida | Red de seguridad ante cualquier caso no previsto |
| 2026-10-10 | Las reglas (DNI, IBAN...) generan sugerencias, no sustituciones automáticas | El usuario decide; criterio único para todas las capas automáticas |
| 2026-10-10 | Catalán como idioma por defecto; castellano seleccionable | ~99,99% de los documentos del bufete están en catalán |
| 2026-10-10 | El matcher acepta partículas de ambos idiomas siempre; el idioma solo cambia alias/presets (y luego NER/LLM) | Hay documentos que mezclan idiomas; no conviene que una opción mal puesta deje pasar un nombre |
| 2026-10-10 | Alias sin tildes ni caracteres especiales (`[ADRECA_1]`, `[TELEFON_1]`) | Que sobrevivan intactos a la IA y se puedan revertir después |
| 2026-10-10 | Interfaz en catalán; cambia a castellano junto con el idioma del documento | Petición del cliente; un solo selector, más sencillo |
| 2026-10-10 | El núcleo devuelve `Notice`/`AnonymizerError` con código, la UI los traduce | Separar lógica y textos; mensajes siempre en el idioma de la interfaz |
| 2026-10-10 | Listas de términos por caso en .json elegido por el usuario; QSettings solo guarda la última carpeta | Reutilizar listas sin que la app guarde datos personales por su cuenta |
| 2026-10-10 | PyMuPDF para PDF (redacción real). **Licencia AGPL-3.0 / comercial: PENDIENTE de validar** | Es la única librería madura que elimina texto del contenido del PDF; aislada en `pdf_io.py` por si hay que cambiarla |
| 2026-10-10 | Las páginas escaneadas no se procesan hasta tener OCR y se avisa con un mensaje destacado | Mejor un aviso claro que una falsa sensación de seguridad |
| 2026-10-10 | PDF solo se guarda como PDF o .txt (no .docx) | Convertir PDF→Word pierde formato y no aporta para la IA |
| 2026-10-10 | "i"/"y" entre apellidos opcional; `·` forma parte de la palabra; `’` = `'` | Particularidades de los nombres catalanes y del autocorrector de Word |
