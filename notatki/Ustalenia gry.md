[[Główny obraz]] · [[Prawidła świata]] · [[Elementy mapy]] · [[Plan implementacji]]

# Ustalenia gry

Wszystkie ustalone parametry w jednym miejscu. Wartości oznaczone *(roboczo)* zmienią się przy kalibracji (krok 5). Przepisy i stawki są z pamięci albo ze starego Levasa – *do weryfikacji*.

## Gra
| Parametr | Wartość |
|---|---|
| Runda | 1 tydzień w świecie gry |
| Tempo | 2–3 rundy na tydzień rzeczywisty; moment zamknięcia rundy ustala mistrz gry (ręcznie albo o ustalonej godzinie) |
| Długość gry | ustala mistrz gry, domyślnie 18 rund (18 tygodni: od września do początku stycznia) |
| Drużyny | 1–4 osób, wszystkie na jednej wspólnej mapie Lublina |
| Marka firmy | w rundzie 1 drużyna wybiera nazwę, slogan, kolor (w nim jej lokale na mapie) i wgrywa logo (PNG albo JPG) |
| Boty | mistrz gry włącza je albo nie i wybiera poziom trudności |
| Kapitał startowy | 40 000 zł |
| Miasto | Lublin, 10 stref (Stare Miasto, Centrum, Miasteczko Akademickie, Politechnika, Dworzec, Zygmuntowskie, LSM i Czuby, Czechów i Kalinowszczyzna, Felin, Zemborzyce) |
| Marki | prawdziwe nazwy (banki, sklepy, hurtownie) |
| Postacie | biuro rachunkowe Jakuba Klimka-Ślęzaka (J.K.Ś.), lokal Tymka na sprzedaż, lichwiarz Harpagon |
| Ocena | karta wyników Revasa dostosowana do kebabu (p. niżej) |

## Firma i podatki *(do weryfikacji – `podatki_2026.yaml` starego Levasa)*
- Jednoosobowa działalność gospodarcza (JDG), KPiR, czynny podatnik VAT.
- Rozliczenia **co tydzień**: płace, ZUS, zaliczka PIT, VAT.
- PIT liniowy 19%; składka zdrowotna 4,9% (z minimum).
- ZUS właściciela: ulga na start przez 26 tygodni (tylko zdrowotna), potem ZUS preferencyjny.
- ZUS pracodawcy przy umowie o pracę ok. 20,5%; student poniżej 26 lat na zleceniu – bez ZUS i PIT.
- Płaca minimalna 2026: 4806 zł miesięcznie (31,40 zł/h); w grze przeliczana na tydzień.
- VAT sprzedaży: dania 8%, napoje 23%. VAT zakupu: żywność 5% (część 8%), napoje, opakowania i sprzęt 23%.

## Limity i czasy
| Co | Wartość |
|---|---|
| Nowi pracownicy | najwyżej 3 na rundę |
| Nowy lokal | najwyżej co 3 rundy |
| Pusta działka → lokal | 3–4 rundy; w ostatniej rundzie budowy można już kupić stanowiska i sprzęt oraz zatrudnić ludzi – lokal rusza od razu gotowy do sprzedaży |
| Lokal niewyposażony → gotowy | 1 runda; w tej rundzie kupuje się wyposażenie i zatrudnia ludzi – lokal rusza od razu gotowy |
| Ceny dań | od 50% do 200% ceny rynkowej (cena spoza widełek jest odrzucana) |
| Kredyt inwestycyjny | od wzięcia lokalu (wynajętego albo kupionego), także na zakup lokalu w tej samej rundzie |
| Pojedynczy sprzęt, mebel | od razu |
| Kasyno | otwarte tylko na 1 rundę po zaproszeniu |

## Magazyn
- Nie ma stałego kosztu magazynowania ani zwrotów towaru do dostawcy – kupiony towar zostaje w lokalu.
- Pojemność chłodni i zamrażarki zależy od sprzętu w lokalu. Towar, który się nie mieści, trafia do wynajętej chłodni: 1 zł za litr nadmiaru przy dostawie, termin przydatności krótszy o 2 dni *(roboczo)*.
- Sanepid: duży nadmiar w wynajętej chłodni i przeterminowany towar zwiększają szansę kontroli; kontrola z zastrzeżeniami to mandat i mniej klientów przez kilka rund.
- Bank żywności: gdy w lokalu jest dużo jedzenia blisko końca terminu, może pojawić się zdarzenie z propozycją oddania go do banku żywności.

## Przejęcia
- Okres wypowiedzenia pracownika na umowie o pracę (KP art. 36) w rundach: 2 rundy (staż < 6 mies.), 4 rundy (6 mies. – 3 lata), 13 rund (≥ 3 lata). Pracownicy w puli mają losowy staż u obecnego pracodawcy.
- Zleceniobiorca odchodzi od razu.
- Kontroferta obecnego pracodawcy: w tej samej rundzie, przed decyzją pracownika.
- Wypowiedzenie najmu przez nowego właściciela budynku: 4 rundy (KC art. 673, 678); rozliczenie ulepszeń wg KC art. 676.
- Licytacja: wygrywa najwyższa oferta w rundzie; przy remisie decyduje losowanie. Licytacja lokali działa od rundy 1; przegrana drużyna widzi obie oferty i wyjaśnienie, co zrobić następnym razem.

## Odblokowywanie zakładek – domyślny harmonogram *(roboczo, mistrz gry może zmienić)*
| Runda | Co się odblokowuje |
|---|---|
| 1 | Marka firmy (nazwa, slogan, kolor, logo), Lokale (najem, kupno, licytacja), Menu, Dostawcy (dyskonty, hurtownie), HR (pracuj.pl), Finanse (bank, biuro rachunkowe) |
| 2 | Producent mięsa, agencja pracy, promocje, parki |
| 3 | Agencje reklamowe (część kanałów), ubezpieczyciel |
| 4 | Karta skumulowana, headhunter (podkupywanie), przejęcia lokali |
| 5 | Wszystkie kanały reklamy, handel między drużynami |

## Karta wyników *(roboczo, wzory w kroku 4)*
**Wynik tygodnia** = iloczyn pięciu wskaźników; przy ujemnym wyniku ekonomicznym = 0. **Karta skumulowana** = średnia wszystkich kart.

| Wskaźnik | Od czego zależy w Levasie |
|---|---|
| Wynik ekonomiczny | dochód netto tygodnia (z KPiR) względem progu |
| Zadowolenie pracowników | płaca względem oczekiwanej, umowa, przepracowanie, zmiany w zatrudnieniu |
| Zadowolenie klientów | cena względem strefy, jakość dań, czas obsługi, brakujące dania, świeżość, wypadki i kontrole |
| Rozwój firmy | liczba lokali, dań w menu i pracowników, wartość sprzętu |
| Wskaźnik zadłużenia | kredyty bankowe względem majątku (1 bez kredytu) |
