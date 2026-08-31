# Foto Nummeraar Online (FNO)

Foto Nummeraar Online is een Flask-webapplicatie voor het identificeren van personen op historische foto's. Foto's en officiële bronmetadata blijven live afkomstig uit Maior Memorix/BrabantCloud. FNO bewaart uitsluitend eigen gegevens, zoals labels, namen, opmerkingen, lokale metadata, historie, zichtbaarheid, voortgang, instellingen en gebruikers.

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

De minimale wachtwoordlengte is tijdens de ontwikkelfase vier tekens en kan later via configuratie worden aangescherpt.

Start de applicatie:

```powershell
flask run
```

## Kwaliteitscontrole

Voer na iedere wijziging uit:

```powershell
git status
ruff check . --fix
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

Milestones 1 tot en met 3 en Sprint 3.9 zijn afgerond. De volgende functionele fase is Milestone 4: vergelijking en handmatige synchronisatie van FNO-metadata met Maior Memorix.

## Ontwikkeltools

Start het centrale toolmenu vanuit de projectmap:

```powershell
.\tools\FNO-Tools.ps1
```

Het menu bevat support-ZIP, database-reset, beheerder aanmaken, back-up,
herstel en de standaard projectcontrole. Destructieve databaseacties maken
eerst een back-up en vragen expliciete bevestiging.
