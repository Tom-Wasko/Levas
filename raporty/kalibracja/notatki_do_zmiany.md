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

**Nowa mechanika – zatwierdzona przez autora 29.10.2026** (POSTEP, B5: „4 × tak”); tekst do notatek czeka na
wpisanie. Proponowany wiersz tabeli:
> | Rozruch nowego lokalu | w pierwszym tygodniu sprzedaży lokal ma 40% klientów, co tydzień +10 p.p., pełny popyt od 7. tygodnia sprzedaży (każdy kolejny lokal tak samo) |

Proponowany dopisek do opisu popytu (jeśli autor trzyma go w „Prawidłach świata”):
> Pule klientów stref zmniejszone o 10% (B5): jeden lokal średniej drużyny sprzedawał ok. 97 tys. zł
> miesięcznie, po zmianie ok. 85 tys. zł – bliżej typowego kebaba na dobrej ulicy w Lublinie.

## U20 – zadowolenie pracowników i odejścia (4.11.2026) → `notatki/Ustalenia gry.md`, nowa sekcja po „Limity i czasy”

Mechanika zatwierdzona przez autora 4.11.2026 (etap 1 + ukryte cechy). Proponowana sekcja:
> ## Pracownicy – zadowolenie i odejścia
> - Każda osoba ma własne **zadowolenie**: pensja z premią wobec preferowanej, sprzęt stanowiska, udogodnienia
>   lokalu, szkolenia, rodzaj umowy; przepracowanie je obniża. Wskaźnik zadowolenia w karcie wyników liczy się
>   jak dotąd (średnia firmy).
> - **Próg 0,87** (`zalozenia.yaml: pracownicy.odejscia`, założenie): pierwszy tydzień poniżej – tylko
>   ostrzeżenie na liście błędów; od drugiego tygodnia z rzędu szansa wypowiedzenia 5% za każde 0,01 poniżej
>   progu, najwyżej 50%. Wypowiedzenie działa jak zwolnienie bez odprawy.
> - **10 ukrytych cech** (np. szybki, niespieszny, lojalny) – gracz ich nie widzi, wnioskuje z krótkiego
>   żartobliwego opisu pod „i” w profilu. Cecha mnoży szansę odejścia albo zmienia godziny stanowiska o ±10%.
> - Boty od poziomu średniego podnoszą pensję niezadowolonej osobie (najwyżej do 115% preferowanej); łatwy
>   ostrzeżenia ignoruje.
> - Pomiar (dziennik kalibracji, U20): przy progu 0,87 odchodzą tylko zaniedbani; średni i trudny prawie bez
>   zmian, łatwy −0,23. Wyższy próg (0,89) sprawia, że skąpienie na pensjach się nie opłaca – do decyzji autora.

## U24 – opinie klientów i grupy klientów (4.11.2026) → `notatki/Prawidła świata.md`, nowa sekcja „Klienci”; krótko w `notatki/Elementy mapy.md`

Mechanika zatwierdzona przez autora 4.11.2026. Proponowana sekcja w „Prawidłach świata”:
> ## Klienci – grupy i opinie
> - Klienci strefy to mieszanka **8 grup**: studenci, uczniowie, pracownicy biur, imprezowicze, rodziny, turyści,
>   goście wydarzeń, podróżni (udziały wg opisu strefy, z porą roku i wydarzeniami). Każda grupa ma swój koszyk
>   dań, wrażliwość na cenę, czekanie i jakość oraz udział wegetarian (najwięcej wśród studentów, 14%) –
>   wegetarianie zamiast kebabów biorą falafel. Popyt roczny miasta się nie zmienia – zmienia się, kto go zjada i gdzie.
> - Klient, który nie znajdzie w lokalu swojego kebaba, w 10% przypadków bierze tam inny kebab (zastępstwo).
> - **Opinie:** każdy lokal ma ocenę 1–5★ z przeżyć klientów w tygodniu (jakość, cena wobec oczekiwań,
>   kolejki, braki, reklamacje, wyposażenie) – średnia krocząca, start 3,6★. Ocena zmienia popyt lokalu
>   (mnożnik ok. 0,86–1,06, mocniej, gdy opinii jest dużo).
> - Pomiar (dziennik, U24): kolejność strategii bez zmian, najwięcej zyskuje premium; jeśli w grze z drużynami
>   przewaga premium będzie za duża, pierwsza dźwignia to waga jakości w ocenie (0,3 → 0,2★).

Proponowany dopisek w „Elementach mapy” (przy lokalach):
> Nad lokalem na mapie widać jego ocenę klientów (gwiazdki) i kilka żartobliwych komentarzy z ostatniego tygodnia.

