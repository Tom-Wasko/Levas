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

## Z4 – liczba lokali zależna od liczby firm (29.10.2026, Claude Code, Opus 5.5)
- Lokal w `dane/mapa/lokale.yaml` może mieć `od_firm: N` – jest na mapie tylko w grze z co najmniej N firmami
  (`lokale.na_mapie`). Bez klucza lokal jest zawsze.
  - Wynik: 8+ firm – 38 lokali (19 gotowych, 14 do urządzenia, 5 działek), 6–7 firm – 29 (15/10/4), 4–5 firm
    i mniej – 20 (11/6/3). To około 5 lokali na firmę, a wszystkie 10 stref zostaje na mapie.
  - Gotowych do najmu od rundy 1: 16, 12 i 8.
  - Zostają lokale wystawiane później (`od_rundy`) i lokal Tymka.
- Liczba firm to `len(stan.firmy)`. Przechodzi przez `dostepne(…, liczba_firm)` (oferta, boty, zakładka Lokale) i
  przez `powod_odrzucenia`/`wybierz` (decyzja i licytacje). Lokal spoza mapy daje „Nie ma takiego lokalu.”
  Mapa gracza dostaje listę `v.lokale.na_mapie`.
- Popyt miasta bez zmian.
- Zamrożona kopia danych **nie** dostała `od_firm`. W testach mechanik (2–3 firmy) jest więc cała pula, jak dotąd,
  a liczby tej kopii się nie zmieniły.
- Testy: nowy `test_liczba_lokali_na_mapie_zalezy_od_liczby_firm` (dane gry). Pozostałe bez zmian.
- Boty grają bez nowych błędów w grach z 4, 6 i 8 firmami (8 rund, ziarno 7).
- Wybór lokali do usunięcia jest założeniem (proporcje typów, premium w Starym Mieście i Centrum zostaje). Autor
  może go zmienić w YAML.

## Z5 – bot „jak człowiek” (29.10.2026, Claude Code, Opus 5.5)
- Trzy nowe poziomy w `dane/boty.yaml`: `czlowiek_slaby`, `czlowiek_sredni`, `czlowiek_dobry`. Strategia
  (cena, jakość, menu…) zostaje osobno, więc „jak człowiek” może grać każdą strategię. Plan mówi „nowa
  strategia”, ale wersje różnią się sposobem decydowania, a to w kodzie jest poziom.
- Prognoza (`boty._prognoza_czlowieka`, opcja poziomu `prognoza_czlowieka`) korzysta tylko z tego, co drużyna
  widzi w zakładkach:
  - popyt dań w każdym lokalu z raportu ostatniej rundy (`wyniki[r].klienci.lokale[].dania`);
  - wersja dobra: średnia z 2 rund, każda razy pula strefy w rundzie sprzedaży / pula w tamtej rundzie
    (zakładka Klienci pokazuje pule stref, więc widać sezon i kalendarz);
  - lokal albo danie bez historii (rundy 1–2, nowe danie, nowy lokal): potencjał lokalu jak w zakładce Klienci
    (2★, ceny preferowane strefy, obecna konkurencja);
  - rozkład na dni z wag dni strefy (też widoczne w zakładce Klienci).
  Bot nie woła prognozy modelu dla własnych cen i jakości (`_prognoza_lokali`), co pilnuje test.
- Wersje (różnią się staraniem):
  - słaba – planowanie proste (jak łatwy), błąd ±25%, kandydat jakikolwiek, bez kampanii i promocji;
  - średnia – planowanie obsady dzień po dniu (jak średni), błąd ±10%;
  - dobra – średnia z dwóch tygodni poprawiona o pulę strefy, bez błędu, reklama tylko z wolną kuchnią, drugi
    lokal na tych samych warunkach co trudny.
  - Żadna nie ma korekty o prognozę modelu, wyboru ceny po modelu ani oszustwa (schemat tego zabrania).
- Poziomy mają `tylko_pomiar: true` – nie ma ich na liście poziomów w panelu mistrza gry (API i strona listy
  gier); gra z konfiguracją je przyjmuje. **Pytanie do autora:** czy pokazać je nauczycielom jako rywali?
- `balans/warianty.py`: nowe pole kontekstu `rywale` (`--rywale sredni`) – badana firma na poziomie „jak
  człowiek”, rywale na swoim. Klucz kontekstu bez `rywale` się nie zmienia (stare `gry.csv` pasują).
- Pomiar orientacyjny (nie B4): 18 rund, 6 firm, badana zrównoważona, rywale średni, ziarna 1–8:
  - karta skumulowana: słaba 0,11–0,30, średnia 0,38–0,96, dobra 0,55–1,00; dobra > średnia w 8/8 par;
  - pierwszy plus: słaba w rundzie 2–4, średnia i dobra w rundzie 2–3 (cel dla średniej: 4–6 – gra za łatwa,
    zgodnie z H1);
  - majątek netto na koniec: słaba 61–87 tys., średnia 105–174 tys., dobra 123–180 tys. zł (start 40 tys.);
    alarmów brak.
  - W grze samych botów (`balans.symuluj 12`, ziarno 7) średnia gotówka: słaba 35 tys., średnia 61 tys., dobra
    70 tys. zł (poziom średni: 63 tys.).
- Testy: 3 nowe w `testy/rdzen/test_boty.py`, 1 w `testy/rdzen/test_warianty.py` (dane gry). Pozostałe bez
  zmian; `test_poziom_botow` (panel MG) dalej widzi tylko 4 poziomy.

## Z6 – kalendarz do kwietnia 2026 (29.10.2026, Claude Code, Opus 5.5)
- Domowe mecze Motoru wiosną 2026 (`rok: 2026`, prawdziwe daty z Wikipedii, ta sama strona co jesień; dni
  tygodnia sprawdzone): Pogoń 01.02, Lechia 15.02, Korona 28.02, Górnik 08.03, Zagłębie 20.03, Raków 12.04.
  Mnożniki jak jesienią (Arena 1,6–1,9).
- Nowe wydarzenia co roku: Finał WOŚP (data ruchoma `final_wosp`, prawdziwe daty 2025–2026), Popielec
  (Wielkanoc −46, falafel ×1,5), Początek semestru letniego (23–27.02), Jarmark Wielkanocny (Wielkanoc −10…−4,
  Stare Miasto), Wielki Piątek (falafel ×1,6, talerz ×0,6). Mnożniki to założenia, jak reszta kalendarza.
- Gęstość: 09–12.2025 – 23 wydarzenia, 01–04.2026 – 23 (było 11 bez meczów). Runda 26 zaczyna się 23.02.2026,
  runda 35 – 27.04.2026.
- Gra botów 34 rundy (ziarno 7) bez błędów. Testy bez zmian (testy kalendarza czytają zamrożoną kopię).

## Z7 – miejsce na pulpicie jak ranking mistrza gry (29.10.2026, Claude Code, Opus 5.5)
- `api/prezentacja.py`: nowa funkcja `miejsca(skum)`, z której korzystają pulpit drużyny (`_dashboard`) i ranking
  mistrza gry (`przeglad_mg`, eksport CSV). Miejsce = kolejność średniego wyniku działalności z rund 2…N (karta
  skumulowana, ta sama, którą pokazuje zakładka Karta wyników). Wcześniej pulpit brał kartę tylko z ostatniej
  rundy. Ranking jest dostępny od rundy 3, jak dotąd.
- Test: nowy `test_miejsce_na_pulpicie_jak_ranking_mistrza_gry` (`testy/aplikacja/test_panel_mg.py`) – w każdej
  rundzie gry botów miejsce na pulpicie = miejsce u mistrza gry, a ranking z ostatniej rundy choć raz się różni.
- **Pytanie do autora (zmiana widoczna dla gracza, nie ruszałem):** po zakończeniu gry widok drużyny staje na
  rundzie N, a ta pokazuje skutki rundy N−1 (jak w REVAS: wyniki rundy r widać w rundzie r+1). Drużyna nie widzi
  więc wyników ani miejsca po ostatniej rundzie, a mistrz gry widzi. Czy po końcu gry pokazać drużynie widok
  „po rundzie N” (wyniki ostatniej rundy i końcowe miejsce)? Warto to sprawdzić w części A.

## B3 – boty, część do pomiaru: poziomy łatwy < średni < trudny (29.10.2026, Claude Code, Opus 5.5)
- Do pomiaru B4 boty nie muszą same wybierać opcji: warianty z B2 (banki, dostawcy, kupno, lokale…) wymuszają
  decyzje badanej firmy. Reszta B3 (każda strategia sięga po każdą opcję) to krok 0 każdego obszaru B6–B12.
- Pomiar poziomów: 18 rund, 6 firm, badana wśród średnich rywali, 5 strategii × ziarna 1–8
  (`pomiary/b3_poziomy` – przed, `b3_poziomy_blad` – krok pośredni, `b3_poziomy_po` – po).
- Przed: karta skumulowana łatwy 0,207, średni 0,540, trudny 0,797; średni < trudny tylko w 19/40 par
  (agresywny 8/8 dzięki drugiemu lokalowi, premium 1/8, zrównoważony 2/8, tani i naśladowca 4/8).
- Ablacja trudnego (warianty `poziom:bez_…`, 32 pary): bez korekty prognozy +0,15 ± 0,07 (84%, „lepszy”),
  bez mnożników ceny i bez progu kampanii – szum.
- Zmiany:
  1. `silnik/boty.py: _korekta_prognozy` – błąd: „prognoza” w raporcie to oferta bota, która ma już korektę,
     więc stosunek popyt / prognoza przy stałym błędzie modelu skakał co rundę między błędem a 1. Teraz
     korekta narastająco (poprzednia × popyt / oferta) i zbiega do błędu modelu. Po poprawce wariant „bez
     korekty” to szum (+0,02 ± 0,04).
  2. `dane/boty.yaml`, średni: `blad_prognozy: 0.1` (było brak) – średni planował z dokładnego modelu popytu
     prawie jak trudny. Wpływ mały (średni 0,540 → 0,524).
  3. `dane/boty.yaml`, trudny i niemożliwy: `kolejny_lokal.obsluga` 0,85 → 1,0 – drugi lokal, gdy stać
     (gotówka > 60 / 45 tys. zł), a nie tylko przy brakach obsługi. Wariant w parach: +0,33 ± 0,09 karty,
     89% wygranych, +32 tys. zł majątku, bez alarmów. Bot „jak człowiek dobry” bez zmian (to B5).
- Po: łatwy 0,207, średni 0,524, trudny 1,132 (majątek 80 / 126 / 186 tys. zł). Łatwy < średni w 39/40 par,
  średni < trudny w 37/40 – przy każdej strategii (agresywny 8/8, naśladowca 8/8, tani 8/8, zrównoważony 7/8,
  premium 6/8).
- Dla B4 (hipotezy): drugi lokal opłaca się prawie zawsze, gdy jest gotówka (do sprawdzenia, czy to nie
  dominacja); agresywny na poziomie łatwym i średnim ma alarmy debetu w 4–5/8 gier, a na łatwym ujemną kartę
  (H17).
- Testy: nowy `test_korekta_prognozy_trudnego_zbiega_do_bledu_modelu` (`testy/rdzen/test_boty.py`); w
  `balans/warianty.py` nowe warianty `poziom:bez_korekta_prognozy|mnozniki_ceny|obsluga_kampanii`. Inne testy
  bez zmian.

## B4 – pomiar startowy (29.10.2026, Claude Code, Opus 5.5)
- Raport: `raporty/kalibracja/stan_poczatkowy.md`; pomiary `pomiary/b4_*` (7090 gier, 2 h 13 min na
  5 procesach – limit autora „do ok. 3 h”); tag `kalibracja-start` na tym commicie.
- Kod bez zmian. Skrypt pomiaru: krzywa trudności (6 poziomów × 5 strategii × 20 ziaren), 4/8 firm i
  12/26 rund (człowiek średni, poziom średni, 10 ziaren), warianty 28 opcji × 5 strategii × 30 ziaren
  (6 firm) i × 3 strategie × 10 ziaren (4 i 8 firm).
- Najważniejsze:
  - trudność: pierwszy plus „jak człowiek” średniego w rundzie 2 w 62/100 gier (cel 4–6 – 19%); wersja słaba
    ma alarm w 17/100 gier (agresywny 15/20); dobra > średnia w 95/100 par;
  - dominacje: umowa zlecenie (99% par), drugi lokal (85%), mBank, e-Księgi24, higiena podstawowa; polisy
    lekko na plus; jakość 2★ zdominowana u zrównoważonego i naśladowcy;
  - strategie: tani (karta 0,30) i agresywny (0,05, alarm w 9/30) nigdy nie wygrywają; agresywnego poprawia
    prawie każda zmiana parametru, taniego – wyższa cena i brak promocji;
  - realia: marża netto 19%, praca 21% przychodu, czynsz 4% – czynsz w złotych realny (ogłoszenia z Lublina),
    za wysoki jest przychód na lokal (ok. 97 tys. zł / mies.).
- **Pytanie do autora:** przy 4 firmach gra jest wyraźnie łatwiejsza (karta człowieka średniego 0,68 wobec
  0,44 przy 6 i 0,30 przy 8 firmach; alarmów 0/50). Z4 zmniejsza liczbę lokali, ale popyt miasta zostaje.
  Czy popyt (pule stref) ma zależeć od liczby firm, czy tak ma zostać (mniejsza klasa = łatwiej)? Plan każe
  tego nie stroić bez zgody – w B5 kalibruję na 6 firmach.
- Dalej: B5 od razu (gospodarka i trudność), potem stop do zatwierdzenia.

## B5 – gospodarka i trudność (29.10.2026, Claude Code, Opus 5.5) – zatwierdzone przez autora
- Pomiary: `pomiary/b5_trudnosc` (6 poziomów × 5 strategii × 20 ziaren, 6 firm, 18 rund, rywale średni),
  `b5_firmy` (4 i 8 firm), `b5_dlugosc` (12 i 26 rund), `b5_szybki` (regresja wariantów). Porównanie z B4:
  `b4_trudnosc`, `b4_firmy_trudnosc`, `b4_dlugosc`. Szukanie liczb: skrypt par na kopii `dane/`
  (bot „jak człowiek” słaby / średni / dobry × 5 strategii × 10–20 ziaren, ok. 3 min na 10 ziaren).
- Diagnoza B4: pierwszy plus w rundzie 2, bo pierwszy tydzień sprzedaży ma pełny popyt przy najniższych
  kosztach (2 osoby, mały zapas). Same pule nie pomagają: pule ×0,75 → mediana pierwszego plusu 3, ale marża
  spada do 11% i wersja słaba częściej wygrywa ze średnią (37/50 par); ×0,6 – marża 7%. Kapitał 50–60 tys. zł
  nie zmienia alarmów (agresywny 5–6/50).
- Zmiany:
  1. **Nowa mechanika – rozruch nowego lokalu** (`silnik/rynek/popyt.py: rozruch`, schemat `Rozruch`,
     `dane/mapa/popyt.yaml: model.rozruch: {start: 0.4, przyrost: 0.1}`): mnożnik atrakcyjności lokalu
     0,4 w pierwszym tygodniu sprzedaży (najwcześniej runda 2), co tydzień +0,1, od 7. tygodnia 1. Działa tak
     samo dla kolejnego lokalu; widzą go prognozy (zakładka Klienci, boty). Bez klucza w danych – 1 (zamrożona
     kopia danych testów go nie ma, więc testy wzorów bez zmian). Warianty: 0,5/0,1 – wynik podobny, ale pierwszy
     plus bywa już w rundzie 2 (2/50); 0,4/0,1 – nigdy w 2.
  2. **Pule stref ×0,9** (`dane/mapa/popyt.yaml`, wszystkie strefy; było 1,0 / 1,2 / 1,1 / 0,7 / 0,8 / 0,6 /
     0,9 / 0,7 / 0,5 / 0,4): przychód lokalu bliżej realiów i mniej pierwszych plusów w rundzie 3
     (×0,85 – słaba częściej wygrywa ze średnią: 83/100 par wobec 89/100).
  3. **Boty: zakupy dodatkowe w budżecie** (`silnik/boty.py: _w_budzecie`): wyposażenie i udogodnienia bot kupuje
     po kolei, póki po zakupie zostaje `bufor_gotowki` (30 tys. zł); szkolenia i nowe promocje – tylko gdy coś
     z budżetu zostało. Wcześniej przy gotówce > 30 tys. zł agresywny kupował od razu cały komplet (12 pozycji,
     ok. 17 tys. zł) + kampanie i szkolenie i wpadał w debet ponad limit. Bez rozruchu alarmy wersji słabej
     7/50 → 4/50.
- Wynik (bot „jak człowiek”, 6 firm, 18 rund, 100 gier na wersję; przed = B4):

  | miara | przed (B4) | po (B5) | cel |
  |---|---|---|---|
  | pierwszy plus średniej w rundach 4–6 | 19/100 (w 2: 62) | 65/100 (w 3: 35, w 2: 0) | 4–6 |
  | alarmy wersji słabej | 17/100 (bez agresywnego 2) | 8/100 (bez agresywnego **0**) | 0 |
  | dobra > średnia (pary) | 95/100 | 92/100 | ≥ 80% |
  | słaba < średnia (pary) | – | 89/100 | – |
  | karta słaba / średnia / dobra | 0,11 / 0,42 / 0,62 | −0,01 / 0,23 / 0,34 | słaba może być na minusie |
  | majątek netto średniej (tys. zł) | 115 | 93 | – |

  Realia (średnia wersja, wszystkie strategie): marża netto 16% → 13%, praca 22% → 23% przychodu, czynsz
  4,2% → 4,8%, składniki 35%, przychód lokalu ok. 103 → 87 tys. zł na miesiąc (20 tys. zł na tydzień).
