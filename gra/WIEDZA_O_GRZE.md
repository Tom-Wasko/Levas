# REVAS Klub Fitness – uporządkowana wiedza o grze

Stan na 2026-10-17. Zebrane ze wszystkich przesłanych materiałów, instrukcji „Biuro podróży” i dotychczasowych narzędzi.
Oznaczenia pewności: **✔ potwierdzone** (widać w grze lub przeliczone na danych), **≈ skalibrowane** (dopasowane do danych, z błędem),
**? założenie** (brak danych, przyjęte rozsądnie).

---

## 0. Inwentarz źródeł

Układ folderów po porządkach: `revas_26/README.md`. Stare → nowe ścieżki: `revas_26/PRZENIESIENIA.csv`.
Pliki z gier leżą w folderach rund `rNN_miesiac`. Runda to ta, w której zrobiono screen: zakładki „Wyniki” i karta wyników
w rundzie N pokazują skutki decyzji z rundy N−1.

| Folder / plik (względem `revas_26`) | Gra | Co zawiera |
|---|---|---|
| `materialy/fitness/gra_ATH/` | fitness, rynek ATH, Firma 1, Firma 2 | **najpełniejsza seria**: karta wyników, sprzedaż, dostawcy, HR i sprzęt (wyniki) r3–r9; KPiR styczeń–sierpień (`kpir/`, xlsx + 3 pdf); bank (oferty, lokaty, kredyt) r9; stanowiska, wyposażenie, szkolenia r9; udogodnienia r8; HR – zatrudnienie – decyzje r8–r9 (pracownik na każdym stanowisku, pensje); marketing tradycyjny (decyzje r6–r8, wyniki r7–r9) i internetowy (wyniki r7–r9) |
| `materialy/fitness/gra_A_B_C_Apex_Vela/` | fitness, 5 firm (widok drużyn A i C) | dashboard i biuro rachunkowe r1; oferta r2–r3; HR r2–r4 (kandydaci, wyniki A i C, decyzje C r4); dostawcy r3–r4 (A i C); sprzęt r3–r4 (A i C); udogodnienia r4; sprzedaż r3–r4 (C); karta wyników r3–r4; **KPiR styczeń–marzec drużyn A i C** (`kpir/kpir_MM_miesiac_A/C.xlsx`). Gra skończyła się na rundzie 4 |
| `materialy/fitness/inne/` | fitness, gra nieustalona | 7 profili pracowników, 3 listy kandydatów (xlsx), screeny wymagań usług |
| `materialy/biuro_podrozy/gry/` | biuro podróży, 9 gier | 8 gier: popyt, ceny z rabatem, jakość zasobów (niska/średnia/wysoka) w r3–r5; Fruukulele: karta wyników, sprzedaż, dostawcy r3–r7 |
| `materialy/biuro_podrozy/spisane/` | biuro podróży | `popyt.txt` (436 obserwacji, luty–kwiecień), szczęście, wskaźniki (wynik ekonomiczny), reklama, notatki |
| `materialy/instrukcje/` | biuro podróży | oficjalna instrukcja REVAS „Biuro podróży” (PDF) |
| `dane/uslugi/` | fitness | 12 usług: popyt roczny, cena preferowana, godziny, grupa, sezonowość, sprzęt (ceny 3 jakości), pracownicy, zasoby |
| `dane/dostawcy/` | fitness | ceny 6 dostawców × 4 zasoby × 3 jakości, luty–czerwiec |
| `narzedzia/excel/REVAS 26.xlsx` | fitness | 28 obserwacji popytu (cena, jakość, popyt) z 3 gier + notatki o strategiach |
| `narzedzia/notatniki/` | fitness | Twoje modele: popyt, stanowiska, optymalizator endgame (punkt startowy, nie pewnik) |
| `revas_gra/dane_zrodlowe/popyt_biuro_podrozy.txt` | biuro podróży | `popyt.txt` + 7 brakujących wierszy Realni3 (marzec) uzupełnionych ze screenów |
| `materialy/revas_online/` | fitness + biuro podróży | **zrzut z REVAS online (konto instruktora, 2026-10-18)**: oficjalny podręcznik „Klub fitness”; gra A/B/C/Apex/Vela – widok każdego zespołu r1–r4 (wszystkie zakładki, KPiR, bank, kandydaci, sprzęt na stanowiskach) + panel instruktora (zadowolenie z 6 miejscami); 9 gier biura podróży (zespół referencyjny + próba losowa). Opis: `materialy/revas_online/README.md`, wyniki testu: `POROWNANIE_ABC.md` |

**Gra ATH to inna gra niż A/B/C/Apex/Vela.** W ATH na rynku są tylko ATH, Firma 1 i Firma 2. Mimo to luty w KPiR ATH (zatrudnienie Miś, Mroczkowski i Tarnowska; pensje 16 000 + ZUS = 19 040) zgadza się co do złotówki z ekranem HR drużyny „A”. Najpewniej ta sama osoba grała tak samo w obu grach, a pula kandydatów jest w każdej grze taka sama.

---

## 1. Parametry ogólne ✔

| Parametr | Wartość | Źródło |
|---|---|---|
| Kapitał startowy | 40 000 PLN | dashboard r1, bank r1 |
| Liczba rund | zależy od gry: 10 (drużyna A: „1 / 10”), w grze ATH co najmniej do grudnia (lokaty kończą się w grudniu) → **parametr gry** | dashboard, bank |
| Runda 1 | styczeń, bez sprzedaży, nieoceniana | dashboard, instrukcja |
| Płaca minimalna brutto | 4806 PLN / mies. | dashboard |
| Czas pracy pracownika i sprzętu | 160 h / mies., klub otwarty 9:00–17:00 | dashboard |
| Podatek dochodowy (CIT) | 19% od dodatniego dochodu miesiąca | dashboard, KPiR |
| Składki ZUS pracodawcy | 19% wynagrodzenia brutto (umowa o pracę) | dashboard, KPiR |
| Amortyzacja | sprzęt ≤ 10 000 PLN: 100% w miesiącu zakupu; > 10 000 PLN: 10% (? miesięcznie czy rocznie – w fitness brak takiego sprzętu, więc w praktyce wszystko idzie w koszty od razu) | dashboard, KPiR |
| Koszt utrzymania klubu | 2000 PLN / mies., niezależnie od liczby stanowisk | KPiR, stanowiska r9 |

---

## 2. Rundy i odblokowywanie zakładek

