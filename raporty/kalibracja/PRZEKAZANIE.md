# Przekazanie pracy – kalibracja B6–B15 (stan 7.11.2026, po B15 – kalibracja zamknięta)

Ten plik pozwala nowemu agentowi przejąć kalibrację bez znajomości wcześniejszych rozmów. Przeczytaj go
w całości, potem `AGENTS.md`, `POSTEP.md` (sekcja „Krok 5” i lista B6–B15) i ostatnie sekcje
`raporty/kalibracja/dziennik.md` (B13–B15) oraz `raport.md` (raport końcowy).

## 1. Gdzie jesteśmy

- Repo: `C:\Users\PC\Pulpit\Levas\levas_gra`, **gałąź `kalibracja-b`** (do 7.11.2026 `kalibracja-b6`, nazwę zmienił autor na GitHubie) (cała praca B6–B15 tylko tutaj).
- **B6–B15 zamknięte i wypchnięte** (raport końcowy: `raporty/kalibracja/raport.md`). Dalej tylko decyzje autora (pkt 6) i merge do main.
- Równolegle sesja „ufajnianie” (worktree `Pulpit\Levas\levas_ufajnianie`, gałąź `ufajnianie`) przebudowuje
  Ludzi i menu i scali `kalibracja-b` + `ufajnianie` do main na zlecenie autora (instrukcja
  `raporty/ufajnianie/SCALANIE.md` na jej gałęzi). Każdy wynik commitować od razu; zmiany w `gra/silnik/ludzie/`,
  `panel_gracza/static/zakladki/index.js`, `hr.js`, `rynek_pracy.js` opisywać w dzienniku (konflikty).
- Pełny dziennik pomiarów i decyzji: `raporty/kalibracja/dziennik.md`. Propozycje czekające na autora:
  `raporty/kalibracja/notatki_do_zmiany.md`. Hipotezy H1–H29: `raporty/kalibracja/inwentarz.md`.
- Pomiary (katalogi z `gry.csv`, `pary.csv`, `raport.md`): `raporty/kalibracja/pomiary/`.
- Skrypty analiz z sesji (nie są częścią gry): `raporty/kalibracja/skrypty/` – opis w punkcie 5.

## 2. Zasady (od autora – obowiązują zawsze)

Gałąź i git:
- Wszystko z B6–B15 na `kalibracja-b`. **Bez merge do main bez zgody autora.** Bez `push --force`.
- Po każdym zamkniętym etapie: testy, ruff, `sprawdz` (pkt 3), wpis w dzienniku, odhaczenie w `POSTEP.md`,
  commit, `git pull --rebase`, push. Pushe na tę gałąź **nie** idą na FTP (lustro FTP tylko dla main).
- Nigdy nie commitować: `plan.txt`, `gra/db.sqlite3`, `gra/lokalne.json`, `gra/zapisy/`,
  `raporty/analiza/serwer.log`, plików `.log` z pomiarów. Nie ruszać `pytanko.txt` ani `archiwum/pytanko.txt`
  (zmiana autora – zostaje poza commitem).
- **Hasła FTP nigdy nie zapisywać ani nie commitować** (jest w `strona/ftp.json` i `gra/lokalne.json`).
- Nie kopiować niczego z folderu Revas (tylko referencja).
- Nie ruszać serwera gry autora (`manage.py graj`).

Co wymaga zgody autora (wtedy tylko propozycja w `notatki_do_zmiany.md`):
- nowe mechaniki gry; zmiany w `notatki/` (pliki autora); liczby z B5 (rozruch, pule stref);
- decyzje Z1 i U22; H19 („nic nie rób”) i H22 (wypłaty) zostają, jak są;
- **zmiany poziomu `czlowiek_dobry`** w `dane/boty.yaml` (decyzja autora po K: najpierw diagnoza i tabela,
  zmiana dopiero po zgodzie).
Bez zgody wolno: liczby i wzory, które służą celom planu; nowe umiejętności botów (z testami).

Kod (`AGENTS.md`):
- W `gra/silnik/` żadnych liczb gry (pilnuje test `test_w_kodzie_silnika_nie_ma_liczb_gry`) – liczby w `gra/dane/`.
- Identyfikatory po polsku bez znaków diakrytycznych; nowe mechaniki i umiejętności botów z testami;
  test „co do grosza” – nazwać go i podać powód w opisie commita.
- Kwoty z gier ATH/Revas są miesięczne, runda gry – tygodniowa: przy każdej cenie sprawdzić `dane.na_runde`.
- Pliki w repo z końcami linii LF (Python na Windows zapisuje CRLF – pisać z `newline="\n"`).
- Po większym bloku zmian liczb widocznych dla gracza w `gra/INSTRUKCJA.md`: `manage.py instrukcja_pdf`
  i osobny commit „Instrukcja: …”. Po B13 zmienił się tylko tekst (H22) – PDF odświeżyć w B15.

Pomiary:
- **Jeden pomiar naraz, `--procesy 2`** (3 procesy zabijały się brakiem pamięci, komputer ma 16 GB).
- W trakcie pomiaru **nie zmieniać `gra/dane/` ani kodu** (workery wczytują dane raz).
- Pomiar zabity brakiem pamięci – nie uruchamiać ponownie samemu, zgłosić autorowi. Przerwany pomiar można
  dokończyć tym samym poleceniem z tym samym `-o` (liczy tylko brakujące gry; log wcześniej przenieść).
