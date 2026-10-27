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
Są na branch 'kod' w Tom-Wasko/Levas-stary
2. **Start gry i runda 1 (F2.7).** Przyjąłem: runda 1 = tydzień 5–11.10.2026 (początek roku akademickiego) i jest
   tygodniem przygotowań bez sprzedaży (jak w Revasie). Czy data i tydzień przygotowań są dobre? Zmiana to tylko
   `rundy.kalendarz.start` w `dane/katalog.yaml`. (zadane: 25.10 22:20, do wysłania w poniedziałek o 6:00)
pierwszy tyg września na start, wrzesien jest jako wprowadzenie a jak studenci wrócą to zaczyna sie zabawa

3. **Logowanie kontem Microsoft (F3a.1).** Kod jest gotowy, ale potrzebna jest aplikacja zarejestrowana
   w Microsoft Entra ID szkoły (identyfikator klienta, sekret, identyfikator dzierżawy) – to zrobi administrator
   szkolnego Microsoft 365 albo Ty, jeśli masz dostęp. Czy mam przygotować krótką instrukcję krok po kroku?
   Do tego czasu działa własny login i hasło. (zadane: 26.10 0:40, do wysłania w poniedziałek o 6:00)
zrób instrukcje w plliku md

4. **Czas właściciela (F3a.7).** Przyjąłem 20 h na rundę (tydzień), tyle samo dla każdej drużyny – firma ma jednego
   właściciela, więc liczba osób w drużynie nie zmienia puli. Na razie zużywa ją tylko odbiór osobisty w dyskontach
   (1–1,5 h za dzień zakupów), później pracuj.pl i parki. Czy 20 h jest dobre i czy pula ma rosnąć z liczbą osób
   w drużynie? (zadane: 26.10 5:30, do wysłania w poniedziałek o 6:00)
20h jest ok, najwyzej sie zmieni. wlasciciel tez moze uzupelniac roboczogodziny pracownikow jesli ich zabraknie

5. **Agencja pracy (F3a.8).** Przyjąłem: pracuj.pl – kandydaci 1–2★, 150 zł + 2 h czasu właściciela;
   agencja – 2–3★, koszt = koszt rekrutacji kandydata; headhunter (od rundy 4) – 3★, 3 × koszt rekrutacji, a za
   podkupienie 50% oferowanej pensji. Limit 3 nowych osób na rundę, okres wypowiedzenia 2/4/13 rund (staż od 0/26/156
   rund). Staż liczę od zatrudnienia w grze – notatki mówią o „losowym stażu” kandydatów w puli; czy kandydaci
   mają przychodzić z losowym stażem (wtedy ten staż liczy się do okresu wypowiedzenia)? Czy kwoty i gwiazdki pasują?
   (zadane: 26.10 5:45, do wysłania w poniedziałek o 6:00)
ok, ale 13 rund to az dużo

6. **Banki (F3a.9).** Przyjąłem 6 banków z mapy: Crédit Agricole (kredyt na start bez historii, 11,9%),
   PKO BP (inwestycyjny pod zastaw 7,9%, do 70% wartości), Pekao (leasing 7,5%, wpłata 10%), ING (lokaty do 4%),
   mBank (konto i terminal 0 zł, prowizja 0,79%), Santander (limit 40 000 zł, 16,9%). Kwoty to mój szacunek na 10.2026.
   „Historia firmy” = 4 rundy od otwarcia pierwszego lokalu; 70% sprzedaży płacone kartą; 3 rundy bez raty → bank
   przejmuje zastaw (kupiony lokal staje się wynajmowany). Czy banki, oprocentowanie i te zasady pasują?
   (zadane: 26.10 6:05)
ok

7. **Harpagon (F3a.10).** Przyjąłem: pożyczka 500–20 000 zł, 5% na rundę (tydzień) od całego długu, termin 4 rundy;
   po terminie: 1. runda – przypomnienie, od 2. – odsetki karne 10%, od 3. – co rundę jedna losowa wizyta (szkody
   800–3000 zł w KPiR jako „Naprawa szkód w lokalu”, albo atrakcyjność lokali −30% w tej rundzie, albo odejście
   losowego pracownika bez wypowiedzenia). Dług u Harpagona nie wchodzi do wskaźnika zadłużenia w karcie wyników
   i boty z niego nie korzystają. Czy te wartości i zasady pasują? (zadane: 26.10)
ok

8. **Księgowość JDG (F3a.11).** Przyjąłem: wszystkie ceny w danych są brutto (VAT wydzielany z kwoty, także opłaty
   banków i czynsz); rozliczenie VAT/PIT/ZUS co rundę (tydzień), nie co miesiąc; zdrowotna od dochodu tej rundy,
   minimum 324,41 zł/mies.; ZUS społeczny preferencyjny 420,86 zł/mies. po 26 rundach ulgi (czyli w grze na 26 rund
   go nie ma); kwoty ZUS 2026 z pamięci; lokal, działka i budowa budynku bez VAT; próg amortyzacji liczony od brutto.
   Czy tak może zostać? (nie wysłane – okno pytań minęło; zapisane 26.10 18:25)
ok, dodaj krótkie opisy wytłumaczające co jest czym, rzeby miało charakter dydaktyczny

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
ok

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
ok

11. **Limity (F3a.15).** Do limitu 3 nowych pracowników liczę zatrudnienia z puli **i** oferty podkupienia
   (także te, które pracownik odrzuci – oferta jest złożona w tej rundzie); zastąpienie kandydata na tym samym
   stanowisku się nie liczy. Lokal „co 3 rundy” liczę od rundy wzięcia poprzedniego lokalu (lokal z rundy 1 →
   kolejny od rundy 4), nie od chwili, gdy zacznie działać. Czy tak? (zapisane 26.10)
