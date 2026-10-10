from anonimizador.core.matcher import Matcher, Term, variants
from anonimizador.core.text import fold


def test_fold_keeps_length():
    text = "Ñandú PÉREZ Müller"
    assert fold(text) == "nandu perez muller"
    assert len(fold(text)) == len(text)


def test_variants_of_person_name():
    v = variants("Juan Pérez García")
    assert {"Juan Pérez", "Pérez García", "J. Pérez García", "Pérez", "García"} <= set(v)
    assert "Juan" not in v


def test_variants_of_company_skip_legal_form():
    v = variants("Construcciones Levante SL")
    assert "SL" not in v
    assert "Levante" in v


def test_ignores_case_and_accents():
    m = Matcher([Term("Juan Pérez García", "[CLIENTE_1]")])
    text = "Comparece JUAN PEREZ GARCIA y luego el Sr. Pérez y J. Pérez García."
    assert m.replace(text) == "Comparece [CLIENTE_1] y luego el Sr. [CLIENTE_1] y [CLIENTE_1]."


def test_derived_variants_require_capital_letter():
    m = Matcher([Term("Calle Mayor 5", "[DIRECCION_1]")])
    assert m.replace("Vive en Calle Mayor 5. Es mayor de edad.") == (
        "Vive en [DIRECCION_1]. Es mayor de edad."
    )


def test_whole_words_only():
    m = Matcher([Term("Ana López", "[PERSONA_1]")])
    assert m.replace("Analizar a Ana López") == "Analizar a [PERSONA_1]"


def test_shared_surname_is_ambiguous_and_not_replaced():
    m = Matcher([Term("Juan Pérez", "[PERSONA_1]"), Term("Luis Pérez", "[PERSONA_2]")])
    assert m.replace("Juan Pérez y Luis Pérez. El Sr. Pérez.") == (
        "[PERSONA_1] y [PERSONA_2]. El Sr. Pérez."
    )
    assert "Pérez" in m.ambiguous


def test_longest_match_wins():
    m = Matcher([Term("Pérez", "[A]"), Term("Juan Pérez García", "[B]")])
    assert m.replace("Juan Pérez García") == "[B]"
