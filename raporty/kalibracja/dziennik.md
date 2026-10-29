# Dziennik kalibracji

Pamięć między sesjami części B. Po każdym kroku: co zmierzono, co zmieniono, co wyszło i co dalej. Najnowszy
wpis na dole.

## B1 – inwentarz decyzji (29.10.2026, Claude Code, Opus 5.5)
- Zrobione:
  - docstring `gra/silnik/decyzje.py` uzupełniony o `przejecie`, `wypowiedz`, `lokal.oferta`,
    `wlasciciel_stanowisko`, pola banku w kredytach i lokatach, `leasing_wez`, `harpagon_wez/splac`,
    `wyplata/wplata_wlasna`, `kasyno`, `detektyw` i `higiena`;
  - `raporty/kalibracja/inwentarz.md`: opcje, parametry, użycie przez boty, zamierzony kompromis i 17 hipotez
    (H1–H17).
- Zmierzone (9 gier botów, 18 rund; dokładny pomiar w B4):
  - pierwszy plus w tygodniu 2–4 prawie u wszystkich;
  - marża netto średniego bota 25–40%, praca 12–20% przychodu;
  - wszystkie boty: mBank i e-Księgi24.
- Pytanie do autora (nie blokuje B2):
  - **P1. Umowa zlecenia nie ma składek ZUS pracodawcy** (`runda.py:211`). W prawie 2026 zlecenie też ma
    składki (bez nich tylko student do 26 lat).
  - Czy uznać to za regułę gry (wtedy balansuję innymi kosztami zlecenia, np. rotacją, w B9), czy dodać
    składki do zlecenia jako część zamrożonego prawa?
  - Domyślnie zostawiam bez zmian do B9 i sprawdzam hipotezę H3.
- Dalej: B2 (zamrożone dane testów, profilowanie, wymuszanie decyzji bota, `balans/warianty.py`).

## B2 – narzędzie porównań i punkt zero (29.10.2026, Claude Code, Opus 5.5)
- Zrobione:
  - testy mechanik czytają zamrożoną kopię `gra/testy/dane_zamrozone/` (kopia `dane/` z 29.10.2026). Testy
    zasad (determinizm, schematy, boty, uzgodnienie, brak liczb w kodzie) mają znacznik `dane_gry` i czytają
    `dane/`. Sprawdzone zmianą `mnoznik_bazowy` w `dane/`: wszystkie testy mechanik przechodzą;
  - `balans/odcisk.py` – odcisk stanów 5 gier botów (72 rundy, ok. 30 s): `zapisz` przed zmianą,
    `porownaj` po niej;
  - `balans/warianty.py` – pary gier. Badana firma to bot, któremu wymusza się decyzję (`decyzje`), parametr
    strategii albo poziomu, albo pole zatrudnienia. Konteksty: strategia, rundy, firmy, poziom, strefa
    (nowy, opcjonalny parametr strategii `strefy` w `silnik/boty.py`) i kapitał. Gry trafiają do `gry.csv`
    na bieżąco, a przerwany pomiar wznawia się bez powtórek. Raport: `pary.csv` i `raport.md`. Ocena
    „lepszy”/„gorszy” wymaga ≥ 70% wygranych par i 95% przedziału bez zera. Polecenia: `szybki`, `pelny`,
    `raport`, `lista`. Testy: `testy/rdzen/test_warianty.py`;
  - odcisk przed i po zmianie `strefy` w botach jest identyczny.
- Profilowanie (gra 18 rund, jeden proces):
  - 4 firmy – 3,6 s, 6 firm – 5,2 s, 8 firm – 6,9 s; w pomiarze na 5 procesach średnio 5,5 s na grę
    (6 firm);
  - ok. 40% czasu to dwa wywołania `linprog` (HiGHS) w `kuchnia/operacje.py` (ok. 1400 na grę) – pierwsze
    miejsce do przyspieszenia (cache wyników dla tych samych ograniczeń albo mniej wywołań). Dalej
    `rynek/popyt.py: podzial` (ok. 12%) i `losowosc.strumien` (ok. 7%);
  - przyspieszać tylko z kontrolą odcisku.
