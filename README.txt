FNO Auth Step 3 - UI fix

Voer uit vanuit de root van FNO-public:

    git apply --check step3_ui_fix.patch
    git apply step3_ui_fix.patch

Daarna:

    python -m ruff check .
    python -m ruff format .
    python -m pytest

Deze patch:
- maakt het e-mailveld gelijk aan de andere registratievelden;
- maakt onbevestigde user-accounts volledig read-only in de foto-UI;
- voegt Registreren en Verificatiemail opnieuw sturen toe aan het sleutelmenu;
- laat gewone users hun eigen wachtwoord wijzigen via de API;
- voegt regressietests toe.
