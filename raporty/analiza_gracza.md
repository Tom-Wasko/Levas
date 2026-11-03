# Analiza oczami gracza (część A, krok 6)

Wykonawca: Claude Code (Opus 5.5) zamiast Fable, decyzja autora z 3.11.2026. Gałąź `analiza-a`, wersja gry
po Z1–Z7 i zatwierdzonym B5 (commit 28acb40). Kod gry bez zmian.

Na czym opiera się raport (wszystko w `raporty/analiza/`):
- **Nowicjusz**, 16 lat (`dziennik_nowicjusz.md`): 1 gra, 18 rund, 4 firmy, typowe błędy ucznia.
  13 zrzutów ekranu.
- **Optymalizator** (`dziennik_optymalizator.md`): 18 wariantów strategii × 3 ziarna = 54 pełne gry.
  Ocena kartą skumulowaną i majątkiem netto.
- **Nauczyciel / mistrz gry** (`dziennik_nauczyciel.md`): 4 drużyny „uczniów” z zaplanowanymi błędami
  i 2 boty. Konta uczniów, pauza, cofnięcie rundy, inwestor, eksporty. 14 zrzutów ekranu.
- Skrypty do powtórzenia: `raporty/analiza/skrypty/` (gracz przez API jak przeglądarka; osobny serwer
  i baza).
- Raport B4 i dziennik kalibracji przeczytałem dopiero po grach. Znanych dominacji nie powtarzam, piszę
  tylko o różnicach (sekcja 6).

Jak czytać pozycje 1–22 (sekcje 2–4):
- **Priorytet:**
  - **P1** – psuje zrozumienie gry albo wynik ucznia; zrobić przed lekcjami.
  - **P2** – wyraźnie poprawi grę.
  - **P3** – drobiazg albo pomysł na później.
- **Koszt:** **S** – godzina–dwie; **M** – pół dnia do dnia; **L** – kilka dni.
- **Balans:** czy zmiana rusza liczby (wtedy krok K po U ją zmierzy).
- Numery są ciągłe, żeby można było napisać po prostu „U: 1, 3, 5, 9”.

---

## 1. Najważniejsze 10 wniosków

1. **Zakup sprzętu potrafi „zabić” kartę.** Wyposażenie lokalu (pozycje poniżej 10 000 zł) idzie od razu
   w koszty. Strata liczy się z wagą 1,0, a zysk jest mnożony przez wskaźniki ok. 0,5. Nowicjusz za
   urządzenie drugiego lokalu dostał w jednej rundzie −2,48, czyli więcej, niż zarobił przez 12 rund. Instrukcja
   (rozdz. 3) mówi, że nowy sprzęt i kolejne lokale *podnoszą* rozwój. Uczeń odbierze to jako oszustwo gry.
   → poz. 1.
2. **„Nic nie rób” daje kartę ≈ 0 (−0,02)** i 3. miejsce z 4, przed aktywnymi słabymi graczami. Firma bez
   lokalu nie ponosi kary za zero klientów i zero pracowników. → sekcja 6, pytanie 2.
3. **Premium z wyższą ceną wygrywa każdą grę** (karta 0,9–0,96 wobec 0,34–0,49 bazy). Ceny × 1,2 u premium
   poprawiają wynik, a u zwykłego kebaba ceny × 1,3 go niszczą. → sekcja 6.
4. **Kredyt na rozwój zawsze się nie opłaca.** Podobny dochód i majątek, a karta 0,18 wobec 0,55 bez kredytu.
   Wskaźnik zadłużenia nie widzi gotówki z kredytu leżącej na koncie. → sekcja 6, pytanie 3.
5. **Alarm debetu jest głośny u mistrza gry, a cichy u ucznia.** Uczeń widzi go tylko w Finanse ▸ Bank,
   a Dashboard i Lista błędów milczą. → poz. 2.
6. **Lista błędów jest najlepszym przewodnikiem w rundzie 1, a od rundy 3 uczeń przestaje ją czytać.**
   Ostrzeżenia o przeterminowaniu co rundę, 12+ linijek o jednym niewyposażonym lokalu, humor i prawdziwe
   błędy wyglądają tak samo. → poz. 5.
7. **Dwa realne błędy tekstów:** fałszywy komunikat „właściciel leży na kanapie” zaraz po pierwszym
   lokalu i stare nazwy zakładek („Inwestycje”, „Kadry”) w instrukcji urządzania lokalu. → poz. 3 i 4.
8. **Drużyna w spirali nie ma wyjścia.** Po jedynym inwestorze mistrz gry nie ma już narzędzia, a uczniowie
   grają 12 rund bez szans na zmianę miejsca (4D: −1,25, majątek −70 tys. zł). → poz. 18, pytanie 4.
