# Inwentarz decyzji – kompas kalibracji (B1, 29.10.2026)

Dla każdej decyzji z `gra/silnik/decyzje.py` (format w docstringu, uzupełniony w B1): opcje, parametry YAML,
czy boty jej używają i **zamierzony kompromis** – kiedy dana opcja powinna wygrywać. Kompromisy są zapisane
**przed** strojeniem; w B4–B12 mierzymy, czy gra je spełnia. Obszary jak w planie (B6–B12).

Skróty: `L` = `dane/mapa/`, `Z` = `dane/zdarzenia/`, `zal` = `dane/zalozenia.yaml`. „Boty: nie” znaczy, że
przed pomiarem tej opcji trzeba dopisać ją do botów (B3) albo wymusić decyzję narzędziem z B2.

## Stan wyjściowy (9 gier botów, 18 rund, 5 strategii, ziarna 7/11/23)

Skrypt: gra botów na jednym poziomie, sumy KPiR z 18 rund. Liczby zgrubne – dokładny pomiar robi B4.

| poziom | pierwszy tydzień z dochodem > 0 | dochód 18 rund (od–do) | towary / przychód | praca / przychód |
|---|---|---|---|---|
| łatwy | 2–4 (agresywny w 1 z 3 gier – nigdy, bankructwo) | −121 tys. – 195 tys. | 0,32–1,15 | 0,12–0,23 |
| średni | 2–4 | 17 tys. – 169 tys. | 0,31–0,43 | 0,14–0,19 |
| trudny | 2–4 | 53 tys. – 240 tys. | 0,28–0,37 | 0,14–0,20 |

- Marża netto (dochód / przychód) średniego bota: zwykle 25–40%. Realia: kilka do kilkunastu procent.
- Każdy bot wybiera mBank i biuro e-Księgi24 (reguły `najlepsze()` / `najtansze()`).
- Poziomy: średni > łatwy u wszystkich strategii; trudny > średni tylko tam, gdzie bierze drugi lokal (tani,
  agresywny) – premium i naśladowca na trudnym bywają słabsi niż na średnim.
- Agresywny obsługuje 50–70% popytu: reklama tworzy popyt, którego jeden lokal nie obsłuży.

## Lokale (B6)

**`lokal`** – `{id, forma: najem | kupno, oferta}`
- Opcje: 38 lokali w 10 strefach; typ gotowy (19) / niewyposażony (14) / działka (5, tylko kupno); najem albo
  kupno; oferta w licytacji (do `oferta_max` × wywoławcza).
- Parametry: `L/lokale.yaml` (zasady: `nowy_lokal_co_rund` 3, `kaucja_miesiecy` 2, `licytacje_od_rundy` 1,
  `oferta_max` 3, `urzadzanie_rund`; na lokal: czynsz, cena, utrzymanie, miejsca, zestaw, metraż, koszt i czas
  budowy), `L/strefy.yaml`, `L/popyt.yaml` (pula strefy), `L/budynki.yaml`; kredyt pod zastaw – `L/banki.yaml`.
- Boty: tylko gotowy lokal w najmie (`boty.py: _wybierz_lokal`); trudny bierze drugi lokal (`kolejny_lokal`,
  maks. 2), niemożliwy – trzeci.
- Kompromis:
  - najem – mało kapitału i elastyczność, drożej w długiej grze;
  - kupno – duży wkład, tańsze od około połowy gry 18 rund, w majątku netto (po amortyzacji); ryzyko: zamrożona
    gotówka na start;
  - niewyposażony – niższy czynsz albo cena, ale adaptacja, zakup sprzętu i tydzień opóźnienia; wygrywa, gdy
    gracz chce własny (lepszy) sprzęt;
  - działka – najdłuższy zwrot, ma się opłacać tylko w długiej grze (26 rund);
  - strefa – centrum i Stare Miasto: duża pula, drogo i tłoczno; peryferie: tanio, mało klientów; każda strefa
    powinna być najlepsza dla jakiejś strategii;
  - drugi lokal – wzrost, ale koszty stałe i ryzyko; przy jednym lokalu z wolnym popytem ma przegrywać z
    lepszym wykorzystaniem pierwszego;
  - licytacja – przepłacenie kontra utrata lokalu.

**`przejecie`** – `{id, oferta}`, kupno budynku z najemcą (od `przejecia_od_rundy` 4)
- Boty: nie.
- Kompromis: czynsz od najemcy (przychód) i możliwość wypowiedzenia rywalowi kontra zamrożony kapitał; opłaca
  się w dłuższej grze albo jako ruch przeciw silnemu rywalowi, nie zawsze.

