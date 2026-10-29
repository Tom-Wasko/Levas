# Levas – przewodnik dla agenta (OpenCode / Claude Code)

Czytaj w całości na początku każdej sesji. Autor projektu pisze po polsku – **odpowiadaj po polsku**.

## Co to jest
Levas to edukacyjna symulacja biznesowa dla uczniów i studentów. Gra się tak:
- drużyny (1–4 osoby) prowadzą kebaby na wspólnej mapie Lublina;
- runda to jeden tydzień w grze (domyślnie 18 rund, 40 000 zł kapitału na start);
- co rundę drużyna podejmuje decyzje w zakładkach: lokal, menu i ceny, dostawcy, ludzie, reklama, bank, księgowość (KPiR), urząd, handel z innymi drużynami i tak dalej;
- mistrz gry (nauczyciel) zamyka rundę, a silnik liczy tydzień dzień po dniu;
- wynik to **karta wyników**, a ranking drużyn liczy się z wyniku działalności.

W grze biorą udział boty o 5 strategiach i 4 poziomach. Levas powstał z kopii gry REVAS (klub fitness), przebudowanej na kebab i rozbudowanej o nowe mechaniki.

**Stan (29.10.2026):** kroki 1–4 są zrobione (cała gra grywalna). Teraz kolej na kroki 5–6: analizę (A) i kalibrację (B) według `notatki/Plan optymalizacji.md` – sesje po kolei, najpierw A. Zadania i postęp są w `POSTEP.md`, instrukcje dla sesji w `zadania/` (polecenia do wklejenia: `zadania/README.md`).

## Mapa repozytorium
```
AGENTS.md            ten plik
POSTEP.md            lista zadań z checkboxami (F/P/Q – zrobione; A, U, B – bieżące)
zadania/             instrukcje dla sesji: README.md (polecenia), A_analiza_gracza.md, B_kalibracja.md
raporty/             wyniki analiz i kalibracji (tworzysz tu pliki)
notatki/             notatki projektowe autora (Obsidian) – NIE zmieniaj bez zgody (niżej)
dokumentacja/        tło: WIEDZA_O_GRZE.md (oryginalny REVAS: karta wyników, mechaniki),
                     ROZNICE_LEVAS_STARY.md (stara wersja Levasa – źródło pomysłów)
archiwum/            zakończone plany i dzienniki prac (Plan implementacji – tylko do odczytu)
plan.txt             prywatny plik autora – nie commituj, nie zmieniaj
gra/
  silnik/            silnik gry: czysty Python (pydantic, numpy), bez Django
    *.py             rdzeń: gra, runda, decyzje, co_jesli, dane, schematy, model, losowosc,
                     harmonogram, limity, boty
    kuchnia/         menu, jakosc, operacje, planowanie, dostawcy, magazyn, swiezosc
    rynek/           popyt, konkurencja, kalendarz, reklama, promocje, handel
    ludzie/          rynek_pracy, kandydaci, czas_wlasciciela
    nieruchomosci/   lokale, przejecia
    ksiegowosc/      finanse (KPiR, rachunek), rozliczenie, uzgodnienie, biuro, urzad, srodki_trwale
    pieniadze/       banki, lichwiarz (Harpagon), kasyno, wlasciciel, zaleglosci
    swiat/           zdarzenia, awarie
    wyniki/          karta, wnioski
  dane/              WSZYSTKIE liczby gry w YAML (mapa/, zdarzenia/, kalendarz/, zalozenia.yaml, boty.yaml…)
  api/               Django: widoki JSON; prezentacja.py buduje widok `v` dla zakładek
  panel_gracza/      strony gracza; static/zakladki/*.js – zakładki (moduły ES, rejestr w index.js)
  panel_mg/          panel mistrza gry (/mg/)
  gry/, konta/       modele Django (gry w SQLite), konta i logowanie
  balans/symuluj.py  symulacja gier botów (balans poziomów)
  testy/             pytest: podfoldery jak podpakiety silnika (rdzen/, kuchnia/, rynek/…) i aplikacja/
                     (API, panele, konta); wspólne funkcje pomocnicze w pomocnicze.py
  README.md          uruchomienie, opis rozgrywki, słownik nazw kod → gra (usługa = danie itd.)
  INSTRUKCJA.md      instrukcja dla graczy (w grze: /jak-grac, szablon panel_gracza/templates/…/jak_grac.html)
```

## Uruchomienie na nowym komputerze
```
git clone https://github.com/Tom-Wasko/Levas.git && cd Levas/gra
python -m venv .venv                       # Python 3.12+ (autor: 3.13)
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python manage.py graj        # migracje + serwer http://127.0.0.1:8765 (Windows: start.bat)
```

## Polecenia (z folderu `gra/`)
```
.venv/Scripts/python -m pytest -q                       # ~280 testów, ok. 3 min
.venv/Scripts/python -m ruff check .                    # linia ≤ 100 znaków
.venv/Scripts/python -X utf8 -m silnik.dane sprawdz      # schematy i odwołania w dane/*.yaml
.venv/Scripts/python -X utf8 -m balans.symuluj 12 sredni 7   # gra botów; 12 rund ≈ 5 s
node --check plik.mjs                                    # składnia zakładki JS (skopiuj .js jako .mjs)
```
Na Windows używaj `python -X utf8` przy wypisywaniu polskich znaków.