9. **Prowadzenie gry przez nauczyciela działa bardzo dobrze.** Pauza, „zamknij mimo braków” z jasnym
   komunikatem, cofnięcie rundy (deterministyczne co do grosza), zmiana poziomu bota, eksport CSV do
   polskiego Excela. → sekcja 5.
10. **Ranking zaskoczy klasę.**
    - Wygrała drużyna, która „przepalała” gotówkę na reklamę i wypłaty (64 tys. zł wypłat nie obniża karty).
    - Bot z największym majątkiem był 3.
    - Drużyna grająca „porządnie” (kalkulator „jak człowiek – dobry”) była 5. z 6.
    - Nauczyciel potrzebuje w panelu majątku obok wyniku i jednego zdania „dlaczego”. → poz. 16,
      pytanie 1.

---

## 2. Problemy

### [1] Jednorazowy zakup sprzętu daje ogromny minus na karcie
**P1 · koszt M · balans: duży · w planie: częściowo (B13 – wagi karty, ale nie ten mechanizm)**

- **Problem:** Środki poniżej progu 10 000 zł (`dane/zalozenia.yaml:188`, `amortyzacja_prog`) idą w całości
  w koszty rundy zakupu. Tydzień ze stratą to `wynik_ekonomiczny × waga 1,0` bez mnożników
  (`gra/silnik/wyniki/karta.py:93`), a tydzień z zyskiem jest mnożony przez wskaźniki (zwykle razem
  ok. 0,5). Zakup wyposażenia za 11 tys. zł kosztuje więc na karcie tyle, co ok. 20 dobrych tygodni.
- **Dowód:**
  - Nowicjusz R15 (`dziennik_nowicjusz.md`): urządzenie Pawilonu na Witosa (rożen 4500, kasa 1500,
    lada 2500, tablica 600, stanowiska po 1000 zł) dało dochód −11 448 zł i kartę **−2,481**.
    Suma rund R3–R14 wynosiła ok. +2,2.
  - Optymalizator: `planista_trudny` (2 lokale) ma −0,40 / −0,33 na 2 z 3 ziaren.
  - Sprzeczne z `gra/INSTRUKCJA.md:84` („Rozwój firmy … Nowy sprzęt i wyposażenie, … kolejne lokale”).
- **Propozycja** (do wyboru przez autora, pytanie 5):
  - **(a)** Karta nie widzi zakupu środków trwałych jako kosztu. Wynik ekonomiczny do karty liczy się
    z dochodu KPiR plus wydatki na środki poniżej progu, minus ich „amortyzacja do karty”, np. przez
    8 rund. KPiR i podatki bez zmian (to prawo, a wydatek nadal jest kosztem podatkowym).
  - **(b)** Najprostsza: dolna granica karty jednego tygodnia, np. −1,0.
  - **(c)** Ostrzeżenie przed zakupem („ten zakup obniży tę rundę o ok. X na karcie”). To tylko łata.
  - Polecam (a). Zgadza się z instrukcją i uczy, że inwestycja to nie koszt jednego tygodnia.
- **Pliki:** `gra/silnik/wyniki/karta.py`, `dane/zalozenia.yaml` (`karta_wynikow`), `gra/INSTRUKCJA.md`
  rozdz. 3, testy karty.

### [2] Alarm debetu ponad limit prawie niewidoczny dla ucznia
**P1 · koszt S · balans: brak · w planie: nie (Z3 dał alarm u mistrza gry)**

- **Problem:** Komunikat o blokadzie inwestycji i możliwości inwestora jest tylko w uwagach pod kontem
  w Finanse ▸ Bank (`panel_gracza/static/zakladki/banki.js:153`).
- **Dowód:** Nauczyciel R6, drużyna 4D, zrzut `nauczyciel_r06_4D_alarm.png`:
  - Dashboard pokazuje saldo 0 zł i „Zadłużenie 10 524 PLN” drobnym drukiem.
  - Lista błędów pokazuje tylko ten sam co rundę tekst o kredycie odnawialnym.
  - Panel mistrza gry ma wyraźny czerwony alarm.
- **Propozycja:**
  - Czerwony pasek na Dashboardzie: „ALARM: debet ponad limit X zł. W tej rundzie nie możesz inwestować,
    brać kredytów, leasingu ani lokat. Spłać debet albo poproś mistrza gry o inwestora.”
  - Ta sama pozycja jako pierwsza na Liście błędów, z przyciskiem „Popraw” do Finanse ▸ Bank.
- **Pliki:** `gra/api/prezentacja.py` (dashboard, lista błędów), `gra/silnik/decyzje.py` (uwagi),
  `panel_gracza/static/zakladki/ogolne.js`.

