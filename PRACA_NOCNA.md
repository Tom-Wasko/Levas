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

## Odłożone zadania

_brak_

## Dziennik

- 25.10 21:15 – start; plan zaktualizowany (prototyp mapy w F3a.3); zaczynam F2.3 (pydantic + grosze).
- 25.10 21:20 – F2.3 gotowe (`95bd126`): pydantic, grosze, testy hypothesis; wyniki botów bez zmian. Start F2.4.
- 25.10 21:27 – test powiadomień: Remote Control połączony, ale push **nie wysłany** – „mobile push is disabled in /config” (do włączenia przez użytkownika w `/config`). Wracam do F2.4.
- 25.10 21:41 – test powiadomień po włączeniu „Push when Claude decides” w `/config`: **wysłane** (powiadomienie w terminalu + push na telefon). Wracam do F2.4.