- Bez limitu czasu (`--minut` nie podawać).
- Na Windows w Bash nie wołać gołego `python` – tylko `gra/.venv/Scripts/python`.
- Nie obchodzić blokady `rm` – pliki tymczasowe w folderze tymczasowym, przenosić `mv`.

Komunikacja: autor pisze po polsku, lubi serie pytań; gdy długo bez kontaktu – krótki status po polsku i dalej.

## 3. Polecenia

Z katalogu `gra/`:

```
.venv/Scripts/python -m pytest -q -p no:cacheprovider        # 404 testy, ok. 3,5 min
.venv/Scripts/ruff check .
.venv/Scripts/python -X utf8 -m silnik.dane sprawdz
.venv/Scripts/python -X utf8 -m balans.warianty lista          # warianty do pomiarów
```

Pomiar wariantów (w tle; `P=../raporty/kalibracja/pomiary`):

```
(nohup .venv/Scripts/python -X utf8 -m balans.warianty pelny -o $P/NAZWA --ziarna 6 \
  --strategie zrownowazony,tani,premium --firm 6 --rund 18 --poziom sredni --warianty prefiks1,prefiks2 \
  --procesy 2 > $P/NAZWA.log 2>&1 &)
# koniec: until grep -q "^| wariant\|Traceback\|MemoryError" $P/NAZWA.log; do sleep 60; done
# potem log przenieść poza repo (nie commitować .log)
```

Kontrola trudności (cele B5, 300 gier, ok. 35 min):

```
... pelny -o $P/bNN_trudnosc --ziarna 20 --strategie zrownowazony,tani,premium,agresywny,nasladowca \
  --firm 6 --rund 18 --poziom czlowiek_slaby,czlowiek_sredni,czlowiek_dobry --rywale sredni --warianty baza --procesy 2
.venv/Scripts/python -X utf8 ../raporty/kalibracja/skrypty/trud.py $P/b12_trudnosc $P/bNN_trudnosc
```

Commit (stopka obowiązkowa):

```
git commit -q -F - <<'EOF'
B14: …

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MKxrroukbs3PDn3sd7B3z1
EOF
git pull -q --rebase --autostash origin kalibracja-b && git push -q origin kalibracja-b
```

## 4. B14 i B15 zrobione

B14 opisane w dzienniku („## B14 – boty po kalibracji”): trudny kupuje drugi lokal od 50 tys. zł (było 60),
poziomy 99 / 84 / 100 par, turniej strategii (`pomiary/b14_turniej`), H24 – propozycja dla `czlowiek_dobry`
w `notatki_do_zmiany.md`, alarm słabej premium – przypadek graniczny. Kontrola trudności „jak człowiek”
(odniesienie: `b12_trudnosc`, polecenie w dzienniku B12) – powtórzyć tylko po zmianie liczb tych poziomów
albo gry.

**B15** (dziennik „## B15 – raport końcowy”): `raport.md` z tabelami przed/po, realia tym samym skryptem
(`skrypty/realia.py`), poprawki `pewnosc`/komentarzy w YAML, PDF instrukcji odświeżony. Nowe pomiary tylko po
decyzjach autora z pkt 6 – wtedy kontrola trudności (`b12_trudnosc` jako odniesienie) i realia.

## 5. Skrypty w `raporty/kalibracja/skrypty/`

Uruchamiać z `gra/` z `PYTHONPATH=.`:
- `trud.py kat [kat2]` – cele B5 z pomiaru poziomów „jak człowiek” (pierwszy plus, alarmy, pary dobra/średnia).
- `poz.py kat poziom1,poziom2,…` – pary dowolnych poziomów z pomiaru `--warianty baza`.
- `turniej.py` – turniej strategii (pkt 4.2).
- `graj.py kat od do procesy` – gry mieszane 6 firm (strategie × poziomy), składniki karty co rundę (B13).
- `ana.py kat a_zp,a_zk,a_roz,a_zad,strata …` – zgodność rankingu karty z majątkiem przy innych wagach (B13).
- `wsk.py` – `balans.warianty` z kolumną `skladowe`; `pary.py kat wagi… [-v]` – Δ karty vs Δ majątku przy
  innych wagach (B13; raport końcowy `wsk.py` pada na kolumnie `skladowe` – gry są dobre, zob. B13 w dzienniku).
- `alarm.py`, `alarm2.py strategia poziom ziarno [rund]` – przebieg jednej gry badanej (gotówka, debet).
- `ludzie.py`, `polisy.py` – zadowolenie/odejścia badanej (B9), wartość polis (B12).
- `realia.py [poziom]` – marża i udziały kosztów w grze 6 botów (B15; działa też na wypakowanym tagu).

## 6. Czeka na decyzję autora (nie wdrażać samemu)

W `notatki_do_zmiany.md`: waga nieruchomości (Z1), lokal niewyposażony, wykup na kredyt, szerokie menu bez kosztu
(menu 8 dań u premium +0,53 karty), rozruch (liczba B5), promocje bez trwałego skutku / z rabatem przegrywają,
płaca minimalna bez rotacji, szkolenie z efektem na kilka tygodni, udogodnienia bez skutku przy uczciwej płacy,
kredyt bez celu obniża kartę (U22), mandaty skarbowe nie obniżają karty (Z1), „jak człowiek – dobry” kupuje
drugi lokal jak trudny (B14), marża wyżej niż realia (B15). Merge `kalibracja-b` → main.
