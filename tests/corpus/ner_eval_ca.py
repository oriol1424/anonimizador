"""Conjunto de evaluación del detector de entidades, en catalán y con datos INVENTADOS.

Cada ejemplo: (texto, [(fragmento, tipo)]) con tipo PER (persona), ORG (empresa u
organización privada) o ADDR (dirección). Lo que NO aparece en la lista no debería
detectarse como dato a anonimizar (juzgados, leyes, ciudades sueltas, cargos...).
"""

EXAMPLES: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "En Jordi Casals i Pons, major d'edat, amb domicili al carrer de la Indústria, 45, "
        "3r 2a, 08025 Barcelona, compareix davant el Jutjat de Primera Instància núm. 3 de Girona.",
        [
            ("Jordi Casals i Pons", "PER"),
            ("carrer de la Indústria, 45, 3r 2a, 08025 Barcelona", "ADDR"),
        ],
    ),
    (
        "La senyora Núria Ferrer Bosch va signar el contracte amb TALLERS MECÀNICS EMPORDÀ, SL "
        "el dia 4 de febrer de 2024.",
        [("Núria Ferrer Bosch", "PER"), ("TALLERS MECÀNICS EMPORDÀ, SL", "ORG")],
    ),
    (
        "DEMANDANT: MARIA DEL CARME VILADOMAT ROIG. DEMANDADA: INMOBILIARIA COSTA BRAVA SA.",
        [("MARIA DEL CARME VILADOMAT ROIG", "PER"), ("INMOBILIARIA COSTA BRAVA SA", "ORG")],
    ),
    (
        "El perit, Sr. Xavier Puigdemont Serra, va emetre informe a petició de Mapfre.",
        [("Xavier Puigdemont Serra", "PER"), ("Mapfre", "ORG")],
    ),
    (
        "Segons l'article 1.902 del Codi Civil, l'actora reclama 12.000 euros a l'empresa "
        "Construccions Rovira i Fills, SL.",
        [("Construccions Rovira i Fills, SL", "ORG")],
    ),
    (
        "La testimoni, Fatima El Amrani, resideix a l'avinguda Diagonal, 640, de Barcelona.",
        [("Fatima El Amrani", "PER"), ("avinguda Diagonal, 640, de Barcelona", "ADDR")],
    ),
    (
        "Que en data 12 de març l'Ajuntament de Sant Cugat va notificar la sanció a la "
        "Sra. Laia Mas.",
        [("Laia Mas", "PER")],
    ),
    (
        "El vehicle propietat d'en Pere Soler va col·lisionar a la plaça Major, 3, de Vic.",
        [("Pere Soler", "PER"), ("plaça Major, 3, de Vic", "ADDR")],
    ),
    (
        "L'administrador únic de Gestió Integral Lleida, SLU és el Sr. Ramon Torrent.",
        [("Gestió Integral Lleida, SLU", "ORG"), ("Ramon Torrent", "PER")],
    ),
    (
        "Es cita a declarar a Montserrat Prat Vila i a Josep Maria Font en qualitat de testimonis.",
        [("Montserrat Prat Vila", "PER"), ("Josep Maria Font", "PER")],
    ),
    (
        "La lletrada Anna Garcia Martínez, col·legiada núm. 34.567 de l'ICAB, actua en nom de "
        "la part actora.",
        [("Anna Garcia Martínez", "PER")],
    ),
    (
        "El senyor Hans Müller, de nacionalitat alemanya, va contractar els serveis de "
        "Viatges Mediterrani SL.",
        [("Hans Müller", "PER"), ("Viatges Mediterrani SL", "ORG")],
    ),
    (
        "La finca situada al passeig de Gràcia, 92, principal, està inscrita al Registre de "
        "la Propietat núm. 4 de Barcelona.",
        [("passeig de Gràcia, 92, principal", "ADDR")],
    ),
    (
        "Ho va comunicar per escrit a la seva germana, Rosa Pujol, i al seu advocat.",
        [("Rosa Pujol", "PER")],
    ),
    (
        "La mercantil FARMÀCIA BALAGUER CB va deixar de pagar les quotes al Banc Sabadell.",
        [("FARMÀCIA BALAGUER CB", "ORG"), ("Banc Sabadell", "ORG")],
    ),
    (
        "El menor, Pol Rius Camps, viu amb la mare al carrer Nou, 12, baixos, de Manresa.",
        [("Pol Rius Camps", "PER"), ("carrer Nou, 12, baixos, de Manresa", "ADDR")],
    ),
    (
        "La Sra. Sílvia Domènech va rebre un correu del director de recursos humans, Albert Coll.",
        [("Sílvia Domènech", "PER"), ("Albert Coll", "PER")],
    ),
    (
        "El Tribunal Superior de Justícia de Catalunya va desestimar el recurs de la "
        "Fundació Esplai Solidari.",
        [("Fundació Esplai Solidari", "ORG")],
    ),
    (
        "En Marc i la Clàudia, fills del matrimoni, quedaran sota la guarda de la mare.",
        [("Marc", "PER"), ("Clàudia", "PER")],
    ),
    (
        "La reunió es va fer a les oficines de Serveis Logístics Penedès, SA, a la carretera "
        "de Sant Sadurní, km 3, de Vilafranca del Penedès.",
        [
            ("Serveis Logístics Penedès, SA", "ORG"),
            ("carretera de Sant Sadurní, km 3, de Vilafranca del Penedès", "ADDR"),
        ],
    ),
    (
        "El jutge va requerir a l'Agència Tributària i a la Tresoreria General de la "
        "Seguretat Social informació sobre el deutor.",
        [],
    ),
    (
        "Vistos els articles 248 i següents de la Llei d'Enjudiciament Civil, procedeix "
        "estimar la demanda.",
        [],
    ),
    (
        "SEGON.- El Sr. Àlex Sánchez López va abonar la fiança mitjançant transferència des "
        "del compte de la seva sogra, Dolors Bru.",
        [("Àlex Sánchez López", "PER"), ("Dolors Bru", "PER")],
    ),
    (
        "La demandada, IMPORT EXPORT ZHANG SL, representada per Wei Zhang, no va comparèixer.",
        [("IMPORT EXPORT ZHANG SL", "ORG"), ("Wei Zhang", "PER")],
    ),
    (
        "El contracte d'arrendament de l'habitatge del carrer de Sant Pere Més Alt, 7, 2n 1a, "
        "es va signar a Barcelona.",
        [("carrer de Sant Pere Més Alt, 7, 2n 1a", "ADDR")],
    ),
]
