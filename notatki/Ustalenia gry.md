[[Główny obraz]] · [[Prawidła świata]] · [[Elementy mapy]] · [[Plan implementacji]]

# Ustalenia gry

Wszystkie ustalone parametry w jednym miejscu. Wartości oznaczone *(roboczo)* zmienią się przy kalibracji (krok 5). Przepisy i stawki są z pamięci albo ze starego Levasa – *do weryfikacji*.

## Gra
| Parametr | Wartość |
|---|---|
| Runda | 1 tydzień w świecie gry |
| Tempo | 2–3 rundy na tydzień rzeczywisty; moment zamknięcia rundy ustala mistrz gry (ręcznie albo o ustalonej godzinie) |
| Długość gry | ustala mistrz gry, domyślnie 26 rund (pół roku) |
| Drużyny | 1–4 osób, wszystkie na jednej wspólnej mapie Lublina |
| Boty | mistrz gry włącza je albo nie i wybiera poziom trudności |
| Kapitał startowy | 100 000 zł |
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
| Pusta działka → lokal | 3–4 rundy |
| Lokal niewyposażony → gotowy | 1 runda |
| Pojedynczy sprzęt, mebel | od razu |
| Kasyno | otwarte tylko na 1 rundę po zaproszeniu |

## Przejęcia
- Okres wypowiedzenia pracownika na umowie o pracę (KP art. 36) w rundach: 2 rundy (staż < 6 mies.), 4 rundy (6 mies. – 3 lata), 13 rund (≥ 3 lata). Pracownicy w puli mają losowy staż u obecnego pracodawcy.
- Zleceniobiorca odchodzi od razu.
- Kontroferta obecnego pracodawcy: w tej samej rundzie, przed decyzją pracownika.
- Wypowiedzenie najmu przez nowego właściciela budynku: 4 rundy (KC art. 673, 678); rozliczenie ulepszeń wg KC art. 676.
- Licytacja: wygrywa najwyższa oferta w rundzie; przy remisie decyduje losowanie.

## Odblokowywanie zakładek – domyślny harmonogram *(roboczo, mistrz gry może zmienić)*
| Runda | Co się odblokowuje |
|---|---|
| 1 | Lokale (najem, kupno), Menu, Dostawcy (dyskonty, hurtownie), HR (pracuj.pl), Finanse (bank, biuro rachunkowe) |
| 2 | Producent mięsa, agencja pracy, promocje, parki |
| 3 | Agencje reklamowe (część kanałów), ubezpieczyciel |
| 4 | Karta skumulowana, headhunter (podkupywanie), licytacje i przejęcia lokali |
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
