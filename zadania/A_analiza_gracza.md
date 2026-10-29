# Zadanie A – analiza Levasa oczami gracza (krok 6)

Wykonawca: **Fable 5.1** w OpenCode. Najpierw przeczytaj `AGENTS.md`, potem `notatki/Plan optymalizacji.md`.

## Twoja rola
Jesteś jednocześnie doświadczonym projektantem gier edukacyjnych, badaczem UX i wymagającym graczem. Autor zbudował grę sam i zna ją od środka, więc nie widzi jej oczami kogoś, kto siada do niej pierwszy raz. Masz mu dać to spojrzenie z zewnątrz oraz pomysły, na które sam mógłby nie wpaść.

**W tym zadaniu nie zmieniasz kodu gry.** Wynikiem jest raport, a wdrożenie zależy od decyzji autora (zadania U w `POSTEP.md`). Grasz na wersji po krokach B1–B5 (sesje idą po kolei): zasady Z1–Z7 są już wdrożone (karta wyników ujemna przy stracie, majątek netto, alarm debetu ponad limit i inwestor ratunkowy, liczba lokali zależna od liczby firm, bot „jak człowiek”, kalendarz do kwietnia 2026), a gospodarka ma liczby zatwierdzone w B5. Kalibracja obszarów (B6–B12) przyjdzie po tobie i po wdrożeniu twoich uwag, więc nierówności opcji (np. jeden bank zawsze najlepszy) zgłaszaj jako tropy dla B, a problemy zrozumiałości, informacji zwrotnej i frustracji – jako uwagi do wdrożenia. Oceniaj też nowe zasady: czy uczeń rozumie ujemną kartę i majątek netto, czy nauczyciel rozumie alarm i inwestora.

## Kontekst
- **Kto gra:** uczniowie szkół średnich i studenci, w drużynach 1–4 osób, 2–3 rundy na tydzień rzeczywisty, przez kilka tygodni. Prowadzi nauczyciel jako mistrz gry.
- **Cel dydaktyczny:** zrozumieć, jak działa mała firma: koszty stałe i zmienne, marża, prognozowanie popytu, gotówka a zysk, kredyt, podatki i KPiR, ludzie, ryzyko, konkurencja.
- **Cel rozgrywki:** gra ma wciągać, nie może zniechęcać i ma nagradzać myślenie, a nie zgadywanie.
- **Wizja i zasady:** `notatki/Główny obraz.md`, `Zarys aplikacji.md`, `Ustalenia gry.md`, `Prawidła świata.md`, `Elementy mapy.md`, `Menu i składniki.md`, `Zdarzenia i historie.md`, `Artstyle.md`.
- **Dla gracza:** `gra/INSTRUKCJA.md` i strona `/jak-grac`.
- **Pomysły ze starej wersji:** `dokumentacja/ROZNICE_LEVAS_STARY.md`.

## Jak pracować
1. **A1 – przygotowanie.**
   - Przeczytaj materiały powyżej.
   - Przejrzyj zakładki w `gra/panel_gracza/static/zakladki/*.js` (każda zakładka ma `decyzje` i `wyniki`; rejestr i menu są w `index.js`) oraz widok `v` w `gra/api/prezentacja.py`. Tak dowiesz się, co dokładnie widzi gracz.
   - Uruchom grę (`AGENTS.md`).
2. **A2 – rozgrywka.** Rozegraj trzy pełne gry po 18 rund. W każdej jest twoja drużyna i 3–4 boty.
   - Jeśli masz przeglądarkę (np. narzędzie Playwright lub browser w OpenCode), graj przez `http://127.0.0.1:8765` i rób zrzuty ekranu.
   - Jeśli jej nie masz, graj przez API: endpointy są w `gra/api/urls.py` (widok `GET /api/gry/<id>/widok/<firma>`, decyzje, wysłanie i przeliczenie), np. klientem testowym Django albo `requests`. Treść ekranu odtwarzaj z kodu zakładek JS i widoku `v`.

   Grasz trzema personami:
   - **Nowicjusz, 16 lat.** Nie wie, co to VAT ani marża, i czyta tylko to, co jest na ekranie. Gdzie się gubi? Co go zniechęca? Czy wie, co zrobić w rundzie 1, 2 i 5?
   - **Optymalizator.** Szuka najlepszej strategii, luk i sposobów na oszukanie gry (np. wieczne nabijanie karty jednym zabiegiem, darmowe pieniądze, decyzje bez konsekwencji). Strategie ocenia **kartą skumulowaną** (średni wynik działalności z rund 2..N, jak ranking mistrza gry) i **majątkiem netto** na koniec gry (definicja w planie), a nie samą gotówką. Zapisuj każdą „za dobrą” strategię z liczbami i sposobem odtworzenia – to tropy dla kalibracji obszarów (B6–B12, dopisywane do inwentarza B1).
   - **Nauczyciel (mistrz gry), panel `/mg/`.** Załóż grę z 3–4 drużynami „uczniów”, które prowadzisz samodzielnie, każda z zaplanowanym błędem: drużyna, która nie zamawia składników; drużyna, która wpada w debet; drużyna bez deklaracji w samodzielnej księgowości; drużyna z cenami poza widełkami. Do tego 2 boty. Czy łatwo założyć grę i prowadzić rundy? Czy z panelu widać, **która drużyna ma problem i jaki**, zanim powiedzą to uczniowie? Czy da się omówić wyniki z klasą? Czy alarm debetu i inwestor ratunkowy (Z3) są jasne i czy majątek netto pomaga omówić wyniki? Czego brakuje do przeprowadzenia lekcji?

   Raport z pomiaru startowego (`raporty/kalibracja/stan_poczatkowy.md`) i `raporty/kalibracja/dziennik.md` czytaj **dopiero po rozegraniu wszystkich gier**, przed pisaniem raportu: najpierw świeże spojrzenie, potem porównanie. W raporcie nie powtarzaj dominacji znalezionych w B4 – wskaż tylko, gdzie widzisz je inaczej albo co B4 przeoczył.

   Po każdej rundzie zapisuj w dzienniku: co widzę, co rozumiem, czego nie rozumiem, co bym zrobił, co się stało i czy wynik był dla mnie zrozumiały. Dziennik trzymaj w `raporty/analiza/dziennik_<persona>.md`. Skrypty pomocnicze trzymaj poza repozytorium albo w `raporty/analiza/skrypty/`.
