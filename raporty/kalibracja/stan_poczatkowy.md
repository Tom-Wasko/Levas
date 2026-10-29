# Stan początkowy kalibracji (B4, 29.10.2026)

Punkt odniesienia „przed” dla B5–B15: tag `kalibracja-start`. Zasady po krokach Z1–Z7, boty po B3.

Wszystkie pomiary: badana firma (bot) wśród rywali na poziomie średnim, 18 rund, 6 firm, kapitał 40 tys. zł,
chyba że napisano inaczej. Karta = średni wynik działalności z rund 2…N (karta skumulowana, ranking mistrza
gry). „Lepszy” / „gorszy” = ≥ 70% wygranych par i 95% przedział bez zera. Pomiary w `pomiary/b4_*`:

| katalog | co | gier |
|---|---|---|
| `b4_trudnosc` | 6 poziomów (3 wersje „jak człowiek” + łatwy, średni, trudny) × 5 strategii × 20 ziaren | 600 |
| `b4_firmy_trudnosc` | człowiek średni i poziom średni, 4 i 8 firm, 10 ziaren | 200 |
| `b4_dlugosc` | człowiek średni i poziom średni, 12 i 26 rund, 10 ziaren | 200 |
| `b4_warianty` | 28 wariantów opcji × 5 strategii × 30 ziaren, poziom średni | 4350 |
| `b4_warianty_firmy` | to samo przy 4 i 8 firmach, strategie zrównoważony, tani, premium, 10 ziaren | 1740 |

Razem 7090 gier, 2 h 13 min na 5 procesach (ok. 1,1 s na grę).

## 1. Krzywa trudności

| poziom badanej | karta | majątek na koniec | 1. plus (średnio) | 1. plus w rundzie 2 | gry z alarmem | miejsce (z 6) |
|---|---|---|---|---|---|---|
| człowiek słaby | 0,11 | 68 tys. zł | 2,9 | 51/100 | 17/100 | 5,1 |
| człowiek średni | 0,42 | 115 tys. zł | 2,6 | 62/100 | 9/100 | 3,7 |
| człowiek dobry | 0,62 | 136 tys. zł | 2,6 | 62/100 | 9/100 | 3,0 |
| łatwy | 0,21 | 80 tys. zł | 3,2 | – | 11/100 | 4,6 |
| średni | 0,49 | 122 tys. zł | 2,9 | – | 8/100 | 3,4 |
| trudny | 1,08 | 182 tys. zł | 2,6 | – | 8/100 | 1,9 |

- Kolejność w parach (ta sama gra i ziarno): słaby < średni 96/100, średni < dobry 95/100, łatwy < średni
  88/100, średni < trudny 93/100. Przy każdej strategii osobno też (najsłabiej: łatwy < średni przy
  agresywnym 15/20, średni < trudny przy premium 16/20, wersje „jak człowiek” ≥ 18/20).
- Pierwszy plus bota „jak człowiek” średniego: runda 2 – 62, runda 3 – 18, runda 4 – 16, runda 5 – 3,
  runda 7 – 1 (na 100 gier). **Cel B5 (runda 4–6) spełnia 19% gier – gra jest za łatwa (H1).**
- Alarmy debetu prawie tylko przy strategiach agresywnej i premium: wersja słaba – agresywny 15/20, premium
  2/20; średnia – 5/20 i 4/20; dobra – 6/20 i 3/20. **Cel B5 „wersja słaba bez alarmu” nie jest spełniony.**
- Cel B5 „dobra wygrywa ze średnią w ≥ 80% par” jest spełniony (95%).

## 2. Opcje: dominacje (6 firm, 150 par na wariant)

Baza bota średniego: konto mBank, biuro e-Księgi24, higiena podstawowa, polisy wg strategii, umowy o pracę.

