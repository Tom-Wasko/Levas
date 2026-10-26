# Praca bez nadzoru: 25.10.2026 21:15 → 26.10.2026 15:50

Dziennik i zasady samodzielnej pracy Claude nad planem implementacji (kolejne zadania z [`POSTEP.md`](POSTEP.md)).

## Zasady

- Kolejność: F2.3 → F2.4 … F2.8 → F3a.1 … → F3b … → F4 (według `notatki/Plan implementacji.md`).
- Po każdym zadaniu: pytest, ruff, wpis w `POSTEP.md`, commit `F…: …` i push.
- Nowe elementy gry zawsze z zakładkami **Decyzje** i **Wyniki**; prototyp mapy w F3a.3.
- Notatek (`notatki/`) nie zmieniam bez zgody – propozycje zmian trafiają do pytań.
- Pytania: tylko niedziela do 21:30 i poniedziałek 6:00–16:00. Powiadomienie push (aplikacja Claude,
  Remote Control) + okno pytania na ekranie. Zadanie, które czeka na odpowiedź, odkładam i robię kolejne,
  niezależne od niej.
- Przypomnienie (cron w sesji) co ok. 15 min wznawia pracę, także po odnowieniu limitu.
- 26.10 o 15:50 kończę: commit, push, podsumowanie, usunięcie przypomnienia.

## Otwarte pytania (czekają na odpowiedź)

1. **Gdzie jest kod starego Levasa?** Plan zakłada przeniesienie modułów i danych z `Pulpit/Levas/levas_gra`
   (strefy, lokale, sklepy, banki, podatki 2026, parki, kalendarz, PCG64), ale tego folderu nie ma na dysku,
   a repo `Tom-Wasko/Levas-stary` ma tylko notatki. Do czasu odpowiedzi: F2.5 (PCG64) piszę od zera,
   a dane do F3a biorę z notatek. (zadane: 25.10 21:50, do wysłania w poniedziałek o 6:00)

2. **Start gry i runda 1 (F2.7).** Przyjąłem: runda 1 = tydzień 5–11.10.2026 (początek roku akademickiego) i jest
   tygodniem przygotowań bez sprzedaży (jak w Revasie). Czy data i tydzień przygotowań są dobre? Zmiana to tylko
   `rundy.kalendarz.start` w `dane/katalog.yaml`. (zadane: 25.10 22:20, do wysłania w poniedziałek o 6:00)

3. **Logowanie kontem Microsoft (F3a.1).** Kod jest gotowy, ale potrzebna jest aplikacja zarejestrowana
   w Microsoft Entra ID szkoły (identyfikator klienta, sekret, identyfikator dzierżawy) – to zrobi administrator
   szkolnego Microsoft 365 albo Ty, jeśli masz dostęp. Czy mam przygotować krótką instrukcję krok po kroku?
   Do tego czasu działa własny login i hasło. (zadane: 26.10 0:40, do wysłania w poniedziałek o 6:00)
4. **Czas właściciela (F3a.7).** Przyjąłem 20 h na rundę (tydzień), tyle samo dla każdej drużyny – firma ma jednego
   właściciela, więc liczba osób w drużynie nie zmienia puli. Na razie zużywa ją tylko odbiór osobisty w dyskontach
   (1–1,5 h za dzień zakupów), później pracuj.pl i parki. Czy 20 h jest dobre i czy pula ma rosnąć z liczbą osób
   w drużynie? (zadane: 26.10 5:30, do wysłania w poniedziałek o 6:00)
5. **Agencja pracy (F3a.8).** Przyjąłem: pracuj.pl – kandydaci 1–2★, 150 zł + 2 h czasu właściciela;
   agencja – 2–3★, koszt = koszt rekrutacji kandydata; headhunter (od rundy 4) – 3★, 3 × koszt rekrutacji, a za
   podkupienie 50% oferowanej pensji. Limit 3 nowych osób na rundę, okres wypowiedzenia 2/4/13 rund (staż od 0/26/156
   rund). Staż liczę od zatrudnienia w grze – notatki mówią o „losowym stażu” kandydatów w puli; czy kandydaci
   mają przychodzić z losowym stażem (wtedy ten staż liczy się do okresu wypowiedzenia)? Czy kwoty i gwiazdki pasują?
   (zadane: 26.10 5:45, do wysłania w poniedziałek o 6:00)
6. **Banki (F3a.9).** Przyjąłem 6 banków z mapy: Crédit Agricole (kredyt na start bez historii, 11,9%),
   PKO BP (inwestycyjny pod zastaw 7,9%, do 70% wartości), Pekao (leasing 7,5%, wpłata 10%), ING (lokaty do 4%),
   mBank (konto i terminal 0 zł, prowizja 0,79%), Santander (limit 40 000 zł, 16,9%). Kwoty to mój szacunek na 10.2026.
   „Historia firmy” = 4 rundy od otwarcia pierwszego lokalu; 70% sprzedaży płacone kartą; 3 rundy bez raty → bank
   przejmuje zastaw (kupiony lokal staje się wynajmowany). Czy banki, oprocentowanie i te zasady pasują?
   (zadane: 26.10 6:05)