3. **A3 – raport** `raporty/analiza_gracza.md` (po polsku, dla autora, który nie jest programistą-UX-owcem). Układ:
   1. **Najważniejsze 10 wniosków** – lista od najważniejszego.
   2. **Problemy.** Dotyczą zrozumiałości, informacji zwrotnej po rundzie, nawigacji i liczby zakładek, tempa (nuda, przeciążenie), sprawiedliwości (losowość, boty), frustracji i błędów. Przy błędach podaj sposób odtworzenia. Każdy problem ma dowód: zakładkę, tekst albo `plik:linia`.
   3. **Zmiany w tym, co jest.**
   4. **Nowe funkcje**, szczególnie takie, na które autor mógł nie wpaść. Możliwe kierunki (nie jest to lista do odhaczenia):
      - nauka: cele lekcji, refleksja po rundzie, scenariusze dla nauczyciela, porównanie z realiami;
      - współpraca: role w drużynie, wspólne decyzje;
      - motywacja: osiągnięcia, historia firmy, wydarzenia fabularne;
      - regrywalność: scenariusze startowe, różne miasta i warunki;
      - narzędzia mistrza gry;
      - dostępność i telefon;
      - uczciwość, czyli zapobieganie oszustwom.
   5. **Co działa dobrze – nie psuć.**
   6. **„Za dobre” strategie znalezione przez Optymalizatora** – przekazanie do części B.
   7. **Pytania do autora.**

   Każda pozycja w punktach 2–4 ma mieć:
   - **problem albo cel**, czyli dlaczego;
   - **propozycję**, konkretnie (co gracz zobaczy albo zrobi);
   - **priorytet** P1/P2/P3;
   - **koszt** S/M/L;
   - **wpływ na balans** (czy wymaga ponownej kalibracji);
   - **pliki**, których dotyczy;
   - informację, czy pomysł jest już zaplanowany w notatkach (jeśli tak, nie powtarzaj go jako nowego, tylko podaj odwołanie).

## Poprzeczka jakości
- Pisz konkretnie, z dowodami. Zdanie „UI mogłoby być czytelniejsze” nic nie daje. Zdanie „w zakładce Dostawcy uczeń nie wie, ile zamówić, bo prognoza z Menu nie jest tu pokazana (dostawcy.js:…)” daje.
- Liczy się jakość, nie liczba. Lepiej 15 mocnych propozycji niż 60 ogólników. Pomysły dzikie, ale wartościowe oznacz jako „eksperyment”.
- Szanuj decyzje autora zapisane w notatkach. Jeśli uważasz, że któraś szkodzi grze, napisz to wprost i z uzasadnieniem w „Pytaniach do autora”, ale nie zakładaj z góry, że trzeba ją zmienić.
- Gra jest po polsku i dla polskich szkół, a realia to Lublin w 2026 roku.

## Zakończenie
1. Odhacz A1–A3 w `POSTEP.md`.
2. Zrób commit `A3: raport z analizy oczami gracza` i wypchnij zmiany (`git pull --rebase origin main`, potem `git push origin main`). Pliki: raport, dzienniki i POSTEP.
3. Napisz autorowi krótkie podsumowanie (5–10 zdań) i poproś, żeby zaznaczył w raporcie, które pozycje wdrożyć. Zatwierdzone pozycje dopiszesz potem do `POSTEP.md` jako U1, U2… z odwołaniem do raportu.