| wariant | Δ karta | wygrane | Δ majątek | ocena | uwagi |
|---|---|---|---|---|---|
| umowa zlecenie dla wszystkich | +0,08 ± 0,01 | 99% | +9,8 tys. zł | **dominuje** | każda strategia i liczba firm (97–100%) |
| drugi lokal (jak trudny) | +0,23 ± 0,04 | 85% | +24,0 tys. zł | **dominuje** | 83–97% poza agresywnym (szum); 4 firmy +0,74…+0,94 |
| wszystkie polisy | +0,01 ± 0,00 | 73% | +1,3 tys. zł | lepszy | mała korzyść; premium = baza |
| inny bank niż mBank | −0,01 | 5–7% | −1,0…−1,4 tys. zł | zdominowane | każdy z 5 banków |
| inne biuro niż e-Księgi24 | −0,00…−0,01 | 3–6% | −0,2…−0,8 tys. zł | zdominowane | każde z 4 biur |
| higiena „firma” / „HACCP” | −0,01 | 28% / 17% | −0,9 / −1,5 tys. zł | zdominowane | „podstawowa” wystarcza |
| higiena „brak” | −2,74 ± 0,11 | 0% | −268 tys. zł | katastrofa | lokal nie rusza, alarm w 14 rundach |
| cena 85 / 100 / 115% preferowanej | −0,04 / +0,13 / +0,18 | 47–65% | | szum ogółem | zależy od strategii (niżej) |
| jakość 1 / 2 / 3★ | +0,01 / −0,05 / +0,07 | 40–64% | | szum ogółem | zależy od strategii (niżej) |
| bez kampanii | +0,03 ± 0,02 | 50% | | szum ogółem | agresywny 100% lepiej, premium i zrównoważony gorzej |
| bez promocji | +0,03 ± 0,01 | 64% | | szum ogółem | tani 95%, premium 100% lepiej; zrównoważony 17% |

Po strategiach (wygrane pary wariantu wobec bazy, 30 par):

| strategia | cena 0,85 / 1,0 / 1,15 | jakość 1 / 2 / 3 | bez kampanii | bez promocji |
|---|---|---|---|---|
| agresywny | 93 / 100 / 100% | 93 / 93 / baza | 100% | 57% |
| tani | 83 / 80 / 70% | baza / 3 / 43% | 47% | 95% |
| premium | 3 / 20 / 77% | 0 / 3 / baza | 27% | 100% |
| zrównoważony | 30 / 43 / 37% | 83 / baza / 87% | 27% | 17% |
| naśladowca | 27 / 50 / 40% | 90 / baza / 90% | baza | baza |

- **Agresywny ma złe parametry strategii**: poprawia go prawie każda zmiana (inna cena, inna jakość, brak
  kampanii). Reklamuje się ponad przepustowość jednego lokalu (H7) i wpada w debet.
- **Tani jest za tani**: każda z cen 0,85–1,15 ceny preferowanej daje więcej niż jego własna; promocje mu
  szkodzą.
- **Premium**: wyższa cena (1,15) pomaga, promocje szkodzą. Niższa jakość to przegrana w każdym kontekście.
- Jakość 2★ przegrywa z 1★ i 3★ u zrównoważonego i naśladowcy (83–90% par za 1★ i za 3★) – środek jest
  zdominowany (do B7/B10).

## 3. Hipotezy z B1

