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
