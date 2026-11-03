# A1 – przygotowanie do analizy oczami gracza

Wykonawca: Claude Code (Opus 5.5) zamiast Fable – decyzja autora 3.11.2026, gałąź `analiza-a`.
Gra na wersji po Z1–Z6 (commit 28acb40) – menu z grupami, decyzje per lokal, Auchan, reklama z emisjami.

## Co przeczytałem
- `AGENTS.md`, `notatki/Plan optymalizacji.md` (część A, definicje majątku netto, alarmu, pierwszego plusa),
  `Główny obraz`, `Zarys aplikacji`, `Ustalenia gry` (karta ze stratą, debet ponad limit, inwestor, boty
  „jak człowiek”, harmonogram odblokowań), `zadania/A_analiza_gracza.md`.
- `gra/INSTRUKCJA.md` – 15 rozdziałów; ważne dla analizy: rozdz. 3 (karta i strata), 4–5 (tydzień 1 i 2),
  13 (rozwój: „nowy sprzęt i wyposażenie podnoszą rozwój firmy”), 14 (odblokowania), 15 (10 rad).
- `dokumentacja/ROZNICE_LEVAS_STARY.md` – 12 kandydatów ze starej wersji; propozycja dokumentu: okrojona
  dynamika pracowników (4), opinie klientów na mapie (7), grupy klientów w strefach (2). W raporcie A3
  odwołuję się do tych numerów zamiast zgłaszać je jako nowe.
- Zakładki: `panel_gracza/static/zakladki/index.js` – 13 pozycji menu (Mapa, Wyniki, Lokale, Rynek, Parki
  i zdarzenia, Marketing, Inwestycje, Handel, Firma, Finanse, Księgowość, Lista błędów, Wyślij) i 26
  podzakładek; kasyno „Nocna 13” ukryte do zaproszenia. Widok `v`: `api/prezentacja.py: widok` (decyzje,
  szkic, wyniki rundy, lista błędów, wnioski, karta skumulowana, dashboard).

## Jak gram (A2)
- Osobny serwer analizy na porcie 8766 z osobną bazą `raporty/analiza/analiza.sqlite3`
  (`skrypty/ustawienia_analizy.py`), żeby nie mieszać z grami autora.
- Gracz przez API tak jak przeglądarka (`skrypty/gracz.py: Klient`): mistrz gry – lokalne logowanie,
  uczeń – logowanie kontem z `/konta/login/`. Decyzje: kalkulator botów „jak człowiek” jako „co by kliknął
  gracz” + zmiany persony (błędy nowicjusza, warianty optymalizatora, błędy drużyn nauczyciela).
- Zrzuty ekranu: Chrome bez okna (`gracz.zrzut`) – `raporty/analiza/zrzuty/`.
- Optymalizator szybciej – w silniku bez API (`skrypty/eksperymenty.py`), 18 rund × 3 ziarna na wariant.
