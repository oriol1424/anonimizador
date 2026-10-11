"""Textos visibles para el usuario. Catalán por defecto, castellano como alternativa."""

STRINGS: dict[str, dict[str, str]] = {
    # Ventana principal
    "app_title": {"ca": "Anonimitzador", "es": "Anonimizador"},
    "document": {"ca": "Document", "es": "Documento"},
    "no_file": {
        "ca": "Cap fitxer seleccionat (també el pots arrossegar aquí)",
        "es": "Ningún fichero seleccionado (también puedes arrastrarlo aquí)",
    },
    "choose_file": {"ca": "Tria el fitxer…", "es": "Elegir fichero…"},
    "language": {"ca": "Idioma del document:", "es": "Idioma del documento:"},
    "terms": {"ca": "Què cal anonimitzar", "es": "Qué anonimizar"},
    "col_original": {"ca": "Text original", "es": "Texto original"},
    "col_replacement": {"ca": "Substituir per", "es": "Sustituir por"},
    "add_row": {"ca": "+ Afegeix", "es": "+ Añadir"},
    "remove_row": {"ca": "− Elimina", "es": "− Quitar"},
    "load_list": {"ca": "Carrega llista…", "es": "Cargar lista…"},
    "save_list": {"ca": "Desa llista…", "es": "Guardar lista…"},
    "terms_hint": {
        "ca": "Escriu el nom complet (p. ex. «Joan Puig i Ferrer»). També se substituiran "
        "formes com «Sr. Puig» o «J. Puig Ferrer».",
        "es": "Escribe el nombre completo (p. ej. «Juan Pérez García»). También se sustituirán "
        "formas como «Sr. Pérez» o «J. Pérez García».",
    },
    "save_as": {"ca": "Desa com a", "es": "Guardar como"},
    "folder": {"ca": "Carpeta:", "es": "Carpeta:"},
    "choose_folder": {"ca": "Tria…", "es": "Elegir…"},
    "file_name": {"ca": "Nom:", "es": "Nombre:"},
    "format": {"ca": "Format:", "es": "Formato:"},
    "format_docx": {"ca": "Word (.docx)", "es": "Word (.docx)"},
    "format_pdf": {"ca": "PDF (.pdf)", "es": "PDF (.pdf)"},
    "format_txt": {
        "ca": "Text (.txt) — per enganxar a la IA",
        "es": "Texto (.txt) — para pegar en la IA",
    },
    "anonymize": {"ca": "Anonimitza", "es": "Anonimizar"},
    "working": {"ca": "Treballant…", "es": "Trabajando…"},
    "ocr_progress": {
        "ca": "Llegint pàgines escanejades… {done}/{total}",
        "es": "Leyendo páginas escaneadas… {done}/{total}",
    },
    "anonymized_suffix": {"ca": "_anonimitzat", "es": "_anonimizado"},
    "input_filter": {
        "ca": "Documents Word o PDF (*.docx *.pdf)",
        "es": "Documentos Word o PDF (*.docx *.pdf)",
    },
    "list_filter": {"ca": "Llista de termes (*.json)", "es": "Lista de términos (*.json)"},
    # Validaciones
    "err_title": {"ca": "Falta informació", "es": "Falta información"},
    "err_no_file": {"ca": "Tria primer el document.", "es": "Elige primero el documento."},
    "err_no_folder": {"ca": "Tria la carpeta on desar-lo.", "es": "Elige la carpeta de destino."},
    "err_no_name": {
        "ca": "Escriu un nom per al fitxer.",
        "es": "Escribe un nombre para el fichero.",
    },
    "err_empty_replacement": {
        "ca": "Falta el text de substitució per a «{original}».",
        "es": "Falta el texto de sustitución para «{original}».",
    },
    "overwrite_title": {"ca": "El fitxer ja existeix", "es": "El fichero ya existe"},
    "overwrite": {"ca": "Vols substituir «{name}»?", "es": "¿Quieres reemplazar «{name}»?"},
    "error_title": {"ca": "Error", "es": "Error"},
    "error_unexpected": {
        "ca": "No s'ha pogut processar el document:\n{detail}",
        "es": "No se ha podido procesar el documento:\n{detail}",
    },
    "error_bad_list": {
        "ca": "El fitxer no és una llista de termes vàlida.",
        "es": "El fichero no es una lista de términos válida.",
    },
    # Errores del núcleo
    "error_unsupported_input": {
        "ca": "Format no admès encara: {suffix}",
        "es": "Formato no soportado todavía: {suffix}",
    },
    "error_unsupported_output": {
        "ca": "Format de sortida no admès: {suffix}",
        "es": "Formato de salida no soportado: {suffix}",
    },
    "error_encrypted": {
        "ca": "El PDF està protegit amb contrasenya. Desa'n una còpia sense protecció i "
        "torna-ho a provar.",
        "es": "El PDF está protegido con contraseña. Guarda una copia sin protección y "
        "vuelve a intentarlo.",
    },
    "error_same_file": {
        "ca": "El fitxer de sortida no pot ser el mateix que l'original.",
        "es": "El fichero de salida no puede ser el mismo que el original.",
    },
    # Avisos del núcleo
    "notice_ambiguous": {
        "ca": "«{detail}» coincideix amb diverses persones amb substituts diferents i no s'ha "
        "substituït automàticament. Afegeix-lo a la llista amb el substitut correcte.",
        "es": "«{detail}» coincide con varias personas con sustitutos distintos y no se ha "
        "sustituido automáticamente. Añádelo a la lista con el sustituto correcto.",
    },
    "notice_leftovers": {
        "ca": "Verificació: queden {count} aparicions sense substituir ({detail}). "
        "Revisa el document.",
        "es": "Verificación: quedan {count} apariciones sin sustituir ({detail}). "
        "Revisa el documento.",
    },
    "notice_leftovers_scan": {
        "ca": "ATENCIÓ: a les pàgines escanejades {pages} encara es llegeixen {count} dades "
        "que no s'han pogut esborrar ({detail}). Revisa aquestes pàgines abans de fer "
        "servir el document.",
        "es": "ATENCIÓN: en las páginas escaneadas {pages} todavía se leen {count} datos "
        "que no se han podido borrar ({detail}). Revisa esas páginas antes de usar el "
        "documento.",
    },
    "notice_failed_pages": {
        "ca": "ATENCIÓ: no s'han pogut processar les pàgines {pages}. S'han substituït per "
        "una pàgina en blanc amb l'avís «Pàgina no processada», així que el document no "
        "les inclou. Revisa-les a l'original.",
        "es": "ATENCIÓN: no se han podido procesar las páginas {pages}. Se han sustituido por "
        "una página en blanco con el aviso «Página no procesada», así que el documento no "
        "las incluye. Revísalas en el original.",
    },
    "notice_unreadable_pages": {
        "ca": "ATENCIÓ: no s'han pogut llegir les pàgines {pages} i no s'hi han buscat dades. "
        "Revisa-les a l'original i afegeix a la llista els noms i dades que hi apareguin.",
        "es": "ATENCIÓN: no se han podido leer las páginas {pages} y no se han buscado datos "
        "en ellas. Revísalas en el original y añade a la lista los nombres y datos que "
        "aparezcan.",
    },
    "notice_ocr_doubtful": {
        "ca": "El reconeixement de text (OCR) no està segur de {count} línies (pàgines "
        "{pages}). Comprova-les a l'original: si hi ha noms o dades, afegeix-los a la llista.",
        "es": "El reconocimiento de texto (OCR) no está seguro de {count} líneas (páginas "
        "{pages}). Compruébalas en el original: si hay nombres o datos, añádelos a la lista.",
    },
    "notice_images": {
        "ca": "El document conté {count} imatges o objectes que no es poden llegir (dibuixos "
        "EMF/WMF, fulls de càlcul o documents incrustats). No s'anonimitzen: revisa'ls.",
        "es": "El documento contiene {count} imágenes u objetos que no se pueden leer "
        "(dibujos EMF/WMF, hojas de cálculo o documentos incrustados). No se anonimizan: "
        "revísalos.",
    },
    "notice_images_ocr": {
        "ca": "S'han llegit {count} imatges amb reconeixement de text (OCR) i s'hi han esborrat "
        "les dades trobades. Revisa-les: amb lletra manuscrita o mala qualitat pot fallar.",
        "es": "Se han leído {count} imágenes con reconocimiento de texto (OCR) y se han borrado "
        "los datos encontrados. Revísalas: con letra manuscrita o mala calidad puede fallar.",
    },
    "notice_leftovers_images": {
        "ca": "ATENCIÓ: en algunes imatges encara es llegeixen {count} dades que no s'han pogut "
        "esborrar ({detail}). Revisa les imatges abans de fer servir el document.",
        "es": "ATENCIÓN: en algunas imágenes todavía se leen {count} datos que no se han podido "
        "borrar ({detail}). Revisa las imágenes antes de usar el documento.",
    },
    "notice_attachments_removed": {
        "ca": "S'han tret {count} fitxers adjunts del PDF: el seu contingut no es pot revisar. "
        "Si els necessites, anonimitza'ls a part.",
        "es": "Se han quitado {count} ficheros adjuntos del PDF: su contenido no se puede "
        "revisar. Si los necesitas, anonimízalos aparte.",
    },
    "notice_ocr": {
        "ca": "{count} pàgines escanejades s'han llegit amb reconeixement de text (OCR). "
        "Revisa-les: amb lletra manuscrita, segells o mala qualitat d'imatge pot fallar.",
        "es": "{count} páginas escaneadas se han leído con reconocimiento de texto (OCR). "
        "Revísalas: con letra manuscrita, sellos o mala calidad de imagen puede fallar.",
    },
    "notice_ner_unavailable": {
        "ca": "El detector de noms i empreses no està instal·lat: només s'han buscat dades "
        "com DNI, telèfons o adreces. Revisa els noms manualment.",
        "es": "El detector de nombres y empresas no está instalado: solo se han buscado datos "
        "como DNI, teléfonos o direcciones. Revisa los nombres manualmente.",
    },
    # Diálogo de sugerencias
    "sugg_title": {"ca": "Revisa els suggeriments", "es": "Revisa las sugerencias"},
    "sugg_intro": {
        "ca": "He trobat aquestes dades que no eren a la teva llista. Marca les que vols "
        "substituir i, si cal, canvia el substitut.",
        "es": "He encontrado estos datos que no estaban en tu lista. Marca los que quieres "
        "sustituir y, si hace falta, cambia el sustituto.",
    },
    "col_apply": {"ca": "Aplicar", "es": "Aplicar"},
    "col_type": {"ca": "Tipus", "es": "Tipo"},
    "col_found": {"ca": "Text trobat", "es": "Texto encontrado"},
    "col_count": {"ca": "Vegades", "es": "Veces"},
    "select_all": {"ca": "Marca-ho tot", "es": "Marcar todo"},
    "select_none": {"ca": "Desmarca-ho tot", "es": "Desmarcar todo"},
    "apply_and_save": {"ca": "Aplica i desa", "es": "Aplicar y guardar"},
    "cancel": {"ca": "Cancel·la", "es": "Cancelar"},
    "warnings": {"ca": "Atenció", "es": "Atención"},
    # Tipos de dato
    "label_DNI": {"ca": "DNI", "es": "DNI"},
    "label_NIE": {"ca": "NIE", "es": "NIE"},
    "label_CIF": {"ca": "NIF empresa", "es": "CIF"},
    "label_NRT": {"ca": "NRT (Andorra)", "es": "NRT (Andorra)"},
    "label_PASAPORTE": {"ca": "Passaport", "es": "Pasaporte"},
    "label_CASS": {"ca": "Núm. CASS", "es": "Nº CASS"},
    "label_RESIDENCIA": {"ca": "Permís de residència", "es": "Permiso de residencia"},
    "label_NACIMIENTO": {"ca": "Data de naixement", "es": "Fecha de nacimiento"},
    "label_IBAN": {"ca": "Compte bancari", "es": "Cuenta bancaria"},
    "label_TELEFONO": {"ca": "Telèfon", "es": "Teléfono"},
    "label_EMAIL": {"ca": "Correu electrònic", "es": "Correo electrónico"},
    "label_MATRICULA": {"ca": "Matrícula", "es": "Matrícula"},
    "label_PROCEDIMIENTO": {"ca": "Núm. procediment", "es": "Nº procedimiento"},
    "label_DIRECCION": {"ca": "Adreça", "es": "Dirección"},
    "label_PERSONA": {"ca": "Persona", "es": "Persona"},
    "label_EMPRESA": {"ca": "Empresa / entitat", "es": "Empresa / entidad"},
    # Guía de correspondencias
    "save_guide": {
        "ca": "Desa també la guia de correspondències (confidencial: conté els noms reals)",
        "es": "Guardar también la guía de correspondencias (confidencial: contiene los nombres "
        "reales)",
    },
    "guide_suffix": {"ca": "_GUIA_CONFIDENCIAL", "es": "_GUIA_CONFIDENCIAL"},
    "guide_title": {"ca": "Guia de correspondències", "es": "Guía de correspondencias"},
    "guide_warning": {
        "ca": "CONFIDENCIAL: aquest fitxer conté les dades reals. No el comparteixis ni el "
        "pugis a cap IA. Guarda'l només al despatx.",
        "es": "CONFIDENCIAL: este fichero contiene los datos reales. No lo compartas ni lo "
        "subas a ninguna IA. Guárdalo solo en el despacho.",
    },
    "guide_source": {"ca": "Document original", "es": "Documento original"},
    "guide_output": {"ca": "Document anonimitzat", "es": "Documento anonimizado"},
    "guide_date": {"ca": "Data", "es": "Fecha"},
    "guide_col_alias": {"ca": "Substitut", "es": "Sustituto"},
    "guide_col_original": {"ca": "Text original", "es": "Texto original"},
    "guide_col_found": {"ca": "Formes trobades (vegades)", "es": "Formas encontradas (veces)"},
    "guide_col_type": {"ca": "Origen", "es": "Origen"},
    "guide_col_count": {"ca": "Total", "es": "Total"},
    "guide_type_user": {"ca": "La teva llista", "es": "Tu lista"},
    "guide_not_found": {
        "ca": "No trobat al document (revisa com està escrit)",
        "es": "No encontrado en el documento (revisa cómo está escrito)",
    },
    "guide_saved": {
        "ca": "Guia de correspondències (confidencial):\n{path}",
        "es": "Guía de correspondencias (confidencial):\n{path}",
    },
    # Pasos (barra lateral)
    "step_document": {"ca": "Document", "es": "Documento"},
    "step_terms": {"ca": "La teva llista", "es": "Tu lista"},
    "step_suggestions": {"ca": "Suggeriments", "es": "Sugerencias"},
    "step_save": {"ca": "Desa", "es": "Guardar"},
    "local_badge": {"ca": "100% local · sense internet", "es": "100% local · sin internet"},
    "back": {"ca": "Enrere", "es": "Atrás"},
    "continue": {"ca": "Continua", "es": "Continuar"},
    # Paso 1: documento
    "doc_title": {"ca": "Tria el document", "es": "Elige el documento"},
    "doc_intro": {
        "ca": "El document original no es modifica mai: es desa una còpia anonimitzada.",
        "es": "El documento original nunca se modifica: se guarda una copia anonimizada.",
    },
    "drop_here": {
        "ca": "Arrossega aquí un document Word o PDF",
        "es": "Arrastra aquí un documento Word o PDF",
    },
    "drop_or": {"ca": "o bé", "es": "o bien"},
    "change_file": {"ca": "Canvia el fitxer…", "es": "Cambiar fichero…"},
    "file_word": {"ca": "Document Word", "es": "Documento Word"},
    "file_pdf": {"ca": "PDF · {pages} pàgines", "es": "PDF · {pages} páginas"},
    "file_pdf_scanned": {
        "ca": "PDF · {pages} pàgines ({scanned} escanejades)",
        "es": "PDF · {pages} páginas ({scanned} escaneadas)",
    },
    # Paso 2: lista
    "analyze": {"ca": "Analitza el document", "es": "Analizar el documento"},
    # Paso 3: sugerencias
    "sugg_found": {
        "ca": "He trobat {count} dades que no eren a la teva llista. Marca les que vols "
        "substituir i, si cal, canvia el substitut.",
        "es": "He encontrado {count} datos que no estaban en tu lista. Marca los que quieres "
        "sustituir y, si hace falta, cambia el sustituto.",
    },
    "sugg_none": {
        "ca": "No he trobat cap altra dada a part de la teva llista.",
        "es": "No he encontrado ningún otro dato aparte de tu lista.",
    },
    "search": {"ca": "Cerca un nom o una dada…", "es": "Busca un nombre o un dato…"},
    "filter_all": {"ca": "Tots", "es": "Todos"},
    "group_people": {"ca": "Persones", "es": "Personas"},
    "group_companies": {"ca": "Empreses", "es": "Empresas"},
    "group_ids": {"ca": "Documents d'identitat", "es": "Documentos de identidad"},
    "group_contact": {"ca": "Telèfons i correus", "es": "Teléfonos y correos"},
    "group_addresses": {"ca": "Adreces", "es": "Direcciones"},
    "group_other": {"ca": "Altres", "es": "Otros"},
    "marked_count": {"ca": "{checked} de {total} marcades", "es": "{checked} de {total} marcadas"},
    "apply_continue": {"ca": "Aplica i continua", "es": "Aplicar y continuar"},
    # Paso 4: guardar
    "save_title": {"ca": "On el vols desar?", "es": "¿Dónde lo quieres guardar?"},
    "save_intro": {
        "ca": "Per enganxar-lo a una IA, el format de text és el més net.",
        "es": "Para pegarlo en una IA, el formato de texto es el más limpio.",
    },
    "cloud_warning": {
        "ca": "Aquesta carpeta es sincronitza amb el núvol (OneDrive, Dropbox, iCloud...): la "
        "guia de correspondències, amb els noms reals, s'hi pujarà. Si no ho vols, tria una "
        "altra carpeta o desmarca la guia.",
        "es": "Esta carpeta se sincroniza con la nube (OneDrive, Dropbox, iCloud...): la guía "
        "de correspondencias, con los nombres reales, se subirá. Si no quieres, elige otra "
        "carpeta o desmarca la guía.",
    },
    "format_text_short": {"ca": "Text per a la IA (.txt)", "es": "Texto para la IA (.txt)"},
    # Progreso
    "progress_analyzing": {"ca": "Analitzant el document…", "es": "Analizando el documento…"},
    "progress_anonymizing": {"ca": "Anonimitzant…", "es": "Anonimizando…"},
    "phase_read": {"ca": "Lectura de les pàgines", "es": "Lectura de las páginas"},
    "phase_detect": {"ca": "Cerca de noms i dades", "es": "Búsqueda de nombres y datos"},
    "phase_anonymize": {"ca": "Anonimització", "es": "Anonimización"},
    "phase_verify": {"ca": "Comprovació final", "es": "Comprobación final"},
    "phase_export": {"ca": "Exportació a text", "es": "Exportación a texto"},
    "phase_pages": {"ca": "pàgina {done} de {total}", "es": "página {done} de {total}"},
    "phase_images": {"ca": "imatge {done} de {total}", "es": "imagen {done} de {total}"},
    "phase_percent": {"ca": "{percent}%", "es": "{percent}%"},
    "phase_pending": {"ca": "pendent", "es": "pendiente"},
    "phase_done": {"ca": "fet", "es": "hecho"},
    "eta": {"ca": "Temps restant aproximat: {time}", "es": "Tiempo restante aproximado: {time}"},
    "eta_minutes": {"ca": "{n} min", "es": "{n} min"},
    "eta_less_minute": {"ca": "menys d'un minut", "es": "menos de un minuto"},
    "eta_unknown": {"ca": "Calculant el temps restant…", "es": "Calculando el tiempo restante…"},
    "keep_awake_note": {
        "ca": "Pots fer servir altres programes mentrestant. L'ordinador no entrarà en repòs "
        "fins que acabi.",
        "es": "Puedes usar otros programas mientras tanto. El ordenador no entrará en reposo "
        "hasta que termine.",
    },
    "cancelling": {"ca": "Cancel·lant…", "es": "Cancelando…"},
    # Resultado
    "result_ok": {"ca": "Document anonimitzat", "es": "Documento anonimizado"},
    "result_warn": {"ca": "Fet, però revisa els avisos", "es": "Hecho, pero revisa los avisos"},
    "result_serious": {
        "ca": "Atenció: revisa el document abans de fer-lo servir",
        "es": "Atención: revisa el documento antes de usarlo",
    },
    "result_summary": {
        "ca": "{total} substitucions. Desat a:",
        "es": "{total} sustituciones. Guardado en:",
    },
    "open_file": {"ca": "Obre el document", "es": "Abrir el documento"},
    "new_document": {"ca": "Anonimitza un altre document", "es": "Anonimizar otro documento"},
    # Lista "No anonimitzar"
    "keep_button": {"ca": "No anonimitzar · {count}", "es": "No anonimizar · {count}"},
    "keep_title": {
        "ca": "Noms i dades que no s'anonimitzen",
        "es": "Nombres y datos que no se anonimizan",
    },
    "keep_intro": {
        "ca": "Per exemple, el nom de l'advocada o l'adreça i el telèfon del despatx: es "
        "deixen tal qual perquè la IA els pugui fer servir. Es desen en aquest ordinador i "
        "s'apliquen a tots els documents. Si un nom també és a la llista del cas, s'anonimitza.",
        "es": "Por ejemplo, el nombre de la abogada o la dirección y el teléfono del despacho: "
        "se dejan tal cual para que la IA los pueda usar. Se guardan en este ordenador y se "
        "aplican a todos los documentos. Si un nombre también está en la lista del caso, se "
        "anonimiza.",
    },
    "keep_col": {
        "ca": "Nom o dada que es deixa tal qual",
        "es": "Nombre o dato que se deja tal cual",
    },
    "save_button": {"ca": "Desa", "es": "Guardar"},
    "never_anonymize": {"ca": "No anonimitzar mai", "es": "No anonimizar nunca"},
    "never_anonymize_tip": {
        "ca": "Afegeix les files seleccionades a la llista «No anonimitzar» (per a tots els "
        "documents).",
        "es": "Añade las filas seleccionadas a la lista «No anonimizar» (para todos los "
        "documentos).",
    },
    # Revisión final
    "review_title": {"ca": "Revisió final", "es": "Revisión final"},
    "review_found": {
        "ca": "Queden {count} paraules amb majúscula que no s'han substituït. Fes-hi una ullada "
        "per si alguna és un nom o una dada.",
        "es": "Quedan {count} palabras con mayúscula que no se han sustituido. Échales un vistazo "
        "por si alguna es un nombre o un dato.",
    },
    "review_none": {
        "ca": "No queda cap paraula amb majúscula sense substituir que sembli un nom.",
        "es": "No queda ninguna palabra con mayúscula sin sustituir que parezca un nombre.",
    },
    "review_button": {"ca": "Revisa", "es": "Revisar"},
    "review_intro": {
        "ca": "En groc, les paraules amb majúscula que no s'han substituït. Si alguna és un nom o "
        "una dada, marca-la a la dreta i torna a anonimitzar el document.",
        "es": "En amarillo, las palabras con mayúscula que no se han sustituido. Si alguna es un "
        "nombre o un dato, márcala a la derecha y vuelve a anonimizar el documento.",
    },
    "review_apply": {"ca": "Anonimitza les marcades", "es": "Anonimizar las marcadas"},
    "label_REVISIO": {"ca": "Revisió final", "es": "Revisión final"},
    # Quant a
    "about_button": {"ca": "Quant a", "es": "Acerca de"},
    "about_version": {"ca": "Versió {version}", "es": "Versión {version}"},
    "about_text": {
        "ca": "Anonimitza documents Word i PDF abans de passar-los a una IA. Tot es fa en "
        "aquest ordinador: no es connecta a internet, no envia dades i no desa còpies dels "
        "documents.",
        "es": "Anonimiza documentos Word y PDF antes de pasarlos a una IA. Todo se hace en "
        "este ordenador: no se conecta a internet, no envía datos y no guarda copias de los "
        "documentos.",
    },
    "about_licenses": {"ca": "Components de tercers", "es": "Componentes de terceros"},
    "about_component": {"ca": "Component", "es": "Componente"},
    "about_license": {"ca": "Llicència", "es": "Licencia"},
    "about_source": {
        "ca": "Fa servir Qt (LGPL-3.0) i PyMuPDF (AGPL-3.0). El codi font complet i el text de "
        "les llicències són a la carpeta «codi_font» del USB i a {url}.",
        "es": "Usa Qt (LGPL-3.0) y PyMuPDF (AGPL-3.0). El código fuente completo y el texto de "
        "las licencias están en la carpeta «codi_font» del USB y en {url}.",
    },
    "error_logged": {
        "ca": "S'ha desat un informe tècnic (sense cap dada del document) a:\n{path}",
        "es": "Se ha guardado un informe técnico (sin ningún dato del documento) en:\n{path}",
    },
    # Resultado
    "done_title": {"ca": "Fet", "es": "Hecho"},
    "done": {
        "ca": "Document anonimitzat i desat a:\n{path}\n\n{total} substitucions.",
        "es": "Documento anonimizado y guardado en:\n{path}\n\n{total} sustituciones.",
    },
    "open_folder": {"ca": "Obre la carpeta", "es": "Abrir la carpeta"},
    "close": {"ca": "Tanca", "es": "Cerrar"},
}


def tr(lang: str, key: str, **params: object) -> str:
    """Texto traducido; si falta el idioma, cae al catalán."""
    entry = STRINGS[key]
    text = entry.get(lang) or entry["ca"]
    return text.format(**params) if params else text
