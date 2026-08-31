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

### Fotopagina

- OpenSeadragon geïntegreerd
- OverlayManager
- DragManager
- Persoonslabels
- Autosave
- Historie
- Opmerkingen
- Helpmodule

### Landingspagina

- Zoekfunctie
- Filters
- Drie thumbnailgroottes
- Lijstweergave
- Scrollpositie herstellen
- Responsive layout

### Huisstijl

- Centrale theme.css
- Huisstijl afgestemd op vortum-mullem.info
- Blauwe header
- Randloze panelen
- Centrale CSS-variabelen

### Kwaliteit

- Ruff
- Pytest
- Stabilisatieronde v0.1

### Adminomgeving

- Authenticatie en beheerder-CLI
- Rolgebaseerde autorisatie voor labelbeheer
- Dashboard met publicatiestatussen, open opmerkingen en recente activiteit
- Labelbeheerknoppen en hernummerpijlen verborgen voor bezoekers


### Adminomgeving en MM-import

- Authenticatie, rollen en autorisatie afgerond
- Beheerdashboard en volledige historie met CSV-export
- BrabantCloud-facets en bulkimport op onder andere deelcollectie
- Selecteerbare, filterbare en sorteerbare importvoorvertoning
- Lokale metadata, zichtbaarheid, voortgang en naamvergrendeling
- 229 tests geslaagd na stabilisatieronde 3.6.3

### Refactor en opschoning

- Backendrequests en metadata-extractie gecentraliseerd
- Frontendcontrollers vereenvoudigd
- Databasegebruik buiten repositories verwijderd
- API gebruikt uitsluitend publieke service-methoden
- Architectuurcontroles als regressietests toegevoegd
- Verouderde milestonebestanden en ongebruikte viewer-testafbeeldingen verwijderd
