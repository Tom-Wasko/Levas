# Dziennik – persona „Nauczyciel / mistrz gry”

Gra „A2 nauczyciel”, ziarno 303, 18 rund. Uczestnicy: 4 drużyny uczniów i 2 boty, Bafra
(zrównoważony, jak człowiek – średni, od R8 trudny) i Sułtan Premium (premium, trudny).
Skrypt: `skrypty/nauczyciel.py`, log: `log_nauczyciel.json`, przebieg: `przebieg_nauczyciel.txt`,
eksporty: `nauczyciel_wyniki.csv`, `nauczyciel_ranking.csv`, zrzuty: `zrzuty/nauczyciel_*.png`.

Drużyny (decyzje wysyłane przez API, tak jak robi to przeglądarka):
- **1A** gra z konta ucznia, porządnie (kalkulator „jak człowiek – dobry”).
- **2B** przepala gotówkę: od R3 reklama w 6 kanałach po 10 emisji i 4000 zł wypłaty co rundę.
- **3C** zapomina wysłać decyzje: w R5 zapisuje szkic bez „Wyślij”, w R6 nie robi nic.
- **4D** ustawia ceny × 2 i zamówienia „na zapas” × 3.

## Przebieg z perspektywy mistrza gry

**Przygotowanie.**
- Konta: `POST /api/konta` z dwiema osobami daje loginy i hasła (`ala.analizowa3`, `jan.testowy3`;
  końcówka 3 pochodzi z poprzednich uruchomień, więc unikalność loginów działa).
- Dopisanie do drużyny 1A daje 2 × 200. Panel pokazuje „Ala Analizowa, Jan Testowy”, a przy
  pozostałych drużynach link „dopisz uczniów” (zrzut `nauczyciel_r01_mg.png`).

**Uprawnienia (wszystko działa jak trzeba):**
- uczeń loguje się przez `/konta/login/`;
- zapis mistrza gry w drużynie z uczniami daje 403 „Mistrz gry ogląda decyzje drużyny tylko do
  odczytu.”;
- uczeń 1A próbujący zapisać decyzje w 2B dostaje 403 „To nie jest firma Twojej drużyny.”;
- uczeń w panelu mistrza gry widzi „Tylko mistrz gry może to zrobić.”.

**R1–R4.** Rundy zamykają się same, gdy wszyscy wyślą decyzje. Boty decydują przy zamknięciu.
Panel Decyzje pokazuje firmę, kto ją prowadzi, status („czeka” lub „wysłane”), gotówkę i link
„Strona firmy”. 4D od R2 jest na ostatnim miejscu i szybko traci gotówkę (39,9k → 17,0k w R4).

**R5 – 3C nie wysłało.**
- Panel: „Decyzje wysłało 3 z 4 drużyn. Runda zamyka się sama, gdy wyślą wszystkie. Możesz zamknąć
  ją wcześniej – drużyny bez wysłanych decyzji zagrają wtedy decyzjami zapisanymi do tej pory”
  (zrzut `nauczyciel_r05_mg_czeka.png`). Komunikat jest bardzo dobry: nauczyciel wie, co się
  stanie.
- Wstrzymanie gry, a potem „Przelicz” zwraca 400 „Gra jest wstrzymana – wznów ją, żeby zamknąć
  rundę.” To poprawne i zrozumiałe.
- Wznowienie i „Zamknij rundę” dają 200, runda 6. 3C zagrało zapisanym szkicem i nic nie straciło.

**R6 – 3C nie zapisało nic.**
- Zamknięcie wymuszone. 3C traci ok. 5000 zł majątku (52,2k → 47,2k) i spada z 2. na 3. miejsce.
- Potem wraca do gry i kończy na 2. miejscu, więc kara za zapomnienie jest odczuwalna, ale nie
  przekreśla wyniku. To dobra proporcja.

**R6 – alarm 4D.**
- Debet ponad limit: 524 zł. Panel mistrza gry (zrzut `nauczyciel_r06_mg_alarm.png`) pokazuje:
  „Alarm – debet ponad limit konta: 4D. W tej rundzie nie mogą inwestować ani brać kredytów, leasingu
  i lokat. Drużynę bez inwestora możesz uratować – link „Przyślij inwestora” przy gotówce”.
- W wierszu 4D widać „0 PLN · debet ponad limit 524 PLN · przyślij inwestora”. Jest to jasne
  i w dobrym miejscu.
- **Uczeń 4D tego alarmu prawie nie widzi.**
  - Dashboard (zrzut `nauczyciel_r06_4D_alarm.png`) pokazuje saldo 0 PLN, dochód −5919 i
    „Zadłużenie: 10 524 PLN” drobnym drukiem w „Pozostałe informacje”.
  - W planie rundy jest „Składniki: brak” i „Ceny: nie wszystkie dania mają cenę”, a o debecie
    ani słowa.
  - Lista błędów mówi tylko „Wydatki przekraczają saldo konta – zostanie uruchomiony kredyt
    odnawialny (ok. 3237 PLN)”, czyli to samo co w każdej rundzie od R6 do R18.
  - Komunikat o blokadzie i o inwestorze jest wyłącznie w Finanse ▸ Banki (`banki.js`, uwagi pod
    kontem).
- Inwestor ratunkowy 20 000 zł (`prowadzenie` → `inwestor`) daje 200. Od R7 alarm znika (wpłata
  spłaciła debet).

