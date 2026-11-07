# Postęp

Pełna historia kroków 1–6 (F2–F4, poprawki P/Q, Z1–Z6, A1–A3, U1–U24): [archiwum/POSTEP_do_2026-11-06.md](archiwum/POSTEP_do_2026-11-06.md).
1 commit = 1 zadanie (`F2.1: …`, `B3: …`, `UF7: …`).

## Zrobione (skrót)
- Krok 2 – kopia Revasa → Levas: Django, pydantic, grosze, YAML z `zrodlo`, strumienie losowości, kebab, rundy tygodniowe, panel MG.
- Krok 3a/3b/4 – konta i drużyny, mapa i lokale, popyt strefowy, świeżość, dostawcy, czas właściciela, rynek pracy,
  banki, Harpagon, księgowość JDG, biura rachunkowe, parki i zdarzenia, karta wyników kebabu (bez giełdy).
- Poprawki 27.10 (P), 28.10 (Q), przebudowa zakładek per lokal (Z1–Z6, 2–3.11), poprawki 4.11.
- Krok 5 część 1 – kalibracja B1–B5 (29.10). Krok 6 – analiza oczami gracza A1–A3 i wdrożenie U1–U24 (3–4.11),
  raport w `archiwum/czesc_A/`.

## Krok 5 – kalibracja, część druga: obszary B6–B15

