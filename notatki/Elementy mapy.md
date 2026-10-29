[[Zarys aplikacji]] · [[Prawidła świata]] · [[Ustalenia gry]]

# Elementy mapy

Każdy element ma plusy i minusy – nie ma jednego najlepszego wyboru.

## Kebab (lokale)
- Wiele lokalizacji w strefach Lublina; wszystkie drużyny grają na jednej wspólnej mapie.
- **Globalna pula lokali** – ta sama dla wszystkich drużyn. Lokal zajęty przez jedną drużynę znika z oferty dla pozostałych.
- Lokale można wynajmować albo kupować; ceny i czynsze zależą od strefy.
- Gdy o ten sam lokal w jednej rundzie walczy kilka drużyn, wygrywa wyższa oferta (licytacja od rundy 1); przegrany dostaje wyjaśnienie.
- Lokale innych drużyn są na mapie w kolorze ich firmy (kolor wybierany w rundzie 1), a legenda mówi, która to firma.

| Typ | Gotowy po | Plusy | Minusy |
|---|---|---|---|
| Lokal gotowy do działania | od razu | sprzedaż od pierwszej rundy | najwyższy czynsz lub cena, cudzy układ i sprzęt |
| Lokal niewyposażony | 1 runda urządzania | czynsz i cena kupna niższe niż gotowego, własny wybór sprzętu | trzeba kupić całe wyposażenie (w rundzie urządzania – lokal rusza od razu gotowy) |
| Pusta działka | 3–4 rundy budowy | najtańsza, własność, dobre miejsca | długa budowa, duży wydatek na start; stanowiska, sprzęt i ludzi kupuje się już w ostatniej rundzie budowy |

- Jeden z lokali należy do **Tymka** i jest wystawiony na sprzedaż.
- Limit: nowy lokal najwyżej co 3 rundy ([[Prawidła świata]]).
- Liczba lokali na mapie zależy od liczby drużyn (klucz `od_firm` w `dane/mapa/lokale.yaml`): 8 firm – 38 lokali, 6–7 – 29, 4–5 – 20 (około 5 na firmę, wszystkie strefy, podobne proporcje typów). Popyt miasta się nie zmienia.
- **Rozruch:** nowy lokal dopiero zdobywa klientów – w pierwszym tygodniu sprzedaży ma 40% popytu, co tydzień więcej ([[Ustalenia gry]]).

## Sklepy budowlane
Leroy Merlin, IKEA, OBI, Jula, Castorama – meble, wyposażenie sali, materiały do urządzenia lokalu. Pojedynczy element jest od razu, pełne wyposażenie lokalu mieści się w 1 rundzie urządzania.

## Dostawcy jedzenia
| Rodzaj | Marki | Jak działa |
|---|---|---|
| Dyskonty | Biedronka, Lidl, Stokrotka | dobre ceny przy małych ilościach, gazetki z promocjami, odbiór osobisty kosztuje czas właściciela |
| Hurtownie | Makro, Selgros, Eurocash | ceny hurtowe, dostawa w wybrane dni, darmowa od progu zamówienia |
| Producent mięsa kebab | (nazwa do ustalenia) | najlepsza cena i jakość mięsa, minimalne zamówienie, dostawa 1–2 razy w tygodniu |
| Piekarnia | (nazwa do ustalenia) | świeże bułki i pita, dostawa codziennie rano, osobna ilość na każdy dzień |

Składniki i terminy ważności: [[Menu i składniki]].

## Giełda
Nie implementujemy – zajmie się nią kolega.

## Banki
Prawdziwe banki, każdy specjalizuje się w czymś innym. Sześć budynków – na mapie układają się w dwa równe rzędy po trzy.

| Bank            | Specjalizacja       | W praktyce                                                                         |
| --------------- | ------------------- | ---------------------------------------------------------------------------------- |
| Crédit Agricole | kredyt na start     | szybka decyzja, kredyt dla firmy bez historii, wyższe oprocentowanie               |
| PKO BP          | kredyt inwestycyjny | najniższe oprocentowanie dużych kwot, wymaga zastawu (lokal, sprzęt), długa spłata; dostępny od wzięcia lokalu, także na zakup lokalu w tej samej rundzie (kupowany lokal jako zastaw) |
| Pekao           | leasing sprzętu     | sprzęt kuchenny w ratach, raty w kosztach                                          |
| ING             | lokaty              | najlepsze oprocentowanie lokat, lokaty tygodniowe i dłuższe                        |
| mBank           | tanie konto firmowe | najniższe opłaty za konto, przelewy i terminal płatniczy                           |
| Santander       | limit w koncie      | kredyt odnawialny uruchamiany automatycznie przy braku gotówki, drogi              |