| Runda | Nowe elementy | Pewność |
|---|---|---|
| 1 (styczeń) | nazwa, misja, oferta (3 usługi + prognoza popytu), inwestycje – stanowiska, finanse – bank i biuro rachunkowe | ✔ |
| 2 (luty) | sprzęt, HR – zatrudnienie, dostawcy, sprzedaż; sprzedaje się tylko 3 usługi wybrane w r1 | ✔ |
| 3 (marzec) | karta wyników, wyniki we wszystkich zakładkach, HR – udogodnienia (pierwsze 3: automat z kawą, kuchenka, stojak na rowery) | ✔ |
| limit usług | **łącznie w ofercie najwyżej 3 usługi w rundach 1–2 (tylko Step, TBC, Zumba – w rundzie 2 można dobrać brakujące), potem +3 na rundę narastająco** (r3: 6, r4: 9 …). Apex: 1 → 2 → 6, Vela: 2 → 3 → 5, ATH: 3 → 6 (+5 nowych, −2 usunięte) | ✔ (online) |
| 4 (kwiecień) | udogodnienia +3, inwestycje – wyposażenie (pierwsze 3), karta skumulowana | ✔ (od Ciebie) |
| 5 (maj) | wyposażenie +3; marketing tradycyjny (wg instrukcji biura podróży) | ✔ wyposażenie / ? marketing |
| 6 (czerwiec) | marketing internetowy (wyniki lipca pokazują wydatki z czerwca) | ≈ |
| 7 (lipiec) | HR – szkolenia (wg instrukcji biura podróży) | ? |
| 8 (sierpień) | udogodnienia +3 (razem 9) | ✔ (od Ciebie) |

Karta wyników i zakładki „Wyniki” w rundzie N pokazują skutki decyzji z rundy N−1. Strzałki ◀ ▶ pozwalają oglądać poprzednie rundy.

---

## 3. Oferta i usługi ✔

| Usługa | Kategoria | Prowadzący | Popyt roczny | Cena pref. | Godz./zajęcia | Grupa | Sezonowość (sty → gru) |
|---|---|---|---|---|---|---|---|
| Joga | zajęcia grupowe | instruktor | 4560 | 60 | 1,5 | 10 | 1,3 1,3 1,2 1 1 0,9 0,7 0,7 0,8 0,9 1,1 1,1 |
| Pilates | zajęcia grupowe | instruktor | 5520 | 50 | 1,25 | 10 | 1,2 1,2 1,1 1 1 0,9 0,8 0,7 0,8 0,9 1,2 1,2 |
| TBC | zajęcia grupowe | instruktor | 5640 | 50 | 1,5 | 10 | 1,2 1,2 1,2 1 1 0,9 0,7 0,7 0,8 0,9 1,2 1,2 |
| Step | zajęcia grupowe | instruktor | 4920 | 40 | 1,25 | 10 | 1,3 1,3 1,2 1 1 0,9 0,7 0,7 0,8 0,9 1,1 1,1 |
| TRX | zajęcia grupowe | instruktor | 4080 | 50 | 1,25 | 10 | 1,2 1,2 1,2 1 1 1 0,7 0,7 0,8 1 1,1 1,1 |
| Zumba | zajęcia grupowe | instruktor | 3840 | 45 | 1,25 | 10 | 1,3 1,3 1,2 1,1 1 0,9 0,7 0,7 0,8 0,9 1,1 1 |
| Zdrowy kręgosłup | trening personalny | trener personalny | 492 | 150 | 1,25 | 1 | 1,3 1,3 1,2 1,1 1 0,9 0,7 0,7 0,7 0,8 1,1 1,2 |
| Kobiety po ciąży | trening personalny | trener personalny | 456 | 130 | 1,25 | 1 | 1,1 1 0,9 1,1 1 1 0,9 0,9 0,9 0,9 1,1 1,1 |
| Trening wzmacniający | trening personalny | trener personalny | 540 | 170 | 1,5 | 1 | 1,3 1,3 1,2 1,1 1 0,9 0,7 0,7 0,8 0,9 1,1 1 |
| Bodybuilding | trening siłowy | instruktor | 5400 | 155 | 1 | 15 | 1,1 1,1 1,2 1 1 0,9 0,7 0,7 0,9 1 1,2 1,2 |
| Crossfit | trening siłowy | instruktor | 4560 | 160 | 1,5 | 15 | jak bodybuilding |
| Kettlebell trening | trening siłowy | instruktor | 4920 | 145 | 1 | 15 | jak bodybuilding |

- Recepcja: 0,08 h na klienta dla każdej usługi.
- Prognozowany popyt (decyzja w Ofercie) służy do planowania. W wynikach jest wykres „prognozowany vs popyt”.
- Pensje „rynkowe” prowadzących (z danych usług): instruktor 4840 / 5133 / 5280, trener personalny 4840 / 5042 / 5390, recepcjonista 4895 / 5005 / 5445 (1★ / 2★ / 3★).

---

## 4. Popyt

Model skalibrowany 2026-10-18 na grze ATH i grze A/B/C online (`kalibracja/kalibracja_popytu.py` – parametry cenowe,
222 obserwacje, błąd 4,5%; `kalibracja/kalibracja_online.py` – mnożnik i jakość; test: `POROWNANIE_ABC.md`):

```
popyt = popyt roczny / 12 × sezonowość                       ✔ (step, marzec: 533)
        × 1,56 (mnożnik bazowy firmy 3★) × korekta miesiąca (luty 1,011, marzec 0,963, kwiecień 0,995; dalej ≈)
        × jakość usługi: 0·pracownicy + 0,18·sprzęt + 0,82·zasoby, 3★ = 1,00 / 2★ = 0,697 / 1★ = 0,595
        × exp(−1,413 · (r − 1))                               r = cena po rabacie / cena preferowana
        × exp(−0,867 · (r − r̄))                               r̄ = średnie r firm oferujących usługę
        × n^(−0,282)                                          n = liczba firm oferujących usługę
        × (1 + 0,06 · Σ % klientów oczekujących posiadanego wyposażenia)
        × (1 + wzrost z reklamy tradycyjnej + internetowej)
```

- **Gwiazdki pracowników nie wpływają na popyt ✔ (online):** A i B miały w marcu ten sam popyt na bodybuilding
  (911 = 911) przy tej samej cenie mimo różnych zespołów. Podział wag między sprzęt i zasoby jest słabo wyznaczony
  (w danych idą razem); wagi 0,4/0,4/0,2 dają w odtworzeniu A/B/C błąd 8,4% zamiast 5,2%.
- **Różnica poziomu między grami ≈:** A/B/C chce mnożnika ~1,60, ATH ~1,45 (ATH luty zawyżony o 12%) – możliwy wpływ
  liczby firm w grze (5 vs 3), niepotwierdzony.
