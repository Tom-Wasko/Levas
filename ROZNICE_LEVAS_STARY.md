# Stary Levas a obecny – lista różnic (P20, 27.10)

Porównanie gałęzi `kod` repozytorium `Tom-Wasko/Levas-stary` (commit 76b19fe, „Sprawozdanie 2 – dzień”, fazy F0–F4.7
starego planu) z obecną grą w `gra/`. Kod starej wersji tylko przeczytany – nic z niego nie uruchamiano ani nie
kopiowano. To lista do decyzji: co warto przenieść później, a co zostało świadomie uproszczone.

## Podstawa – dwa różne podejścia

| | Stary Levas | Obecny Levas |
|---|---|---|
| Wzór | własny projekt „od zera” (dokumentacja `../LEVAS`) | Revas przeniesiony do Lublina, rozbudowany o mapę i nowe miejsca |
| Runda | tydzień, kalendarz 2027–2028 | tydzień, 18 rund od pon. 1.09.2025 do 4.01.2026, wrzesień – wprowadzenie |
| Decyzje | pojedyncze akcje (`wykonaj_akcje`), każda sprawdzana od razu | jeden plik decyzji na rundę (format Revasa), błędy na liście z zakładkami |
| Interfejs | strony Django z formularzami | panel w JS: zakładki Decyzje / Wyniki dla każdego elementu i mapa miasta |
| Pieniądze | int w groszach | float zaokrąglany do grosza |
| Logowanie | brak (tryb deweloperski) | konta, role (uczeń, mistrz gry), logowanie Microsoft |
| Czas właściciela | 60 h na tydzień | 20 h na rundę, zakładka Czas właściciela |

## Było w starym, nie ma w obecnym (kandydaci do przeniesienia)

1. **Receptury z konkretnych produktów** – gracz sam składał danie (`slot=produkt:ilość`, do 12 składników, jakość
   z produktów). Obecnie dania mają stały skład z `uslugi.yaml`, a gracz wybiera jakość składników.
2. **Grupy klientów** – 8 grup (studenci, uczniowie, biurowi, imprezowicze, rodziny, turyści, goście wydarzeń,
   podróżni) z własnymi preferencjami, koszyk (np. wegetarianie przenoszą udziały). Obecnie popyt strefowy:
   strefy mają opis klientów i sezonowość, ale bez osobnych grup w modelu.
3. **Godziny otwarcia i obsada na pory dnia** – gracz ustawiał godziny lokalu i grafik (kuchnia/kasa rano,
   w południe, wieczorem, nocki). Obecnie obsada liczona na godziny pracy w rundzie i popyt dzień po dniu.
4. **Dynamika pracowników** – zadowolenie każdej osoby (stawka, przeciążenie, sprzęt, klimatyzacja, szef na miejscu,
   premie), L4, rezygnacje, kradzieże z kasy (cecha „lepkie ręce” i monitoring), rozwój umiejętności, ukryte cechy
   (szybki, miły, perfekcjonista, lojalny, spóźnialski, wdzięczny, imprezowicz) ujawniane z czasem, reputacja
   pracodawcy. Obecnie: gwiazdki, zadowolenie pracowników jako wskaźnik karty wyników, wypowiedzenia w obie strony.
5. **Rodzaje umów** – umowa o pracę, zlecenie, student (różne koszty i warunki), limit 3 zatrudnień na tydzień.
   Obecnie jedna forma zatrudnienia z ZUS pracodawcy i limitem nowych pracowników na rundę.
6. **Zużycie i awarie sprzętu** – stan sprzętu w %, losowe awarie (przestój w konkretne dni), faktura serwisu,
   używany sprzęt w gotowych lokalach. Obecnie sprzęt ma gwiazdki i amortyzację, a „awarie” to rzadkie wypadki
   z historyjką i ubezpieczeniem (inny mechanizm).
7. **Oceny i opinie klientów** – czekanie w kolejce, satysfakcja, ocena lokalu i liczba opinii widoczna dla innych.
   Obecnie zadowolenie klientów z karty wyników działa na popyt kolejnej rundy, bez opinii.
8. **Upadłość i decyzje mistrza gry** – alarm przy kapitale poniżej −50 000 zł, egzekucja, wypowiedzenie najmu,
   przejęcie zastawu, dofinansowanie, pożyczka inwestora, umorzenie, likwidacja i restart firmy. Obecnie: kredyt
   odnawialny, zaległości i wizyty Harpagona, bez osobnej procedury upadłości.
