# Ufajnianie – przekazanie pracy (czytaj najpierw, jeśli zaczynasz bez wiedzy o tej pracy)

Aktualizowane po każdym zadaniu. Ostatnia aktualizacja: patrz `git log -1 -- raporty/ufajnianie/PRZEKAZANIE.md`.

## Gdzie i jak pracujesz
- Worktree: `C:\Users\PC\Pulpit\Levas\levas_ufajnianie`, gałąź **`ufajnianie`** (od `kalibracja-b@9e2afb9`, czyli
  main + B6–B13 + przekazanie B14). Push: `git push origin ufajnianie`. **Nie pushuj na main** – scalanie robi się
  osobno według `SCALANIE.md` (autor zlecił je na 7.11.2026, po zakończeniu pracy nocnej).
- `C:\Users\PC\Pulpit\Levas\levas_gra` to główny checkout na gałęzi `kalibracja-b`. Pracuje tam druga sesja
  Claude Code („bambiczkowanie”), która liczy pomiary B14 i commituje na `kalibracja-b`. **Nie zmieniaj tam niczego**
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
- `SCALANIE.md` – jak jutro skleić `kalibracja-b` i `ufajnianie` do `main`.

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
  - W Moim lokalu część „zatrudnienie” to `obsada` (kopia `zatrudnienie` bez wyników) – po UF20 sama obsada.
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
- [x] UF20 – silnik: decyzja `przenosiny: [{pracownik, typ, nr, dodatek}]` (`silnik/ludzie/przenosiny.py`). W tym samym
  lokalu – od razu; do innego lokalu – zgoda losowana w `rynek_pracy.przed_decyzjami` (strumień „przenosiny”; w podglądzie
  `podglad=True` – bez losowania, lista błędów pokazuje szansę). Wzór i parametry: `zalozenia.yaml: pracownicy.przenosiny`
  (zadowolenie − próg odejść, odległość lokali na mapie, dodatek ÷ pensja). Kolejność w `decyzje.zastosuj`: zwolnienia →
  zmiany → przenosiny → zatrudnienia. Raport: `wyniki.rynek_pracy.przenosiny` (odpowiedzi) i `.przeniesieni` (wykonane).
  Panel (hr.js): w grze z lokalami pusty kafelek obsady ma „Przypisz osobę” (`oknoPrzypisania`, `oknoPrzenosin` z szansą
  przy dodatkach 0/¼/½/1 pensji – `szansaPrzejscia` to kopia wzoru, odległości w `v.agencja.przenosiny`) i „Stań sam”;
  zatrudnianie – `kandydaciRynku` w Rynku pracy (okno zatrudnienia bez stanowiska ma `<select id="z-miejsce">` typ:nr).
  Gra bez lokali (stare zapisy) – po staremu. Test: `testy/ludzie/test_przenosiny.py`.
- [x] UF21+UF10 – formy zatrudnienia. Dane: `zalozenia.yaml: pracownicy.formy_zatrudnienia` (prace, pol_etatu,
  zlecenie, student, staz, b2b – etat, rodzaj ZUS, wypowiedzenie, kadry biura, kara zlecenia, mnożnik oczekiwanej pensji,
  płaca minimalna) i `pracownicy.studenci` (wiek, udział, godziny, odejścia, pensja). `podatki_2026.yaml:
  zus_pracodawcy_zlecenie: 0` (UF10) i reguła VAT „Faktura B2B”. Logika: `silnik/ludzie/formy.py` (bez danych –
  dawne dwie formy, więc testy na zamrożonej kopii działają po staremu). `Pracownik.student`; studenci losowani
  osobnym strumieniem „studenci” (reszta puli bez zmian). Godziny: `Firma.godziny_stanowiska(…, dane)` × `fz.etat`.
  B2B: zamiast pensji i ZUS księgowana „Faktura B2B: <imię>” brutto z VAT. Staż: pensja 0, `fz.koniec_stazu` na
  początku kadr w `decyzje.zastosuj`. Zmiana formy w `zmiany` walidowana (`fz.blad`), błędy na liście (`hr_zatrudnienie`).
  Licytacja kandydata porównuje oferty `fz.porownawcza` (w przeliczeniu na etat). Opcja MG (TYMCZASOWE – do usunięcia
  przed oficjalną wersją): `konfiguracja.formy_zatrudnienia`, POST `prowadzenie {formy_zatrudnienia: [...]}`, wiersz
  „Formy zatrudnienia (test)” w panelu MG; wyłączone formy w decyzjach → umowa o pracę (`fz.przytnij` w runda.py).
  Panel: `zakladki/formy.js` (nazwy, ZUS, koszt, minimum, formy dla osoby, opis), okno zatrudnienia i profil (hr.js,
  `zmiany["forma-zatrudnienia"]` przelicza pensję i opis), Rynek pracy, Lokal (koszt), Podatki (tekst).
  Testy: `testy/ludzie/test_formy.py`, test MG w `test_panel_mg.py`, przepisany test ZUS zlecenia w test_zadowolenie.py.
