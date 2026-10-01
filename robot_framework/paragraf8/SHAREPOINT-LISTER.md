# §8-ansøgninger — SharePoint-lister robotten skriver til

**Site:** `https://aarhuskommune.sharepoint.com/teams/Jordportalen`

Dokumentet beskriver kun de fire lister og de kolonner, som robotten udfylder med data
fra OS2Forms-blanketten "Ansøgning om §8-tilladelse efter jordforureningsloven". Sitet
kan have flere lister og kolonner end dem her, men robotten rører dem ikke.

Alle lister oprettes som **Brugerdefineret liste** ("Custom List" / Generic List) via
**Site Contents → Ny → Liste → Tom liste**.

Kolonnerne er udledt af en faktisk testindsendelse fra den nuværende blanket.

---

## Interne kolonnenavne — læs dette først

Det navn du taster ind, er kolonnens **visningsnavn**. SharePoint udleder et **internt
navn** af det ved oprettelsen, og det er det interne navn, koden skriver til. De to kan
falde fra hinanden:

1. **Specialtegn kodes om.** Bindestreg bliver til `_x002d_`, `ø` til `_x00f8_`, mellemrum
   til `_x0020_`.
2. **Navnet afkortes ved 32 tegn.**
3. **Omdøbning ændrer kun visningsnavnet.** Det interne navn er låst fra oprettelsen.
4. **To kolonner kan have samme visningsnavn** (fx `Magistratsafdeling` og
   `Magistratsafdeling0`). Skriver robotten til den forkerte, **lykkes kaldet uden fejl**,
   og værdien lander bare i en kolonne, visningen ikke viser.

**Derfor** er navnene herunder korte, rene ASCII-navne uden mellemrum, bindestreger eller
æ/ø/å og under 32 tegn. Tastes de præcis som vist, bliver det interne navn identisk med
visningsnavnet. Bekræft det efter oprettelsen med `get_internal_column_names()` i
`sharepoint_client.py`.

---

## Rækkefølge og sammenhæng

`P8Ansogninger` skal oprettes først, fordi de tre øvrige lister har en Lookup til den:

1. `P8Ansogninger` — én række pr. ansøgning
2. `P8Adresser` — én række pr. ejendom
3. `P8Kontakter` — én række pr. kontaktperson
4. `P8Vedhaeftninger` — én række pr. uploadet dokument

`SubmissionUUID` findes på alle fire lister og er robottens dubletsikring. Robotten
springer ansøgninger over, hvis UUID'et allerede findes, så en kørsel kan gentages uden
dubletter. Lookup-kolonnen `Ansogning` sættes via REST som `AnsogningId`.

---

## 1. P8Ansogninger

| Kolonnenavn (præcis stavning!) | Type | Fra blanketten | Indstillinger |
|---|---|---|---|
| **SubmissionUUID** | Enkelt tekstlinje | `uuid` | Dubletsikring. **Skal indekseres** |
| **SubmissionSerial** | Tal | `serial` | 0 decimaler |
| **SubmissionSid** | Tal | `sid` | 0 decimaler |
| **OS2FormsUrl** | Hyperlink eller billede | *(udledt af `sid`)* | Format: **Hyperlink**. Link til indsendelsen i OS2Forms |
| **Udfylder** | Enkelt tekstlinje | `udfylder` | |
| **IndsendtAf** | Valg | `ansoegning_indsendt_af` | Valgmuligheder: `Grundejer`, `Bygherre`, `Rådgiver` |
| **AnsogningsDato** | Dato og klokkeslæt | `vaelg_dato_for_ansoegning` | Inkluder klokkeslæt: **Nej** |
| **Bemaerkninger** | Flere tekstlinjer | `bemaerkninger` | Almindelig tekst (ikke Rich Text) |
| **ModtagetDato** | Dato og klokkeslæt | `created` | Inkluder klokkeslæt: **Ja** |
| **AfsluttetDato** | Dato og klokkeslæt | `completed` | Inkluder klokkeslæt: **Ja**. Kan stå tom |
| **FlereGrundejere** | Ja/Nej | `er_der_flere_grundejere` | Standard: Nej |
| **BygherreSammeSomGrundejer** | Ja/Nej | `er_bygherre_den_samme_som_grundejer` | Standard: Nej |
| **Status** | Valg | *(sættes til `Ny`)* | Skal have valgmuligheden `Ny`. Robotten sætter den kun ved oprettelse og rører den aldrig igen |
| **AntalAdresser** | Tal | *(udledt)* | 0 decimaler, standard 0 |
| **AntalKontakter** | Tal | *(udledt)* | 0 decimaler, standard 0 |
| **AntalVedhaeftninger** | Tal | *(udledt)* | 0 decimaler, standard 0 |
| **AdresserTekst** | Flere tekstlinjer | *(udledt)* | Alle adresser, én pr. linje |
| **Grundejere** | Flere tekstlinjer | *(udledt)* | Grundejernes navne (eller firma), ét pr. linje |

> `Title` findes automatisk. Robotten sætter den til ansøgningens første adresse med
> `(+N flere)` bagefter, eller `§8 – <SubmissionSerial>` hvis der ingen adresse er.

