# Postęp

Postęp prac według [Planu implementacji](notatki/Plan%20implementacji.md). 1 commit = 1 zadanie (`F2.1: …`).

## Krok 2 – kopia Revasa i przebudowa pod Levas
- [x] F2.1 Kopia `revas_gra` → `gra/` (bez kalibracji, gry przez GitHub, importu stanu i raportów), pyproject + ruff, testy przechodzą
- [x] F2.2 Django zamiast Flaska: aplikacje `gry/` (modele Gra/Runda/Decyzja w SQLite), `api/` (widoki JSON), `panel_gracza/` (strony, zakładki JS bez zmian, komenda `graj`); CSRF w zapytaniach JS; testy API
- [x] F2.3 Model pydantic, grosze, `WERSJA_STANU` – modele stanu w pydantic (`extra="forbid"`), kwoty jako int grosze (pola `…_gr`, silnik liczy w złotych przez właściwości zaokrąglające do grosza), widok w złotych dla zakładek (`do_slownika`), testy własności (hypothesis): zapis → odczyt, to samo ziarno = ten sam wynik; wyniki gry botów bez zmian
- [x] F2.4 Dane w YAML ze schematami i `zrodlo` – `dane/*.yaml` (usługi, sprzęt, zasoby, dostawcy, kandydaci z parametrami losowania, katalog, boty, założenia), każdy plik/sekcja/parametr ze `zrodlo`; schematy pydantic (`silnik/schematy.py`) i odwołania między plikami: `python -m silnik.dane sprawdz`; liczby gry z kodu silnika (rynek pracy, strategie botów, dostawcy, limit stanowisk) przeniesione do danych, test pilnuje, żeby nie wróciły; wyniki gry botów bez zmian
- [x] F2.5 Nazwane strumienie losowości (PCG64) – `silnik/losowosc.py`: `strumien(ziarno, runda, cel, *klucze)` → `Generator(PCG64)` z pełnego skrótu SHA-256 (`SeedSequence`), cele w `CELE`; testy: wartości wzorcowe, niezależność od kolejności, różne klucze = różne liczby, losowość tylko z tego modułu (napisane od zera – kodu starego Levasa nie ma na dysku)
- [ ] F2.6 Kebab zamiast klubu fitness
- [ ] F2.7 Rundy tygodniowe
- [ ] F2.8 Podstawowy panel mistrza gry

## Krok 3a, 3b, 4
Zadania F3a.1–F3a.15, F3b.1–F3b.9, F4.1–F4.7 – jeszcze nie zaczęte.
