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