- Inne kształty krzywej cenowej (potęgowy, łamany w r = 1, logit z udziałami) nie były lepsze od wykładniczego.
- Drobne niewyjaśnione różnice: A i B przy tych samych cenach kettlebell mają 830 i 861.

- **Konkurencja ✔ (≈):** firmy częściowo dzielą rynek. Przy 2 firmach każda ma 80% popytu monopolisty, przy 3 – 70%, przy 5 – 60%. Liczy się też cena względem konkurentów. Uwzględnienie konkurencji obniżyło błąd modelu z 9,9% do 4,5%.
- **Elastyczność cenowa:** przy niezmienionych cenach konkurentów to około E₁ + E₂·(1 − 1/n), np. 2,0 przy 3 firmach. Wcześniejsze E ≈ 2,5 mieszało cenę z różnicami między firmami.
- **Jakość ✔ (≈):** Vela (2/2,5/2★), Apex (1,33/1,75/1★) i boty ATH (1,5/2/2★) pasują do współczynników z dokładnością 2–3%.
- **Wyposażenie ≈:** po zakupie WiFi, parkingu i terminala (kwiecień) popyt ATH wzrósł o 13–16%.
- **Korekta miesiąca ? (niska pewność):** wspólny wzrost popytu botów latem (lipiec–sierpień +25%). Najpewniej sezonowość była odczytana niedokładnie z małego wykresu. Wartości są w `zalozenia.json`.
- **Boty w grze ATH:** Firma 1 i Firma 2 to boty prowadzącego („bot1”, „bot2” w Twoich notatkach).
- **Popyt zaokrąglany do całych klientów** ✔. Różnice „wzrostu popytu przez reklamę” między usługami (np. 9,8% vs 10,9%) wynikają z zaokrągleń przy małych liczbach klientów.
- **Zużycie zasobów** jest o 0,4–1% większe niż liczba obsłużonych klientów (ATH luty–sierpień). To reklamacje (usługa wykonana ponownie). Silnik: prawdopodobieństwo = ryzyko reklamacji pracownika × 0,15 ≈ (odtworzenie ATH: przy samym ryzyku zużycie było o 3,6% za duże).

**Dane do kalibracji:**
- fitness: `dane_zrodlowe/obserwacje_popytu_fitness.json` (z PDF-ów), `narzedzia/excel/REVAS 26.xlsx` (28 obserwacji),
- biuro podróży: `dane_zrodlowe/popyt_biuro_podrozy.txt` (443 obserwacje).

**Uwaga do `popyt.txt`:** kolumny `jakosc_niska/srednia/wysoka` to **udział drużyny w rynku zasobów danej jakości** (z wykresów „Jakość zasobów”), a nie miks jakości drużyny. Np. TODOS: 0 / 0 / 0,97 oznacza, że kupił 97% wszystkich zasobów ★★★ w grze. Miks jakości drużyny trzeba liczyć z liczb sztuk na wykresach (są na screenach). Do poprawienia w Etapie 0.

---

## 5. Inwestycje

### 5.1 Stanowiska ✔
- **Godziny prowadzących i sprzętu są wspólne dla całego klubu ✔ (online)** – sprzęt kupuje się na stanowisko, ale nie musi
  stać na stanowisku prowadzącego. Apex w lutym prowadził Step, choć zestaw stepów stał na nieobsadzonym stanowisku;
  Vela w marcu sprzedawała bodybuilding ze sprzętem na pustych stanowiskach. Obłożenie rodzaju sprzętu = godziny zajęć /
  (liczba sztuk × 160 h), wykorzystanie zawodu = godziny wszystkich usług tego zawodu / (osoby × 160 h) – co do 0,1 pkt proc.
  Silnik: `operacje.model_stanowisk` = `pula`.
- Osobne stanowiska dla **instruktorów/trenerów** i dla **recepcjonistów**. **Działają już w rundzie zakupu** (od Ciebie; zgodne z KPiR: zakup w styczniu, zatrudnienie w lutym, zakup w marcu, zatrudnienie w marcu).
- Koszt uruchomienia (pakiety, jednakowe dla obu typów, ten sam cennik od stycznia do września):

| Liczba stanowisk | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Koszt | 1000 | 1800 | 2200 | 3000 | 4000 |

- KPiR: styczeń 2200 + 2200 (3 + 3), luty 2200 (3 instruktorskie), marzec 4000 + 4000 (5 + 5). Razem 11 stanowisk instruktorów, tyle ile na ekranie HR drużyny A w kwietniu.
- Brak widocznego limitu liczby stanowisk (ATH w r9: 19 instruktorskich, 11 recepcji). Wcześniejsze „11 / 9” w planie było liczbą posiadanych stanowisk, nie limitem.
- ? Jeden zakup na typ na rundę (maks. 5 naraz).

### 5.2 Sprzęt ✔ (ceny) / ? (utrzymanie)
- Kupowany na konkretne stanowisko, w jakości 1–3 (ceny w `uslugi/zasoby/*.json` – zgodne z ekranem gry). Zapotrzebowanie 100% (sprzęt zajęty przez cały czas zajęć).
- Sprzęt recepcji (★/★★/★★★): biurko 180/220/260, drukarka 250/300/350, fotel 150/180/210, telefon 200/300/400, zestaw komputerowy 2800/3200/3600.
- **Koszt utrzymania ✔ (online):** tylko część sprzętu 1★: Atlas 35 PLN, **zestaw ciężarków 20 PLN, zestaw do nagłośnienia
  20 PLN** (Apex: 2 × 20 + 20 = 60 PLN/mies. = KPiR). Wszystkie pozycje 2★ i 3★ oraz pozostałe 1★ widoczne w grze A/B/C
  (telefon, maty, piłki, stepy) – 0 PLN.
- **Sprzedaż sprzętu ✔ (online):** 50% ceny zakupu **ucięte do 2 cyfr znaczących**: stepy 3500 → 1700, pomost 5500 → 2700,
  atlas 2★ 2500 → 1200, box 350 → 170, box 2★ 250 → 120, komputer 3600 → 1800, nagłośnienie 1200 → 600.
- Obłożenie sprzętu = godziny zajęć usług używających go na stanowisku / 160 h ✔.
- Wykres „Liczba i jakość sprzętów” podaje liczbę sztuk niskiej / średniej / wysokiej jakości na całym rynku i liczbę sztuk każdej firmy. W grze ATH cały sprzęt Firmy 1 i Firmy 2 jest średniej jakości (2★) we wszystkich miesiącach ✔ (np. luty: 0 / 40 / 12, ATH 12 sztuk 3★). Wykres „Liczba pracowników” podaje liczbę osób w zawodzie (bez gwiazdek): boty ATH w lutym 1 instruktor + 1 recepcjonista, w kwietniu Firma 1: 1 + 2, Firma 2: 1 + 1.