- **Punkt zero** (zasady sprzed kroków Z; `raporty/kalibracja/pomiary/punkt_zero/`):
  - zakres: `szybki` – strategie zrównoważony, tani, premium × 6 ziaren × 28 wariantów, 6 firm, 18 rund,
    poziom średni; 522 gry w 9,7 min;
  - karta = suma wyników działalności z rund; alarm do Z3 = runda z debetem ponad limit konta;
  - **dominują**:
    - umowa zlecenie: +1,30 ± 0,41, 100% par, +10,9 tys. zł majątku (H3 potwierdzona);
    - mBank: każdy inny bank −0,14…−0,18 i 0% wygranych (H4);
    - e-Księgi24: każde inne biuro −0,07…−0,14 i 0% wygranych (H5);
    - wszystkie polisy: +0,17 ± 0,08, 83% (wbrew H14 – polisy się opłacają);
  - **zdarzają się katastrofy**: higiena „brak” – sanepid nie odbiera lokalu, firma nie rusza. Karta −11,3,
    majątek −287 tys. zł, 14 rund alarmu. Kredyt odnawialny rośnie bez górnego limitu (sprawdzić w Z3 i B11);
  - **szum przy 18 parach**: cena 0,85/1,0/1,15, jakość 1 i 3, drugi lokal (+0,89 ± 1,38), kampanie. Brak
    promocji daje +0,81 ± 0,66 przy 69% (na granicy – H13 do pełnego pomiaru). Rozstrzygnąć te opcje może
    dopiero pełny pomiar (≥ 30 ziaren);
  - jakość 2 wypada gorzej niż bazowa (−1,57): baza ma jakość strategii (premium 3, tani 1), więc wariant
    zmienia charakter strategii, a nie tylko jedną decyzję. W B4 czytać warianty strategii z podziałem na
    konteksty (sekcje raportu).
- Dalej: Z1–Z7, potem B3 (część do pomiaru) i B4.

## Z1 – karta wyników (29.10.2026, Claude Code, Opus 5.5)
- **Strata:** wynik działalności = `strata.waga` × wynik ekonomiczny. Nowy parametr
  `karta_wynikow → strata → waga` = 1,0 (założenie). Nie mnoży się przez wskaźniki, więc przy tej samej stracie
  wynik od nich nie zależy. Do sprawdzenia w B5/B6: czy strata na rozruchu nie waży za dużo wobec zysku, który
  mnoży się przez wskaźniki (iloczyn zwykle < 1).
- **Majątek do karty:** `karta.majatek_karty`, czyli suma inwestycji po amortyzacji puli plus kupione lokale,
  budynki i grunt z ewidencji (netto).
  - Tańsze zakupy (< 10 tys. zł, czyli prawie cały sprzęt i wyposażenie) idą od razu w koszty i nie trafiają do
    ewidencji. Dlatego suma inwestycji ma własne umorzenie `Firma.umorzenie_majatku`.
  - Odpis liniowy według stawki sprzętu, od sumy sprzed rundy (`srodki_trwale.amortyzuj_majatek`).
  - Przy sprzedaży umorzenie maleje proporcjonalnie (`zmniejsz_majatek`, pięć miejsc sprzedaży).
  - Ten majątek trafia też do wskaźnika zadłużenia.
- **Odkup:** zakupy podnoszą rozwój tylko ponad `Firma.szczyt_majatku` – najwyższą sumę inwestycji po cenach
  zakupu z minionych rund. Sprzedaż dalej obniża rozwój.
  - Zakup lokalu nie jest „inwestycją” w rozwoju (jak dotąd); podnosi tylko majątek. Inaczej jeden zakup za
    300 tys. zł dałby rozwój ×4 w jednym tygodniu.
- **Harpagon:** odsetki z rundy obniżają dochód do karty (`runda._netto_karty`). KPiR się nie zmienia.
- Testy:
  - nowe w `testy/wyniki/test_karta.py`: strata, majątek po amortyzacji z lokalem i budynkiem, odkup, odsetki
    Harpagona;
  - zmienione: `test_karta_kebabowa_w_grze` (oczekiwany wynik przy stracie) i `test_wynik_ekonomiczny` w
    `test_mechaniki.py` (strata daje −10 × waga zamiast 0).
- Tekst dla gracza: `INSTRUKCJA.md` §3 i podpowiedź karty w `ogolne.js`. Propozycja do notatki „Ustalenia gry”:
  `notatki_do_zmiany.md`.
- Zmienia wyniki gier (odcisk inny, celowo).
- `balans/warianty.py`: karta to teraz średnia z rund 2..N, jak w definicji z planu (w punkcie zero była suma
  rund, czyli Δ karta ×17; kolejność firm i oceny wariantów bez zmian).

## Z2 – majątek netto (29.10.2026, Claude Code, Opus 5.5)
- `silnik/wyniki/majatek.py: majatek_netto(f)` – składniki i `razem`; w wynikach rundy jako
  `w["majatek_netto"]`.
  - Aktywa: gotówka, lokaty, kaucje, nadwyżka VAT, zapasy, nieruchomości i sprzęt po amortyzacji.
  - Długi: kredyty z zaległymi ratami, debet, zaległe raty leasingu i Harpagon z odsetkami.