**R8.** Zmiana poziomu Bafry z „jak człowiek – średni” na „trudny” z listy w panelu daje 200. Bafra
przyspiesza (przyrost majątku ok. 8–10k na rundę wobec 4–5k wcześniej), awansuje z 3. na 2. miejsce
w R12, ale pod koniec spada na 4. (R17–R18 −8k majątku). Zmiana poziomu w trakcie gry działa i ma
widoczny skutek.

**R10 – cofnięcie i ponowne przeliczenie.** „Cofnij rundę 10” daje 200, po czym te same drużyny
ponownie wysyłają decyzje i runda się przelicza. Majątek wszystkich 6 firm przed i po jest
**identyczny co do grosza**. Determinizm jest zachowany, więc nauczyciel może bezpiecznie cofnąć
pomyłkę.

**R10–R18 – 4D w spirali.**
- Od R10 alarm wraca: debet ponad limit rośnie z 3826 zł do 54 567 zł w R18. Majątek netto spada
  z −20,6k do −70,1k, zadłużenie dochodzi do 84,6k.
- Drugiego inwestora nie ma (jeden na grę), więc mistrz gry nie ma żadnego narzędzia.
- 4D dalej co rundę traci 4–9k zł. Przyczyny: ceny × 2 (a dodatek 6,00 zł powyżej 200% ceny
  rynkowej wypada z menu) i zamówienia × 3, przez co psuje się 300–900 zł mięsa na rundę.
  Lista błędów mówi o tym co rundę („przeterminuje się… zamów mniej”), ale 4D tego nie czyta.
  To realistyczne.
- Dashboard po inwestorze (R13, zrzut `nauczyciel_r12_4D_po_inwestorze.png`) wygląda tak samo jak
  przed nim: saldo 0, zadłużenie 24 244 zł. Nigdzie nie widać, że był inwestor ani ile mu się
  jeszcze należy.
- Karta skumulowana 4D wynosi −1,245, czyli 1,4 punktu za 5. miejscem. Drużyna od R7 nie miała
  szans nawet na przedostatnie miejsce.

**Koniec.**
- Panel (zrzut `nauczyciel_koniec_mg.png`): „Gra zakończona – wyniki w zakładce Wyniki”, tabela
  firm z gotówką i przyciski „Cofnij rundę 18”, „Pobierz plik gry”.
- Eksport JSON: 410 KB. `wyniki.csv` (8 KB) i `ranking.csv` (0,5 KB) mają BOM, średniki i przecinek
  dziesiętny, więc otwierają się od razu w polskim Excelu.
- Ranking: miejsce, firma, bot, wynik (średnia), dochód razem, majątek, gotówka, zadłużenie, lokaty,
  pracownicy.

| miejsce | firma | wynik | dochód razem | majątek netto | gotówka |
|---|---|---|---|---|---|
| 1 | 2B (przepala gotówkę) | 0,58 | 83 634 | 62 485 | 46 584 |
| 2 | 3C (zapomina wysłać) | 0,53 | 72 800 | 118 385 | 101 151 |
| 3 | Sułtan Premium (bot trudny) | 0,37 | 46 853 | **131 807** | 47 321 |
| 4 | Bafra (bot, od R8 trudny) | 0,32 | 56 825 | 100 176 | 67 798 |
| 5 | 1A (gra porządnie, „dobry”) | 0,12 | 24 986 | 66 090 | 58 987 |
| 6 | 4D (ceny × 2, zapasy × 3) | −1,25 | −97 801 | −70 103 | 0 |

## Wnioski nauczyciela
- **Prowadzenie gry jest proste i bezpieczne.** Pauza, zamknięcie mimo braków, cofnięcie, zmiana
  poziomu bota, inwestor i eksporty działają z pierwszego razu, a komunikaty mówią, co się stanie.
- **Ranking zaskoczy klasę.**
  - Drużyna, która „przepalała” gotówkę na reklamę i wypłaty (2B), wygrała. Reklama zadziałała
    (najwyższy dochód), a 64 000 zł wypłat nie obniżyło karty.
  - Drużyna z największym majątkiem (bot Sułtan, 131,8k) jest dopiero 3.
  - Uczniowie zapytają: „czemu oni wygrali, skoro mają połowę naszych pieniędzy?”. Nauczyciel
    potrzebuje jednego zdania wyjaśnienia (rozdz. 3 instrukcji) albo kolumny „majątek” obok wyniku
    w Wynikach mistrza gry.
- **1A, grająca „porządnie” (kalkulator „jak człowiek – dobry”), była 5.** Gorzej od 2B i 3C
  („średni”). To kolejny przypadek odwróconej monotoniczności poziomów (por. optymalizator:
  `planista_trudny`).
- **Drużyna w spirali nie ma wyjścia.**
  - Po jednym inwestorze nauczyciel nie ma żadnego narzędzia, a uczniowie grają 12 rund bez
    szansy na zmianę miejsca.
  - Alarm jest głośny u mistrza gry, ale cichy u ucznia.
- **Brakuje w panelu mistrza gry:**
  - kolumny „wynik / miejsce” obok gotówki w widoku Decyzje (nauczyciel nie widzi, kto tonie, bez
    przełączania na Wyniki);
  - informacji, że inwestor już był (link po prostu znika).
