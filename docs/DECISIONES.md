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
| 2026-10-10 | PyMuPDF para PDF (redacción real) bajo **AGPL-3.0, gratis** (sin licencia comercial) | Es la única librería madura que elimina texto del contenido del PDF; aislada en `pdf_io.py` por si hay que cambiarla |
| 2026-10-10 | OCR con RapidOCR (PP-OCRv6), no Tesseract | Lee bien el catalán (·, à, ç), los modelos van dentro del paquete pip (sin binarios por plataforma ni descargas), Apache-2.0 |
| 2026-10-10 | Toda página cuya imagen cubra ≥50% se rehace desde OCR, ignorando su capa de texto | Una capa de texto ajena puede no coincidir con lo que se ve; más lento pero seguro |
| 2026-10-10 | Verificación de páginas escaneadas con un segundo OCR del resultado | Única forma de comprobar que los píxeles ya no muestran el dato |
| 2026-10-10 | PDF solo se guarda como PDF o .txt (no .docx) | Convertir PDF→Word pierde formato y no aporta para la IA |
| 2026-10-10 | Coste cero: solo licencias libres válidas para uso profesional; nada de terceros en git | Petición del usuario; el bufete lo usa en su trabajo (uso comercial) |
| 2026-10-10 | NER: modelo AINA (RoBERTa catalán) en ONNX int8, no GLiNER ni spaCy | Mejor resultado en la evaluación (32/32 sin falsos positivos tras filtros), el más rápido, sin PyTorch, Apache-2.0 |
| 2026-10-10 | Direcciones por reglas, no por el modelo | Ningún modelo cubría la dirección completa (piso, CP, población) |
| 2026-10-10 | El mismo modelo AINA para castellano | Los modelos oficiales en castellano (PlanTL) se retiraron; AINA acierta en las pruebas en castellano |
| 2026-10-10 | Unir variantes de un nombre sin IA (`merge_variants`) | Las variantes ya se conocen por el matcher; determinista y explicable |
| 2026-10-10 | Guía de correspondencias en .docx junto a la salida, activada por defecto | Registro pedido por el usuario; legible para el bufete; nombre y aviso dejan claro que es confidencial |
| 2026-10-10 | "i"/"y" entre apellidos opcional; `·` forma parte de la palabra; `’` = `'` | Particularidades de los nombres catalanes y del autocorrector de Word |
| 2026-10-10 | LLM local aplazado (opcional a futuro); en su lugar historial de nombres anonimizados + revisión final resaltada | OCR y NER ya cubren lo importante; el LLM cuesta 2–5 GB, mucha memoria, minutos por documento y no es determinista |
| 2026-10-10 | El original nunca se modifica: siempre se escribe un fichero nuevo | Seguridad: no perder el documento original |