tak, jesli ktos sprobuje kupic lokal przed uplywem 3 dni to napisz że właściciel musi sobie odpocząć/odstresować się czy coś takiego

12. **Parki (F3b.1).** Założenia do sprawdzenia: porcja jedzenia w evencie kosztuje 9 zł (koszt towaru, bez VAT);
   gotówka z eventów (nagrody, opłaty) bez VAT; od rundy 2 **co rundę** jedna historia, ta sama dla wszystkich
   drużyn, bez powtórzeń w cyklu 14 historii; skutki: popyt od −3% do +8% na 1–3 rundy, 2–6 h właściciela mniej na 1
   rundę, nagrody 210–1200 zł, straty 120–400 zł; 12 historii komicznych i 2 poważne (biegacz, zaginione dziecko); 4 nowe parki na
   mapie (Ogród Botaniczny, Park Bronowicki, Park Rury, Błonia); boty wybierają losowo spośród opcji do 3 h;
   pan Zbyszek (kucharz 2★) trafia na rynek pracy tylko dla drużyny, która go zaprosiła. Czy tak? (zapisane 26.10)
chcę żeby w każdej rundzie było kilka eventów do wyboru w różnych parkach. na runde, ale zrob tak ze jesli gracz weźnie wszystkie to zabraknie mu czasu właściciela na inne rzeczy 
Dodaj kolejne hjistoryjki (jak skończysz wszyststkie inne poprawki to generuj aż do 15:00)

13. **Magazyn (zmiana 26.10).** Liczby do sprawdzenia (`zalozenia.yaml` → `magazyn`): wynajem 1 zł za litr nadmiaru
   (jednorazowo za dostawę, nie za dzień), termin −2 dni, VAT 23%; sanepid: szansa 3% co rundę + 0,05 pp. za litr
   w wynajmie + 0,04 pp. za złotówkę przeterminowanego towaru (max 60%) – kontrola „z problemem” kończy się
   mandatem 300 zł + 1 zł/l + 0,5 zł za złotówkę przeterminowaną (max 3000 zł, zaokr. do 50 zł) i −7% popytu przez
   2 rundy; mandat nie jest kosztem podatkowym; bank żywności: zapas, któremu do końca terminu zostało ≤ 3 dni, wart
   ≥ 200 zł, szansa 40% na rundę, raz na grę; oddanie bez kosztu w KPiR (był kosztem przy zakupie). Uwaga: jedno
   wyrzucone opakowanie mięsa to już ok. +14 pp. szansy kontroli – może za ostro? Gra bez lokali (`dane_revas/`)
   zostaje ze zwrotami i kosztem magazynowania. Czy tak? (zapisane 26.10)
lubie jak jest ostra kara za błędy, więc zostaw

14. **Agencje reklamowe (F3b.2).** Liczby do sprawdzenia (`dane/mapa/reklama.yaml`): kampanie 250–2500 zł netto
   (w strefie × pula strefy, więc w Centrum ok. 20% drożej), efekt: +1–8% puli strefy i +5–20% atrakcyjności u jej
   mieszkańców; zagłuszanie – każda inna firma z kampanią tego samego **rodzaju** (druk / internet / radio
   i billboardy / wydarzenia) w strefie dzieli efekt (×1/(1+0,5·n)); nasycenie −30% za każdą wcześniejszą kampanię
   w tym kanale i strefie w ostatnich 4 rundach; wygasanie ×0,5 na rundę. Poszerzenie puli pomaga też konkurencji
   w tej strefie (w teście kampania degustacji + ulotek: firma +4% popytu, sąsiad bez zmian). Radio działa w całym
   mieście, ale słabiej. W grze z lokalami **nie ma** już reklamy tradycyjnej i internetowej z Revasa (zakładki
   ukryte). Czy tak? (zapisane 26.10)
chcę żeby wzrost popytu w kebabie z reklamy był mniej więcej w zakresie (+10% do +30%)

15. **Promocje (F3b.3).** Liczby do sprawdzenia (`dane/mapa/promocje.yaml`): 2 za 1 – przyciąganie +50% → min. +20%
   (−8 pp./rundę), koszt włączenia 150 zł; zestaw – dopłata 4 zł brutto, napój 1,80 zł netto, +18% → +10%, 100 zł;
   happy hours pn–czw −20%, +35% → +20%, 120 zł; karta −10%, +5% → +22% (+3 pp./rundę), 400 zł; zniżka studencka −15%,
   +40% (stałe), tylko mieszkańcy Akademickich i Politechniki, 80 zł. Najwyżej 2 promocje naraz, od rundy 2.
   Dopłata do zestawu idzie jako sprzedaż napoju (VAT 23%), nie dania (8%). Popyt w Wynikach przy 2 za 1 liczony
   w porcjach (klient bierze dwie). Obserwacja: boty prawie zawsze mają za mało kuchni (obsługują 50–70% popytu),
   a wtedy promocja tylko obcina cenę – w grze 4 botów promocje zmniejszały przychód o 5–30%; dlatego boty
   włączają promocje dopiero, gdy w poprzedniej rundzie obsłużyły ≥ 90% popytu (w praktyce rzadko). To lekcja dla
   graczy („promocja, gdy masz wolne moce”), ale może warto osłabić rabaty? Czy tak? (zapisane 27.10)
jest ok