| | hipoteza | wynik B4 |
|---|---|---|
| H1 | gra za łatwa | **potwierdzona**: 1. plus „jak człowiek” średniego w rundzie 2 w 62% gier, marża netto 19% (tabela 6) |
| H2 | koszty pracy za niskie | **potwierdzona**: 21% przychodu (realia 25–35%) |
| H3 | umowa zlecenie dominuje | **potwierdzona**: 99% par, +9,8 tys. zł |
| H4 | mBank dominuje | **potwierdzona**: każdy inny bank 5–7% par |
| H5 | e-Księgi24 dominuje | **potwierdzona**: każde inne biuro 3–6% par |
| H6 | drugi lokal zawsze się opłaca | **potwierdzona**: 85% par, +24 tys. zł; przy 4 firmach 100% |
| H7 | reklama ponad przepustowość się nie zwraca | **potwierdzona dla agresywnego** (bez kampanii 100% par); premium i zrównoważony na kampaniach zyskują |
| H8 | jakość 3★ dominuje | **częściowo**: 3★ lepsza u zrównoważonego i naśladowcy (87–90%), u taniego szum; 2★ zdominowana |
| H9 | lokata bije gotówkę | nie zmierzona – bot nie zakłada lokat (krok 0 B11) |
| H10 | Harpagon darmową dźwignią | nie zmierzona – bot nie pożycza (krok 0 B11); Z1 wyjął Harpagona z karty |
| H11 | sprzęt pompuje kartę | nie zmierzona wariantem; Z1 zmienił „rozwój firmy” (krok 0 B6/B10) |
| H12 | kupno lokalu bije najem | nie zmierzona – brak wariantu kupna (krok 0 B6) |
| H13 | 2 za 1 opłaca się zawsze | **raczej obalona**: promocje bota szkodzą taniemu i premium, pomagają zrównoważonemu; każda promocja osobno – B7/B10 |
| H14 | polisy mają ujemną wartość | **obalona** (jak w punkcie zero): komplet polis lepszy w 73% par, mała kwota |
| H15 | higiena „podstawowa” wystarcza | **potwierdzona**: „firma” i „HACCP” zdominowane; „brak” to katastrofa (do B12: brak powinien być ryzykiem, a nie pewną klęską) |
| H16 | dyskont dominuje zakupy | nie zmierzona – brak wariantów dostawców (krok 0 B8) |
| H17 | łatwy agresywny bankrutuje | **potwierdzona**: łatwy agresywny karta −0,22, alarmy 4/8; nawet średni agresywny ma alarm w 9/30 gier |

Wobec punktu zero (zasady sprzed Z): wnioski o umowie zlecenie, banku, biurze, polisach i higienie bez zmian.
Karta liczy się dziś inaczej (średnia zamiast sumy), więc wielkości Δ nie są porównywalne.

## 4. Strategie (poziom średni, gry bazowe)

| strategia | firm | gier | karta | majątek | 1. plus | alarmy | miejsce | 1. miejsce |
|---|---|---|---|---|---|---|---|---|
| zrównoważony | 6 | 30 | 0,68 | 138 tys. zł | 2,8 | 0/30 | 2,8 | 7/30 |
| premium | 6 | 30 | 0,70 | 153 tys. zł | 2,9 | 1/30 | 2,6 | 6/30 |
| naśladowca | 6 | 30 | 0,56 | 120 tys. zł | 2,8 | 0/30 | 3,0 | 5/30 |
| tani | 6 | 30 | 0,30 | 88 tys. zł | 2,4 | 0/30 | 4,4 | 0/30 |
| agresywny | 6 | 30 | 0,05 | 92 tys. zł | 3,8 | 9/30 | 5,1 | 0/30 |

Tani i agresywny nigdy nie wygrywają (cel B14: każda strategia wygrywa w jakimś kontekście). Przy 4 firmach
premium wygrywa 7/10 gier.

## 5. Liczba firm i długość gry

| poziom badanej | firm | rund | karta | majątek | 1. plus | plus w rundzie 2 | alarmy | miejsce |
|---|---|---|---|---|---|---|---|---|
| człowiek średni | 4 | 18 | 0,68 | 145 tys. zł | 2,3 | 39/50 | 0/50 | 2,3 z 4 |
| człowiek średni | 6 | 18 | 0,44 | 117 tys. zł | 2,4 | 36/50 | 7/50 | 3,6 z 6 |
| człowiek średni | 8 | 18 | 0,30 | 101 tys. zł | 2,7 | 29/50 | 5/50 | 4,6 z 8 |
| człowiek średni | 6 | 12 | 0,46 | 100 tys. zł | 2,4 | 36/50 | 7/50 | 3,5 |
| człowiek średni | 6 | 26 | 0,46 | 143 tys. zł | 2,4 | 36/50 | 7/50 | 3,5 |
| średni | 4 | 18 | 0,73 | 150 tys. zł | 2,4 | 33/50 | 1/50 | 2,3 z 4 |
| średni | 6 | 18 | 0,52 | 125 tys. zł | 2,8 | 23/50 | 6/50 | 3,3 z 6 |
| średni | 8 | 18 | 0,36 | 108 tys. zł | 2,9 | 24/50 | 6/50 | 4,3 z 8 |