### 5.3 Wyposażenie dla klientów (od r4: 3 pozycje, od r5: kolejne 3) ✔
| Pozycja | % klientów oczekujących | Cena zakupu | Utrzymanie / mies. |
|---|---|---|---|
| Darmowe WiFi | 95% | ≈ 200 (sprzedaż 100) | 20 |
| Miejsca parkingowe | 90% | ≈ 0 (sprzedaż 0) ? | 1500 |
| Terminal płatniczy | 80% | ≈ 0 (sprzedaż 0) ? | 100 |
| Automat z napojami | 75% | ≈ 2000 (sprzedaż 1000) | 200 |
| Fotele w strefie klienta | 60% | ≈ 2500 (sprzedaż 1250) | 0 |
| Telewizor w strefie klienta | 30% | 2300 | 10 |

Sprawdzenie: utrzymanie posiadanych 20 + 1500 + 100 + 200 + 0 = 1820 PLN = wartość na ekranie ✔. Cena zakupu = 2 × cena sprzedaży (jak przy udogodnieniach).

---

## 6. HR

### 6.1 Kandydaci ✔
- Pola: imię i nazwisko, doświadczenie 1–3★, zawód, preferowane wynagrodzenie, koszt rekrutacji, koszt odprawy, zadowolenie klientów (%), ryzyko reklamacji (%), wiek.
- Pula na rynku (lista xlsx, po zatrudnieniach drużyny): instruktorzy 6, recepcjoniści 5–6, trenerzy personalni 6. Do tego zatrudnieni wcześniej: Miś (instr. 3★), Mroczkowski (instr. 3★), Rak (instr. 2★), Prus (instr. 2★), Nowak (instr. 2★), Tarnowska (rec. 3★), Tytus (rec. 3★), Małka (rec. 2★), Woś (rec. 1★), Szymański (tr. pers. 3★). Kandydaci 3★ są rzadcy. **Każda firma widzi pełną listę ✔** – w grze A/B/C drużyny A i C zatrudniły w lutym te same osoby (Miś, Tarnowska), a Mroczkowskiego A w lutym, C w marcu (KPiR obu drużyn). Silnik: kandydat znika tylko z listy firmy, która go zatrudniła.
- Preferowane pensje 4785–5500. Koszt rekrutacji 200–700. **Odprawa = 30 / 35 / 40 / 50 / 60% preferowanej pensji** ✔ (np. 2640 = 50% × 5280, 1436 = 30% × 4785, 2970 = 60% × 4950).
- Te same osoby mają w różnych grach nieco inne parametry (np. Miś: pref. 5280 vs 5390) → przy generowaniu nowej gry losujemy parametry z niewielkim rozrzutem ≈.

### 6.2 Zatrudnienie ✔
- Pensja ≥ 4806 brutto. Umowa o pracę: + 19% ZUS i wyższa opłata kadrowa. Umowa zlecenie: bez ZUS, niższa opłata kadrowa, niższe zadowolenie pracownika.
- Nowo zatrudniony w bieżącej rundzie: przycisk „Anuluj zatrudnienie”. Zatrudniony wcześniej: zmiana pensji, **premia** (jednorazowa), zmiana umowy, „Zwolnij” (odprawa).
- KPiR: koszt zatrudnienia w miesiącu zatrudnienia; wynagrodzenia i ZUS miesięcznie (luty: 5300 + 5300 + 5400 = 16 000; ZUS 3040 = 19%).
- Wykorzystanie czasu pracownika = godziny pracy / 160 h ✔ (instruktor 80,3%, recepcja 47,2% – przeliczone dokładnie).

### 6.3 Zadowolenie pracowników ✔ (skalibrowane, błąd 0,0006)
```
0,9464 + 0,3162 · (płaca / preferowana − 1)          płaca = średnia (pensja + premia) / preferowana
       + 0,0163 · (średnie gwiazdki całego sprzętu − 3)
       − 0,0115 · udział umów zlecenie
       + 0,0009 · Σ % pracowników oczekujących posiadanych udogodnień
       + 0,0513 · Σ % oczekujących szkoleń w tym miesiącu
```
- 17 kart (gra A/B/C online z 6 miejscami + ATH), maks. błąd 0,0024. Przykład: A, B, ATH w lutym (etat, płaca ≈ pref.,
  sprzęt 3★) → 0,9470 / 0,9471 / 0,9470; C (wszyscy na zleceniu) 0,9349.
- **Udogodnienia prawie nie działają** (A, B, C w marcu pasują do wzoru bez nich co do 0,001); zmiany zatrudnienia – bez efektu.
- Dane biura podróży (`szczęście pracowników.xlsx`): te same warunki dają te same wartości w różnych grach (funkcja deterministyczna).

### 6.4 Udogodnienia dla pracowników (r3: 3, r4: +3, r8: +3) ✔
| Udogodnienie | % pracowników oczekujących | Cena zakupu | Utrzymanie / mies. |
|---|---|---|---|
| Automat z kawą fair trade | 95% | 2500 | 200 |
| Klimatyzacja | 80% | 3000 | 100 |
| Kuchenka mikrofalowa | 60% | 202 | 5 |
| Stojak na rowery | 40% | 1000 | 0 |
| Roślinność do biura | 15% | 1100 | 0 |
| Fotel do masażu | 30% | 2500 | **10** (online) |
| Głośnik Bluetooth | 90% | 75 | 0 |
| Lodówka z napojami | 70% | 1000 | 0 |
| Strefa relaksu | 22% | 4000 | 0 |

Sprzedaż = 50% ceny zakupu ✔ (automat 1250, kuchenka 101). Utrzymanie płatne już w miesiącu zakupu ✔ (KPiR marzec: 205 = 200 + 5).
Kolejność odblokowania ✔ (online): r3 – automat z kawą, kuchenka, stojak na rowery (B kupił stojak w marcu);
r4 – klimatyzacja, fotel do masażu, roślinność; r8 – głośnik, lodówka, strefa relaksu.