16. **Licytacje i przejęcia (F3b.4).** Zamiast `oferty.py` i `koniec_najmu.py` z planu – jeden moduł
   `silnik/przejecia.py`. Spór o lokal rozstrzyga teraz najwyższa oferta względem ceny wywoławczej (czynszu albo
   ceny; najwyżej 3 ×), od rundy 4; wcześniej i przy remisie – losowanie (dotąd: kolejność rundy). Kupić można tylko
   budynek, który ma cenę w danych (lokale tylko do najmu – nie) i który wynajmuje drużyna; najemca płaci ten sam
   czynsz nowemu właścicielowi (przychód z VAT 23%). Wypowiedzenie: 4 rundy łącznie z rundą wypowiedzenia, potem
   wyprowadzka na początku rundy: sprzęt najemcy sprzedany (jak w zakładce Sprzęt), pracownicy przeniesieni na wolne
   stanowiska w innych lokalach, reszta zwolniona z odprawą; nakłady najemcy (adaptacja + zakup stanowisk) rozliczone
   wg wyboru właściciela: zatrzymanie – płaci 50% nakładów i zostają mu stanowiska, przywrócenie – najemca płaci 30%.
   Uproszczenia: kaucja wraca do najemcy „z zewnątrz” (nie z kasy właściciela, który jej nie dostał); stanowiska
   najemcy zostają w jego ewidencji środków trwałych (amortyzacja) także po wyprowadzce; brak podatku od
   nieruchomości; boty nie licytują i nie kupują budynków. Czy tak? (zapisane 27.10)
ok

17. **Wypadki i ubezpieczyciel (F3b.5).** Liczby do sprawdzenia (`dane/zdarzenia/losowe.yaml`): wypadki od rundy 4,
   szansa 8% na rundę (średnio niecałe 2 wypadki na grę), szkody 500–4200 zł w scenie, limit 8000 zł za jedną szkodę
   (nie za całą historię); polisy (kwoty miesięczne): lokal 140 zł za lokal, pokrycie 90%, franszyza 300 zł; sprzęt
   0,2% majątku, 85%, 200 zł; OC 80 zł, 100%, 100 zł; karencja 1 runda. Uproszczenia: szkody i odszkodowania bez VAT
   (zw), składka zwolniona z VAT; polisa chroni przed wypadkiem tylko, gdy chroniła w rundzie jego początku (ciąg
   dalszy też); wypowiedzenie – od razu, bez zwrotu składki. Nazwa ubezpieczyciela: TUW „Pod Koziołkiem”. Czy tak?
   (zapisane 27.10)
w każdej kolejnej rundzie bez wypadku zwiększ szansę

18. **Urząd i sanepid (F3b.6).** Rejestracja w CEIDG – bezpłatna i tylko informacyjna (bez decyzji). Odbiór sanepidu
   w rundzie, w której lokal ma zacząć działać; przy higienie „brak” odmowa i lokal czeka 1 rundę (powtarza się do
   skutku). Poziomy higieny (zł/mies. brutto za działający lokal): brak 0 zł (+6 pp. szansy kontroli, +400 zł do
   mandatu, bez odbioru), mop i grafik 120 zł (domyślny), firma „Błysk-Pol” 750 zł (część szansy z problemów ×0,7),
   Błysk-Pol + HACCP 1300 zł (×0,45). Skargi w historiach (Gołąb Zenon „zostaw”: +10 pp. przez 2 rundy, Pani Halina
   „zignoruj”: +12 pp. przez 2 rundy). Boty: zrównoważony i tani – mop, premium – HACCP, agresywny – firma. Ratusz na
   mapie otwiera teraz zakładkę Urząd i sanepid (lista błędów nadal w menu). Czy tak? (zapisane 27.10)
ok

19. **Kasyno i portfel właściciela (F3b.7).** Liczby: oszczędności na start 2000 zł; zaproszenie od rundy 4, szansa
   8% na rundę, najwyżej 2 w grze; do 5 zakładów w rundzie, stawka 10–2000 zł; ruletka europejska (kolor/parzyste
   ×2, tuzin ×3, zero ×36), automat: 55% nic, 28% zwrot, 12% ×2, 4% ×5, 1% ×10 (zwrot ok. 82%). Ukrywanie:
   mistrz gry nie widzi ani klubu, ani **portfela** (jego zmiany zdradzałyby klub) – wpłaty i wypłaty własne widać
   tylko jako operacje na koncie firmy; drużyna prowadzona przez MG nie ma więc ani klubu, ani portfela.
   `LEVAS_KASYNO=0` ukrywa tylko klub, portfel zostaje. Eksport gry jest bez zakładów – po imporcie gra przelicza
   się bez klubu, więc portfel i wpłaty z wygranych mogą wyjść inaczej. Wypłata własna nie zmienia podatku (PIT
   od dochodu JDG). Pytania: czy portfel też ukrywać przed MG? czy eksport ma zawierać zakłady (MG mógłby je
   wtedy zobaczyć w pliku)? czy liczby takie? (zapisane 27.10)
właściciel ma mieć możliwość wyciągnąć pieniądze z konta kebaba, gdzieś w panelu kasyna dodaj jhakąś ironiczną/metaforyczn przesłankę rzeby gracze nie poinformowali mistrza o istnieniu kasyna

