# Zadania dla sesji – polecenia do wklejenia

Kolejność i cele: `notatki/Plan optymalizacji.md`. Sesje idą **po kolei**: najpierw B1–B5, potem A, wdrożenie uwag
z A (U), kontrola K i B6–B15 (zmiana z 29.10.2026 – A ocenia grę już po zmianach zasad i z docelową trudnością).
Na nowym komputerze najpierw `git clone https://github.com/Tom-Wasko/Levas.git` i uruchomienie według `AGENTS.md`.
Na początku każdej sesji agent robi `git pull --rebase origin main`.

## Sesja 1 – B1, B2, zmiany zasad Z, B3, B4 i B5 (Claude Code albo OpenCode, Opus 5.5) – zrobiona 29.10.2026
```
Przeczytaj AGENTS.md, notatki/Plan optymalizacji.md i zadania/B_kalibracja.md. Wykonaj po kolei
B1, B2, Z1–Z7, B3 (część potrzebna do pomiaru), B4 i B5 według planu. Po każdym zadaniu testy, ruff,
sprawdz, wpis w raporty/kalibracja/dziennik.md, POSTEP.md, commit i push. Przed pełnym pomiarem
zapytaj mnie, ile może trwać (bez odpowiedzi – do 1 h). Po B4 daj mi podsumowanie pomiaru startowego
i rób B5. Po B5 nie przechodź dalej: pokaż mi tabelę zmienionych liczb (stara, nowa, powód) i wyniki
trudności, i poczekaj na zatwierdzenie.
```

## Sesja 2 – część A (Fable 5.1 w OpenCode, po zatwierdzeniu B5)
```
Przeczytaj AGENTS.md i notatki/Plan optymalizacji.md, a potem wykonaj zadanie z pliku
zadania/A_analiza_gracza.md (A1–A3). Pracuj samodzielnie, po każdym kroku commit i push.
Kodu gry nie zmieniaj. Raport z pomiaru startowego czytaj dopiero po grach. Na końcu daj mi
krótkie podsumowanie raportu.
```

## Sesja 3 – wdrożenie uwag z A i kontrola K
```
Wdróż z raportu raporty/analiza_gracza.md pozycje: [numery]. Dopisz je do POSTEP.md jako U1, U2…
i rób po kolei, każdą z testem, commitem i pushem. „Za dobre” strategie z raportu dopisz do
raporty/kalibracja/inwentarz.md. Potem zrób K według zadania/B_kalibracja.md i pokaż mi wynik.
```

## Kolejne sesje – B6–B15
```
Kontynuuj kalibrację od pierwszego nieodhaczonego zadania B w POSTEP.md, według zadania/B_kalibracja.md.
Zacznij od raporty/kalibracja/dziennik.md.
```
