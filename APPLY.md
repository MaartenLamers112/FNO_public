# FNO parser diagnosepatch

Deze patch wijzigt geen parserlogica.

Alleen de foutmelding bij een onbetrouwbare naamregel bevat nu:
- het positienummer;
- de oorspronkelijke waarde (`repr`).

Voorbeeld:
`Namenlijst bevat een onbetrouwbare naamregel: 33 = '?'`

Doel:
gericht vaststellen welke MM-regel A00221 of een ander kandidaatpatroon blokkeert.

Controle:
python -m ruff check .
python -m ruff format .
python -m pytest

Daarna opnieuw de parseranalyse voor alleen Vortum-Mullem downloaden.