- Inne konteksty (człowiek średni, 50 gier): 4 firmy – pierwszy plus 4–6 w 28/50 (było 3/50), karta 0,50
  (było 0,68); 8 firm – 36/50 (było 10/50), karta 0,15; 12 i 26 rund – 33/50 (było 7/50), alarmy tylko
  u agresywnego. Pytanie z B4 o 4 firmy nadal otwarte (gra łatwiejsza: karta 0,50 wobec 0,23 przy 6).
- Poziomy botów (B3) po zmianach: łatwy < średni w 83/100 par, średni < trudny w 88/100 (każda strategia
  ≥ 13/20; naśladowca najsłabiej). Karta łatwy / średni / trudny 0,10 / 0,33 / 0,67.
- Regresja `balans.warianty szybki` (549 gier w limicie 10 min): ten sam obraz co w B4 – „lepsze” umowa zlecenie
  (100% par), drugi lokal (74%), polisy, brak promocji u zrównoważonego; banki inne niż mBank i inne biura
  „gorsze”; brak higieny – bankructwo. Nowych dominacji brak.
- Czego B5 nie rozwiązuje (do B6–B12): **strategia agresywna** (cena 0,8 przy jakości 3★, cała reklama)
  traci na każdym poziomie – wersja słaba ma alarm w 8/20 gier, bo proste planowanie kupuje towar za tyle,
  ile wynosi przychód, a potem dokupuje sprzęt kuchni bez patrzenia na gotówkę (H17). To balans strategii,
  nie liczb gospodarki. Praca 23% przychodu – trochę poniżej celu 25–35% (płace przy minimalnej; prawo
  zamrożone, więc zostaje).
- **Pytania do autora (zatwierdzenie B5):**
  1. Czy zgoda na nową mechanikę „rozruch nowego lokalu” (40% klientów w pierwszym tygodniu sprzedaży,
     +10 p.p. co tydzień)? Jest widoczna dla gracza – opis w `gra/INSTRUKCJA.md` (rozdział 6), propozycja do
     „Ustaleń gry” w `notatki_do_zmiany.md`.
  2. Czy zatwierdzić pule stref ×0,9 i regułę zakupów bota?
  3. Strategia agresywna zostaje „pułapką” do B6–B12 – czy tak może być?
- **Odpowiedzi autora (29.10.2026): 4 × tak** – rozruch nowego lokalu zostaje, pule ×0,9 i zakupy bota
  w budżecie zatwierdzone, strategia agresywna zostaje do B6–B12, przy 4 firmach gra może być łatwiejsza
  (popyt nie zależy od liczby firm; pytanie z B4 zamknięte).
- Inne odpowiedzi autora (29.10.2026): **P1** – zlecenie dostaje składki ZUS pracodawcy (w B9); **Z7** – po
  końcu gry drużyna widzi wyniki ostatniej rundy i końcowe miejsce; **Z5** – boty „jak człowiek” do wyboru
  przez mistrza gry. Propozycje Z1–Z6 i B5 wpisane do notatek.
- Testy: nowe `test_rozruch_nowego_lokalu` (`testy/rynek/test_popyt.py`) i
  `test_zakupy_dodatkowe_bota_zostawiaja_bufor_gotowki` (`testy/rdzen/test_boty.py`). Inne testy bez zmian.

## H17 – słaby bot agresywny bez bankructwa (29.10.2026, Claude Code, Opus 5.5)
- Wybór autora po B5: „poprawić bota agresywnego”. Diagnoza (6 gier, słaby „jak człowiek” agresywny, 6 firm,
  18 rund): kuchnia obsługuje ok. 37% popytu na 8 dań (brak miejsc w kuchni – przyczyna „pracownicy/sprzęt”),
  a proste planowanie zamawia towar na cały przewidywany popyt. Psuje się towar za 27% przychodu (przy innych
  strategiach 7–9%), towary to 68% przychodu. Sprzęt kuchni nie był przyczyną – zakupy w budżecie działają od B5.
- Zmiana: nowe pole poziomu `zamowienia_ze_sprzedazy` (`dane/boty.yaml`, schemat `PoziomBota`), tylko
  u `czlowiek_slaby` = 1,1: gdy tydzień temu danie traciło klientów w kolejce (kuchnia lub kasa, `karta.KOLEJKI`),
  bot zamawia na nie najwyżej tamtą sprzedaż × 1,1 – człowiek widzi, że towar się psuje. Łatwy bez zmian
  (zostaje najsłabszy, test „planujący bot marnuje mniej towaru”).
- Wynik (20 ziaren × 5 strategii, jak seria B5; przed = konfiguracja B5):

  | miara | przed | po |
  |---|---|---|
  | alarmy wersji słabej | 8/100 (wszystkie agresywny) | **0/100** |
  | karta słaba / średnia / dobra | −0,01 / 0,23 / 0,34 | 0,05 / 0,23 / 0,34 |
  | słaba < średnia (pary) | 89/100 | 85/100 |
  | średnia < dobra (pary) | 92/100 | 92/100 |
  | pierwszy plus średniej w rundach 4–6 | 65/100 | 65/100 |
  | psucie towaru słabego agresywnego (% przychodu) | 27% | 7% |

  Średnia i dobra wersja bez zmian (ich planowanie nie korzysta z nowego pola). Strategia agresywna dalej
  traci (dochód słabej ok. −1 tys. zł za grę) – balans strategii zostaje do B6–B12.
- Test: nowy `test_slaby_czlowiek_zamawia_mniej_gdy_kuchnia_nie_nadazyla` (`testy/rdzen/test_boty.py`;
  bez reguły nie przechodzi). Inne testy bez zmian.

## U21 – „zarób i zamknij”: pomiar zamknięcia firmy (4.11.2026, Claude Code, Opus 5.5)
- Pozycja [22] raportu `raporty/analiza_gracza.md`: czy opłaca się zarobić kilka rund i zamknąć firmę
  (karta rund bez sprzedaży ≈ 0, pyt. 2 – autor: zostaje jak jest).
- **Najemca nie może wypowiedzieć najmu.** `wypowiedz` w decyzjach to wypowiedzenie przez nowego właściciela
  budynku po przejęciu (`silnik/nieruchomosci/przejecia.py`), nie przez gracza. Zamknięta firma płaci więc
  czynsz (i media) do końca gry – „wypowiedzenie najmu” z opisu pozycji nie istnieje.
- Warianty w `balans/warianty.py` (`zamknij_od`, `zamknij_twardo`, decyzje z `_zamknij`): od rundy N firma
  zwalnia wszystkich i nic nie zamawia, nie reklamuje się, nie bierze kredytów; wersja „twarda” do tego
  sprzedaje sprzęt, zdejmuje menu i polisy. `zamkniecie:1` – od rundy 1 nic nie robi (bez lokalu), punkt
  odniesienia.
- Pomiar: zrównoważony, 18 rund, 6 firm, poziom średni, 20 ziaren (1000–1019), 120 gier,
  `pomiary/u21_zamkniecie/`. Karta = średni wynik działalności rund 2–18 (jak ranking).

  | wariant | karta | Δ karta vs baza (95%) | dochód zł | majątek zł | miejsce (z 6) |
  |---|---|---|---|---|---|
  | baza (gra do końca) | 0,523 | – | 70 308 | 118 316 | 2,7 |
  | zamknięcie od R11 | −0,130 | −0,65 ± 0,06 | 3 365 | 50 782 | 5,9 |
  | zamknięcie od R11, twarde | −0,123 | −0,65 ± 0,06 | 3 862 | 47 253 | 5,85 |
  | zamknięcie od R6 | −0,449 | −0,97 ± 0,11 | −33 686 | 11 423 | 6,0 |
  | zamknięcie od R6, twarde | −0,442 | −0,96 ± 0,11 | −33 110 | 9 298 | 6,0 |
  | nic od R1 (bez lokalu) | −0,016 | −0,54 ± 0,10 | −1 347 | 40 653 | 5,65 |

- **Wniosek: zamknięcie się nie opłaca** – 0 z 20 par lepszych od gry do końca, przy każdym terminie.
  Zamknięta firma ma gorszą kartę niż ta, która w ogóle nie otworzyła lokalu: czynsz bez sprzedaży to strata
  każdego tygodnia, a strata liczy się do karty z wagą 1,0. Wcześniejsze zamknięcie = dłużej płacony czynsz
  = gorzej (R6 gorzej niż R11). Sprzedaż sprzętu prawie nic nie zmienia (sprzęt poniżej 10 000 zł jest już
  zamortyzowany w kosztach). Bezczynność od R1 daje karta ≈ 0 – zgodnie z odpowiedzią autora na pyt. 2,
  ale to 5.–6. miejsce. Pułapki „zarób i zamknij” w tej grze nie ma; zmiana zasad niepotrzebna.

## U22 – wskaźnik zadłużenia z gotówką w mianowniku (4.11.2026, Claude Code, Opus 5.5) – decyzja autora
- Pytanie 3 raportu `raporty/analiza_gracza.md`, odpowiedź autora 3.11.2026: gotówka wchodzi do mianownika.
  Dotąd kredyt leżący na koncie karał tak samo jak przejedzony (A2: „nigdy nie bierz kredytu”).
- Wzór (`silnik/wyniki/karta.py: wskaznik_zadluzenia`, `dane/zalozenia.yaml`):
  1 − dług / (majątek karty + skumulowany dochód netto + dług + gotówka), min 0. Ujemna gotówka (debet)
  nie zmniejsza mianownika – debet jest już w długu. Bez długu wskaźnik = 1, jak dotąd.
- Pomiar: warianty A2 `ekspansja` i `ekspansja_na_kredyt` (kredyt 50 tys. zł w R1, 52 tygodnie),
  `raporty/analiza/skrypty/eksperymenty.py`, ziarna 202–204, ten sam silnik ze starym i nowym wzorem:

  | ziarno | ekspansja | na kredyt – przed | na kredyt – po | wskaźnik przed → po |
  |---|---|---|---|---|
  | 202 | 0,555 | 0,183 | 0,370 | 0,42 → 0,75 |
  | 203 | 0,487 | 0,199 | 0,360 | 0,39 → 0,75 |
  | 204 | 0,521 | 0,184 | 0,374 | 0,42 → 0,75 |

  „Przed” odtwarza liczby z A2 (`raporty/analiza/dziennik_optymalizator.md`, pkt 3). Dochód i majątek bez
  zmian (wzór dotyczy tylko karty). Kara za kredyt zmalała mniej więcej o połowę; kredyt nadal kosztuje
  (odsetki, wskaźnik < 1), więc bierze się go po to, żeby na nim zarobić. Gry bez długu – bez zmian (boty
  kredytów nie biorą).
- Teksty: podpowiedź przy nowym kredycie (Finanse ▸ Bank) i tabela wskaźników w INSTRUKCJA.
  Test: `test_wskaznik_zadluzenia` (gotówka w mianowniku, debet nie pomaga).

## U23 – zatrudnianie od tygodnia 1 (4.11.2026, Claude Code, Opus 5.5) – decyzja autora
- Pytanie 6 raportu `raporty/analiza_gracza.md`, odpowiedź autora 3.11.2026: zatrudnienie od tygodnia 1, żeby
  pierwszy tydzień sprzedaży nie startował z rekrutacją.
- `dane/katalog.yaml`: `hr_zatrudnienie` tydzień 2 → 1 (zakładki i lista odblokowania). Tydzień 1 jest
  przygotowawczy, więc mistrz gry nie przesunie już tego terminu w harmonogramie. W tygodniu 1 działa tylko
  pracuj.pl (agencja od 2, headhunter od 4 – `dane/kandydaci.yaml`, bez zmian). Pensja liczy się od tygodnia
  zatrudnienia. Dane zamrożone testów bez zmian (testy mechanik zostają przy tygodniu 2).
- Boty zatrudniają, gdy zakładka jest odblokowana, więc teraz robią to w tygodniu 1. Pomiar (zrównoważony,
  18 rund, 6 firm, średni, ziarna 1000–1019, baza z `pomiary/u21_zamkniecie` wobec tej samej serii po zmianie):

  | miara | tydzień 2 | tydzień 1 |
  |---|---|---|
  | karta | 0,523 | 0,528 |
  | dochód zł | 70 308 | 69 179 |
  | majątek zł | 118 316 | 117 058 |
  | pierwszy plus (runda) | 3,7 | 3,6 |
  | alarmy | 0 | 0 |

  Tydzień pensji więcej kosztuje ok. 1,1 tys. zł dochodu, a karta (od tygodnia 2) minimalnie rośnie – obsada
  jest gotowa na pierwszy tydzień sprzedaży. Balans bez istotnej zmiany.
- Teksty: INSTRUKCJA rozdz. 4 (krok 5 „Ludzie”) i tabela w rozdz. 14; panel gracza `OD_RUNDY`.
  Test: `test_zatrudnienie_w_tygodniu_przygotowawczym` (`testy/ludzie/test_rynek_pracy.py`, dane gry).

## U20 – zadowolenie osób, ukryte cechy i odejścia (4.11.2026, Claude Code, Opus 5.5) – decyzja autora
- Projekt `raporty/projekt_U20_dynamika_pracownikow.md`. Decyzja autora 4.11.2026: etap 1 + ukryte cechy, które
  gracz wnioskuje z krótkiego żartobliwego opisu pod „i”. Odejście nie jest pewne, szansa rośnie z niezadowoleniem.
- Zadowolenie osoby liczy wzór karty dla jednej osoby (pensja z premią ÷ preferowana, sprzęt stanowiska,
  udogodnienia lokalu, szkolenia, zlecenie) i odejmuje przepracowanie (próg i waga z kebabu karty). Wskaźnik karty
  liczy się jak dotąd, więc kalibracja karty się nie zmienia.
- `dane/zalozenia.yaml: pracownicy.odejscia` (`pewnosc: zalozenie`): próg 0,87. Pierwszy tydzień poniżej progu
  daje tylko ostrzeżenie (lista błędów, pomarańczowy). Od drugiego tygodnia z rzędu jest szansa 5% za każde 0,01
  poniżej progu, najwyżej 50%. Cecha mnoży tę szansę. Wypowiedzenie działa jak zwolnienie bez odprawy.
- `dane/kandydaci.yaml: cechy`: 10 cech z wagami, każda ma 3 opisy. Panel gracza nie dostaje pola `cecha` ani `wydajnosc`.
  Szybki/niespieszny: ±10% godzin stanowiska.
- Boty: `dba_o_ludzi` (średni, trudny, niemożliwy, człowiek średni/dobry). Bot podnosi pensję
  niezadowolonej osobie do progu + 0,01, najwyżej do 115% preferowanej. Cechy nie zna. Łatwy ignoruje ostrzeżenia.
- Pomiar: 5 strategii × 6 ziaren (1–6) × 12 rund. Miara to suma wyniku działalności z 12 tygodni, średnia na firmę.
  „Bez U20” to te same ziarna i cechy, ale osoby nie odchodzą.

  | poziom | bez U20 | z U20 | odejścia (30 gier) | osobotygodnie niezadowolone |
  |---|---|---|---|---|
  | łatwy | 1,391 | 1,160 | 5 | 8,0% |
  | średni | 4,080 | 4,079 | 0 | 1,3% |
  | trudny | 4,549 | 4,527 | 0 | 1,4% |
  | niemożliwy | 4,181 | 4,001 | 0 | 1,1% |

  Skąpy gracz to boty płacące wszystkim płacę minimalną, bez podwyżek (pensja ≈ 95% preferowanej):

  | poziom | bez U20 | próg 0,87 | próg 0,88 | próg 0,89 |
  |---|---|---|---|---|
  | łatwy, normalnie | 1,391 | 1,160 | 1,021 | 0,919 |
  | łatwy, skąpo | 1,519 | 1,261 (9 odejść) | 0,979 (14) | 0,843 (16) |
  | trudny, normalnie | 4,549 | 4,527 | 4,519 | 4,516 |
  | trudny, skąpo | 4,716 | 4,650 (3 odejścia) | 4,698 (5) | 4,426 (8) |

  - **Próg 0,87.** Odejścia zdarzają się tylko przy zaniedbaniu (przepracowanie, słaby sprzęt, niska pensja).
    Poziomy średni i trudny prawie się nie zmieniają. Łatwy traci ok. 0,23, bo przeciąża ludzi i nie reaguje na
    ostrzeżenia. Oszczędzanie na pensjach opłaca się mniej niż bez U20 (trudny: +0,17 → +0,12), ale nadal trochę się opłaca.
  - **Próg 0,89.** Skąpstwo przestaje się opłacać (trudny: 4,426 wobec 4,516), ale łatwy spada o ok. 0,47.
  - **Wahania między ziarnami** są duże (próg 0,88 na trudnym wypada lepiej dla skąpych niż 0,87).
  - **Decyzja:** zostawiam 0,87, a autor może podnieść próg (jedna liczba w `zalozenia.yaml`).
