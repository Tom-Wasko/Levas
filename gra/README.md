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
poprzedniej rundy, strzałki ‹ › przełączają podgląd poprzednich rund. Limity (`silnik/limity.py`): najwyżej
3 nowych pracowników na rundę (zatrudnienia i oferty podkupienia razem) i kolejny lokal co 3 rundy – zapis
decyzji z przekroczeniem jest odrzucony. **Zdarzenia** (`silnik/zdarzenia.py`, `dane/zdarzenia/parki.yaml`):
od rundy 2 co tydzień w jednym z parków zaczyna się historia, ta sama dla wszystkich drużyn; reakcja kosztuje czas
właściciela, gotówkę albo porcje, ciąg dalszy przychodzi w kolejnych rundach. **Magazyn** (`silnik/magazyn.py`,
`dane/zdarzenia/magazyn.yaml`, `zalozenia.yaml` → `magazyn`): w grze z lokalami nie ma kosztu magazynowania ani zwrotów
do dostawcy – co nie zmieści się w chłodni i zamrażarce lokalu, jedzie do wynajętej chłodni (za litr, krótszy termin);
towar w wynajmie i przeterminowane jedzenie zwiększają szansę kontroli sanepidu (mandat poza KPiR, mniej klientów),
a duży zapas z krótkim terminem może wywołać telefon z banku żywności. **Agencje reklamowe** (`silnik/reklama.py`,
`dane/mapa/reklama.yaml`): w grze z lokalami zamiast reklamy tradycyjnej i internetowej z Revasa – cztery agencje na
mapie (druk, internet, radio i billboardy, wydarzenia), kampania = agencja × kanał × strefa; poszerza pulę klientów
strefy i przyciąga jej mieszkańców do firmy, kampanie tego samego rodzaju w strefie się zagłuszają, powtórka zaraz
po poprzedniej działa słabiej, po końcu efekt wygasa. **Promocje** (`silnik/promocje.py`, `dane/mapa/promocje.yaml`):
2 za 1, zestaw z napojem, happy hours, karta stałego klienta i zniżka studencka z własną, ozdobną nazwą drużyny;
przyciągają objętych klientów (dni tygodnia, strefy), ale obcinają cenę (rabat, porcje gratis), trwają do
wyłączenia, a ich siła z czasem słabnie albo (karta) rośnie. **Licytacje i przejęcia** (`silnik/przejecia.py`): o lokal
wybrany w jednej rundzie przez kilka drużyn decyduje najwyższa oferta (remis – losowanie), budynek wynajmowany przez
inną drużynę można kupić (najemca płaci czynsz nowemu właścicielowi) albo wykupić własny, a właściciel może
wypowiedzieć najem – po 4 rundach najemca się wyprowadza, nakłady rozlicza się wg KC art. 676. **Wypadki
i ubezpieczenia** (`silnik/awarie.py`, `dane/zdarzenia/losowe.yaml`): od rundy 4 w lokalu drużyny może zacząć się
wypadek – zwykle komiczna historia w kilku scenach, która kończy się szkodą; polisy TUW „Pod Koziołkiem” (lokal,
sprzęt, OC) po karencji zwracają część szkody. **Urząd i sanepid** (`silnik/urzad.py`, `dane/zdarzenia/urzad.yaml`):
sanepid odbiera każdy lokal przed pierwszą rundą działania – bez sprzątania odmawia i lokal rusza później; poziom
higieny kosztuje co rundę za lokal i zmienia szansę oraz wynik kontroli, a skargi z historii ściągają sanepid
częściej. **Analiza** liczy przewidywany wynik rundy
dla zapisanych wariantów decyzji. W treningu można cofnąć ostatnią rundę.

**Panel mistrza gry** – http://127.0.0.1:8765/mg/ (tylko rola mistrza gry): nowa gra
(drużyny, liczba rund, kapitał startowy, boty tak/nie i które strategie), a w grze zakładki **Decyzje** (które
drużyny wysłały decyzje, *Zamknij rundę* – także bez decyzji wszystkich, *Cofnij rundę*, strona każdej firmy,
plik gry), **Wyniki** (ranking według średniej karty wyników, dochód netto, gotówka, zadłużenie, wykresy rund)
i **Drużyny** (skład drużyn, nowe konta uczniów, nowe hasło). Runda zamyka się sama, gdy wszystkie drużyny
wyślą decyzje. Przy zakładaniu gry każdy bot dostaje poziom (łatwy / średni / trudny – na razie zapisany, działa
od F4.4), poziom można zmienić w trakcie gry (od następnej rundy).

**Prowadzenie gry** (zakładka *Decyzje* panelu mistrza gry):

- *Wstrzymaj grę* – drużyny widzą decyzje, ale ich nie zmieniają ani nie wysyłają, runda się nie zamyka
  (cofnięcie rundy działa); *Wznów grę* liczy następny termin od chwili wznowienia,
