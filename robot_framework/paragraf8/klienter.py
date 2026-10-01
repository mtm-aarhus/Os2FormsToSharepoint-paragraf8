"""Bygger OS2Forms- og SharePoint-klienterne ud fra OpenOrchestrator.

Bruger de samme credentials og constants som resten af robotten.
"""

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework.paragraf8 import config
from robot_framework.paragraf8.os2forms_client import OS2FormsClient
from robot_framework.paragraf8.sharepoint_client import SharePointClient, build_context


def build_os2forms_client(orchestrator_connection: OrchestratorConnection) -> OS2FormsClient:
    """Bygger en OS2Forms-klient ud fra credentialet OS2FormsAPI.

    Credentialet baerer base-URL'en i username og noeglen i password.
    """
    credential = orchestrator_connection.get_credential("OS2FormsAPI")
    return OS2FormsClient(
        base_url=credential.username,
        webform_id=config.WEBFORM_ID,
        api_key=credential.password,
    )


def build_sharepoint_client(orchestrator_connection: OrchestratorConnection) -> SharePointClient:
    """Bygger en SharePoint-klient med certifikat-auth mod §8-sitet."""
    api_cred = orchestrator_connection.get_credential("SharePointAPI")
    cert_cred = orchestrator_connection.get_credential("SharePointCert")
    base_url = orchestrator_connection.get_constant("AarhusKommuneSharePoint").value

    ctx = build_context(
        site_url=f"{base_url.rstrip('/')}{config.SHAREPOINT_SITE_PATH}",
        tenant=api_cred.username,
        client_id=api_cred.password,
        thumbprint=cert_cred.username,
        cert_path=cert_cred.password,
    )
    return SharePointClient(ctx=ctx)