## Jak działa silnik
- `silnik/gra.py` – `Gra.nowa(nazwa, [(firma, strategia_bota|None)], liczba_rund, ziarno, **opcje)`. Opcje to między innymi `poziomy`, `kapital_startowy`, `ceny_dostawcow`, `kredyt_odnawialny` i `auto_zamowienia`. Gra ma metody `ustaw_decyzje(firma, decyzje)`, `wyslij`, `przelicz(wymus=True)`, `stan(r)` i `wyniki`. Boty dostają decyzje z `silnik/boty.py: decyzje_bota` w `Gra.przelicz`.
- `silnik/decyzje.py` – **format decyzji** (docstring na górze) i ich zastosowanie. `silnik/runda.py` – przebieg tygodnia.
- Wyniki rundy są w `stan.wyniki[runda][firma]`: `karta`, `kpir`, `sprzedaz` (popyt, sprzedaż, utracona sprzedaż, przyczyna), `magazyn`, `lista_bledow` i tak dalej. Karta wyników jest w `silnik/wyniki/karta.py`.
- Losowość pochodzi **tylko** z `silnik/losowosc.py: strumien(ziarno, runda, cel, *klucze)`. To samo ziarno daje ten sam wynik, a testy tego pilnują.
- Kwoty w stanie są w groszach (`int`, pola `…_gr`), a silnik liczy w złotych przez właściwości.
- Moduły mechanik: lokale, popyt, konkurencja, menu, dostawcy, magazyn, swiezosc, rynek_pracy, kandydaci, banki, lichwiarz (Harpagon), kasyno, biuro, urzad, awarie, reklama, promocje, handel, przejecia, zdarzenia, wlasciciel, czas_wlasciciela, wnioski, co_jesli i inne.

## Zasady kodu
- **Żadnych liczb gry w kodzie silnika.** Wszystkie liczby trzymaj w `dane/*.yaml`; pilnuje tego test `test_w_kodzie_silnika_nie_ma_liczb_gry`. Każdy parametr w `zalozenia.yaml` ma postać `{wartosc, pewnosc: potwierdzone|skalibrowane|zalozenie, zrodlo}`. Gdy zmieniasz liczbę, zaktualizuj `zrodlo` (np. `'kalibracja B6: …, było X'`) i `pewnosc`.
- Identyfikatory piszemy po polsku bez ogonków (`gotowka`, `wynik_dzialalnosci`), a teksty dla gracza po polsku z ogonkami.
- Pisz w stylu otaczającego kodu: zwięzłe komentarze po polsku, gęstość komentarzy jak obok.
- Do nowej mechaniki dodaj test w `testy/`. Nie usuwaj i nie osłabiaj testów tylko po to, żeby przeszły.
- Gdy celowo zmieniasz liczbę, a test sprawdza wynik co do grosza, zaktualizuj oczekiwaną wartość i **napisz w commicie, które testy zmieniłeś i dlaczego**.
- Od B2: testy mechanik (wzory, scenariusze co do grosza) czytają zamrożoną kopię danych `testy/dane_zamrozone/`, a testy zasad (determinizm, brak liczb w kodzie, schematy, uzgodnienie kasy, boty bez błędów) – `dane/`. Zmiana liczby w `dane/` nie powinna więc łamać testów wzorów; liczb w zamrożonej kopii nie zmieniaj przy kalibracji (gdy zmienia się schemat danych, dopisz w niej tylko nowe klucze).
- Funkcje pomocnicze wspólne dla kilku plików testów trzymaj w `testy/pomocnicze.py`, a nie w importach między `test_*.py`.

## Git i postęp
- Pracujesz na gałęzi `main` w `origin` = github.com/Tom-Wasko/Levas. Autor pracuje na kilku komputerach, więc **wypychaj zmiany regularnie**.
- Po każdym zadaniu (A1, B3, U2…):
  1. `pytest`, `ruff`, `sprawdz` – wszystko musi przejść;
  2. odhacz zadanie w `POSTEP.md` i dopisz jedno zdanie o tym, co zrobiłeś;
  3. zrób commit `B3: krótki opis` z opisem w treści;
  4. `git pull --rebase origin main`, potem `git push origin main`.
- Na końcu każdego commita dopisz linię współautora z nazwą modelu, np. `Co-Authored-By: <model> <noreply@…>`.
- Nie commituj `plan.txt`, `gra/db.sqlite3`, `gra/lokalne.json` ani `gra/zapisy/`. Nie używaj `push --force`.

## Notatki autora (`notatki/`)
**Każda zmiana albo dodanie czegokolwiek w `notatki/` wymaga zgody autora.** Najpierw zapytaj i pokaż proponowany tekst. Jeśli autora nie ma, zapisz propozycje w raporcie (`raporty/…/notatki_do_zmiany.md`) i pracuj dalej. Postęp prac odhaczasz w `POSTEP.md`, nie w notatkach.

Najważniejsze notatki:
- `Plan optymalizacji` – bieżący plan;
- `Ustalenia gry` – wszystkie parametry;
- `Prawidła świata`, `Elementy mapy`, `Menu i składniki` – zasady świata;
- `Główny obraz` i `Zarys aplikacji` – wizja;
- `archiwum/Plan implementacji.md` – plan kroków 1–4, archiwum, wyłącznie do odczytu.

## Kiedy pytać autora
Pytaj o decyzje projektowe, których nie da się wyprowadzić z notatek ani z celów planu: nowa mechanika, zmiana zasad widocznych dla gracza, usunięcie funkcji. Liczb i wzorów nie musisz konsultować, o ile służą celom z `notatki/Plan optymalizacji.md`. Gdy pytanie czeka na odpowiedź, zapisz je w raporcie zadania i zajmij się czymś niezależnym.