## B6 – lokal niewyposażony (5.11.2026) → `notatki/Elementy mapy.md`, lokale; do decyzji autora

Stan: lokal niewyposażony przegrywa z gotowym w każdym pomiarze (dziennik kalibracji, B6), choć ma czynsz ok. 40%
niższy (0,75 wobec 1,25 stawki strefy). Trzy próby po stronie botów (kredyt na sprzęt, leasing sprzętu, rachunek
czynszu) zmniejszyły stratę z −0,68 do −0,03…−0,06 karty, ale nie dały wygranej:
- niewyposażony 3★ − gotowy 3★: −0,09 (126/360 par wygranych); wygrywa tylko w lsm_czuby;
- drugi lokal niewyposażony − drugi gotowy: −0,19 (1 z 80 par wygrana, `b6_drugi_po2`).

Przyczyna: cały sprzęt kupuje się naraz, a pozycje do 10 000 zł idą od razu w koszty (KPiR, `amortyzacja_prog`).
W rundzie zakupu dochód spada o kilkanaście tysięcy (np. premium, drugi lokal: −17 tys. zł, karta −3,7 w tej
rundzie). Oszczędność czynszu i mediów to ok. 90–550 zł na rundę, więc zwrot sprzętu i adaptacji trwa ok. 45 rund,
a gra ma 18–26 rund. Nawet zerowy czynsz nie zwraca tego w grze, więc sama zmiana liczb nie wystarczy.

Propozycje (do wyboru, każda to zmiana mechaniki):
1. **Wybór amortyzacji sprzętu poniżej progu** – gracz przy zakupie decyduje: od razu w koszty albo amortyzacja
   20% rocznie (jak w prawie: środek do 10 000 zł można zamortyzować). Uczy realnej decyzji podatkowej i usuwa
   jednorazowy spadek dochodu. Bot przy lokalu niewyposażonym wybiera amortyzację.
2. **Okres bez czynszu na urządzenie lokalu** (2–4 rundy; tak bywa w umowach najmu) – liczba w `lokale.yaml`.
3. **Wynajmujący pokrywa adaptację** (adaptacja 0 zł przy najmie, zostaje przy kupnie).
4. **Bez zmian** – niewyposażony zostaje opcją na długą grę i własny lepszy sprzęt (3★), a uczniowie uczą się,
   że tańszy czynsz nie zawsze się opłaca. Wtedy opis w instrukcji powinien to mówić wprost.

Rekomendacja: 1 (największy sens edukacyjny, nie zmienia cen świata); po zgodzie – pomiar jak `b6_niewyp3`.

## B6 – wykup najmowanego lokalu na kredyt (5.11.2026) → `notatki/Ustalenia gry.md`, kredyty; do decyzji autora

Pomiar `b6_wykup`: bot nie wykupuje lokalu ani nie przejmuje budynku rywala, bo nigdy nie ma ceny budynku (110–200 tys.
zł) plus rezerwy w gotówce. Kredyt pod zastaw działa dziś tylko przy kupnie lokalu z Inwestycje ▸ Lokale; budynek
kupowany z najemcą może być zastawem dopiero od następnej rundy (wykupiony lokal), a kupiony z cudzym najemcą – wcale.
Uczeń, który chce wykupić swój lokal, musi więc najpierw mieć całą kwotę.

Propozycja (rozszerzenie istniejącej zasady): **budynek kupowany z najemcą może być zastawem kredytu inwestycyjnego
w tej samej rundzie**, jak kupowany lokal (limit: część wartości, `zastaw` produktu). Przy cudzym najemcy zastawem
jest budynek, którego firma jest właścicielem (dochód z czynszu spłaca raty – dobra lekcja o inwestycji w
nieruchomość na wynajem). Po zgodzie: bank (`nowy_lokal` także dla decyzji `przejecie`), bot (wykup na kredyt, jak
kupno), pomiar jak `b6_wykup`.

## B6 – kupiony lokal w „rozwoju firmy” na karcie (6.11.2026) → `notatki/Ustalenia gry.md`, karta wyników; do decyzji autora

Z1 (ustalone z autorem): kupiony lokal, budynek i grunt wchodzą do majątku w rozwoju firmy. Wzór rozwoju z Revasa
(`0,535 + 0,106 · ln(1 + majątek / 10 000) + …`) był kalibrowany na majątku ze sprzętu (kilkanaście–kilkadziesiąt
tys. zł). Lokal za 90–330 tys. zł wychodzi daleko poza ten zakres i sam podnosi rozwój o 0,2–0,3, czyli kartę o
40–55%, bez względu na to, czy kupno się opłaciło.