> **Datoer gemmes i UTC.** Robotten konverterer alle datoer i `datoer.py`. Det
> forudsætter, at sitets tidszone står til dansk tid (**Webstedsindstillinger → Regionale
> indstillinger → Tidszone**). Ellers vises ansøgningsdatoer en dag for tidligt.

---

## 2. P8Adresser

Fra `adresser` i blanketten. Antallet er ubegrænset.

| Kolonnenavn (præcis stavning!) | Type | Fra blanketten | Indstillinger |
|---|---|---|---|
| **Ansogning** | Opslag (Lookup) | | Hent fra `P8Ansogninger`, felt `Title`. Enkelt værdi |
| **SubmissionUUID** | Enkelt tekstlinje | `uuid` | **Skal indekseres** |
| **Adresse** | Enkelt tekstlinje | `vaelg_adresse` | |
| **Matrikel** | Enkelt tekstlinje | `mat` | |
| **LokalitetsNummer** | Enkelt tekstlinje | `lokalitets_nummer` | |

> `Title` sættes til adressen.

---

## 3. P8Kontakter

Blanketten er flad: hver part har sine egne felter med et suffiks.

| Suffiks | Rolle | Felter i blanketten |
|---|---|---|
| *(intet)* | Grundejer | `navn_kontaktperson`, `evt_firma`, `cvr`, `e_mail`, `telefon_nr`, `adresse` |
| `_2` | Grundejer nr. 2 | `evt_firma_2`, `cvr_2`, `e_mail_2`, `telefon_nr_2`, `adresse_2` |
| `_byg` | Bygherre | `navn_kontaktperson_byg`, `evt_firma_byg`, `cvr_byg`, `e_mail__byg`, `telefon_nr_byg`, `adresse_byg` |
| `_raad` | Rådgiver | `navn_kontaktperson_raad`, `evt_firma_raad`, `cvr_raad`, `e_mail_raad`, `telefon_nr_raad`, `adresse_raad` |

Bemærk: `e_mail__byg` har dobbelt underscore, og `navn_kontaktperson_2` findes ikke i
blanketten. Grundejer nr. 2 oprettes kun, hvis `er_der_flere_grundejere` er Ja. Bygherren
oprettes kun, hvis `er_bygherre_den_samme_som_grundejer` er Nej.

| Kolonnenavn (præcis stavning!) | Type | Indstillinger |
|---|---|---|
| **Ansogning** | Opslag (Lookup) | Hent fra `P8Ansogninger`, felt `Title`. Enkelt værdi |
| **SubmissionUUID** | Enkelt tekstlinje | **Skal indekseres** |
| **KontaktType** | Valg | `Grundejer`, `Bygherre`, `Rådgiver` |
| **ErUdfylder** | Ja/Nej | Standard: Nej |
| **Navn** | Enkelt tekstlinje | Kan stå tom for grundejer nr. 2 |
| **Firma** | Enkelt tekstlinje | |
| **CVR** | Enkelt tekstlinje | Tekst, ikke Tal (bevarer foranstillede nuller) |
| **Email** | Enkelt tekstlinje | |
| **Telefon** | Enkelt tekstlinje | Tekst |
| **Adresse** | Enkelt tekstlinje | Kontaktens egen adresse |

> `Title` sættes til navnet, eller firmaet hvis navnet mangler.

---

## 4. P8Vedhaeftninger

Fra `upload_dokumenter` i blanketten.

| Kolonnenavn (præcis stavning!) | Type | Indstillinger |
|---|---|---|
| **Ansogning** | Opslag (Lookup) | Hent fra `P8Ansogninger`, felt `Title`. Enkelt værdi |
| **SubmissionUUID** | Enkelt tekstlinje | **Skal indekseres** |
| **FilId** | Enkelt tekstlinje | OS2Forms' fil-id |
| **Filnavn** | Enkelt tekstlinje | Står foreløbig tom |
| **FilUrl** | Hyperlink eller billede | Format: **Hyperlink**. Står foreløbig tom |

> `Title` sættes til filnavnet, eller fil-id'et hvis navnet ikke kendes.

---

## Tjekliste efter oprettelse

- Alle fire lister findes under **Site Contents**
- `SubmissionUUID` er indekseret på **alle fire** lister
- `Ansogning`-lookup-kolonnerne viser værdier fra `P8Ansogninger`
- `get_internal_column_names()` viser interne navne identiske med visningsnavnene
- Sitets tidszone står til **(UTC+01:00) Bruxelles, København, Madrid, Paris**
- Robottens SharePoint-app har **skriveadgang** til sitet

## Åbne punkter

1. **Vedhæftede filer.** Blanketten leverer kun fil-id'er, ikke filnavne eller URL'er.
   Indtil opslaget via OS2Forms' `/entity/file/{file_id}` er verificeret, står `Filnavn`
   og `FilUrl` tomme.
2. **`navn_kontaktperson_2` mangler i blanketten.** Skal grundejer nr. 2 have et navnefelt,
   skal det tilføjes i OS2Forms.