### [3] Fałszywy komunikat „właściciel leży na kanapie” po pierwszym lokalu (błąd)
**P1 · koszt S · balans: brak · w planie: nie**

- **Kroki:**
  1. Nowa gra, runda 1.
  2. Wybrać pierwszy lokal i zapisać decyzje.
  3. Na Liście błędów pojawia się niebieska pozycja „Właściciel leży na kanapie z mrożonym kebabem na
     czole… Kolejny lokal można wziąć co 3 rundy – najwcześniej w rundzie 4”.
- **Dowód:** `log_nowicjusz.json` (R1), `dziennik_nowicjusz.md`. Nowicjusz uznał, że lokal nie został
  przyjęty.
- **Przyczyna:** `gra/silnik/decyzje.py:595` dodaje komunikat zawsze, gdy firma ma jakikolwiek lokal,
  a runda jest przed `od_rundy` kolejnego lokalu.
- **Propozycja:** Pokazywać komunikat tylko w Inwestycje ▸ Lokale (przy przycisku najmu lub kupna) albo na
  Liście błędów dopiero wtedy, gdy gracz próbuje wziąć kolejny lokal (`limity.py:40` już to robi).
- **Pliki:** `gra/silnik/decyzje.py:594-596`, test listy błędów.

### [4] Stare nazwy zakładek w instrukcji urządzania lokalu
**P1 · koszt S · balans: brak · w planie: nie (przebudowa zakładek 2.11 tego nie objęła)**

- **Problem:** `gra/silnik/nieruchomosci/lokale.py:233`: „kup stanowiska kuchni i kasy (Inwestycje), sprzęt
  na stanowiska i zatrudnij pracowników (Kadry)”. Zakładki „Kadry” nie ma, a stanowiska są
  w Lokale ▸ Sprzęt, ludzie w Lokale ▸ Ludzie.
- **Dowód:** nowicjusz R12.
- **Propozycja:**
  - „kup stanowiska i sprzęt (Lokale ▸ Sprzęt) i zatrudnij pracowników (Lokale ▸ Ludzie)”.
  - Przy okazji: grep po wszystkich tekstach silnika za „(Kadry)”, „(Inwestycje)”, „(Oferta)” i test,
    który pilnuje, że nazwy zakładek w tekstach istnieją w `MENU`.
- **Pliki:** `gra/silnik/nieruchomosci/lokale.py:233`, ewentualnie inne teksty, nowy test.

### [5] Lista błędów: szum zamiast przewodnika
**P1 · koszt M · balans: brak · w planie: nie**

- **Problem:** Wszystkie pozycje wyglądają tak samo. Co rundę są ich 5–20 i powtarzają się.
- **Dowód:**
  - Ostrzeżenia o przeterminowaniu „ok. 0,8 opak. bułki, 37 zł” po kilka co rundę do końca gry
    (nowicjusz od R2; 4D co rundę).
  - Niewyposażony lokal daje po dwie linijki na każde danie (`gra/silnik/kuchnia/menu.py:128` i `:132`),
    czyli 12+ linijek o jednej sprawie (nowicjusz R13–R14).
  - „Wydatki przekraczają saldo… kredyt odnawialny” u 4D w rundach R6–R18 bez zmiany.
- **Propozycja:**
  - Trzy grupy z nagłówkami: **Do zrobienia** (czerwone), **Uwaga** (pomarańczowe), **Dla informacji**
    (niebieskie, domyślnie zwinięte).
  - Łączenie pozycji tej samej sprawy:
    - „Pawilon: 6 dań bez sprzętu i kucharza – urządź lokal” z jednym „Popraw”;
    - „Przeterminuje się towar za ok. 120 zł (bułka, mięso, …) – zamów mniej” w jednej linijce
      z kwotą łącznie.
  - Licznik w menu liczy tylko czerwone.
- **Pliki:** `gra/silnik/decyzje.py` (od ok. linii 588), `gra/silnik/kuchnia/menu.py`,
  `panel_gracza/static/zakladki/ogolne.js:201`, `lokal.js:113`.

### [6] Mandat za brak deklaracji – uczeń nie wie, że biuro jest tańsze
**P2 · koszt S · balans: mały · w planie: B12 (kary) – tylko liczby, nie tekst**

- **Problem:** „Nie złożono deklaracji… mandat 500 zł” (`gra/silnik/ksiegowosc/biuro.py:316`) nie mówi,
  co zrobić zamiast. Przycisk „Popraw” prowadzi do Księgowość ▸ Biuro, ale tam nie ma porównania.
- **Dowód:** Nowicjusz zapłacił 5 × 500 zł, myśląc, że „mandat to tylko 500 zł”. Biura kosztują ok.
  160–230 zł na tydzień (ryczałty 690–984 zł / mies.; Trybunał 6,15 zł za dokument, min. 246 zł).
