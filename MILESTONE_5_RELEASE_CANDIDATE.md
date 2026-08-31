# Milestone 5 Release Candidate

Deze versie rondt de technische werkzaamheden van Milestone 5 af.

## Inbegrepen

- foto-export met altijd zwarte labels;
- TXT-, CSV- en JSON-export;
- OpenVINO Auto label met blokkering van dubbele acties in de frontend;
- controle op ontbrekende en ongeldige Auto label-uploads;
- maximale requestgrootte van 10 MB;
- begrijpelijke foutmelding bij te grote uploads;
- roterende applicatielogging;
- veilige standaarden voor sessiecookies;
- aanvullende regressietests.

## Nog niet inbegrepen

- gebruikersacceptatietest;
- verwerking van acceptatiebevindingen;
- definitieve documentatie-update;
- v1.0-release en Git-tag.

Deze onderdelen volgen in Milestone 6.

## Lokale controle

```powershell
ruff check . --fix
ruff format .
ruff check .
ruff format --check .
pytest
```

## Handmatige controle

1. Exporteer een foto met zowel lege als ingevulde namen; alle labels moeten zwart zijn.
2. Controleer TXT, CSV en JSON op volledige inhoud.
3. Voer Auto label tweemaal uit; de tweede uitvoering mag geen duplicaten maken.
4. Probeer een tekstbestand als Auto label-upload; dit moet worden geweigerd.
5. Controleer dat `logs/application.log` wordt aangemaakt.
6. Controleer als bezoeker dat beheerexports en Auto label niet toegankelijk zijn.