Pomiar `b6_kupno3` (tani, zygmuntowskie, ziarno 1000, średnie z rund 2–18): najem – rozwój 0,535 (sama stała, bo
sprzęt w lokalu jest wynajmującego), karta 0,221; kupno – rozwój **0,764**, wynik ekonomiczny +20% (bez czynszu),
wskaźnik zadłużenia 0,712 (kredyt), karta 0,265. W zygmuntowskim kupno wygrywa kartą w 34–36/36 par **przy każdej
cenie** (×1, ×1,5, ×2), choć majątek netto prawie się nie różni. Droższy lokal jeszcze podnosi rozwój, więc cena
kupna słabo działa na kartę – po ×1,5 (f4335c5) tani dalej wygrywa kartą 28–29/30, a majątkiem 25–27/30.

Propozycje (do wyboru):
1. **Nieruchomości w rozwoju z wagą** (np. 0,25–0,5): lokal dalej się liczy (Z1 zostaje), ale nie przeważa nad
   sprzętem. Jeden parametr `rozwoj_firmy.waga_nieruchomosci` w `zalozenia.yaml`; wskaźnik zadłużenia liczy
   majątek w pełni. Po zgodzie – pomiar jak `b6_kupno3` z wagami 1 / 0,5 / 0,25.
2. **Osobna skala dla nieruchomości** (`ln(1 + lokale / 100 000)`): podobny efekt, trudniej wytłumaczyć uczniowi.
3. **Bez zmian** – kupno lokalu „rozwija firmę” na karcie, a cena działa tylko na majątek netto. Wtedy kupno
   zostaje najlepsze kartą w słabych strefach i dla strategii bez wydatków na marketing.

Rekomendacja: 1 z wagą 0,5 (lokal za 115 tys.: rozwój ok. 0,74 zamiast 0,80 – nadal wyraźnie wyżej niż 0,535 przy
   najmie).

## B7 – szerokie menu bez kosztu (6.11.2026) → `notatki/Ustalenia gry.md` (menu i popyt); do decyzji autora

Każde danie ma własną pulę klientów miasta (`uslugi.yaml: popyt_roczny`). Klient dania, którego lokal nie ma w
menu, nie wybiera w tym lokalu innego dania, tylko inny lokal albo „obiad w domu”. Dodatkowe dania (box, talerz,
falafel) nie wymagają nowego sprzętu, bo rożen i frytownica już stoją. Dlatego każde nowe danie to prawie same
nowe pule klientów. Pomiar `b7_cena` (6 ziaren, 18 i 26 rund): pełne menu 8 dań wygrywa w 12/12 par u
zrównoważonego (6 → 8 dań: karta +0,20, majątek +26 tys.) i u premium (5 → 8: karta +0,74, majątek +61 tys.;
przychód +48%, koszty +31%). Kompromis z inwentarza („szersze menu – więcej składników, psucie i czas kuchni;
wąskie – prostsza kuchnia”) prawie nie działa: dobry uczeń zawsze weźmie wszystko.

Propozycje (do wyboru):
1. **Zastępowalność dań** (rekomendowana): klient dania, którego nie ma w menu lokalu, z ułamkiem
   `zastepowalnosc` (np. 0,5–0,6) bierze danie tej samej kategorii (kebab w bułce zamiast talerza). W modelu:
   lokal bez dania uczestniczy w jego puli z atrakcyjnością × `zastepowalnosc`, a obsłużeni klienci kupują danie
   zastępcze. Wąskie menu traci mniej klientów, szerokie zyskuje mniej, ale nadal więcej. Już dziś
   `mapa/menu.yaml: zmiana_dania` (0,5) robi to samo dla dania z menu, którego zabrakło – byłoby to rozszerzenie
   tej zasady na dania spoza menu.
2. **Koszt stały dania**: każde danie w menu lokalu kosztuje tygodniowo (przygotowanie, minimalna partia,
   resztki), np. 150–300 zł. Proste, ale sztuczne – uczeń nie zobaczy, skąd koszt.
3. **Bez zmian**: pełne menu jako „oczywista dobra decyzja” (jak płacenie ZUS). Wtedy w botach wszystkie
   strategie biorą 8 dań, a strategie różnią się ceną, jakością, strefą i marketingiem.

Rekomendacja: 1 – zgodne z realiami (klient przychodzi „na kebaba”, a nie na konkretną pozycję) i z istniejącą
zasadą zmiany dania. Po zgodzie: pomiar `menu` 3/5/8 jak w `b7_cena` z `zastepowalnosc` 0,4 / 0,6.
