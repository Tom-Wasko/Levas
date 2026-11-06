# Ufajnianie – przekazanie pracy (czytaj najpierw, jeśli zaczynasz bez wiedzy o tej pracy)

Aktualizowane po każdym zadaniu. Ostatnia aktualizacja: patrz `git log -1 -- raporty/ufajnianie/PRZEKAZANIE.md`.

## Gdzie i jak pracujesz
- Worktree: `C:\Users\PC\Pulpit\Levas\levas_ufajnianie`, gałąź **`ufajnianie`** (od `kalibracja-b6@9e2afb9`, czyli
  main + B6–B13 + przekazanie B14). Push: `git push origin ufajnianie`. **Nie pushuj na main** – scalanie robi się
  osobno według `SCALANIE.md` (autor zlecił je na 7.11.2026, po zakończeniu pracy nocnej).
- `C:\Users\PC\Pulpit\Levas\levas_gra` to główny checkout na gałęzi `kalibracja-b6`. Pracuje tam druga sesja
  Claude Code („bambiczkowanie”), która liczy pomiary B14 i commituje na `kalibracja-b6`. **Nie zmieniaj tam niczego**
  (kodu, `gra/dane/`, gałęzi, katalogów `raporty/kalibracja/pomiary/`). Kontakt z nią: `ListAgents` → `SendMessage`.
- Python: `../levas_gra/gra/.venv/Scripts/python` (wspólny venv – pakiety bez instalacji edytowalnej, więc kod
  bierze się z bieżącego katalogu). Nie wołaj gołego `python` w Bash na Windows (zawiesza się).
- Polecenia (w `gra/`):
  - `../../levas_gra/gra/.venv/Scripts/python -m pytest -q -p no:cacheprovider` (pełne testy ok. kilku minut)
  - `../../levas_gra/gra/.venv/Scripts/python -m ruff check .`
  - `../../levas_gra/gra/.venv/Scripts/python -X utf8 -m silnik.dane sprawdz`
  - serwer do oglądania: `../../levas_gra/gra/.venv/Scripts/python manage.py runserver 8777` (inny port niż 8765/8766)
- Zasady repo: `AGENTS.md` (wszystkie liczby gry w `gra/dane/*.yaml` jako `{wartosc, pewnosc, zrodlo}`, kwoty w
  groszach `…_gr`, losowość tylko przez `silnik/losowosc.py: strumien`, kod i teksty po polsku).
- Zgoda autora (6.11.2026) na zmiany w całym repo, także w `notatki/`.
- Autor prosi: do prostych, mechanicznych prac używaj agentów z `model: "sonnet"` (oszczędność tokenów).

