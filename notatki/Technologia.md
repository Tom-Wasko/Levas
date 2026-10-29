`archiwum/Plan implementacji.md` · [[Różnice Revas – Levas]]

# Technologia

Na podstawie `STACK.md` (ten sam plik leży w `Pulpit/Revas` i `Pulpit/Levas/levas_gra`). Różnice względem `STACK.md` są oznaczone **(zmiana)**.

## W skrócie
| Warstwa | Technologia |
|---|---|
| Język | Python 3.13 (wymagane ≥ 3.12) |
| Silnik gry | czysty Python + pydantic 2 + numpy – **silnik Revasa** przepisany z dataclasses na pydantic **(zmiana)** |
| Dane gry | YAML (PyYAML), walidowane schematami pydantic |
| Aplikacja webowa | Django 5.2 |
| Baza danych | SQLite (`db.sqlite3`) |
| Frontend | zakładki Revasa w czystym JS (`static/zakladki/*.js`) + Chart.js, dane z widoków JSON w Django **(zmiana – STACK.md zakłada szablony Django)** |
| Logowanie | `django.contrib.auth` + django-allauth (konto Microsoft) **(zmiana – STACK.md zakłada brak logowania)** |
| Testy | pytest, pytest-django, hypothesis |
| Jakość kodu | ruff (lint + formatowanie) |
| Kontrola wersji | git |

Kod gry: `Pulpit/Revas/Levas/gra`. Zależności w `requirements.txt`, instalacja do `.venv`, konfiguracja w `pyproject.toml`. Bez Dockera i bez frameworków JS.

## Architektura
```
przeglądarka ──HTTP/JSON──▶ Django (api, panel_gracza, panel_mg, konta) ──▶ gry/serwisy.py ──▶ silnik/
                                   │                                                          │
                                   └── SQLite: Gra (konfiguracja, ziarno), Decyzja, Migawka ◀──┘
                                                                              dane/*.yaml ──┘
```

### Silnik (`silnik/`)
- **Nie importuje Django** – da się go uruchamiać i testować bez serwera (boty, symulator balansu).
- **Event sourcing jak w Revasie:** stan gry = konfiguracja + ziarno + decyzje wszystkich drużyn. Przeliczenie od rundy 1 daje zawsze ten sam wynik. Migawki stanu po każdej rundzie są tylko pamięcią podręczną (szybkie wczytanie, cofanie rundy = usunięcie decyzji i migawek od tej rundy).
- **Stan gry:** drzewo modeli pydantic (`extra="forbid"`), zapisywany jako JSON z numerem `WERSJA_STANU`. Model rośnie z modelu Revasa (`silnik/model.py`) – nie przenosimy całego starego `stan.py`.
- **Pieniądze:** liczby całkowite w groszach; `Decimal` tylko do zaokrągleń (VAT, zaliczka PIT do pełnych złotych).
- **Losowość:** jedyne źródło – nazwane strumienie `numpy.random.Generator(PCG64)` z ziarnem wyprowadzanym SHA-256 z (ziarno gry, runda, cel, klucze).

### Dane gry (`dane/`)
- YAML w katalogach tematycznych (`menu/`, `sklepy/`, `praca/`, `mapa/`, `finanse/`, `kalendarz/`, `zdarzenia/`, `boty/`) oraz `parametry.yaml` i `podatki_2026.yaml`.
- Każda niepewna liczba ma pole `zrodlo` (potwierdzone / orientacyjne / roboczo) – zastępuje `zalozenia.json` Revasa.
- Zasada: **żadnych liczb gry w kodzie**. Sprawdzenie danych: `python -m silnik.dane sprawdz`.

### Warstwa Django
- Projekt `levas/`, aplikacje:
  - `gry/` – modele (`Gra`, `Druzyna`, `Decyzja`, `Migawka`), serwisy w `transaction.atomic()`, komenda `zamykaj_rundy` (zamykanie o ustalonej godzinie);
  - `api/` – widoki JSON dla zakładek (odpowiednik `serwer/app.py` Revasa);
  - `panel_gracza/` – strona z zakładkami;
  - `panel_mg/` – panel mistrza gry;
  - `konta/` – logowanie (Microsoft + własny login), role: uczeń, mistrz gry.
- Język `pl`, strefa `Europe/Warsaw`.

### Narzędzia poboczne
- `silnik/boty.py` + `dane/boty/` – boty z poziomami trudności, grające tym samym API decyzji.
- `balans/symuluj.py` – gry samych botów do kalibracji (krok 5).
- `gielda/` – pusty zaczep pod moduł giełdy kolegi.

## Testy i jakość
- `testy/` – pytest, testy własności w hypothesis (np. uzgodnienie kasy z KPiR), scenariusze liczbowe co do grosza.
- ruff: długość linii 100, cel `py312`, reguły `E, F, W, I, B, UP`.

```
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe manage.py runserver
```

## Konwencje
- Kod po polsku: identyfikatory bez polskich znaków, `snake_case` dla funkcji i zmiennych, `PascalCase` dla klas; komentarze i interfejs po polsku.
- Końce linii LF (`.gitattributes`), wyjątek: `*.bat` w CRLF.
- Historia liniowa na `main`, 1 commit = 1 zadanie z `archiwum/Plan implementacji.md` (np. `F3a.9: banki ze specjalizacjami`), postęp w `POSTEP.md`.
- Serwer produkcyjny – do decyzji później.
