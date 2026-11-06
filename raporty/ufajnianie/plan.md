# Ufajnianie – plan (ustalenia z autorem 6.11.2026)

Gałąź `ufajnianie` od `kalibracja-b6@9e2afb9` (decyzja autora 6.11 wieczorem: najpierw praca, scalanie do main
jutro – `SCALANIE.md`). Worktree `Pulpit\Levas\levas_ufajnianie`; w `levas_gra` druga sesja liczy B14 – nie
zmieniać tam kodu, danych ani gałęzi. Stan pracy: `PRZEKAZANIE.md` i `POSTEP.md` (UF0–UF24).

## Nowy układ menu (wygląd menu bez zmian – tylko kolejność i grupy)
```
MAPA (start; nie ruszać mapy – kolega dostarczy nową mapę i giełdę; obok mapy informacja „w budowie” z żółtymi taśmami)
── Miasto
  NOWE LOKALE   Do wynajęcia · Licytacje · Przejęcia
  KLIENCI       Strefy · Konkurencja · Kalendarz
── Twój lokal  [wybór lokalu tylko tutaj]
  MÓJ LOKAL     stan, sprzedaż, obsada (tylko wybór, kto na którym stanowisku)
  KUCHNIA       Menu i ceny (cena dalej w kafelku dania)
  ZAOPATRZENIE  Dostawy · Magazyn i świeżość · Przewozy
  WNĘTRZE       Stanowiska i sprzęt (+ sprzedaż sprzętu) · Wyposażenie
── Firma
  LUDZIE        Rynek pracy (zatrudnianie z przypisaniem) · Zespół (pensje, umowy, przenosiny) · Szkolenia · Udogodnienia
  MARKETING     Promocje · Ulotki i radio · Internet
  HANDEL        Handel z drużynami
  PIENIĄDZE     Wyniki finansowe · Bank · Harpagon
  KSIĘGOWOŚĆ    Biuro · KPiR (+ amortyzacja z dawnych Środków trwałych) · VAT · Podatki
  URZĘDY        Urząd · Sanepid · Ubezpieczenia
  WŁAŚCICIEL    Czas właściciela · Portfel · Giełda (pusta, „w budowie”)
── WYNIKI        Karta · Wnioski · Ranking (nowa: tabela + historia pozycji)
── LISTA BŁĘDÓW (osobno)
[WYŚLIJ]                                   | Zadania ▸ (panel po prawej)
```
Środki trwałe – usunięte z menu. Parki i zdarzenia – usunięte z menu, wejście tylko przez mapę (park pokazuje swoje
eventy). Kasyno – ukryte, wejście kodem z klawiatury `koziol` (każdy, kto zna; zaproszenia zostają).
Zakładki przed swoją rundą: szare z kłódką i „od rundy N”.

## Ustalenia do poprawek
- (3) terminy: promocje 3; reklama – pierwsze kanały 5, reszta 8, agencja eventowa 10; internet 7; sanepid 4 (reszta
  urzędu od 1); ubezpieczenia 4; handel 6.
- (4) umowa zlecenie bez ZUS; studenci <26 – bez PIT (ulga dla młodych) na obu umowach, ale mniej godzin / częściej
  odchodzą.
- (5) dwa kółka ⓘ pod ceną (dwie długie podpowiedzi zwinięte w gołe kółka) → jedna czytelna linia.
- (6) „brak składnika” → odsyła do Zaopatrzenia (Dostawy), nie do Menu.
- (8) w kafelku dania zamiast „Sezonowość (wrzesień) × 1” – 4 słupki (bieżący miesiąc + 3 kolejne).
- (9) zatrudnianie tylko w Rynku pracy, przypisanie do lokalu i stanowiska obowiązkowe przy zatrudnieniu; w lokalu
  tylko obsada; przenosiny: zgoda zależy od zadowolenia i odległości, jednorazowy dodatek. Licytacje widoczne:
  znaczek „oferty: N drużyn” przy kandydacie (na żywo), ostrzeżenie o próbie podkupienia, raport po rundzie.
