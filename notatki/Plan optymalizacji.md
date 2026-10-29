[[Plan działania]] · [[Ustalenia gry]] · [[Główny obraz]] · `archiwum/Plan implementacji.md` (archiwum)

# Plan optymalizacji – kroki 5–6

Zastępuje plan implementacji (`archiwum/Plan implementacji.md`, kroki 1–4 zrobione 28.10.2026). Wykonuje go OpenCode (modele Opus 5.5 high albo Fable 5.1). Zasady pracy w repozytorium są w `AGENTS.md`, szczegółowe instrukcje dla sesji w `zadania/`, a gotowe polecenia do wklejenia w `zadania/README.md`. Postęp (checkboxy) jest w `POSTEP.md`, a nie w tej notatce.

Ustalenia z autorem: 28.10.2026 (cele), 29.10.2026 (odpowiedzi na pytania z przeglądu planu, wycena lokalu w majątku netto, inwestor ratunkowy, czas pomiarów – wpisane poniżej).

## Kolejność
Sesje idą **po kolei**, nie równolegle: część A działa na dzisiejszych botach i zasadach, a B od kroku B3 je zmienia.

1. **Część A – analiza oczami gracza** (Fable 5.1, `zadania/A_analiza_gracza.md`). Kod się nie zmienia, powstaje tylko raport z propozycjami.
2. **B1 – inwentarz decyzji** i hipotezy „za dobrych” strategii (z raportu A).
3. **B2 – narzędzie porównań**, profilowanie silnika i wymuszanie decyzji bota.
4. **Z – zmiany zasad** ustalone z autorem (niżej): karta wyników, majątek netto, debet ponad limit z alarmem i inwestorem, liczba lokali zależna od liczby firm, bot „jak człowiek”, kalendarz do kwietnia 2026.
5. **B3 – boty**, tylko część potrzebna do pomiaru, oraz monotoniczność poziomów: łatwy < średni < trudny.
6. **B4 – pomiar startowy** i tag w git `kalibracja-start` (punkt odniesienia „przed”).
7. **STOP – decyzja autora.** Autor czyta raport z A i pomiar startowy. Zatwierdzone pozycje z A trafiają do `POSTEP.md` jako U1, U2… i są wdrażane **przed** kalibracją obszarów, których dotyczą, bo każda nowa mechanika zmienia balans.
8. **B5 – gospodarka i trudność.** Zmienione liczby czekają na **zatwierdzenie autora** przed dalszą pracą, bo od nich zależy cała reszta.
9. **B6–B12 – obszar po obszarze.** Przed każdym obszarem dokończyć tę część B3, która go dotyczy (boty muszą umieć użyć badanych opcji).
10. **B13 – karta wyników**: tylko wagi składowych (wzory zmienia już krok Z), potem szybki pomiar wszystkich obszarów.
11. **B14 – boty po kalibracji** i sprawdzenie, że cele trudności z B5 nadal są spełnione.
12. **B15 – raport końcowy.**

## Część A – analiza oczami gracza (krok 6)
- **A1 – przygotowanie.** Przeczytać instrukcję gracza, notatki i kod zakładek, a potem uruchomić grę.
- **A2 – rozgrywka.** Trzy pełne gry (18 rund, z botami), każda jako inna persona:
  - uczeń-nowicjusz bez wiedzy o firmach i księgowości;
  - ambitny gracz szukający luk i najlepszej strategii (Optymalizator); swoje strategie ocenia kartą wyników skumulowaną (średnia rund 2..N, jak ranking) i majątkiem netto na koniec, a nie samą gotówką;
  - nauczyciel jako mistrz gry, który prowadzi grę z kilkoma drużynami „uczniów” o zaplanowanych błędach (np. drużyna bez zamówień, drużyna w debecie, drużyna bez deklaracji) i sprawdza, czy panel `/mg/` pozwala te problemy zauważyć i omówić.

  W każdej rundzie trzeba obejrzeć to, co widzi gracz, i prowadzić dziennik wrażeń.