**`wypowiedz`** – `[{id, ulepszenia: zatrzymaj | przywroc}]` (`wypowiedzenie_rund` 4, `ulepszenia_zwrot` 0,5,
`przywrocenie_koszt` 0,3)
- Boty: nie.
- Kompromis: usunięcie konkurenta z budynku za cenę czasu (4 rundy) i rozliczenia nakładów; nie może być tanim
  sposobem na wykończenie rywala.

**`stanowiska`** – `{kuchnia: 0–5, kasa: 0–5}`, najwyżej tyle, ile miejsc w lokalu
- Parametry: `dane/sprzet.yaml`, `L/lokale.yaml` (miejsca), `zal` (`operacje`).
- Boty: tak (planujący – na popyt dzień po dniu).
- Kompromis: więcej stanowisk – większa przepustowość w szczycie, ale koszt sprzętu i pracy w spokojne dni.

## Menu i ceny (B7)

**`oferta`** – lista dań (limit: 3 w rundach 1–2, potem +3 na rundę; `dane/katalog.yaml: rundy`)
- Parametry: `dane/uslugi.yaml`, `L/menu.yaml`, `zal: popyt`.
- Boty: tak (`uslugi` w strategii: 5–8 dań).
- Kompromis: szersze menu – więcej klientów, ale więcej składników, psucie i czas kuchni; wąskie – prostsza
  kuchnia i mniej strat.

**`sprzedaz`** – `{danie: {cena, rabat}}`
- Parametry: `zal: popyt` (`elastycznosc_ceny`, `elastycznosc_wzgledem_rynku`), cena preferowana w
  `dane/uslugi.yaml`.
- Boty: tak (cena = ułamek ceny preferowanej: 0,78–1,08; trudny sprawdza mnożniki ceny pod marżę).
- Kompromis: niska cena – wolumen, wymaga przepustowości, mała marża; wysoka – marża, mniej klientów; przy
  zatkanej kuchni podwyżka ma się opłacać.

**`promocje`** – `[{typ, nazwa, danie}]`, najwyżej `limit_aktywnych` 2, od rundy 2
- Typy (`L/promocje.yaml`): 2 za 1, zestaw z napojem, happy hours, karta stałego klienta, studencka i inne;
  każdy z przyciąganiem malejącym (`przyrost`) albo rosnącym (karta – przywiązanie).
- Boty: tak (wg strategii, wyłączają przy obsłudze < 0,9 popytu; łatwy nie daje promocji).
- Kompromis: promocja wypełnia wolną przepustowość; przy pełnej kuchni ma się nie opłacać (rabat bez nowych
  klientów); 2 za 1 – mocny start, szybkie znużenie; karta – słaba na początku, silna długo.

**`nazwa`, `misja`** – tylko wygląd, bez wpływu na wynik (zamierzone).

## Zaopatrzenie (B8)

**`zamowienia`** – `[{dostawca, zasob, jakosc, ilosc, dzien}]`
- Dostawcy (`dane/dostawcy.yaml`):
  - piekarnia: codziennie, dostawa 15 zł, darmowa od 150 zł;
  - 3 dyskonty: odbiór osobisty (1–1,5 h właściciela), limit 4 opakowań, gazetka z rabatem 10–35% na kilka
    pozycji;
  - 3 hurtownie: dostawy 2–3 dni w tygodniu, koszt 69–89 zł, darmowa od 900–1200 zł;
  - producent mięsa „Rożen”: od rundy 3, 2 dni dostaw, minimum 800 zł.
- Parametry: ceny miesięczne w `dane/dostawcy.yaml`, `dane/zasoby.yaml` (opakowania, świeżość), `Z/magazyn.yaml`
  (sanepid, chłodnia).
- Boty: tak (`zamowienie_zasobow`: jakość wg strategii, zapas `zapas_zasobow` 1,05).
- Kompromis:
  - dyskont – tanio przy małej skali, kosztuje czas właściciela i limit opakowań;
  - hurtownia – taniej przy dużym wolumenie, rzadkie dostawy (zapas → psucie);
  - producent – najlepsza cena mięsa przy dużym zamówieniu, próg wejścia;
  - piekarnia – świeże pieczywo codziennie, drożej;
  - jakość składnika – zadowolenie klientów kontra koszt;
  - duży zapas – bezpieczeństwo kontra przeterminowanie i mandaty sanepidu.