- [x] B6 Lokale (typ × forma × strefa, licytacje, przejęcia) — zrobione 6.11.2026 na gałęzi `kalibracja-b6` (bez merge do main): wzór konkurencji stref (lokale gry dzielą atrakcyjność w strefie) i popyt stref K4 – centrum przestało dominować (strefa najlepsza w 6 grupach strategia × długość gry: centrum 6, dworzec 4, lsm_czuby 3, stare_miasto 2, czechów i politechnika po 1); ceny kupna lokali ×1,5 (kupno na peryferiach −0,16 karty wobec najmu w centrum, wygrywa tylko u taniego w swojej strefie); boty umieją kupno na kredyt, niewyposażony z leasingiem, działkę, przebicie, wykup i przejęcie; magazyn każdego lokalu osobno. Trudność (`b6_trudnosc`): dobra > średnia 74 → 86/100, słaba bez alarmów. Otwarte – decyzje autora w `notatki_do_zmiany.md`: lokal niewyposażony, wykup na kredyt, kupiony lokal w rozwoju firmy (Z1), rozruch (liczba B5 – pierwszy plus średniej w rundach 4–6 tylko 33–43/100).
- [x] B7 Menu i ceny (dania, marże, widełki, promocje) — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: krzywa jakości 1★ 0,55 / 2★ 0,654 / 3★ 0,82 (było 0,616 / 0,654 / 1,0 – 3★ wygrywało 12/12 par, +0,25 karty; teraz 3★ +0,05, 1★ −0,13 względem 2★), tani z kuchnią 2 miejsc (karta 0,29 → 0,44); ceny strategii blisko optimum (każde odchylenie traci). Trudność bez regresji (`b7_trudnosc`: dobra > średnia 87/100, słaba bez alarmów). Otwarte – decyzje autora: szerokie menu bez kosztu (menu 8 dań +0,74 u premium) i promocje bez trwałego skutku (żadna z rabatem nie wygrywa z brakiem promocji) – sprawdzenie w B10.
- [x] B8 Zaopatrzenie (dostawcy, gwiazdki, świeżość, magazyn, auto-zamawianie, handel) — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: boty umieją gwiazdki składników niezależnie od jakości, zapas zamówień, wybór dostawców, dyskont (odbiór osobisty, limit opakowań) i auto-dostawy; zapas zamówień botów 1,05 → 1,2 (przy 1,05 boty traciły ok. 9% sprzedaży na brakach; optimum 1,15–1,3, przy 2,0 −0,2…−0,3 karty), poziomy z prostym planowaniem zostają przy 1,05. Liczby gry bez zmian – bez dominacji: każda strategia wygrywa na składnikach swojej jakości, piekarnia i producent się opłacają, dyskont +0,03…+0,05 karty za ok. 10 h czasu właściciela tygodniowo (ok. 18 zł/h, H16 tylko w słabej formie – wraca w B9), auto-dostawy −0,004…−0,07 (+9% sprzedaży, +24% kosztu towaru). Trudność (`b8_trudnosc2`): pierwszy plus średniej w 4–6 37 → 43/100, dobra > średnia 87 → 90/100, słaba bez alarmów. Bez pomiaru: handel między drużynami (boty nie handlują) i mrożonki jako zapas.
- [x] B9 Ludzie (rekrutacja, umowy, pensje, premie, szkolenia, headhunter, czas właściciela) — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: P1 (decyzja autora 29.10.2026) – zlecenie płaci ZUS pracodawcy 20,48% jak umowa o pracę (zlecenie −0,003…−0,008 karty, bez dominacji); boty umieją pensję, gwiazdki ludzi, kanał, premię i właściciela na kasie; szkolenia i premia przeliczone na rundę tygodniową (ceny szkoleń z ATH są miesięczne – szkolenie kosztowało 4,3× za dużo, premium bez szkoleń +0,21 karty; teraz jedno szkolenie +0,006…+0,024, kolejne tracą; boty: 1 szkolenie u zrównoważonego, premium i agresywnego); właściciel na kasie i headhunter przegrywają. Trudność (`b9_trudnosc`): dobra > średnia 90 → 88/100, słaba bez alarmów, karty +0,09. Otwarte – decyzje autora w `notatki_do_zmiany.md`: płaca minimalna dominuje u premium (+0,05 karty 6/6, kandydat przyjmuje każdą ofertę, nikt nie odchodzi) i szkolenie z efektem na kilka tygodni.
- [x] B10 Marketing (reklama, agencje, promocje, udogodnienia, wyposażenie) — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: wyposażenie z nasyceniem (`popyt.wyposazenie_nasycenie` 3,0 – liniowo komplet dawał +31% popytu i +0,12…+0,13 karty, wygrywał zawsze; teraz komplet +0,06…+0,07 przy wolnej kuchni, ≈ 0 przy pełnej); radio 180 → 70 zł, degustacja 110 → 80 zł, noc kebaba 400 → 200 zł za emisję (przegrywały z każdym kanałem, teraz ≈ inne; noc kebaba w strefie akademickiej lekko na plus); boty umieją emisje i przerwę kampanii, wyposażenie: tani 3, zrównoważony 6, udogodnienia premium i agresywny 3, premium na zestawie zamiast karty (+0,16 karty), tani bez happy hours. Brak kampanii i brak eventów zawsze tracą. Trudność (`b10_trudnosc`): dobra > średnia 88 → 85/100, słaba < średnia 99/100, bez alarmów, karta średniej 0,38 → 0,45. Otwarte – decyzje autora w `notatki_do_zmiany.md`: promocje z rabatem nadal przegrywają (karta także przy 5%), udogodnienia nic nie dają przy uczciwej płacy.
- [x] B11 Finanse (banki, kredyty, lokaty, odnawialny bez limitu; Harpagon i kasyno – ryzykowne, ale czasem opłacalne)
- [x] B12 Księgowość i urzędy (samodzielnie / biuro z OC i bez, kary, sanepid, higiena, ubezpieczenia; łamanie zasad średnio się nie opłaca) — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: boty umieją samodzielną księgowość (ustawienie `ksiegowosc`: błędy i zaniżenie deklaracji) i higienę obniżaną po odbiorze lokali; biura bez dominacji (eksiegi nieznacznie najlepsze, jks gorszy o 0,4 tys. zł), samodzielnie +3 tys. zł za pracę gracza; łamanie zasad traci w majątku (bez deklaracji −6,9 tys. zł, higiena „brak” po odbiorze −2,5 tys. zł), higiena podstawowa wystarcza (H15). Polisy dominowały (+1,67 tys. zł, 82% – odszkodowania 2,9 × składki, sprzęt 24 ×): składki lokal 140 → 300 zł, sprzęt + 400 zł stałej, OC 80 → 60 zł miesięcznie – teraz lekko ujemna wartość oczekiwana i mniejszy rozrzut (`b12_polisy2`). Trudność (`b12_trudnosc`) bez zmian, 1 alarm słabej (151 zł, do B14). Otwarte – decyzja autora w `notatki_do_zmiany.md`: mandaty skarbowe nie obniżają karty (bez deklaracji +0,01 karty przy −6,9 tys. zł majątku).
- [x] B13 Karta wyników – tylko wagi składowych (brak „nabijania”, zgodność z majątkiem netto), potem szybki pomiar wszystkich obszarów — zrobione 6.11.2026 na gałęzi `kalibracja-b6`: wagi bez zmian – ranking według karty zgodny z majątkiem netto wyraźnie, ale nie idealnie (Spearman 0,935, ten sam 1. w 81% z 80 gier mieszanych), żadna wersja wykładników ani wagi straty nie poprawia tego ponad szum; karta i majątek mają ten sam znak w 83% par (`b13_wagi`, 35 wariantów ze wszystkich obszarów – to też szybki pomiar obszarów, bez nowej dominacji). Jedyne „nabicie”: księgowość bez deklaracji (+0,01 karty, −6,6 tys. zł) – propozycja B12 u autora. Progi słów karty (U10) przeliczone po kalibracji: wynik działalności 0,2 / 0,9, ekonomiczny 0,35 / 1,4, rozwój 0,54 / 0,64. H19: nic nie rób −0,016, słaba wersja nad zerem poza agresywną (−0,04…−0,06 – do B14). H22: opis w instrukcji.
- [ ] B14 Boty po kalibracji (poziomy wyraźnie różne, każda strategia wygrywa w jakimś kontekście; cele B5 nadal spełnione) — w toku; stan i dalsze kroki dla kolejnego agenta: `raporty/kalibracja/PRZEKAZANIE.md`
- [ ] B15 Raport końcowy (przed/po od tagu `kalibracja-start`), `zrodlo`/`pewnosc` w YAML, propozycje zmian w notatkach, instrukcja gracza