7. **Harpagon (F3a.10).** Przyjąłem: pożyczka 500–20 000 zł, 5% na rundę (tydzień) od całego długu, termin 4 rundy;
   po terminie: 1. runda – przypomnienie, od 2. – odsetki karne 10%, od 3. – co rundę jedna losowa wizyta (szkody
   800–3000 zł w KPiR jako „Naprawa szkód w lokalu”, albo atrakcyjność lokali −30% w tej rundzie, albo odejście
   losowego pracownika bez wypowiedzenia). Dług u Harpagona nie wchodzi do wskaźnika zadłużenia w karcie wyników
   i boty z niego nie korzystają. Czy te wartości i zasady pasują? (zadane: 26.10)
8. **Księgowość JDG (F3a.11).** Przyjąłem: wszystkie ceny w danych są brutto (VAT wydzielany z kwoty, także opłaty
   banków i czynsz); rozliczenie VAT/PIT/ZUS co rundę (tydzień), nie co miesiąc; zdrowotna od dochodu tej rundy,
   minimum 324,41 zł/mies.; ZUS społeczny preferencyjny 420,86 zł/mies. po 26 rundach ulgi (czyli w grze na 26 rund
   go nie ma); kwoty ZUS 2026 z pamięci; lokal, działka i budowa budynku bez VAT; próg amortyzacji liczony od brutto.
   Czy tak może zostać? (nie wysłane – okno pytań minęło; zapisane 26.10 18:25)
9. **Biura rachunkowe i samodzielna księgowość (F3a.13).** Przyjąłem:
   - 5 biur (ceny brutto/mies., przeliczane na tydzień): J.K.Ś. 690 zł do 80 dok. + 4,92 zł, 4 osoby w kadrach
     w cenie, bez błędów; Pod Trybunałem 6,15 zł/dok., min. 246 zł, ryzyko 3%; Pani Halinka 369 zł do 40 dok.
     + 7,38 zł, ryzyko 6%; e-Księgi24.pl 3,69 zł/dok., min. 123 zł, ryzyko 12%, **bez OC** (błąd = mandat 200 zł);
     Debet & Kredyt 984 zł bez limitu, bez błędów; kadry 18–74 zł za osobę,
   - samodzielnie: deklaracje za rundę składa się w następnej (wtedy też jest płacony VAT/PIT/zdrowotna),
     mandat 200 zł za każdą błędną deklarację (różnica od 1 zł – także nadpłata, z korektą do poprawnej kwoty),
     500 zł za niezłożone; błędne zapisy w KPiR tylko wyjaśniane, bez kary; czas właściciela za księgowanie
     niepobierany; ostatnia runda rozliczana od razu (nie ma rundy na deklarację),
   - do złożenia deklaracji drużyna nie widzi KPiR, podatków i dochodu netto rundy (karta wyników tak),
   - w deklaracji JS podpowiada stawkę VAT jednym wyborem na dokument (faktura z kilkoma stawkami – stawka
     przeważająca, poprawna kwota VAT i tak jest w deklaracji).
   Czy ceny, kary i zasady pasują? (zapisane 26.10)
10. **Panel mistrza gry (F3a.14).** Przyjąłem:
   - zamykanie o ustalonej godzinie = tygodniowe terminy (dzień + godzina, np. wt 8:00 i czw 8:00); runda
     zamyka się w pierwszym terminie po zamknięciu poprzedniej (zamknięta wcześniej ręcznie albo przez
     wszystkie drużyny – następny termin liczony od tej chwili); potrzebna komenda `zamykaj_rundy` co kilka
     minut (Harmonogram zadań) – serwer WWW sam z siebie nic nie uruchamia,
   - pauza blokuje zmianę i wysyłanie decyzji oraz zamykanie rundy (ręczne i z harmonogramu), cofnięcie
     rundy działa; po wznowieniu termin, który minął w czasie pauzy, nie zamyka rundy od razu,
   - mistrz gry ogląda drużyny **z uczniami** tylko do odczytu (nawet przez API); drużyny bez uczniów
     (i gra lokalna) prowadzi dalej sam – inaczej nie dałoby się grać na jednym komputerze,
   - poziom botów zapisany i widoczny, ale **bez wpływu** do F4.4 – próba mnożników (ilość zakupów, reklama)
     dawała odwrotne wyniki (łatwy bot zarabiał najwięcej, bo strategie przesadzają z zapasami i reklamą),
     więc poziomy trzeba zrobić razem z poprawą botów,
   - CSV: ranking (miejsce, firma, bot, średni wynik działalności, dochód razem, gotówka, zadłużenie, lokaty,
     pracownicy) i wyniki firm w każdej rundzie (przychody, koszty, dochód netto, gotówka, zadłużenie, wynik
     działalności); średnik i przecinek dziesiętny pod polskiego Excela.
   Czy tak może zostać? (zapisane 26.10)

