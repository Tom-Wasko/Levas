# Stack technologiczny – Levas

Przeglądarkowa symulacja biznesowa. Silnik gry to czysty Python. Nad nim jest cienka warstwa Django: zapisuje decyzje,
udostępnia API JSON i serwuje panele gracza i mistrza gry. Wszystkie liczby gry leżą w plikach YAML.
Stan na 29.10.2026.

## W skrócie
| Warstwa | Technologia | Wersja w `.venv` |
|---|---|---|
| Język | Python | 3.13 (wymagany ≥ 3.12) |
| Silnik gry | czysty Python, pydantic (stan, schematy), numpy (popyt, losowość) | pydantic 2.14, numpy 2.5 |
| Optymalizacja | scipy `linprog` (HiGHS) – plan obsługi klientów w `kuchnia/operacje.py` | scipy 1.18 |
| Dane gry | YAML (PyYAML), walidowane schematami pydantic | PyYAML 6.0 |
| Aplikacja webowa | Django: API JSON i szablony stron | 5.2 |
| Logowanie | konta Django + django-allauth (opcjonalnie Microsoft / Entra ID szkoły) | allauth 65 |
| Baza danych | SQLite (`gra/db.sqlite3`, poza gitem) | wbudowana |
| Frontend | czysty JavaScript (moduły ES, bez bundlera), CSS, Chart.js w `static/vendor/` | – |
| Testy | pytest, pytest-django, hypothesis | pytest 9.1, hypothesis 6.170 |
| Jakość kodu | ruff (lint, linia ≤ 100) | 0.17 |
| Udostępnianie | `cloudflared` (darmowy tunel Cloudflare, `hostuj.bat`) | pobierany do `narzedzia/` |

Zależności są w `gra/requirements.txt` (instalacja do `gra/.venv`), konfiguracja narzędzi w `gra/pyproject.toml`.
Projekt nie używa Dockera, npm ani frameworków JS i nie potrzebuje usług zewnętrznych poza opcjonalnym logowaniem
Microsoft i tunelem.

## Architektura
```
przeglądarka ── HTML (szablony) ──▶ panel_gracza / panel_mg / konta
     │
     └── fetch JSON ──▶ api/widoki.py ──▶ gry/serwisy.py ──▶ silnik/gra.py (czysty Python)
                          │                   │                  │
                api/prezentacja.py       SQLite: Gra, Runda,     dane/*.yaml
                (widok `v` zakładek)     Decyzja, Druzyna
```

### Silnik (`gra/silnik/`)
- **Nie importuje Django**, więc boty, symulator balansu i testy działają bez serwera.
- **Rdzeń:**
  - `gra.py` – klasa `Gra`: konfiguracja, decyzje w rundach, stany po rundach i przeliczanie;
  - `runda.py` – przebieg tygodnia dzień po dniu;
  - `decyzje.py` – format decyzji (opisany w docstringu) i ich zastosowanie;
  - `model.py` – stan gry jako drzewo modeli pydantic (`StanGry`); `StanGry.kopia()` kopiuje stan bez raportów
    minionych rund, które są tylko do odczytu;
  - `dane.py` i `schematy.py` – wczytanie i walidacja YAML (`python -m silnik.dane sprawdz`);
  - `harmonogram.py` – odblokowanie zakładek i elementów w kolejnych tygodniach;
  - `boty.py` – decyzje botów (5 strategii × 4 poziomy);
  - `co_jesli.py` – warianty „co jeśli” w zakładce Analiza;
  - `limity.py`, `losowosc.py`.
- **Podpakiety mechanik:** `kuchnia/` (menu, jakość, operacje, dostawcy, magazyn, świeżość), `rynek/` (popyt,
  konkurencja, kalendarz miejski, reklama, promocje, handel), `ludzie/`, `nieruchomosci/`, `ksiegowosc/` (KPiR,
  rozliczenie, uzgodnienie kasy, biuro, urząd, środki trwałe), `pieniadze/` (banki, Harpagon, kasyno, portfel
  właściciela, zaległości), `swiat/` (zdarzenia, awarie), `wyniki/` (karta wyników, wnioski).
- **Pieniądze:** w stanie są liczbami całkowitymi w groszach (pola `…_gr`), a silnik liczy w złotych przez właściwości.
  `Decimal` służy tylko do zaokrągleń „połówki w górę”.
- **Losowość** ma jedno źródło: `losowosc.strumien(ziarno, runda, cel, *klucze)`. Każdy nazwany strumień to
  `numpy.random.Generator` z ziarnem wyprowadzonym skrótem. To samo ziarno i te same decyzje dają zawsze ten sam wynik.
- **Zapis gry (event sourcing):** baza trzyma konfigurację i decyzje, a nie stan. Silnik odtwarza stan, przeliczając
  rundy. Wczytana gra zostaje w pamięci serwera (`gry/serwisy.py`) z policzonymi stanami, dopóki nie zmieni się
  `Gra.zmieniono`. Gry można eksportować i importować jako `.json`.