- **Propozycja:** Dopisek w komunikacie: „Zaksięguj dokumenty w Księgowość ▸ KPiR i złóż deklarację albo
  wybierz biuro (najtańsze ok. 160 zł / tydzień)”. W zakładce Biuro wiersz „samodzielnie bez deklaracji:
  500 zł mandatu co rundę”.
- **Pliki:** `gra/silnik/ksiegowosc/biuro.py:316`, `panel_gracza/static/zakladki/finanse.js` (biuro).

### [7] Przy samodzielnej księgowości bez deklaracji uczeń nie widzi swojego dochodu
**P2 · koszt S · balans: brak · w planie: nie**

- **Problem:** Wynik podatkowy jest celowo ukryty do złożenia deklaracji (`gra/api/prezentacja.py:284-289`).
  Nowicjusz, który deklaracji nie składa, przez 5 rund ma na Dashboardzie pusty dochód. Karta i panel
  mistrza gry go znają.
- **Dowód:** `log_nowicjusz.json`, R2–R6: `wyniki.kpir.dochod_netto = None`.
- **Propozycja:** Zamiast pustego pola napis „Dochód poznasz po złożeniu deklaracji (Księgowość ▸ KPiR) –
  albo wybierz biuro”. Mechanizm ukrycia zostaje (jest dobry dydaktycznie), ale ma się tłumaczyć.
- **Pliki:** `panel_gracza/static/zakladki/ogolne.js` (dashboard), `finanse.js`.

### [8] Zdarzenie: gra po cichu zmienia wybraną opcję, gdy brakuje czasu właściciela
**P2 · koszt S · balans: brak · w planie: nie**

- **Problem:** Wybór opcji, na którą nie starcza godzin, jest odrzucany przy przeliczeniu
  (`gra/silnik/ludzie/czas_wlasciciela.py:5`), a gra wybiera inną.
- **Dowód:** Nowicjusz R9, zdarzenie „Zaginął Kebab”: wybrał 5 h szukania jamnika, ale dowiedział się
  z Listy błędów *po* rundzie, że wykonano drugą opcję.
- **Propozycja:** Przy opcji zdarzenia pokazywać „wymaga 5 h, masz wolne 3 h” i wyszarzać ją od razu
  (dane są w widoku czasu właściciela). Czerwony komunikat na Liście błędów już *przed* wysłaniem.
- **Pliki:** `panel_gracza/static/zakladki/zdarzenia.js`, `czas.js`, `gra/silnik/decyzje.py`.

---

## 3. Zmiany w tym, co jest

### [9] Wyjaśnić stratę w pierwszym tygodniu sprzedaży
**P2 · koszt S · balans: brak · w planie: nie (rozruch z B5 jest w INSTRUKCJA rozdz. 6)**

- **Cel:** Nowicjusz w R2 ma −3430 zł i kartę −0,743 „bez słowa” (`dziennik_nowicjusz.md`).
- **Propozycja:** Na Dashboardzie w rundzie 2 (i po otwarciu każdego kolejnego lokalu) ramka
  „Rozruch: w pierwszym tygodniu przychodzi 40% klientów, co tydzień +10 p.p. Strata na starcie jest
  normalna – mała strata kosztuje mało”. Dane już są (`dane/mapa/popyt.yaml: model.rozruch`).
- **Pliki:** `gra/api/prezentacja.py` (dashboard), `ogolne.js`.

### [10] Skala przy wskaźnikach karty wyników
**P3 · koszt S · balans: brak · w planie: nie**

- **Cel:** „0,914 / 0,928 / 0,535” bez punktu odniesienia. Uczeń nie wie, czy rozwój 0,535 to mało.
  Tabela „Skąd Twoja karta” jest bardzo dobra, a sam nagłówek nie.
- **Propozycja:** Przy każdym wskaźniku kolor i słowo (niski / średni / dobry) według progów z danych
  karty oraz dymek „co go podnosi” (tekst już jest w INSTRUKCJA rozdz. 3).
- **Pliki:** `panel_gracza/static/zakladki/ogolne.js` (karta_wynikow).

### [11] Inwestor widoczny dla ucznia także po wpłacie
**P2 · koszt S · balans: brak · w planie: nie**

- **Problem:** Po wpłacie (spłata debetu) Dashboard wygląda jak wcześniej. Uczeń nie wie, że przez 8 rund
  inwestor bierze 30% zysku ani ile rund zostało (zrzut `nauczyciel_r12_4D_po_inwestorze.png`).
  `inw.raport` jest w widoku (`gra/api/prezentacja.py:419`), ale go nie widać.
