# Milestone 6.1–6.6

Deze patch bevat:

- automatisch hernummeren in visuele leesvolgorde;
- een conservatievere MM-beschrijvingsparser;
- contextafhankelijke help voor overzicht, foto en beheer;
- publieke pagina's voor privacy, disclaimer en contact;
- tooltips voor belangrijke fotoknoppen;
- de CSV-menu-ID-fix;
- zwarte labels in de foto-export.

## Lokale controle

```powershell
ruff check . --fix
ruff format .
ruff check .
ruff format --check .
pytest
```

## Handmatig controleren

1. Open Help op overzicht, foto en beheer en controleer de verschillende inhoud.
2. Controleer Privacy, Disclaimer en Contact zonder in te loggen.
3. Plaats labels in meerdere rijen en gebruik Hernummer.
4. Controleer dat namen en opmerkingen gekoppeld blijven aan dezelfde persoon.
5. Controleer opnieuw de JPG-, TXT- en CSV-export.
6. Test een MM-beschrijving met een expliciete kop `Namen:` en een onbetrouwbare lijst.