## Ufajnianie (polecenia autora 6.11.2026; gałąź `ufajnianie`, plan i przekazanie: `raporty/ufajnianie/`)
Kolejność pracy (od najtrudniejszych): UF15 → UF12 → UF13 → UF11 → UF20 → UF21+UF10 → UF22 → UF19 → UF18 → UF17 → UF14 →
UF23 → UF9…UF1 → UF24. Numery UF = numery z `raporty/ufajnianie/plan.md` (w nawiasie numer poprawki autora).
- [x] UF0 Sprzątanie Pulpit\Levas i repo, notatki zaktualizowane, plan i przekazanie (89db989)
- [ ] UF23 (11) Redakcja kart wyników, Wniosków i widoków „Wyniki” wszystkich zakładek
- [x] UF22 (20) Lista zadań po prawej (z sytuacji + własne drużyny, odhaczają się same, nieodhaczone przechodzą dalej)
- [x] UF21 (10) Formy zatrudnienia (pół etatu, student, staż, B2B) + przełączniki w panelu MG (tymczasowe)
- [x] UF20 (9) Zatrudnianie w Rynku pracy z przypisaniem, obsada w Moim lokalu, przenosiny
- [x] UF19 (15) Marketing internetowy od rundy 7 (Marketing → Internet; Lajk + TikTok, mapy, „Lublin Jedzie”; efekt narasta i wolno gaśnie)
- [x] UF18 (9) Licytacje pracowników widoczne (znaczek „oferty: N drużyn”, ostrzeżenie o podkupieniu, raport kto wygrał)
- [x] UF17 (19) Gra pokazowa (`manage.py gra_pokazowa`: 18 rund, 4 boty + drużyna „Pokazowa” grana przez trudnego bota, przypisana mistrzom gry)
- [x] UF15 Nowy układ menu (Miasto / Twój lokal / Firma / Wyniki, aliasy starych kluczy), Giełda „w budowie”, taśmy przy mapie, kłódki „od rundy N”
- [x] UF14 (18) Agencje reklamowe – nowy wygląd (karty agencji, kafelki kanałów z progami i kalkulatorem), siatki 3 kolumn → auto-fit
- [x] UF13 (2) Parki tylko z mapy: znak „!” na parku, lista spraw nad mapą, okno parku (kafelki A/B/C, poprzednia runda, historia); sprawy w lokalu w Moim lokalu
- [x] UF12 Środki trwałe → KPiR (ewidencja i odpisy), sprzedaż sprzętu w Wnętrzu z uwagą o amortyzacji; zakładka usunięta
- [x] UF11 Ranking w Wynikach: tabela drużyn (miejsce, zmiana, średnia i ostatnia karta, majątek) + wykres miejsc
- [x] UF10 (4) Zlecenie bez ZUS pracodawcy, student <26 – forma „zlecenie ze studentem” (razem z UF21)
- [ ] UF9 (16) Nowe udogodnienia (do rundy 14, kot zakładowy)
- [ ] UF8 (13) Falafel – bójka
- [ ] UF7 (8) 4 słupki sezonowości w kafelku dania
- [ ] UF6 (3) Terminy odblokowań
- [ ] UF5 (7) Wnioski: rozruch w pierwszych tygodniach
- [ ] UF4 (6) „Brak składnika” → Dostawy
- [ ] UF3 (5) Jedno ⓘ pod ceną
- [ ] UF2 (12) Kod `koziol` do kasyna
- [ ] UF1 (14) Mapa jako ekran startowy
- [ ] UF24 Instrukcja + PDF, kontrola botów, gra pokazowa na nowo