- Zmieniony test: `test_trudny_bot_otwiera_kolejny_lokal`. Na ziarnie 7 jedno odejście i podwyżki przesunęły próg gotówki
  drugiego lokalu, a na ziarnach 1–5 liczba drugich lokali się nie zmienia, więc test sprawdza też drugie ziarno.
  Nowe testy: `testy/ludzie/test_zadowolenie.py`.
- Teksty: INSTRUKCJA rozdz. 8 i 15, podpowiedź „Dbaj o ludzi”. Usunięte zdanie „pracują gorzej”, bo wydajność
  zależy od cechy, nie od nastroju. Panel HR: opis pod „i”, zadowolenie w profilu i wynikach, tabela wypowiedzeń.

## U24 – opinie klientów i 8 grup klientów (4.11.2026, Claude Code, Opus 5.5)
- Decyzje autora: projekt `raporty/projekt_U24_opinie_i_grupy_klientow.md` (ocena z przeżyć klientów, wpływ
  na popyt + komentarze, 8 grup z koszykiem, obie mechaniki razem).
- Zrobione:
  - `silnik/rynek/klienci.py` – grupy, koszyk (wegetarianie przenoszą popyt mięsny na bezmięsne dania koszyka,
    popyt roczny miasta bez zmian), wrażliwość cenowa grup (średnio równa wrażliwości strefy), zastępstwo dań;
  - `silnik/rynek/opinie.py` – ocena tygodnia z powodów, średnia krocząca, liczba opinii ze sprzedaży,
    mnożnik popytu z zaufaniem, komentarze ze strumienia `opinie`;
  - `popyt.podzial` liczy grupa × lokal × dzień. Mapa: gwiazdki i komentarze przy lokalach. Zakładka Klienci:
    skład grup stref, grupy w lokalach, tabela powodów oceny.
- Pomiar: 5 strategii × ziarna 7–10 × 14 rund. Miara to suma wyniku działalności, średnia na firmę. „Przed” to te
  same gry bez `klienci.yaml`.

  | poziom | strategia | przed | po | mnożnik (mediana) | ocena (mediana) |
  |---|---|---|---|---|---|
  | łatwy | agresywny | −4,91 | −3,83 | 0,87 | 2,3 |
  | łatwy | naśladowca | −0,10 | 0,14 | 0,88 | 2,2 |
  | łatwy | premium | 4,58 | 6,89 | 1,03 | 3,6 |
  | łatwy | tani | 0,69 | 1,25 | 0,85 | 2,0 |
  | łatwy | zrównoważony | 4,00 | 4,19 | 0,94 | 2,7 |
  | średni | agresywny | 1,66 | 1,54 | 0,86 | 2,2 |
  | średni | naśladowca | 5,24 | 6,21 | 1,00 | 3,4 |
  | średni | premium | 7,17 | 9,76 | 1,06 | 3,9 |
  | średni | tani | 4,59 | 4,60 | 0,90 | 2,4 |
  | średni | zrównoważony | 6,06 | 6,83 | 1,00 | 3,3 |
  | trudny | agresywny | 2,55 | 4,61 | 0,91 | 2,5 |
  | trudny | naśladowca | 5,70 | 6,45 | 1,01 | 3,4 |
  | trudny | premium | 7,53 | 8,96 | 1,03 | 3,7 |
  | trudny | tani | 3,81 | 3,76 | 0,92 | 2,5 |
  | trudny | zrównoważony | 6,23 | 7,40 | 1,01 | 3,4 |

- Wnioski z kalibracji:
  - **Zastępstwo dań** było najmocniejszą dźwignią. Przy 35% premium (wąskie menu, drogie dania) miał ok. 12
    zamiast 6,6, bo klienci bez ulubionego dania i tak zostawali. Przy 10% reszta grup działa umiarkowanie.
  - **Rozrzut wrażliwości cenowej grup** prawie nie zmienia wyników – grupy działają głównie przez koszyk.
  - **Opinie:** pierwsza wersja (start 3,0, odniesienie 3,4, wykładnik 1) dawała typową ocenę 2,4 i mnożniki
    0,58–1,0 – za mocno. Teraz start 3,6, jakość 0,3★ za gwiazdkę ponad 2, odniesienie 3,3, wykładnik 0,4:
    mnożniki 0,86–1,06, jak dawny mnożnik karty (0,83–1,05).
  - Prawie wszyscy zyskują (agresywny na średnim i tani na trudnym bez zmian). Najwięcej
    zyskuje premium: na średnim prowadzi ok. 1,4× przed zrównoważonym (wcześniej 1,18×), na trudnym 1,21×
    (wcześniej 1,21×). Tani ma najniższe oceny, bo jego kolejki i słaba jakość widać w opiniach.
  - Kolejność strategii bez zmian. Do obserwacji w B: przewaga premium na średnim; jeśli w grze z drużynami
    będzie za duża, pierwsza dźwignia to `opinie.jakosc` (0,3 → 0,2).
- Zmienione testy: `test_zamrozona_kopia_ma_wszystkie_pliki_danych` (pomija opcjonalny `mapa/klienci.yaml`).
  `sprawdz` nie wymaga tego pliku. Wyniki testów mechanik do grosza bez zmian (zamrożona kopia nie ma grup).
  Nowe testy: `testy/rynek/test_klienci_opinie.py`.
- Teksty: INSTRUKCJA rozdz. 6 i rada 4 w rozdz. 15, „i” w zakładkach Mapa i Klienci, podpowiedź karty.

## K – kontrola po U (4.11.2026, Claude Code, Opus 5.5)
- Pomiary: `pomiary/k_trudnosc` – bot „jak człowiek” słaby / średni / dobry × 5 strategii × ziarna 1000–1019,
  6 firm, 18 rund, rywale średni (300 gier); `pomiary/k_szybki` – `balans.warianty szybki`, 3 strategie × 6 ziaren
  (666 gier, 648 par, 18 par na wariant). Pierwsza wersja wpisu (10 min, 10 ziaren, 7 par) – dokończona tego
  samego dnia bez limitu czasu; wnioski bez zmian kierunku.
- Trudność – porównanie z B5 na tych samych ziarnach 1000–1019 (100 trójek gier):

  | miara | B5 | K (po U1–U24) | cel |
  |---|---|---|---|
  | pierwszy plus średniej w rundach 4–6 | 65/100 (w 3: 35) | 51/100 (w 3: 48, w 2: 1) | 4–6 |
  | alarmy wersji słabej | 8/100 (agresywny) | **0/100** | 0 |
  | dobra > średnia (pary) | 92/100 | **74/100** | ≥ 80% |
  | słaba < średnia (pary) | 89/100 | 89/100 | – |
  | karta słaba / średnia / dobra | −0,01 / 0,23 / 0,34 | 0,09 / 0,32 / 0,35 | słaba może być na minusie |
  | majątek netto średniej (tys. zł) | 93 | 99 | – |

  Dobra > średnia wg strategii: agresywny 13/20, naśladowca 15/20, tani 14/20, premium 15/20, zrównoważony 17/20
  (B5: 20, 20, 17, 18, 17). Remisów brak (jedna para z różnicą < 0,005). Na 10 pierwszych ziarnach – 34/50 jak
  w pierwszej wersji wpisu.
- Wnioski:
  - **Cel „dobra wyraźnie wygrywa” rozjechał się** (74% par wobec ≥ 80%). Średnia i słaba zyskały po U (karta
    +0,09…+0,10), dobra – prawie nie (+0,01). Najbardziej przy agresywnym i naśladowcy. To nie liczby B5 (rozruch,
    pule), tylko poziom `czlowiek_dobry` w `dane/boty.yaml` albo mechaniki U20/U24, które dobra wykorzystuje gorzej
    (np. drugi lokal bez opinii). Propozycja i decyzja – u autora (hipoteza H24 w inwentarzu).
  - **Pierwszy plus przesunął się na rundę 3** (48/100 wobec 35/100) – cel 4–6 spełniony w 51% gier. Po U
    średnia szybciej wychodzi na plus (zatrudnianie od tygodnia 1 – U23, grupy klientów – U24). Do rozważenia
    razem z poziomem dobrym (rozruch nowego lokalu, B5); bez zmiany do decyzji autora.
  - Alarmy wersji słabej zniknęły – cel spełniony.
- Obszary (`k_szybki`, 18 par): bank i biuro bez zmian (mBank, e-Księgi24 najtańsze – H4, H5); higiena brak
  katastrofą, HACCP lekko gorsza (H15); **umowa zlecenie +0,07 w 18/18 par** (H3, H27 – czeka na składki w B9);
  **polisy komplet +0,01 w 78% par** – „lepszy”, odwrotnie niż H14 (H26); jakość 3★ +0,05 (67%, szum; przy
  premium jakość 1–2 to −0,17…−0,19 – H28); **drugi lokal −0,23 (19% par, „gorszy”)** – odwrotnie niż H6 z B4
  (H21); kampanie – brak −0,05 (gorszy, H25); **promocje – brak +0,13 w 6/6 par przy premium** (nowa H29);
  cena 1,15 przy premium +0,05 w 6/6 par (szum przedziału, H18). Nowe hipotezy H18–H29 w inwentarzu (H18–H25
  z raportu A, H26–H29 z K).
- Do pełnego K zostaje decyzja autora o poziomie „dobrym” (poprawka liczb tylko za zgodą).
- **Diagnoza poziomu dobrego** (`pomiary/k_dobry`, decyzja autora po K, pkt 1): `balans.warianty pelny --poziom
  czlowiek_dobry --rywale sredni`, 5 strategii × ziarna 1000–1019 × 18 rund × 6 firm (600 gier, 16 min).
  Gra bazowa = dobra z `k_trudnosc` (100/100 kart identycznych), więc każdy wariant porównuję z tą samą grą
  średniej. Nowe warianty `czlowiek:*` w `balans/warianty.py` zabierają dobremu po jednej przewadze nad średnim;
  `czlowiek:jak_sredni` (wszystkie naraz) daje gry identyczne ze średnią (karta 0,320) – kontrola metody.

  | dobry … | karta | dobra > średnia | agresywny | naśladowca | premium | tani | zrównoważony |
  |---|---|---|---|---|---|---|---|
  | jak teraz | 0,351 | 74/100 | 13/20 | 15/20 | 15/20 | 14/20 | 17/20 |
  | bez drugiego lokalu (`lokale:jeden`) | **0,398** | **85/100** | 19/20 | 15/20 | 16/20 | 18/20 | 17/20 |
  | bez reklamy z wolną kuchnią | 0,340 | 73/100 | 10/20 | 15/20 | 15/20 | 16/20 | 17/20 |
  | prognoza bez poprawki o pulę | 0,306 | 52/100 | 12/20 | 10/20 | 13/20 | 7/20 | 10/20 |
  | prognoza jak średni (1 tydzień, ±10%) | 0,269 | 18/100 | 12/20 | 0/20 | 1/20 | 4/20 | 1/20 |
  | wszystko jak średni (kontrola) | 0,320 | 0/100 (remisy) | – | – | – | – | – |

  - **Cała przewaga dobrego to prognoza** (2 tygodnie z poprawką o pulę strefy, bez błędu): bez niej dobry
    przegrywa ze średnim w 82% par.
  - **Drugi lokal ją zjada:** dobry otwiera go w 14/100 gier (agresywny 7, tani 4, premium 3) i w tych grach
    traci (agresywny −0,15, 68% par). To ten sam problem co H21 (drugi lokal się nie opłaca w 18 rundach –
    rozruch B5, opinie od zera), nie błąd poziomu.
  - Reklama z wolną kuchnią pomaga tylko agresywnemu (+0,07), reszta bez zmian.
  - Propozycja: w `czlowiek_dobry` usunąć `kolejny_lokal` (85/100 par). **Decyzja autora 4.11.2026: nie** – boty
    mają dalej kupować kolejne lokale; naprawa w B6 (H21: drugi lokal ma się opłacać w swojej sytuacji), cel
    „dobra wyraźnie wygrywa” sprawdza ponownie B14. K zamknięte.
- Decyzje autora po K (4.11.2026): (1) bot dobry – zdiagnozować parami i zaproponować zmiany poziomu
  `czlowiek_dobry` (tabela przed zmianą, zmiana po zgodzie); (2) pomiary B6–B15 **bez limitu czasu**, wiele
  pomiarów naraz; (3) przewaga premium – w B7 razem z ceną (H18, H28); (4) U20 i U24 – propozycje tekstów do
  `notatki_do_zmiany.md`, wpis do `notatki/` po zgodzie.

## B6 – lokale (4.11.2026, Claude Code, Opus 5.5) – zakończone 6.11, gałąź `kalibracja-b6`

Cała praca B6–B15 na gałęzi `kalibracja-b6` (decyzja autora: bez merge do main bez zgody, bez FTP).
Pomiary `balans.warianty pelny`, 3 strategie (zrównoważony, tani, premium) × 18 i 26 rund × 6 firm, poziom średni,
badana firma w strefie z listy; Δ – wariant − baza na tych samych grach (para: kontekst + ziarno).

**Krok 0 i poprawki botów (commity na gałęzi):**
- c7f80e3, f283986 – boty mogą wziąć każdą opcję lokalu (kupno na kredyt pod zastaw, niewyposażony, działka,
  przebicie w licytacji), sprzęt w leasingu, wykup własnego lokalu i kupno budynku rywala z wypowiedzeniem.
- 36816c6 – bot z kilkoma lokalami zamawia towar z zapasów każdego lokalu (wcześniej z całej firmy: w jednym
  lokalu brak towaru, w drugim się psuł).
- a06b562 – bot kupuje szafę chłodniczą i zamrażarkę do lokalu bez nich (lokal bez zestawu nie miał gdzie trzymać
  towaru); działka: koszt budowy w decyzji i w zastawie kredytu (decyzja autora: zastaw liczy budynek).
- 6401d33 – dopłata do kupna lokalu kredytem bez historii (działka: kredyt pod zastaw nie pokrywał wejścia
  z budową); rezerwa 30 tys. dla wariantów bez zestawu; wariant `lokale:niewyposazony_q3`.
- 8655353 – bot planujący finansuje sprzęt ponad gotówkę kredytem bez historii (`rezerwa_po_sprzecie`
  10 000 zł): wcześniej przy lokalu bez zestawu kupował cały sprzęt gotówką, wpadał w debet ponad limit i bank
  blokował mu inwestycje na kilka rund. W grach z gotowym lokalem żadnego kredytu – baza bez zmian.

**Wyniki dotąd** (Δ karty, wygrane pary):

| wariant | pomiar (kod) | 18 rund | 26 rund | razem |
|---|---|---|---|---|
| niewyposażony w najmie | `b6_typy` (przed chłodnią) | – | – | −0,68 (1/600) |
| niewyposażony w najmie | `b6_typy_po` (a06b562) | −0,08 | −0,03 | −0,05 (230/600) |
| niewyposażony, sprzęt w leasingu | `b6_typy_po` | −0,05 | −0,05 | −0,05 (217/600) |
| kupno gotowego (6 stref peryferyjnych) | `b6_typy_po`, niepełny (6401d33) | −0,06 | −0,09 | −0,07 (64/114) |
| kupno niewyposażonego | `b6_typy_po`, niepełny (6401d33) | −0,27 | −0,22 | −0,24 (16/114) |

`b6_drugi_po` (4/6/8 firm, 12/18/26 rund, 5 strategii; kod przed 6401d33) – drugi lokal (H21):

| wariant | 12 rund | 18 rund | 26 rund | razem |
|---|---|---|---|---|
| drugi gotowy w najmie | +0,04 | +0,11 | **+0,23** | +0,13 (211/450) |
| drugi gotowy na kupno | +0,03 | +0,09 | +0,20 | +0,11 (219/450) |
| drugi niewyposażony | −0,07 | −0,15 | −0,13 | −0,12 (27/450) |

- Drugi lokal **już się opłaca** i tym bardziej, im dłuższa gra (cel H21) – po zamówieniach z zapasów lokalu.
- Niewyposażony: z −0,68 do −0,05 po chłodni i zamrażarce. Wariant 3★ (niewyposażony z własnym lepszym sprzętem
  – kompromis z inwentarza) przegrywał z gotowym 3★ o 0,22 (niepełny pomiar, 141 par) przez debet przy zakupie
  sprzętu – stąd 8655353; pomiar na nowym kodzie w toku.

**`b6_niewyp2`** (kod 8655353, 10 stref × 3 strategie × 18/26 rund × 6 ziaren, 1800 gier, ok. 25 min):

| wariant − baza | 18 rund | 26 rund | razem |
|---|---|---|---|
| niewyposażony w najmie | −0,16 | −0,09 | −0,12 (100/360) |
| niewyposażony, sprzęt w leasingu | −0,06 | −0,07 | −0,06 (125/360) |
| gotowy, jakość 3★ (`jakosc:3`) | +0,05 | +0,06 | +0,06 (172/360) |
| niewyposażony 3★ | −0,21 | −0,08 | −0,15 (99/360) |
| **niewyposażony 3★ − gotowy 3★** | −0,26 | −0,15 | **−0,20 (59/360)** |

