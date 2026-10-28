# Zadanie B – kalibracja i balans (krok 5)

Wykonawca: **Opus 5.5 (high)** albo **Fable 5.1** w OpenCode. Najpierw przeczytaj `AGENTS.md`, potem `notatki/Plan optymalizacji.md`. Cele, zadania B1–B15 i kryteria „zbalansowania” są tam i obowiązują.

## Twoja rola
Jesteś projektantem systemów gry i analitykiem danych. Masz dostroić wszystkie parametry i funkcje Levasa tak, żeby:
1. **w żadnej decyzji nie było jednoznacznie najlepszej opcji** – każda ma swoją sytuację;
2. gra miała zamierzoną **krzywą trudności**;
3. liczby **przypominały realia** kebaba w Lublinie w 2026 roku.

Balans jest ważniejszy od realizmu, ale realizm nie może być rażąco złamany.

## Od czego zacząć sesję
1. Otwórz `POSTEP.md` i znajdź pierwsze nieodhaczone zadanie B (albo U, jeśli autor tak zdecydował).
2. Przeczytaj `raporty/kalibracja/dziennik.md`. To twoja pamięć między sesjami. Po każdym kroku zapisuj w nim: co zmierzono, co zmieniono, co wyszło i co dalej.
3. Jeśli istnieje `raporty/analiza_gracza.md`, przeczytaj sekcję „za dobre strategie”. To gotowe tropy dominacji.

## Metoda (dla każdego obszaru B5–B13)
1. **Zmierz.** Uruchom narzędzie z B2 dla wszystkich opcji obszaru i kontekstów. Pełny pomiar uruchamiaj w tle i w tym czasie czytaj kod.
2. **Zdiagnozuj.** Ustal, *dlaczego* opcja dominuje albo przegrywa: znajdź wzór i parametr w kodzie (`plik:linia`). Porównaj to z zamierzonym kompromisem z `raporty/kalibracja/inwentarz.md`.
3. **Popraw najmniejszą zmianą.** Kolejność prób: parametr w YAML → wzór → nowa mechanika (np. malejące korzyści, koszt utrzymania, ryzyko). Sprawdź realizm: czy liczba mieści się w orientacyjnych widełkach. Gdy znajdziesz źródło, wpisz je do `zrodlo`.
4. **Zmierz ponownie** dany obszar, a potem szybki pomiar wszystkich obszarów, żeby wykryć regresję. Strojenie jednego obszaru często psuje inny.
5. **Sprawdź jakość:** `pytest`, `ruff`, `sprawdz`. Jeśli testy z oczekiwanymi liczbami zmieniły się celowo, zaktualizuj je i opisz w commicie.
6. **Zapisz postęp:** wpis w dzienniku, odhaczenie w `POSTEP.md`, commit `B6: …` z liczbami przed i po w treści, a potem `git push origin main`.

Jeśli po 3 rzetelnych próbach obszaru nie da się zbalansować bez dużej zmiany zasad, opisz problem i propozycję w raporcie, zapytaj autora i przejdź do następnego obszaru.

## Orientacyjne realia (do sprawdzenia, nie dogmat)
Jeśli masz dostęp do sieci, zweryfikuj te liczby i podaj źródła w `zrodlo`. Widełki są szacunkowe:
- cena kebaba w Polsce w 2026 roku: ok. 25–40 zł;
- koszt składników: ok. 25–35% ceny;
- koszty pracy: ok. 25–35% przychodu;
- czynsz: ok. 8–15% przychodu;
- marża netto dobrze prowadzonego lokalu: kilka do kilkunastu procent;
- mały lokal obsługuje od kilkudziesięciu do kilkuset klientów dziennie;
- płaca minimalna 2026 jest w `dane/zalozenia.yaml`.

## Pułapki
- **Szum losowy.** Wnioskuj tylko z porównań parami (ta sama gra i ziarno, różni się jedna decyzja) i na wielu ziarnach. Pojedyncza gra niczego nie dowodzi.
- **Boty to nie gracze.** Bot „niemożliwy” oszukuje przy popycie, więc nie używaj go do oceny opcji. Boty nie myślą jak ludzie, dlatego hipotezy z analizy części A sprawdzaj także „ręcznie”: rozpisz wariant decyzji, który wybrałby rozsądny człowiek.
- **Goodhart.** Nie strój karty wyników pod boty. Karta ma nagradzać dobrą firmę, a nie konkretny zabieg.
- **Determinizm.** To samo ziarno musi dawać ten sam wynik. Losowość bierz tylko z `silnik/losowosc.py`.
- **Czas obliczeń.** 12 rund gry botów trwa ok. 5 s. Szybki pomiar musi mieścić się w ≤ 10 min, żeby dało się go uruchamiać po każdej zmianie.
- **Długość gry.** Bazowo 18 rund, ale 12 i 26 rund też nie mogą się psuć: np. kupno lokalu może się opłacać dopiero w dłuższej grze, i to jest w porządku.

## Zakończenie (B15)
1. Napisz raport końcowy `raporty/kalibracja/raport.md`:
   - tabele przed i po;
   - wszystkie zmiany parametrów: stara wartość, nowa wartość i powód;
   - otwarte problemy.
2. Zapisz propozycje zmian w notatkach w `raporty/kalibracja/notatki_do_zmiany.md` – autor je zatwierdzi, ty ich nie wprowadzasz.
3. Zaktualizuj instrukcję gracza, jeśli zmieniły się liczby widoczne dla gracza.
4. Na koniec zrób commit, wypchnij zmiany i napisz autorowi krótkie podsumowanie.
