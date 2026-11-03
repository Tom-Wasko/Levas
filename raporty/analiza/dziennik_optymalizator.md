# Dziennik – persona „Optymalizator (student ekonomii, szuka exploitów)”

18 wariantów strategii × 3 ziarna (202, 203, 204). Każdy wariant to pełna gra 18 rund. Firma „Optima”
gra przeciwko 3 botom: Gigant (agresywny, trudny), Bafra (zrównoważony, jak człowiek – dobry) i Kopiuj
(naśladowca, średni). Decyzje Optimy to kalkulator botów (planista, poziom „jak człowiek – dobry”)
plus zmiana z wariantu. Miary:
- **wynik** – karta skumulowana, czyli średnia rund 2–18, tak jak ranking;
- **miejsce** w rankingu (z 4);
- **majątek netto** po 18. rundzie (start 40 000 zł);
- **dochód netto razem** z 18 rund;
- liczba **lokali** na końcu gry.

Powtórzenie (z `raporty/analiza/skrypty`, ok. 1–2 min na grę):
```
../../../gra/.venv/Scripts/python -X utf8 eksperymenty.py 202 203 204           → eksperymenty.json
../../../gra/.venv/Scripts/python -X utf8 eksperymenty.py --warianty=lokal_i_zamkniecie 202 203 204
                                                                                 → eksperymenty_dodatkowe.json
```
Skrypt korzysta z silnika bez API (to te same funkcje, które woła serwer). Żaden wariant nie miał
decyzji odrzuconych przez `limity.naruszenia`. Pierwsze uruchomienie `lokal_i_zamkniecie` wywróciło
się na błędzie w moim skrypcie (zwalniałem obiekty zamiast nazw), a nie w grze. Wyniki tego wariantu
pochodzą z drugiego uruchomienia, w pliku `eksperymenty_dodatkowe.json`.

## Wyniki (wynik / miejsce / majątek / dochód razem / lokale)

| wariant | ziarno 202 | ziarno 203 | ziarno 204 |
|---|---|---|---|
| **baza** (planista „jak człowiek – dobry”) | 0,452 / 1 / 112k / 66,9k / 1 | 0,489 / 2 / 114k / 67,8k / 1 | 0,337 / 2 / 99k / 54,1k / 1 |
| planista_trudny | **−0,396** / 4 / 25k / −15,6k / 2 | 0,26 / 2 / 89k / 43,5k / 2 | **−0,325** / 4 / 37k / −9,3k / 2 |
| drogo (ceny × 1,3) | 0,071 / 2 / 66k / 28,6k / 1 | 0,332 / 2 / 96k / 54,5k / 1 | −0,019 / 3 / 57k / 18,0k / 1 |
| tanio (ceny × 0,8) | 0,326 / 1 / 94k / 49,5k / 1 | 0,439 / 2 / 106k / 58,9k / 1 | 0,281 / 2 / 92k / 46,3k / 1 |
| **premium** (strategia premium) | 0,754 / 1 / 154k / 77,0k / 1 | 0,633 / 1 / 152k / 66,5k / 1 | 0,71 / 1 / 153k / 72,6k / 2 |
| **premium_drogo** (premium, ceny × 1,2) | **0,912** / 1 / 174k / 96,0k / 1 | 0,69 / 1 / 145k / 77,7k / 1 | **0,962** / 1 / 182k / 102,4k / 1 |
| premium_ekspansja (premium, trudny) | 0,897 / 1 / 172k / 94,9k / 1 | 0,648 / 1 / 153k / 69,8k / 1 | 0,977 / 1 / 181k / 101,8k / 1 |
| tani_kebab (strategia tani) | −0,245 / 3 / 35k / −3,8k / 2 | 0,241 / 3 / 78k / 36,6k / 1 | 0,002 / 3 / 55k / 15,3k / 2 |
| agresywny (strategia agresywna) | 0,039 / 4 / 76k / 13,0k / 1 | 0,203 / 3 / 94k / 29,2k / 1 | 0,069 / 3 / 81k / 16,6k / 1 |
| ekspansja (trudny, kolejny lokal przy 30k) | 0,555 / 2 / 121k / 76,0k / 1 | 0,487 / 2 / 112k / 65,8k / 1 | 0,521 / 1 / 119k / 72,3k / 1 |
| ekspansja_na_kredyt (+50k kredytu w R1) | 0,183 / 2 / 116k / 70,9k / 1 | 0,199 / 3 / 109k / 63,2k / 1 | 0,184 / 2 / 118k / 71,8k / 1 |
| **bez_lokalu_lokata** (nic, lokata ING) | −0,019 / 3 / 30k / −1,3k / 0 | −0,019 / 3 / 30k / −1,3k / 0 | −0,019 / 3 / 30k / −1,3k / 0 |
| nic_z_biurem (jak wyżej + najtańsze biuro) | −0,028 / 3 / 38k / −2,1k / 0 | −0,028 / 3 / 38k / −2,1k / 0 | −0,028 / 3 / 38k / −2,1k / 0 |
| lokal_i_zamkniecie (od R11 bez ludzi i dostaw) | −0,166 / 3 / 46k / 0,5k / 1 | −0,189 / 3 / 42k / −3,5k / 1 | −0,254 / 4 / 37k / −8,2k / 1 |
| **wyplaty** (gotówka ponad 25k do portfela) | 0,447 / 1 / **32k** / 67,4k / 1 | 0,474 / 2 / **42k** / 66,2k / 1 | 0,331 / 2 / **33k** / 53,4k / 1 |
| harpagon_dzwignia (20k w R1, spłata R5) | 0,438 / 1 / 111k / 70,5k / 1 | 0,453 / 2 / 110k / 67,9k / 1 | 0,31 / 2 / 98k / 56,7k / 1 |
| niskie_pensje (płaca minimalna) | 0,462 / 1 / 114k / 69,1k / 1 | 0,497 / 2 / 116k / 70,0k / 1 | 0,352 / 2 / 102k / 56,5k / 1 |
| max_reklama (ulotki + plakaty po 10 emisji) | 0,46 / 1 / 112k / 68,6k / 1 | 0,596 / 1 / 127k / 80,5k / 1 | 0,408 / 2 / 110k / 64,3k / 1 |

