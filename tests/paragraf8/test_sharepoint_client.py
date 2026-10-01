"""Tests for robot_framework/paragraf8/sharepoint_client.py — URL-kolonnerne.

En Hyperlink-kolonne skal sendes som en SP.FieldUrlValue. Sendes den som ren
tekst, afviser SharePoint hele raekken — og saa oprettes ingen ansoegning.
"""

# Testnavnene beskriver hvad der testes.
# pylint: disable=missing-function-docstring

from robot_framework.paragraf8 import sharepoint_client

# De Hyperlink-kolonner robotten skriver til:
#   P8Ansogninger.OS2FormsUrl    link til indsendelsen i OS2Forms
#   P8Vedhaeftninger.FilUrl      link til borgerens bilag
# Faar en af de fire lister en ny Hyperlink-kolonne, skal den med baade her og
# i URL_FIELDS.
HYPERLINK_KOLONNER = {"OS2FormsUrl", "FilUrl"}


def test_url_fields_er_praecis_hyperlink_kolonnerne():
    assert sharepoint_client.URL_FIELDS == HYPERLINK_KOLONNER


def test_os2formsurl_sendes_som_fieldurlvalue():
    renset = sharepoint_client._clean({"OS2FormsUrl": "https://selvbetjening.aarhuskommune.dk/x/1"})  # pylint: disable=protected-access
    assert renset["OS2FormsUrl"]["__metadata"] == {"type": "SP.FieldUrlValue"}
    assert renset["OS2FormsUrl"]["Url"] == "https://selvbetjening.aarhuskommune.dk/x/1"