- **A3 – raport** `raporty/analiza_gracza.md`. Zawiera:
  - problemy (z dowodami);
  - propozycje zmian istniejących elementów;
  - nowe funkcje, na które autor mógł nie wpaść;
  - listę rzeczy, które działają dobrze i których nie należy psuć;
  - „za dobre” strategie dla części B;
  - pytania do autora.

  Każda pozycja ma priorytet, koszt (S/M/L), wpływ na balans i pliki, których dotyczy.

## Część B – kalibracja (krok 5)

### Cele
- **Przede wszystkim balans.** Liczby mają przynajmniej przypominać realia (kebab w Lublinie, 2025/2026).
- **Żadnej jednoznacznie najlepszej opcji** w żadnej decyzji: lokal, forma, strefa, bank, dostawca, jakość, ceny, ludzie, reklama, księgowość, ubezpieczenia i tak dalej. Każda opcja ma sytuację, w której się opłaca, i sytuację, w której nie.
- **Miara „lepszej decyzji”: karta wyników skumulowana** – średni wynik działalności z rund 2..N, tak jak w rankingu mistrza gry (`api/prezentacja.py`). Pomocniczo: majątek netto na koniec gry, pierwsza runda na plusie i alarmy (definicje niżej).
- **Wyjątek: Harpagon i kasyno.** Średnio się nie opłacają (mierzone majątkiem netto), ale w konkretnej sytuacji (pilnie brakuje gotówki, końcówka gry) bywają opłacalne. To lekcja o ryzyku.
- **Prawo:** parametry prawne są zamrożone na prawie z 2026 roku (płaca minimalna 4806 zł, ZUS, VAT, PIT, próg 10 000 zł dla środków trwałych) przez całą grę, także w rundach z 2025 roku. Kalibracja ich nie zmienia. Terminowe płacenie ZUS i podatków, higiena i sanepid oraz rodzaj umowy to lekcje: kalibracja sprawdza tylko, czy łamanie zasad **średnio się nie opłaca**.
- **Trudność** – mierzona botem „jak człowiek” (krok Z5) w trzech wersjach:
  - wersja średnia ma pierwszy tydzień na plusie w rundzie 4–6;
  - wersja słaba może skończyć grę na minusie, ale nie wpada w alarm;
  - wersja dobra wyraźnie wygrywa.

  Dziś (12 rund, ziarno 7, poziom średni) każdy bot kończy grę z 47–100 tys. zł przy 40 tys. zł kapitału, czyli gra jest za łatwa.
- **Długość gry:** bazowo 18 rund. Sprawdzić także 12 i 26 rund, żeby krótsza ani dłuższa gra się nie psuła.
- **Liczba firm:** 4–8. Pomiar bazowy na 6 firmach, sprawdzenie na 4 i 8. Z liczbą firm skaluje się tylko liczba lokali na mapie (krok Z4), popyt miasta nie. Jeśli przy 4 firmach gra robi się wyraźnie łatwiejsza, zgłosić to autorowi zamiast stroić popyt.
- **Bez pilotażu** z prawdziwymi uczniami w tym planie.
- **Zakres zmian:** wszystko – liczby w YAML, wzory, nowe mechaniki, a w razie potrzeby UI. Najpierw jednak próbować najmniejszej zmiany: parametr, potem wzór, na końcu mechanika.

