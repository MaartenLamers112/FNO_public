# FNO Development Guidelines

Dit document bevat de implementatieafspraken voor Foto Nummeraar Online. Het vult het Software Architecture & Functional Design en het Software Technical Design aan, maar introduceert geen nieuwe functionaliteit.

Het SAFD en STD blijven leidend voor functionele eisen, architectuur, gegevensstructuren en interfaces. Dit document beschrijft uitsluitend hoe de implementatie consequent wordt uitgevoerd.

## 1. Algemene uitgangspunten

Voor alle implementatiecode gelden de volgende principes:

* volg het definitieve STD;
* voeg geen nieuwe functionaliteit toe zonder expliciet besluit;
* kies de eenvoudigste passende oplossing;
* voorkom over-engineering;
* houd verantwoordelijkheden strikt gescheiden;
* lever complete, leesbare en testbare code;
* gebruik duidelijke Engelse namen in de broncode;
* gebruik korte docstrings waar de bedoeling niet direct duidelijk is.

De afhankelijkheidsrichting is altijd:

```text
REST API
    ↓
Services
    ↓
Repositories
    ↓
SQLAlchemy Models
    ↓
Database
```

Een lagere laag roept nooit een hogere laag aan.

## 2. Python en codekwaliteit

FNO gebruikt Python 3.14.

Voor codekwaliteit worden Ruff en pytest gebruikt.

Voer vóór iedere commit minimaal uit:

```powershell
python -m compileall app
ruff check .
ruff format .
ruff check .
pytest -v
```

Gebruik voor automatisch herstelbare Ruff-meldingen:

```powershell
ruff check . --fix
```

Gebruik `--unsafe-fixes` niet zonder afzonderlijke beoordeling.

## 3. Type hints

Nieuwe code gebruikt moderne Python-typeannotaties.

Voorbeelden:

```python
def get(self, entity_id: int) -> Photo | None: ...
```

```python
class BaseRepository[T]: ...
```

SQLAlchemy-relaties gebruiken `Mapped`:

```python
persons: Mapped[list["Person"]] = relationship(...)
```

Gebruik bij circulaire modelverwijzingen imports onder `TYPE_CHECKING`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.photo import Photo
```

Hierdoor zijn typen beschikbaar voor Ruff en editors zonder runtime-importcycli te veroorzaken.

## 4. Datums en tijdzones

Alle tijdstippen worden functioneel als UTC behandeld.

SQLite bewaart geen tijdzone-offset. Daarom worden datums in de database opgeslagen als naïeve UTC-datetimes.

Gebruik hiervoor uitsluitend:

```python
utc_now()
```

en bij externe of tijdzonebewuste invoer:

```python
normalize_utc(value)
```

Gebruik niet rechtstreeks:

```python
datetime.now()
```

voor databasewaarden.

## 5. Modellen

Modellen beschrijven uitsluitend:

* kolommen;
* relaties;
* constraints;
* eenvoudige representatie;
* eenvoudige modelhelpers.

Modellen bevatten geen bedrijfslogica, repositoryqueries of HTTP-logica.

Iedere tabel gebruikt:

* een interne integer-primary-key;
* enkelvoudige tabelnamen;
* snake_case voor kolommen;
* PascalCase voor Python-klassen.

Voorbeeld:

```python
class Photo(TimestampMixin, BaseModel):
    __tablename__ = "photo"
```

## 6. Repositories

Repositories vormen de enige toegang tot SQLAlchemy en de database.

Repositories bevatten uitsluitend:

* selecties;
* inserts;
* updates;
* deletes;
* tellingen;
* bestaancontroles;
* queryoptimalisatie.

Repositories bevatten geen:

* bedrijfsregels;
* autorisatie;
* HTTP-statuscodes;
* gebruikersmeldingen;
* communicatie met Maior Memorix.

Gebruik uitsluitend SQLAlchemy 2.x-stijl:

```python
statement = select(Photo).where(Photo.mm_id == mm_id)
return db.session.scalar(statement)
```

Gebruik niet:

```python
db.session.query(...)
```

Repositories committen alleen via een expliciete `save()`-aanroep. Hierdoor kunnen services meerdere wijzigingen binnen één transactie coördineren.

HTTP-specifieke helpers zoals `get_or_404()` horen niet in repositories.

## 7. Services

Alle bedrijfslogica bevindt zich in services.

Services zijn verantwoordelijk voor:

* functionele validatie;
* statusovergangen;
* coördinatie van repositories;
* transacties;
* historieregistratie;
* autorisatie via `AuthorizationService`;
* communicatie met gespecialiseerde externe services.

Services ontvangen repositories via constructor-injectie:

```python
class PhotoService(BaseService[PhotoRepository]):
    def __init__(
        self,
        repository: PhotoRepository | None = None,
    ) -> None:
        super().__init__(repository or PhotoRepository())
