[[Plan działania]] · [[Ustalenia gry]] · [[Główny obraz]] · [[Plan implementacji]] (archiwum)

# Plan optymalizacji – kroki 5–6

Zastępuje [[Plan implementacji]] (kroki 1–4 zrobione 28.10.2026). Wykonuje go OpenCode (modele Opus 5.5 high albo Fable 5.1). Zasady pracy w repozytorium są w `AGENTS.md`, szczegółowe instrukcje dla sesji w `zadania/`. Postęp (checkboxy) jest w `POSTEP.md`, a nie w tej notatce.

## Kolejność
1. **Część A – analiza oczami gracza** (Fable 5.1, `zadania/A_analiza_gracza.md`). Kod się nie zmienia, powstaje tylko raport z propozycjami.
2. **B1–B4 – narzędzia i pomiar startowy** (`zadania/B_kalibracja.md`). Można je robić równolegle z A, bo nie zmieniają zasad gry.
3. **Decyzja autora o raporcie z A.** Zatwierdzone pozycje trafiają do `POSTEP.md` jako U1, U2… i są wdrażane **przed** kalibracją obszarów, których dotyczą, bo każda nowa mechanika zmienia balans.
4. **B5–B15 – kalibracja obszar po obszarze**, a na końcu raport.

## Część A – analiza oczami gracza (krok 6)
- **A1 – przygotowanie.** Przeczytać instrukcję gracza, notatki i kod zakładek, a potem uruchomić grę.
- **A2 – rozgrywka.** Trzy pełne gry (18 rund, z botami), każda jako inna persona:
  - uczeń-nowicjusz bez wiedzy o firmach i księgowości,
  - ambitny gracz szukający luk i najlepszej strategii,
  - nauczyciel jako mistrz gry.

  W każdej rundzie trzeba obejrzeć to, co widzi gracz, i prowadzić dziennik wrażeń.
- **A3 – raport** `raporty/analiza_gracza.md`. Zawiera:
  - problemy (z dowodami),
  - propozycje zmian istniejących elementów,
  - nowe funkcje, na które autor mógł nie wpaść,
  - listę rzeczy, które działają dobrze i których nie należy psuć,
  - pytania do autora.

  Każda pozycja ma priorytet, koszt (S/M/L), wpływ na balans i pliki, których dotyczy.

## Część B – kalibracja (krok 5)

### Cele (ustalone z autorem 28.10.2026)
- **Przede wszystkim balans.** Liczby mają przynajmniej przypominać realia (kebab w Lublinie, 2026).
- **Żadnej jednoznacznie najlepszej opcji** w żadnej decyzji: lokal, forma, strefa, bank, dostawca, jakość, ceny, ludzie, reklama, księgowość, ubezpieczenia i tak dalej. Każda opcja ma sytuację, w której się opłaca, i sytuację, w której nie.
- **Miara „lepszej decyzji”: karta wyników.** Liczy się wynik działalności, tak jak w rankingu mistrza gry (`api/prezentacja.py`). Pomocniczo: majątek netto na koniec gry, pierwsza runda na plusie i bankructwa.
- **Wyjątek: Harpagon i kasyno.** Średnio się nie opłacają, ale w konkretnej sytuacji (pilnie brakuje gotówki, końcówka gry) bywają opłacalne. To lekcja o ryzyku.
- **Trudność:**
  - przeciętna drużyna (bot średni) ma pierwszy tydzień na plusie w rundzie 4–6;
  - słaba drużyna (bot łatwy) może skończyć grę na minusie, ale nie bankrutuje;
  - dobra drużyna wyraźnie wygrywa.

  Dziś (12 rund, ziarno 7, poziom średni) każdy bot kończy grę z 47–100 tys. zł przy 40 tys. zł kapitału, czyli gra jest za łatwa.
- **Długość gry:** bazowo 18 rund. Sprawdzić także 12 i 26 rund, żeby krótsza ani dłuższa gra się nie psuła.
- **Zakres zmian:** wszystko – liczby w YAML, wzory, nowe mechaniki, a w razie potrzeby UI. Najpierw jednak próbować najmniejszej zmiany: parametr, potem wzór, na końcu mechanika.

### Zadania
- **B1 – inwentarz decyzji** `raporty/kalibracja/inwentarz.md`. Dla każdej decyzji (lista w `gra/silnik/decyzje.py`) zapisać:
  - jakie ma opcje i które parametry YAML ją kształtują;
  - czy boty jej używają;
  - **zamierzony kompromis**, czyli kiedy dana opcja powinna wygrywać.

  To kompas kalibracji: kompromisy zapisuje się przed strojeniem.
