# Propozycje zmian w notatkach autora (kalibracja B)

Notatki (`notatki/`) zmienia się tylko za zgodą autora. Tu są proponowane teksty – do akceptacji albo poprawki.

**29.10.2026: autor zatwierdził Z1–Z6 i B5 – wpisane do notatek** (Z5 z poprawką: boty „jak człowiek”
widoczne dla mistrza gry).

## Z1 – karta wyników (29.10.2026) → `notatki/Ustalenia gry.md`, sekcja „Karta wyników”

Dziś:
> **Wynik tygodnia** = iloczyn pięciu wskaźników; przy ujemnym wyniku ekonomicznym = 0. **Karta skumulowana** = średnia wszystkich kart.

Proponowany tekst:
> **Wynik tygodnia** = iloczyn pięciu wskaźników. Przy stracie wynik jest ujemny i proporcjonalny do straty
> (waga × wynik ekonomiczny, bez mnożenia przez wskaźniki – lepsze wskaźniki nie pogłębiają minusa; waga w
> `zalozenia.yaml → karta_wynikow → strata`). **Karta skumulowana** = średnia kart z rund 2..N.

W tabeli wskaźników:
- „Wynik ekonomiczny” → „dochód netto tygodnia (z KPiR) minus odsetki Harpagona, względem progu”;
- „Rozwój firmy” → „liczba lokali, dań w menu i pracowników; majątek po amortyzacji (sprzęt, wyposażenie, kupione
  lokale, budynki i działki); inwestycje liczą się tylko ponad najwyższy dawny majątek (odkup nie jest
  inwestycją)”;
- „Wskaźnik zadłużenia” → „kredyty bankowe i dług u Harpagona względem majątku po amortyzacji (1 bez długu)”.

## Z2 – majątek netto (29.10.2026) → `notatki/Plan optymalizacji.md`, „Definicje”

Doprecyzowanie: portfel właściciela jest poza majątkiem netto pokazywanym mistrzowi gry (wynik rundy, panel,
CSV), bo zmiany portfela zdradzałyby klub (kasyno jest ukryte przed mistrzem gry). Pomiary balansu doliczają
portfel osobno. Proponowany dopisek do definicji majątku netto:
> Mistrz gry widzi majątek netto firmy bez portfela właściciela (portfel zdradzałby klub); w pomiarach
> balansu portfel jest doliczany. Zaległości to dziś zaległe raty kredytów (w długu kredytu) i leasingu –
> podatki, ZUS, czynsz i dostawcy są płacone od razu z konta (debet).

## Z3 – debet ponad limit i inwestor ratunkowy (29.10.2026) → `notatki/Ustalenia gry.md`, finanse

Proponowany dopisek:
> **Debet ponad limit konta** – alarm u mistrza gry; w następnej rundzie blokada inwestycji (lokal, stanowiska,
> sprzęt, udogodnienia, wyposażenie), nowych kredytów, leasingu i lokat. Odsetki karne banku zostają, innych kar
> nie ma. **Inwestor ratunkowy** (przysyła mistrz gry, jeden na grę): wpłata do 40 000 zł na początku rundy,
> najpierw spłaca debet; przez 8 rund bierze 30% dodatniego dochodu netto; niezwrócona część wpłaty liczy się
> jak dług (wskaźnik zadłużenia, majątek netto). Wartości: założenie, do kalibracji.

## Z4 – liczba lokali zależna od liczby firm (29.10.2026) → `notatki/Elementy mapy.md`

Proponowany dopisek:
> Liczba lokali na mapie zależy od liczby drużyn (klucz `od_firm` w `dane/mapa/lokale.yaml`): 8 firm – 38 lokali,
> 6–7 – 29, 4–5 – 20 (około 5 na firmę, wszystkie strefy, podobne proporcje typów). Popyt miasta się nie zmienia.

## Z5 – bot „jak człowiek” (29.10.2026) → `notatki/Ustalenia gry.md`, boty

Proponowany dopisek:
> **Bot „jak człowiek”** (do pomiaru trudności, poziomy `czlowiek_slaby/sredni/dobry`, niewidoczne dla mistrza
> gry): prognozuje z popytu w raportach poprzednich rund i z potencjału lokalu w zakładce Klienci, a nie z modelu
> popytu. Słaby: zeszły tydzień ±25%, proste reguły; średni: zeszły tydzień ±10%, planuje obsadę; dobry: średnia
> z dwóch tygodni razy zmiana puli strefy, reklama z wolną kuchnią, drugi lokal.

## Z6 – kalendarz do kwietnia 2026 (29.10.2026) → `notatki/Prawidła świata.md`, kalendarz miejski

Proponowany dopisek:
> Kalendarz sięga do kwietnia 2026: mecze Motoru wiosną 2026 (prawdziwy terminarz), Finał WOŚP, Popielec i
> Wielki Piątek (więcej falafla, mniej mięsa), początek semestru letniego, Jarmark Wielkanocny na Starym Mieście.

## B5 – rozruch nowego lokalu i pule stref (29.10.2026) → `notatki/Ustalenia gry.md`, „Limity i czasy”

**Nowa mechanika – czeka na zgodę autora.** Proponowany wiersz tabeli:
> | Rozruch nowego lokalu | w pierwszym tygodniu sprzedaży lokal ma 40% klientów, co tydzień +10 p.p., pełny popyt od 7. tygodnia sprzedaży (każdy kolejny lokal tak samo) |

Proponowany dopisek do opisu popytu (jeśli autor trzyma go w „Prawidłach świata”):
> Pule klientów stref zmniejszone o 10% (B5): jeden lokal średniej drużyny sprzedawał ok. 97 tys. zł
> miesięcznie, po zmianie ok. 85 tys. zł – bliżej typowego kebaba na dobrej ulicy w Lublinie.