- (10) formy: umowa o pracę pełny/pół etatu, zlecenie (bez ZUS), student <26, staż z urzędu pracy, B2B; w panelu MG
  przełączniki dostępnych form (z komentarzem w panelu: usunąć przed oficjalną wersją).
- (11) zredagować Kartę wyników + Wnioski i widoki „Wyniki” wszystkich zakładek – ciekawe do czytania.
- (13) falafel: mała szansa na bójkę następnego dnia, komiczny raport, mały skutek (czas właściciela / plastry).
- (15) nowa zakładka Marketing internetowy od 7: Lajk i Spółka przeniesiona + nowe kanały, efekt narasta i wolniej gaśnie.
- (16) ok. 10 nowych udogodnień, co 2–3 rundy do rundy 14, kilka żartobliwych (w tym kot zakładowy).
- (17) sprzątanie: logi do archiwum/.gitignore, stare raporty i zadania do archiwum/, martwy kod, skrócić POSTEP.md.
- (18) nowy wygląd Agencji reklamowych + poprawić siatki „3 kolumny, a 2 rzeczy w wierszu”.
- (19) gra pokazowa w „Twoich grach”: pełne 18 rund, drużyna autora grana przez dobrego bota; polecenie
  `manage.py gra_pokazowa`, odtwarzana po każdej większej zmianie.
- (20) lista zadań po prawej: generowana z sytuacji + własne zadania drużyny, aktualizowana na żywo z decyzjami
  (nie tylko po rundzie), odhacza się sama + ręcznie, obok Listy błędów, wysuwana i zwijana do paska z licznikiem;
  punkt o eventach w parkach.
- Pytanie 2 (podkupienie i długi) – autor: pominąć, zamiast tego wyeksponować licytacje (9).

## Lista zadań (numer UF = pozycja; od najszybszej – pracujemy od dołu, od najtrudniejszych)
1. (14) mapa jako ekran startowy
2. (12) kod `koziol` do kasyna
3. (5) jedno ⓘ pod ceną
4. (6) „brak składnika” → Dostawy
5. (7) wnioski: rozruch w pierwszych tygodniach
6. (3) terminy odblokowań (+ boty, testy)
7. (8) 4 słupki sezonowości
8. (13) falafel
9. (16) nowe udogodnienia
10. (4) zlecenie bez ZUS, student bez PIT
11. Ranking w Wynikach
12. Środki trwałe → KPiR i Wnętrze
13. (2) parki tylko z mapy
14. (18) agencje reklamowe i siatki
15. (1, nowy układ) menu, Giełda „w budowie”, taśmy przy mapie
16. (17) sprzątanie
17. (19) gra pokazowa
18. (9) licytacje widoczne
19. (15) marketing internetowy
20. (9) Rynek pracy z przypisaniem, obsada, przenosiny
21. (10) formy zatrudnienia + panel MG
22. (20) lista zadań
23. (11) redakcja kart wyników i widoków Wyniki
24. instrukcja + PDF, kontrola botów (bez błędów, trudność), gra pokazowa na nowo

## Plan implementacji (kolejność pracy: od najtrudniejszych i najdłuższych)
Każde zadanie: testy + ruff + `sprawdz`, wpis w `POSTEP.md` i `PRZEKAZANIE.md`, commit `UFn: …`, push `ufajnianie`.
Liczby gry tylko w YAML. Teksty po polsku, ciekawie i krótko (styl gry: lekki humor, Lublin, Koziołek).