- Strefy (niewyposażony 3★ − gotowy 3★): wygrywa tylko lsm_czuby (+0,08, 19/36); zemborzyce −0,09, czechow
  −0,14, centrum −0,18 … zygmuntowskie −0,50.
- **Poprawka 8655353 nie pomaga w karcie:** na tych samych ziarnach (1000–1005) niewyposażony 1★ − baza
  z −0,067 (`b6_typy_po`, przed nią) do −0,124. Debetu i blokady inwestycji już nie ma, ale kredyt bez historii
  (11,9%, do 50 tys.) kosztuje odsetki i obniża wskaźnik zadłużenia, który mnoży kartę. Leasing (−0,06) wypada
  lepiej niż kredyt.
- Wniosek: przy obecnych liczbach niewyposażony nie ma szans – cały sprzęt naraz (1★ ok. 11 tys., 3★ ok. 31 tys.
  zł, pozycje < 10 tys. od razu w koszty) wobec oszczędności czynszu i mediów ok. 90–220 zł na rundę.
  Kompromis z inwentarza (niewyposażony wygrywa przy własnym lepszym sprzęcie) nie działa.

**Sprzęt lokalu niewyposażonego w leasingu (5.11):** zamiast kredytu bez historii bot bierze w leasing najdroższe
pozycje (bank z najtańszym leasingiem, 26 rund), aż po zakupach i opłatach wstępnych zostanie `rezerwa_po_sprzecie`;
kredyt bez historii tylko na resztę braku. Leasing nie wchodzi do zadłużenia karty (`finanse.zadluzenie`: kredyty,
debet, inwestor), więc nie obniża wskaźnika zadłużenia. Pomiar **`b6_niewyp3`** – ten sam układ i ziarna co
`b6_niewyp2` (baza praktycznie bez zmian: średnio −0,0005, różnice tylko przez rywali):

| wariant − baza | `b6_niewyp2` (kredyt) | `b6_niewyp3` (leasing) |
|---|---|---|
| niewyposażony w najmie | −0,12 (100/360) | −0,06 (139/360) |
| niewyposażony, sprzęt w leasingu (strategia) | −0,06 | −0,06 |
| gotowy, jakość 3★ | +0,06 | +0,06 |
| niewyposażony 3★ | −0,15 (99/360) | −0,03 (176/360) |
| **niewyposażony 3★ − gotowy 3★** | **−0,20 (59/360)** | **−0,09 (126/360)** |

- Strefy (niewyposażony 3★ − gotowy 3★): lsm_czuby +0,19 (21/36), zemborzyce +0,02 (25/36); czechow, stare_miasto
  −0,03, centrum −0,06; politechnika, felin, dworzec −0,12, akademickie −0,24, zygmuntowskie −0,37.
- Rachunek lokali (`dane/mapa/lokale.yaml`): niewyposażony ma już czynsz ok. 40% niższy od gotowego (0,75 vs 1,25
  stawki strefy), np. centrum 50 m²: ok. 550 zł oszczędności na rundę wobec adaptacji i sprzętu 1★ ok. 25 tys. zł –
  zwrot ok. 45 rund przy grze 18–26 rund; nawet zerowy czynsz nie zwraca tego w grze. Dalsza zmiana czynszu nic nie
  da – zostaje adaptacja albo odkup zestawu wynajmującego w ratach (decyzja autora, balans typów lokali).

**`b6_kupno2`** (kod 4d7cfb2; 6 stref peryferyjnych × 3 strategie × 18/26 rund × 6 ziaren, 864 gry, 2 procesy –
przy 3 procesach Claude Code zatrzymał pomiar przy braku pamięci; wznowiony od 51. gry), wariant − baza:

| strefa | kupno gotowego | kupno niewyposażonego | działka |
|---|---|---|---|
| czechow | +0,07 (32/36) | −0,05 (7/36) | −0,09 (10/36) |
| felin | +0,04 (26/36) | −0,13 (9/36) | −0,04 (18/36; 26 rund −0,02) |
| lsm_czuby | +0,06 (31/36) | −0,17 (1/36) | −0,14 (9/36) |
| politechnika | +0,08 (29/36) | −0,12 (5/36) | −0,12 (11/36) |
| zemborzyce | −0,31 (2/36) | −0,37 (10/36) | −0,67 (0/36, alarmy) |
| zygmuntowskie | −0,28 (12/36) | −0,34 (12/36) | −0,39 (10/36) |
| **razem** | **−0,06 (132/216)** | **−0,20 (44/216)** | **−0,24 (58/216)** |

- Kupno gotowego wygrywa w 4 strefach (72–89% par); przegrywa tam, gdzie lokal do kupna jest słaby albo drogi
  względem czynszu: w zemborzycach jedyny gotowy to budka nad Zalewem (tylko kupno, 1 kuchnia) – baza wynajmuje
  wtedy lokal w zygmuntowskich; w zygmuntowskich ten sam lokal (35 m², 1 kuchnia) za 77 tys. zł = 35 czynszów,
  a kredyt pod zastaw obniża wskaźnik zadłużenia karty (dług ≈ majątek → ok. 0,5–0,6).
- Działka (110–130 m², 5 kuchni, grunt 54–82 tys. + budowa 99–117 tys. zł) to całość na kredyt (np. zemborzyce:
  119,7 tys. pod zastaw + 41,3 tys. bez historii, rata ok. 1950 zł na rundę). Bot kupuje 1 kuchnię, popyt strefy nie
  wypełnia budynku – gotówka spada do zera w rundzie 9 i nie wraca (alarmy). W felin i politechnice (bez działki
  przy 6 firmach) bot bierze działkę z innej strefy. Liczby nie odbiegają od realiów w stronę drożyzny (budowa
  900 zł/m² to dolna granica, prawdziwy pawilon kosztuje kilka razy więcej) – działka jako pierwszy lokal to
  projekt na dłuższą grę; sprawdzam ją jako drugi lokal (`b6_drugi_po2`).

**`b6_drugi_po2`** (kod 95f7d5f; 5 strategii × 18/26 rund × 6 firm × 8 ziaren, 400 gier, 2 procesy), drugi lokal:

| wariant | − baza 18 r. | − baza 26 r. | − drugi gotowy w najmie |
|---|---|---|---|
| drugi gotowy w najmie | +0,07 (21/40) | **+0,22 (32/40)** | – |
| drugi gotowy na kupno | +0,06 | +0,19 | −0,02 (26/80) – w szumie |
| drugi niewyposażony | −0,14 | +0,06 | −0,19 (1/80) |
| drugi na działce | −0,12 | −0,06 | −0,24 (6/80) |

- Drugi lokal opłaca się dalej (H21), najem i kupno gotowego prawie równe – kupno to rozsądna alternatywa.
- Niewyposażony – ta sama przyczyna co przy pierwszym lokalu (sprzęt od razu w koszty, np. −17 tys. zł dochodu
  w rundzie zakupu); propozycja dla autora w `notatki_do_zmiany.md` (B6 – lokal niewyposażony).
- Działka: wszystkie 5 działek leży w strefach peryferyjnych (czechow, felin, lsm_czuby, zemborzyce,
  zygmuntowskie – popyt 7–12 tys. zł na tydzień wobec 14,5 tys. w centrum). Kupiona w rundzie ok. 10 działa od
  rundy 13–14, budynek na 5 kuchni z 1 kuchnią; np. zrównoważony, ziarno 1000, 26 rund: działka w zemborzycach
  (72 tys. + 99 tys. zł budowy na kredyt) daje dochód 8–10 tys. zł na rundę, drugi gotowy w centrum 10–16 tys.
  Liczby działki są już po stronie taniej (budowa 900 zł/m² – dolna granica realiów, 3–4 rundy budowy – szybciej
  niż w rzeczywistości; m² działki z budową ok. 1400–1600 zł wobec ok. 2200–2500 zł przy kupnie gotowego), więc nie
  stroję ich w dół. Działka zostaje opcją niszową: jako pierwszy lokal w 26 rundach jest w szumie od najmu
  (`b6_kupno2`: felin −0,02, czechow −0,09), jako drugi przegrywa przez strefę i późny start.

**`b6_przejecia`** (kod 655712d; 3 strategie × 18/26 rund × 6 firm × 6 ziaren, strefa wg strategii), wariant − baza:

| wariant | 18 rund | 26 rund | razem |
|---|---|---|---|
| wykup własnego lokalu | 0 | 0 | 0 (nigdy się nie zdarzył) |
| kupno budynku rywala | +0,01 | +0,04 | +0,03 (13/36; tani – nigdy) |
| kupno budynku rywala z wypowiedzeniem | +0,01 | +0,05 | +0,03 (13/36; zrównoważony 26 r. +0,11, 5/6) |
| przebicie w licytacji (oferta × 1,2) | −0,04 | −0,04 | −0,04 (2/36) |

- Wykup: lokale w centrum, na Starym Mieście, przy dworcu i akademikach są tylko w najmie (bez ceny), więc bot,
  który tam stoi, nie ma czego wykupić. Kupić da się 14 lokali w strefach peryferyjnych (cena ok. 35 czynszów
  gotowego, 40 niewyposażonego) – wykup sprawdzam osobno w tych strefach (`b6_wykup`).
- Przejęcie budynku rywala: mały zysk w długiej grze (czynsz od najemcy), z wypowiedzeniem trochę więcej –
  zgodnie z kompromisem z inwentarza („opłaca się w dłuższej grze, nie zawsze”); nie dominuje.
- Przebicie: boty rzadko biją się o ten sam lokal, więc wyższa oferta to zwykle wyższy czynsz bez zysku. To
  zamierzony kompromis (przepłacenie kontra utrata lokalu) – przebicie ma sens tylko w sporze, którego w tym
  pomiarze prawie nie ma. Bez zmian.

**Pomiar strefy – gdzie naprawdę stoi badana firma** (5.11): kontekst strefy (`--strefy`) zawęża lokale bota,
ale dotąd planujący bot (zrównoważony, premium: `min_kuchnia` 2) najpierw odrzucał lokale z 1 kuchnią, a dopiero
potem filtrował strefę – w zygmuntowskich (jedyny gotowy w najmie ma 1 kuchnię) brał lokal w innej strefie.
Teraz strefa idzie przed kuchnią (test `test_strefa_strategii_wazniejsza_niz_liczba_kuchni`). Zostają dwa
przypadki, w których pomiar strefy mierzy inną strefę (6 ziaren × 3 strategie, firma po 3 rundach):
- zemborzyce – nie ma tam lokalu w najmie (budka tylko na kupno, działka od 6 firm): 18/18 gier w innej strefie;
  wyniki „zemborzyce” w najmie to w praktyce dworzec, centrum, stare_miasto albo felin;
- zajęta strefa – w rundzie 1 rywal wygrywa ten sam lokal, a reszta strefy jest zajęta (np. tani w centrum: 2/6
  gier w czechowie, akademickie 3/18).
Pomiar zapisuje teraz w `gry.csv` kolumnę `strefy_lokali` (strefy lokali badanej na koniec gry) – tabela strefa ×
wariant liczy tylko gry, w których firma stoi w swojej strefie.

**Kontekst `dane` w pomiarze** (5.11): przewaga centrum i starego miasta to popyt, nie czynsz (szacunek tygodniowy
przy 5 rywalach: stare_miasto 14,9 tys. zł przychodu, centrum 14,5 … felin 8,3, zemborzyce 7,3). Żeby porównać
tabele stref przy innych liczbach popytu bez zmiany `dane/`, pomiar ma kontekst `--dane "ścieżka=wartość;…|…"`
(`dane_ze_zmianami` w `balans/warianty.py`, test `test_kontekst_ze_zmianami_danych_gry`) – zmiana dotyczy
wszystkich firm w grze. Szacunek przy `mapa.popyt.model.zasieg` 3 → 2: stare_miasto 13,1, centrum 11,1,
akademickie i dworzec 10,0, lsm_czuby 9,8 … zemborzyce 4,9 – centrum traci najwięcej, peryferie zostają w tyle
(odległości 4,5–18 na mapie, klient sięga dalej niż jedna dzielnica).

**Pomiar `b6_strefy`** (5.11; gry bazowe, 10 stref × 3 strategie × 18/26 rund × 6 ziaren, 6 firm, konteksty: dane
domyślne i `zasieg=2`; liczone tylko gry, w których badana stoi w swojej strefie – skrypt pomocniczy jak w
`strefy_lokali`). Średnia karta, kolejność stref (zrównoważony, 26 rund, dane domyślne): centrum 0,89,
stare_miasto 0,76, dworzec 0,71, akademickie 0,46, lsm_czuby 0,42, zygmuntowskie 0,35, czechów 0,34,
politechnika 0,32, felin 0,24. Tani: centrum 0,83 … felin 0,18; premium: centrum 0,90, stare_miasto 0,84 …
felin −0,05. **Centrum jest najlepsze (albo w szumie od najlepszego) we wszystkich 6 grupach** strategia × rund,
stare_miasto w 2; przy `zasieg=2` to samo (centrum 6, stare_miasto 4), wszystkie strefy niżej. Kompromis z
inwentarza („każda strefa najlepsza dla jakiejś strategii”) nie działa – dominacja.

Diagnoza (gra zrównoważonego, rundy 4–8, 2 ziarna, przychód / czynsz / dochód netto na tydzień): centrum
23,7 tys. / 1,2 tys. (5,0%) / 5,5 tys.; stare_miasto 22,5 / 1,7 (7,5%) / 5,4; dworzec 21,0 / 1,0 / 4,7;
lsm_czuby 15,5 / 0,6 (3,7%) / 2,6; politechnika 14,8 / 0,6 / 2,4; felin 12,0 / 0,45 / 2,1. Czynsz to 3–8%
przychodu (widełki planu 8–15%), a różnica zysku centrum – osiedla (~3 tys. zł/tydz.) jest kilka razy większa
niż cały czynsz centrum. Podniesienie stawki strefy do górnej granicy ofert Lublina (130 zł/m², `zrodlo` F3a.3)
daje +350 zł/tydz. – za mało. Źródło przewagi: popyt (`silnik/rynek/popyt.py: podzial` – udział lokalu =
a / (opcja_zewnetrzna + Σa); pula centrum 1,08, najbliżej wszystkich stref).

Poprawka (wzór, nie nowa decyzja): **`konkurencja` strefy** w `dane/mapa/popyt.yaml` (strefy), mnożnik opcji
zewnętrznej klientów tej strefy – lokale miasta spoza gry (w centrum i na Starym Mieście jest ich dużo, na
osiedlach mniej). `popyt.py: podzial` – `a0 × konkurencja strefy klienta`; bez klucza 1 (test
`test_konkurencja_strefy`). Na razie wszędzie 1,0 (bez zmiany gry). Szybka próba (2 ziarna, rundy 4–8, dochód
netto/tydz.): centrum i stare_miasto 1,6, dworzec 1,2, osiedla i peryferie 0,7–0,8 → centrum 5,2, stare_miasto
4,3, zemborzyce/dworzec 4,2–4,5, lsm_czuby 3,7, akademickie 3,5, zygmuntowskie 3,3, politechnika 2,7, felin 2,3
(różnica centrum – osiedla mniej więcej o połowę mniejsza); mocniej (centrum i stare_miasto 2,5, dworzec 1,8,
reszta 1) wyrównuje zysk, ale obniża całą gospodarkę (centrum 2,9) – psułoby cele B5. Pełny pomiar `b6_strefy2`
po `b6_wykup`.

**Pomiar `b6_strefy2`** (5.11; konteksty K1: centrum i stare_miasto 1,6, dworzec 1,2, reszta 0,7–0,8; K2: 2,0 /
1,4 / 0,6–0,7 – konkurencja jako mnożnik opcji zewnętrznej klientów strefy). Centrum dalej najlepsze w 6 z 6 grup
przy obu (zrównoważony 26r: centrum 0,89 → 0,83 / 0,77, felin 0,24 → 0,27 / 0,28). Przyczyna: lokal w centrum łapie
klientów sąsiednich stref, a mniejsza konkurencja na osiedlach obniżała opcję zewnętrzną także dla niego.
**Zmiana wzoru** (190cb3c): `konkurencja` dzieli atrakcyjność lokali gry stojących w strefie (`popyt.py:
_skladniki`) – lokal ginie wśród lokali miasta spoza gry, dla klientów wszystkich stref. Szybka próba (2 ziarna,
rundy 4–8, dochód netto/tydz., zrównoważony): K1 w nowym wzorze za mocne (peryferie przed centrum); K3 (centrum
1,25, stare_miasto 1,2, dworzec 1,1, akademickie 1, politechnika i zygmuntowskie 0,85, lsm_czuby i czechów 0,9,
felin 0,8, zemborzyce 0,85): centrum 5,5 → 4,4 tys., stare_miasto 5,4 → 4,2, politechnika 2,4 → 3,4, lsm_czuby
2,6 → 3,2, felin 2,1 → 2,5; średnia stref 3,87 → 3,67 tys. (−5%). Pełny pomiar `b6_strefy3` (K3 i mocniejsze K4:
1,4 / 1,35 / 1,15 / 1 / 0,8 / 0,85 / 0,75) – w toku; potem wybór wartości do `popyt.yaml`, szybki pomiar celów
B5 i `b6_kupno3` (peryferie, kontekst cen `lokale.*.cena*=1;1,5;2`).

