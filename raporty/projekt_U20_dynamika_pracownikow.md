# U20 – okrojona dynamika pracowników: projekt do decyzji autora

4.11.2026, Claude Code (Opus 5.5). Pozycja [21] raportu `raporty/analiza_gracza.md`, kandydat (4)
z `dokumentacja/ROZNICE_LEVAS_STARY.md`. Kandydaci (7) opinie na mapie i (2) grupy klientów – dopiero po (4).

## Dlaczego

- **Instrukcja obiecuje coś, czego silnik nie robi.** INSTRUKCJA rozdz. 8: „Niezadowoleni pracują gorzej
  i odchodzą”. Podobnie podpowiedź z U19 („Dbaj o ludzi”). W silniku zadowolenie pracowników to tylko
  jeden wskaźnik karty dla całej firmy (`silnik/wyniki/karta.py: zadowolenie_pracownikow`). Nikt nie odchodzi
  sam i nikt nie pracuje gorzej.
- **Pensja to słaba dźwignia.** Optymalizator (A2): płaca minimalna daje +0,01 karty. Zadowolenie stoi na
  ok. 0,91–0,98 i oszczędność na pensjach się opłaca. Uczeń nie ma powodu patrzeć na ludzi.

## Proponowany zakres (etap 1, koszt M)

1. **Zadowolenie każdej osoby** – ten sam wzór co dziś, liczony na osobę: jej pensja ÷ preferowana, sprzęt
   jej stanowiska, udogodnienia jej lokalu, szkolenia firmy. Dochodzi **przeciążenie**: wykorzystanie
   godzin powyżej progu (np. 95% przez tydzień) obniża zadowolenie. Wskaźnik karty = średnia osób, więc
   kalibracja karty zostaje (przy równych pensjach wynik ten sam co dziś).
2. **Odejście z niezadowolenia** – osoba poniżej progu (np. 0,85) przez 2 tygodnie z rzędu składa
   wypowiedzenie. Działa jak dziś przy odejściu do konkurencji: umowa o pracę 2 rundy, zlecenie od razu,
   wraca do puli. Bez losowania, więc gracz może to przewidzieć.
3. **Ostrzeżenie tydzień wcześniej** – w Lokale ▸ Ludzie i na liście błędów: „Kowalski jest niezadowolony
   (pensja 15% poniżej oczekiwanej, przepracowanie) – za tydzień złoży wypowiedzenie”. Podwyżka albo
   odciążenie ratuje sprawę.
4. **Boty** – poziom łatwy ignoruje ostrzeżenie, średni i trudny podnoszą pensję do progu. Pole w
   `dane/boty.yaml`.
5. Teksty (INSTRUKCJA rozdz. 8 i 15, kółka „i”), testy, pomiar balansu (płaca minimalna wobec preferowanej,
   9 strategii × 3 poziomy).

Progi i wagi trafiają do `dane/zalozenia.yaml` (`pewnosc: zalozenie`) i są do kalibracji.

## Poza etapem 1 (osobna decyzja)

- **Ukryte cechy** (szybki, miły, spóźnialski, lojalny…) ujawniane po 2 tygodniach pracy – etap 2, koszt M.
- **Niższa wydajność niezadowolonych** (np. −10% godzin) – mocno zmienia obsługę kolejek, więc
  proponuję dopiero po pomiarze etapu 1.
- L4, kradzieże z kasy i reputacja pracodawcy – nie teraz (koszt L, dużo losowości).

## Gdyby etap 1 odpadł

Trzeba poprawić teksty, które dziś mówią nieprawdę: INSTRUKCJA rozdz. 8 („Niezadowoleni pracują gorzej
i odchodzą”) i podpowiedź „Dbaj o ludzi” (`api/prezentacja.py: PODPOWIEDZI`).

## Decyzja autora i wdrożenie (4.11.2026)

- **Zakres:** etap 1 + ukryte cechy. Cech nie ujawnia gra. Gracz wnioskuje je z krótkiego, żartobliwego opisu
  (1–2 zdania) pod kółkiem „i” przy pracowniku i kandydacie.
- **Odejście:** nie jest pewne po 2 tygodniach. Szansa rośnie z niezadowoleniem. Pierwszy tydzień poniżej progu to
  tylko ostrzeżenie, od drugiego z rzędu jest losowanie (5% za każde 0,01 poniżej progu 0,87, najwyżej 50%,
  × mnożnik cechy).
- **Cechy** (`dane/kandydaci.yaml: cechy`): zwyczajny, lojalny, niespokojny duch, materialista, wygodnicki,
  pracoholik, szybki, niespieszny, pogodny, maruda. Każda zmienia wagi składników zadowolenia, szansę
  odejścia albo wydajność (±10% godzin).
- **Niższa wydajność niezadowolonych** – nie wdrożona (zostaje do decyzji po pomiarze). Wydajność zależy tylko od cechy.
- **Kod:** `silnik/ludzie/zadowolenie.py` (wzór, odejścia, ostrzeżenia, ukrywanie cech w widoku gracza), boty:
  `dba_o_ludzi` w `dane/boty.yaml`, panel: `panel_gracza/static/zakladki/hr.js`.
- **Pomiar balansu i warianty progu:** `raporty/kalibracja/dziennik.md`, sekcja U20.
