[[Elementy mapy]] · [[Ustalenia gry]] · [[Prawidła świata]]

# Menu i składniki

Menu to **stała lista dań ze stałymi recepturami** – drużyna nie wymyśla własnych dań. Decyduje, które dania sprzedaje, po jakiej cenie i z jakich składników je robi.

## Decyzje drużyny (co rundę, osobno dla każdego lokalu)
- Które dania są w menu. Danie wymaga sprzętu – bez rożna nie ma kebaba.
- Cena brutto każdego dania.
- Skąd i jakiej jakości składniki kupuje (1–3★; lepsze są droższe).
- **Plan dostaw na cały tydzień:** ilość każdego składnika na każdy dzień dostawy danego dostawcy (p. „Psucie się przy decyzjach co tydzień”). Za dużo oznacza straty, za mało – utraconą sprzedaż.

## Lista dań (roboczo)
| Danie | Receptura (1 porcja) | Sprzęt | Cena rynkowa brutto |
|---|---|---|---|
| Kebab w bułce | bułka, 130 g mięsa, 60 g warzyw, 40 g sosu, opakowanie | rożen | 22–27 zł |
| Kebab w tortilli (rollo) | tortilla, 150 g mięsa, 80 g warzyw, 40 g sosu, opakowanie | rożen | 24–30 zł |
| Kebab box | 200 g frytek, 130 g mięsa, 40 g sosu, box | rożen, frytownica | 20–26 zł |
| Talerz kebab | 230 g mięsa, 200 g frytek, 150 g surówek, 50 g sosu, box | rożen, frytownica | 30–40 zł |
| Falafel (wege) | 5 falafli, pita, 80 g warzyw, 40 g hummusu, opakowanie | frytownica | 22–28 zł |
| Frytki | 200 g frytek, opakowanie | frytownica | 9–14 zł |
| Napój | 1 puszka lub butelka | lodówka na napoje | 6–9 zł |
| Dodatek (sos, ser, jalapeño) | 40 g | – | 2–4 zł |

Receptury i ceny pochodzą ze starego Levasa (`dane/menu/kategorie.yaml`). Wybieranie wielkości porcji i zamienników składników usuwamy – zostaje jedna receptura na danie.

## Jakość dania (roboczo, do kalibracji w kroku 5)
`jakość = 0,5 × jakość składników + 0,3 × umiejętności kucharzy + 0,2 × jakość sprzętu`, wszystko w gwiazdkach 1–3, minus kara za składniki w ostatnim dniu terminu. Jakość wpływa na popyt i zadowolenie klientów.

## Terminy ważności (startowo)
| Składnik                     | Przechowywanie | Termin od dostawy              |
| ---------------------------- | -------------- | ------------------------------ |
| Mięso kebab – stożek świeży  | chłodnia       | 4 dni                          |
| Mięso kebab – stożek mrożony | zamrażarka     | 90 dni (niższa jakość)         |
| Bułki i pita świeże          | suche          | 2 dni                          |
| Pita mrożona                 | zamrażarka     | 60 dni (tańsza, niższa jakość) |
| Tortilla                     | suche          | 30 dni                         |
| Warzywa i surówki            | chłodnia       | 3–10 dni (zależnie od rodzaju) |
| Sosy, ser                    | chłodnia       | 14–30 dni                      |
| Hummus                       | chłodnia       | 7 dni                          |
| Frytki, falafel mrożone      | zamrażarka     | 90–180 dni                     |
| Napoje, olej                 | suche          | 180 dni                        |
| Opakowania                   | suche          | bez terminu                    |

- Zużycie metodą **FIFO** (najpierw najstarsze partie). Przeterminowane partie są wyrzucane i trafiają do raportu strat.
- Chłodnia i zamrażarka mają pojemność zależną od sprzętu; nie da się zamówić więcej, niż się zmieści.
- Brak składnika wyłącza dania, które go potrzebują, do następnej dostawy. Część klientów wybiera inne danie, reszta odchodzi.
- Dostawy w dni dostaw dostawcy (np. poniedziałek i czwartek) – dwie mniejsze dostawy w tygodniu to mniej strat niż jedna duża.

## Psucie się przy decyzjach co tydzień
Drużyna decyduje raz na rundę (tydzień), ale terminy ważności liczą się w dniach. Dlatego:
1. **Decyzja = plan dostaw na 7 dni.** Dla każdego dostawcy drużyna wpisuje ilość na każdy jego dzień dostawy. Piekarnia dowozi codziennie, hurtownie i producent mięsa 1–2 razy w tygodniu, z dyskontu przywozi się towar samemu w wybrany dzień (czas właściciela).
2. **Silnik liczy tydzień dzień po dniu.** Rano przychodzą dostawy, w ciągu dnia klienci (popyt z losowością) zużywają składniki od najstarszej partii, wieczorem przeterminowane partie idą do strat. Termin liczy się razem z dniem dostawy: bułki z poniedziałku (2 dni) sprzedaje się w poniedziałek i wtorek, a we wtorek wieczorem idą do strat.
3. **W trakcie tygodnia nic się nie zmienia.** Drużyna nie widzi, jak idzie sprzedaż, i musi przewidzieć popyt (więcej w piątek i sobotę, kalendarz miejski). Planuje na podstawie raportu z poprzedniej rundy.
4. **Raport po rundzie:** sprzedaż, braki i straty dzień po dniu dla każdego składnika.

```
Zamówienie – Piekarnia (dostawa codziennie)
      Pn  Wt  Śr  Cz  Pt  So  Nd
Bułki 80  80  90  90 120 150 100

Zamówienie – Makro (dostawa Pn, Cz)
           Pn     Cz
Mięso   12 kg  14 kg
Warzywa  6 kg   7 kg
```

**Zamiennik:** mrożona pita (60 dni) jest zapasem bezpieczeństwa – tańsza i bez strat, ale obniża jakość dania. Drużyna wybiera między świeżością a pewnością.