### Definicje (wspólne dla A i B)
- **Karta skumulowana** – średni wynik działalności z rund 2..N (runda 1 to przygotowanie), tak samo jak w rankingu mistrza gry.
- **Majątek netto** = gotówka + lokaty + kaucje za najem + nadwyżka VAT do przeniesienia + zapasy + kupiony lokal, budynek i grunt **po amortyzacji** (wartość z ewidencji środków trwałych, tak jak w karcie po Z1) + sprzęt po amortyzacji + portfel właściciela − kredyty − debet − zaległości (ZUS, US, czynsz, dostawcy) − dług u Harpagona z odsetkami − wpłaty inwestora ratunkowego (Z3). Sprzęt w leasingu nie jest majątkiem, a przyszłe raty nie są długiem (jak najem). Na tej mierze sprawdza się wyjątek Harpagona i kasyna.
- **Pierwszy plus** – pierwsza runda z dochodem netto > 0.
- **Na minusie** – majątek netto na koniec gry < kapitał startowy (dziś 40 000 zł; jeśli B5 zmieni kapitał, próg idzie za nim).
- **Alarm** – debet ponad limit (krok Z3). W pomiarach „bankructwo” = alarm. Boty nie są ratowane przez inwestora.
- **Wyraźnie wygrywa** – wersja dobra bije średnią w ≥ 80% par gier (ta sama gra, ziarno i rywale).

### Zmiany zasad (krok Z, przed B3)
Ustalone z autorem 29.10.2026. Każda zmiana ma test w `testy/`.
- **Z1 – karta wyników.**
  - Strata obniża kartę: wynik działalności jest ujemny, proporcjonalnie do straty (dziś przy stracie jest 0, więc tydzień ze stratą 500 zł i 20 000 zł znaczy to samo).
  - Załatać cztery dziury:
    - kupiony budynek wchodzi do majątku w rozwoju firmy;
    - majątek liczy się po amortyzacji, a nie po cenach zakupu;
    - zakup sprzętu nie pompuje rozwoju firmy (inwestycja netto, nie „kupić i sprzedać”);
    - odsetki Harpagona (poza KPiR) obniżają kartę, tak jak koszty w KPiR.
  - Uwaga na wzór: dziś wynik to iloczyn wskaźników i wyniku ekonomicznego. Przy stracie lepsze wskaźniki nie mogą pogłębiać minusa (lepsza obsługa klientów nie może dawać gorszej karty) – np. część ujemna bez mnożenia przez wskaźniki albo z odwróconą zależnością. Test: przy tej samej stracie lepsze wskaźniki dają wynik nie gorszy.
  - Zmienia się zasada z notatki „Ustalenia gry” („przy ujemnym wyniku ekonomicznym = 0”) i opis w `gra/INSTRUKCJA.md` – propozycję tekstu notatki zapisać w `raporty/kalibracja/notatki_do_zmiany.md`.
- **Z2 – majątek netto** jako wynik firmy (`stan.wyniki[r][firma]`), w panelu mistrza gry i w eksporcie CSV; definicja wyżej.
- **Z3 – debet ponad limit z rosnącymi skutkami.**
  - blokuje inwestycje i nowe kredyty;
  - mistrz gry dostaje alarm w panelu;
  - mistrz gry może uratować drużynę inwestorem: gotówka w zamian za udział w przyszłych dochodach; wpłata inwestora odejmuje się od majątku netto i liczy się w karcie jak dług (wskaźnik zadłużenia), więc ratunek pozwala grać dalej, ale nie poprawia miejsca w rankingu (ustalone 29.10.2026); warunki (kwota, udział, czas) w YAML;
  - bez odsetek karnych i bez zajęcia majątku.
- **Z4 – liczba lokali na mapie zależna od liczby firm** (4–8 firm), popyt bez zmian.
- **Z5 – bot „jak człowiek”** (nowa strategia, obecne poziomy zostają jako rywale): prognozuje z zeszłotygodniowej sprzedaży, a nie z gotowej prognozy `pp.prognoza` bez szumu; trzy wersje: słaba, średnia, dobra (różnią się staraniem, nie oszukiwaniem).
- **Z6 – kalendarz do kwietnia 2026**: wydarzenia miejskie i święta w `dane/kalendarz/kalendarz.yaml` do 04.2026 (dziś kończą się na 2025), żeby gra 26 rund (do końca lutego 2026) i dłuższa, aż do kwietnia, miała tak samo gęsty kalendarz jak jesień.
- **Z7 – miejsce na pulpicie** liczone jak ranking mistrza gry (karta skumulowana); dziś pulpit bierze wynik działalności tylko z ostatniej rundy (`api/prezentacja.py`, `_dashboard`), a ranking mistrza gry – średnią z rund 2..N.