- **Propozycja:** Wiersz w Finanse ▸ Właściciel i na Dashboardzie: „Inwestor: wpłacił 20 000 zł, bierze
  30% zysku jeszcze przez N rund, dotąd wziął X zł”.
- **Pliki:** `panel_gracza/static/zakladki/wlasciciel.js`, `ogolne.js`.

### [12] Panel mistrza gry: wynik, miejsce i „inwestor wykorzystany” w widoku Decyzje
**P2 · koszt S · balans: brak · w planie: nie**

- **Cel:** Nauczyciel widzi gotówkę, status i alarm, ale nie widzi, kto tonie w rankingu, bez
  przełączania na Wyniki. Po użyciu inwestora link po prostu znika.
- **Propozycja:**
  - Kolumny „wynik (skum.)” i „miejsce” w tabeli Decyzje.
  - Przy firmie po inwestorze napis „inwestor: runda 6, 20 000 zł”.
- **Pliki:** panel `/mg/` (szablon i JS widoku Decyzje), `gra/api/` widok mistrza gry.

### [13] Ranking: majątek netto obok wyniku i zdanie „dlaczego”
**P2 · koszt S · balans: brak · w planie: B13 mówi o zgodności rankingu z majątkiem**

- **Cel:** „Czemu oni wygrali, skoro mają połowę naszych pieniędzy?” (2B: 62 tys. zł majątku wygrywa
  z botem 132 tys. zł).
- **Propozycja:**
  - W Wynikach (uczeń i mistrz gry) kolumna majątku netto obok wyniku.
  - Pod tabelą jedno zdanie: „Ranking liczy średnią kartę wyników ze wszystkich tygodni – liczy się
    zarabianie co tydzień, zadowolenie i rozwój, a nie sam stan konta”.
- **Pliki:** `ogolne.js` (wyniki), panel mistrza gry.

### [14] Menu w rundzie 1: podpis „od tygodnia 3” i jeden komunikat zamiast dwóch
**P3 · koszt S · balans: brak · w planie: nie**

- **Dowód:** nowicjusz R1, zrzut `nowicjusz_r01_lokal_menu.png`.
  - Wyszarzone „Wybierz” bez powodu.
  - Na Liście błędów dwie pozycje o tym samym („W rundzie 1 można wybrać tylko…” i „liczba dań może
    wzrosnąć najwyżej o 3…”).
  - „Popyt roczny 36 000” bez wyjaśnienia, czego dotyczy.
- **Propozycja:**
  - Podpis przy wyszarzonym przycisku „od tygodnia 3”.
  - Łączenie obu komunikatów w jeden.
  - „Popyt roczny” zamienić na „klientów w strefie na tydzień” albo dać dymek.
- **Pliki:** `panel_gracza/static/zakladki/oferta.js`, `gra/silnik/kuchnia/menu.py`.

### [15] Harpagon: kwota do oddania w złotych przy pożyczce
**P3 · koszt S · balans: brak · w planie: nie**

- **Dowód:** Nowicjusz R4 pożyczył 5000 zł i oddał 6381 zł po 5 rundach (+28%). Przy przycisku jest
  oprocentowanie na rundę, ale nie ma kwoty.
- **Propozycja:** W oknie pożyczki tekst na żywo „oddasz ok. X zł, jeśli spłacisz w terminie (N rund)”.
- **Pliki:** `panel_gracza/static/zakladki/harpagon.js`.

---

## 4. Nowe funkcje

### [16] „Dlaczego mój wynik się zmienił?” – automatyczny wniosek po rundzie
**P2 · koszt M · balans: brak · w planie: nie**

- **Cel:** Nowicjusz rozumiał rundy R3–R11, ale nie rozumiał R2 i R15, które zdecydowały o wyniku.
- **Propozycja:**
  - Na Dashboardzie po przeliczeniu 1–3 zdania z największych zmian składników karty: „Karta spadła
    z 0,44 do −2,48: koszt zakupu sprzętu 11 448 zł zamienił zysk w stratę”.
  - Dane są w tabeli „Skąd Twoja karta”; potrzebny ranking przyczyn i szablony zdań.
- **Pliki:** `gra/silnik/wyniki/` (wnioski), `gra/api/prezentacja.py`, `ogolne.js` (wnioski).

### [17] Refleksja drużyny po rundzie (dla nauczyciela)
**P3 · koszt M · balans: brak · w planie: nie**

- **Cel:** Gra uczy tylko wtedy, gdy uczeń nazwie, co poszło nie tak.
- **Propozycja:**
  - Przy „Wyślij decyzje” jedno opcjonalne pole „Co zmieniamy w tej rundzie i dlaczego?” (1–2 zdania).
  - Mistrz gry widzi odpowiedzi w panelu obok wyniku rundy i w eksporcie CSV, więc ma gotowy materiał na
    omówienie.
  - Opcja w ustawieniach gry: wymagane / opcjonalne / wyłączone.