**Pomiar `b6_strefy3`** (5.11; nowy wzór, K3 i K4, 720 gier). Strefa najlepsza albo w szumie od najlepszej
w 6 grupach strategia × rund: K3 – centrum 6 (dalej dominacja); **K4 – centrum 6, dworzec 4, lsm_czuby 3,
stare_miasto 2, czechów 1, politechnika 1**. Premium wygrywa w centrum, na dworcu i Starym Mieście, tani – na
lsm_czuby, w czechowie i na politechnice (np. tani 26r: centrum 0,63, lsm_czuby 0,60, czechów 0,60, politechnika
0,57; premium 26r: centrum 0,57, dworzec 0,53, stare_miasto 0,49, politechnika 0,42). Centrum nadal na czele
każdej grupy, ale w szumie (4–5 gier w strefie). Średnia karta gospodarki bez spadku (zrównoważony 26r 0,523 →
0,546, tani 18r 0,391 → 0,446, premium 18r 0,344 → 0,358). **K4 wpisane do `popyt.yaml`** (e624cd0); felin i
zygmuntowskie zostają najsłabsze (0,2–0,4) – mało klientów, a nie czynsz.

**Kontrola trudności `b6_trudnosc`** (6.11; jak K: słaby / średni / dobry × 5 strategii × ziarna 1000–1019,
18 rund, rywale średni, 300 gier):

| miara | K | po K4 | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 51/100 (w 3: 48) | **33/100 (w 3: 67)** | 4–6 |
| alarmy wersji słabej | 0/100 | 0/100 | 0 |
| dobra > średnia (pary) | 74/100 | **86/100** | ≥ 80% |
| słaba < średnia (pary) | 89/100 | 94/100 | – |
| karta słaba / średnia / dobra | 0,09 / 0,32 / 0,35 | 0,07 / 0,28 / 0,35 | – |

Dobra > średnia wróciła do celu (agresywny 13 → 18, naśladowca 15 → 18, premium 15 → 18). Pierwszy plus średniej
przyspieszył: w rundzie 3 zrównoważony 4 → 13 z 20, naśladowca 4 → 13 (tani i premium już wcześniej w 3).
To liczba B5 (rozruch nowego lokalu) – zmiana wymaga zgody autora; propozycja w `notatki_do_zmiany.md` po
próbie wariantu rozruchu (po `b6_kupno3`).

**Pomiar `b6_wykup`** (5.11; strefy peryferyjne z lokalami na kupno: czechów, felin, lsm_czuby, politechnika,
zygmuntowskie; 3 strategie × 18/26 rund × 6 ziaren, warianty `lokale:kupno`, `lokale:wykup`,
`lokale:przejecie_wypowiedz`, rezerwa bota 30 tys.). Wykup i przejęcie z wypowiedzeniem = baza: bot nigdy nie ma
ceny budynku + rezerwy w gotówce (mediana gotówki na koniec 42–100 tys., cena 110–200 tys.) – opcja jest w grze
dla graczy, ale nie dla bota. **Kupno dominuje najem**: +0,06 ± 0,01 karty, 86% wygranych par (premium 18r
+0,14 / 29 z 30, tani +0,06–0,07, zrównoważony −0,01…+0,01 – szum). Kompromis z inwentarza („kupno opłaca się
od połowy gry 18 rund”) nie działa – kupno wygrywa od początku.

Diagnoza: (1) **sprzęt liczony dwa razy** – przy kupnie gotowego lokalu (i wykupie, i przejęciu ze sprzętem
wynajmującego) lokal szedł do ewidencji za pełną cenę, a wartość sprzętu zestawu (11,5 tys. przy zestawie
podstawowym, 10–19% ceny) dodatkowo do majątku firmy – bez wydatku i bez kosztu; zawyżało to rozwój firmy.
Poprawione (1e69d61): cena dzieli się na lokal (cena − sprzęt) i sprzęt (od progu amortyzacji środek trwały,
poniżej – koszt w KPiR od razu, bez wydatku); zastaw kupowanego lokalu liczony tak samo jak ewidencja.
(2) Kupno jest tanie w utrzymaniu: odsetki (7,9%) + amortyzacja lokalu (2,5% rocznie) ≈ 150 zł/tydz. przy
czynszu ≈ 650 zł/tydz. (cena ≈ 35–40 czynszów miesięcznych). Po poprawce (1) – ponowny pomiar `b6_kupno3`
(peryferie, `lokale:kupno`); jeśli kupno dalej wygrywa od początku 18 rund, kolejny krok to cena lokalu
(liczba czynszów w cenie, F3a.3) albo koszty posiadania (podatek od nieruchomości – nowa pozycja, do zgody
autora).

**Pomiar `b6_kupno3`** (6.11; po poprawce sprzętu, peryferie jak `b6_wykup`, `lokale:kupno`, konteksty cen
`lokale.*.cena*=1 / 1,5 / 2`, 1080 gier). Karta (różnica kupno − najem, wygrane pary) i majątek netto:

| cena | karta | zrównoważony 18r / 26r | tani 18r / 26r | premium 18r / 26r |
|---|---|---|---|---|
| ×1 | +0,029, 135/180 | maj. −1,4 / +0,2 tys. | maj. +4,9 / +6,4 tys. (28/30) | maj. +3,6 / +5,6 tys. |
| ×1,5 | +0,002, 107/180 | maj. −5,8 / −5,3 tys. (7–9/30) | maj. +2,6 / +2,8 tys. (25–27/30) | maj. +0,3 / +2,5 tys. |
| ×2 | −0,006, 102/180 | maj. −10,6 / −11,3 tys. | maj. +0,8 / +0,6 tys. | maj. −0,9 / +3,4 tys. |

Rozbicie (skrypty w scratchpadzie: składniki karty, KPiR, decyzje bota w parze): (1) zrównoważony po kupnie na
kredyt ma 1–3 tys. gotówki zamiast 30 tys. i przez całą grę nie kupuje ulotek, promocji, udogodnień ani
wyposażenia – przychód z tego samego lokalu −11% (czechów ×2: 289 vs 324 tys.). To zamierzone ryzyko kupna
(zamrożona gotówka). (2) Tani nie wydaje na marketing, więc nic nie traci, a zyskuje brak czynszu. (3) **Rozwój
firmy w karcie**: najemca bez własnego sprzętu ma rozwój = stała 0,535, kupiony lokal za 77 tys. podnosi go do 0,764
(+43%), więc kupno wygrywa kartą w zygmuntowskim w 34–36/36 par przy każdej cenie (droższy lokal = wyższy rozwój).
Stosunek cena/czynsz jest równy w strefach (35–41), więc to nie dane lokali.

Decyzja: **cena kupna ×1,5** (≈ 60 czynszów; f4335c5; 15 lokali, działki bez zmian): każda forma ma swoją sytuację
– tani zyskuje na kupnie, zrównoważony traci (marketing), premium wychodzi na zero w 18 rundach i na plus w 26
(kompromis z inwentarza). Przy ×2 kupno nie wygrywa majątkiem w żadnej grupie. Efekt rozwoju firmy to wzór Z1 –
propozycja (waga nieruchomości w rozwoju) w `notatki_do_zmiany.md`. Kontrola stref centralnych: `b6_kupno4`.

**Pomiar `b6_kupno4`** (6.11; ceny ×1,5, strefy centrum, stare_miasto, dworzec, akademickie, zemborzyce; 360 gier).
W strefach centralnych nie ma lokali na sprzedaż (cena tylko na peryferiach), więc bot z kupnem kupuje w czechowie,
na politechnice, w zygmuntowskim itd., a baza wynajmuje w swojej strefie: to para „najem w centrum” kontra „kupno
na peryferiach”. Najem w centrum wygrywa: karta −0,16 ± 0,03 dla kupna (47/180 par), majątek −26 tys. (centrum
−0,21, stare_miasto −0,12, dworzec −0,13, akademickie −0,10). Zemborzyce (tylko budka na kupno, najem w innej
strefie): kupno −0,23 (5/36). Kompromis lokali po B6: centrum – najem i duży ruch, peryferie – własność albo tani
najem; kupno wygrywa tylko dla strategii bez wydatków na marketing (tani) i to w strefie, w której kupuje.

**Próba rozruchu `b6_rozruch`** (6.11; jak `b6_trudnosc`, konteksty `mapa.popyt.model.rozruch.start` 0,3 i 0,25,
600 gier). Liczba B5 – tylko pomiar, zmiana za zgodą autora:

| start | plus średniej w 4–6 | alarmy słabej | dobra > średnia | karta S / Ś / D | majątek Ś |
|---|---|---|---|---|---|
| 0,4 (dziś, `b6_trudnosc`) | 33/100 (reszta w 3) | 0 | 86 | 0,07 / 0,28 / 0,35 | 96 tys. |
| 0,3 | 42/100 | 2 | 81 | 0,04 / 0,23 / 0,30 | 90 tys. |
| 0,25 | 61/100 | 1 | 81 | 0,03 / 0,20 / 0,27 | 87 tys. |

Niższy start opóźnia pierwszy plus, ale daje pojedyncze alarmy (premium i agresywny na słabym, 1–2 na 100) i
obniża wszystkie karty. Następna próba: start 0,4 i wolniejszy przyrost (0,07 / 0,05) – mniejsza strata w
pierwszych tygodniach.

**Próba `b6_rozruch2`** (6.11; start 0,4, `mapa.popyt.model.rozruch.przyrost` 0,07 i 0,05, 600 gier):

| przyrost | plus średniej w 4–6 | alarmy słabej | dobra > średnia | karta S / Ś / D | majątek Ś |
|---|---|---|---|---|---|
| 0,1 (dziś) | 33/100 | 0 | 86 | 0,07 / 0,28 / 0,35 | 96 tys. |
| 0,07 | 38/100 | 0 | 85 | 0,06 / 0,25 / 0,32 | 92 tys. |
| 0,05 | 43/100 | 1 | 85 | 0,06 / 0,21 / 0,28 | 87 tys. |

Wolniejszy przyrost działa słabiej niż niższy start, a też obniża karty. Cel B5 (ok. połowa w 4–6, jak 51/100 w K)
osiąga tylko start 0,25 (61/100, 1 alarm na 100). Propozycja dla autora w `notatki_do_zmiany.md` (B6 – rozruch).

**Następne kroki:**
1. ~~Bot: zamiast kredytu bez historii na sprzęt – leasing~~ (zrobione 5.11, `b6_niewyp3`).
2. ~~Propozycja dla autora~~ – zapisana 5.11 w `notatki_do_zmiany.md` (B6 – lokal niewyposażony; rekomendacja:
   wybór amortyzacji sprzętu poniżej progu); czeka na decyzję autora.
3. ~~Pomiary `b6_kupno2`, `b6_drugi_po2`, `b6_przejecia`~~ (zrobione 5.11); w toku `b6_strefy` (tabela stref,
   konteksty: dane domyślne i `mapa.popyt.model.zasieg=2`), potem `b6_wykup` (strefy z lokalami na kupno);
   2 procesy, jeden pomiar naraz (przy 3 procesach zabrakło pamięci).
4. Potem: tabela strefa × wariant (każda strefa najlepsza dla jakiejś strategii), kupno od połowy gry 18 rund,
   działka tylko w 26 rundach, licytacja, inwentarz (opis botów w sekcji `lokal`), odhaczenie B6 w POSTEP.

## B7 – menu i ceny (6.11.2026, Claude Code, Opus 5.5) – zakończone 6.11, gałąź `kalibracja-b6`

**Pomiar `b7_cena`** (warianty `cena` 0,85/1,0/1,15/1,3, `jakosc` 1/2/3, `menu` 3/5/8; zrównoważony, tani,
premium; 18 i 26 rund, 6 firm, 6 ziaren, 792 gry). Różnica karty wariant − baza (średnio 18 i 26 rund, wygrane
pary z 12; w nawiasie majątek netto 18r). Baza strategii: zrównoważony cena 0,92 / 2★ / 6 dań, tani 0,78 / 1★ /
8 dań, premium 1,08 / 3★ / 5 dań.

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| cena 0,85 | −0,00, 5/12 (−2 tys.) | +0,04, 10/12 (+7 tys.) | −0,24, 0/12 (−27 tys.) |
| cena 1,0 | −0,05, 1/12 (−5 tys.) | +0,12, 9/12 (+20 tys.) | −0,06, 0/12 (−7 tys.) |
| cena 1,15 | −0,12, 0/12 (−13 tys.) | +0,16, 11/12 (+27 tys.) | +0,02, 4/12 (0) |
| cena 1,3 | −0,17, 0/12 (−18 tys.) | +0,11, 6/12 (+22 tys.) | +0,06 ± 0,07, 9/12 (−2 tys.) |
| jakość 1★ | −0,01, 6/12 | baza | −0,18, 0/12 (−30 tys.) |
| jakość 2★ | baza | −0,03, 2/12 | −0,21, 0/12 (−33 tys.) |
| jakość 3★ | **+0,25, 12/12** (+27 tys.) | −0,04, 6/12 | baza |
| menu 3 | −0,42, 0/12 | −0,25, 0/12 | −0,37, 0/12 |
| menu 5 | −0,18, 0/12 | −0,07, 6/12 | baza |
| menu 8 | **+0,20, 12/12** (+26 tys.) | baza | **+0,74, 12/12** (+61 tys.) |

Wyniki 26 rund są takie same co do znaku (różnice nieco większe). Alarmów brak, pierwszy plus bez zmian.

Diagnoza (pary rozpisane skryptami w scratchpadzie, ziarno 1000):
1. **Cena – zrównoważony i premium bez dominacji.** Zrównoważony ma optimum przy swojej cenie (0,85–0,92),
   premium przy 1,15–1,3, ale bez istotnej różnicy (+0,06 ± 0,07). H18 (premium ×1,2 wyraźnie lepsze) po B6
   (konkurencja stref) już nie zachodzi.
2. **Cena – tani gra za tanio, bo ma za małą kuchnię.** Tani (`min_kuchnia: 1`, 2 osoby) traci 45% popytu w
   kolejce (12,1 z 27,0 tys. klientów: „pracownicy/sprzęt”). Bot nie zatrudnia trzeciej osoby, bo przy cenie 0,78
   dodatkowa sprzedaż × marża porcji nie pokrywa pensji (`silnik/boty.py: _plan_lokalu`). Przy cenie 1,15
   przychód +30%, towary −13%, dochód 108 vs 42 tys. To zamierzony kompromis („przy zatkanej kuchni podwyżka ma się
   opłacać”), a nie błąd modelu popytu. Do sprawdzenia: tani z `min_kuchnia: 2`.
3. **Jakość – 3★ dominuje 2★, a 2★ nie różni się od 1★.** Mnożnik jakości w atrakcyjności
   (`zalozenia.yaml: popyt.wspolczynniki_jakosci`) to 1★ 0,616, 2★ 0,654, 3★ 1,0: krok 2→3★ daje +53%
   atrakcyjności, krok 1→2★ tylko +6%. Składniki 3★ są droższe o ok. 18% (mięso 330 → 390 zł), więc zrównoważony
   z 3★: przychód +26%, towary +48%, dochód 119 vs 94 tys. Środkowa jakość nie ma sensu: albo 1★ (tani), albo 3★.
   Wpływ jakości na opinie (`mapa/klienci.yaml: opinie.jakosc` 0,3 gwiazdki za gwiazdkę ponad 2) jest mały obok
   tego mnożnika. Następna próba: łagodniejsza krzywa (2★ wyżej, 3★ niżej), pomiar `b7_jakosc`.
4. **Menu – pełne menu (8 dań) dominuje.** Każde danie ma własną pulę klientów (`uslugi.yaml: popyt_roczny`), a
   klient dania, którego lokal nie ma w menu, nie wybiera innego dania w tym lokalu, tylko inny lokal albo
   „obiad w domu”. Nowe dania nie wymagają nowego sprzętu (rożen i frytownica już są), więc szersze menu to
   prawie same nowe pule: premium 5 → 8 dań – przychód +48%, koszty +31%, jedna osoba więcej, dochód 144 vs
   58 tys. Kompromis z inwentarza („więcej składników, psucie, czas kuchni”) prawie nie działa. Liczby w danych go
   nie odtworzą bez sztucznych kosztów, potrzebna mechanika (zastępowalność dań albo koszt stały dania) –
   propozycja dla autora w `notatki_do_zmiany.md`. Ranking dań bota (`silnik/boty.py: _ranking_uslug`, przychód na
   godzinę kucharza) daje premium frytki, napój i dodatek zamiast talerza i boxa.

**Próba `b7_jakosc`** (6.11; konteksty dla wszystkich firm: krzywa A – mnożniki jakości 1★/2★/3★ 0,616 / 0,75 /
0,95, krzywa C – 0,6 / 0,72 / 0,9, oraz tani z `boty.strategie.tani.min_kuchnia: 2`; 18 rund, 6 ziaren, 378 gier).
Karta wariant − baza, wygrane pary z 6:

| kontekst | zrównoważony 1★ / 3★ | premium 1★ / 2★ | tani 2★ / 3★ | tani cena 1,0 / 1,15 / 1,3 |
|---|---|---|---|---|
| dziś (`b7_cena`, 18r) | −0,00 / **+0,23 (6/6)** | −0,18 / −0,19 | −0,03 / −0,04 | +0,12 / +0,16 / +0,11 |
| A 0,616 / 0,75 / 0,95 | −0,17 (0/6) / +0,05 ± 0,04 (4/6) | −0,18 / −0,05 (3/6) | +0,03 / −0,03 | +0,11 / +0,17 / +0,10 |
| C 0,6 / 0,72 / 0,9 | −0,15 (0/6) / +0,01 ± 0,02 (4/6) | −0,16 / −0,05 (2/6) | +0,02 / −0,04 | +0,10 / +0,16 / +0,09 |
| tani `min_kuchnia: 2` | (bez zmian krzywej) | | −0,05 / −0,07 | **−0,06 / −0,09 / −0,15** |

Obie krzywe usuwają dominację 3★: zrównoważony ma 2★ i 3★ prawie równe, 1★ wyraźnie gorsze, premium dalej
woli 3★ (−0,05 przy 2★), tani – 1★ albo 2★. Karta bazowa zrównoważonego rośnie jednak 0,57 → 0,67–0,70, bo
2★ dostaje +10–15% popytu (wszystkie firmy z 2★). Pule stref B5 kalibrowano na lokalu 2★, więc do wdrożenia
wybieram krzywą o tych samych proporcjach co C, ale z 2★ bez zmian: **1★ 0,55, 2★ 0,654, 3★ 0,82** (2★/1★ = 1,19,
3★/2★ = 1,25; dziś 1,06 i 1,53).

Tani z dwoma miejscami w kuchni ma kartę bazową 0,54 zamiast 0,29 (majątek 117 vs 84 tys.), a podwyżka ceny
przestaje się opłacać (1,3: −0,15, 0/6). Z jednym miejscem tani bot nie da się prowadzić jako „tani”, bo kolejka
zjada mu połowę popytu. `min_kuchnia: 2` u taniego (dane botów, nie zasady gry) – razem z krzywą w `b7_jakosc2`.

**Pomiar `b7_promocje`** (6.11; `promocje:brak` i `promocja:<typ>` – jedna promocja przez całą grę od rundy 2,
18 rund, 6 ziaren, 126 gier). Karta wariant − baza (baza strategii: zrównoważony – zestaw, tani – happy hours i
studencka, premium – karta stałego klienta), wygrane z 6:

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| bez promocji | −0,01 (1/6) | +0,02 (4/6) | **+0,13 (6/6)** |
| 2 za 1 | −0,09 (0/6) | +0,00 | −0,27 (0/6) |
| zestaw | baza | +0,02 | +0,19 (6/6) |
| happy hours | −0,07 (0/6) | +0,00 | −0,01 |
| karta stałego klienta | −0,07 (0/6) | +0,00 | baza |
| studencka | −0,02 (0/6) | +0,02 | +0,13 (6/6) |

Żadna promocja z rabatem nie wygrywa z brakiem promocji, a zestaw (dopłata zamiast rabatu) wychodzi na zero. Tani
wyłącza promocje, bo nie obsługuje całego popytu (`min_obsluga_promocji`), stąd zera. Diagnoza
(`silnik/rynek/popyt.py: podzial`, `silnik/rynek/promocje.py`): rabat promocji nie wchodzi do ceny w atrakcyjności,
klientów przyciąga tylko `przyciaganie` z `mapa/promocje.yaml`. Obniżka ceny o r daje w modelu popytu
atrakcyjność × exp(2 · wrażliwość · r): −10% → +22%, −15% → +35%, −20% → +49%. Promocje mają mniej: karta (−10% na
całe menu) +5% → +22% po 6 tygodniach, happy hours (−20% pn–czw) +35% → +20%, studencka (−15%, studenci o
wrażliwości 1,3–1,4) +40% (obniżka ceny dałaby ok. +50%). Promocja jest więc zawsze gorsza od zwykłej obniżki
ceny, a ta przy cenach botów jest na granicy opłacalności. 2 za 1 daje dwie porcje za cenę jednej (marża porcji
spada z ok. 0,7 do 0,4 ceny), a bot trzyma promocję całą grę, choć jej przyciąganie spada z 0,5 do 0,2.

Próba (`b7_promocje2`): przyciąganie co najmniej jak obniżka ceny o rabat, plus mały efekt promocji – happy hours
0,6 → 0,4 (−0,04 na tydzień), karta 0,05 → 0,3 (+0,04), studencka 0,55, 2 za 1 0,8 → 0,2 (−0,12); zestaw bez
zmian. Wtedy promocja ma się opłacać przy wolnej kuchni (słabe dni, strefy studenckie), a przy pełnej nie.

**Pomiar `b7_jakosc2` i wdrożenie** (6.11; krzywa 1★ 0,55 / 2★ 0,654 / 3★ 0,82 i tani z `min_kuchnia: 2`,
18 i 26 rund, 6 ziaren, 288 gier). Karta wariant − baza, wygrane z 6, 18r (26r w nawiasie):

| wariant | zrównoważony (2★, 0,92) | tani (1★, 0,78) | premium (3★, 1,08) |
|---|---|---|---|
| jakość 1★ | −0,13 0/6 (−0,14) | baza | −0,11 1/6 (−0,14) |
| jakość 2★ | baza | +0,05 6/6 (+0,06) | −0,03 1/6 (−0,03) |
| jakość 3★ | +0,05 5/6 (+0,07) | −0,02 2/6 (+0,02) | baza |
| cena 0,85 | −0,02 (−0,02) | +0,01 (+0,00) | −0,16 (−0,19) |
| cena 1,0 | −0,04 (−0,04) | −0,05 (−0,05) | −0,04 (−0,05) |
| cena 1,15 | −0,12 (−0,13) | −0,05 (−0,05) | +0,01 (+0,02) |
| cena 1,3 | −0,18 (−0,18) | −0,14 (−0,15) | +0,02 (+0,03) |

Przed (b7_cena, stara krzywa): zrównoważony 3★ +0,25 (12/12), 1★ ≈ 2★. Teraz każdy krok jakości coś daje, ale
3★ już nie dominuje (+0,05, dopiero w dłuższej grze +0,07), a ceny mają optimum przy cenach strategii (tani
0,78–0,85, zrównoważony 0,85–0,92, premium 1,08–1,3 – płasko). Tani na 2★ zyskuje +0,05 (6/6): przy większej
kuchni nie musi już oszczędzać na jakości – zostawiam 1★ jako charakter strategii (różnorodność rywali), do
decyzji przy B8 (boty). Karta bazowa 18r: zrównoważony 0,57 → 0,63, tani 0,29 → 0,44, premium 0,40 → 0,26 (niższy
mnożnik 3★; premium ma też tylko 5 dań – zob. `notatki_do_zmiany.md`, „szerokie menu”). Wdrożone:
`zalozenia.yaml: popyt.wspolczynniki_jakosci` (1★ 0,616 → 0,55, 3★ 1,0 → 0,82, 2★ bez zmian – pule B5) i
`boty.yaml: tani.min_kuchnia` 1 → 2. Testy bez zmian (380 zielonych – żaden nie liczył na krzywej jakości).
Sprawdzenie trudności B5 po zmianie – pomiar `b7_trudnosc`.

**Próba `b7_promocje2`** (6.11; mocniejsze przyciąganie – happy hours 0,6 → 0,4, karta do 0,3, studencka 0,55,
2 za 1 0,8 → 0,2; gry na starej krzywej jakości – pule procesów wczytały dane przed jej wdrożeniem, więc wynik
porównywalny z `b7_promocje`). Karta wariant − baza, 18r, 6 ziaren:

| wariant | zrównoważony (przed → po) | premium (przed → po) |
|---|---|---|
| bez promocji | −0,01 → −0,01 | +0,13 → +0,14 |
| 2 za 1 | −0,09 → −0,11 | −0,27 → −0,25 |
| happy hours | −0,07 → −0,08 | −0,01 → −0,01 |
| karta stałego klienta | −0,07 → −0,08 | baza |
| studencka | −0,02 → −0,03 | +0,13 → +0,14 |

Mocniejsze przyciąganie nic nie daje, a u zrównoważonego nawet szkodzi. Rozbicie jednej gry (`para.py`,
zrównoważony, ziarno 1000, 18r): z happy hours przychód spada o 12,8 tys. zł, towary o 2 tys. zł, ludzie bez
zmian (3 osoby), a utracona sprzedaż rośnie z 2,4 do 3,0 tys. sztuk. Karta stałego klienta: przychód −11,6 tys.
zł, sprzedaż bez zmian. Dodatkowi klienci promocji trafiają do kolejki, bo kuchnia bota jest pełna, a rabat
dostają wszyscy objęci, także ci, którzy przyszliby i tak. Do tego bot ustala cenę blisko optimum (`b7_jakosc2`
– wszystkie odchylenia ceny tracą), więc obniżka ceny przez promocję z zasady nie może wygrać. W modelu promocja
nie ma trwałego skutku (nowi klienci nie wracają po jej końcu) – bez tego różni się od obniżki ceny tylko maską
dni i stref. Liczby promocji bez zmian; propozycja dla autora w `notatki_do_zmiany.md` („B7 – promocje bez
trwałego skutku”), sprawdzenie w B10 (marketing) razem z reklamą.

**Kontrola trudności `b7_trudnosc`** (6.11; po krzywej jakości i kuchni taniego, jak `b6_trudnosc`, 300 gier):

| miara | `b6_trudnosc` | `b7_trudnosc` | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 33/100 (w 3: 67) | 37/100 (w 3: 63) | 4–6 |
| alarmy wersji słabej | 0/100 | 0/100 | 0 |
| dobra > średnia (pary) | 86/100 | 87/100 | ≥ 80% |
| słaba < średnia (pary) | 94/100 | 86/100 | – |
| karta słaba / średnia / dobra | 0,07 / 0,28 / 0,35 | 0,06 / 0,29 / 0,36 | – |

Bez regresji; dobra > średnia w każdej strategii 16–18/20. Słaba < średnia spadła (94 → 86) – słaba częściej
dorównuje średniej, cel B5 jej nie dotyczy. Wczesny plus średniej dalej za wcześnie (propozycja rozruchu czeka).

**B7 zamknięte** (6.11): wdrożona krzywa jakości i kuchnia taniego; otwarte decyzje autora – szerokie menu bez
kosztu i promocje bez trwałego skutku (`notatki_do_zmiany.md`), promocje wracają w B10.

## B8 – zaopatrzenie

**Krok 0 – boty.** Boty dostały ustawienia strategii (`silnik/schematy.py: Strategia`): `jakosc_zasobow`
(gwiazdki składników niezależnie od jakości strategii), `zapas_zasobow`, `dostawcy` (lista dozwolonych) i
`dyskonty` (e8b093a). Wcześniej bot w grze z lokalami w ogóle pomijał dyskonty (odbiór osobisty, limit opakowań),
więc H16 nie dało się zmierzyć. Z `dyskonty` bot wybiera jeden dyskont, który w rundzie najwięcej oszczędza
(ceny z gazetką), i kupuje tam dzień po dniu, najwyżej do limitu opakowań, składniki tańsze niż z dowozem
(`silnik/kuchnia/planowanie.py: _z_dyskontu`). Odbiór kosztuje czas właściciela (`dostawcy.py: zasady_dostaw`).

**Pomiar `b8_zaopatrzenie`** (6.11; 18r, 6 firm, 6 ziaren; karta wariant − baza, wygrane pary):

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| zapas 1,0 (baza 1,05) | −0,04 (0/6) | −0,02 | +0,01 |
| zapas 1,15 | **+0,07 (6/6)** | **+0,04 (6/6)** | +0,01 |
| zapas 1,3 | **+0,08 (6/6)** | +0,03 (5/6) | +0,01 |
| zapas 1,5 | +0,02 | −0,01 | −0,09 |
| zapas 2,0 | −0,21 (0/6) | −0,15 (0/6) | −0,23 (0/6) |
| składniki 1★ | +0,03 (5/6) | baza | −0,04 |
| składniki 2★ | baza | −0,03 | −0,02 |
| składniki 3★ | −0,08 (0/6) | −0,14 (0/6) | baza |
| bez piekarni | −0,13 (0/6) | −0,08 (0/6) | −0,12 (0/6) |
| bez producenta | −0,01 | 0,00 | −0,02 |
| tylko Makro / Selgros / Eurocash | −0,25 / −0,28 / −0,01 | −0,12 / −0,13 / −0,05 | −0,18 / −0,15 / −0,02 |
| dyskont | **+0,06 (6/6)** | +0,03 (5/6) | +0,02 (4/6) |

Diagnoza:
- **Zapas.** Kompromis działa w samej grze: za mały zapas to braki (zrównoważony, ziarno 1000: przy 1,3
  przychód +29,6 tys. zł, towary +16 tys. zł – przy 1,05 bot tracił ok. 9% sprzedaży), za duży (2,0) to
  przeterminowanie. Optimum 1,15–1,3 dla wszystkich strategii. Zły był tylko domyślny zapas botów –
  `boty.yaml: zapas_zasobow` 1,05 → 1,2 (c3f3665; ustawienie botów, nie liczba gry).
- **Dostawcy.** Piekarnia (codzienne dostawy pieczywa) jest potrzebna każdemu; jedna hurtownia bez piekarni i
  producenta przegrywa – rzadkie dostawy to braki albo psucie (Eurocash dowozi 3 razy w tygodniu, dlatego traci
  mało). Producent daje mało (mięso 307 zamiast ok. 350 zł, ale minimum 800 zł i 2 dostawy w tygodniu) –
  zgodnie z kompromisem.
- **Dyskont (H16).** Zysk ma dwa źródła (zrównoważony, ziarno 1000): przychód +6,1 tys. zł (codzienne dokupki
  łatają braki przy zapasie 1,05) i koszty −4 tys. zł (towary −2,7 tys., brak opłat za dowóz −1,4 tys.).
  Oszczędność ok. 4% towarów ogranicza limit 4 opakowań; kosztem jest czas właściciela (1,5 h dziennie z 20 h
  w tygodniu). Ponowny pomiar przy nowym zapasie botów pokaże, ile zostaje.
- **Składniki.** Premium najlepiej na 3★, tani na 1★, ale zrównoważony (2★) też woli 1★: przychód −1%,
  towary −7,5% (ziarno 1000). Składniki 2★ nie wygrywają w żadnej strategii. Kuchnia zrównoważonego jest
  pełna (kolejka), więc słabsza atrakcyjność prawie nie zmniejsza sprzedaży – jak przy promocjach w B7.

**Ponowny pomiar `b8_po`** (zapas botów 1,2; 18r, 6 firm, 6 ziaren; karta wariant − baza):

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| zapas 1,0 / 1,15 / 1,3 / 1,5 / 2,0 | −0,11 / −0,02 / −0,01 / −0,05 / −0,28 | −0,07 / −0,01 / −0,01 / −0,05 / −0,19 | −0,05 / −0,01 / −0,02 / −0,10 / −0,25 |
| składniki 1★ / 2★ / 3★ | −0,01 (2/6) / baza / −0,06 (0/6) | baza / −0,01 / −0,10 (0/6) | −0,06 (1/6) / −0,06 (1/6) / baza |
| bez producenta | −0,03 (1/6) | 0,00 | −0,03 (0/6) |
| dyskont | +0,05 (6/6) | +0,03 (6/6) | +0,03 (3/6) |

- Zapas 1,2 jest optimum dla wszystkich strategii, a odchylenia w obie strony kosztują.
- Każda strategia wygrywa na składnikach swojej jakości: u zrównoważonego 2★ bije 1★ (4/6). Wcześniejsza
  przewaga 1★ wynikała z braków przy zapasie 1,05 – kuchnia z pustym magazynem i tak nie sprzedawała więcej.
  Krzywej jakości ani cen składników nie zmieniam.
- Dyskont: przy pełnym zapasie zostaje sama oszczędność (zrównoważony, ziarno 1000: towary −3,9 tys. zł,
  opłaty za dowóz −1,1 tys. zł, przychód bez zmian; dochód +3,4 tys. zł w 18 rundach). To ok. 190 zł tygodniowo
  za ok. 10 h czasu właściciela, czyli ok. 18 zł/h – mniej niż godzina płacy minimalnej (4806 zł / 168 h ≈ 29 zł).
  H16 („dyskont dominuje zakupy małej firmy”) potwierdza się tylko w słabej formie: dyskont się opłaca, gdy
  właściciel nie ma lepszego zajęcia (dziś boty nie używają czasu właściciela na nic innego). Kompromis
  „tanio przy małej skali kontra czas i limit opakowań” działa, liczby dyskontów bez zmian. Wrócić do tego w B9
  (ludzie i czas właściciela), gdy czas zyska inne zastosowania.
- Hurtownia przy 1 lokalu (druga część H16): tylko-hurtownia przegrywa, ale przez rzadkie dostawy, a w zestawie
  z piekarnią i producentem hurtownie są podstawą zakupów botów – „nie zwraca się nigdy” się nie potwierdza.