- Specjalizacje i liczby są robocze – przed kalibracją trzeba sprawdzić prawdziwe oferty.
- **Zastaw:** pod kredyt można zastawić lokal albo sprzęt; przy niespłaceniu bank go przejmuje.

## Lichwiarz Harpagon
- Pożyczka „na czarno” (nawiązanie do Harpagona ze „Skąpca” Moliera): od ręki, bez sprawdzania zdolności kredytowej, poza KPiR.
- **Rosnąca presja:** najpierw przypomnienia, potem odsetki karne co rundę, potem „wizyty” (szkody w lokalu, odpływ klientów, odejście pracownika).

## Biuro rachunkowe
- Kilka biur z różnymi ofertami (cena za dokument, ryczałt, obsługa kadr). Jedno należy do **Jakuba Klimka-Ślęzaka** (Biuro Rachunkowe J.K.Ś.).
- Biuro prowadzi za drużynę KPiR, VAT, ZUS i PIT, ale kosztuje.
- **Samodzielna księgowość** (uproszczona): drużyna sama wpisuje zapisy i deklaracje, a gra je sprawdza i pokazuje błędy. Błąd w deklaracji oznacza korektę i karę. Nad tabelą dokumentów jest instrukcja krok po kroku, jak samemu wypełnić KPiR i deklaracje.

## Parki
- Prawdziwe parki Lublina: Ogród Saski, Park Ludowy, Park Bronowicki, Park Rury, Ogród Botaniczny UMCS, Błonia pod Zamkiem, Zalew Zemborzycki.
- **W każdej rundzie jeden event**, ten sam dla wszystkich drużyn. Każda drużyna może go wybrać niezależnie od innych – eventów nie „podkrada” się tak jak pracowników czy lokali.
- Udział kosztuje **czas właściciela**, czasem też gotówkę albo porcje jedzenia.
- Skutki bywają opóźnione – inspiracja: gra „60 Seconds!”. Przykład: spotykasz bezdomnego, dajesz mu kebaba, a za dwie rundy przychodzi do ciebie pracować.

## Agencja pracy
- **Globalna pula pracowników** – ta sama dla wszystkich drużyn. Jak podkupisz pracownika kolegi, to pracuje dla ciebie.
- Trzy poziomy:

| Poziom                 | Koszt   | Kandydaci                                                         |
| ---------------------- | ------- | ----------------------------------------------------------------- |
| pracuj.pl (ogłoszenie) | tanio   | dużo, przeciętni, sam ich przebierasz (czas właściciela)          |
| Agencja pracy          | średnio | sprawdzeni, szybciej                                              |
| Headhunter             | drogo   | najlepsi; tylko headhunter może podkupić pracownika innej drużyny |

- Podkupienie: oferta dla cudzego pracownika → jego pracodawca może złożyć kontrofertę → jeśli pracownik przyjmie twoją ofertę, odchodzi po okresie wypowiedzenia (umowa o pracę) albo od razu (umowa zlecenie).
- Limit: najwyżej 3 nowych pracowników na rundę.

## Agencje reklamowe
- Kilka agencji, każda specjalizuje się w innych kanałach (ulotki i plakaty, internet i social media, radio i billboardy, lokalne wydarzenia).
- Kampanie wybiera się z listy (jak w Revasie) – nie ma własnych kampanii.
- Reklama działa podwójnie: **poszerza pulę klientów** w strefie i **odbiera klientów** konkurencji.
- Reklamy sobie przeszkadzają: jeśli kilka drużyn używa tego samego kanału w tej samej strefie (np. wszyscy rozdają ulotki), każda z tych reklam działa słabiej.

## Nowe elementy
- **Ubezpieczyciel** – polisy na lokal, sprzęt i OC; zmniejszają skutki wypadków ([[Prawidła świata]]).
- **Urząd / Sanepid** – rejestracja firmy, zgoda na otwarcie lokalu, kontrole (higiena, przeterminowany towar), mandaty.
- **Kasyno** – zasady poniżej.

### Kasyno (tajne)
- Nie ma go na mapie ani w menu. Odblokowuje się **tylko na jedną rundę**, gdy drużyna dostanie zaproszenie z losowego eventu.
- Event z zaproszeniem nie może niczego sugerować o kasynie (np. „Nieznajomy wręcza ci wizytówkę z adresem i godziną”).
- **Mistrz gry ma nie mieć pojęcia, że kasyno istnieje:** kasyna nie ma w panelu mistrza gry, w podglądzie drużyn, w rankingu, w eksporcie ani w instrukcji dla mistrza gry.