- **Pliki:** model decyzji (`gra/silnik/decyzje.py` – pole tekstowe bez wpływu na silnik), `wyslij`
  w `ogolne.js`, panel i eksport mistrza gry.

### [18] Narzędzia mistrza gry dla drużyny w spirali
**P2 · koszt M · balans: mały (tylko gdy mistrz gry użyje) · w planie: nie (Z3 dał jednego inwestora)**

- **Cel:** 4D od R10 do R18 tonęła (debet ponad limit do 54 567 zł) i nie miała żadnej szansy. Mistrz gry
  po inwestorze nie ma narzędzi.
- **Propozycja** (do wyboru, pytanie 4):
  - **(a)** „Restrukturyzacja”: mistrz gry zamienia debet ponad limit na kredyt na N rund z wyższym
    oprocentowaniem. Wskaźnik zadłużenia karze dalej, ale firma może grać.
  - **(b)** Drugi inwestor na gorszych warunkach (np. 50% zysku).
  - **(c)** „Upadłość i restart”: firma zaczyna od nowa z kapitałem startowym, a jej karta za dotychczasowe
    rundy zostaje (wynik dalej się liczy jako średnia, więc nie da się na tym zyskać).
- **Pliki:** `gra/silnik/pieniadze/inwestor.py`, panel `/mg/` (prowadzenie), `gra/api/`.

### [19] Kontrola uczciwości: dziennik zmian decyzji dla mistrza gry *(eksperyment)*
**P3 · koszt M · balans: brak · w planie: nie**

- **Cel:** Uprawnienia działają (403 dla obcej drużyny, mistrz gry tylko odczyt). Nauczyciel nie widzi
  jednak, kto i kiedy zmienił decyzje drużyny ani czy jedno konto zmienia dwie drużyny (np. jeden uczeń
  zalogowany dwa razy).
- **Propozycja:**
  - Lista „zapis decyzji: osoba, godzina, zakładka” dla każdej drużyny w rundzie (już jest „kto wysłał”
    w składzie drużyny).
  - Ostrzeżenie, gdy ta sama sesja lub adres zapisuje w dwóch drużynach.
- **Pliki:** `gra/api/` (zapis decyzji), panel `/mg/`.

### [20] Tryb „podpowiedzi” dla pierwszych 3 rund *(eksperyment)*
**P3 · koszt M · balans: mały · w planie: nie**

- **Cel:** R1 prowadzi dobrze, ale od R2 uczeń zostaje sam z 13 zakładkami.
- **Propozycja:** Mistrz gry włącza tryb, w którym przez 3 rundy Dashboard pokazuje „3 rzeczy do sprawdzenia
  w tej rundzie” (np. R2: zatrudnij, sprawdź zamówienia, zaksięguj dokumenty). Teksty z INSTRUKCJA rozdz. 15
  („10 rad”).
- **Pliki:** `gra/api/prezentacja.py`, `ogolne.js`, ustawienia gry.

### [21] Okrojona dynamika pracowników, opinie na mapie, grupy klientów
**P3 · koszt L · balans: duży · w planie: tak – kandydaci z `dokumentacja/ROZNICE_LEVAS_STARY.md`**

- **Cel:** Optymalizator widzi, że płaca minimalna daje +0,01 (dźwignia za słaba, zadowolenie pracowników
  stoi na ok. 0,91). Opinie i grupy klientów dałyby uczniowi powód, żeby patrzeć na mapę.
- **Propozycja:** Potwierdzam kandydatów (4) dynamika pracowników, (7) opinie klientów na mapie
  i (2) grupy klientów w strefach. Najwięcej da (4) przy obecnym problemie z pensjami. Nie zgłaszam ich
  jako nowych.
- **Pliki:** wg `ROZNICE_LEVAS_STARY.md`.

### [22] „Zamknięcie firmy” jako świadoma decyzja *(do sprawdzenia w B6)*
**P3 · koszt S (pomiar) · balans: mały · w planie: B6 (lokale)**

- **Cel:** Wariant „od R11 bez ludzi i dostaw” daje −0,17 do −0,25, gorzej niż bezczynność od początku
  (czynsz i biuro dalej idą). Nie sprawdziłem wypowiedzenia najmu (`wypowiedz`, `gra/silnik/decyzje.py:9`).
- **Propozycja:** W B6 zmierzyć wariant z wypowiedzeniem. Jeśli bezczynność po zamknięciu daje ≈ 0, a gra
  trwa, to „zarób i zamknij” staje się strategią. Wtedy karta w rundach bez sprzedaży ≠ 0 (patrz pytanie 2).