### 6.5 Szkolenia ✔ (oferta) / ≈ (efekt)
Trzy firmy szkoleniowe: Edu for Fitness (90% zadowolonych klientów), Gym Masters (83%), Akademia Zdrowia (80%).
12 szkoleń z % oczekujących pracowników i cenami w każdej firmie (`dane/katalog.json`). Przykłady: Creative yoga (90%,
2100–2500 PLN), Crossfit master (90%), Trening metaboliczny (89%).
KPiR ATH: lipiec „Szkolenie w firmie: Edu for fitness” 4800 PLN (trening metaboliczny 2300 + stretching 2500), sierpień 3300 PLN
(crossfit master 1600 + fit with ball 1700). Zadowolenie pracowników ATH i botów wzrosło w tych miesiącach o 0,07 i nie
rosło dalej. Efekt działa więc w miesiącu szkolenia i zależy od Σ % oczekujących.

---

## 7. Dostawcy i magazyn

### 7.1 Zasoby ✔
| Zasób | Zużycie na klienta | Opakowanie | Usługi |
|---|---|---|---|
| Napój izotoniczny | 1 szt. | 24 szt. | wszystkie poza „kobiety po ciąży” |
| Woda | 1 szt. | 20 szt. | tylko „kobiety po ciąży” |
| Płyn do dezynfekcji | 5 ml | 5 l | wszystkie |
| Ręcznik papierowy | 5 szt. | 1000 szt. | wszystkie |

Zużycie liczone w ułamkach opakowań. Niezużyte zostaje w magazynie na kolejny miesiąc ✔ (85,833 op. napoju = 2060 klientów; magazyn na koniec marca = na początek kwietnia).
Wartość magazynu gra liczy metodą **FIFO** ✔ (ATH lipiec: płyn 4,283 op. × 58 + 15 op. × 56 = 1088,41). Silnik liczy średnią cenę – różnica dotyczy tylko wyświetlanej wartości, nie KPiR.

### 7.2 Dostawcy i ceny
- Luty–marzec: FullService, InterShop, OfficeShop. Od kwietnia dochodzą Bis, DealTag, Traftixx ✔.
- U każdego dostawcy: koszt zwrotu 10%, koszt magazynowania 50 PLN, wybór „zwrot zasobów nadmiarowych”. W KPiR jest jedna pozycja „Koszt magazynowania 50” na miesiąc, mimo zakupów u 2 dostawców ≈.
- **Zwrot ✔ (online, Vela luty):** wracają tylko **całe nienaruszone opakowania** z zakupów tej rundy (kupione 3, zużyte 0,1 →
  zwrot 2). Pozycja „Zakup zasobu od dostawcy” maleje o ich wartość (205,32 − 68 = 137,32), osobna pozycja „Koszt zwrotu
  zasobów do dostawcy” = 10% tej wartości, resztka w magazynie nadal kosztuje 50 PLN magazynowania.
- **Analiza zmian cen** (`kalibracja/analiza_cen_dostawcow.py`, 208 zmian, luty–czerwiec):
  - ceny **wahają się wokół stałej bazy**, a nie błądzą losowo: autokorelacja kolejnych zmian −0,37, brak trendu (średni indeks 0,99–1,00 w każdym miesiącu),
  - baza ≈ średnia cena z danych usług (odchylenie średnio −0,5%, std 5,7%). Dostawcy mają małe stałe przesunięcia (FullService ≈ −3%, InterShop ≈ +1%),
  - zmiana miesiąc do miesiąca: mediana 2,7%, 90% zmian ≤ 6,7%, maks. 17%. Około 1/4 cen się nie zmienia,
  - **pułapka:** Bis ma napój i wodę 2★/3★ za 1,8–2,4 × średnia (lekko taniejące). Reszta Bis normalnie,
  - format cen: płyn, ręcznik i woda w pełnych złotych; napój zwykle z groszami.
- **Model do gry:** cena(m) = baza(zasób, jakość) × (1 + przesunięcie dostawcy) × (1 + ε_m), ε_m losowe z rozkładu dopasowanego do powyższego (ziarno gry). Dla miesięcy z danymi (luty–czerwiec) używamy prawdziwych cen, lipiec–grudzień generujemy (danych z tych miesięcy jeszcze nie ma).

---

## 8. Sprzedaż ✔
- Cena i rabat dla każdej usługi. Klient płaci cenę po rabacie (np. Joga 41 797 PLN w marcu – przychód zbiorczy na usługę).
- Wyniki: zestawienie popytu (wszystkie firmy), prognozowany vs popyt, sprzedaż vs utracona sprzedaż, udział usług w sprzedaży, ceny usług z rabatem (wszystkie firmy).
- Utracona sprzedaż, gdy zabraknie czasu prowadzącego, sprzętu, recepcji albo zasobów.
- **Kolejność ✔:** prowadzący i sprzęt → zużycie zasobów → recepcja. Klienci utraceni przez brak recepcji zużyli już zasoby (ATH luty: utracone 85 TBC, zużycie = popyt 2084 + reklamacje; maj: zużycie napoju 10 170 przy sprzedaży 7946).
- **Podział braku mocy między usługi ?:** nie jest proporcjonalny. Luty: przy braku recepcji obcięto tylko TBC; kwiecień (brak płynu): najmniej obcięto drogie usługi (bodybuilding, kettlebell 78–80%, joga, TBC, zumba po 460 klientów); maj: trener personalny 100% mimo braku recepcji. Silnik dzieli proporcjonalnie (główne źródło różnic w lutym, kwietniu i maju).

---

## 9. Finanse

### 9.1 KPiR ✔ (przeliczone na 3 miesiącach)
- Pozycje: opłata za konto, uruchomienie stanowisk, zakup sprzętu i udogodnień (w całości w koszty), koszt zatrudnienia, wynagrodzenia, ZUS pracodawcy, sprzedaż usług (osobno każda), zakup zasobów od dostawcy (osobno każdy), utrzymanie klubu, koszt magazynowania, koszt biura rachunkowego, obsługa kadrowo-płacowa, utrzymanie udogodnień i benefitów.
- **Biuro rachunkowe:** opłata za księgowanie × liczba dokumentów, gdzie liczba dokumentów = liczba pozycji KPiR bez pozycji „obsługa kadrowo-płacowa” (styczeń 5 × 1,20 = 6; luty 27 × 1,20 = 32,40; marzec 50 × 1,20 = 60). Plus opłata kadrowa za każdego pracownika (luty 3 × 32 = 96; marzec 7 × 32 = 224 – wszyscy na etacie, biuro PLUS).
- **Premia ✔ (online):** osobna pozycja na pracownika „Bonus dla pracownika: <osoba>” w kolumnie wynagrodzeń, **bez ZUS**
  (A, marzec: 3 × 500, ZUS 9 576 = 19% samych pensji 50 400); każda to osobny dokument dla biura rachunkowego.
