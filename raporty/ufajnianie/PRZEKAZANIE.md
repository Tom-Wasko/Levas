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
- Następne: UF23 (redakcja wyników), potem kolejno według listy w `POSTEP.md`.

## Pułapki
- Pomiary bambiczkowania czytają dane z `levas_gra`, nie stąd – tu możesz zmieniać `gra/dane/`.
- Konflikty przy scalaniu będą w: `POSTEP.md` (tu skrócony), `gra/dane/boty.yaml` i `silnik/boty.py` (B14 zmienia
  boty; tu boty dostają tylko nowe decyzje – dopisuj osobnymi blokami, nie przestawiaj kodu), `gra/INSTRUKCJA.md`.
- `zus_zlecenie` z B9 (20,48%) – UF10 przywraca zlecenie bez ZUS (decyzja autora 6.11.2026, zastępuje P1 z 29.10).