20. **Handel między drużynami (F3b.8).** Założenia: od rundy 5 (notatka „Ustalenia gry”); towar i sprzęt – **bez
   lokali** (notatka „Prawidła świata” wymienia też lokale: przekazanie najmu/własności z kaucją, nakładami
   i wyposażeniem to osobna, większa zmiana – zrobić później?); cena brutto w widełkach 50–200% wartości (towar –
   średni koszt zakupu z magazynu, sprzęt – cena katalogowa nowego), żeby nie dało się przelewać pieniędzy „za
   grosz” albo „za milion”; najwyżej 5 ofert w rundzie; oferta ważna jedną rundę (adresat przyjmuje w następnej,
   potem wygasa); towar sprawdzany na stan po tygodniu sprzedaży, a przy przyjęciu – czy nadal jest; boty nie
   handlują. Pytania: czy widełki i limity takie? czy dodać negocjację (kontroferta adresata) albo handel w tej
   samej rundzie? czy handel lokalami robić teraz? (zapisane 27.10)
tak, chce negocjacje

21. **Kalendarz miejski (F3b.9).** Założenia: kalendarz przeniesiony z `mapa/popyt.yaml` do
   `dane/kalendarz/kalendarz.yaml`; 23 wydarzenia od października do kwietnia, mnożniki puli stref dobrane „na oko”
   (np. przerwa świąteczna – Miasteczko i Politechnika ×0,35, jarmark – Stare Miasto ×1,25, Wielkanoc – całe miasto
   ×0,45); daty ferii zimowych w lubelskim (2026: od 2.02, 2027: od 18.01, 2028: od 14.02) to założenie –
   trzeba sprawdzić w harmonogramie MEN; kalendarz zmienia tylko liczbę klientów stref (nie dań – np. więcej
   frytek w sesji). Notatka „Zdarzenia i historie” (koziołki do końca sesji) – zostawione na później. Pytania: czy
   lista i mnożniki takie? czy wydarzenia mają też zmieniać popyt na konkretne dania? czy dodać mecze Motoru na
   Arenie Lublin? (zapisane 27.10)
dodaj kilka meczy, konkretne dania to fajny pomysł

22. **Karta wyników dla kebabu (F4.1).** Założenia (`zalozenia.yaml → karta_wynikow.kebab`, wszystkie „na oko”):
   kolejki −0,15 × udział klientów, którzy nie doczekali się obsługi; brakujące dania −0,3 × udział dań-dni
   wyłączonych; mandat sanepidu −0,05; każdy wypadek w lokalu −0,03; przepracowanie −0,5 × nadwyżka wykorzystania
   czasu ponad 85%; każdy kolejny lokal +0,08 do rozwoju; dług u Harpagona liczony ×1,5 w zadłużeniu. Cena porównywana
   z ceną preferowaną strefy lokalu, a nie ze średnią rynku. Z tabeli w „Ustaleniach gry” nie dodałem jeszcze:
   „umowa” i „zmiany w zatrudnieniu” działają jak w Revasie (zmiany mają wagę 0), „świeżość” liczę pośrednio (braki
   w menu, sanepid), „wartość sprzętu” jest w majątku. Pytania: czy wagi takie? czy dodać do karty kontrole skarbówki
   lub zaległości? czy przy notatce „Ustalenia gry” wpisać ostateczne wzory? (zapisane 27.10)
zrób jak uważasz że będzie najlepiej

23. **Lista błędów (F4.2).** Założenia (`zalozenia.yaml → lista_bledow`): pomarańczowe ostrzeżenie, gdy składniki
   kosztują ponad 50% ceny dania (koszt liczony po średniej cenie zapasu, a bez zapasu – po najtańszej średniej cenie
   z danych), czerwone poniżej kosztu; ostrzeżenie o przeterminowaniu liczone z prognozy popytu (pole „prognoza”
   w Ofercie) i dopiero od 20 zł straty w tygodniu. Komunikaty z lekkim humorem („klienci sami sobie tego nie
   zrobią”). Pytania: czy progi takie? czy brak gotówki na zamówienie ma blokować zamówienie (teraz: ostrzeżenie,
   płaci kredyt odnawialny)? (zapisane 27.10)
ok, tak ostrzeżenie, humor jest fajny

24. **Harmonogram odblokowań (F4.3).** Tygodnie domyślne jak w REVAS (`katalog.yaml → rundy.harmonogram_lokali`):
   tydzień 1 to tydzień przygotowań (bez dostaw i sprzedaży), więc Sprzęt, Ceny dań, Dostawcy i Zatrudnienie
   otwierają się w tygodniu 2 – notatka „Ustalenia gry” mówi o dostawcach i pracuj.pl od rundy 1. Mistrz gry może
   zmienić tydzień każdego elementu (zakładki, kanały rekrutacji, późniejsi dostawcy, licytacje, przejęcia, promocje,
   kanały agencji reklamowych, eventy w parkach, wypadki, handel) – przy zakładaniu gry (API) i w trakcie (panel MG,
   tylko elementy jeszcze nieodblokowane, najwcześniej na bieżący tydzień, tydzień „liczba rund + 1” = wyłączone).
   Klub z kasynem nie jest w harmonogramie (mistrz gry o nim nie wie). Pytania: czy tydzień 1 ma zostać
   przygotowawczy? ubezpieczyciel „od rundy 3” z notatek – na razie bez blokady; czy MG ma móc przesuwać też zakładki
   tygodnia 1 (teraz tak – można je opóźnić)? (zapisane 27.10)
tyg1 jest przygotowawczy, nie mg nie ma takiej mocy