- **Kolejność w historii rachunku ✔ (online):** koszty miesiąca są księgowane przed przychodami ze sprzedaży – saldo chwilowo
  spada poniżej zera, a mimo to kredyt odnawialny nie powstaje (zgodnie z „jednocześnie” w rozdz. 9.3).
- **Podatek:** 19% dochodu miesiąca (luty 33 306,10 → 6328,16; marzec 376 231,81 → 71 484). Przy stracie 0. Strata ze stycznia nie pomniejszyła podatku w lutym (brak rozliczania strat) ✔.

### 9.2 Biura rachunkowe ✔
| Biuro | Księgowanie | Etat | Umowa cywilnoprawna |
|---|---|---|---|
| Prefix | 1,20 | 33 | 10 |
| Plus | 1,20 | 32 | 11 |
| Seven | 1,10 | 37 | 14 |
| Rachmistrz | 1,30 | 29 | 9 |
| Krak | 1,00 | 32 | 12 |
| Petra | 1,50 | 28 | 5 |

Źródło: `materialy/fitness/gra_ATH/r09_wrzesien/finanse_biuro_rachunkowe.png` (6 biur; zrzut z gry A_B_C pokazywał tylko 3 pierwsze). ATH: Plus do marca, od kwietnia Krak (KPiR: 1,00 za dokument, 12 za zlecenie).

### 9.3 Bank ✔ (oferty z r9)
| Bank | Konto | Karta | Lokata | Kredyt odnawialny | Kredyt |
|---|---|---|---|---|---|
| MBP Bank | 10 | 5 | 2% | 7% | 5% |
| Beauty Bank | 5 | 5 | 3% | 6% | 7% |
| Euro Biznes Bank | 15 | 0 | 5% | 5% | 5% |
| Gaz Bank | 20 | 0 | 7% | 12% | 10% |
| IT Bank | 5 | 15 | 1% | 12% | 12% |
| Brand Bank | 10 | 2 | 1% | 10% | 11% |

- Oprocentowanie roczne. **Lokata:** odsetki proste naliczane miesięcznie ✔ (215 600 × 7% × 4/12 = 5030,67; 275 572 × 7% × 3/12 = 4822,51; 500 000 × 7% × 1/12 = 2916,67). Okres 1–N miesięcy, kończy się najpóźniej w grudniu. Zerwanie = utrata odsetek.
- Kredyt: rata miesięczna. Kredyt odnawialny uruchamiany automatycznie przy braku gotówki i spłacany z nadwyżki w kolejnych miesiącach. Szczegóły (maks. kwota, okresy) ?.
- ✔ (użytkownik) W oficjalnej grze przychody i wydatki miesiąca dzieją się jednocześnie – kredyt odnawialny pobierany tylko na niedobór (wydatki > saldo + przychody). W grze lokalnej opcja `kredyt_odnawialny` w konfiguracji: `jednoczesnie` (domyślnie, jak w oryginale) albo `na_biezaco` (zakupy z decyzji opłacane przed wpływem przychodów).
- W styczniu w KPiR opłata za konto = 15 PLN (bank wybrany w r1).
- ✔ (użytkownik) Dostępność banków: od rundy 1 MBP Bank, Beauty Bank, Euro Biznes Bank; pozostałe od rundy 4 (`od_rundy` w dane/katalog.json).

### Dostępność marketingu (✔ użytkownik)
- Tradycyjny: runda 5 – Billboard/Ulotki i Prasa; runda 6 – Radio; runda 7 – Telewizja.
- Internetowy: runda 6 – strona www, portal branżowy, Panorama Firm, fora, portal lokalny + Facebook; runda 7 – YouTube, Instagram, aplikacja mobilna.

---

## 10. Marketing (gra ATH) ✔ dane / ✔ model (eksperymenty rund 9–12, `WYNIKI_EKSPERYMENTOW_ATH.md`)

### 10.1 Tradycyjny – oferta
| Kategoria | Medium (zasięg, cena emisji, zniżki) |
|---|---|
| Billboard / ulotki | Ulotki 75%, 220 (4–10: 15%, 11+: 30%) · Ekrany LED 50%, 700 (4–10: 20%, 11+: 30%) · Billboard 45%, 500 (4–10: 15%, 11+: 30%) |
| Prasa | Super Fit 60%, 750 (6–13: 20%, 14+: 30%) · Głos Miasta 55%, 650 (6–13: 15%, 14+: 25%) · Newsy Miasta 50%, 500 (6–13: 10%, 14+: 20%) |
| Radio | Radio Fakty 70%, 400 (10–20: 20%, 21+: 30%) · Fit FM 65%, 300 (10–20: 15%, 21+: 20%) · Radio City 62%, 200 (10–20: 10%, 21+: 20%) |
| Telewizja | Fitness TV 72%, 30 000 (3–6: 20%, 7+: 30%) · Fit TV 70%, 25 000 (3–6: 10%, 7+: 20%) · Yoga TV 35%, 20 000 (2–4: 15%, 5+: 25%) |

### 10.2 Efekt (decyzje → wyniki następnej rundy)
| Decyzje (miesiąc) | Wydatki | Emisje (ATH) | Wzrost popytu (wszystkie usługi) |
|---|---|---|---|
| czerwiec | 46 375 | ulotki 20, LED 11, billboard 11, prasa 3×14, radio 3×21 | **+49,4%** |
| lipiec | 215 825 | jak wyżej, radio 21/10/10, TV 3/3/2 | **+65,0%** |
| sierpień | 48 875 | ulotki 30, LED 11, prasa 14 + 6, radio 10, TV (Fit TV) 1 | **+28,7%** |

Efekt jest jednakowym % wzrostu popytu dla wszystkich usług ✔. Sama kwota go nie wyjaśnia (46 tys. → +49%, 49 tys. → +29%).

Dalsze miesiące (eksperymenty): maj (ulotki 20, LED 11, billboard 11, prasa 20/14/14) +27,6%; wrzesień – brak reklamy
**0,0%**; październik – **60 ulotek +4,1%**; listopad – 20 ulotek +3,5%; grudzień – **2 × Fitness TV +6,8%**.

**Model ✔ (8 miesięcy, błąd 0,5 pkt proc.):** każde medium nasyca się osobno:
wzrost = Σ_media A_kategorii · zasięg · (1 − e^(−0,265 · emisje)), A: billboard/ulotki 5,1%, prasa 11,9%, radio 11,0%,
telewizja 18,8%. Ok. 10 emisji = ponad 90% efektu medium (pasuje do progów zniżek). Reklama działa tylko w miesiącu
emisji. Reklama ATH nie zabierała klientów botom (rynek rośnie). ~~Dawny model liniowy~~ (0,0055·Σ, TV × 8) przewidywał
dla 60 ulotek +24,8%.

