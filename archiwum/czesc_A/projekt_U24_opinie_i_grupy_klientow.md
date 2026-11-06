# U24 – opinie klientów na mapie i grupy klientów: projekt

4.11.2026, Claude Code (Opus 5.5). Kandydaci (7) i (2) z `dokumentacja/ROZNICE_LEVAS_STARY.md`, którzy zostali po U20.

## Decyzje autora (4.11.2026, okno pytań)

1. **Ocena lokalu** bierze się z przeżyć klientów, osobno dla każdego lokalu: czekanie w kolejce, jakość dań,
   cena wobec strefy, reklamacje. To średnia krocząca z kilku tygodni, a liczba opinii rośnie ze sprzedażą.
2. **Działanie oceny:** wpływa na popyt i ma żartobliwe komentarze klientów z powodami oceny.
3. **Grupy klientów:** pełne 8 grup z koszykiem, jak w starym Levasie (wegetarianie przenoszą udziały).
4. **Kolejność:** obie mechaniki razem, jedno wdrożenie i jeden pomiar balansu na końcu.

## Opinie klientów (7)

- **Ocena tygodnia lokalu (1–5★).** Startuje od 3★. Podnosi ją jakość dań, a obniżają: cena powyżej ceny strefy,
  utracona sprzedaż (kolejka), reklamacje i brakujące dania. Wyposażenie daje mały plus. Wagi trafiają do
  `dane/zalozenia.yaml` (`pewnosc: zalozenie`).
- **Ocena lokalu.** Średnia krocząca ważona liczbą opinii. Opinie tygodnia to mały ułamek klientów lokalu, więc
  ocena dużego lokalu jest stabilniejsza. Nowy lokal nie ma opinii i ma mnożnik neutralny.
- **Popyt.** Mnożnik atrakcyjności lokalu zależy od oceny i od zaufania do niej (liczba opinii n: n ÷ (n + n₀)).
  Zastępuje dzisiejszy mnożnik z zadowolenia klientów karty (`popyt.mnoznik_zadowolenia`).
  - Wskaźnik karty liczy się jak dotąd, więc kalibracja karty się nie zmienia.
  - Wagi dobieram tak, żeby średni lokal miał mnożnik zbliżony do dzisiejszego.
- **Widoczność.** Na mapie przy każdym lokalu (wszystkie drużyny i mistrz gry): gwiazdki i liczba opinii. Po
  kliknięciu 2–3 krótkie żartobliwe komentarze, losowane strumieniem z szablonów przypisanych do powodów (kolejka,
  cena, jakość, reklamacje, brak dań). Są komentarze dobre i złe. Gracz widzi u siebie też rozbicie powodów.

## Grupy klientów (2)

- **8 grup** (`dane/mapa/grupy.yaml`): studenci, uczniowie, biurowi, imprezowicze, rodziny, turyści, goście
  wydarzeń, podróżni. Każda grupa ma:
  - wrażliwość na cenę (mnożnik wrażliwości strefy),
  - wagę jakości i wagę czekania (czekanie obniża ocenę i popyt silniej u podróżnych i biurowych),
  - rozkład dni tygodnia,
  - koszyk dań (udziały w daniach),
  - udział wegetarian.
- **Strefy** mają udziały grup (suma 1) zamiast jednego profilu. Z udziałów i profili grup wynikają dzisiejsza
  wrażliwość cenowa i dni tygodnia strefy. Goście wydarzeń pojawiają się, gdy kalendarz miejski ma wydarzenie
  w strefie: wydarzenie dokłada pulę tej grupy.
- **Koszyk.** Pula grupy w strefie dzieli się na dania według koszyka.
  - Wegetarianie nie kupują dań mięsnych, więc ich część popytu na mięso przechodzi na dania bezmięsne
    z koszyka (przeniesienie udziałów).
  - Gdy lokal nie ma dania z koszyka, część klientów wybiera u niego inne danie z koszyka, zamiast od razu odejść
    do opcji zewnętrznej.
- **Warunek kalibracji.** Przy dzisiejszych ofertach suma pul grup na strefę i danie ma dać w przybliżeniu
  dzisiejsze pule. Pule stref i popyt roczny dań zostają, a grupy zmieniają to, kto i jak reaguje.
- **Widoczność.** W zakładce Klienci widać skład grup strefy i ich upodobania, opisane krótko i z humorem. Raport
  sprzedaży pokazuje, które grupy kupowały w lokalu.

## Wdrożenie (4.11.2026) – czym różni się od projektu

- Wszystkie liczby są w `dane/mapa/klienci.yaml` (grupy, strefy, koszyki, opinie, komentarze), bez
  `zalozenia.yaml`. Brak pliku wyłącza obie mechaniki (zamrożona kopia testów liczy popyt jak przed U24).
- Dni tygodnia zostają ze strefy (`popyt.yaml`), grupy nie mają własnego rozkładu dni. Inaczej zmieniłby się
  kalibrowany kształt tygodnia stref.
- Ocena tygodnia startuje od 3,6★ (nie 3★), a mnożnik popytu = (ocena ÷ 3,3)^(0,4 × zaufanie). Przy tych liczbach
  średni lokal botów ma mnożnik ok. 1,0, a rozpiętość 0,86–1,06, podobnie jak dawny mnożnik karty (0,83–1,05).
- Zastępstwo: 10% klientów bez ulubionego dania bierze inne danie z koszyka w tym samym lokalu (przy 35%
  lokal premium z wąskim menu zarabiał prawie 2× więcej).
- Wskaźnik „Zadowolenie klientów” w karcie liczy się jak dotąd, ale nie zmienia już popytu – robią to opinie.

## Pomiar i teksty

- Jeden pomiar na końcu: poziomy × strategie × ziarna, przed i po. Cele:
  - przychód i karta botów w granicach ok. ±5%, bez alarmów,
  - lokale w różnych strefach wymagają innej oferty,
  - zła obsługa widocznie obniża ocenę i popyt.
- Teksty: INSTRUKCJA rozdz. 6 (Klienci) i 15, kółka „i” na mapie i w zakładce Klienci. Po wdrożeniu odświeżyć PDF.
- Testy: determinizm, ocena rośnie i spada z przyczyn, koszyk przenosi wegetarian, zachowanie pul przy
  dzisiejszych ofertach.