25. **Poziomy botów (F4.4).** Poziomy różnią się sposobem planowania (`dane/boty.yaml → poziomy`, `silnik/boty.py`):
   **łatwy** – stare proste reguły (osobna kuchnia na danie, zamówienia na cały przewidywany popyt, błąd prognozy
   ±25%, zatrudnia losowego kandydata z zawodu, bez kampanii i promocji); **średni** – planuje obsadę i sprzęt na
   popyt dzień po dniu (kolejny kucharz/kasjer tylko, gdy dodatkowa sprzedaż × marża pokrywa jego koszt), zamawia
   tylko to, co kuchnia sprzeda, reklamuje się wg strategii; **trudny** – dodatkowo poprawia prognozę o wynik
   poprzedniej rundy, wybiera cenę o największej oczekiwanej marży (±10–15%), reklamuje się tylko, gdy nadąża
   z obsługą, i bierze drugi lokal (gotówka > 60 000 zł, kuchnia nie nadąża). Planujące boty wybierają lokal
   z co najmniej 2 miejscami w kuchni (tani – 1). Wyniki (`gra/balans_botow.py`, 12 tygodni, ziarna 7/11/23, średnia
   gotówka 5 strategii): łatwy ≈ 46 tys., średni ≈ 69 tys., trudny ≈ 82 tys.; towar przeterminowany: łatwy 10–70
   tys., średni/trudny ≈ 3–7 tys. Wyjątek: Premium na poziomie łatwym zarabia więcej niż na średnim (kampanie
   influencer + billboard ≈ 14 tys. i karta stałego klienta, a dodatkowa obsada sprzedaje niewiele więcej). Nie
   zrobione: przejęcia i licytacje lokali przez boty, zwalnianie pracowników. Pytania: czy takie różnice poziomów
   wystarczą? czy trudny bot ma też przejmować i licytować lokale? czy Premium ma reklamować się taniej (np. bez
   billboardu)? (zapisane 27.10)
jeśli będziesz miał czas to stwórz boty 'niemożliwy' który będzie robił wszystko jak tylko możliwie najlepiej, tylko jeśli będziesz miał wolny czas. jesli nie to zapisz gdzies do rzeczy do zrobienmia w przyszlosci

26. **„Co jeśli” (F4.5).** W podglądzie inne drużyny powtarzają decyzje z poprzedniej rundy: ceny, prognozę,
   zamówienia, kampanie, reklamę, promocje, polisy i higienę (jednorazowe – lokal, zatrudnienia, sprzęt, kredyty,
   handel – nie). Wcześniej (jak w Revasie) podgląd brał robocze decyzje rywali, czyli zdradzał np. ich nowe ceny.
   Pytania: czy lista powtarzanych decyzji jest dobra? czy podgląd ma też pokazywać ryzyko zdarzeń losowych
   (teraz wypadki i wynik kasyna są w podglądzie pomijane)? (zapisane 27.10)
daj każddemu graczowi ogólny obraz tego co robią jego przeciwnicy w zakładce decyzje/wyniki, natomiast jeśli bedzie on chcaił bardziej dokładne dane to musi zatrudnić szpiega albo cos takiego

27. **Sprzątanie (F4.6).** Usunąłem tryb „gra bez lokali” (stary Revas: gotowy lokal na start, popyt i reklama
   z Revasa, zwroty do dostawców) – Levas ma teraz jeden tryb: gra z mapą miasta. Da się go przywrócić z commita
   `9930e14`. Zostało bez zmian: sezonowość popytu nadal miesięczna (`uslugi.yaml → sezonowosc`, 12 wartości –
   tygodnie biorą wartość swojego miesiąca), dane Revasa (`gra/dane_revas/`) zostają jako wzorzec dla kilku
   testów mechaniki obsługi. Pytania: czy usunąć tryb Revasa na stałe (w tym `dane_revas/` i zakładkę Marketing
   z reklamą Revasa w panelu)? czy sezonowość ma być tygodniowa (np. wakacje, sesja, święta – część jest już
   w kalendarzu miasta)? (zapisane 27.10)
morzesz usuwac nie potrzebne rzeczy, zrob bardziej dopasowana sezonowosc do obecnych wydarzen, skup się na okresie czasy (wrezsień-grudzień)

28. **Zakładki (F4.7).** Menu: „Oferta” → „Menu”, „Zdarzenia” → „Parki” (pełny tytuł: Parki – eventy, zdarzenia
   i wypadki), „Magazyn i świeżość” jako podzakładka Dostawców, nowa zakładka Finanse ▸ VAT (wydzielona
   z Podatków, z krótkim komicznym wstępem o panu Zenonie z urzędu skarbowego), wyniki dla Stanowisk i Szkoleń.
   Pytania: czy nazwy i grupowanie pasują (np. Parki jako osobna pozycja menu czy pod Klientami)? czy zostawić
   pana Zenona? Zakładki bez trybu wyników (Pulpit, Mapa, Lista błędów, Wyślij, Analiza) i bez decyzji (Karta,
   Raport, KPiR) zostały celowo – to podglądy/raporty. (zapisane 27.10)
jest ok , na razie sie tym nie przejmuj


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
- 26.10 – F3a.15 gotowe: limity odrzucane przy zapisie decyzji (`silnik/limity.py`); pytanie 11. Krok 3a zakończony, start F3b.1 Parki.
- 26.10 – F3b.1 gotowe: eventy w parkach (14 historii, zakładka Zdarzenia); pytanie 12. Nowe polecenia użytkownika: kapitał 40 000 zł, sortowanie list, lodówki + sanepid zamiast kosztu magazynowania, bez zwrotów + event z bankiem żywności.
- 26.10 – kapitał 40 000 zł, poprawione 4 notatki (zgoda użytkownika), sortowanie tabel i oferty lokali. Boty przy 40 000 zł nie schodzą poniżej ok. 18 000 zł gotówki (2 ziarna × 26 rund). Dalej: magazyn (wynajem chłodni, sanepid, bank żywności).
- 26.10 – magazyn gotowy: wynajęta chłodnia, sanepid z mandatami poza KPiR, bank żywności, bez zwrotów i kosztu magazynowania w grze z lokalami; pytanie 13. Start F3b.2.
- 26.10 – F3b.2 gotowe: agencje reklamowe (4 agencje, 8 kanałów, zagłuszanie, nasycenie, wygasanie), zakładka Agencje reklamowe, boty z kampaniami; pytanie 14. Start F3b.3 (promocje).
- 27.10 – F3b.3 gotowe: promocje (5 rodzajów z ozdobną nazwą, znużenie i przywiązanie, 2 za 1 z podwójnymi porcjami,
  zestaw z dopłatą i VAT napoju), zakładka Promocje, boty z promocjami tylko przy wolnych mocach; pytanie 15.
  Start F3b.4 (licytacje i przejęcia).