**`sprzet_kup` / `sprzet_sprzedaj`** – `{typ, nr, nazwa, jakosc 1–3}`, sprzedaż za ok. 50% (`zal: finanse`)
- Parametry: `dane/sprzet.yaml` (cena, utrzymanie, wydajność według jakości).
- Boty: kupują wg jakości strategii; nie sprzedają.
- Kompromis: lepszy sprzęt – szybciej i lepiej, ale drożej w zakupie i utrzymaniu; tańszy wystarcza przy małym
  ruchu.

**`handel_oferty` / `handel_przyjmij` / `handel_odpowiedzi`** – handel towarem i sprzętem między drużynami
- Parametry: `Z/handel.yaml`.
- Boty: nie.
- Kompromis: zbycie nadwyżek i sprzętu rywalowi poniżej ceny rynkowej – obie strony zyskują trochę; nie może
  dawać darmowego arbitrażu.

**Opcja gry `auto_zamowienia`** – zamówienia z prognozy; ma być wygodne, ale gorsze od dobrego planu ręcznego.

## Ludzie (B9)

**`zatrudnij`** – `[{kandydat, typ, nr, pensja, umowa: prace | zlecenie, kanal}]`; **`podkup`**,
**`kontroferty`**, **`zmiany`** (`pensja`, `umowa`, `premia`), **`zwolnij`**
- Parametry: `dane/kandydaci.yaml`, `zal` (rynek pracy, `zadowolenie_pracownikow`, `godziny_pracownika`),
  kanały pracuj.pl / agencja / headhunter (`silnik/ludzie/rynek_pracy.py`), `dane/podatki_2026.yaml`
  (ZUS – prawo zamrożone).
- Boty: zatrudniają kandydata o gwiazdkach bliskich jakości strategii, za pensję preferowaną, zawsze na umowę o
  pracę; bez podkupów, kontrofert, premii i zwolnień.
- Kompromis:
  - więcej gwiazdek – wydajność i jakość kontra pensja;
  - umowa o pracę – droższa (ZUS), ale okres wypowiedzenia chroni przed podkupieniem; zlecenie – taniej, ryzyko
    natychmiastowego odejścia;
  - pensja ponad preferowaną i premia – zadowolenie i mniejsza rotacja kontra koszt;
  - headhunter – drogo, ale dostęp do najlepszych i podkupienie rywalowi.

**`szkolenia`** – `[{firma, szkolenie}]` (`dane/katalog.yaml`)
- Boty: tak (0–2 wg strategii).
- Kompromis: koszt teraz, zadowolenie i jakość później; w krótkiej grze mniej warte.

**`wlasciciel_stanowisko`** – `{typ, nr, godziny}` – właściciel na pustym stanowisku
- Parametry: `zal: operacje` (`czas_wlasciciela`, `godziny_pracownika`), jakość jak kandydat 1★.
- Boty: nie.
- Kompromis: oszczędność pensji na starcie kontra czas na odbiory w dyskontach, eventy i detektywa; przy
  większej firmie ma przegrywać z pracownikiem.

## Marketing (B10)

**`kampanie`** – `[{agencja, kanal, strefa}]` (od rundy 3, wszystkie od 5)
- Parametry: `L/reklama.yaml` (`model`: zagłuszanie 0,5, nasycenie 0,3 w oknie 4 rund, wygasanie 0,5,
  `maks_przyciagania` 0,7, `maks_puli` 0,15; na kanał: koszt, pula, przyciąganie, rundy, zasięg).
- Boty: tak (wg strategii, z buforem gotówki i minimalną siłą; łatwy – nie).
- Kompromis: kampania w strefie, gdzie rywale reklamują się tym samym rodzajem, słabnie (zagłuszanie);
  powtarzanie tej samej słabnie (nasycenie); reklama bez przepustowości to strata; każdy rodzaj (druk,
  internet, radio, wydarzenia) ma wygrywać w jakimś kontekście.

**`udogodnienia_kup` / `udogodnienia_sprzedaj`**, **`wyposazenie_kup` / `wyposazenie_sprzedaj`** – `[nazwa]`
- Parametry: `dane/katalog.yaml` (cena, procent klientów), `zal: popyt` (`wyposazenie_na_procent_klientow`),
  `zal: zadowolenie_pracownikow` (`udogodnienia_na_procent`).
- Boty: tak (0–9 sztuk wg strategii, gdy gotówka > `bufor_gotowki`).
- Kompromis: trwały efekt kontra jednorazowy wydatek; z malejącymi korzyściami – pierwsze sztuki warte więcej.

**`zdarzenia`** – wybór opcji w historiach i eventach w parkach (`Z/parki.yaml`)
- Boty: tak (losowo, opcje do 3 h właściciela).
- Kompromis: event – klienci i reputacja za czas i pieniądze; nie każdy jest wart udziału.