### 10.3 Internetowy
9 narzędzi. Koszty z KPiR ATH (uruchomienie / utrzymanie miesięcznie): strona WWW 2500/250, portal branżowy 3000/200,
Panorama Firm 3500/250, fora 100/500, portal lokalny 500/700, YouTube 500/750, Facebook 1200/1000. Instagram i aplikacja
mobilna – nieznane (założenie). Wyniki ATH:

| Miesiąc | Narzędzia | Wzrost popytu |
|---|---|---|
| czerwiec | 5 uruchomionych w czerwcu | +12,6% |
| lipiec | + YouTube | +9,8% |
| sierpień | + Facebook | +7,5% |

| wrzesień | wszystkie wyłączone | **0,00%** |
| październik | sam Instagram (konkurenci 10 narzędzi) | +0,14% |
| listopad | Instagram (konkurenci 12) | +0,09% |
| grudzień | Facebook ponownie + Instagram (konkurenci 14) | +0,56% |

**Model ✔ (7 miesięcy, błąd 0,24 pkt proc.):** wzrost = 0,22 · (narzędzia firmy / aktywne narzędzia wszystkich firm)^1,59.
Wyłączenie zeruje efekt od razu; ~~„wygasanie × 0,55”~~ to w rzeczywistości dokładanie narzędzi przez konkurentów.
Instagram i Facebook: 1 200 PLN + 1 000 PLN/mies. Utrzymanie płaci się co miesiąc, także w miesiącu uruchomienia.

---

## 11. Karta wyników

| Wskaźnik | Co wiemy | Pewność |
|---|---|---|
| Wynik działalności | iloczyn 5 wskaźników; 0 przy ujemnym wyniku ekonomicznym; firmy bez działalności „niesklasyfikowane” | ✔ (A, r3: 1,242 × 0,947 × 1,050 × 1,369 × 1 = 1,691) |
| Wynik ekonomiczny | dochód netto / 20 000 | ✔ (7/7 rund ATH, co do 0,001) |
| Zadowolenie pracowników | wzór w rozdz. 6.3; błąd 0,0006 na 17 kartach (A/B/C online z 6 miejscami + ATH) | ✔ |
| Zadowolenie klientów | 1,0775 + 0,2035·ln(min(usługi, 6)) − 0,2549·(cena / średnia cena rynku, ważona klientami) − 0,1213·(udział utraconej sprzedaży **w poprzednim miesiącu**) + 0,0082·Σ% wyposażenia; LOO 0,024. Jakość i reklamacje bez wyraźnego efektu. Vela: −93% sprzedaży w lutym → spadek zadowolenia w marcu | ≈ (średnia) |
| Rozwój firmy | 0,308·ln(1 + majątek/10 tys.) + 1,192·inwestycje/majątek + 0,031·przyrost (bez wygładzania); błąd 0,11. W lutym wynik zależy głównie od sumy usług i pracowników (A, ATH, Apex – po 6 → 1,36–1,37), ale reguła nie przenosi się na marzec | ≈ (niska) |
| Wskaźnik zadłużenia | 1 bez kredytu; z kredytem 0,2–0,6 (Fruukulele r7); wzór z kredytem – założenie | ≈ |
| Karta skumulowana | średnia kart ze wszystkich rund (od r4) | ✔ instrukcja |

---

## 12. Losowość

| Element | Wniosek |
|---|---|
| Popyt | deterministyczny (zaokrąglany do całych klientów); resztę rozrzutu ma wyjaśnić Etap 0 (konkurencja, zadowolenie) |
| Zadowolenie pracowników | deterministyczne (te same warunki → ta sama wartość w różnych grach) |
| Ceny dostawców | losowe wahania wokół stałej bazy (p. 7.2) |
| Parametry kandydatów | rozrzut między grami (pref. pensja, rekrutacja, % klientów, ryzyko) |
| Reklamacje | losowe z prawdopodobieństwem = ryzyko reklamacji pracownika (instrukcja) |

---

## 13. Otwarte pytania

0. **Po teście online (2026-10-18, `POROWNANIE_ABC.md`):** rozwój firmy (niska pewność), różnica poziomu popytu między
   grami (liczba firm?), utracona sprzedaż Apex w marcu bez widocznej przyczyny, podział braku zasobów między usługi (Vela,
   marzec), drobne różnice popytu przy identycznych decyzjach (A/B kettlebell). Reklama w biurze podróży nasyca się
   (`kalibracja/reklama_biuro.py`) – do sprawdzenia w fitness, gdy gra A/B/C dojdzie do reklamy.
1. ~~Wzory zadowolenia klientów i pracowników~~ – skalibrowane na danych online (rozdz. 6.3, 11).
2. Korekta sezonowości (lato) – możliwy błąd odczytu wykresu sezonowości.
3. Model reklamy – tylko 4 + 3 punkty.
4. ~~Koszty utrzymania sprzętu~~ – 1★: Atlas 35, ciężarki 20, nagłośnienie 20; reszta widoczna w grze 0 (rozdz. 5.2).
5. Kredyt: limity i okresy; oprocentowanie kredytu odnawialnego od salda.
6. Kolejność obsługi klientów przy braku mocy przerobowych (przyjęto: proporcjonalnie).
7. Koszt magazynowania: 50 PLN za miesiąc ogółem (tak w KPiR ATH przy 2 dostawcach).
8. ~~Biura rachunkowe zmieniają oferty w trakcie gry~~ – wyjaśnione: biur jest 6, ATH od kwietnia przeszedł z Plus do Krak (rozdz. 9.2).
9. Podział braku mocy (recepcja, zasoby, trener) między usługi – patrz rozdz. 8.
10. Zrzut banku z rundy 1 pokazuje Gaz Bank, ale opłata za konto w KPiR styczeń–kwiecień = 15 PLN (Euro Biznes Bank), od maja 20 PLN (Gaz Bank). Najpewniej ekran pokazuje bieżący bank przy przeglądaniu starej rundy.

## 14. Odtworzenie gry ATH (2026-10-18)

Skrypt `kalibracja/odtworzenie_ath.py` przepuszcza odtworzone decyzje ATH (`dane_zrodlowe/decyzje_ath.json`) przez silnik i porównuje wyniki z oryginałem. Wyniki i lista brakujących danych: `POROWNANIE_ATH.md`.

## 15. Test na grze A/B/C online i kalibracja (2026-10-18)