- [x] UF22 – lista zadań. Panel: `zakladki/zadania.js` (`zadaniaAutomatyczne` – grupy czerwonych pozycji listy błędów
  według klucza zakładki `GRUPY`, reszta jako „Popraw: <zakładka>”; sprawy w parkach – jedno zadanie na park, sprawy
  w lokalu, Harpagon przy terminie ≤ 1 runda, „Wyślij decyzje”; zadanie z listy błędów, które się pojawiło, zostaje
  w rundzie jako odhaczone – pamięć w `localStorage` na rundę). `app.js`: `rysujZadania(ctx())` na początku `rysuj()`
  (ten sam hak co lista błędów), przycisk „Zadania” w menu za Listą błędów, `AKCJE_ZADAN`, Enter w polu → Dodaj.
  Własne zadania: decyzje `zadania_wlasne: [{id, tekst, zrobione}]` (silnik ich nie czyta); walidacja w
  `api/widoki.py: _zadania_wlasne` (≤ 30 zadań, ≤ 120 znaków); przeniesienie nieodhaczonych –
  `api/prezentacja.py: zadania_z_poprzedniej` (w widoku, zapis przy pierwszej zmianie decyzji). Style na końcu
  `styl.css`. Test: `test_api.py: test_wlasne_zadania_druzyny_przechodza_na_kolejna_runde`; panel sprawdzony w node
  na zrzucie widoków (bez przeglądarki – wygląd panelu do obejrzenia przy scalaniu).
- [x] UF19 – marketing internetowy od rundy 7. Dane: `mapa/reklama.yaml` – nowa sekcja `internet` (model:
  `narastanie` [0,35, 0,7, 1,0], `trwalosc` 0,8, `prog_wygasania`; agencja `lajk` przeniesiona z `agencje` – te same id
  kanałów grupa_osiedlowa i influencer, teraz od rundy 7 i z mniejszym przyciąganiem – plus nowe: tiktok, mapy,
  lublin_jedzie). Schemat `ModelInternetu`/`ReklamaInternetowa`, `PlikReklamy.internet` opcjonalne (dane zamrożone
  testów bez tej sekcji działają po staremu – Lajk tam jest agencją tradycyjną). Silnik `rynek/reklama.py`:
  `agencje(dane)` (obie sekcje), `internetowa`, `waga_internetu` (waga kampanii z jej wieku – „pamięć efektu” liczona
  z historii `Firma.kampanie`, bez nowego pola w `Firma`, więc zapisy gier się nie psują), `prognoza_internetu`
  (widok: przyciąganie na 4 rundy), uwagi zamówień internetowych w `uwagi_internet` → lista błędów, zakładka
  `internet`. Harmonogram: element `internet` (MG może przesunąć tydzień). Panel: `marketing.js` – zakładka
  `internet` (agencje tradycyjne filtrowane `tylko(R, false)`), menu Marketing → Promocje · Ulotki i radio · Internet;
  budynek `agencja_lajk` prowadzi do zakładki `internet`. Boty: strategie z Lajkiem używają go od 7, premium dokłada
  `lajk/mapy`. Testy: `testy/rynek/test_internet.py` (dane_gry). **Do kalibracji:** liczby kanałów to założenie UF19
  (suma wag ≈ 5,6 rundy efektu, reklama tradycyjna ≈ 1,9 – przyciąganie ok. 2,5× mniejsze); przy scalaniu z
  kalibracja-b sprawdzić, czy B10/B-pomiary nie zakładały Lajka od rundy 3.
- [x] UF18 – licytacje pracowników widoczne. Silnik `ludzie/rynek_pracy.py`: `zainteresowanie(decyzje_gry, nazwa)`
  (liczba innych drużyn z ofertą dla kandydata / pracownika innej drużyny, z zapisanych decyzji, bez kwot),
  `ostrzezenia(oferty_dla, kontroferty, firmy)` (lista błędów: pomarańczowe bez kontroferty, niebieskie gdy kontroferta
  przebija), raport licytacji z `wygral`/`druzyn`, oferty złożone z `wygral`/`najwyzsza`. API `_agencja`:
  `zainteresowanie`; podgląd decyzji dokłada ostrzeżenia. Panel: `hr.js` `pigulkaOfert` (Rynek pracy – kandydaci
  i headhunter), Zespół – pigułka „chce go podkupić” (link do Rynku pracy), `rynek_pracy.js` wyniki – kolumny Wygrała,
  Za ile. Boty decydują dopiero w przeliczeniu, więc ich ofert znaczek nie widzi. Testy w `testy/ludzie/test_rynek_pracy.py`.
- Następne kolejno: UF17 → UF14 → UF23 → UF9…UF1 → UF24.
- Bambiczkowanie (6.11, w nocy): B15 skończone i wypchnięte na `kalibracja-b` (9f54765, c028931); ta sesja już tam
  nie commituje – gałąź gotowa do scalenia wg SCALANIE.md, gdy autor zleci.

## Pułapki
- Pomiary bambiczkowania czytają dane z `levas_gra`, nie stąd – tu możesz zmieniać `gra/dane/`.
- Konflikty przy scalaniu będą w: `POSTEP.md` (tu skrócony), `gra/dane/boty.yaml` i `silnik/boty.py` (B14 zmienia
  boty; tu boty dostają tylko nowe decyzje – dopisuj osobnymi blokami, nie przestawiaj kodu), `gra/INSTRUKCJA.md`.
- `zus_zlecenie` z B9 (20,48%) – UF10 przywraca zlecenie bez ZUS (decyzja autora 6.11.2026, zastępuje P1 z 29.10).
  Zrobione w UF21; przy scalaniu z kalibracja-b sprawdź, czy B14/B15 nie zmieniły `zus_pracodawcy_zlecenie` z powrotem.
- UF21: boty pomijają kandydatów-studentów i zatrudniają po staremu (umowa o pracę / zlecenie). Zlecenie bez ZUS
  może stać się dla graczy wyraźnie tańsze od etatu – do sprawdzenia w następnej kalibracji (kara zadowolenia
  `udzial_umow_zlecenie`). Testy z `_kandydat()` biorą domyślnie nie-studentów.