1. **UF23 (11) Redakcja wyników.** `silnik/wyniki/wnioski.py`, zakładki z widokiem „Wyniki” (`zakladki/*.js`,
   `ogolne.js` – karta i wnioski). Karta wyników: nagłówek-historia tygodnia („Tydzień w liczbach”: najlepszy dzień,
   najchętniej brane danie, co zjadło zysk), porównanie z poprzednią rundą (strzałki), 3 najważniejsze sprawy.
   Wnioski: zdania z liczbami i konkretną radą, odsyłacz do zakładki. Widoki „Wyniki” pozostałych zakładek: na górze
   1–2 zdania podsumowania (co się stało, czy dobrze), zamiast suchych tabel – kafelki z najważniejszymi liczbami,
   tabele szczegółów zwijane. Najpierw przejrzeć wszystkie widoki (agent Sonnet może zrobić spis), potem wspólne
   pomocniki w `wspolne.js` (np. `podsumowanie()`, `kafelkiLiczb()`), potem zakładka po zakładce.
2. **UF22 (20) Lista zadań.** Nowy moduł `zakladki/zadania.js` + przycisk obok Listy błędów; panel po prawej,
   wysuwany, zwijany do paska z licznikiem. Zadania automatyczne liczone w przeglądarce z `S.stan` + bieżących
   decyzji (przeliczane po każdej zmianie decyzji – ten sam hak co lista błędów), np.: wybierz lokal, ustaw menu
   i ceny, zamów składniki na dni sprzedaży, obsadź stanowiska, odpowiedz w parku (event z mapy), złóż deklaracje,
   spłać Harpagona; odhaczają się same, gdy warunek spełniony. Własne zadania drużyny: zapis w decyzjach rundy
   (pole `zadania_wlasne` w decyzjach JSON – bez migracji, przenoszone na następną rundę dopóki nieodhaczone) –
   sprawdzić, czy schemat decyzji (`silnik/decyzje.py`) przepuszcza dodatkowe pole; jeśli nie – dodać.
3. **UF21 (10) Formy zatrudnienia.** `dane/kandydaci.yaml`/`katalog.yaml`: formy `praca_pelny`, `praca_pol`,
   `zlecenie`, `student`, `staz`, `b2b` z parametrami (godziny, ZUS, PIT, odejścia, koszt, dopłata urzędu przy
   stażu, B2B – faktura z VAT, brak ZUS, wyższa stawka). Silnik: `silnik/ludzie/*`, koszty płac (`ksiegowosc`),
   `hr.js` (UMOWY), okno zatrudnienia. Opcja gry `formy_zatrudnienia` (lista) ustawiana w panelu MG (przełączniki
   + komentarz „TYMCZASOWE – usunąć przed oficjalną wersją”), domyślnie wszystkie. Boty: tylko praca/zlecenie.
4. **UF20 (9) Rynek pracy z przypisaniem.** Okno zatrudnienia w Rynku pracy wymaga lokalu i stanowiska. „Mój lokal”
   pokazuje tylko obsadę (wybór, kto na którym stanowisku, z ludzi przypisanych do lokalu). Przenosiny: decyzja
   `przenosiny: [{pracownik, do_lokalu, dodatek_gr}]`; zgoda = f(zadowolenie, odległość stref, dodatek) – parametry
   w YAML, losowanie przez `strumien`; wynik w raporcie rundy.
5. **UF19 (15) Marketing internetowy od 7.** Nowa podzakładka Marketing → Internet; agencja Lajk i Spółka
   przeniesiona z reklamy (kanały posty, influencerka) + nowe kanały (np. TikTok, Google Maps, grupa „Lublin
   Jedzie”); efekt narasta przez kilka rund i wolniej gaśnie (pamięć efektu w `Firma`). Dane w `mapa/reklama.yaml`
   (nowa sekcja) i silnik `silnik/rynek/reklama.py`. Boty: dobry bot czasem używa.
6. **UF18 (9) Licytacje widoczne.** Znaczek „oferty: N drużyn” przy kandydacie (z bieżących decyzji innych drużyn
   – API stanu musi zwracać liczbę ofert na kandydata bez ujawniania kwot), ostrzeżenie o próbie podkupienia
   (w Zespole i liście błędów), raport po rundzie (kto wygrał, za ile – jak przy lokalach).