## Odłożone zadania

_brak_

## Dziennik

- 25.10 21:15 – start; plan zaktualizowany (prototyp mapy w F3a.3); zaczynam F2.3 (pydantic + grosze).
- 25.10 21:20 – F2.3 gotowe (`95bd126`): pydantic, grosze, testy hypothesis; wyniki botów bez zmian. Start F2.4.
- 25.10 21:27 – test powiadomień: Remote Control połączony, ale push **nie wysłany** – „mobile push is disabled in /config” (do włączenia przez użytkownika w `/config`). Wracam do F2.4.
- 25.10 21:41 – test powiadomień po włączeniu „Push when Claude decides” w `/config`: **wysłane** (powiadomienie w terminalu + push na telefon). Wracam do F2.4.
- 25.10 21:35 – F2.4 gotowe (`57299d7`): dane w YAML ze schematami, `python -m silnik.dane sprawdz`, liczby gry z kodu do danych. Użytkownik poszedł spać (okno zminimalizowane). Start F2.5.
- 25.10 21:45 – F2.5 gotowe (`272d39a`): strumienie PCG64 (od zera, pytanie 1 nadal otwarte). Start F2.6 (kebab).
- 25.10 22:05 – F2.6 gotowe (`80cf033`): kebab w danych, zakładkach i szablonach. Decyzje (do przejrzenia):
  - dane Revasa przeniesione do `gra/dane_revas/` – testy mechaniki liczą na liczbach z prawdziwych gier, więc działają na nich; gra używa `dane/` (kebab),
  - identyfikatory silnika i klucze danych zostają z Revasa do kroku 3a (słownik w `gra/README.md`), żeby nie mieszać przebranżowienia z przebudową,
  - **odstępstwo od planu:** sprzęt (rożen, frytownica, lodówka) nadal kupuje się na stanowisko kuchenne, nie do lokalu – przeniesienie do lokalu razem z gotowym lokalem (F2.7) albo z F3a,
  - liczby dań (popyt, czas kuchni 3–5 min/porcję, kasa 0,3–1,2 min, sezonowość studencka, pensje 4810–5800 zł), ceny sprzętu i hurtowe ceny składników – moje założenia z `zrodlo` „założenie F2.6”, do kalibracji w kroku 5; receptury i ceny dań – z notatki „Menu i składniki” (środek przedziału),
  - 3 fikcyjni dostawcy: Piekarnia Koziołek (pieczywo), Mięsny Bazar Zamojski (mięso, warzywa, sosy) – taniej, węższa oferta; Hurtownia Lubelska Spiżarnia – wszystko,
  - nazwy mediów, szkoleń i firm szkoleniowych przerobione na gastronomię (fikcyjne), liczby z Revasa bez zmian; `zalozenia.yaml` bez zmian,
  - gra botów (12 mies.): dochód netto 0,45–0,78 mln zł na firmę (Revas: 0,8–2,4 mln) – rząd wielkości ten sam, balans przy rundach tygodniowych.
- 25.10 22:20 – F2.7 gotowe (`35f28eb`): rundy tygodniowe. Decyzje (do przejrzenia):
  - kalendarz w danych (`katalog.yaml` → `rundy.kalendarz`), silnik działa na tygodniach i na miesiącach; Revas (`dane_revas/`) nadal miesięczny – jego testy i wyniki bez zmian,
  - kwoty w danych zostają **miesięczne** (pensje w umowach, czynsz, utrzymanie) – silnik księguje je na tydzień (× 12/52); oprocentowanie roczne / 52; okresy lokat i kredytów w tygodniach (kredyt do 26 tyg.); koszty jednorazowe (zakupy, rekrutacja, premie, księgowość za dokument, emisje reklam) bez skalowania,
  - **założenie:** start 5.10.2026 (poniedziałek, początek roku akademickiego) – do pytania w poniedziałek; runda 1 nadal tydzień przygotowań bez sprzedaży (jak w Revasie),
  - sezonowość: tydzień należy do miesiąca swojego czwartku; popyt tygodniowy = roczny / 52 × sezonowość miesiąca,
  - ceny dostawców: z danych w październiku, potem losowane co tydzień (ta sama zmienność co w Revasie co miesiąc),
  - gotowy lokal na start: kuchnia (rożen, frytownica, lodówka) i kasa (kasa fiskalna, lada, tablica menu), za darmo; sprzęt nadal należy do stanowisk, nie do lokalu (do F3a); darmowy sprzęt można sprzedać,
  - etat i sprzęt 40 h / tydzień, kapitał 100 000 zł, wynik ekonomiczny = dochód / 4615 (20 000 × 12/52),
  - gra botów (26 tyg.): dochód netto od −74 tys. (agresywny marketing – reklamy jednorazowe nie są skalowane, więc tygodniowo są drogie) do +267 tys. (premium); kalibracja w kroku 5,
  - strona gracza: nazwy tygodni („Tydzień 3 (19–25.10)”, skróty T1…T26) w nawigatorze i na wykresach, koszty utrzymania „/ tydz.”, liczba rund i kapitał na stronie startowej z danych.
