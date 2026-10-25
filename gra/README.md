# Levas – gra

Symulacja biznesowa kebabu w Lublinie, budowana na bazie lokalnego Revasa („Klub fitness”). Na razie (krok 2
[planu](../notatki/Plan%20implementacji.md)) to mechanika Revasa na Django z danymi kebaba (dania, kucharze, kasa,
składniki, dostawcy jedzenia), rundami tygodniowymi (26 tygodni) i podstawowym panelem mistrza gry
(postęp: [`POSTEP.md`](../POSTEP.md)).

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
.venv\Scripts\python -m silnik.dane sprawdz     # dane/*.yaml: schematy i odwołania
```

## Jak się gra

Strona startowa → „Nowa gra”: firmy graczy (na tym komputerze) i boty (zrównoważony, tani, premium,
agresywny marketing, naśladowca). Zakładki są jak w Revasie: Oferta (menu) → Inwestycje → HR → Dostawcy → Marketing →
Sprzedaż → Finanse → Lista błędów → **Wyślij decyzje**. Przełącznik **Decyzje / Wyniki** pokazuje wyniki
poprzedniej rundy, strzałki ‹ › przełączają podgląd poprzednich rund. **Analiza** liczy przewidywany wynik rundy
dla zapisanych wariantów decyzji. W treningu można cofnąć ostatnią rundę.

**Panel mistrza gry** – http://127.0.0.1:8765/mg/ (na razie bez logowania – tryb deweloperski): nowa gra
(drużyny, liczba rund, kapitał startowy, boty tak/nie i które strategie), a w grze zakładki **Decyzje** (które
drużyny wysłały decyzje, *Zamknij rundę* – także bez decyzji wszystkich, *Cofnij rundę*, strona każdej firmy,
plik gry) i **Wyniki** (ranking według średniej karty wyników, dochód netto, gotówka, zadłużenie, wykresy rund).
Runda zamyka się sama, gdy wszystkie drużyny wyślą decyzje.

**Wygląd** (lista w nagłówku): klasyczny, *Talerze z kebabem*, *Grafik zmian*, *Kebab nocą* – pliki `panel_gracza/static/motywy/*.css`,
przełącznik `panel_gracza/static/motyw.js`.

## Budowa

| Folder | Co zawiera |
|---|---|
| `silnik/` | silnik gry (czysty Python, bez Django): rynek, operacje, finanse, karta wyników, boty |
| `dane/*.yaml` | dane gry (kebab) i założenia (niepewne parametry), każdy z `zrodlo`; sprawdzenie: `python -m silnik.dane sprawdz` |
| `dane_revas/` | dane oryginalnego Revasa (fitness) – wzorzec, na którym testy sprawdzają mechanikę: `python -m silnik.dane sprawdz dane_revas` |
| `levas/` | projekt Django (ustawienia, adresy) |
| `gry/` | modele `Gra`, `Runda`, `Decyzja` (event sourcing: konfiguracja + decyzje, stan liczy silnik) i `serwisy.py` |
| `api/` | widoki JSON dla zakładek (`widoki.py`) i budowa widoku rundy (`prezentacja.py`) |
| `panel_gracza/` | strony gracza, zakładki w czystym JS (`static/zakladki/`), Chart.js, komenda `graj` |
| `panel_mg/` | panel mistrza gry (`/mg/`): nowa gra, prowadzenie rund, wyniki drużyn; dane z `GET /api/gry/<id>/mg` |
| `testy/` | pytest (mechaniki Revasa, zasady rund, API) |

`WIEDZA_O_GRZE.md` – opis mechanik Revasa, z których korzysta silnik (liczby z gier – w `dane_revas/`).

### Kalendarz rund

`katalog.yaml` → `rundy.kalendarz`: okres (`tydzien` / `miesiac`), rund w roku, data startu. Kebab: runda = tydzień,
26 rund od 5.10.2026, 100 000 zł i gotowy lokal (`stanowiska.startowe`: kuchnia z rożnem, frytownicą i lodówką,
kasa). Revas (`dane_revas/`): runda = miesiąc od stycznia. Kwoty w danych są **miesięczne** (pensje, czynsz,
utrzymanie) – silnik księguje je na rundę przez `Dane.na_runde` (× 12 / rund w roku); oprocentowanie roczne dzieli
się przez rundy w roku, okresy lokat i kredytów liczą się w rundach, sezonowość – według miesiąca rundy
(`Dane.miesiac_rundy`, tydzień należy do miesiąca swojego czwartku). Koszty jednorazowe (zakupy, rekrutacja,
reklama, księgowość za dokument) się nie skalują. Runda 1 to przygotowanie – sprzedaż od rundy 2. Strona gracza
dostaje kalendarz w `v.gra.kalendarz` (`wspolne.js`: `nazwaRundy`, `naRunde`, `OKRES`).

### Słownik: nazwy w kodzie a kebab

Silnik i klucze danych mają jeszcze nazwy z Revasa (zmiana nazw razem z przebudową w kroku 3a):

| W kodzie i danych | W grze |
|---|---|
| usługa (`uslugi`, `oferta`) | danie |
| zasób (`zasoby`) | składnik |
| prowadzący, `godziny_prowadzacego` | kucharz, czas kuchni na porcję |
| recepcja, `godziny_recepcji`, `liczba_recepcjonistow` | kasa, czas przy kasie, liczba kasjerów |
| `grupa` | porcji naraz (w kebabie 1) |
| `utrzymanie_klubu` | utrzymanie lokalu |
| stanowisko typu `kuchnia` / `kasa` | stanowisko kuchenne / kasowe (nazwy i zawody: `katalog.yaml` → `stanowiska.typy`) |
