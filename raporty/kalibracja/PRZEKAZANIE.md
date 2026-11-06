# Przekazanie pracy – kalibracja B6–B15 (stan 6.11.2026, wieczór)

Ten plik pozwala nowemu agentowi przejąć kalibrację bez znajomości wcześniejszych rozmów. Przeczytaj go
w całości, potem `AGENTS.md`, `POSTEP.md` (sekcja „Krok 5” i lista B6–B15) i ostatnie sekcje
`raporty/kalibracja/dziennik.md` (B12, B13).

## 1. Gdzie jesteśmy

- Repo: `C:\Users\PC\Pulpit\Levas\levas_gra`, **gałąź `kalibracja-b6`** (cała praca B6–B15 tylko tutaj).
- B6–B13 zamknięte i wypchnięte (ostatni commit B13: `07b26e3`). W toku: **B14 – boty po kalibracji**.
  Zostaje B14 i B15 (opis w `POSTEP.md`).
- Pełny dziennik pomiarów i decyzji: `raporty/kalibracja/dziennik.md`. Propozycje czekające na autora:
  `raporty/kalibracja/notatki_do_zmiany.md`. Hipotezy H1–H29: `raporty/kalibracja/inwentarz.md`.
- Pomiary (katalogi z `gry.csv`, `pary.csv`, `raport.md`): `raporty/kalibracja/pomiary/`.
- Skrypty analiz z sesji (nie są częścią gry): `raporty/kalibracja/skrypty/` – opis w punkcie 5.

## 2. Zasady (od autora – obowiązują zawsze)

Gałąź i git:
- Wszystko z B6–B15 na `kalibracja-b6`. **Bez merge do main bez zgody autora.** Bez `push --force`.
- Po każdym zamkniętym etapie: testy, ruff, `sprawdz` (pkt 3), wpis w dzienniku, odhaczenie w `POSTEP.md`,
  commit, `git pull --rebase`, push. Pushe na tę gałąź **nie** idą na FTP (lustro FTP tylko dla main).
- Nigdy nie commitować: `plan.txt`, `gra/db.sqlite3`, `gra/lokalne.json`, `gra/zapisy/`,
  `archiwum/czesc_A/analiza/serwer.log`, plików `.log` z pomiarów. Nie ruszać `pytanko.txt` ani `archiwum/pytanko.txt`
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
git pull -q --rebase --autostash origin kalibracja-b6 && git push -q origin kalibracja-b6
```

## 4. B14 – co zrobione i co dalej

Cel z planu: poziomy botów wyraźnie różne, każda strategia wygrywa w jakimś kontekście, cele B5 nadal spełnione.

Stan wyjściowy (`b12_trudnosc`, wersje „jak człowiek”, rywale średni, karty bez zmian po B13):
- dobra > średnia 87/100 par (cel ≥ 80%), słaba < średnia 99/100, karta słaba/średnia/dobra 0,10 / 0,45 / 0,52;
- pierwszy plus średniej w rundach 4–6 tylko 43/100 (w 3: 57) – to liczby B5 (rozruch), propozycja czeka u autora;
- alarmy słabej 1/100: premium słaba, ziarno 1018 – 4 tygodnie strat na starcie (gotówka po 1. rundzie 8 tys. zł,
  potem 0), w rundzie 5 debet 151 zł ponad limit (`skrypty/alarm2.py premium czlowiek_slaby 1018 7`);
- wg strategii (słaba / średnia / dobra): zrównoważony 0,19/0,54/0,65, tani 0,10/0,52/0,55, premium 0,11/0,39/0,53,
  **agresywny −0,06/0,34/0,34** (dobra = średnia, słaba poniżej „nic nie rób” −0,016), naśladowca 0,16/0,46/0,54.
  Słaba na minusie jest dozwolona przez cele B5 – problemem jest tylko alarm.

W toku: **pomiar `pomiary/b14_poziomy`** – poziomy botów łatwy/średni/trudny/niemożliwy, 5 strategii × 20 ziaren,
rywale średni, 400 gier (uruchomiony 6.11 wieczorem, log `pomiary/b14_poziomy.log`). Jeśli nie skończył się
w całości – dokończyć tym samym poleceniem:

```
.venv/Scripts/python -X utf8 -m balans.warianty pelny -o $P/b14_poziomy --ziarna 20 \
  --strategie zrownowazony,tani,premium,agresywny,nasladowca --firm 6 --rund 18 \
  --poziom latwy,sredni,trudny,niemozliwy --rywale sredni --warianty baza --procesy 2
```

Analiza: `skrypty/poz.py $P/b14_poziomy latwy,sredni,trudny,niemozliwy` (pary niższy < wyższy wg strategii,
alarmy, miejsca). Odniesienie z B5: łatwy < średni 83/100, średni < trudny 88/100, karty 0,10 / 0,33 / 0,67.

Następne kroki B14:
1. Wynik `b14_poziomy`. Jeśli średni < trudny słabo (< ok. 85%) – rozważyć umiejętność z B11: trudny bierze kredyt
   na drugi lokal (kredyt + drugi lokal dawał +0,30 karty, `b11_rozwoj`); zmiana poziomu `trudny` (nie
   `czlowiek_dobry`) z testem.
2. Turniej strategii (wszystkie firmy na jednym poziomie, kto wygrywa wg karty w jakim kontekście):
   `PYTHONPATH=. .venv/Scripts/python -X utf8 ../raporty/kalibracja/skrypty/turniej.py KATALOG 2 100 120
   sredni:6:18 sredni:4:18 sredni:8:18 sredni:6:12 sredni:6:26 trudny:6:18` – zapisuje `KATALOG/gry/*.csv`
   (strategia, strefy, karta, majątek, miejsce). Skrypt nowy, nieprzetestowany – najpierw 1 gra. Celem jest, żeby
   każda z 5 strategii była 1. w jakimś kontekście (liczba firm, długość gry, strefa).
3. H24 (dobra ≈ średnia przy agresywnym i tanim): diagnoza parami jak `k_dobry` (warianty `czlowiek:*`
   w `balans/warianty.py`); **zmiany `czlowiek_dobry` tylko jako propozycja** z tabelą przed/po.
4. Alarm słabej premium (ziarno 1018): sprawdzić, czy da się go usunąć umiejętnością bota (np. słaba nie kupuje
   dodatków przy zerowej gotówce) – nowa umiejętność z testem; inaczej opisać jako przypadek graniczny.
5. Po zmianach: kontrola trudności (`b14_trudnosc`) i porównanie z `b12_trudnosc` (`trud.py`).
6. Sekcja „## B14 – …” w dzienniku, odhaczenie w `POSTEP.md`, propozycje w notatkach, commit, push.

Potem **B15**: raport końcowy przed/po od tagu `kalibracja-start`, pola `zrodlo`/`pewnosc` w YAML przy każdej
zmienionej liczbie, zebranie propozycji z `notatki_do_zmiany.md`, instrukcja gracza (`gra/INSTRUKCJA.md` + PDF).

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

## 6. Czeka na decyzję autora (nie wdrażać samemu)

W `notatki_do_zmiany.md`: waga nieruchomości (Z1), lokal niewyposażony, wykup na kredyt, szerokie menu bez kosztu
(menu 8 dań u premium +0,53 karty), rozruch (liczba B5), promocje bez trwałego skutku / z rabatem przegrywają,
płaca minimalna bez rotacji, szkolenie z efektem na kilka tygodni, udogodnienia bez skutku przy uczciwej płacy,
kredyt bez celu obniża kartę (U22), mandaty skarbowe nie obniżają karty (Z1). Merge `kalibracja-b6` → main.
