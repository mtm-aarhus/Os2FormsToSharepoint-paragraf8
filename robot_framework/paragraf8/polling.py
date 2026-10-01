"""Sikkerhedsnet: poller OS2Forms for §8-ansoegninger webhooken har tabt.

Koeres kun naar procesargumentet indeholder "paragraf8-poll" (se config.py),
typisk fra en natlig planlagt trigger. Robottens oevrige triggere roerer den
ikke. Manglende ansoegninger laegges i robottens faelles koe og behandles
derefter af den almindelige koe-loekke i samme koersel.
"""

import json
from datetime import datetime, timedelta

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework.paragraf8 import config
from robot_framework.paragraf8.klienter import build_os2forms_client, build_sharepoint_client


def fill_queue_from_os2forms(orchestrator_connection: OrchestratorConnection, queue_name: str) -> None:
    """Poller OS2Forms og laegger ubehandlede §8-ansoegninger i koeen."""
    os2forms = build_os2forms_client(orchestrator_connection)
    sharepoint = build_sharepoint_client(orchestrator_connection)

    starttime = (datetime.now() - timedelta(days=config.POLL_WINDOW_DAYS)).strftime("%Y-%m-%d")
    orchestrator_connection.log_info(f"§8: henter indsendelser fra OS2Forms siden {starttime}...")

    submissions = os2forms.list_submissions(starttime=starttime)
    orchestrator_connection.log_info(f"§8: OS2Forms returnerede {len(submissions)} indsendelser i vinduet.")

    if not submissions:
        return

    _log_serial_gaps(submissions, orchestrator_connection)

    known_uuids = sharepoint.get_all_submission_uuids()
    orchestrator_connection.log_info(f"§8: SharePoint indeholder i forvejen {len(known_uuids)} ansoegninger.")

    new_uuids = [
        uuid for uuid in (s.get("uuid") for s in submissions)
        if uuid and uuid not in known_uuids
    ]

    if not new_uuids:
        orchestrator_connection.log_info("§8: ingen nye ansoegninger at laegge i koeen.")
        return

    # Koeen kan allerede indeholde elementer — enten fra webhooken, eller fra en
    # tidligere koersel der ikke naaede at blive faerdig. Referencen er UUID'et,
    # saa de kan filtreres fra her.
    queued = _references_already_in_queue(new_uuids, queue_name, orchestrator_connection)
    to_enqueue = [uuid for uuid in new_uuids if uuid not in queued]

    if not to_enqueue:
        orchestrator_connection.log_info(
            f"§8: alle {len(new_uuids)} nye ansoegninger ligger allerede i koeen."
        )
        return

    # Samme dataform som webhooken laegger ind. Data SKAL vaere en JSON-streng:
    # OpenOrchestrator gemmer den i en tekstkolonne, og process.py koerer
    # json.loads paa hvert element foer den ved hvilken blanket det er.
    orchestrator_connection.bulk_create_queue_elements(
        queue_name,
        references=tuple(to_enqueue),
        data=tuple(
            json.dumps({"application_uuid": uuid, "formular": config.WEBFORM_ID})
            for uuid in to_enqueue
        ),
        created_by="Paragraf8-sikkerhedsnet",
    )
    orchestrator_connection.log_info(
        f"§8: lagde {len(to_enqueue)} ansoegninger i koeen som webhooken ikke havde meldt ind."
    )


def _references_already_in_queue(uuids: list[str], queue_name: str,
                                 orchestrator_connection: OrchestratorConnection) -> set[str]:
    """Finder de UUID'er der allerede ligger som koeelementer."""
    found = set()
    for uuid in uuids:
        if orchestrator_connection.get_queue_elements(queue_name, reference=uuid, limit=1):
            found.add(uuid)
    return found


def _log_serial_gaps(submissions: list[dict], orchestrator_connection: OrchestratorConnection) -> None:
    """Advarer hvis der er huller i serienumrene.

    OS2Forms-serials er fortloebende pr. webform. Et hul betyder enten at en
    indsendelse er slettet, eller at den aldrig blev listet til os — det sidste
    ville ellers kunne passere ubemaerket, fordi vi kun ser det vi faar udleveret.
    """
    serials = sorted(
        int(s["serial"]) for s in submissions
        if str(s.get("serial", "")).isdigit()
    )
    if len(serials) < 2:
        return

    gaps = [
        (prev, nxt) for prev, nxt in zip(serials, serials[1:])
        if nxt - prev > 1
    ]
    if gaps:
        orchestrator_connection.log_info(
            f"§8: huller i serienumre fra OS2Forms: {gaps}. "
            "Kan skyldes slettede indsendelser, men boer efterses hvis det gentager sig."
        )