## Po każdym zadaniu UF
1. testy, ruff, `sprawdz`; przy zmianach widocznych dla gracza – dopisz do `gra/INSTRUKCJA.md`;
2. odhacz zadanie w `POSTEP.md` (jedno zdanie, co zrobione);
3. zaktualizuj sekcję „Stan” niżej (co zrobione, co w połowie, pułapki);
4. commit `UFn: krótki opis` z linią `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; push na `ufajnianie`.

## Plan i ustalenia
- `plan.md` – wszystkie ustalenia z autorem (układ menu, decyzje do każdej poprawki) i **plan implementacji**
  (kolejność od najtrudniejszych, szczegóły techniczne każdego zadania).
- `SCALANIE.md` – jak jutro skleić `kalibracja-b6` i `ufajnianie` do `main`.

## Stan
- [x] UF0 sprzątanie (Pulpit\Levas, repo), notatki, plan, przekazanie – 6.11.2026 wieczorem.
- [x] UF15 nowy układ menu – 6.11.2026 w nocy. Co jest gdzie:
  - `zakladki/index.js`: `MENU` (grupy z planu), zakładki złożone przez `zlozona()` (lokal_przeglad = Mój lokal,
    lokal_menu = Kuchnia, zaop_dostawy/zaop_magazyn/zaop_przewozy, wnetrze_sprzet/wnetrze_wyposazenie), `ALIAS` stary
    klucz → nowa zakładka (linki „Popraw”, `#adres`, budynki mapy działają po staremu). Tytuły części grup zmienione
    przez `Object.assign` w index.js (raport → „Wyniki finansowe”, agencje → „Ulotki i radio”, wlasciciel → „Portfel”,
    klienci → „Strefy”).
  - Nowe zakładki: `licytacje` (przejecia.js), `przewozy` (swiezosc.js, akcje przewozów przeniesione), `sanepid`
    (urzad.js), `zespol` (hr.js – tabela wszystkich pracowników, klik → profil), `gielda` (gielda.js, „w budowie”,
    `W_BUDOWIE` używa też mapa.js). `lokal_przeglad` z lokal.js to teraz część `stan_lokalu`.
  - W Moim lokalu część „zatrudnienie” to `obsada` (kopia `zatrudnienie` bez wyników). **UF20** ma z niej usunąć
    zatrudnianie (zostaje sama obsada), a zatrudnianie z przypisaniem dać do Rynku pracy.
  - Udogodnienia i Szkolenia to zwykłe zakładki w Ludzie; Udogodnienia mają mały wybór lokalu (`wyborLokaluKrotki`).
  - `app.js`: zablokowane pozycje (góra, podmenu, pasek podzakładek) – kłódka, szare, „od rundy N” (dla grupy
    najwcześniejsza runda części); `odRundy` liczy też zakładki złożone.
  - Kolory działów: `motywy/grafik.css` – nowe klucze grup.
  - Teksty z nazwami zakładek („X ▸ Y”) poprawione w silniku, danych, panelu i INSTRUKCJA.md; pilnuje tego
    `testy/aplikacja/test_nazwy_zakladek.py` (nazwy po lewej strzałki muszą być pozycjami MENU).
  - Sprawdzanie bez przeglądarki: zrzut widoków z gry botów (`api.prezentacja.widok`) i wyrysowanie wszystkich zakładek
    w node (kopia `static/` z `package.json {"type":"module"}`, atrapa `document`) – 358 wyrysowań bez błędów.
    Node w systemie jest stary (v14): pliki ES trzeba kopiować do katalogu z `"type":"module"`.
- [x] UF12 – zakładka Środki trwałe usunięta; `ewidencja`, `RODZAJ_ST` eksportowane z inwestycje.js, tabela i odpisy na końcu KPiR (`amortyzacja()` w finanse.js), alias `srodki_trwale → kpir`.
- [x] UF13 – zakładki Parki i zdarzenia nie ma. `zdarzenia.js`: `oknoParku(c, id)` (okno z mapy), `parkiNaMapie` (pasek
  spraw nad mapą), `parkiZeSprawa` (znak „!” w `mapa.js: budynek`), `AKCJE_ZDARZEN` (wpięte w `mapa.akcje` i część
  `sprawy`; po wyborze opcji w oknie okno rysuje się na nowo). Część `sprawy` („Sprawy w lokalu”: bank żywności, wypadki)
  w Moim lokalu, ukryta, gdy nic się nie dzieje. W danych mapy `zakladka: zdarzenia` przy parkach zostaje jako znacznik
  parku (mapy nie ruszamy). Silnik: lista błędów i czas właściciela mają `zakladka` „mapa” (park) albo „sprawy” (lokal),
  tekst „kliknij <park> na mapie miasta”; `oczekujace` mają `park`. Alias `zdarzenia → mapa`.
  Przypomnienie o evencie na liście zadań – w UF22.
- [x] UF11 – zakładka `ranking` (ogolne.js) w grupie Wyniki, od rundy 3. Dane: `v.ranking` z `api/prezentacja.py:
  historia_rankingu` (miejsca po każdej rundzie 2…, liczone jak `miejsca(karta_skumulowana)` – test w test_panel_mg.py).
  Tabela w Karcie wyników nazywa się teraz „Karty wszystkich zespołów”. Bez `Array.at` (node 14 w testach).
- Następne: UF20, potem kolejno: UF21+UF10 → UF22 → UF19 → UF18 → UF17 → UF14 → UF23 → UF9…UF1 → UF24.

## Pułapki
- Pomiary bambiczkowania czytają dane z `levas_gra`, nie stąd – tu możesz zmieniać `gra/dane/`.
- Konflikty przy scalaniu będą w: `POSTEP.md` (tu skrócony), `gra/dane/boty.yaml` i `silnik/boty.py` (B14 zmienia
  boty; tu boty dostają tylko nowe decyzje – dopisuj osobnymi blokami, nie przestawiaj kodu), `gra/INSTRUKCJA.md`.
- `zus_zlecenie` z B9 (20,48%) – UF10 przywraca zlecenie bez ZUS (decyzja autora 6.11.2026, zastępuje P1 z 29.10).