- **Pliki:** `gra/balans/warianty.py` (nowy wariant).

---

## 5. Co działa dobrze – nie psuć

- **Runda 1 prowadzi ucznia.** Lista błędów po pierwszym zapisie mówi wprost: nie masz lokalu, menu puste,
  brak banku i biura. Nowicjusz wiedział, co zrobić.
- **„Skąd Twoja karta”.** Tabela z wpływem przyczyn (np. „Dania wyłączone z braku składnika 9,5% → −0,029”)
  to najlepsza rzecz dydaktyczna w grze.
- **Puste stanowiska z „+” i „Stań sam (właściciel)”** w Lokale ▸ Ludzie – czytelne od razu.
- **Urząd i sanepid** – teksty z humorem, a przy tym jasne („Mop i grafik na lodówce” wystarcza).
- **Humor w komunikatach** (kanapa, joga dla przedsiębiorców) – byle nie na Liście błędów jako fałszywy
  alarm (poz. 3).
- **Harpagon** jest ustawiony dobrze: nie jest exploitem (−0,01 do −0,03), a uczy ceny lichwy.
- **Elastyczność ceny zwykłego kebaba:** ceny × 0,8 → −0,1, × 1,3 → −0,3 do −0,4. Rozsądne.
- **Reklama się opłaca** (+0,01 do +0,11) – to dobry sygnał dla ucznia.
- **Kara za zapomnienie o decyzjach jest w dobrej proporcji.** 3C traci ok. 5 tys. zł i 1 miejsce, a kończy
  na 2. Zapisany szkic gra sam.
- **Panel mistrza gry:**
  - komunikat „Decyzje wysłało 3 z 4… drużyny bez wysłanych decyzji zagrają decyzjami zapisanymi do
    tej pory”;
  - „Gra jest wstrzymana – wznów ją, żeby zamknąć rundę”;
  - alarm z linkiem „przyślij inwestora” przy gotówce.
- **Cofnięcie rundy jest deterministyczne** – majątek 6 firm co do grosza ten sam. Nauczyciel może
  bezpiecznie naprawić pomyłkę.
- **Zmiana poziomu bota w trakcie gry** działa i ma widoczny skutek.
- **Uprawnienia:** 403 dla obcej drużyny, mistrz gry tylko do odczytu w drużynie z uczniami, uczeń bez
  dostępu do `/mg/`. Unikalne loginy kont.
- **Eksport CSV** (BOM, średnik, przecinek dziesiętny) otwiera się od razu w polskim Excelu.

---

## 6. „Za dobre” (i „za złe”) strategie dla części B

Do dopisania w inwentarzu B1 jako hipotezy (krok 9 planu). Porównanie z B4/B5 w ostatniej kolumnie.

| # | strategia | wynik w A | obszar | wobec B4/B5 |
|---|---|---|---|---|
| H-A1 | **premium z cenami × 1,2** | 0,69–0,96, 1. miejsce na 3/3 ziarnach; baza 0,34–0,49 | B7 (elastyczność ceny przy jakości 3★) | B4: premium 0,70, „przy 4 firmach wygrywa 7/10”. **Nowe:** podniesienie cen premium *dalej* poprawia wynik – popyt premium za mało czuły na cenę |
| H-A2 | **„nic nie rób” (bez lokalu, gotówka na lokacie)** | −0,019 na każdym ziarnie, 3. z 4 | B13 (karta przy zerowej sprzedaży) | **Nowe.** B4 tego nie mierzył. Bije aktywnych słabych (nowicjusz −0,30; tani −0,25…0,24) |
| H-A3 | **kredyt 50 tys. zł na rozwój** | 0,18 wobec 0,55 bez kredytu przy podobnym dochodzie i majątku | B11 / B13 (wskaźnik zadłużenia) | **Nowe** – pułapka odwrotna. Mianownik wskaźnika (`karta.py`) nie zawiera gotówki, więc kredyt trzymany na koncie karze od razu |
| H-A4 | **drugi lokal** | `planista_trudny` (2 lokale) −0,40 / 0,26 / −0,33; baza z 1 lokalem 0,34–0,49 | B6, poz. 1 | **Różnica z B4** (drugi lokal dominuje: 85% par, przy 4 firmach 100%). Mój wariant nie jest czystą parą: zmienia cały poziom kalkulatora, nie tylko liczbę lokali. Wspólny trop: koszt urządzania (środki < 10 tys. zł) w jednej rundzie ze stratą o wadze 1,0. Do zmierzenia parą z samą zmianą „drugi lokal *niewyposażony*” |
| H-A5 | **wypłaty właściciela** | 70–80 tys. zł wypłat: karta −0,005, majątek 32k wobec 112k | B13, pytanie 1 | **Nowe.** Ranking nie widzi wypłat. W klasie wygrała drużyna z 64 tys. zł wypłat |
| H-A6 | **płaca minimalna** | +0,01–0,015 | B9 | Zgodne z B5 (praca 23% przychodu). Dźwignia za słaba, żeby uczeń ją odczuł (poz. 21) |
| H-A7 | **monotoniczność poziomów „jak człowiek”** | klasa: 1A („dobry”) 5. z 6, za 2B i 3C („średni”) | B14 | B5: dobra > średnia w 92/100 par. U mnie jedna gra, nie para – sygnał, nie dowód. Razem z H-A4 warto sprawdzić, czy „dobry” częściej bierze drugi lokal |
| H-A8 | **reklama 10 emisji ulotek i plakatów** | +0,01…+0,11 | B10 | B4: reklama ponad przepustowość szkodzi agresywnemu. U mnie (1 lokal, zrównoważony) pomaga – sprawdzić nasycenie |