- 25.10 22:22 – start F2.8 (podstawowy panel mistrza gry).
- 25.10 22:25 – F2.8 gotowe: podstawowy panel mistrza gry pod `/mg/` (link z listy gier). Decyzje (do przejrzenia):
  - bez logowania (tryb deweloperski, jak w planie) – każdy z dostępem do strony otworzy panel; role i konta w F3a.1,
  - nowa gra: drużyny (domyślnie „Drużyna 1–4”), rundy, kapitał startowy (nowa opcja gry `kapital_startowy`, puste = z danych), boty tak/nie z wyborem strategii (firma bota nazywa się jak strategia, np. „Tani Kebab Nocny”); kredyt i ceny dostawców w „Więcej ustawień”,
  - w grze zakładki **Decyzje** (kto wysłał, zamknięcie rundy także bez decyzji wszystkich – drużyna gra wtedy zapisanym szkicem, cofnięcie, plik gry; odświeżanie co 15 s) i **Wyniki** (ranking wg średniej karty wyników z rund od 2 jak w Revasie, dochód, gotówka, zadłużenie, wykresy),
  - „podgląd drużyn” = przycisk „Strona firmy” otwiera stronę gracza tej firmy – mistrz gry widzi wszystko, ale może też zmieniać decyzje (do czasu ról w F3a.1),
  - przeglądarka (rozszerzenie Chrome) nie była połączona – stronę sprawdziłem testami Django i uruchomieniem skryptu panelu w node na sztucznym DOM; warto raz kliknąć `/mg/` ręcznie,
  - **koniec kroku 2**: test `test_koniec_kroku_2_cala_gra` – drużyna + 5 botów grają 26 tygodni, mistrz gry zamyka rundy przez API; pytest i ruff na zielono. Popyt nadal algorytmem Revasa (zgodnie z planem).
- 26.10 0:40 – F3a.1 gotowe: konta i role (`konta/`, django-allauth 65). Decyzje **do potwierdzenia**:
  - logowanie wymagane na każdej stronie; API bez logowania odpowiada 401, strony przekierowują na `/konta/login/`,
  - rola mistrza gry = grupa `mistrz_gry` (albo superużytkownik), każde inne konto to uczeń,
  - konta z własnym loginem zakłada mistrz gry (komenda `manage.py konto` albo panel Konta = panel administracyjny Django `/admin/`); samodzielna rejestracja wyłączona (`LEVAS_REJESTRACJA=1` włącza),
  - konto Microsoft: pierwsze logowanie samo zakłada konto ucznia; dostęp ogranicza dzierżawa szkoły (`LEVAS_MS_TENANT`) – pytanie 3,
  - drużyny: model `gry.Druzyna` (gra + firma + uczniowie); w F3a.1 uczniów dopisuje się w panelu Konta (Gry → gra → drużyny), wygodne przypisywanie w panelu mistrza gry w F3a.2,
  - uczeń widzi tylko gry i firmy swoich drużyn (strona i API – 403), nie zakłada gier, nie zamyka ani nie cofa rund, nie pobiera pliku gry (są w nim decyzje innych drużyn),
  - mistrz gry nadal może zmieniać decyzje drużyn ze strony firmy – „tylko do odczytu” z [[Zarys aplikacji]] dojdzie w F3a.14,
  - **gra na własnym komputerze** (`start.bat` → `graj`) loguje się sama na lokalne konto mistrza gry `lokalny`, tylko dla zapytań z tego komputera – żeby gra jednoosobowa działała jak dotąd; sam `runserver` wymaga logowania,
  - sprawdzone: pytest (72) i ruff na zielono, strony przez curl na żywym serwerze (logowanie, przekierowania, 401, gra lokalna).
- 26.10 0:30 – F3a.2 gotowe: drużyny. Decyzje **do potwierdzenia**:
  - uczeń jest w jednej drużynie danej gry (w innej grze może być w innej); limit 4 osób pilnuje API, zakładka i panel Konta,
  - uczniów dopisuje mistrz gry w nowej zakładce **Drużyny** gry (obok Decyzji i Wyników) – lista wolnych kont + „Dodaj”, ✕ usuwa,
  - konta zakładane hurtem z listy imion i nazwisk: login `imie.nazwisko` bez polskich znaków (`ala.nowak2`, gdy zajęty), losowe hasło 8 znaków bez mylących znaków (l/1, o/0), widoczne **tylko raz** w oknie z drukiem; potem tylko „nowe hasło” (nie dla kont mistrza gry),
  - decyzje wysyła **dowolna** osoba z drużyny za całą drużynę (bez głosowania / zatwierdzania przez kapitana); strona pokazuje, kto ostatnio zapisał i kto wysłał,
  - dwie osoby naraz: zapis na starszej wersji niż ostatni zapis **innej** osoby → 409 z komunikatem „Ala Nowak zmienia teraz decyzje drużyny…”, strona wczytuje aktualne decyzje (swoje szybkie zapisy nigdy nie kolidują),
  - strona drużyny co 20 s pyta o stan (`/stan`) i odświeża się sama po zmianie kolegi, wysłaniu albo przeliczeniu rundy – ale nie w trakcie wpisywania,
  - drużyna bez uczniów: prowadzi ją mistrz gry (jak dotąd); w Decyzjach link „dopisz uczniów”,
  - sprawdzone: pytest (79) i ruff na zielono; panel mistrza gry (Decyzje, Drużyny, okno z hasłami) i strona drużyny obejrzane w Chrome bez okna (zrzuty ekranu przez DevTools, osobna kopia bazy) – bez błędów JS.
