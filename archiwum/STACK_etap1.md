# Stack technologiczny – Levas (Etap 1, 25.10.2026 – archiwum; aktualny: `dokumentacja/STACK.md`)

Przeglądarkowa symulacja biznesowa: czysty silnik gry w Pythonie + cienka warstwa Django,
która przechowuje stan i pokazuje strony. Wszystkie liczby gry leżą w plikach YAML.

## W skrócie
| Warstwa | Technologia | Wersja (w `.venv`) |
|---|---|---|
| Język | Python | 3.13 (wymagane ≥ 3.12) |
| Silnik gry | czysty Python + pydantic + numpy | pydantic 2.14, numpy 2.5 |
| Dane gry | YAML (PyYAML), walidowane schematami pydantic | PyYAML 6.0 |
| Aplikacja webowa | Django (szablony renderowane po stronie serwera) | 5.2 |
| Baza danych | SQLite (`db.sqlite3`) | wbudowana w Pythona |
| Frontend | HTML z szablonów Django, CSS w szablonie bazowym, odrobina czystego JS | – |
| Testy | pytest, pytest-django, hypothesis | pytest 9.1, hypothesis 6.170 |
| Jakość kodu | ruff (lint + formatowanie) | 0.17 |
| Kontrola wersji | git | – |

Zależności: `requirements.txt` (instalacja do `.venv` w repozytorium). Konfiguracja narzędzi:
`pyproject.toml`. Bez Dockera, bez usług zewnętrznych, bez frameworków JS.

## Architektura
```
przeglądarka ──HTTP──▶ Django (panel_gracza, panel_mg) ──▶ gry/serwisy.py ──▶ silnik/ (czysty Python)
                              │                                                    │
                              └── SQLite: Gra.stan_json, Migawka, dziennik ◀───────┘
                                                                     dane/*.yaml ──┘
```

### Silnik (`silnik/`) – czysty Python
- **Nie importuje Django** – można go uruchamiać i testować bez serwera (boty, symulator balansu).
- **Stan gry** (`silnik/stan.py`): jeden dokument – drzewo modeli pydantic (`StanGry`,
  `extra="forbid"`), zapisywany i odtwarzany jako JSON (`do_json` / `z_json`), z numerem
  `WERSJA_STANU`.
- **Akcje graczy** (`silnik/akcje.py`): każda decyzja drużyny to akcja walidowana przez silnik;
  zamknięcie rundy (`silnik/gra.py`, `rozliczenie.py`) liczy tydzień, księgowość i raporty.
- **Pieniądze** (`silnik/pieniadze.py`): liczby całkowite w groszach; `Decimal` tylko do
  zaokrągleń (VAT i kwoty „połówki w górę”, zaliczka PIT do pełnych złotych).
- **Losowość** (`silnik/losowosc.py`): jedyne źródło losowości – nazwane strumienie
  `numpy.random.Generator(PCG64)` z ziarnem wyprowadzanym SHA-256 z (ziarno gry, tydzień, cel,
  klucze). To samo ziarno i te same decyzje dają zawsze ten sam wynik.

### Dane gry (`dane/`)
- YAML w katalogach tematycznych (`menu/`, `sklepy/`, `praca/`, `mapa/`, `finanse/`,
  `kalendarz/`, `zdarzenia/`, `boty/` …) oraz `parametry.yaml` i `podatki_2026.yaml`.
- `silnik/dane.py` wczytuje wszystko do niemutowalnych `Katalogi` (z hashem wersji danych),
  walidując schematami z `silnik/schematy.py`. Sprawdzenie: `python -m silnik.dane sprawdz`.
- Zasada: **żadnych liczb gry w kodzie** – tylko w `dane/*.yaml`.

### Warstwa Django
- Projekt `levas/` (ustawienia, URL-e), aplikacje:
  - `gry/` – modele (`Gra` ze stanem w polu tekstowym JSON, `Firma`, `Migawka` do cofania rund),
    serwisy w `transaction.atomic()`, komendy `gra_demo` i `zamykaj_rundy`;
  - `panel_gracza/` – panel drużyny (pulpit, lokal, menu, pracownicy, sklepy, finanse, handel…),
    formularze i własne tagi szablonów;
  - `panel_mg/` – panel mistrza gry (zakładanie gry, zamykanie/cofanie rundy, decyzje MG).
- Minimalny zestaw: bez `auth`, `admin` i sesji – **tryb deweloperski bez logowania**
  (`DEBUG = True`, tylko localhost / sieć szkolna). Język `pl`, strefa `Europe/Warsaw`.

### Frontend
- Strony renderowane po stronie serwera szablonami Django (`szablony/`, `*/templates/`).
- Style wbudowane w `szablony/baza.html`; JavaScript tylko punktowo (np. karta dania – food cost
  liczony na bieżąco). Brak bundlera, npm i bibliotek zewnętrznych.

### Narzędzia poboczne
- `boty/` + `silnik/boty.py` – boty regułowe z poziomami trudności, grające tym samym API akcji.
- `balans/symuluj.py` – symulator balansu: gry samych botów równolegle (`ProcessPoolExecutor`),
  wyniki w CSV + raport Markdown (`python -m balans.symuluj`).
- `gielda/` – zaczep pod integrację z zewnętrznym modułem giełdy (na razie pusty).

## Testy i jakość
- `testy/` – pytest (`pytest-django` dla warstwy Django, `DJANGO_SETTINGS_MODULE` w
  `pyproject.toml`), testy własności w **hypothesis** (np. uzgodnienie kasy), scenariusze
  liczbowe z notatek co do grosza.
- **ruff**: długość linii 100, cel `py312`, reguły `E, F, W, I, B, UP`; formatowanie
  `ruff format`.

```
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format .
.venv/Scripts/python.exe manage.py runserver
```

## Konwencje
- Kod po polsku: identyfikatory bez polskich znaków, `snake_case` dla funkcji i zmiennych,
  `PascalCase` dla klas; komentarze, docstringi i interfejs po polsku.
- Końce linii LF (`.gitattributes`), wyjątek: `*.bat` w CRLF.
- Historia liniowa na `main`, 1 commit = 1 zadanie (`F1.3: …`), postęp w `POSTEP.md`.