**Kontrola trudności `b8_trudnosc`** (6.11; po zapasie botów 1,2; jak `b7_trudnosc`, 300 gier): pierwszy plus
średniej w rundach 4–6 43/100 (było 37), dobra > średnia 90/100 (87), słaba < średnia 89/100 (86), karta
0,05 / 0,29 / 0,37 – ale **1 alarm** wersji słabej (agresywny, ziarno 1013: bankructwo od rundy 12; przy zapasie
1,05 ta sama gra kończy się bez alarmu z 14,7 tys. zł). Przyczyna: proste planowanie (`czlowiek_slaby`, `latwy`)
zamawia na prognozę popytu z zeszłego tygodnia, a po odejściu kucharza (runda 7) zamówienia skaczą co tydzień
między ok. 2 a 14 tys. zł przy przychodzie ok. 11 tys. zł – zapas 1,2 powiększa to, co się psuje. Zapas
bezpieczeństwa to umiejętność lepszego planowania, więc poziomy z prostym planowaniem zostają przy 1,05
(nowe ustawienie poziomu `zapas_zasobow`, `boty.yaml`). Ponowny pomiar wersji słabej (`b8_trudnosc2`, gry
średniej i dobrej przeniesione z `b8_trudnosc` – zmiana ich nie dotyczy):

| miara | `b7_trudnosc` | `b8_trudnosc2` | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 37/100 (w 3: 63) | 43/100 (w 3: 57) | 4–6 |
| alarmy wersji słabej | 0/100 | 0/100 | 0 |
| dobra > średnia (pary) | 87/100 | 90/100 | ≥ 80% |
| słaba < średnia (pary) | 86/100 | 89/100 | – |
| karta słaba / średnia / dobra | 0,06 / 0,29 / 0,36 | 0,06 / 0,29 / 0,37 | – |

Bez regresji, cele B5 nieco bliżej (lepsze zaopatrzenie średniej przesuwa jej pierwszy plus z rundy 3 na 4).

**Auto-dostawy (Z4)** – wariant `dostawcy:auto` w `b8_po` (lokal główny na auto-dostawach; bot zamawia tygodniową
ilość × zapas bez towaru, który już ma): zrównoważony −0,004 (3/6), premium −0,03 (2/6), tani −0,07 (0/6).
Rozbicie (zrównoważony, ziarno 1000): przychód +30,4 tys. zł (+9% – bez braków i psucia przy rzadkich dostawach
hurtowni), towary +26,7 tys. zł (+24%: Auchan, prowizja 10%), pozostałe +7,8 tys. zł (abonament, przechowanie);
dochód netto −4,2 tys. zł. Kompromis „wygoda i pewność dostaw kontra cena” działa: dobrze prowadzone własne
zakupy wygrywają lekko, a tani (niska marża) traci wyraźnie. Uczeń, który zamawia gorzej niż bot, na
auto-dostawach może zyskać – po to są. Liczby bez zmian.

**Poza pomiarem:** handel towarem między drużynami (`handel_*`) – boty nie handlują, to wymiana między
graczami, do sprawdzenia w grze testowej; mrożonki jako zapas na braki (`zamiennik_dla`) – boty ich nie
kupują, a przy zapasie 1,2 braki są małe, więc zysk byłby niewielki.

**B8 zamknięte** (6.11): wdrożone zapas zamówień botów 1,2 (poziomy z prostym planowaniem 1,05); boty umieją
dyskonty, auto-dostawy, wybór gwiazdek składników i dostawców. Liczby gry bez zmian – dominacji nie ma: każda
strategia wygrywa na składnikach swojej jakości, zapas ma optimum, dyskont daje mniej niż godzina płacy
minimalnej za czas właściciela (do sprawdzenia w B9), auto-dostawy są droższe od dobrych własnych zakupów.

## B9 – ludzie (6.11.2026, gałąź `kalibracja-b6`)

**P1 (decyzja autora 29.10.2026, f8484fd):** umowa zlecenie płaci składki ZUS pracodawcy 20,48% jak umowa o pracę
(`podatki_2026.yaml: zus_pracodawcy_zlecenie`, art. 6 ust. 1 pkt 4 ustawy o s.u.s.; studentów w grze nie ma).
Panel pokazuje stawkę zlecenia w HR, Lokalu i Podatkach (wcześniej panel liczył 19% z `finanse`).

**Krok 0 – boty (78a76a6):** strategie umieją pensję (`minimalna` albo × preferowana), gwiazdki zatrudnianych
niezależnie od jakości (`jakosc_ludzi`), kanał rekrutacji, premię co rundę i właściciela na ostatniej kasie
(`wlasciciel_godziny`, z odjęciem czasu rekrutacji); warianty `pensja:*`, `ludzie:*`, `kanal:*`, `premia:*`,
`szkolenia:*`, `podwyzki:brak`, `wlasciciel:*`; testy `testy/rdzen/test_boty_ludzie.py`.

**Pomiar `b9_ludzie`** (360 gier, 18 rund, 6 firm, 6 ziaren; różnica karty wariant − baza, ile par wygrało):

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| umowa:zlecenie | −0,008 (0/6) | −0,005 (0/6) | −0,003 (1/6) |
| pensja:minimalna | +0,006 (6/6) | +0,001 (6/6) | +0,044 (6/6) |
| pensja:1.25 | −0,067 | −0,059 | −0,104 |
| ludzie:3 | +0,016 (5/6) | +0,030 (6/6) | baza |
| kanal:headhunter | −0,174 | −0,078 | −0,158 |
| premia:300 | −0,084 | −0,079 | −0,103 |
| szkolenia:1 / 3 | −0,085 / −0,340 | −0,094 / −0,353 | +0,106 / −0,103 (baza 2) |
| podwyzki:brak | +0,001 | +0,001 | −0,001 |
| wlasciciel:20 / 10 | −0,187 / −0,960 | −0,141 / −0,882 | −0,152 / −0,604 |

Diagnoza:
- **Szkolenia i premia – pomylona jednostka.** Ceny szkoleń w katalogu są miesięczne (gra ATH), a
  `silnik/decyzje.py` pobierał je co tydzień – szkolenie kosztowało 4,3 raza za dużo (premium bez szkoleń
  +0,21 karty 6/6). Premia jest za rundę, a pensja miesięczna – w zadowoleniu tygodniowa premia 100 zł liczyła
  się jak miesięczna podwyżka o 100 zł. Poprawka (6b7cadf): koszt szkolenia = `na_runde(cena)` (jak czynsz),
  w zadowoleniu premia × rund_w_roku / 12 (`zadowolenie.placa_wzgledna`); panel: ceny szkoleń za rundę, koszt
  wynagrodzeń = pensje z ZUS na rundę + premie (wcześniej premia była dzielona przez 52/12).
- **Zlecenie (H27):** po P1 traci 0,003–0,008 (tylko −0,0115 zadowolenia) – bez dominacji; zostaje elastyczność
  (odejście bez okresu wypowiedzenia).
- **Właściciel na kasie:** 20 h zamiast 40 h kasjera – kasa staje się wąskim gardłem; przegrywa zawsze. Zgodne
  z kompromisem („przy większej firmie ma przegrywać”); oszczędność pensji ma sens tylko przy bardzo małym ruchu.
- **Headhunter:** drogi i bez podkupów (boty ich nie robią) – przegrywa; agencja i pracuj.pl ≈ 0.
- **Lepsi ludzie:** 3★ u taniego +0,03 (6/6), u zrównoważonego +0,016 (5/6) – słaba przewaga jakości (dania
  i obsługa) nad pensją większą o ok. 10%. Bez zmiany (rozpiętość pensji realistyczna, przewaga mała).

**Pomiar `b9_po`** (468 gier; drugi kontekst – próg odejść 0,90 dla wszystkich firm):

| wariant | zrównoważony | tani | premium (baza 2 szkolenia) |
|---|---|---|---|
| szkolenia:0 | baza | baza | +0,028 (6/6) |
| szkolenia:1 | +0,019 (6/6) | +0,006 (5/6) | +0,024 (6/6) |
| szkolenia:2 | −0,005 | −0,016 | baza |
| szkolenia:3 | −0,038 | −0,047 | −0,032 |
| premia:100 / 300 | −0,011 / −0,039 | −0,018 / −0,047 | −0,021 / −0,122 |
| pensja:minimalna (próg 0,87) | +0,006 (6/6) | +0,001 (6/6) | +0,050 (6/6) |
| pensja:minimalna (próg 0,90) | +0,004 (5/6) | +0,001 (6/6) | +0,032 (6/6) |

- Szkolenie jest teraz decyzją: jedno w tygodniu daje mały plus, kolejne tracą (efekt to włącznik). Ustawienia
  botów (`boty.yaml`): zrównoważony 0 → 1, premium i agresywny 2 → 1; tani zostaje przy 0.
- Premia nadal przegrywa – pomaga tylko niezadowolonej osobie (przed odejściem), a przy zadowoleniu nad progiem
  to czysty koszt. Zgodne z jej rolą (narzędzie doraźne).
- **Płaca minimalna (H23)** dominuje u premium: kandydat przyjmuje każdą ofertę od płacy minimalnej, a 3★ przy
  płacy minimalnej ma ok. 0,91 – powyżej progu odejść. Próg 0,90 tylko zmniejsza przewagę (+0,032), wyższy
  wyrzuca ludzi także przy pensji preferowanej. Liczbą się nie da – propozycja „kandydat odrzuca ofertę poniżej
  95% preferowanej” w `notatki_do_zmiany.md`; próg zostaje 0,87. Tam też: szkolenie z efektem na 4 tygodnie.

**Trudność** (`b9_trudnosc`, 5 strategii × 20 ziaren, rywale średni):

| miara | `b8_trudnosc2` | `b9_trudnosc` | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 43/100 (w 3: 57) | 43/100 (w 3: 57) | 4–6 |
| alarmy wersji słabej | 0/100 | 0/100 | 0 |
| dobra > średnia (pary) | 90/100 | 88/100 | ≥ 80% |
| słaba < średnia (pary) | 89/100 | 90/100 | – |
| karta słaba / średnia / dobra | 0,06 / 0,29 / 0,37 | 0,11 / 0,38 / 0,46 | – |

Karty wyższe o ok. 0,09, bo rywale (premium, agresywny) i badane firmy płacą za szkolenia czterokrotnie mniej –
skala słów karty (U10) do odświeżenia w B13. B9 zamknięte; otwarte – decyzje autora: płaca minimalna,
trwały skutek szkoleń. Bez pomiaru: podkupienia i kontroferty (boty ich nie robią), zwolnienia.

## B10 – marketing (6.11.2026, gałąź `kalibracja-b6`)

Krok 0: boty umieją emisje i przerwę kampanii (`emisje_kampanii`, `przerwa_kampanii` w strategii); warianty
`kampania:<agencja/kanał>`, `emisje:N`, `przerwa:N`, `udogodnienia:N`, `wyposazenie:N`, `zdarzenia:brak`.

**Pomiar `b10_marketing`** (504 gry, 18 rund, 6 firm, średni; Δ karty wobec bazy, pary wygrane z 6):

| wariant | zrównoważony | tani | premium |
|---|---|---|---|
| wyposazenie:6 (komplet) | +0,131 (6/6) | +0,117 (6/6) | ≈ 0 |
| udogodnienia:0 | – | – | +0,060 (6/6) |
| kampanie:brak | −0,027 | −0,035 | −0,15 |
| najlepszy kanał | influencer | influencer | baza (2 kanały) |
| radio (cała Lublin) | traci | traci | traci |
| emisje:3 / 10 / 15 | ≈ 0 | ≈ 0 | ≈ 0 |
| przerwa:0 | +0,015 | +0,015 | +0,057 (5/6) |

- **Wyposażenie dominowało:** mnożnik popytu był liniowy (1 + 0,073 × suma % klientów), więc komplet dawał +31%
  popytu za ok. 7 tys. zł i 420 zł tygodniowo – każda sztuka się opłacała. Teraz przyrost się nasyca:
  1 + κ·S·(1 − e^(−x/S)), S = 3 (`popyt.wyposazenie_nasycenie`, `silnik/kuchnia/jakosc.py`) – pierwsza sztuka
  działa jak dawniej, komplet daje ok. +17%.

**Pomiar `b10_po`** (216 gier, z agresywnym; po nasyceniu):

| wariant | zrównoważony | tani | premium | agresywny |
|---|---|---|---|---|
| wyposazenie:3 | baza (2) +0,033 | +0,048 | ≈ 0 | ≈ 0 |
| wyposazenie:6 | +0,062 (6/6) | +0,072 (6/6) | ≈ 0 | ≈ 0 |
| udogodnienia:0 / 3 | – | – | +0,055…+0,059 (6/6) | +0,024…+0,028 (6/6) |
| zdarzenia:brak | −0,02…−0,05 | −0,02…−0,05 | −0,02…−0,05 | −0,02…−0,05 |
| promocje:brak | −0,014 | +0,051 | +0,105 (6/6) | +0,046 (3/6) |

- Wyposażenie to teraz kompromis: komplet opłaca się przy wolnej kuchni (tani, zrównoważony), przy pełnej
  (premium, agresywny) wystarczą 3 sztuki. Boty: tani 3, zrównoważony 6.
- Udogodnienia przy pensji preferowanej nic nie dają (nikt nie odchodzi) – premium i agresywny 3 zamiast 9 i 6;
  propozycja w `notatki_do_zmiany.md` (ta sama przyczyna co płaca minimalna w B9).

**Pomiar `b10_promocje`** (216 gier; drugi kontekst – karta z rabatem 5%):

| promocja | zrównoważony (baza zestaw) | tani (baza happy + studencka) | premium (baza karta) |
|---|---|---|---|
| brak | −0,024 | +0,045 (6/6) | +0,092 (6/6) |
| zestaw | baza | +0,048 (6/6) | +0,156 (6/6) |
| studencka | −0,021 | +0,043 (6/6) | +0,091 (6/6) |
| happy hours | −0,102 | +0,004 | +0,002 |
| 2 za 1 | −0,182 | +0,001 | −0,114 |
| karta przy rabacie 5% | −0,074 | +0,029 (6/6) | baza; brak +0,030 |

- Zestaw (dopłata, bez rabatu) wygrywa – premium przechodzi z karty na zestaw, tani zostaje przy studenckiej.
  Promocje z rabatem dla wszystkich nadal przegrywają, także karta z rabatem 5% – rabat zostaje 10%, dopisek
  do propozycji B7 (trwały skutek promocji).

**Pomiary `b10_kanaly` i `b10_kanaly2`** (po 360 gier; zrównoważony, premium; lokal w centrum, akademickich,
na Felinie; jeden kanał zamiast kanałów strategii, Δ wobec bazy – średnio z 18 par):

| kanał | zrówn. przed | zrówn. po | premium przed | premium po |
|---|---|---|---|---|
| radio (180 → 70 zł) | −0,042 (0/18) | −0,008 (6/18) | −0,072 | −0,033 |
| degustacja (110 → 80 zł) | −0,007 | +0,004 (10/18) | −0,029 | −0,020 |
| noc kebaba (400 → 200 zł) | −0,027 | −0,011 | −0,068 | −0,056 |
| noc kebaba, lokal w akademickich | −0,041 | +0,008 | −0,045 | +0,002 |
| influencer | +0,007 (13/18) | +0,005 | −0,018 | −0,019 |
| plakaty | +0,006 | +0,008 | −0,020 | −0,020 |
| brak kampanii | −0,028 | −0,028 | −0,070 | −0,067 |

- Przy starych cenach radio, degustacja i noc kebaba przegrywały z każdym kanałem; po obniżce wszystkie kanały
  mieszczą się w ±0,01 u zrównoważonego, a noc kebaba (tylko strefy akademickie i politechnika) jest na plus
  tam, gdzie działa. Brak kampanii traci zawsze. W połowie ziaren strefa akademicka była zajęta przez rywali –
  wiersz „lokal w akademickich” liczy tylko pary z lokalem badanej w tej strefie (3 z 6).

**Trudność** (`b10_trudnosc`, 5 strategii × 20 ziaren, rywale średni):

| miara | `b9_trudnosc` | `b10_trudnosc` | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 43/100 (w 3: 57) | 43/100 (w 3: 57) | 4–6 |
| alarmy wersji słabej | 0/100 | 0/100 | 0 |
| dobra > średnia (pary) | 88/100 | 85/100 | ≥ 80% |
| słaba < średnia (pary) | 90/100 | 99/100 | – |
| karta słaba / średnia / dobra | 0,11 / 0,38 / 0,46 | 0,10 / 0,45 / 0,52 | – |

Karta średniej +0,07 – boty rywali kupują mniej udogodnień, premium ma zestaw zamiast karty; skala słów karty do
B13. B10 zamknięte; otwarte – decyzje autora: trwały skutek promocji, udogodnienia przy uczciwej płacy.


## B11 – finanse (6.11.2026, gałąź `kalibracja-b6`)