- 26.10 1:00 – F3a.3 gotowe: strefy, lokale i prototyp mapy miasta. Decyzje **do potwierdzenia**:
  - nowe gry są domyślnie **z lokalami** (drużyna zaczyna bez lokalu i stanowisk); stare zapisy gier i opcja
    „Lokale: nie” w panelu mistrza gry – gotowy lokal na start jak dotąd,
  - mapa napisana od zera (pytanie 1 – brak `levas_gra`): 10 stref Lublina (Stare Miasto, Centrum, Akademickie,
    LSM/Czuby, Politechnika, Dworzec, Czechów, Felin, Zemborzyce, Zygmuntowskie), 38 lokali z fikcyjnymi nazwami
    (bez prawdziwych marek), budynki: bank, ratusz, urząd skarbowy, dostawcy, agencje reklamowe, szkolenia, park, zalew,
  - ceny: czynsz, cena kupna i media według stawek stref × metraż (moje założenia, `zrodlo` w danych) – kalibracja w kroku 5,
  - najem: kaucja = 2 × czynsz miesięczny, potem czynsz co tydzień (KPiR); kupno, kaucja i budowa to ruchy na rachunku,
    nie koszty KPiR (dlatego w „Kosztach decyzji” lokal = 0 zł); kupiony lokal nie liczy się jeszcze do majątku –
    tylko sprzęt z zestawu (bilans w F3a.6),
  - gotowy lokal działa od razu (przy najmie sprzęt wynajmującego – nie do sprzedania), lokal do urządzenia – od
    następnej rundy (adaptacja w KPiR), działka – budowa 3–4 rund w równych ratach, potem lokal bez sprzętu,
  - stanowiska tylko w działających lokalach, tyle ile miejsc (kuchnia / kasa); ponad limit – czerwony błąd,
  - dwie drużyny chcą ten sam lokal w jednej rundzie – dostaje firma wcześniej w (losowej) kolejności rundy,
  - kolejny lokal co 3 rundy; wyprowadzka, sprzedaż lokalu i zwrot kaucji – później (F3a.6 / krok 5),
  - boty biorą jeden gotowy lokal w najmie (wybór według strategii),
  - mapa to prototyp obok menu (pierwsza pozycja „Mapa miasta”, `#mapa`): izometryczny SVG, kliknięcie budynku →
    zakładka, lokalu → opis i Wynajmij / Kup, własnego lokalu → zakładki firmy,
  - gra botów 26 tyg. z lokalami: dochód netto od −69 tys. (agresywny) do 242 tys. (premium) – podobnie jak bez lokali,
  - sprawdzone: pytest (89) i ruff na zielono, mapa i zakładka Lokale obejrzane w Chrome bez okna (zrzuty ekranu).
- 26.10 1:20 – F3a.4 gotowe: popyt strefowy. Decyzje **do potwierdzenia**:
  - każda strefa ma własną pulę klientów na danie i dzień: popyt roczny dania / 52 × sezonowość dania × pula strefy ×
    miesiąc strefy (uczelnie latem puste, Zemborzyce latem pełne) × kalendarz × dzień tygodnia × szum ±8% –
    sezonowość liczona podwójnie (danie i strefa) celowo,
  - wybór lokalu – model logitowy: cena względem ceny strefy (Stare Miasto ×1,15, Akademickie ×0,88) z wrażliwością
    strefy, jakość, odległość między strefami (zasięg 3 pola mapy), zadowolenie klientów firmy, wyposażenie, reklama
    (mnożnik reklamy z Revasa zostaje do F3b); opcja zewnętrzna A0 = 1 – część klientów zawsze idzie poza grę,
  - pule dobrane tak, że lokal 2★ po cenie strefy w Centrum bez konkurencji ma 400–1500 kebabów tygodniowo (rząd
    wielkości firmy z Revasa); popyt na lokal często przekracza moc małych lokali – zachęta do rozbudowy,
  - obsługa dzień po dniu: godziny pracowników i sprzętu dzielone równo na 7 dni (grafiki dzienne – później); zapasy
    schodzą z tygodniowego magazynu (dostawy na dni – F3a.5+),
  - sprzedaż od rundy 2 jak w Revasie; stali konkurenci z Revasa (`konkurenci_stali`) w grze z lokalami pominięci –
    konkurencją są drużyny i boty, a resztę rynku zastępuje opcja zewnętrzna,
  - prognoza dla drużyny: konkurenci z cenami z poprzedniej rundy i jakością 2★ (prawdziwej jakości nie widać); w
    wynikach firmy jakość/oferta dania = lokal z największym popytem,
  - kalendarz na razie podstawowy (9 wydarzeń z humorem: Wszystkich Świętych, 11 listopada, święta, Sylwester, sesja,
    przerwa międzysemestralna, Walentynki); pełny kalendarz miejski – F3b.9,
  - boty planują stanowiska i kasjerów na najmocniejszy dzień tygodnia (szczyt strefy),
  - nowa zakładka **Klienci i strefy** w menu pod Lokalami (Decyzje + Wyniki), szacunek klientów na kafelkach lokali,
  - sprawdzone: pytest (96) i ruff na zielono, `sprawdz` danych, zakładka wyrenderowana na prawdziwym widoku gry
    botów (bez błędów, bez `undefined`/`NaN`); gra 4 botów 26 tyg. – ok. 6 s.