### Dane gry (`gra/dane/`)
- Pliki główne: `zalozenia.yaml` (każdy parametr ma postać `{wartosc, pewnosc, zrodlo}`), `uslugi.yaml` (dania),
  `zasoby.yaml`, `sprzet.yaml`, `dostawcy.yaml`, `kandydaci.yaml`, `katalog.yaml`, `boty.yaml` i `podatki_2026.yaml`.
- Katalogi: `mapa/` (strefy, budynki, lokale, popyt, menu, banki, biura, Harpagon, promocje, reklama),
  `kalendarz/` (kalendarz miejski Lublina) i `zdarzenia/` (eventy w parkach, losowe, handel, kasyno, urząd…).
- **Żadnych liczb gry w kodzie silnika.** Pilnuje tego test `test_w_kodzie_silnika_nie_ma_liczb_gry`.
- Testy wzorów czytają zamrożoną kopię danych `testy/dane_zamrozone/` (od B2).

### Warstwa Django (`gra/`)
- `levas/` – ustawienia i URL-e. Ustawienia lokalne komputera trzyma `lokalne.json` (poza gitem). Zmienne
  środowiskowe: `LEVAS_DEBUG`, `LEVAS_HOSTY`, `LEVAS_HTTPS`, `LEVAS_SECRET_KEY` i ustawienia Microsoft
  (`LOGOWANIE_MICROSOFT.md`).
- `gry/` – modele `Gra`, `Runda`, `Decyzja` i `Druzyna`, serwisy z blokadą i transakcją, harmonogram automatycznego
  zamykania rund i komenda `zamykaj_rundy`.
- `api/` – widoki JSON (`widoki.py`) i budowa widoku zakładek (`prezentacja.py`).
- `konta/` – role (mistrz gry: grupa `mistrz_gry` albo superużytkownik; uczeń widzi tylko swoje drużyny), adapter
  allauth i komenda `konto`.
- `panel_gracza/` – strony gracza, instrukcja „Jak grać” i komendy `graj` (serwer lokalny 127.0.0.1:8765 z kontem
  mistrza gry), `hostuj` (serwer z tunelem Cloudflare) i `instrukcja_pdf` (PDF przez Edge albo Chrome bez okna).
- `panel_mg/` – panel mistrza gry `/mg/`.

### Frontend
- Strony to szablony Django (`*/templates/`). Dane zakładek przychodzą z API jako JSON.
- `panel_gracza/static/app.js` uruchamia panel. Zakładki to moduły ES w `static/zakladki/*.js` z rejestrem
  w `index.js`. Motywy kolorów (`motywy/*.css`, `motyw.js`): domyślny szmaragdowy, noc, grafik i talerze.
  Wykresy rysuje Chart.js (`static/vendor/chart.umd.min.js`).
- Składnię zakładki sprawdza `node --check plik.mjs` (skopiuj `.js` jako `.mjs`).

### Narzędzia poboczne
- `balans/symuluj.py` – gry samych botów do pomiaru balansu (`python -X utf8 -m balans.symuluj 12 sredni 7`).
- `narzedzia/cloudflared.exe` – pobierany raz przez `hostuj`.

## Testy i jakość
- `gra/testy/`: około 280 testów pytest w podfolderach odpowiadających podpakietom silnika (`rdzen/`, `kuchnia/`,
  `rynek/`…) i `aplikacja/` (API, panele, konta). Wspólne funkcje są w `pomocnicze.py`.
- Testy własności używają hypothesis (np. uzgodnienie kasy). Testy pilnują też determinizmu i scenariuszy co do
  grosza.
- ruff: linia ≤ 100, cel `py312`, reguły `E, F, W, I, B, UP`. Dla kodu przeniesionego z REVAS (`silnik/`,
  `api/prezentacja.py`, `testy/`) część reguł jest wyłączona w `pyproject.toml`. Globalnego `ruff format` nie używamy.

```
cd gra
.venv/Scripts/python -m pytest -q                          # ok. 2 min
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -X utf8 -m silnik.dane sprawdz
.venv/Scripts/python manage.py graj                        # albo start.bat
```

## Wydajność (orientacyjnie, laptop autora)
- Gra 5 botów × 18 rund liczy się w ok. 5 s, a widok gracza buduje się w ok. 0,1 s.
- Najwięcej kosztują: plan obsługi (scipy HiGHS), prognozy popytu botów i import scipy (ok. 1 s przy starcie).

## Konwencje
- Identyfikatory po polsku bez ogonków (`snake_case`, klasy `PascalCase`). Komentarze, docstringi i teksty dla
  gracza po polsku z ogonkami.
- Końce linii LF (`.gitattributes`), z wyjątkiem `*.bat` w CRLF.
- Historia liniowa na `main`: jeden commit na zadanie (`B3: …`), a postęp w `POSTEP.md`. Zasady pracy agentów
  opisuje `AGENTS.md`.
