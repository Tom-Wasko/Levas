# Praca bez nadzoru: 25.10.2026 21:15 → 26.10.2026 15:50

Dziennik i zasady samodzielnej pracy Claude nad planem implementacji (kolejne zadania z [`POSTEP.md`](POSTEP.md)).

## Zasady

- Kolejność: F2.3 → F2.4 … F2.8 → F3a.1 … → F3b … → F4 (według `notatki/Plan implementacji.md`).
- Po każdym zadaniu: pytest, ruff, wpis w `POSTEP.md`, commit `F…: …` i push.
- Nowe elementy gry zawsze z zakładkami **Decyzje** i **Wyniki**; prototyp mapy w F3a.3.
- Notatek (`notatki/`) nie zmieniam bez zgody – propozycje zmian trafiają do pytań.
- Pytania: tylko niedziela do 21:30 i poniedziałek 6:00–16:00. Powiadomienie push (aplikacja Claude,
  Remote Control) + okno pytania na ekranie. Zadanie, które czeka na odpowiedź, odkładam i robię kolejne,
  niezależne od niej.
- Przypomnienie (cron w sesji) co ok. 15 min wznawia pracę, także po odnowieniu limitu.
- 26.10 o 15:50 kończę: commit, push, podsumowanie, usunięcie przypomnienia.

## Otwarte pytania (czekają na odpowiedź)

1. **Gdzie jest kod starego Levasa?** Plan zakłada przeniesienie modułów i danych z `Pulpit/Levas/levas_gra`
   (strefy, lokale, sklepy, banki, podatki 2026, parki, kalendarz, PCG64), ale tego folderu nie ma na dysku,
   a repo `Tom-Wasko/Levas-stary` ma tylko notatki. Do czasu odpowiedzi: F2.5 (PCG64) piszę od zera,
   a dane do F3a biorę z notatek. (zadane: 25.10 21:50, do wysłania w poniedziałek o 6:00)

2. **Start gry i runda 1 (F2.7).** Przyjąłem: runda 1 = tydzień 5–11.10.2026 (początek roku akademickiego) i jest
   tygodniem przygotowań bez sprzedaży (jak w Revasie). Czy data i tydzień przygotowań są dobre? Zmiana to tylko
   `rundy.kalendarz.start` w `dane/katalog.yaml`. (zadane: 25.10 22:20, do wysłania w poniedziałek o 6:00)

## Odłożone zadania

_brak_

## Dziennik

- 25.10 21:15 – start; plan zaktualizowany (prototyp mapy w F3a.3); zaczynam F2.3 (pydantic + grosze).
- 25.10 21:20 – F2.3 gotowe (`95bd126`): pydantic, grosze, testy hypothesis; wyniki botów bez zmian. Start F2.4.
- 25.10 21:27 – test powiadomień: Remote Control połączony, ale push **nie wysłany** – „mobile push is disabled in /config” (do włączenia przez użytkownika w `/config`). Wracam do F2.4.
- 25.10 21:41 – test powiadomień po włączeniu „Push when Claude decides” w `/config`: **wysłane** (powiadomienie w terminalu + push na telefon). Wracam do F2.4.
- 25.10 21:35 – F2.4 gotowe (`57299d7`): dane w YAML ze schematami, `python -m silnik.dane sprawdz`, liczby gry z kodu do danych. Użytkownik poszedł spać (okno zminimalizowane). Start F2.5.
- 25.10 21:45 – F2.5 gotowe (`272d39a`): strumienie PCG64 (od zera, pytanie 1 nadal otwarte). Start F2.6 (kebab).
- 25.10 22:05 – F2.6 gotowe (`80cf033`): kebab w danych, zakładkach i szablonach. Decyzje (do przejrzenia):
  - dane Revasa przeniesione do `gra/dane_revas/` – testy mechaniki liczą na liczbach z prawdziwych gier, więc działają na nich; gra używa `dane/` (kebab),
  - identyfikatory silnika i klucze danych zostają z Revasa do kroku 3a (słownik w `gra/README.md`), żeby nie mieszać przebranżowienia z przebudową,
  - **odstępstwo od planu:** sprzęt (rożen, frytownica, lodówka) nadal kupuje się na stanowisko kuchenne, nie do lokalu – przeniesienie do lokalu razem z gotowym lokalem (F2.7) albo z F3a,
  - liczby dań (popyt, czas kuchni 3–5 min/porcję, kasa 0,3–1,2 min, sezonowość studencka, pensje 4810–5800 zł), ceny sprzętu i hurtowe ceny składników – moje założenia z `zrodlo` „założenie F2.6”, do kalibracji w kroku 5; receptury i ceny dań – z notatki „Menu i składniki” (środek przedziału),
  - 3 fikcyjni dostawcy: Piekarnia Koziołek (pieczywo), Mięsny Bazar Zamojski (mięso, warzywa, sosy) – taniej, węższa oferta; Hurtownia Lubelska Spiżarnia – wszystko,
  - nazwy mediów, szkoleń i firm szkoleniowych przerobione na gastronomię (fikcyjne), liczby z Revasa bez zmian; `zalozenia.yaml` bez zmian,
  - gra botów (12 mies.): dochód netto 0,45–0,78 mln zł na firmę (Revas: 0,8–2,4 mln) – rząd wielkości ten sam, balans przy rundach tygodniowych.
- 25.10 22:20 – F2.7 gotowe: rundy tygodniowe. Decyzje (do przejrzenia):
  - kalendarz w danych (`katalog.yaml` → `rundy.kalendarz`), silnik działa na tygodniach i na miesiącach; Revas (`dane_revas/`) nadal miesięczny – jego testy i wyniki bez zmian,
  - kwoty w danych zostają **miesięczne** (pensje w umowach, czynsz, utrzymanie) – silnik księguje je na tydzień (× 12/52); oprocentowanie roczne / 52; okresy lokat i kredytów w tygodniach (kredyt do 26 tyg.); koszty jednorazowe (zakupy, rekrutacja, premie, księgowość za dokument, emisje reklam) bez skalowania,
  - **założenie:** start 5.10.2026 (poniedziałek, początek roku akademickiego) – do pytania w poniedziałek; runda 1 nadal tydzień przygotowań bez sprzedaży (jak w Revasie),
  - sezonowość: tydzień należy do miesiąca swojego czwartku; popyt tygodniowy = roczny / 52 × sezonowość miesiąca,
  - ceny dostawców: z danych w październiku, potem losowane co tydzień (ta sama zmienność co w Revasie co miesiąc),
  - gotowy lokal na start: kuchnia (rożen, frytownica, lodówka) i kasa (kasa fiskalna, lada, tablica menu), za darmo; sprzęt nadal należy do stanowisk, nie do lokalu (do F3a); darmowy sprzęt można sprzedać,
  - etat i sprzęt 40 h / tydzień, kapitał 100 000 zł, wynik ekonomiczny = dochód / 4615 (20 000 × 12/52),
  - gra botów (26 tyg.): dochód netto od −74 tys. (agresywny marketing – reklamy jednorazowe nie są skalowane, więc tygodniowo są drogie) do +267 tys. (premium); kalibracja w kroku 5,
  - strona gracza: nazwy tygodni („Tydzień 3 (19–25.10)”, skróty T1…T26) w nawigatorze i na wykresach, koszty utrzymania „/ tydz.”, liczba rund i kapitał na stronie startowej z danych.