```

Dit maakt services afzonderlijk testbaar met mocks.

Service-methoden beschrijven use cases. Gebruik bijvoorbeeld:

```python
publish(photo_id)
hide(photo_id)
move_person(person_id, ...)
renumber_person(person_id, ...)
```

in plaats van algemene methoden zonder domeinbetekenis.

## 8. Domeinexceptions

Services gebruiken uitsluitend FNO-domeinexceptions voor verwachte functionele fouten:

* `ValidationError`
* `ConflictError`
* `NotFoundError`
* `AuthorizationError`

Gebruik geen generieke `ValueError` voor domeinfouten.

Voorbeeld:

```python
raise ConflictError(
    "Rol bestaat al.",
    code="ROLE_ALREADY_EXISTS",
    details={
        "role_name": normalized_name,
    },
)
```

### Naamgeving van foutcodes

Foutcodes gebruiken hoofdletters en underscores:

```text
<RESOURCE>_<PROBLEEM>
```

Voorbeelden:

```text
ROLE_NAME_REQUIRED
ROLE_ALREADY_EXISTS
PHOTO_NOT_FOUND
PHOTO_ALREADY_PUBLISHED
PERSON_NOT_FOUND
LABEL_NUMBER_ALREADY_EXISTS
COMMENT_NOT_FOUND
COMMENT_ALREADY_CLOSED
USER_NOT_FOUND
USER_DISABLED
USER_ALREADY_EXISTS
```

Een foutcode beschrijft de stabiele technische betekenis van een fout. De Nederlandse fouttekst mag later wijzigen of vertaald worden.

## 9. Tests voor exceptions

Tests controleren:

* het exceptiontype;
* de foutcode;
* details, wanneer aanwezig.

Tests controleren normaal gesproken niet de exacte Nederlandse fouttekst.

Gebruik:

```python
with pytest.raises(ConflictError) as exc:
    service.create(name="administrator")

assert exc.value.code == "ROLE_ALREADY_EXISTS"
assert exc.value.details == {
    "role_name": "administrator",
}
```

Gebruik niet als primaire controle:

```python
with pytest.raises(
    ConflictError,
    match="bestaat al",
):
    ...
```

De fouttekst is alleen onderdeel van een test wanneer de exacte tekst zelf functioneel relevant is.

## 10. REST API

API-modules bevatten uitsluitend:

* routing;
* request parsing;
* technische invoervalidatie;
* authenticatie;
* autorisatieaanroep;
* serviceaanroepen;
* response-opbouw;
* HTTP-statuscodes.

API-routes bevatten geen databasequeries of bedrijfslogica.

Domeinexceptions worden later centraal vertaald naar HTTP-responses:

| Exception            | HTTP-status |
| -------------------- | ----------: |
| `ValidationError`    |         422 |
| `AuthorizationError` |         403 |
| `NotFoundError`      |         404 |
| `ConflictError`      |         409 |

De response krijgt een consistente structuur:

```json
{
  "error": {
    "code": "ROLE_ALREADY_EXISTS",
    "message": "Rol bestaat al.",
    "details": {
      "role_name": "administrator"
    }
  }
}
```

## 11. Teststrategie

Iedere nieuwe use case krijgt tests voor minimaal:

* succesvolle verwerking;
* ontbrekende objecten;
* ongeldige invoer;
* conflicterende gegevens;
* belangrijke statusovergangen;
* repository-interacties waar mocks nuttig zijn.

Tests gebruiken de geïsoleerde testdatabase uit `TestingConfig`. De echte database in `instance/fno.db` mag nooit door tests worden aangepast.

Voorkom dubbele tests die exact dezelfde code en foutconditie controleren.

## 12. Git-werkwijze

Maak commits per logisch afgerond onderdeel.

Voorbeelden:

```text
Implementeer PersonRepository
Voeg domeinexceptions toe
Baseer fotonavigatie op foto-ID
Refactor servicelaag met repository-injectie
```

Voer vóór iedere commit de volledige kwaliteitscontrole uit:

```powershell
python -m compileall app
ruff check .
ruff format .
ruff check .
pytest -v
```

Commit geen:

* `.env`;
* `.venv`;
* SQLite-databasebestanden;
* logbestanden;
* tijdelijke bestanden;
* geheime sleutels of API-tokens.

## 13. Documentatie

Het SAFD en STD worden alleen aangepast wanneer:

* functionaliteit verandert;
* architectuur verandert;
* het datamodel functioneel verandert;
* een fout in het ontwerp wordt ontdekt.

Kleine implementatiekeuzes, codeconventies en testafspraken worden in dit document bijgehouden.

Dit document wordt bijgewerkt zodra een nieuwe algemene implementatieregel wordt ingevoerd.
