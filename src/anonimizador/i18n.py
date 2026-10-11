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
    "notice_images": {
        "ca": "El document conté {count} imatges o objectes incrustats. El seu contingut no "
        "s'anonimitza: revisa'ls manualment.",
        "es": "El documento contiene {count} imágenes u objetos incrustados. Su contenido no "
        "se anonimiza: revísalos manualmente.",
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
    "sugg_title": {"ca": "Revisa les suggerències", "es": "Revisa las sugerencias"},
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
