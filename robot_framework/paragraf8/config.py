"""Konfiguration for §8-blanketten.

Credentials og constants deles med resten af robotten (OS2FormsAPI,
SharePointAPI, SharePointCert og AarhusKommuneSharePoint). Det der staar her,
gaelder kun §8.
"""

# OS2Forms
# ----------------------

# Blankettens maskinnavn. Indgaar i URL'en som
#   {base_url}{webform_id}/submission/{uuid}
#
# Blanketten hedder "Ansoegning om §8-tilladelse efter jordforureningsloven" og
# ligger paa selvbetjening.aarhuskommune.dk. Navnet er praecis 32 tegn, fordi
# Drupal afkorter maskinnavne dér — "_beb" er altsaa en afhugget rest og ikke
# en tastefejl.
WEBFORM_ID = "ansoegning_om_ss8_tilladelse_beb"

# Vaerdier i koeelementets "formular"-felt, som betyder at elementet er en
# §8-ansoegning. Sammenlignes uden hensyn til store/smaa bogstaver.
#
# Titlen er den webhooken skal saettes op til at sende, ligesom de oevrige
# blanketter i robotten. Maskinnavnet er det sikkerhedsnets-pollingen selv
# laegger i koeen. Begge skal genkendes — ellers ville elementer fra den ene
# kilde falde igennem til de andre blanketters grene.
FORMULAR_NAVNE = (
    "Ansøgning om §8-tilladelse efter jordforureningsloven",
    WEBFORM_ID,
)

# Hvor langt tilbage sikkerhedsnets-koerslen henter. Vinduet er bevidst meget
# bredere end koerselsintervallet: ansoegninger der allerede findes i SharePoint
# springes over paa dedup-feltet, saa overlap er gratis, mens et for smalt
# vindue ville tabe ansoegninger permanent hvis webhooken svigtede.
POLL_WINDOW_DAYS = 14


# Procesargumenter
# ----------------------

# Slaar sikkerhedsnets-pollingen til. Skal staa paa en separat planlagt
# trigger. Pollingen er slaaet FRA som standard, fordi robotten ogsaa koerer
# for Altinget og Cykeloeen — deres triggere skal ikke begynde at polle §8.
POLL_ARGUMENT = "paragraf8-poll"

# Starter diagnose-tilstanden, der skriver blankettens feltstruktur i loggen
# uden at roere koeen eller SharePoint. Se diagnostik.py.
STRUKTUR_ARGUMENT = "paragraf8-struktur"


# SharePoint
# ----------------------

# Jordportalen — samme site som SPFx-frontenden (mtm-aarhus/jordportalen).
# Bemaerk lille t i /teams/, hvor de oevrige blanketter bruger /Teams/.
SHAREPOINT_SITE_PATH = "/teams/Jordportalen"

# Listenavne. Skal matche listerne paa sitet praecist.
LIST_ANSOGNINGER = "P8Ansogninger"
LIST_ADRESSER = "P8Adresser"
LIST_KONTAKTER = "P8Kontakter"
LIST_VEDHAEFTNINGER = "P8Vedhaeftninger"

# Feltet der bruges til dubletfiltrering. Bemaerk at dette er det INTERNE
# kolonnenavn, ikke visningsnavnet — SharePoint koder specialtegn om og
# afkorter ved 32 tegn.
DEDUP_FIELD = "SubmissionUUID"
