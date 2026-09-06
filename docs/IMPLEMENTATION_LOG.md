# Implementatielog

## 2026-07

### Architectuur

- Flask Application Factory
- Repository Pattern
- Service Pattern
- REST API
- Pydantic v2
- Alembic
- SQLite

### Fotopagina en landingspagina

- OpenSeadragon, labels, personenlijst, autosave, historie en opmerkingen
- Zoeken, filters, thumbnailweergaven en scrollherstel
- Responsive layout en centrale huisstijl

### Adminomgeving en MM-import

- Authenticatie, rollen en autorisatie
- Beheerdashboard en historie-export
- BrabantCloud-facets, bulkimport en importvoorvertoning
- Lokale metadata, zichtbaarheid, voortgang en naamvergrendeling

### Refactor en kwaliteit

- Backendrequests en metadata-extractie gecentraliseerd
- Frontendcontrollers vereenvoudigd
- Databasegebruik buiten repositories verwijderd
- API gebruikt publieke service-methoden
- Architectuurgrenzen als regressietests vastgelegd

## 2026-08

### MM en fotopagina

- MM-beschrijvingsparser en parseranalyse afgerond
- Vergelijkingsrapport beperkt tot daadwerkelijk geïmporteerde FNO-foto's
- Personenweergave en labelgrootte uitgebreid
- OpenVINO-gezichtsdetectie geïntegreerd voor Auto label
- Export van foto met labels en metadataformaten afgerond

## 2026-09

### Productie en hosting

- FNO provider-onafhankelijk op een WSGI-host geplaatst
- SQLite/Alembic deployment in productie getest
- OpenCV/OpenVINO op productiehost getest
- stabiele fotolinks toegevoegd
- Nederlandse OpenSeadragon-tooltips toegevoegd

### Accountbeheer

- rollen `user`, `employee` en `administrator`
- openbare registratie en e-mailverificatie
- laatste login zichtbaar in gebruikersbeheer
- wachtwoordherstel per e-mail
- eigen e-mailadres wijzigen met herverificatie
- rolupgrade-aanvragen en beheerdersbeoordeling

### Productie-hardening

- productieconfiguratie fail-fast gemaakt voor secret, publieke URL en SMTP
- regressietests voor kritieke productie-instellingen toegevoegd
- provider-onafhankelijke deployment-, back-up- en herstelchecklist toegevoegd
- roadmap en known issues bijgewerkt naar actuele v1.0-status