- **Odejście od definicji z planu:** bez portfela właściciela. Mistrz gry widzi majątek netto, a test
  `test_mistrz_gry_nie_widzi_klubu` pilnuje, żeby nie widział portfela.
  - `z_portfelem(w)` dolicza portfel w pomiarach (`balans/warianty.py`).
  - Propozycja dopisku do planu: `notatki_do_zmiany.md`.
- Zaległości ZUS, US, czynszu i dostawców w grze nie istnieją: płatności idą z konta, a brak środków daje debet.
  Rata kredytu bez pokrycia trafia do długu kredytu, a rata leasingu – do zaległych rat leasingu.
- Wpłata inwestora (Z3) dojdzie do długów w Z3.
- Panel mistrza gry: kolumna i wykres majątku netto. CSV: kolumna „majątek netto” w rankingu i w wynikach rund.
- Testy: nowy `testy/wyniki/test_majatek.py`; w `test_eksport_csv` dodane sprawdzenie kolumny.

## Z3 – debet ponad limit i inwestor ratunkowy (29.10.2026, Claude Code, Opus 5.5)
- Alarm: `w["alarm"]` = debet ponad limit konta na koniec rundy (`bk.debet_ponad_limit`). Panel mistrza gry
  pokazuje go przy gotówce, a nad tabelą jest ramka z listą firm w alarmie.
- Blokada (`silnik/pieniadze/inwestor.py: BLOKOWANE`) działa w następnej rundzie, gdy debet ponad limit trwa na
  początku rundy. Zablokowane są: nowy lokal, kupno budynku, stanowiska, sprzęt, udogodnienia, wyposażenie,
  kredyty, leasing i lokaty. Każda odrzucona decyzja daje czerwony błąd w zakładce Bank.
  - Zostają Harpagon, sprzedaż majątku i spłaty, żeby drużyna mogła sama wyjść z debetu.
  - Lista kluczy jest w kodzie, bo to teksty, a nie liczby gry.
- **Interpretacja odpowiedzi autora** („bez odsetek karnych i zajęcia majątku”): nie ma nowych kar, ale
  istniejące odsetki karne banku od debetu ponad limit zostają.
- Inwestor (`Gra.ustaw_inwestora(firma, kwota)`, API `POST /prowadzenie {"inwestor": {"firma", "kwota"}}`,
  w panelu link „przyślij inwestora”):
  - tylko firma z debetem ponad limit po ostatniej rundzie, jeden inwestor na grę, kwota do `max_kwota`;
  - kwota 0 odwołuje przysłanie przed zamknięciem rundy;
  - zapis jest w `konfiguracja["inwestorzy"]`, więc przetrwa cofnięcie i ponowne przeliczenie rundy;
  - wpłata trafia na początek rundy, przed aukcjami i decyzjami. Najpierw spłaca debet, więc blokada znika w tej
    samej rundzie;
  - przez `rund` rund inwestor bierze `udzial` dodatniego dochodu netto rundy (poza KPiR, nie jest kosztem w
    karcie);
  - niezwrócona część wpłaty (kwota − wypłacone) liczy się jak dług do końca gry, także po końcu umowy:
    w `zadluzenie` (wskaźnik zadłużenia w karcie) i w majątku netto (`dlugi["inwestor"]`);
  - wypłaty ponad wpłatę to zysk inwestora, a dług wynosi wtedy 0.
- Warunki są w YAML: `finanse.inwestor_ratunkowy` = {max_kwota 40000, udzial 0.3, rund 8}, pewność `zalozenie`
  (do kalibracji w B).
- Boty nie dostają inwestora automatycznie. W grze 12 rund (ziarno 7) alarm łapie agresywny na poziomie łatwym
  (rundy 6–12, 6 blokad) i średnim (runda 3), a premium na łatwym (runda 5); na trudnym nikt. Boty grają bez
  błędów.
- Testy:
  - nowe: `testy/pieniadze/test_inwestor.py` (4) i `test_alarm_debetu_i_inwestor_ratunkowy` w
    `testy/aplikacja/test_prowadzenie.py`;
  - zmieniony: `test_dzialka_budowa_w_ratach_potem_lokal_bez_sprzetu` dostał kapitał 200 000 zł, bo budowa za
    100 000 zł wpychała firmę w debet ponad limit i blokada zatrzymywała stanowiska. Test sprawdza budowę, a nie
    debet.
- Tekst dla gracza: `INSTRUKCJA.md` §11 i komunikat o debecie w zakładce Bank.