- 26.10 5:00 – F3a.5 gotowe: menu i świeżość. Decyzje **do potwierdzenia**:
  - świeżość (partie, terminy, chłodnia) działa tylko w grze z lokalami; gra bez lokali i dane Revasa – jak dotąd,
  - magazyn i pojemność chłodni/zamrażarki są wspólne dla całej firmy (suma sprzętu ze wszystkich lokali), nie
    osobno dla lokalu; suchy magazyn bez limitu,
  - terminy i litry składników (bułka 2 dni, warzywa 3, mięso 4, surówki 3, sosy 3 tyg., mrożonki miesiące) oraz
    pojemności: szafa chłodnicza 600/800/1000 l, zamrażarka 250/300/400 l (wg jakości) – moje założenia, `zrodlo` w danych,
  - nowe składniki: Pita mrożona i Mięso kebab mrożone – zamienniki używane dopiero po świeżych, kara −1★ jakości
    składnika (poniżej 1★ nie schodzi); ceny i opakowania mrożonek – moje założenia,
  - jakość dania = 0,5 składniki + 0,3 kucharze + 0,2 sprzęt (`dane/mapa/menu.yaml`), liczona raz na rundę,
  - danie, któremu rano brakuje składnika, wypada z menu na ten dzień; połowa jego klientów (`zmiana_dania: 0.5`)
    zamawia inne danie (proporcjonalnie do popytu), reszta odchodzi,
  - nadmiar dostawy ponad pojemność chłodni – przepada od razu (powód „nie zmieściło się”),
  - zamówienia w zakładce Dostawcy mają kolumny dni (Pn…Nd); „Zamów automatycznie” rozkłada dostawy jak boty:
    chłodzone i mrożone co 3 dni, krótkoterminowe co termin,
  - boty zamawiają według prognozy popytu, nie mocy obsługi – przy dużym popycie (bot agresywny) mięso się psuje
    (do ok. 9 tys. zł strat tygodniowo); poprawię w kalibracji (krok 5) albo przy F3a.7 (grafiki),
  - sprawdzone: pytest (102) i ruff na zielono, `sprawdz` danych, zakładki Magazyn i świeżość oraz Dostawcy
    wyrenderowane na widoku prawdziwej gry (bez `undefined`/`NaN`).