## Finanse (B11)

**`bank`** – konto firmowe (6 banków, `L/banki.yaml`)
- Różnice: opłata za konto 0–29 zł, terminal (abonament 0–59 zł, prowizja 0,79–1,3% od płatności kartą,
  `udzial_kart` 0,7), limit w koncie 5–40 tys. zł (oprocentowanie 13,5–16,9%).
- Boty: zawsze mBank (`banki.najlepsze()["konto"]` – najtańsze konto + abonament).
- Kompromis: mBank – najtańsze konto przy dużych obrotach kartą; Santander – duży limit dla firm z ujemną
  gotówką na starcie; ING – dla firm z nadwyżką (lokaty); bank „od kredytu” – gdy firma bierze kredyt.

**`lokaty_zaloz` / `lokaty_zerwij`** – `{kwota, miesiecy: 1 | 4 | 13, bank}`
- Boty: nie.
- Kompromis: odsetki od nadwyżki kontra płynność (zerwanie traci odsetki); nie może bić inwestycji w firmę.

**`kredyty_wez` / `kredyty_splac`** – `{bank, produkt: start | obrotowy | inwestycyjny, kwota, miesiecy,
zastaw}`
- Parametry: `L/banki.yaml` (oprocentowanie 7,9–11,9%, prowizja, `historia_rund` 4, `stopa_karna`, `przejecie_po`
  3, `wycena_zastawu` 0,8).
- Boty: nie.
- Kompromis: dźwignia (drugi lokal, kupno lokalu) opłaca się, gdy zwrot > koszt kredytu; kredyt bez planu
  spłaty – ryzyko przejęcia zastawu.

**`leasing_wez`** – `{bank, typ, nr, nazwa, jakosc, rund}` (PKO, Pekao: wpłata 10–15%, 26 albo 52 rundy)
- Boty: nie.
- Kompromis: sprzęt bez wydatku na start kontra wyższy koszt łączny i brak sprzedaży; wygrywa przy braku
  gotówki i krótkiej grze.

**`harpagon_wez` / `harpagon_splac`** – kwota 500–20 000 zł, 5% tygodniowo od całego długu, termin 4 rundy,
potem odsetki karne 10% i wizyty (`L/harpagon.yaml`)
- Boty: nie.
- Kompromis: ratunek na 1–2 tygodnie przy pewnym zwrocie (np. zatowarowanie przed świętem); zwykle się nie
  opłaca, a przeciągnięty dług niszczy firmę. Poza KPiR, więc do Z1 odsetki nie obniżają karty.

**`wyplata_wlasna` / `wplata_wlasna`** – kwota; portfel właściciela poza firmą (`Z/wlasciciel.yaml`)
- Boty: nie.
- Kompromis: brak – to narzędzie (np. wpłata wygranej z kasyna). Wypłata nie może poprawiać karty.

**`kasyno`** – `[{gra, zaklad, stawka}]` po zaproszeniu, z portfela właściciela (`Z/kasyno.yaml`)
- Boty: nie.
- Kompromis: ujemna wartość oczekiwana; czasem wygrana ratuje firmę, ale średnio się nie opłaca.

## Księgowość i urzędy (B12)

**`biuro`** – 5 biur rachunkowych albo `samodzielnie` (`L/biura.yaml`)
- Różnice: ryczałt 0–984 zł, opłata za dokument 0–7,38 zł, kadry 18–74 zł na osobę, `ryzyko_bledu` 0–12%,
  OC (e-Księgi24 bez OC).
- Boty: zawsze najtańsze (`biuro.najtansze()` → e-Księgi24).
- Kompromis: tanie biuro bez OC – ryzyko mandatu na firmie; drogie z OC – spokój; ryczałt opłaca się przy wielu
  dokumentach; samodzielnie – oszczędność kosztem czasu i ryzyka błędów (lekcja KPiR).

**`ksiegowosc`** – `{zapisy, deklaracja}` – samodzielna księgowość za poprzednią rundę (`silnik/ksiegowosc/biuro.py`)
- Boty: nie.
- Kompromis: błędy i spóźnienia kosztują kary (prawo zamrożone); rzetelnie prowadzona ma być tańsza od biura.

**`higiena`** – brak / podstawowa / firma / haccp (`Z/urzad.yaml`, koszt miesięczny za lokal)
- Boty: tak (wg strategii; tani i zrównoważony – podstawowa).
- Kompromis: „brak” nie przechodzi odbioru, a kontrole kończą się mandatem – łamanie zasad średnio się nie
  opłaca; wyższe poziomy – mniejsze ryzyko kontroli przy dużym magazynie i skargach.

