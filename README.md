# Foto Nummeraar Online (FNO)

Foto Nummeraar Online is een Flask-webapplicatie voor het identificeren van personen op historische foto's. Foto's en officiële bronmetadata blijven afkomstig uit Maior Memorix/BrabantCloud. FNO bewaart eigen gegevens, zoals labels, namen, opmerkingen, lokale metadata, historie, zichtbaarheid, voortgang, instellingen en gebruikers. FNO schrijft nooit terug naar Maior Memorix.

## Technische stack

- Python 3.14
- Flask
- SQLAlchemy en Alembic
- SQLite
- Pydantic v2
- HTML, CSS en JavaScript ES Modules
- OpenSeadragon
- Ruff en Pytest

## Architectuur

FNO gebruikt de volgende lagen:

1. Models
2. Repositories
3. Services
4. Schemas
5. REST API
6. Frontend

Businesslogica hoort uitsluitend in Services. Repositories bevatten uitsluitend databasecode. REST-routes verzorgen validatie en responsevorming; de frontend bevat alleen presentatielogica.

## Lokale installatie

Maak en activeer een virtuele omgeving:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installeer de afhankelijkheden:

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Maak `.env` op basis van `.env.example` en voer de migraties uit:

```powershell
flask db upgrade
```

Maak daarna de eerste beheerder aan:

```powershell
flask create-admin
```

De minimale wachtwoordlengte is 8 tekens.

Start de applicatie:

```powershell
flask run
```

## Productie

FNO blijft provider-onafhankelijk en gebruikt standaard SQLite. Productie start via `wsgi.py` met de productieconfiguratie.

Lees vóór deployment `docs/PRODUCTION_CHECKLIST.md`. Productie weigert te starten met een onveilige voorbeeldsecret, een niet-publieke basis-URL of onvolledige actieve SMTP-configuratie.

## Kwaliteitscontrole

Voer na iedere wijziging uit:

```powershell
git status
ruff check .
ruff format .
pytest
git status
```

Maak daarna een gerichte commit en push de wijziging.

## Support-zip

Maak vanuit de projecthoofdmap een supportbestand met:

```powershell
.\tools\create_support_zip.ps1
```

Lokale databases, `.env`, virtuele omgevingen, caches en Git-data worden daarbij uitgesloten.

## Projectstatus

De kernfunctionaliteit voor v1.0 is aanwezig. De actuele fase is productie-hardening en daarna volgen performancecontrole, gebruikersacceptatietest en de definitieve v1.0 releasecheck.

## Ontwikkeltools

Start het centrale toolmenu vanuit de projectmap:

```powershell
.\tools\FNO-Tools.ps1
```

Het menu bevat support-ZIP, database-reset, beheerder aanmaken, back-up, herstel en de standaard projectcontrole. Destructieve databaseacties maken eerst een back-up en vragen expliciete bevestiging.