9. **Lokale do zbudowania** – działka w dzierżawie z kontenerem albo pawilonem (budowa kilka tygodni), lokal
   niewyposażony z adaptacją i odbiorem, odstępne jako środek trwały. Obecnie: lokale gotowe, do wynajęcia albo
   kupienia, przetargi i przejęcia.
10. **Sklepy z minimum zamówienia i dniem dostawy** – dyskont, hipermarket, hurtownia, producent mięsa
    (minimum 300 zł), dostawa w wybrany dzień albo odbiór osobisty za czas właściciela. Obecnie dostawcy z cenami
    rundy, gazetkami i jakością, dostawa na rundę.
11. **Lichwiarz z taliami kart i nalotem policji** – poziomy długu z kartami zdarzeń, przejęcie sprzętu. Obecnie
    Harpagon ma podobną rolę (presja, wizyty), ale bez talii poziomów i nalotu.
12. **Zdarzenia z wyzwalaczami** – kalendarz / warunek / losowe / opisowe i 14 typów skutków. Obecnie: eventy
    w parkach (dla wszystkich te same), rzadkie wypadki w lokalu i kalendarz miejski – mniej typów, za to dłuższe
    historie z humorem.

## Jest w obecnym, nie było w starym

- Mapa miasta z budynkami i strefami (jako alternatywa dla menu), lokale w strefach, popyt strefowy.
- Karta wyników Revasa (wynik ekonomiczny, wynik działalności, zadowolenie klientów i pracowników, wskaźnik zadłużenia).
- Boty na czterech poziomach (łatwy, średni, trudny, niemożliwy) i strategie wybierane przez mistrza gry.
- Agencje reklamowe z kampaniami w strefach (suma kampanii +10–30% popytu), promocje na drzwiach lokali.
- Kasyno z klubem i wycofaniem się (z ironiczną „zasadą ciszy”), Harpagon, ubezpieczyciel z polisami.
- Konkurencja: ogólny obraz rywali dla wszystkich i detektyw z mapy (raport, ryzyko wpadki).
- Negocjacje i handel między drużynami na żywo w rundzie (oferta, kontroferty, akceptacja).
- Eventy w parkach z wielkimi historiami (3–4 na rundę, czas właściciela), wypadki z rosnącą szansą.
- Harmonogram odblokowań elementów (tydzień 1 przygotowawczy), panel mistrza gry (wstrzymanie, cofnięcie rundy,
  zmiana poziomów botów, ceny dostawców, automatyczne zakupy).
- Instrukcja dla uczniów w grze, w `INSTRUKCJA.md` i PDF.
- Logowanie kontami szkolnymi (Microsoft), gra przez wiele komputerów.

## W obu (inaczej rozwiązane)

| Element | Stary | Obecny |
|---|---|---|
| Podatki | VAT, PIT liniowy, składka zdrowotna, ZUS z ulgą na start | to samo: rejestr VAT, PIT liniowy, zdrowotna, ZUS (kwoty 2026) |
| Księgowość | biuro albo samodzielna mini-gra z celowymi błędami i kontrolą | biuro albo samodzielnie (ryzyko błędu, kara) |
| Bank | konto w jednym banku, kredyt na start, inwestycyjny z zastawem | kilka banków, lokaty i kredyty, kredyt odnawialny „na bieżąco” |
| Świeżość | partie FIFO, terminy, straty po koszcie zakupu, przesunięcia między lokalami | partie z terminami i psucie się towaru |
| Higiena / sanepid | wzór higieny (sprzątanie, sprzęt, kuchnia), kontrole | poziomy higieny, kontrole i mandaty, skargi z historyjek |
| Agencja pracy | 3 poziomy wyszukiwania, podkupienie z kontrofertą | kanały (pracuj.pl, agencja, headhunter), licytacje, podkupienie z kontrofertą |
| Handel | sprzęt, towar, lokal, cofnięcie przez MG | sprzęt, towar, lokal, negocjacje na żywo |
| Termin rundy | termin i automatyczne zamykanie | termin rundy i zamknięcie przez mistrza gry albo po decyzjach wszystkich |

## Propozycja (do decyzji)

Najwięcej grywalności przy niewielkim koszcie dałyby: (4) dynamika pracowników w okrojonej wersji – cechy
i zadowolenie osoby, (7) opinie klientów widoczne na mapie i (2) kilka grup klientów w strefach. Pozostałe punkty
to duże zmiany modelu (receptury, pory dnia, budowa lokali) – lepiej po kalibracji w kroku 5.