- **B2 – narzędzie porównań** `gra/balans/warianty.py` z testami. Rozgrywa pary gier: ta sama gra, ziarno i rywale, a badana firma różni się tylko jedną decyzją. Wymagania:
  - wiele ziaren (≥ 30 w pełnym pomiarze) i różne konteksty: strategia bazowa, długość gry, strefa, liczba rywali;
  - obliczenia równoległe;
  - wynik w CSV i jako tabela md: średnia różnica karty z przedziałem ufności, odsetek wygranych par, majątek netto, pierwsza runda na plusie, bankructwa;
  - szybki pomiar (≤ 10 min) do sprawdzania regresji i pełny pomiar uruchamiany w tle.
- **B3 – boty używają wszystkich opcji.** Każda strategia ma parametry dla każdej decyzji: kupno, lokal niewyposażony, działka, banki, dostawcy, gwiazdki, biuro albo samodzielna księgowość, polisy, licytacje i tak dalej. Bot zachowuje swój charakter, ale może sięgnąć po każdą opcję. Bez tego nie da się mierzyć wariantów ani grać z ciekawymi rywalami.
- **B4 – pomiar startowy** `raporty/kalibracja/stan_poczatkowy.md`. Ma pokazać:
  - które opcje dominują, a które są zdominowane;
  - krzywą trudności (pierwsza runda na plusie i wynik na koniec dla każdego poziomu bota);
  - wyniki strategii;
  - tabelę realiów: nasze liczby wobec orientacyjnych widełek z rzeczywistości.
- **B5 – gospodarka i trudność.** Popyt (pule stref, dni tygodnia, elastyczność ceny, jakość), koszty (czynsz, pensje wobec płacy minimalnej 2026, składniki, ZUS, podatki) i kapitał startowy, tak żeby spełnić cele trudności.
- **B6 – lokale.** Typ (gotowy, niewyposażony, działka) × forma (najem, kupno) × strefa, do tego licytacje i przejęcia.
- **B7 – menu i ceny.** Dania, marże, widełki 50–200% i promocje.
- **B8 – zaopatrzenie.** Dostawcy, gwiazdki, świeżość, magazyn i chłodnia, automatyczne zamawianie, handel między drużynami.
- **B9 – ludzie.** Kanały rekrutacji, umowy, pensje, premie, szkolenia, headhunter i czas właściciela.
- **B10 – marketing.** Reklama, agencje i kanały, promocje, udogodnienia i wyposażenie.
- **B11 – finanse.** Banki, kredyty, lokaty i kredyt odnawialny; Harpagon i kasyno według reguły wyjątku; wskaźnik zadłużenia w karcie (kredyt nie może być zawsze zły).
- **B12 – księgowość i urzędy.** Samodzielna księgowość, biuro z OC i bez OC, kary, sanepid i higiena, ubezpieczenia wobec zdarzeń losowych.
- **B13 – karta wyników.** Wagi składowych tak, żeby karty nie dało się „nabić” jednym zabiegiem. Ranking według karty ma być wyraźnie, ale nie idealnie zgodny z majątkiem netto.
- **B14 – boty po kalibracji.** Poziomy łatwy < średni < trudny wyraźnie w wynikach, a każda strategia wygrywa w jakimś kontekście. Odświeżyć `balans.symuluj`.
- **B15 – raport końcowy** `raporty/kalibracja/raport.md`:
  - stan przed i po;
  - każda zmiana parametru: stara wartość, nowa wartość i powód;
  - poprawione `zrodlo` i `pewnosc` w YAML;
  - propozycje zmian w notatkach w `raporty/kalibracja/notatki_do_zmiany.md` (autor je zatwierdza);
  - instrukcja gracza zaktualizowana, jeśli zmieniły się liczby, które gracz widzi.

### Kiedy obszar jest zbalansowany
- Żadna opcja nie jest najlepsza we wszystkich kontekstach.
- Żadna opcja nie wygrywa ≥ 70% par we wszystkich kontekstach przy istotnej różnicy.
- Każda opcja jest najlepsza, albo w granicach szumu od najlepszej, w co najmniej jednym rozsądnym kontekście.
- Żadna opcja nie jest zawsze najgorsza. Wyjątek: Harpagon i kasyno, które podlegają regule opisanej wyżej.
- Poprzednie obszary się nie zepsuły (szybki pomiar wszystkich obszarów po każdej zmianie).
