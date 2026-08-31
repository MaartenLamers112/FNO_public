# FNO ontwikkeltools

Start het menu vanuit de hoofdmap van het project:

```powershell
.\tools\FNO-Tools.ps1
```

Beschikbare acties:

- support-ZIP maken;
- lokale SQLite-database resetten;
- beheerder aanmaken;
- database back-uppen;
- database herstellen;
- projectcontrole uitvoeren met Ruff en Pytest.

## Veiligheid

- Een reset maakt eerst automatisch een databaseback-up.
- Reset en herstel vereisen de expliciete bevestiging `JA`.
- Er wordt nooit een standaardwachtwoord aangemaakt.
- De databasetools weigeren een niet-SQLite `DATABASE_URL`.
- Back-ups worden lokaal opgeslagen in `backups/`.

De map `backups/` hoort niet in Git of in een support-ZIP thuis.
