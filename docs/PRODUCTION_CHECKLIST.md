# Productiechecklist FNO

Deze checklist is provider-onafhankelijk en geldt voor AlwaysData, een eigen server of een andere WSGI-host.

## Voor iedere deployment

1. Maak een back-up van `instance/fno.db`.
2. Activeer de virtuele omgeving.
3. Haal de bedoelde Git-branch of tag op.
4. Installeer gewijzigde dependencies uit `requirements.txt`.
5. Voer `flask db upgrade` uit.
6. Start of herstart de WSGI-applicatie.
7. Controleer `/api/health` en log daarna in met een test- of beheeraccount.

## Verplichte productieconfiguratie

Gebruik `FLASK_ENV=production` en controleer minimaal:

- `SECRET_KEY`: willekeurig en minimaal 32 tekens;
- `PUBLIC_BASE_URL`: publieke `https://`-URL;
- `MAIL_SERVER` en `MAIL_FROM` als e-mailverzending actief is;
- `MAIL_USERNAME` en `MAIL_PASSWORD`: beide ingesteld of beide leeg;
- `MAIL_USE_TLS` en `MAIL_USE_SSL`: nooit beide `true`;
- `MM_API_KEY`: nodig voor functies die de Maior Memorix API aanspreken.

FNO weigert in productie bewust te starten bij onveilige kernconfiguratie.

## SQLite back-up

Maak bij voorkeur een consistente back-up met SQLite zelf terwijl de applicatie nog bereikbaar is:

```bash
python -c "import sqlite3; s=sqlite3.connect('instance/fno.db'); d=sqlite3.connect('instance/fno-backup.db'); s.backup(d); d.close(); s.close()"
```

Verplaats of hernoem het back-upbestand daarna naar een map buiten de actieve applicatiemap. Bewaar minimaal één recente back-up buiten dezelfde hostinglocatie.

## Herstel

1. Stop de WSGI-applicatie zodat er geen databasewrites meer plaatsvinden.
2. Maak eerst een extra kopie van de huidige `instance/fno.db`.
3. Vervang `instance/fno.db` door de gekozen back-up.
4. Voer `flask db upgrade` uit.
5. Start de applicatie opnieuw.
6. Controleer `/api/health`, login en een bestaande foto.

## Releasecontrole

Lokaal vóór merge of deployment:

```powershell
ruff check .
ruff format .
pytest
```

Controleer daarna handmatig minimaal registratie/verificatie, wachtwoordreset, e-mailwijziging, rolverzoek, MM-import, fotopagina, labels, opmerkingen en export.
