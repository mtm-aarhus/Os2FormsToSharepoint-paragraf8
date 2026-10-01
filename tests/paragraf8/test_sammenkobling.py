"""Tests for sammenkoblingen mellem §8-pakken og resten af robotten.

Daekker de steder hvor en fejl ikke ville give nogen fejlmeddelelse:

- at §8-elementer sendes til §8-pakken og ikke falder igennem til
  Altinget/Cykeloeen-grenene (og omvendt),
- at pollingen kun koerer naar den er bedt om det,
- at pollingen laegger data i koeen som en JSON-streng, som process.py kan
  json.loads'e — ikke som et dict.
"""

# Testnavnene beskriver hvad der testes.
# pylint: disable=missing-function-docstring

import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

import robot_framework.paragraf8 as paragraf8_pakke
from robot_framework import process
from robot_framework.paragraf8 import behandling, config, polling, ruting

UUID_1 = "12345678-90ab-cdef-1234-567890abcdef"
UUID_2 = "abcdef12-3456-7890-abcd-ef1234567890"


class _StopBeforeNetwork(Exception):
    """Kastes af den falske forbindelse naar en gren forsoeger at hente credentials."""


class FakeConnection:
    """Minimal OrchestratorConnection der registrerer kald i stedet for at udfoere dem."""

    def __init__(self, process_arguments: str | None = None):
        self.process_arguments = process_arguments
        self.bulk_calls: list[dict] = []
        self.queued_references: set[str] = set()

    def log_trace(self, _message):
        """Ignorer."""

    def log_info(self, _message):
        """Ignorer."""

    def log_error(self, _message):
        """Ignorer."""

    def get_credential(self, _name):
        """Altinget/Cykeloeen-grenene starter med at hente credentials."""
        raise _StopBeforeNetwork()

    def get_queue_elements(self, _queue_name, reference=None, limit=100):  # pylint: disable=unused-argument
        """Returnerer et element hvis referencen er markeret som allerede i koeen."""
        return (object(),) if reference in self.queued_references else ()

    def bulk_create_queue_elements(self, queue_name, references, data, created_by=None):
        """Gemmer kaldet saa testen kan inspicere det."""
        self.bulk_calls.append(
            {"queue_name": queue_name, "references": references, "data": data, "created_by": created_by}
        )


def _element(formular: str | None, uuid: str = UUID_1) -> SimpleNamespace:
    return SimpleNamespace(
        id="element-id",
        reference=uuid,
        data=json.dumps({"application_uuid": uuid, "formular": formular}),
    )


# --- er_paragraf8 ---

@pytest.mark.parametrize("formular", [
    "Ansøgning om §8-tilladelse efter jordforureningsloven",
    "  ansøgning om §8-tilladelse efter jordforureningsloven  ",
    config.WEBFORM_ID,
    config.WEBFORM_ID.upper(),
])
def test_paragraf8_formular_genkendes(formular):
    assert ruting.er_paragraf8(formular)


@pytest.mark.parametrize("formular", [
    "Tilmelding til Altinget",
    "Blanket: Booking af Cykeløen",
    "",
    None,
    42,
])
def test_andre_formularer_genkendes_ikke(formular):
    assert not ruting.er_paragraf8(formular)


# --- process.process sender videre ---

def test_paragraf8_element_gaar_til_paragraf8_pakken(monkeypatch):
    kald = []
    monkeypatch.setattr(behandling, "behandl", lambda oc, qe: kald.append(qe))

    element = _element(config.WEBFORM_ID)
    process.process(FakeConnection(), element)

    assert kald == [element]


@pytest.mark.parametrize("formular", ["Tilmelding til Altinget", "Blanket: Booking af Cykeløen"])
def test_andre_blanketter_gaar_ikke_til_paragraf8_pakken(monkeypatch, formular):
    kald = []
    monkeypatch.setattr(behandling, "behandl", lambda oc, qe: kald.append(qe))

    # De eksisterende grene starter med at hente credentials; den falske
    # forbindelse stopper dem dér, foer de naar netvaerket.
    with pytest.raises(_StopBeforeNetwork):
        process.process(FakeConnection(), _element(formular))

    assert not kald