- 27.10 – F3b.4 gotowe: licytacje lokali (najwyższa oferta, remis – losowanie), kupno budynków z najemcą, wykup,
  wypowiedzenia z rozliczeniem nakładów, wyprowadzki, zakładka Licytacje i przejęcia; pytanie 16. Start F3b.5.
- 27.10 – F3b.5 gotowe: wypadki w lokalu (10 historii, 8 komicznych), ubezpieczyciel z polisami na lokal, sprzęt i OC,
  zakładka Ubezpieczenia, boty z polisami; pytanie 17. Start F3b.6 (urząd/sanepid).
- 27.10 – F3b.6 gotowe: odbiór lokalu przez sanepid, 4 poziomy higieny z kosztem i wpływem na kontrole, skargi
  w historiach, zakładka Urząd i sanepid; pytanie 18. Start F3b.7 (kasyno).
- 27.10 01:25 – F3b.7 gotowe: portfel właściciela (wpłata/wypłata własna poza KPiR) i tajny klub przy ul. Nocnej
  (zaproszenia, ruletka i automat, ukryty przed MG); pytanie 19. Start F3b.8 (handel między drużynami).
- 27.10 04:35 – F3b.8 gotowe: oferty towaru i sprzętu dla innych drużyn, przyjęcie w następnej rundzie, faktury
  w KPiR obu stron, zakładka Handel z drużynami; pytanie 20. Start F3b.9 (kalendarz miejski).
- 27.10 04:45 – F3b.9 gotowe: kalendarz miejski w `dane/kalendarz/` (23 wydarzenia z historiami, daty ruchome),
  zakładka Kalendarz miejski; pytanie 21. Start F4.1.
- 27.10 04:57 – F4.1 gotowe: karta wyników ze składnikami kebabowymi (kolejki, braki w menu, sanepid, wypadki,
  przepracowanie, lokale, Harpagon), rozbicie w zakładce Karta wyników; pytanie 22. Start F4.2 (lista błędów).
- 27.10 05:11 – F4.2 gotowe: lista błędów dla dań (sprzęt, kucharz, cena wobec kosztu składników), przeterminowanie
  przy prognozie, zamówienia ponad saldo; pytanie 23. Start F4.3 (odblokowywanie zakładek).
- 27.10 05:28 – F4.3 gotowe: harmonogram odblokowań w tygodniach z danych, zmiany MG dla jednej gry (widok danych
  gry, wspólne dane bez zmian), edytor w panelu MG, podpowiedzi „od rundy” z harmonogramu; pytanie 24. Start F4.4.
- 27.10 05:55 – F4.4 gotowe: poziomy botów łatwy/średni/trudny (planowanie obsady dzień po dniu z rachunkiem
  opłacalności, zamówienia w granicach przepustowości, wybór ceny, reklama tylko przy nadążającej obsłudze, drugi
  lokal), narzędzie `gra/balans_botow.py`, test `test_boty.py`; pytanie 25. Start F4.5 („co jeśli”).
- 27.10 06:10 – F4.5 gotowe: „co jeśli” w `silnik/co_jesli.py` – inne drużyny powtarzają decyzje z poprzedniej
  rundy (bez zdradzania roboczych decyzji rywali), opis i wiersz przeterminowanego towaru w zakładce Analiza;
  pytanie 26. Start F4.6 (sprzątanie).
- 27.10 06:24 – F4.6 gotowe: jeden tryb gry (z mapą miasta), usunięty kod Revasa (popyt, reklama, zwroty, startowy
  lokal), nazwy kasy zamiast recepcji, `gra/balans/symuluj.py`; 245 testów; pytanie 27. Start F4.7 (zakładki).
- 27.10 06:35 – F4.7 gotowe: menu i zakładki (Menu, VAT, Parki, Dostawcy ▸ świeżość), wyniki Stanowisk i Szkoleń;
  245 testów; pytanie 28. Plan kroków 1–4 (bez giełdy) zrealizowany.
- 27.10 06:45 – dosprzątanie: nieużywane parametry Revasa usunięte z `dane/zalozenia.yaml` (zostają w
  `dane_revas/`), pulpit pokazuje stawkę PIT liniowego.
- 27.10 07:40 – odpowiedzi użytkownika (plik + czat). Na czacie: start pon. 1.09.**2025** (prawdziwy kalendarz),
  18 pełnych rund; kredyt domyślnie „na bieżąco”; „Zamów brakujące” domyślnie wyłączone, opcja MG; parki – te same
  eventy dla wszystkich, każdy może wziąć każdy i dostaje tę samą nagrodę; szpieg – detektyw z mapy (300–800 zł,
  2 h, 15% wpadki); negocjacje na żywo w rundzie; właściciel jako pracownik 1★ (ręcznie); reklama – **suma**
  kampanii +10…30%; wypowiedzenie – jedno, 2 rundy; wypadki +4 pp. za rundę bez wypadku; tutorial – strona
  w grze + md + PDF; stary Levas – tylko lista różnic, jeśli starczy czasu; serwerów na 8765 nie ruszać.
  Lista zadań: `POSTEP.md` → „Poprawki 27.10” (P1–P20).