### Zadania
- **B1 – inwentarz decyzji** `raporty/kalibracja/inwentarz.md`. Dla każdej decyzji (lista w `gra/silnik/decyzje.py`; docstring nie wymienia jeszcze harpagon, kasyno, detektyw, leasing, przejecie, higiena, wlasciciel_stanowisko, wypowiedz – uzupełnić) zapisać:
  - jakie ma opcje i które parametry YAML ją kształtują;
  - czy boty jej używają;
  - **zamierzony kompromis**, czyli kiedy dana opcja powinna wygrywać.

  Do tego lista hipotez „za dobrych” strategii (z raportu A i z czytania kodu) do sprawdzenia w B4. To kompas kalibracji: kompromisy zapisuje się przed strojeniem.
- **B2 – narzędzie porównań** `gra/balans/warianty.py` z testami. Rozgrywa pary gier: ta sama gra, ziarno i rywale, a badana firma różni się tylko jedną decyzją (wymuszoną w decyzjach bota). Wymagania:
  - wiele ziaren (≥ 30 w pełnym pomiarze) i różne konteksty: strategia bazowa, długość gry, strefa, liczba firm (4/6/8);
  - obliczenia równoległe; najpierw profilowanie silnika, żeby wiedzieć, ile gier da się rozegrać. Punkt wyjścia (29.10.2026, laptop autora, 6 rdzeni): gra 18 rund liczy się w ok. 3,5 s przy 4 firmach, 5 s przy 6 i 6,5 s przy 8, więc para gier na 6 firm to ok. 10 s, a na 5 procesach ok. 300 par w 10 minut. Gra bazowa (bez wymuszonej decyzji) jest wspólna dla wszystkich wariantów z tym samym ziarnem i rywalami – liczyć ją raz;
  - przyspieszenie silnika nie może zmienić wyników: przed i po zmianie porównać odcisk (skrót) stanów po każdej rundzie kilku gier botów – muszą być identyczne;
  - wynik w CSV i jako tabela md: średnia różnica karty skumulowanej z przedziałem ufności, odsetek wygranych par, majątek netto, pierwszy plus, alarmy;
  - szybki pomiar (≤ 10 min) do sprawdzania regresji i pełny pomiar uruchamiany w tle, który można przerwać i wznowić z zapisanych CSV. **Ile może trwać pełny pomiar, agent pyta autora przed uruchomieniem** (wieczorem zwykle cała noc, w innym razie do ok. 1 h); bez odpowiedzi – do 1 h;
  - na koniec B2 jeden szybki pomiar na dzisiejszych zasadach („punkt zero”, zapis w dzienniku), żeby w B4 było widać, co zmieniły kroki Z.
- **B3 – boty używają wszystkich opcji.** Każda strategia ma parametry dla każdej decyzji: kupno, lokal niewyposażony, działka, banki, dostawcy, gwiazdki, biuro albo samodzielna księgowość, polisy, licytacje i tak dalej. Bot zachowuje swój charakter, ale może sięgnąć po każdą opcję. Przed B4 – tyle, ile trzeba do pomiaru, i poziomy łatwy < średni < trudny; resztę przed obszarem, którego dotyczy.
- **B4 – pomiar startowy** `raporty/kalibracja/stan_poczatkowy.md` (po krokach Z), tag `kalibracja-start`. Ma pokazać:
  - które opcje dominują, a które są zdominowane, i wynik sprawdzenia hipotez z B1;
  - krzywą trudności (pierwszy plus i wynik na koniec dla każdej wersji bota „jak człowiek” i każdego poziomu);
  - wyniki strategii;
  - wpływ liczby firm (4/6/8);
  - tabelę realiów: nasze liczby wobec orientacyjnych widełek z rzeczywistości.