Silnik odtworzył grę A / B / C / Apex Fitness / Vela Studio z kompletem decyzji wszystkich zespołów (zrzut z REVAS online).
Znaleziono i poprawiono 6 różnic w mechanice (pule godzin, limit usług, premia bez ZUS, zwroty całych opakowań,
utrzymanie sprzętu 1★ i cena sprzedaży, rundy udogodnień), a wzory zadowolenia i popytu skalibrowano na nowo.
Przy prawdziwym popycie dochód netto zgadza się co do złotówki w 4 z 10 miesięcy firm (pozostałe: różnice w sprzedaży),
wykorzystanie pracowników w 16 z 22 pozycji co do 0,1 pkt proc. Pełna symulacja: popyt ±5,2%, zadowolenie pracowników
±0,001, klientów ±0,009. Szczegóły i lista tego, co nadal odbiega: `POROWNANIE_ABC.md`.

## 16. Eksperymenty na grze ATH, rundy 9–12 (2026-10-18)

Pełny opis: `WYNIKI_EKSPERYMENTOW_ATH.md`. W skrócie:
- **Reklama** – rozdz. 10 (nasycenie w medium; internet = udział w narzędziach rynku; brak przeniesienia na kolejny miesiąc).
- **Popyt** – krzywa cenowa potęgowa: popyt ∝ r^(−1,0) · e^(−1,0·(r − r̄)) · n^(−0,28) (błąd 6,3% na 320 obserwacjach,
  ogony 1,2–2,0 bez odchyleń; silnik nadal używa postaci wykładniczej – do zmiany). Konkurencja działa przez ceny względne
  i liczbę firm, nie przez udział w atrakcyjności.
- **Prognoza popytu nie wpływa na popyt** (1,012 ± 0,028). **Gwiazdki trenerów nie wpływają na popyt** (1,02 ± 0,04).
  Sprzęt 1★: −5…−11%.
- **Wyposażenie: +0,095/%** w popycie, **bez wpływu na zadowolenie klientów**.
- **Wskaźnik zadłużenia = 1 − dług / (majątek + skumulowany dochód netto + dług)**; kredyt: odsetki = kwota × stopa / 12.
- **Podział braku zasobów:** najpierw usługi siłowe (kettlebell, bodybuilding, crossfit 66–75% popytu), najmniej joga,
  TBC, step (29–38%) – niezależnie od ceny (kwiecień i grudzień ATH).
- **Zadowolenie pracowników** – wzór z rozdz. 6.3 przewidział wrzesień–grudzień (premia działa jak pensja).
- **Sezonowość IX–XII:** 1,20 / 1,18 / 1,00 / 0,97.
- **Hipoteza (średnia pewność):** po miesiącu z dużą utraconą sprzedażą część klientów nie wraca (ATH φ ≈ 0,37, Vela mniej;
  w silniku 0,2).
- Nierozstrzygnięte: rabat (nie zapisał się), jakość wody, sprzęt recepcji w popycie.

## 17. Analiza od zera wszystkich danych fitness (2026-10-18) – obowiązuje zamiast wcześniejszych wniosków

Pełny opis i wykresy: `SPRAWOZDANIE_ODTWORZENIA.html` (artefakt), skrypty: `kalibracja/dane_fitness.py`, `analiza_od_nowa.py`,
`ath_jesien.py`, `porownanie_przed_po.py`. Nowy zbiór: 361 obserwacji popytu (ATH luty–grudzień z botami + A/B/C), 43 karty
wyników; po raz pierwszy z wyposażeniem, udogodnieniami, reklamą, narzędziami i jakością zasobów botów. Wybór wzorów:
walidacja krzyżowa (prognoza danych pominiętych przy dopasowaniu).

| Mechanizm | Obowiązuje (zalozenia.json) | Zmiana wobec rozdz. 4, 10, 11, 16 |
|---|---|---|
| Cena w popycie | r^−1,096 · e^(−1,004·(r − r̄)) · n^−0,247, M = 1,498 | postać potęgowa zamiast e^(−1,41(r−1)) |
| Sezonowość | z instrukcji; korekta luty–październik 0,90–1,00, listopad 0,808, grudzień 0,796 | **dawne +20% we IX–X było wyposażeniem botów** |
| Utrata klientów po brakach | brak (0) | **hipoteza z rozdz. 16 odrzucona** – pogarsza prognozy |
| Różnica między grami | brak | dawne „+12% w lutym ATH” znika po uwzględnieniu jakości i botów |
| Jakość | 0,41·C(sprzęt★) + 0,59·C(zasoby★); C(2★) = 0,654, C(1★) = 0,616 | wagi z 0,18/0,82 |
| Wyposażenie | +0,073 na 100% oczekujących | z 0,095 |
| Reklama tradycyjna | Σ A_kat · zasięg · ln(1 + 2,2·emisje) | ln zamiast nasycenia wykładniczego (lepsza prognoza: 3,0 wobec 4,3 pkt proc.) |
| Reklama internetowa | 0,19 · (n / (n + 0,4·(N − n)))^2,76 | narzędzia konkurentów ważą 0,4 |
| Raport reklamy | mnożnik popytu (współczynnik 1,005) | potwierdzone |
| Braki zasobów | obsłużeni ∝ popyt · godziny^−1,55 | „usługi siłowe najpierw” = krótsze zajęcia |
| Zadowolenie klientów | 0,849 + 0,177·ln(min(usługi, 6)) − 0,193·cena/średnia rynku + 0,228·jakość − 0,105·utracona poprz. | + jakość (boty) |
| Zadowolenie pracowników | szkolenie w miesiącu = włącznik +0,0755 | zamiast proporcji objętych szkoleniem |
| Rozwój firmy | 0,535 + 0,106·ln(1 + M/10 000) + 0,339·(zakupy − wartość sprzedanego)/max(M poprz., 10 000) | majątek pomniejszany o sprzedany sprzęt |
| Lokaty | koniec z końcem miesiąca m + n − 1; zakładane na początku miesiąca przed zakupami | nowe (KPiR i historia rachunku ATH) |

Gra lokalna na przeszłych grach (pełna symulacja, przed → po): popyt ATH 10,6% → 6,0%, boty 7,3/7,1% → 4,6/5,2%,
sprzedaż ATH 20,2% → 7,9%, zadowolenie klientów ATH 0,062 → 0,020, rozwój 0,124 → 0,075; gra A/B/C: popyt 5,6% → 5,8%,
zadowolenie klientów 0,009 → 0,029 (dawny wzór był dopasowany do tych 10 kart), rozwój 0,092 → 0,069.
Niepewne: przyczyna spadku w listopadzie–grudniu, styczeń (brak danych), rozwój (±0,07), braki (2 miesiące jednej firmy).