Składniki karty skumulowanej (ziarno 202):

| wariant | wynik ekon. | zad. pracowników | zad. klientów | rozwój | wsk. zadłużenia | wynik |
|---|---|---|---|---|---|---|
| baza | 0,868 | 0,915 | 1,069 | 0,593 | 1,0 | 0,452 |
| premium | 1,021 | 0,982 | 1,129 | 0,702 | 1,0 | 0,754 |
| ekspansja_na_kredyt | 0,939 | 0,911 | 1,089 | 0,595 | **0,42** | 0,183 |
| bez_lokalu_lokata | −0,016 | 0 | 0 | 0,535 | 0,294 | −0,019 |
| wyplaty | 0,875 | 0,915 | 1,069 | 0,587 | 1,0 | 0,447 |
| planista_trudny | −0,182 | 0,917 | 0,982 | 0,661 | 0,97 | −0,396 |

## Co znalazłem (jak student szukający dziury)

1. **Premium wygrywa zawsze, a drożej jest jeszcze lepiej.** Strategia premium zajmuje 1. miejsce na
   każdym ziarnie. Podniesienie jej cen o 20% daje kolejne +0,06–0,25 (do 0,96) i majątek 182k.
   W wariancie bazowym te same +30% do cen obniża wynik o 0,15–0,38. Popyt na dania premium reaguje
   na cenę za słabo. To kandydat do kalibracji B, a nie do części A. Porównanie z dominacjami z B4
   jest w raporcie A3.
2. **„Nic nie rób” bije słabego gracza.** Firma bez lokalu, z całą gotówką na lokacie, ma −0,019
   na każdym ziarnie i zajmuje 3. miejsce przed botem naśladowcą lub agresywnym. Nowicjusz, który
   grał aktywnie, skończył z −0,297. Przyczyna: przy stracie karta to `wynik_ekonomiczny × waga 1,0`
   (`silnik/wyniki/karta.py`), a zadowolenie pracowników i klientów równe 0 nie ma wtedy znaczenia.
   Zero klientów nie kosztuje więc nic. Wynik −0,019 to prawie zero, a przy słabszych rywalach
   (nauczyciel: 4D −1,245) daje miejsce w środku stawki.