- 27.10 09:50 – P1 gotowe: `graj` nie uruchamia drugiego serwera, gdy port 8765 jest zajęty (komunikat: zamknij
  okna serwera i uruchom start.bat ponownie). **Po powrocie: zamknij oba okna serwera i uruchom start.bat raz** –
  tworzenie gier wtedy działa (dziś rano odpowiadał stary serwer z 26.10).
- 27.10 09:50 – P2 gotowe: start pon. 1.09.2025, 18 rund (do 4.01.2026), kredyt domyślnie „na bieżąco”, przycisk
  „Zamów brakujące u najtańszych” domyślnie wyłączony – pole w „Więcej ustawień” przy tworzeniu gry i
  „włącz/wyłącz” w tabeli „Ustawienia gry” panelu MG. Wrzesień w kalendarzu: wakacje studenckie (mało studentów),
  początek roku szkolnego, powrót studentów (ostatni weekend), inauguracja roku akademickiego (1–3.10).
  Daty ruchome 2025 (Black Friday 28.11, ferie – założenie 27.01). Start P3 (tutorial).
- **P3 gotowe:** instrukcja dla graczy `gra/INSTRUKCJA.md` (15 rozdziałów: runda, karta wyników, tydzień 1 i 2,
  klienci, dostawcy, ludzie, czas właściciela, marketing, pieniądze, parki/zdarzenia, rozwój, odblokowania,
  10 rad; bez kasyna – jest tajne). W grze strona **/jak-grac** (bez logowania, spis treści, ramki z radami,
  wersja na telefon i do druku), link „Jak grać” w nagłówkach panelu gracza i MG. PDF: `gra/INSTRUKCJA.pdf`,
  odświeżanie: `python manage.py instrukcja_pdf` (drukuje Edge). Na stronie startowej poprawiony tekst
  „gotowym lokalem” → lokal wybiera się na mapie w 1. tygodniu.