Boty umieją korzystać z finansów (`silnik/boty.py`, `_finanse`; ustawienia strategii `lokaty`, `kredyt`,
`harpagon`, `kasyno`, domyślnie wyłączone – testy `testy/rdzen/test_boty_finanse.py`). Zaproszenia do klubu
dostają boty tylko w pomiarach (opcja gry `kasyno_botow`, włączana w `balans/warianty.py`). Harpagon: bot spłaca
z nadwyżki ponad próg, także częściowo – przy spłacie tylko całości dług rósł szybciej niż gotówka (premium
przy 15 tys. zł kapitału: majątek z 117 tys. zł spadał do −41 tys. zł).

**Pomiary** (18 rund, 6 firm, rywale średni; Δ względem bazy w parach z tym samym ziarnem):

| wariant | `b11_finanse` (6 ziaren × 3 strategie) Δ karta / Δ majątek | `b11_stres` (kapitał 15 tys. zł) Δ karta / Δ majątek |
|---|---|---|
| inny bank niż mBank | −0,02 / −1,6…−1,9 tys. zł (0%) | −0,02 / −2,4…−2,7 tys. zł (0%) |
| lokata 4 tyg. | +0,00 / +0,1 tys. zł (78%) | −0,00 / +0,06 tys. zł |
| lokata 13 tyg. | −0,00 / −0,0 tys. zł | – |
| kredyt start 50 tys. zł bez celu | −0,14 / +2,6 tys. zł | −0,05 / +9,3 tys. zł |
| kredyt obrotowy 40 tys. zł bez celu | −0,11 / −0,1 tys. zł | – |
| kredyt start + drugi lokal (`b11_rozwoj`) | +0,30 ± 0,10 / +50 tys. zł (89%) | +0,16 ± 0,07 / +33 tys. zł (78%) |
| kredyt obrotowy + drugi lokal (`b11_rozwoj`) | +0,12 ± 0,07 / +25 tys. zł (72%) | – |
| sam drugi lokal (`b11_rozwoj`) | +0,11 ± 0,07 / +10 tys. zł (78%) | – |

- **Banki:** konto w mBanku (opłata 0 zł, terminal 0,79%) wygrywa zawsze o 1–3 tys. zł; różnica w karcie −0,02.
  Limit Santandera (40 tys. zł) pod stresem usuwa alarmy premium (1,2 → 0,0 na parę), ale nie odrabia opłat.
  Lekcja „porównaj opłaty banku” działa; bank to mały wybór, nie pułapka.
- **Lokata** daje grosze (H9: dużo mniej niż inwestycja w firmę) – zgodnie z planem.
- **Kredyt** bez celu przegrywa w karcie (zadłużenie z U22: 50 tys. zł długu na koncie daje zad ≈ 0,87), a
  kredyt wydany na drugi lokal wygrywa najmocniej ze wszystkich dotąd zmierzonych decyzji (H20 spełnione:
  „kredyt nie zawsze zły”).
- **Harpagon** (`b11_harpagon`, 12 ziaren, kapitał 15 tys. zł, po zmianie spłaty): zrównoważony −1,6 tys. zł
  (1/12 na plus), tani −0,2 tys. zł, premium −11,8 tys. zł i −0,10 karty (2/12 na plus), ale alarmy premium
  spadają z 3,5 do 0,7 na grę. Ryzykowny, czasem opłacalny – zgodnie z planem. W zwykłym starcie bot nie
  potrzebuje Harpagona (wariant = baza).
- **Kasyno** (`b11_kasyno`, 30 ziaren, zrównoważony, 5 × 2000 zł na zaproszenie; zaproszenie w 24/30 gier):

| gra | Δ majątek średnio | w grach z zaproszeniem | na plus / na minus | najlepsza / najgorsza |
|---|---|---|---|---|
| ruletka – czerwone | −0,9 tys. zł | −1,1 tys. zł | 10 / 14 | +10,0 / −13,1 tys. zł |
| ruletka – zero | −2,0 tys. zł | −2,6 tys. zł | 4 / 20 | +62,0 / −21,0 tys. zł |
| automat | −2,1 tys. zł | −2,6 tys. zł | 5 / 19 | +24,0 / −14,0 tys. zł |

  Średnio traci, ale co trzecia–czwarta gra wygrywa – reguła „ryzykowne, czasem opłacalne” spełniona; karta się
  nie zmienia (pieniądze z portfela właściciela, poza firmą).
- **Z3 (debet ponad limit):** bez górnej granicy, z odsetkami karnymi 19%, blokadą w następnej rundzie i
  inwestorem ratunkowym – pod stresem (kapitał 15 tys. zł) alarmy ma tylko premium (1,2 na parę), bez zmian.

Danych gry i domyślnych strategii botów nie zmieniono (zmiana spłaty Harpagona działa tylko przy ustawieniu
`harpagon`), więc kontrola trudności z B10 (`b10_trudnosc`) obowiązuje. Do decyzji autora – „B11 – kredyt bez
celu” w `notatki_do_zmiany.md`. Otwarte do B13: rywale trudni mogą finansować drugi lokal kredytem (dziś kupują go
z gotówki), co wzmocni poziom trudny.

## B12 – księgowość i urzędy (6.11.2026, gałąź `kalibracja-b6`)

Boty umieją samodzielną księgowość (`silnik/boty.py`, `_ksiegowosc`; ustawienie strategii `ksiegowosc` –
`bledy`: szansa błędnej deklaracji, `odchylenie`: o ile zaniżona; bez ustawienia bot nie składa deklaracji i urząd
rozlicza go z urzędu z mandatem) oraz obniżenie higieny dopiero po odbiorze lokali (`higiena_po_odbiorze`). Testy:
`testy/rdzen/test_boty_finanse.py`. Domyślne strategie bez zmian (wszystkie przy biurze eksiegi).

**Pomiar `b12_urzedy`** (18 rund, 6 firm, rywale średni, 3 strategie × 6 ziaren; Δ względem bazy w parach):

| wariant | Δ karta | wygrane | Δ majątek zł | ocena |
|---|---|---|---|---|
| biuro eksiegi (domyślne) | = baza | – | – | – |
| biuro halinka / trybunał / debet-kredyt | −0,01…0,00 | 6% | −0,5…+0,2 tys. | szum |
| biuro jks | −0,01 | 3% | −0,4 tys. | gorszy |
| samodzielnie, rzetelnie | +0,02 ± 0,02 | 83% | +3,0 ± 1,7 tys. | lepszy |
| samodzielnie, co 4. deklaracja zaniżona o 20% | +0,02 ± 0,02 | 89% | +1,4 ± 1,8 tys. | lepszy |
| samodzielnie, bez deklaracji | +0,01 ± 0,02 | 83% | **−6,9 ± 1,5 tys.** | szum |
| higiena brak | −1,73 | 0% | −168 tys. (lokal nieodebrany) | gorszy |
| higiena brak dopiero po odbiorze | −0,01 ± 0,02 | 39% | −2,5 ± 2,2 tys. | szum |
| higiena podstawowa | +0,01 ± 0,02 | 67% | +1,4 ± 1,8 tys. (premium +4,3 tys., 5/6) | szum |
| higiena firma | +0,01 ± 0,02 | 33% | +0,8 ± 2,2 tys. | szum |
| higiena haccp | −0,02 ± 0,01 | 28% | −1,5 ± 1,3 tys. | gorszy |

- **Biura (H5):** najtańsze eksiegi (bez OC, ryzyko 12%) wygrywa nieznacznie; droższe biura tracą 0,1–0,5 tys. zł
  na 18 tygodni, a z niszami (halinka, trybunał wygrywają w pojedynczych grach do +1,2 tys. zł) – mały wybór,
  bez pułapki.
- **Samodzielnie** oszczędza opłatę biura (ok. 3 tys. zł) kosztem pracy gracza przy każdej rundzie i ryzyka błędu
  (200 zł za błędną deklarację) – kompromis „pieniądze za czas”; u bota czas jest darmowy, stąd wygrana.
- **Łamanie zasad** średnio się nie opłaca w majątku: bez deklaracji −6,9 tys. zł, higiena „brak” po odbiorze
  −2,5 tys. zł (7/18 par na plus – czasem się udaje). **Karta tego nie widzi:** bez deklaracji +0,01 karty, bo
  mandaty są poza KPiR – propozycja „B12 – mandaty skarbowe nie obniżają karty” w `notatki_do_zmiany.md`.
- **Higiena (H15):** podstawowa wystarcza; wyższe poziomy to ubezpieczenie przy dużej chłodni i ryzyku
  przeterminowania (premium przy haccp traci 4,3 tys. zł względem podstawowej) – zgodne z planem.

**Polisy (H26).** Pomiar `b12_polisy` (30 ziaren, zrównoważony i tani): komplet polis +1,67 ± 0,5 tys. zł, 82%
wygranych – dominacja. Rachunek w grach (4 ziarna × 6 firm, wszyscy z kompletem): odszkodowania średnio 2,8 tys. zł
na firmę, składki 0,96 tys. zł – lokal 1,9 ×, sprzęt 24 × (składka tylko od majątku, ok. 60 zł na grę), OC 0,63 ×
składki. Wypadki są w grze dużo częstsze niż w życiu (2–3 na 18 tygodni), więc składki z cen rynkowych dawały
pewny zysk. Zmiana w `dane/zdarzenia/losowe.yaml` (miesięcznie): lokal 140 → 300 zł za lokal, sprzęt 0 → 400 zł
stałej + 0,2% majątku, OC 80 → 60 zł. Teraz odszkodowania ≈ 0,85–0,88 składki każdej polisy.

| `b12_polisy2` (30 ziaren) | zrównoważony (lokal, OC) | tani (bez polis) | premium (komplet) |
|---|---|---|---|
| komplet polis | +0,66 tys. zł, 20/30 | −0,19 tys. zł, 13/30, od −6,7 do +5,0 tys. | = baza |
| bez polis | +0,98 tys. zł, 22/30, od −2,4 do +6,1 tys. | = baza | +0,53 tys. zł, 18/30, **od −12,1 do +14,6 tys.** |

Wszystkie konteksty: komplet +0,16 ± 0,35 tys. zł (52%), brak +0,50 ± 0,57 tys. zł (63%) – oba „szum”, karta
±0,01. Polisa ma lekko ujemną wartość oczekiwaną i zmniejsza rozrzut (premium bez polis traci w złej grze do 12
tys. zł) – tak, jak zakłada inwentarz.

**Trudność** (`b12_trudnosc`, 5 strategii × 20 ziaren, rywale średni – po zmianie składek):

| miara | `b10_trudnosc` | `b12_trudnosc` | cel |
|---|---|---|---|
| pierwszy plus średniej w rundach 4–6 | 43/100 (w 3: 57) | 43/100 (w 3: 57) | 4–6 |
| alarmy wersji słabej | 0/100 | 1/100 | 0 |
| dobra > średnia (pary) | 85/100 | 87/100 | ≥ 80% |
| słaba < średnia (pary) | 99/100 | 99/100 | – |
| karta słaba / średnia / dobra | 0,10 / 0,45 / 0,52 | 0,10 / 0,45 / 0,52 | – |

Jedyny alarm: premium słaba, ziarno 1018 – 151 zł ponad limit w rundzie 5 (gotówka 0 zł w rundach 2–6 już w
B10, droższy komplet polis przesunął grę za granicę). Do przejrzenia w B14 razem z rezerwą gotówki poziomu słabego.
B11 i B12 nie zmieniły kart (rywale na poziomie średnim mają polisy lokal + OC, tani – żadnych). B12 zamknięte;
do decyzji autora – „B12 – mandaty skarbowe nie obniżają karty” w `notatki_do_zmiany.md`.

## B13 – karta wyników: wagi składowych (6.11.2026, gałąź `kalibracja-b6`)

Plan: wagi składowych tak, żeby karty nie dało się „nabić” jednym zabiegiem, a ranking według karty był wyraźnie,
ale nie idealnie zgodny z majątkiem netto. Boty nie czytają karty (decyzje nie zależą od wyniku), więc kartę
z innymi wagami można przeliczyć na zapisanych grach – bez nowych pomiarów dla każdej wersji. Badane wagi:
wykładniki przy składnikach, wynik = we × zp^a × zk^b × roz^c × zad^d (wszystkie 1 – jak teraz), i waga straty.

**Ranking** – 80 gier mieszanych (6 firm, 5 strategii + 1 losowa, poziomy łatwy/średni/trudny i człowiek
słaby/średni/dobry pomieszane, 18 rund, ziarna 100–179):

| wagi (zp, zk, roz, zad; strata) | Spearman karta ~ majątek netto | karta ~ dochód | ten sam 1. w karcie i majątku | karta śr. |
|---|---|---|---|---|
| **1, 1, 1, 1; 1 (teraz)** | **0,935** | 0,969 | **81%** | 0,46 |
| 1, 1, 1, 1; 0,6 | 0,948 | 0,955 | 84% | 0,50 |
| 1, 1, 0, 1; 1 (bez rozwoju) | 0,936 | 0,974 | 82% | 0,79 |
| 0,5 każdy; 1 | 0,936 | 0,983 | 82% | 0,59 |
| 2 każdy; 1 | 0,925 | 0,935 | 82% | 0,28 |
| 0 każdy (sam dochód) | 0,927 | 1,000 | 79% | 0,76 |

Każda wersja daje zgodność 0,92–0,95: „wyraźnie, ale nie idealnie” jest spełnione już teraz, a wagi zmieniają ją
mniej niż szum. Iloczyn wskaźników w tygodniach z zyskiem wynosi średnio 0,65 (rozwój 0,61 – największy hamulec,
zadowolenie klientów 1,07, pracowników 0,96, zadłużenie ≈ 1).

**Nabijanie** – pomiar `b13_wagi` (35 wariantów ze wszystkich obszarów B6–B12, zrównoważony / tani / premium,
poziom średni, 6 ziaren, 648 gier; zapisane też składniki karty z każdego tygodnia): karta i majątek mają ten sam
znak w 83% par (teraz); najlepsza wersja wag (sam dochód) – 86%, wykładnik 2 przy zadowoleniu pracowników – 78%,
bez rozwoju – 77%. Każdy wariant, który wyraźnie podnosi kartę, podnosi też majątek (menu 8 premium +0,53 karty
/ +60 tys. zł, kredyt na drugi lokal +0,32…+0,38 / +52…+57 tys. zł, drugi lokal taniego +0,21 / +22 tys. zł,
dyskont +0,05…+0,07 / +7 tys. zł). Jedyny „nabity” zysk: **samodzielna księgowość bez deklaracji** (+0,01 karty,
−6,5…−6,7 tys. zł) – mandaty są poza dochodem karty, wagi tego nie naprawią (propozycja B12 już czeka u autora).
Odwrotne rozbieżności (karta niżej, majątek wyżej) są małe i zgodne z zamysłem karty: bez szkoleń −0,01…−0,02 karty
/ +3,1…+3,5 tys. zł, kredyt start bez celu −0,10…−0,14 (U22, propozycja B11), 6 udogodnień −0,005…−0,011.

**Decyzja: wagi bez zmian.** Żadna zmiana wykładników nie poprawia jednocześnie rankingu i zgodności par, a każda
przesuwa średnią kartę (czyli skalę słów i porównania z wcześniejszymi grami). Waga straty 0,6 dałaby +0,013
Spearmana i mniejszą karę za jednorazowy zakup sprzętu (P1 z analizy gracza), ale U1 to decyzja autora („liczby
karty bez zmian”) – nie proponuję, zysk jest w granicach szumu.

**Skala słów karty (U10)** – percentyle z 80 gier mieszanych (rundy 3–14) po kalibracji B6–B12: wynik
działalności p25 0,20 / p75 0,83 (ludzie) – 1,00 (boty), wynik ekonomiczny 0,36–0,38 / 1,29–1,55, rozwój 0,54 /
0,64, zadowolenia bez zmian. Progi w `dane/zalozenia.yaml` (`karta_wynikow.skala`): wynik działalności 0,1 / 0,7 →
0,2 / 0,9, wynik ekonomiczny 0,15 / 1,1 → 0,35 / 1,4, rozwój 0,56 / 0,67 → 0,54 / 0,64 (tylko słowo i kolor przy
wskaźniku – wynik się nie zmienia).

**H19 („nic nie rób”)** – pomiar `b13_nic` (człowiek słaby, rywale średni, 6 ziaren): firma bez lokalu od rundy 1
ma −0,016 karty. Słaba wersja „jak człowiek” jest nad zerem u zrównoważonego (0,19), naśladowcy (0,16), taniego
(0,10) i premium (0,11; `b12_trudnosc`, 20 ziaren), ale **słaba agresywna ma −0,04…−0,06** (17/20 gier poniżej
zera, w `b13_nic` 4/6 gorsza od nicnierobienia). Zasady zostają (decyzja autora, pyt. 2); słaba agresywna – do B14
(poziomy botów).

**H22** – w INSTRUKCJI (rozdz. 3, zasady karty) dopisane: wypłaty dla siebie nie obniżają wyniku działalności,
zmniejszają gotówkę i majątek netto firmy. Liczby bez zmian.

**Szybki pomiar wszystkich obszarów** – to `b13_wagi` (35 wariantów z B6–B12 na kalibrowanych danych): bez nowej
dominacji – wyraźnie wygrywają tylko zabiegi, które też budują majątek (menu 8 u premium – propozycja B7 czeka,
kredyt na rozwój, drugi lokal taniego, dyskont za czas właściciela). B13 zamknięte.