3. **Kredyt na rozwój karta karze trzy razy mocniej niż dochód go nagradza.**
   - `ekspansja_na_kredyt` ma podobny dochód i majątek jak `ekspansja` (70,9k wobec 76,0k).
   - Mimo to ma wynik 0,18 wobec 0,55, bo wskaźnik zadłużenia spada do 0,42.
   - W mianowniku wskaźnika jest majątek karty (sprzęt, lokale) plus skumulowany dochód plus dług.
     Gotówki z kredytu, która leży na koncie, w nim nie ma.
   - Wniosek dla gracza: nigdy nie bierz kredytu. Stoi to w sprzeczności z zakładką Finanse ▸ Banki,
     która kredyty eksponuje.
4. **Drugi lokal szkodzi.**
   - `planista_trudny` otwiera 2 lokale i kończy na −0,40 / −0,33 (ziarno 203: 0,26). Planista
     „jak człowiek – dobry” z jednym lokalem ma 0,34–0,49.
   - Tak samo nowicjusz (R15, −2,48 w jednej rundzie). Wyposażenie drugiego lokalu idzie w koszty
     rundy (środki poniżej 10 000 zł, amortyzacja 100%), a strata ma wagę 1,0.
   - `ekspansja` z wyższym progiem gotówki nigdy nie otworzyła drugiego lokalu i była lepsza od bazy.
   - Tak więc „trudny” bot gra gorzej niż „dobry”, co jest problemem monotoniczności poziomów
     (poziomy kalibruje B, ale przyczyna leży w karcie).
5. **Wypłaty do portfela są darmowe dla karty.** `wyplaty` wyprowadza 70–80k zł (majątek 32k wobec
   112k), a wynik spada tylko o 0,005. Ranking liczy się wyłącznie z karty, więc drużyna może
   „opróżnić firmę” bez kary. Nauczyciel 2B (4000 zł wypłaty co rundę) wygrał grę. To kwestia do
   decyzji autora: czy wypłata właściciela to koszt w oczach karty? Pytanie zapisałem w A3.
6. **Harpagon jako dźwignia nic nie daje.** 20k na 4 rundy: −0,01 do −0,03. Lichwiarz jest
   ustawiony poprawnie i nie jest exploitem.
7. **Płaca minimalna: +0,01–0,015.** Spadek zadowolenia pracowników prawie się nie odbija w karcie,
   a zadowolenie pracowników zostaje na poziomie ok. 0,91. Dźwignia jest za słaba, żeby gracz
   ją zauważył. Jeszcze nie exploit, ale też nie decyzja z konsekwencjami.
8. **Reklama się opłaca** (+0,01–0,11, najmocniej na ziarnie 203), przy czym bez żadnej strategii:
   to po prostu 10 emisji ulotek i plakatów. To dobry kierunek. Warto sprawdzić w B, czy nie ma
   nasycenia.
9. **Ceny × 0,8 dają −0,1, ceny × 1,3 dają −0,3 do −0,4.** Dla zwykłego kebaba elastyczność cen
   działa sensownie. Kłopot dotyczy tylko premium (punkt 1).
10. **`lokal_i_zamkniecie` (zwolnienie wszystkich od R11):**
    - wynik −0,17 do −0,25, czyli gorzej niż „nic nie rób”;
    - czynsz i biuro dalej idą, więc tak powinno być;
    - w wariancie nie użyłem wypowiedzenia najmu (decyzja `wypowiedz`), więc nie wiem, czy
      „zamknięcie biznesu” z wypowiedzeniem byłoby lepsze od bezczynności. Do sprawdzenia w B.

## Exploity w skrócie
- **Mocny:** premium z wysokimi cenami (powtarzalny, +0,3–0,5 ponad bazę).
- **Średni:** „nic nie rób” daje karta ≈ 0 i miejsce przed słabymi drużynami, a strata nie jest
  karana mocniej niż bezczynność.
- **Odwrotny exploit (pułapka):** kredyt i drugi lokal zawsze obniżają wynik, choć instrukcja
  zachęca do rozwoju.
- **Kwestia zasad:** wypłaty właściciela bez wpływu na kartę.