- **B5 – gospodarka i trudność.** Popyt (pule stref, dni tygodnia, elastyczność ceny, jakość), koszty niezależne od prawa (czynsz, pensje ponad płacę minimalną, składniki) i kapitał startowy, tak żeby spełnić cele trudności. **Wynik do zatwierdzenia przez autora.**
- **B6 – lokale.** Typ (gotowy, niewyposażony, działka) × forma (najem, kupno) × strefa, do tego licytacje i przejęcia.
- **B7 – menu i ceny.** Dania, marże, widełki 50–200% i promocje.
- **B8 – zaopatrzenie.** Dostawcy, gwiazdki, świeżość, magazyn i chłodnia, automatyczne zamawianie, handel między drużynami.
- **B9 – ludzie.** Kanały rekrutacji, umowy, pensje, premie, szkolenia, headhunter i czas właściciela.
- **B10 – marketing.** Reklama, agencje i kanały, promocje, udogodnienia i wyposażenie.
- **B11 – finanse.** Banki, kredyty, lokaty i kredyt odnawialny (dziś bez górnego limitu – sprawdzić z Z3); Harpagon i kasyno według reguły wyjątku; wskaźnik zadłużenia w karcie (kredyt nie może być zawsze zły).
- **B12 – księgowość i urzędy.** Samodzielna księgowość, biuro z OC i bez OC, kary, sanepid i higiena, ubezpieczenia wobec zdarzeń losowych; łamanie zasad (spóźniony ZUS, brak higieny, umowy) średnio się nie opłaca.
- **B13 – karta wyników.** Wagi składowych tak, żeby karty nie dało się „nabić” jednym zabiegiem. Ranking według karty ma być wyraźnie, ale nie idealnie zgodny z majątkiem netto. Potem szybki pomiar wszystkich obszarów.
- **B14 – boty po kalibracji.** Poziomy łatwy < średni < trudny wyraźnie w wynikach, a każda strategia wygrywa w jakimś kontekście. Sprawdzić, że cele z B5 nadal są spełnione. Odświeżyć `balans.symuluj`.
- **B15 – raport końcowy** `raporty/kalibracja/raport.md`:
  - stan przed i po (od tagu `kalibracja-start`);
  - każda zmiana parametru: stara wartość, nowa wartość i powód;
  - poprawione `zrodlo` i `pewnosc` w YAML;
  - propozycje zmian w notatkach w `raporty/kalibracja/notatki_do_zmiany.md` (autor je zatwierdza);
  - instrukcja gracza zaktualizowana, jeśli zmieniły się liczby, które gracz widzi.

### Testy przy kalibracji
Ok. 140 asercji w testach sprawdza dokładne liczby (co do grosza). Żeby kalibracja ich nie łamała przy każdej zmianie:
- testy mechanik (wzory, scenariusze co do grosza) czytają **zamrożoną kopię danych** (`testy/dane_zamrozone/`), a nie `gra/dane/`;
- testy zasad (determinizm, brak liczb w kodzie, schematy, uzgodnienie kasy, boty grają bez błędów) zostają na danych domyślnych.

Przeniesienie testów na zamrożoną kopię to pierwszy krok B2.

### Kiedy obszar jest zbalansowany
- Żadna opcja nie jest najlepsza we wszystkich kontekstach.
- Żadna opcja nie wygrywa ≥ 70% par we wszystkich kontekstach przy istotnej różnicy.
- Każda opcja jest najlepsza, albo w granicach szumu od najlepszej, w co najmniej jednym rozsądnym kontekście.
- Żadna opcja nie jest zawsze najgorsza. Wyjątek: Harpagon i kasyno, które podlegają regule opisanej wyżej.
- Poprzednie obszary się nie zepsuły (szybki pomiar wszystkich obszarów po każdej zmianie).
