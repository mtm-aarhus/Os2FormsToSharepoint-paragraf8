"""This module defines any initial processes to run when the robot starts."""

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config
from robot_framework.paragraf8 import ruting as paragraf8_ruting


def initialize(orchestrator_connection: OrchestratorConnection) -> None:
    """Do all custom startup initializations of the robot."""
    orchestrator_connection.log_trace("Initializing.")

    # Sikkerhedsnet for §8: kun naar procesargumentet indeholder
    # "paragraf8-poll". De oevrige triggere paavirkes ikke, og §8-koden
    # importeres slet ikke paa dem.
    if paragraf8_ruting.polling_oensket(orchestrator_connection):
        from robot_framework.paragraf8 import polling as paragraf8_polling  # pylint: disable=import-outside-toplevel
        paragraf8_polling.fill_queue_from_os2forms(orchestrator_connection, config.QUEUE_NAME)