**`polisy`** – lokal / sprzęt / OC (`Z/losowe.yaml`: wypadki od rundy 4, szansa 8% + 4 pp. na rundę bez wypadku,
do 40%, szkoda do 8000 zł, karencja 1 runda)
- Boty: tak (wg strategii; tani – żadnej).
- Kompromis: lekko ujemna wartość oczekiwana, ale chroni przed szkodą, która przy małej gotówce kończy się
  debetem; bez polisy wygrywa się średnio trochę, przegrywa rzadko a boleśnie.

**`detektyw`** – nazwa rywala (`Z/detektyw.yaml`: koszt losowany, godziny właściciela, szansa wpadki)
- Boty: nie (zamierzone – `konkurencja.py`).
- Kompromis: dokładne dane rywala za pieniądze, czas i ryzyko ujawnienia; wartość zależy od tego, czy gracz
  umie je wykorzystać (ocena w części A, nie w pomiarze botów).

## Hipotezy „za dobrych” strategii do sprawdzenia w B4

Źródło: czytanie kodu i gry botów wyżej. Numery H1… służą w dzienniku i w raporcie B4.

| nr | hipoteza | skąd | jak sprawdzić |
|---|---|---|---|
| H1 | Gra jest za łatwa: pierwszy plus w tygodniu 2–4 u prawie wszystkich botów, marża netto 25–40% | gry botów | B4: krzywa trudności, bot „jak człowiek” (Z5); B5 |
| H2 | Koszty pracy 12–20% przychodu (realia 25–35%) – obsada za mała albo pensje za niskie wobec przychodu | gry botów | B4: struktura kosztów; B5/B9 |
| H3 | Umowa zlecenia dominuje: brak ZUS pracodawcy (`runda.py:211`), kara tylko −1,15 pp. zadowolenia przy 100% zleceń | kod | para: ta sama gra, wszyscy na zleceniu |
| H4 | mBank dominuje konto: najtańszy przy każdym obrocie, limit 10 tys. jak u większości | kod, boty | pary: 6 banków × strategie |
| H5 | e-Księgi24 dominuje biuro: najtańsze, a oczekiwane kary (12% bez OC) mniejsze od oszczędności | kod, boty | pary: 5 biur + samodzielnie |
| H6 | Drugi lokal zawsze się opłaca: trudny tani/agresywny z 2 lokalami ma 2–3× dochód średniego | gry botów | pary: z drugim lokalem i bez, różne rundy |
| H7 | Jeden lokal ma niski sufit obsługi: agresywny obsługuje 50–70% popytu – reklama ponad przepustowość się nie zwraca | gry botów | pary: kampanie włączone / wyłączone przy pełnej kuchni |
| H8 | Strategia premium (cena 1,08, jakość 3, dużo udogodnień) wygrywa na poziomie średnim – jakość 3 może dominować | gry botów | pary: jakość 1/2/3 przy tej samej cenie |
| H9 | Lokata ING bez ryzyka bije trzymanie gotówki ponad bufor – zamierzone, ale nie może bić inwestycji | kod | pary: lokata z nadwyżki / bez |
| H10 | Harpagon jest darmową dźwignią dla karty (poza KPiR) – do naprawy w Z1 | kod | po Z1: para z pożyczką / bez |
| H11 | Zakup sprzętu pompuje „rozwój firmy” w karcie – do naprawy w Z1 | kod, plan | po Z1: para z zakupem / bez |
| H12 | Kupno gotowego lokalu bije najem już w grze 18 rund | kod | pary: najem / kupno tego samego lokalu, 12/18/26 rund |
| H13 | 2 za 1 opłaca się zawsze przy wolnej kuchni (przyciąganie startowe 0,5) | kod | pary: każda promocja / brak |
| H14 | Polisy mają ujemną wartość także dla biednej firmy – nikt rozsądny ich nie kupi | kod | pary: komplet polis / brak, wiele ziaren |
| H15 | Higiena „podstawowa” wystarcza zawsze – „firma” i „haccp” się nie zwracają | kod, boty | pary: 4 poziomy higieny |
| H16 | Dyskont z gazetką dominuje zakupy małej firmy (rabat 15–35%), a hurtownia nie zwraca się nigdy przy 1 lokalu | kod | pary: dostawcy wymuszeni |
| H17 | Łatwy bot agresywny bankrutuje (towary 115% przychodu) – proste planowanie zamawia cały popyt i towar się psuje | gry botów | B3: czy łatwy ma być aż tak słaby |

Hipotezy z raportu części A dopisuje się tu w kroku U (numery H18…), a sprawdza w B6–B12.
