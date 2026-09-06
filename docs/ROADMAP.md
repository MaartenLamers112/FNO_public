# Foto Nummeraar Online (FNO)

# Roadmap

## Status

| Onderdeel | Status |
|-----------|--------|
| Fotopagina en labeling | ✅ Gereed |
| Landingspagina | ✅ Gereed |
| Adminomgeving en MM-import | ✅ Gereed |
| MM-vergelijking en rapportage | ✅ Gereed |
| Accountbeheer en rollen | ✅ Gereed |
| Productieplaatsing | ✅ Gereed |
| Productie-hardening | 🚧 Actuele batch |
| Performance en laatste v1.0-polish | ⏳ Hierna |

---

# Gereed voor v1.0

- OpenSeadragon-fotopagina met labels, namen, opmerkingen en export
- Lokale FNO-metadata zonder terugschrijven naar Maior Memorix
- Automatische FNO-MM-vergelijking en vergelijkingrapportage
- Bulkimport vanuit Maior Memorix/BrabantCloud
- Rollen `user`, `employee` en `administrator`
- Registratie en e-mailverificatie
- Wachtwoordherstel per e-mail
- Wijzigen van eigen e-mailadres met herverificatie
- Rolupgrade-aanvragen met beheerdersbeoordeling
- Stabiele fotolinks en Nederlandse viewer-tooltips
- Logging, CSRF, Alembic en productieconfiguratie
- Live plaatsing op een WSGI-host met SQLite

---

# Productie-hardening

## Doel

De bestaande functionaliteit veilig en reproduceerbaar richting versie 1.0 brengen zonder nieuwe productfunctionaliteit toe te voegen.

## Scope

- fail-fast controle op productieconfiguratie
- regressietests voor kritieke productie-instellingen
- deployment-, back-up- en herstelprocedure vastleggen
- account- en autorisatie-edge-cases controleren
- projectdocumentatie in lijn brengen met de actuele software

---

# Daarna: laatste v1.0-polish

- performance van overzicht en grote datasets meten
- resterende echte UI-regressies oplossen
- gebruikersacceptatietest op productieomgeving
- definitieve v1.0 releasecheck en tag

Nieuwe ideeën en uitbreidingen blijven buiten v1.0 tenzij ze tijdens de releasecontrole als blocker blijken.
