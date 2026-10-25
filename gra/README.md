# Levas – gra

Symulacja biznesowa kebabu w Lublinie, budowana na bazie lokalnego Revasa („Klub fitness”). Na razie (krok 2
[planu](../notatki/Plan%20implementacji.md)) to nadal gra Revasa przeniesiona na Django – przebranżowienie na kebab
i rundy tygodniowe dojdą w kolejnych zadaniach (postęp: [`POSTEP.md`](../POSTEP.md)).

## Uruchomienie

Kliknij dwa razy **`start.bat`**. Za pierwszym razem utworzy środowisko Pythona (`.venv`, potrzebny Python 3.12+)
i zainstaluje pakiety. Gra otworzy się w przeglądarce pod adresem **http://127.0.0.1:8765**. Zamknięcie czarnego
okna kończy grę; gry zapisują się w bazie `db.sqlite3`.

Ręcznie (z folderu `gra`):

```
.venv\Scripts\python manage.py graj            # migracje + serwer + przeglądarka
.venv\Scripts\python manage.py runserver 8765  # sam serwer (z przeładowaniem po zmianie kodu)
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
```

## Jak się gra

Strona startowa → „Nowa gra”: firmy graczy (na tym komputerze) i boty (Zrównoważony, Tani masowy, Premium,
Agresywny marketing, Naśladowca). Zakładki są jak w Revasie: Oferta → Inwestycje → HR → Dostawcy → Marketing →
Sprzedaż → Finanse → Lista błędów → **Wyślij decyzje**. Przełącznik **Decyzje / Wyniki** pokazuje wyniki
poprzedniej rundy, strzałki ‹ › przełączają podgląd poprzednich rund. **Analiza** liczy przewidywany wynik rundy
dla zapisanych wariantów decyzji. W treningu można cofnąć ostatnią rundę.

**Wygląd** (lista w nagłówku): klasyczny, *Talerze*, *Grafik*, *Noc* – pliki `panel_gracza/static/motywy/*.css`,
przełącznik `panel_gracza/static/motyw.js`.

## Budowa

| Folder | Co zawiera |
|---|---|
| `silnik/` | silnik gry (czysty Python, bez Django): rynek, operacje, finanse, karta wyników, boty |
| `dane/`, `zalozenia.json` | dane i niepewne parametry gry |
| `levas/` | projekt Django (ustawienia, adresy) |
| `gry/` | modele `Gra`, `Runda`, `Decyzja` (event sourcing: konfiguracja + decyzje, stan liczy silnik) i `serwisy.py` |
| `api/` | widoki JSON dla zakładek (`widoki.py`) i budowa widoku rundy (`prezentacja.py`) |
| `panel_gracza/` | strony gracza, zakładki w czystym JS (`static/zakladki/`), Chart.js, komenda `graj` |
| `testy/` | pytest (mechaniki Revasa, zasady rund, API) |

`WIEDZA_O_GRZE.md` – opis mechanik Revasa, z których korzysta silnik.