- **P4 gotowe:** `gra/LOGOWANIE_MICROSOFT.md` – rejestracja aplikacji w Microsoft Entra krok po kroku (adres
  zwrotny, identyfikatory, klucz tajny, zgoda administratora), wpisanie danych, próba na własnym komputerze
  (`runserver 8766` + http://localhost:8766), serwer z https, role i drużyny, tabela typowych błędów AADSTS.
  Ułatwienia w kodzie: dane Microsoft można wpisać do `gra/lokalne.json` (zamiast zmiennych środowiskowych),
  `LEVAS_HOSTY`/`"hosty"` (adres serwera), `LEVAS_HTTPS`/`"https"` (serwer za https), `manage.py konto
  <e-mail> --mg` nadaje rolę MG kontu założonemu przez Microsoft. Ważne: klasa w sieci szkoły po
  `http://192.168…` nie zaloguje się kontem Microsoft (Microsoft wymaga https poza localhost) – do tego
  potrzebny serwer z certyfikatem; do tego czasu loginy i hasła.
- **Odpowiedzi 27.10 (po powrocie):** P9 – 3–4 eventy w parkach na rundę, opcje po 2–5 h czasu właściciela;
  P6 – wypowiedzenie 2 rundy w obu kierunkach (zwolniony pracuje i dostaje pensję jeszcze 2 rundy);
  P12 – przycisk „przelej z firmy do portfela” w panelu klubu (na koncie firmy zwykła wypłata własna) +
  „zasada milczenia”; P14 – prawdziwe terminy meczów Motoru Lublin (wyszukać).
- **P5 (27.10):** właściciel może stanąć na jednym wolnym stanowisku (kuchnia albo kasa) – przycisk „Stań sam
  (właściciel)” w HR → Zatrudnienie; pracuje jak 1★ (zadowolenie i ryzyko reklamacji jak przeciętny kandydat 1★),
  bez pensji, godziny (do 40) z puli czasu właściciela; za mało czasu – odrzucone (lista błędów). Tylko w tej
  rundzie (decyzja na każdą rundę). W wynikach – wiersz „Właściciel” w „Twoi pracownicy”. Instrukcja i PDF uzupełnione.
- **P6 (27.10):** jedno wypowiedzenie – 2 rundy (dane/kandydaci.yaml), w obie strony. Zwolniony na umowie o pracę
  pracuje i dostaje pensję jeszcze 2 rundy (odprawa od razu), potem wraca do puli; w HR plakietka „wypowiedzenie
  do r. N” i przycisk „Cofnij zwolnienie” w tej samej rundzie. **Decyzja do potwierdzenia:** zleceniobiorca nadal
  odchodzi od razu (umowa zlecenie nie ma wypowiedzenia z KP) – jeśli wolisz 2 rundy także dla zlecenia, to jedna linijka.
- **P7 (27.10):** opisy dydaktyczne – zwijana ramka 📘 „jak to działa naprawdę” (zakladki/lekcje.js) w zakładkach
  VAT, KPiR, Podatki (PIT i ZUS), Bank i Raport finansowy: przykłady liczbowe, różnica zysk/gotówka, RRSO, ulga na start,
  terminy JPK/ZUS/PIT. Stawki i progi podane ogólnie (bez konkretnych kwot, które co roku się zmieniają).
- **P8 (27.10):** lokal „co 3 rundy” – zamiast suchego limitu 5 rotujących żartów „właściciel musi odpocząć”
  (silnik/lokale.py `ODPOCZYNEK`), w odrzuceniu zapisu, liście błędów, zakładce Lokale i na mapie.
- **P9 (27.10):** parki – co rundę 3–4 historie (`zasady.eventow_na_runde: [3, 4]`), te same dla wszystkich drużyn,
  z talii tasowanej na nowo po wyczerpaniu (w jednej rundzie bez powtórzeń). Czas opcji przeskalowany do 2–5 h
  (1→2, 2→3, 3→5), więc w 20 h właściciela nie zmieszczą się wszystkie; w zakładce Zdarzenia ramka z wolnym
  czasem właściciela. Uwaga: przy 14 historiach i ~60 eventach na grę historie wracają co ~4 rundy – P18 (nowe
  historie) to złagodzi.
- **P10 (27.10):** reklama – siła kanałów ×2 i sufit sumy kampanii (`model.maks_przyciagania: 0.7`, `maks_puli: 0.15`
  w dane/mapa/reklama.yaml; nasycenie x → maks·(1 − e^(−x/maks))). Pomiar (3 boty, lokal A w Centrum, runda 5):
  jedna kampania +4…+10% popytu A, trzy tanie (ulotki + grupa + degustacja) ok. +12%, wszystkie kanały naraz ok. +28%;
  konkurent w tej samej strefie −0…−2%. W wynikach Agencji tabela „Łączne przyciąganie (po sufocie)” – ile uciekło.
- **P11 (27.10):** wypadki – szansa 8% + 4 pp. za każdą rundę bez wypadku (`zasady.przyrost`), sufit 40%
  (`szansa_max`), po wypadku od nowa; licznik od rundy wypadków / otwarcia lokalu (silnik/awarie.py `szansa_wypadku`).
  Symulacja: ok. 2,6 wypadku na grę przy starcie od rundy 4 (ok. 1,7 od rundy 9). W Ubezpieczeniach „Ryzyko wypadku
  w tym tygodniu” i komentarz agenta.
- **P12 (27.10):** w klubie (zakładka Nocna 13) karta „Bankomat w kącie” z przyciskiem „Przelej z firmy do portfela” –
  to ta sama decyzja `wyplata_wlasna` co w Portfelu właściciela, więc na koncie firmy widać tylko zwykłą „Wypłatę własną
  właściciela (poza KPiR)”; wypłata idzie przed zakładami, można ją postawić w tej samej rundzie. Do tego karta
  „Zasada milczenia” (ironiczna tabliczka nad barem + historia o stoisku z watą cukrową). Instrukcja celowo milczy o klubie.

### P13 – negocjacje na żywo w handlu (27.10)
- Adresat widzi szkic oferty od razu (jeszcze w tej samej rundzie): może ją przyjąć, odrzucić albo dać kontrofertę;
  sprzedawca odpowiada przyjęciem kontroferty albo własną kontrą – na przemian, razem najwyżej 3 kontroferty
  (`maks_kontr` w dane/zdarzenia/handel.yaml).
- Przyjęta cena = umowa: transakcja wykonuje się sama na początku następnej rundy (bez klikania „Przyjmij”).
  Oferta bez umowy działa jak dotąd – adresat może ją przyjąć w następnej rundzie po ostatniej cenie sprzedawcy.
  Odrzucona oferta przepada (bez czerwonego błędu u sprzedawcy).
- Wszystko trzymane w szkicach decyzji obu drużyn (`handel_oferty[].ceny/przyjmij_kontre`, `handel_odpowiedzi`),
  więc event sourcing bez zmian. Panel w zakładce Handel odpytuje serwer co 5 s (gdzie indziej co 20 s) i odświeża
  widok po ruchu drugiej drużyny (znacznik w /api/gry/<id>/stan/<firma>).
- Testy: stany negocjacji i limit kontr, pełna negocjacja → umowa → transakcja po uzgodnionej cenie, odrzucenie.
  INSTRUKCJA (md + pdf) – zdanie o targowaniu się.

### P14 – kalendarz wrzesień–grudzień: mecze, dania, płynna sezonowość (27.10)
- 7 prawdziwych domowych meczów Motoru Lublin (Ekstraklasa, jesień 2025, Arena Lublin): 14.09 Termalica, 29.09 Radomiak, 17.10 GKS Katowice, 24.10 Widzew, 8.11 Wisła Płock, 1.12 Legia, 14.12 Jagiellonia (zaległy). Źródła: pl.wikipedia „Motor Lublin (piłka nożna) w sezonie 2025/2026”, fotmob. Każdy mecz ma własny komiczny opis (bez zdradzania wyniku).
- Nowy rodzaj wydarzenia `sport` i pole `rok` (mecze tylko w 2025, nie powtarzają się co roku). Mecz: Zygmuntowskie ×1,6–2,2, Dworzec ×1,15, Centrum ×1,05.
- Nowe pole `dania` – wydarzenie zmienia popyt na konkretne dania w swoich strefach: mecz (kebab w bułce, frytki, napój ↑, talerz ↓), Wigilia (falafel ×1,6), Konfrontacje Teatralne (falafel), Halloween (mniej sosu czosnkowego), Andrzejki, Black Friday, Sylwester itd. Widoczne w zakładce Kalendarz miejski.
- Sezonowość dań płynna z dnia na dzień (interpolacja między środkami miesięcy) zamiast skoku 1. dnia miesiąca. Wrzesień w strefach uczelni nie jest już liczony podwójnie (miesiąc + „Wakacje studenckie”).
- Wydarzenia styczeń–kwiecień zostawiłem (przydają się przy dłuższych grach ustawionych przez MG).
