1. Kolorystyka zielona. Szmaragdowy #1e9e5a w panelu gracza, panelu mistrza gry, logowaniu i „Jak grać”. Motywy noc, grafik i talerze zostały bez zmian. Na mapie Twój lokal jest zielony, a lokal wybrany w tej rundzie pomarańczowy. Sprawdziłem tylko składnię plików, wyglądu w przeglądarce nie oglądałem, więc rzuć okiem przed wyjazdem.

2. Notatki (tylko zatwierdzone):
- Ustalenia gry, Prawidła świata, Elementy mapy, Menu i składniki – dopisane poprawki Q1–Q13, m.in. marka firmy w rundzie 1, licytacja od rundy 1, urządzanie lokalu w ostatniej rundzie, tańsze lokale niewyposażone, widełki cen, kredyt na zakup lokalu i brak gotowej prognozy.
- 18 rund zamiast 26 w Ustaleniach gry, Głównym obrazie i Różnicach Revas – Levas.
- Plan implementacji – oznaczony jako archiwum z odnośnikiem do nowego planu.
- Plan działania – kroki 1–4 oznaczone jako zrobione; kroki 5–6 prowadzą do nowego planu.
- Nowa notatka „Plan optymalizacji”. Część A to analiza oczami gracza, część B to kalibracja w zadaniach B1–B15. Są w niej Twoje cele:
  - miarą jest karta wyników;
  - przeciętna drużyna ma pierwszy tydzień n
  - gra trwa bazowo 18 rund;
  - Harpagon i kasyno są ryzykowne, ale czasem się opłacają.

  Pomiar pokazał, że gra jest dziś za łatwa:kie boty kończą 12 rund z 47–100 tys. zł.

3. Materiały dla OpenCode:
- AGENTS.md – omówienie projektu, które OpenCode czyta sam na starcie: mapa folderów, uruchomienie na nowym komputerze, polecenia, budowa silnika i zasady. Wśród zasad jest pytanie Cię o każdą zmianę w notatkach oraz commit i push po każdym zadaniu.
- zadania/A_analiza_gracza.md – instrukcja dla Fable. Gra 3 pełne gry jako nowicjusz, „optymalizator” szukający luk i nauczyciel. Pisze raport z problemami, zmianami i nowymi funkcjami, każda pozycja z priorytetem i kosztem. Kodu nie zmienia.
- zadania/B_kalibracja.md – instrukcja kalibracji: porównywanie par gier, które różnią się jedną decyzją, na wielu
  ziarnach. Po każdej poprawce sprawdza, czysowanych obszarów, i prowadzi dziennik, żebykolejna sesja wiedziała, gdzie skończyła poprzednia.
- POSTEP.md – nowe sekcje A, U (ulepszenia, które zatwierdzisz po raporcie) i B.
- Stare plany – dziennik pracy nocnej przeniesiony do archiwum/. ROZNICE_LEVAS_STARY.md zostaje, bo to źródło pomysłów
  dla analizy.

Polecenia do wklejenia w OpenCode. Na nowym komputerze najpierw git clone https://github.com/Tom-Wasko/Levas.git.

Sesja 1 (model Fable 5.1):
Przeczytaj AGENTS.md, a potem wykonaj zadanie z pliku zadania/A_analiza_gracza.md (A1–A3). Pracuj samodzielnie, po każdym kroku commit i push. Na końcu daj mi krótkie podsumowanie raportu.

Sesja 2 (Opus 5.5 high albo Fable 5.1; może ruszyć równolegle z sesją 1):
Przeczytaj AGENTS.md, a potem wykonaj zadania.md. Po każdym zadaniu testy, commit i push.

Po przeczytaniu raportu z części A:
Wdróż z raportu raporty/analiza_gracza.md pozycje: [numery]. Dopisz je do POSTEP.md jako U1, U2… i rób po kolei.

Potem:
Kontynuuj kalibrację od pierwszego nieodhaczonego zadania B w POSTEP.md, według zadania/B_kalibracja.md.

Ostatnie polecenie wklejasz w każdej kolejnee miejsce w POSTEP.md i dzienniku, w którymskończył.