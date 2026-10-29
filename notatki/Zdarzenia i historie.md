[[Prawidła świata]] · [[Elementy mapy]] · `archiwum/Plan implementacji.md`

# Zdarzenia i historie

Dotyczy losowych wypadków (F3b.5), eventów w parkach (F3b.1) i zdarzeń rynkowych. W starym Levasie zdarzenie to jedno zdanie i jeden skutek („Producent mięsa ma awarię chłodni – dostawy wstrzymane”). W Levasie zdarzenia są **historiami w kilku scenach**, w większości zabawnymi.

## Forma: łańcuch scen
- Historia ma **2–4 sceny**, każda w innej rundzie (zwykle w następnej, czasem z przerwą).
- W każdej scenie drużyna wybiera reakcję (2–3 opcje). Wybór zmienia dalszy ciąg historii i skutki – kolejna scena zależy od poprzedniego wyboru.
- Wybór jest częścią decyzji rundy: zakładka **Zdarzenia** (Decyzje – sceny do rozstrzygnięcia, Wyniki – co z tego wyszło). Bez wyboru gra bierze opcję domyślną opisaną w scenie.
- Opcje mogą kosztować czas właściciela, gotówkę albo porcje jedzenia.
- Skutki są prawdziwe i liczy je silnik (gotówka, popyt, rozpoznawalność, ocena, zadowolenie pracowników, kontrole). Opis jest zabawny, liczby – nie.
- Wypadki nadal są rzadkie i nie mogą zniechęcać: strata z jednej historii ma górny limit, ubezpieczenie ją zmniejsza.
- Drużyna ma naraz najwyżej jedną otwartą historię wypadku plus event w parku.
- Zaproszenie do kasyna to zwykła historia, która niczego nie sugeruje ([[Elementy mapy]] → Kasyno).

## Ton
- **Ok. 80% historii jest komicznych:** absurdalne sytuacje i lubelskie smaczki (koziołek z herbu, studenci UMCS i KUL, Zalew Zemborzycki, Krakowskie Przedmieście, juwenalia, Motor Lublin).
- **Ok. 20% jest poważnych** (pożar, kradzież, zalanie, poważna choroba pracownika) – bez żartów, żeby skutki dało się traktować serio.
- Humor nie wyśmiewa prawdziwych osób ani grup; postacie są fikcyjne.

## Przykłady

### Gołąb Zenon (komiczna, 3 sceny)
1. **Runda N.** Do kuchni wleciał gołąb i usiadł na rożnie. Klient nagrywa telefonem.
   a) Gonisz go mopem (1 h właściciela) · b) Nazywasz go Zenon i dajesz frytkę · c) Zamykasz lokal na godzinę (utracona sprzedaż).
2. **Runda N+1 (po b).** Zenon wrócił. Z rodziną. Film „kebab z gołębiem” ma 40 tys. wyświetleń.
   a) Robisz z Zenona maskotkę (+rozpoznawalność, większe ryzyko kontroli) · b) Wzywasz firmę od ptaków (400 zł).
3. **Runda N+3 (po a).** Sanepid pyta o „personel skrzydlaty”. Wynik kontroli zależy od higieny lokalu.

### Pani Halina z drugiego piętra (komiczna, 3 sceny)
1. Sąsiadka z góry skarży się, że jej firanki pachną czosnkiem.
   a) Przepraszasz i dajesz darmowy kebab · b) Kupujesz lepszy okap (sprzęt) · c) Ignorujesz.
2. (po a) Pani Halina przychodzi codziennie po „przeprosiny”. (po c) Przynosi petycję podpisaną przez cały blok i… kota.
3. (po a, jeśli dalej dostaje kebab) Pisze na grupie „Czechów – sąsiedzi” recenzję na 2000 słów: +ocena w strefie. (po c) Skarga do urzędu – kontrola.

### Najazd koziołków (komiczna, 2 sceny)
1. Juwenalia. Czterdziestu studentów w strojach koziołków zamawia po kebabie i chce zapłacić monetami jednogroszowymi.
   a) Przyjmujesz i liczysz (3 h pracownika) · b) Odmawiasz · c) Dajesz zniżkę „za strój”.
2. (po c) Koziołki wracają co tydzień do końca sesji (+popyt studentów w strefie). (po b) Mem „kebab, który nie lubi koziołków” (−ocena).

### Zalanie z góry (poważna, 2 sceny)
1. W nocy pękła rura u sąsiada. Woda na zapleczu, część towaru i sprzęt do sprawdzenia.
   a) Zamykasz lokal na dzień i sprzątasz · b) Działasz dalej na pół gwizdka (ryzyko kontroli).
2. Rozliczenie szkody: z polisą na lokal ubezpieczyciel pokrywa większość, bez polisy płaci drużyna; sąsiad może oddać część kosztów po kilku rundach.

## Dane
Historie są w YAML (`dane/zdarzenia/*.yaml`) z polem `zrodlo`: sceny, opcje, koszty, skutki i przejście do następnej sceny (`nastepna`, `za_ile_rund`, prawdopodobieństwo). Gra sprawdza, że każda ścieżka historii się kończy.