- 26.10 5:20 – F3a.6 gotowe: dostawcy i sprzęt. Decyzje **do potwierdzenia**:
  - lista dostawców z notatki „Elementy mapy” (prawdziwe marki: Biedronka, Lidl, Stokrotka, Makro, Selgros,
    Eurocash) + fikcyjny producent mięsa „Rożen” z Łęcznej i Piekarnia Koziołek; dawni Mięsny Bazar Zamojski
    i Hurtownia Lubelska Spiżarnia usunięte (ich ceny są bazą nowych),
  - ceny względem dawnej hurtowni: dyskonty 0,88–0,97 (tylko ★ i ★★), Makro 1,0, Selgros ok. 1,02 (taniej mięso),
    Eurocash ok. 0,99 (bez hummusu i falafla), producent 0,97 dawnego mięsnego (★★ i ★★★) – kalibracja w kroku 5,
  - dni dostaw: Makro pn/czw, Selgros wt/pt, Eurocash pn/śr/pt, producent wt/pt, piekarnia i dyskonty codziennie;
    dowóz: Makro 79 zł (gratis od 1000 zł), Selgros 69 zł (od 900), Eurocash 89 zł (od 1200), piekarnia 15 zł
    (od 150); producent – minimum 800 zł za dostawę, od rundy 3,
  - dyskonty: odbiór osobisty (1–1,5 h czasu właściciela za dzień zakupów – na razie tylko liczone i pokazane,
    ograniczenie czasu właściciela w F3a.7), limit 4 opakowania składnika dziennie, gazetka: 2–3 składniki
    taniej o 10–35%, losowane co tydzień,
  - zamówienie na dzień bez dostaw – odrzucone (czerwony błąd), ponad limit dyskontu – obcięte, poniżej minimum –
    cała dostawa odrzucona; opłata za dowóz to koszt w KPiR („Koszt dostawy: …”),
  - planowanie (boty i „Zamów brakujące”) pomija dyskonty i dostawców, u których dostawa nie osiąga minimum –
    w dyskontach drużyna kupuje ręcznie,
  - środki trwałe (tylko gra z lokalami): próg 10 000 zł netto, amortyzacja liniowa od rundy po zakupie
    (stawka roczna / 52): lokal i budynek 2,5%, grunt 0%, sprzęt i wyposażenie 20%; zakup to ruch na rachunku,
    odpis to koszt w KPiR bez ruchu gotówki; obecnie środkami trwałymi są w praktyce tylko kupione lokale, działki
    i budynki (sprzęt i wyposażenie kosztują mniej niż 10 000 zł); majątek do rozwoju firmy – bez zmian
    (lokal się do niego nie wlicza), sprzedaż lokalu – później,
  - sklepy przy wyposażeniu (WiFi – OBI, dystrybutor wody – Castorama, stoliki – IKEA, telewizor – Jula);
    na mapie jeden budynek „Park handlowy” zamiast osobnych sklepów; okna w barwach marek – krok z grafiką,
  - nowa zakładka **Inwestycje → Środki trwałe** (Decyzje + Wyniki), plan dostaw i opłaty w zakładce Dostawcy,
  - sprawdzone: pytest (111) i ruff na zielono, `sprawdz` danych, zakładki Dostawcy, Środki trwałe, Wyposażenie
    i Dashboard wyrenderowane na widoku prawdziwej gry (bez `undefined`/`NaN`); straty botów po zmianie dostawców:
    agresywny ok. 7,6 tys. zł tygodniowo (było ok. 9 tys.).
- 26.10 5:30 – F3a.7 gotowe: czas właściciela. Decyzje **do potwierdzenia** (pytanie 4):
  - pula 20 h na rundę, niezależna od liczby osób w drużynie, nie przechodzi na następną rundę,
  - godziny zużywane po kolei (dzień, dostawca); dzień zakupów w dyskoncie, na który nie starcza godzin –
    odrzucony w całości, czerwony błąd w zakładce Dostawcy,
  - nowa zakładka **Czas właściciela** (Decyzje + Wyniki) w menu pod „Magazyn i świeżość”; pracuj.pl (F3a.8)
    i parki (F3b.1) dopiszą się do tej samej puli.
- 26.10 5:45 – F3a.8 gotowe: agencja pracy i rynek pracy. Decyzje **do potwierdzenia** (pytanie 5):
  - kanały: pracuj.pl (1–2★, 150 zł + 2 h czasu właściciela), agencja (2–3★, koszt rekrutacji), headhunter
    (od rundy 4, 3★, 3 × koszt rekrutacji; podkupienie: 50% oferowanej pensji, płatne w rundzie przyjęcia oferty),
    bez wskazania kanału – najtańszy dostępny; kandydat bez żadnego kanału nie jest widoczny,
  - wspólna pula: kilka drużyn chce tego samego kandydata → wygrywa wyższa pensja, remis – losowanie; zwolniony wraca
    do puli; kandydaci z puli dostępni od razu,
  - limit 3 nowych osób na rundę (zatrudnienia + oferty podkupienia; zatrudnienia mają pierwszeństwo),
  - podkupienie: pracownik przyjmuje najwyższą ofertę wyższą od pensji i kontroferty; kontroferta pracodawcy
    w tej samej rundzie (oferty widać na żywo, gdy druga drużyna zapisze decyzje), wygrana kontroferta = nowa pensja;
    odejście po okresie wypowiedzenia (umowa o pracę 2/4/13 rund wg stażu, zlecenie – od razu), w tym czasie nie można
    go zwolnić; brak wolnego stanowiska u nowego pracodawcy w dniu przejścia → osoba wraca do puli,
  - boty nie podkupują; staż liczony od zatrudnienia w grze (bez losowego stażu z puli – pytanie 5),
  - nowa zakładka **Rynek pracy** (Decyzje: kanały, oferty dla moich pracowników + kontroferta, staż i okres
    wypowiedzenia, headhunter; Wyniki: zatrudnieni z kanałem i kosztem, licytacje, oferty, odejścia i przyjścia)
    w menu HR; w oknie zatrudnienia wybór kanału rekrutacji.