Nie powtarzam znanych z B4/B5: umowa zlecenie (składki w B9), mBank, e-Księgi24, higiena podstawowa,
polisy, jakość 2★, strategia agresywna jako pułapka.

---

## 7. Pytania do autora

1. **Czy wypłata właściciela ma obniżać kartę?** Dziś drużyna może „opróżnić firmę” (majątek 32 tys. zł
   wobec 112 tys. zł) prawie bez kary (−0,005). Realnie wypłata to nie koszt firmy, ale w grze o rozwój
   firmy uczy złego nawyku. Możliwości:
   - zostawić (decyzja dydaktyczna: zysk należy do właściciela);
   - majątek netto jako składnik rankingu;
   - wypłaty pomniejszają „rozwój”.
2. **Ile ma być warta firma bez sprzedaży?** Dziś ≈ 0, czyli lepiej niż aktywna słaba drużyna. Czy tydzień
   bez działającego lokalu (po rundzie 2) ma mieć np. stałe −0,3?
3. **Wskaźnik zadłużenia a gotówka z kredytu.** Czy gotówka ma być w mianowniku (kredyt leżący na koncie
   nie karze), czy kara ma zostać, bo „kredyt bierze się na inwestycję, a nie na konto”? Dziś kredyt nigdy
   się nie opłaca, a zakładka Bank go eksponuje.
4. **Drużyna w spirali:** restrukturyzacja, drugi inwestor czy upadłość z restartem (poz. 18)? Czy w ogóle
   ratować – może 12 rund „lekcji bankructwa” to też lekcja?
5. **Zakup sprzętu na karcie (poz. 1):** wariant (a) „amortyzacja do karty”, (b) dolna granica tygodnia
   czy (c) tylko ostrzeżenie? Od tego zależy, czy drugi lokal ma sens dla ucznia.
6. **Ludzie od tygodnia 2** (`dane/katalog.yaml:52`). W tygodniu przygotowawczym nie da się nikogo
   zatrudnić, więc pierwszy tydzień sprzedaży startuje z rekrutacją. Czy to celowe (rozruch), czy
   zatrudnienie ma się odblokować w tygodniu 1?

---

Proszę o zaznaczenie, które pozycje 1–22 wdrożyć (staną się U1, U2… w `POSTEP.md`), i odpowiedzi na
pytania 1–6. Pozycje z sekcji 6 trafią do inwentarza B1 jako hipotezy niezależnie od wyboru.

---

## 8. Odpowiedzi autora (3.11.2026)

1. **Wypłaty właściciela:** zostaje jak jest – wypłata nie obniża karty.
2. **Firma bez sprzedaży:** zostaje jak jest (≈ 0), a tygodnie ze stratą liczą się na minus – tak już działa.
3. **Kredyt:** gotówka wchodzi do mianownika wskaźnika zadłużenia → **U22**.
4. **Drużyna w spirali:** nie ratować – jeden inwestor na grę. Pozycja [18] pominięta.
5. **Zakup sprzętu na karcie:** tylko ostrzeżenie przed zakupem (wariant c), liczby karty bez zmian → **U1**.
   Wyjaśnienie dla porządku: −2,48 w R15 nowicjusza to sam wynik ekonomiczny (−11 448 zł ÷ 4615 zł),
   bo przy stracie karta = wynik ekonomiczny × 1,0; majątek netto w tej rundzie wzrósł (57 049 → 58 424 zł).
6. **Zatrudnianie:** od tygodnia 1 → **U23**.

Do wdrożenia: wszystkie pozycje 1–22 poza [18] oraz U22 i U23 – lista U1–U23 w `POSTEP.md`.
Pozycje U robione na gałęzi `analiza-a`.
