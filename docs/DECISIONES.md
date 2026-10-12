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
| 2026-10-10 | Listas de términos por caso en .json elegido por el usuario; QSettings solo guarda la última carpeta (sustituido el 2026-10-11: ya no se guarda nada) | Reutilizar listas sin que la app guarde datos personales por su cuenta |
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
| 2026-10-11 | OCR sin clasificador de orientación (`Global.use_cls: False`) | Giraba 180° líneas correctas y las leía mal: un nombre + DNI quedaban sin borrar |
| 2026-10-11 | Páginas escaneadas: verificar con OCR dentro de `anonymize` y volver a borrar lo encontrado (máx. 2 vueltas); si aún queda algo, aviso destacado con nº de página | Corregir en vez de solo avisar; el aviso indica dónde mirar |
| 2026-10-11 | No se repite el OCR de páginas escaneadas sin datos ni en la verificación final (se revisa su capa de texto) | La imagen no cambia: otro OCR no aporta y duplica el tiempo |
| 2026-10-11 | Equipo de referencia: MacBook Air 2022, M2, 8 GB RAM; debe funcionar en otros equipos | Es el equipo del bufete; puede cambiar |
| 2026-10-11 | OCR de 2 páginas en paralelo (no más) | Medido: 2 → ~1,2× con 1,3 GB; 4 → ~1,3× con 2 GB. Prioridad: que vaya bien en el Mac de 8 GB |
| 2026-10-11 | OCR anticipado al elegir un PDF, detenido antes de analizar | El tiempo de rellenar la lista se aprovecha; PyMuPDF no es seguro con dos hilos |
| 2026-10-11 | Se mantiene la verificación con OCR de la página entera | Es más lenta que releer solo lo modificado, pero puede detectar líneas mal leídas la primera vez |
| 2026-10-11 | Aviso de líneas dudosas del OCR por confianza de línea (< 0,90) y densidad de letras, no por palabra | La confianza por palabra es ruidosa (palabras correctas con 0,53); la de línea separa bien |
| 2026-10-11 | Reglas andorranas: NRT, pasaporte (andorrano y cualquier número tras "passaport/pasaporte/passeport/passport"), teléfono +376, matrícula, CP AD500 | El bufete es de Andorra: allí se usa sobre todo el pasaporte. Formatos de fuentes no oficiales (python-stdnum, Wikipedia, MoraBanc 2017): confirmar con el bufete |
| 2026-10-11 | Organismos andorranos en el filtro del detector, sin prefijos cortos ("comú d", no "comú") | El filtro compara el inicio sin acentos: "comú" descartaría "Comunicacions... SL" |
| 2026-10-11 | PDF: las ligaduras ("ﬁ", "ﬂ") se separan en letras al leer el texto (sin `TEXT_PRESERVE_LIGATURES`) | Con ligaduras "Oﬁcial" o "Griﬃn" no coincidían con la lista ni con los filtros; la 1ª letra se queda la caja del glifo y el borrado lo cubre entero |
| 2026-10-11 | Lista aparte de nombres públicos que solo se descartan si son la entidad entera (CASS, BOPA, Andorra, parroquias) | Como prefijo quitarían empresas reales ("Cassany SL"); el modelo tomaba "CASS" o "la Vella" por empresas |
| 2026-10-11 | Detector de nombres: trozos en paralelo (hilos = núcleos, máx. 8) con 1 hilo de onnxruntime por trozo, en vez de un trozo cada vez con todos los hilos | Medido 16,2 → 13,2 s en 4 núcleos; los lotes no mejoran. Mismo resultado exacto |
| 2026-10-11 | Página de PDF que falla → se borra y se sustituye por una página en blanco «[Pàgina N no processada]» con aviso grave; no se aborta todo | Un documento de 80 págs no debe perderse por una página dañada, y nunca puede quedar la página original sin anonimizar |
| 2026-10-11 | Si `anonymize` falla a mitad, se borra la salida | Mejor no tener fichero que tener uno a medias o sin verificar |
| 2026-10-11 | Evitar el reposo durante las tareas (SetThreadExecutionState / caffeinate), sin impedir que se apague la pantalla | 80 págs escaneadas ≈ 10 min: si el equipo se duerme, el usuario cree que se ha colgado |
| 2026-10-11 | Tests lentos marcados `slow` y excluidos por defecto (`pytest -m slow`) | La suite normal sigue en ~1 min |
| 2026-10-11 | Interfaz: propuesta B (asistente de 4 pasos con barra lateral), elegida por el usuario entre 3 propuestas | Una tarea por pantalla: lo más fácil de seguir para un usuario no técnico; las sugerencias pasan a ser un paso con buscador |
| 2026-10-11 | Tipografía del sistema (Segoe UI / San Francisco), no fuentes empaquetadas | Aspecto nativo y profesional sin ficheros de terceros ni licencias que anotar |
| 2026-10-11 | Interfaz siempre en claro (Fusion + paleta fija) | Con el modo oscuro del sistema, Qt mezclaba colores; el tema oscuro queda como opcional |
| 2026-10-11 | Progreso por fases con códigos (`read`, `detect`, `anonymize`, `verify`, `export`) y cancelación lanzando `Cancelled` (BaseException) desde la función de progreso | El núcleo no conoce la interfaz; la cancelación atraviesa la protección de páginas que fallan y borra la salida a medias |
| 2026-10-11 | Los tests bloquean toda conexión de red fuera del equipo | RapidOCR trae código de descarga de modelos: así se comprueba la regla 1 en cada ejecución |
| 2026-10-11 | Lista «No anonimitzar» (abogados, despacho) como términos `keep` dentro del matcher, no como filtro aparte | Así ocupan su sitio y ninguna variante de otro término los sustituye a medias; sustitución, verificación y guía los respetan sin código extra |
| 2026-10-11 | De la lista «No anonimitzar» solo se protegen el nombre completo y variantes de 2+ palabras; la lista del caso gana si hay conflicto | Un apellido suelto puede ser de un cliente: ante la duda se anonimiza (regla 7) |
| 2026-10-11 | La lista «No anonimitzar» se guarda sin cifrar en la configuración del usuario | Son datos del propio despacho (no de clientes) que el bufete quiere justamente mostrar a la IA; nunca sale del equipo |
| 2026-10-11 | La guía de correspondencias no se cifra y se guarda en la misma carpeta que el documento anonimizado | Decisión del usuario tras la auditoría (excepción a la regla 4) |
| 2026-10-11 | El nombre del fichero de salida se anonimiza con la misma lista | El nombre llega a la IA junto con el documento |
| 2026-10-11 | Word: se quitan la miniatura y se anonimizan propiedades personalizadas y texto alternativo; PDF: se trabaja con la página entera (sin recorte) y se quitan los adjuntos | Fugas comprobadas en la auditoría; los adjuntos no se pueden revisar |
| 2026-10-11 | Apellidos de 2-3 letras (Mas, Pi, Pou) solo como variante tras un tratamiento (Sr., Sra., en, na...) | Solos son palabras corrientes («mas», «pi»); tras un tratamiento son el apellido |
| 2026-10-11 | La última carpeta usada solo se recuerda mientras la app está abierta (sin QSettings) | Su nombre suele ser el del cliente y quedaba en el registro / preferencias del sistema |
| 2026-10-11 | PDF sin texto con ≥150 curvas se trata como escaneado (OCR) | Texto convertido en trazos: si no, no se detectaría nada. Las tablas son rectas y no cuentan |
| 2026-10-11 | Un apellido suelto que encaja con varias personas queda como sugerencia aparte | No se puede saber de quién es: unirlo a una daría a la IA una identidad equivocada |
| 2026-10-11 | Aviso (no bloqueo) si la carpeta de salida está en OneDrive/Dropbox/iCloud y la guía está marcada | La guía va sin cifrar por decisión del usuario; que sepa que subirá a la nube |
| 2026-10-11 | Imágenes sueltas en Word/PDF se leen con OCR y se borran (antes solo se avisaba) | Un DNI escaneado pegado en un Word es habitual en los escritos; el aviso genérico no protegía |
| 2026-10-11 | Revisión final por reglas (mayúsculas no sustituidas), sin IA | Red de seguridad rápida y explicable contra los falsos negativos del detector |
| 2026-10-11 | Registro de errores local sin el mensaje de la excepción | Permite diagnosticar en el bufete sin incumplir la regla 3 (el mensaje puede llevar texto) |
| 2026-10-11 | Tests en GitHub Actions (Windows + macOS) | Detectar fallos de una plataforma antes de empaquetar; mismo sistema que el build del USB |
| 2026-10-11 | Salida Markdown (.md) recomendada para la IA; .txt se mantiene | Conserva títulos, listas y tablas (la IA entiende mejor la estructura); es texto, igual de seguro |
| 2026-10-11 | Porcentaje global ponderado por la duración estimada de cada fase y ETA recalibrada con lo transcurrido | Un % por fase confundía (volvía a 0); los tiempos varían mucho entre equipos |
| 2026-10-11 | Código propio bajo AGPL-3.0 | Obligatorio al distribuir con PyMuPDF (AGPL) sin pagar la licencia comercial; decisión del usuario |
| 2026-10-11 | Paquete PyInstaller --onedir; Mac construido en GitHub Actions (macos-14) | Qt enlazado dinámicamente (LGPL); el .app de Mac no se puede compilar desde Windows |
| 2026-10-11 | En el USB, el Mac va como .zip (no como .app suelto) | Un USB FAT/exFAT pierde permisos y enlaces del .app; descomprimir en el Mac los conserva |
| 2026-10-11 | Autoprueba integrada (`--prova`) en vez de solo tests | Verifica el paquete real (modelos, Qt, OCR) en GitHub y en los equipos del bufete |
| 2026-10-12 | Modelo NER cuantizado con pesos uint8 (QUInt8), no int8 con signo | Con QInt8 el detector no encontraba NADA en CPU x86 sin VNNI (AMD EPYC 7763 en GitHub; también Intel de sobremesa hasta 10ª gen. y Ryzen antiguos): desbordamiento u8×s8. uint8 es igual de preciso (más cercano al modelo sin cuantizar) y ~1,7× más lento en la fase de nombres |
| 2026-10-12 | Comprobación del detector al cargarlo (frase con un nombre evidente) + aviso grave «ner_broken» | Si el modelo falla en un equipo, el usuario lo sabe en vez de recibir cero sugerencias de nombres sin aviso (regla 7) |
