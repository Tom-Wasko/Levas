# Scalanie gałęzi do `main` – instrukcja dla agenta (7.11.2026 albo później)

Cel: na `main` ma się znaleźć wszystko: kalibracja B6–B14/15 (`kalibracja-b6`) i ufajnianie (`ufajnianie`).
Autor zgodził się na to scalanie 6.11.2026 („jutro po zakończeniu pracy zajmiesz się sklejaniem wszystkiego”).
Jeśli B14/B15 nie są skończone, **zapytaj autora**, czy scalać stan bieżący.

## Gałęzie (stan 6.11.2026)
```
main ── … ── (U24, poprawki 4.11)
               └── kalibracja-b6: B6 … B13 (07b26e3) ── 9e2afb9 (przekazanie B14) ── B14… (bambiczkowanie)
                                                          └── ufajnianie: UF0 … UF24
```
`ufajnianie` wychodzi z `kalibracja-b6`, więc najprostsza droga to: najpierw `kalibracja-b6` do `main`, potem
`ufajnianie` do `main`.

## Kroki
0. Daj znać sesji kalibracji (`ListAgents` → „bambiczkowanie”, `SendMessage`), żeby zacommitowała i wypchnęła bieżący
   stan i przestała pracować. Poczekaj na potwierdzenie. Bez odpowiedzi – sprawdź `git log origin/kalibracja-b6`
   i czy nie chodzą procesy `python` z `raporty/kalibracja` (`Get-CimInstance Win32_Process`).
1. W `levas_ufajnianie`: `git fetch origin`, `git merge origin/kalibracja-b6` (do gałęzi `ufajnianie`).
   Konflikty rozwiązuj według tabeli niżej. Po scaleniu: pełne testy, ruff, `sprawdz`, krótka gra botów
   (`python -m balans.symuluj` – parametry w `gra/balans/README` albo `--help`).
2. Commit scalenia, push `ufajnianie`.
3. W `levas_gra` (główny checkout, gdy sesja kalibracji skończyła): `git checkout main`, `git pull`,
   `git merge --no-ff origin/ufajnianie` (zawiera już kalibrację). Testy jeszcze raz.
4. `git push origin main`. **Potem lustro FTP:** `python -I -X utf8 C:\Users\PC\Pulpit\Levas\strona\wyslij_na_strone.py`
   (dane logowania w `strona\ftp.json` – nigdy nie commitować).
5. PDF instrukcji: `python manage.py instrukcja_pdf` w `gra/` (jeśli instrukcja się zmieniła w scaleniu), commit, push, FTP.
6. Gra pokazowa: `python manage.py gra_pokazowa` na lokalnej bazie `levas_gra/gra/db.sqlite3` (odtwarza ją od nowa).
7. Sprzątanie: `git worktree remove ../levas_ufajnianie` (po upewnieniu się, że wszystko jest wypchnięte),
   usunięcie zdalnych gałęzi tylko za zgodą autora. Wpis w `POSTEP.md` i `raporty/kalibracja/dziennik.md`.

## Typowe konflikty i jak je rozwiązać
| Plik | Co zrobić |
|---|---|
| `POSTEP.md` | Weź wersję z `ufajnianie` (skrócona). Z `kalibracja-b6` przenieś tylko zmienione linie B14/B15 do sekcji „Krok 5 – część druga”. |
| `gra/dane/boty.yaml`, `gra/silnik/boty.py` | Kalibracja zmienia liczby i strategie, ufajnianie dokłada obsługę nowych decyzji (formy zatrudnienia, przypisanie do lokalu, marketing internetowy). Zachowaj oba – liczby z kalibracji, nowe bloki z ufajniania. Po scaleniu: test botów i krótki pomiar trudności (`raporty/kalibracja/skrypty/`). |
| `gra/dane/katalog.yaml`, `zalozenia.yaml`, `kandydaci.yaml` | Liczby z kalibracji, nowe klucze i terminy odblokowań z ufajniania. `zus_zlecenie`: zostaje 0 (decyzja autora 6.11). |
| `gra/INSTRUKCJA.md` | Złóż obie wersje ręcznie, potem PDF. |
| `raporty/kalibracja/*` | Zawsze wersja z `kalibracja-b6` (ufajnianie zmieniło tam tylko ścieżki do `archiwum/czesc_A/` – zachowaj te ścieżki). |
| Pliki przeniesione do `archiwum/` | Jeśli kalibracja zmieniła plik, który ufajnianie przeniosło, git zwykle sam to wykryje (rename). Jeśli nie – zastosuj zmianę w nowym miejscu. |

## Po scaleniu sprawdź
- `pytest`, `ruff`, `sprawdz` – zero błędów.
- Gra lokalna (`start.bat`): mapa jako ekran startowy, nowe menu, lista zadań, gra pokazowa w „Twoich grach”.
- Boty grają bez błędów 18 rund, poziomy trudności w kolejności łatwy < średni < trudny.