- **Gra przy 4 firmach jest wyraźnie łatwiejsza** (karta 0,68 wobec 0,44 przy 6 i 0,30 przy 8). Z4 zmniejsza
  liczbę lokali, ale popyt miasta zostaje, więc firma ma mniej konkurentów na tę samą pulę klientów.
  Zgodnie z instrukcją nie stroję popytu – **pytanie do autora** (dziennik B4).
- Długość gry nie zmienia karty (0,46 / 0,44 / 0,46 przy 12 / 18 / 26 rundach); majątek rośnie z liczbą rund.

## 6. Realia (gra 6 botów średnich, 18 rund, ziarna 7 i 11, rundy 3–18, wszystkie firmy)

| wielkość | gra | realia (orientacyjnie) | ocena |
|---|---|---|---|
| cena kebaba (po rabacie) | 25,0 zł (tani 21,4, premium 27,8) | 25–40 zł | dolna granica |
| składniki, % przychodu | 33,8% (agresywny 42,9%) | 25–35% | w widełkach, agresywny marnuje towar |
| koszty pracy (pensje + ZUS pracodawcy), % przychodu | 20,7% | 25–35% | **za nisko** (właściciel pracuje bez pensji) |
| czynsz, % przychodu | 4,2% (z utrzymaniem lokalu 5,5%) | 8–15% | **za nisko** – przez wysoki przychód |
| czynsz w zł | ok. 640 zł / tydz. (ok. 2,8 tys. zł / mies., Nadbystrzycka) | centrum Lublina 1,8–4,8 tys. zł / mies. (25–40 zł/m², ogłoszenia 2026) | realny |
| przychód na lokal | 22,4 tys. zł / tydz. (ok. 97 tys. zł / mies.) | mały kebab: kilkadziesiąt tys. zł / mies. | **za wysoko** |
| dania główne na lokal dziennie | 117 (tani 76, agresywny 186) | kilkadziesiąt do kilkuset klientów | w widełkach |
| marża netto | 19,0% (agresywny 6,8%) | kilka do kilkunastu procent | **za wysoko** |

Wniosek dla B5: czynsz w złotych jest realny, a jego udział jest niski, bo przychód na lokal jest za wysoki.
Stroić trzeba więc popyt i ceny (przychód) oraz koszty pracy, a nie czynsz. Prawo (płaca minimalna, ZUS,
podatki) jest zamrożone.

Źródła czynszów (ogłoszenia, październik 2026): otodom.pl – lokal 133 m², Śródmieście, 4000 zł / mies.;
domiporta.pl – al. Piłsudskiego 145 m², 4800 zł / mies.; adresowo.pl – ul. Szewska 100 m², 4000 zł / mies.;
ul. Obrońców Pokoju 70 m², 1800 zł / mies. Cen kebabów w Lublinie w sieci nie znalazłem – widełki z planu.

## 7. Co dalej
- **B5** (gospodarka i trudność): popyt i ceny, koszty pracy, kapitał – cel: pierwszy plus „jak człowiek”
  średniego w rundzie 4–6, wersja słaba bez alarmu, dobra > średnia w ≥ 80% par. Wynik do zatwierdzenia przez
  autora.
- Dominacje do obszarów: umowa zlecenie (B9), drugi lokal (B6), mBank (B11), e-Księgi24 i higiena (B12),
  jakość 2★, ceny i promocje strategii (B7/B10), parametry strategii agresywnej i taniej (B14).
- Warianty do dopisania w kroku 0 obszarów: lokata i kredyt (B11), Harpagon (B11), kupno lokalu (B6),
  każda promocja (B7), dostawcy (B8).
