"""Línea de comandos (para pruebas, hasta que exista la interfaz gráfica).

Ejemplo:
    python -m anonimizador demanda.docx salida.docx -t "Joan Puig i Ferrer=[CLIENT_1]" -s
"""

import argparse
import sys
from pathlib import Path

from anonimizador.core.lang import DEFAULT_LANGUAGE, LANGUAGES
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize


def _parse_term(raw: str) -> Term:
    original, sep, replacement = raw.partition("=")
    if not sep or not original.strip() or not replacement.strip():
        raise argparse.ArgumentTypeError(f'Formato esperado "Original=Sustituto": {raw}')
    return Term(original.strip(), replacement.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="anonimizador", description=__doc__.splitlines()[0])
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path, help=".docx o .txt")
    parser.add_argument("-t", "--termino", type=_parse_term, action="append", default=[])
    parser.add_argument(
        "-s",
        "--aplicar-sugerencias",
        action="store_true",
        help="aplicar también los datos detectados automáticamente",
    )
    parser.add_argument(
        "-i",
        "--idioma",
        choices=sorted(LANGUAGES),
        default=DEFAULT_LANGUAGE.code,
        help=f"idioma del documento (por defecto: {DEFAULT_LANGUAGE.code})",
    )
    args = parser.parse_args(argv)
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    language = LANGUAGES[args.idioma]
    terms: list[Term] = list(args.termino)
    analysis = analyze(args.entrada, terms, language)
    if analysis.suggestions:
        print("Sugerencias (datos que no estaban en tu lista):")
        for s in analysis.suggestions:
            print(f"  {s.label:<14} {s.text!r:<34} -> {s.replacement}  ({s.count}x)")
        if args.aplicar_sugerencias:
            for s in analysis.suggestions:
                terms.extend(s.to_terms())

    report = anonymize(args.entrada, args.salida, terms)
    print(f"\nGuardado en {report.output} ({report.total} sustituciones)")
    for alias, n in sorted(report.replaced.items()):
        print(f"  {alias}: {n}")
    for notice in analysis.notices + report.notices:
        print(f"AVISO: {notice.message(language)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