- 26.10 6:05 – F3a.9 gotowe: banki. Decyzje **do potwierdzenia** (pytanie 6):
  - 6 banków (`dane/mapa/banki.yaml`), każdy z inną najlepszą ofertą; konto firmowe w jednym banku, lokaty, kredyty
    i leasing w dowolnych; opłaty i oprocentowanie – szacunek na 10.2026, do kalibracji w kroku 5,
  - terminal: abonament + prowizja od 70% sprzedaży (część płacona kartą),
  - kredyt na start bez historii; obrotowy i inwestycyjny dopiero po 4 rundach od otwarcia pierwszego lokalu;
    jeden aktywny kredyt danego rodzaju w jednym banku; inwestycyjny wymaga zastawu (kupiony lokal albo kupiony sprzęt,
    do 70% wartości netto),
  - brak środków na ratę (gotówka + wolny limit): odsetki doliczone do długu, stopa karna 19%, rata do zaległości,
    spłacana razem z następną; po 3 rundach bank przejmuje zastaw po 80% wartości netto, nadwyżka wraca na konto,
    przejęty lokal firma dalej wynajmuje (czynsz z danych lokalu albo 0,6% ceny miesięcznie),
  - leasing: sprzęt od razu na stanowisku, do wykupu własność banku (nie do sprzedania, bez amortyzacji), wpłata
    i raty annuitetowe w koszty, wykup 1% ceny; 3 zaległe raty → bank zabiera sprzęt,
  - limit w koncie z wybranego banku, debet ponad limit – odsetki karne; tryb Revasa bez zmian,
  - zakładka **Finanse → Bank** w grze z lokalami: Decyzje (kafelki banków z najlepszą ofertą, porównanie, lokaty,
    kredyty z zastawem, leasing, limit) + nowe Wyniki (opłaty, raty, leasing, przejęcia, odrzucone decyzje);
    test `test_banki.py`.

26.10 – F3a.10 gotowe: Harpagon (do potwierdzenia – pytanie 7):
  - pożyczka poza KPiR: gotówka i spłata tylko na rachunku (operacje `poza_ksiegami`), odsetki doliczane do długu
    bez ruchu gotówki; jedna pożyczka naraz; spłata przed nową pożyczką w tej samej rundzie,
  - presja: runda terminu – „życzenia”, potem przypomnienia (3 teksty), odsetki karne od 2. rundy po terminie,
    wizyty od 3. (losowane z wag, strumień `harpagon`), komiczne historie z Harpagonem i Mistrzem Jakubem,
  - odpływ klientów zrobiony jako mnożnik atrakcyjności lokali ×0,7 (nie dokładnie −30% gości przy konkurencji),
  - pracownik odchodzi od razu, bez odprawy, wraca do puli kandydatów; wizyta „pracownik” tylko gdy jest kto odejść,
  - dług nie wlicza się do zadłużenia w karcie, boty nie pożyczają; kantor „U Harpagona” na mapie przy dworcu (8,12),
  - zakładka **Finanse → Harpagon** (Decyzje + Wyniki), test `test_harpagon.py`.

26.10 18:20 – koniec pracy (po 15:50): F3a.11 przerwane w połowie – silnik, dane i testy gotowe (142 testy
  przechodzą), zakładka `podatki.js` napisana, ale nie zarejestrowana; pytanie 8 zapisane, nie wysłane.
  Zadania cron usunięte. Notatki bez zmian (w `notatki/Plan implementacji.md` git widzi tylko zmianę końców linii
  – nie commituję jej).

26.10 – F3a.11 dokończone na prośbę („start working until i say to stop”): zakładka **Finanse → Podatki**
  (Decyzje + Wyniki) zarejestrowana, KPiR pokazuje zaliczkę PIT i zdrowotną; render sprawdzony w node (rundy 1 i 4).

26.10 – F3a.12 Uzgodnienie kasy: rodzaje operacji rachunku, `silnik/uzgodnienie.py`, sekcja w Raporcie, test
  hypothesis. Test od razu złapał 4 prawdziwe błędy (3 × grosz z zaokrągleń, 1 × wywrotka gry przy zwrocie
  ostatniej partii) – naprawione. Do potwierdzenia nic – to wewnętrzna kontrola silnika.

26.10 – F3a.13 Biura rachunkowe z mapy i samodzielna księgowość (pytanie 9): 5 biur, opłata od dokumentów,
  błędy biur z OC/bez OC, samodzielne księgowanie dokumentów i deklaracje sprawdzane w następnej rundzie,
  ukrywanie wyników do czasu deklaracji; zakładka Biuro rachunkowe (Decyzje + Wyniki), JS-owe podsumowanie
  deklaracji zgodne z silnikiem (42/42 przypadki); 154 testy. Rozszerzony test uzgodnienia złapał błąd: kredyt
  odnawialny z końca rundy nie trafiał do dokumentów – naprawione.
- 26.10 – F3a.14 gotowe: panel mistrza gry (pauza, harmonogram zamykania rund z komendą `zamykaj_rundy`, podgląd drużyn tylko do odczytu, poziomy botów bez efektu do F4.4, eksport CSV); pytanie 10. Start F3a.15.
