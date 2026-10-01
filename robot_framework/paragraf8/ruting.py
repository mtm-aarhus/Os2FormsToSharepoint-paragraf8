"""Afgoer om en koersel eller et koeelement angaar §8.

Det eneste modul i pakken som resten af robotten importerer ved opstart. Det
afhaenger kun af config.py, som kun indeholder konstanter. Selve §8-koden
(behandling, polling, diagnostik) importeres foerst naar der er brug for den.

Grunden: en fejl der opstaar allerede ved import af §8-koden — en
syntaksfejl, en manglende afhaengighed — ville ellers staa i toppen af
process.py og stoppe robotten foer den naaede til Altinget og Cykeloeen.
"""

import sys

from robot_framework.paragraf8 import config

_FORMULAR_NAVNE = {navn.strip().lower() for navn in config.FORMULAR_NAVNE}


def er_paragraf8(formular) -> bool:
    """Afgoer om koeelementets "formular"-felt betyder en §8-ansoegning."""
    return isinstance(formular, str) and formular.strip().lower() in _FORMULAR_NAVNE


def polling_oensket(orchestrator_connection) -> bool:
    """Afgoer om denne koersel skal polle OS2Forms for §8."""
    arguments = getattr(orchestrator_connection, "process_arguments", None) or ""
    return config.POLL_ARGUMENT in str(arguments).lower()


def struktur_oensket(argv: list[str] | None = None) -> bool:
    """Afgoer om robotten er startet i §8-diagnose-tilstand."""
    args = argv if argv is not None else sys.argv[1:]
    return config.STRUKTUR_ARGUMENT in " ".join(args).lower()