# --- polling ---

@pytest.mark.parametrize("arguments, forventet", [
    (None, False),
    ("", False),
    ("no-poll", False),
    ("paragraf8-poll", True),
    ("PARAGRAF8-POLL", True),
])
def test_polling_kun_naar_den_er_bedt_om_det(arguments, forventet):
    assert ruting.polling_oensket(FakeConnection(arguments)) is forventet


def test_polling_laegger_json_strenge_i_koeen(monkeypatch):
    os2forms = SimpleNamespace(list_submissions=lambda starttime: [
        {"uuid": UUID_1, "serial": "10"},
        {"uuid": UUID_2, "serial": "11"},
    ])
    sharepoint = SimpleNamespace(get_all_submission_uuids=set)
    monkeypatch.setattr(polling, "build_os2forms_client", lambda oc: os2forms)
    monkeypatch.setattr(polling, "build_sharepoint_client", lambda oc: sharepoint)

    connection = FakeConnection("paragraf8-poll")
    connection.queued_references = {UUID_2}  # ligger allerede i koeen fra webhooken
    polling.fill_queue_from_os2forms(connection, "FaellesKoe")

    assert len(connection.bulk_calls) == 1
    call = connection.bulk_calls[0]
    assert call["queue_name"] == "FaellesKoe"
    assert call["references"] == (UUID_1,)

    (data,) = call["data"]
    assert isinstance(data, str)
    parsed = json.loads(data)
    assert parsed == {"application_uuid": UUID_1, "formular": config.WEBFORM_ID}
    assert ruting.er_paragraf8(parsed["formular"])


def test_polling_springer_kendte_ansoegninger_over(monkeypatch):
    os2forms = SimpleNamespace(list_submissions=lambda starttime: [{"uuid": UUID_1, "serial": "10"}])
    sharepoint = SimpleNamespace(get_all_submission_uuids=lambda: {UUID_1})
    monkeypatch.setattr(polling, "build_os2forms_client", lambda oc: os2forms)
    monkeypatch.setattr(polling, "build_sharepoint_client", lambda oc: sharepoint)

    connection = FakeConnection("paragraf8-poll")
    polling.fill_queue_from_os2forms(connection, "FaellesKoe")

    assert not connection.bulk_calls


# --- isolation fra resten af robotten ---

def test_robottens_opstart_importerer_ikke_paragraf8_koden():
    # Koeres i en ny proces, saa andre tests' imports ikke taeller med.
    kode = (
        "import sys\n"
        "import robot_framework.process, robot_framework.initialize\n"
        "tunge = [m for m in sys.modules if m.startswith('robot_framework.paragraf8.')"
        " and m not in ('robot_framework.paragraf8.ruting', 'robot_framework.paragraf8.config')]\n"
        "print(','.join(tunge))\n"
    )
    resultat = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, check=True)
    assert resultat.stdout.strip() == ""


def test_andre_blanketter_koerer_selvom_paragraf8_ikke_kan_importeres(monkeypatch):
    # None i sys.modules faar importen til at fejle, som ved en syntaksfejl
    # eller en manglende afhaengighed i §8-koden.
    # Attributten paa pakken skal ogsaa vaek, ellers genbruger
    # "from ... import behandling" den i stedet for at importere paany.
    monkeypatch.setitem(sys.modules, "robot_framework.paragraf8.behandling", None)
    monkeypatch.delattr(paragraf8_pakke, "behandling")

    # Altinget naar sin egen gren (og stoppes dér af den falske forbindelse).
    with pytest.raises(_StopBeforeNetwork):
        process.process(FakeConnection(), _element("Tilmelding til Altinget"))

    # Kun §8-elementet selv fejler — og det fejler hoejlydt, ikke stille.
    with pytest.raises(ImportError):
        process.process(FakeConnection(), _element(config.WEBFORM_ID))