- *Zamykanie rund o stałej porze* – tygodniowe terminy (np. wtorek 8:00 i czwartek 8:00). Runda zamyka się
  w pierwszym terminie po zamknięciu poprzedniej, jak po kliknięciu *Zamknij rundę*; drużyny widzą termin na
  pasku i w *Wyślij decyzje*. Terminy zamyka komenda uruchamiana co kilka minut:

  ```
  .venv\Scripts\python manage.py zamykaj_rundy              # raz – np. w Harmonogramie zadań Windows co 5 min
  .venv\Scripts\python manage.py zamykaj_rundy --petla 60   # albo w osobnym oknie: sprawdza co 60 s
  ```

  (Linux: `*/5 * * * * cd /sciezka/gra && .venv/bin/python manage.py zamykaj_rundy` w crontab),
- strony drużyn uczniów mistrz gry ogląda **tylko do odczytu** (decyzje zmieniają i wysyłają uczniowie);
  drużynę bez uczniów prowadzi sam,
- *Wyniki* → eksport do arkusza: **Ranking (CSV)** i **Wyniki firm w rundach (CSV)** (średnik, przecinek
  dziesiętny – otwiera się wprost w Excelu).

**Drużyny.** Drużyna to 1–4 uczniów prowadzących jedną firmę; uczeń gra w jednej drużynie danej gry (w innej
grze może być w innej). Mistrz gry wpisuje w zakładce *Drużyny* listę imion i nazwisk – powstają konta z loginem
`imie.nazwisko` (bez polskich znaków, `ala.nowak2`, gdy zajęty) i losowym 8-znakowym hasłem, pokazanym raz
(okno można wydrukować); zapomniane hasło – „hasło” przy uczniu. Każdy z drużyny zmienia i wysyła decyzje za
całą drużynę; strona pokazuje, kto ostatnio zapisał i kto wysłał. Gdy dwie osoby zmieniają decyzje naraz, zapis
na starszej wersji jest odrzucany (409) i strona wczytuje decyzje kolegi – nic się nie nadpisuje po cichu.
Strona drużyny co 20 s sprawdza zmiany (`GET /api/gry/<id>/stan/<firma>`) i sama się odświeża, także po
przeliczeniu rundy. Drużynę bez uczniów prowadzi mistrz gry.

### Konta i role

Każda strona wymaga logowania (`/konta/login/`, django-allauth). Role:

- **mistrz gry** – grupa `mistrz_gry` albo superużytkownik: zakłada gry, prowadzi rundy, widzi wszystkie
  drużyny, zakłada konta uczniów i dopisuje ich do drużyn w zakładce **Drużyny** gry (albo w panelu **Konta**
  `/admin/`: Użytkownicy; Gry → gra → drużyny – ten sam limit 4 osób),
- **uczeń** – każde inne konto: widzi tylko gry i firmy swoich drużyn (strona i API: 403 dla cudzej firmy),
  nie zamyka ani nie cofa rund.

Konta z własnym loginem zakłada mistrz gry (samodzielna rejestracja wyłączona, `LEVAS_REJESTRACJA=1` ją
włącza):

```
.venv\Scripts\python manage.py konto pani-ania --mg --imie "Anna Kowalska"   # mistrz gry (hasło z pytania)
.venv\Scripts\python manage.py konto ala --imie "Ala Nowak"                  # uczeń
```

**Konto Microsoft (szkolne):** zarejestruj aplikację w Microsoft Entra ID (adres przekierowania
`http(s)://<serwer>/konta/microsoft/login/callback/`) i ustaw zmienne `LEVAS_MS_CLIENT_ID`,
`LEVAS_MS_SECRET` i `LEVAS_MS_TENANT` (identyfikator dzierżawy szkoły – logują się tylko jej konta). Bez nich
przycisk Microsoft się nie pokazuje. Pierwsze logowanie zakłada konto ucznia.

**Gra na własnym komputerze** (`start.bat`, `manage.py graj`) loguje się sama na lokalne konto mistrza gry
`lokalny` – tylko z tego komputera. Sam `runserver` wymaga logowania.

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
| `konta/` | logowanie (django-allauth: własny login, konto Microsoft), role uczeń / mistrz gry (`role.py`), komenda `konto` |
| `panel_mg/` | panel mistrza gry (`/mg/`): nowa gra, prowadzenie rund, wyniki drużyn; dane z `GET /api/gry/<id>/mg` |
| `testy/` | pytest (mechaniki Revasa, zasady rund, API) |

`WIEDZA_O_GRZE.md` – opis mechanik Revasa, z których korzysta silnik (liczby z gier – w `dane_revas/`).

### Kalendarz rund

`katalog.yaml` → `rundy.kalendarz`: okres (`tydzien` / `miesiac`), rund w roku, data startu. Kebab: runda = tydzień,
26 rund od 5.10.2026, 40 000 zł i gotowy lokal (`stanowiska.startowe`: kuchnia z rożnem, frytownicą i lodówką,
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
| `grupa` | porcji naraz (w kebabie 1) |
| `utrzymanie_klubu` | utrzymanie lokalu |
| stanowisko typu `kuchnia` / `kasa` | stanowisko kuchenne / kasowe (nazwy i zawody: `katalog.yaml` → `stanowiska.typy`) |