7. **UF17 (19) Gra pokazowa.** `gry/management/commands/gra_pokazowa.py`: usuwa starą grę „Pokazowa”, zakłada nową
   (18 rund, 4 boty + drużyna „Pokazowa” grana przez dobrego bota), przypisuje konto mistrza gry, rozgrywa wszystkie
   rundy przez te same funkcje co zamykanie rundy. Widoczna w „Twoich grach”.
8. **UF15 Nowy układ menu.** `zakladki/index.js` (MENU, OD_RUNDY, ALIAS – stare klucze zostają jako aliasy), nowe
   grupy według rysunku wyżej; zakładki złożone (`zlozona()` w `lokal.js`); Giełda – pusta zakładka „w budowie”;
   obok mapy pasek z żółtymi taśmami (CSS) i tekstem „Nowa mapa i giełda – w budowie”. Zakładki przed swoją rundą
   szare z kłódką i „od rundy N” (zamiast ukrywania). Wybór lokalu tylko w „Twój lokal”.
9. **UF14 (18) Agencje i siatki.** Nowy wygląd Agencji reklamowych (karty agencji z logo-kolorem, kanały jako
   kafelki z ceną, zasięgiem i progami zniżek, kalkulator emisji). Przegląd CSS siatek `grid-template-columns:
   repeat(3…)` z 2 elementami → `auto-fit, minmax(…)`.
10. **UF13 (2) Parki tylko z mapy.** Usunąć Zdarzenia z menu; klik w park na mapie otwiera okno parku z jego
   historią (tylko eventy tego parku), lepiej rozdzielone kafelki opcji. Lista zadań przypomina o evencie.
11. **UF12 Środki trwałe** – usunąć zakładkę; tabela amortyzacji do KPiR, sprzedaż sprzętu do Wnętrza.
12. **UF11 Ranking** – podzakładka Wyniki → Ranking: tabela drużyn (karta, majątek) + wykres pozycji w rundach.
13. **UF10 (4)** – `zus_zlecenie` 0 (zostaje parametr), student <26 bez PIT – razem z UF21.
14. **UF9 (16)** – ~10 nowych udogodnień w `katalog.yaml` (rundy 5–14), kilka żartobliwych, m.in. kot zakładowy.
15. **UF8 (13)** – falafel: `dane/zdarzenia/` nowy wpis, szansa na bójkę następnego dnia, komiczny raport, skutek:
   −kilka godzin właściciela albo koszt plastrów; strumień losowości „falafel”.
16. **UF7 (8)** – w kafelku dania (`oferta.js`) 4 słupki sezonowości: bieżący miesiąc + 3 kolejne.
17. **UF6 (3)** – terminy odblokowań: `katalog.yaml` harmonogram zakładek, `od_rundy` w promocje/reklama/handel/
   urząd (sanepid 4), ubezpieczenia 4; testy harmonogramu i boty (nie używają przed terminem).
18. **UF5 (7)** – wnioski z rund 1–3: zdanie o rozruchu (każda firma potrzebuje kilku tygodni).
19. **UF4 (6)** – „brak składnika” (`silnik/decyzje.py:528`) – odsyłacz do Zaopatrzenia/Dostaw.
20. **UF3 (5)** – jedno ⓘ pod ceną (`oferta.js: cenaDania`, `dymki.js: zwinPodpowiedzi`).
21. **UF2 (12)** – kod `koziol` z klawiatury otwiera kasyno (`app.js`, nasłuch klawiszy poza polami tekstowymi).
22. **UF1 (14)** – mapa jako ekran startowy (`app.js`: domyślna zakładka, logo).
23. **UF24** – instrukcja gracza + PDF, kontrola botów (18 rund bez błędów, kolejność trudności), gra pokazowa.
