# Przebudowa zakładek i decyzje per lokal – ustalenia z autorem (2.11.2026)

Źródło: polecenia autora po teście gry (2.11.2026) i cztery serie pytań w sesji Claude Code.

## Interfejs
- **Kółka „i”**: na stronie zostają tylko nagłówki, tabele, pola decyzji i krótkie etykiety; opisy zakładek
  (`info`), akapity podpowiedzi i objaśnienia wzorów → dymek po najechaniu na kółko „i” obok tytułu / sekcji / pola.
- **Infografiki**: proste SVG w dymkach dla 5–8 najtrudniejszych mechanik (np. świeżość/FIFO, wybór lokalu przez
  klienta, nasycenie reklamy i progi zniżek, przepływ kasy i podatków); reszta dymków – tekst.
- **Usunąć pasek „podsumowanie”** (saldo po decyzjach / koszty decyzji / poważne braki / status decyzji) widoczny na
  każdej zakładce (`app.js: podsumowanie`).
- **Kalendarz miejski**: siatka miesiąca Pn–Nd, wiersz = runda (tydzień), wydarzenia jako kolorowe etykiety w dniach,
  bieżący tydzień podświetlony, strzałki ‹ › między miesiącami, szczegóły wydarzenia po najechaniu.
- **Bieżący tydzień**: czysta tabela – wiersze = dni (Pn–Nd), kolumny: data, wydarzenie, strefy z większą liczbą
  klientów, strefy z mniejszą, dania z większym popytem.
- **Usunąć zakładkę Analiza całkiem** – zakładka, zapytanie API, moduł `silnik/co_jesli.py` i jego testy.

## Decyzje per lokal
- Osobno dla każdego lokalu: **menu i ceny**, **zamówienia i magazyn** (partie, chłodnia), **HR, sprzęt
  i wyposażenie** (pracownicy, stanowiska, sprzęt, wyposażenie, udogodnienia).
- Wspólne dla firmy: promocje, higiena, bank, podatki, czas właściciela, handel, reklama itd.
- **Towar można przewozić** między własnymi lokalami: kurs kosztuje czas właściciela + trochę pieniędzy, partia traci
  1 dzień terminu. **Pracowników nie można przenosić.**
- Progi dostaw (darmowy dowóz hurtowni, minimum „Rożna”) liczone **razem dla firmy**.
- Zakładka **Lokale**: kafelki lokali drużyny na górze (wybrany aktywny) + podzakładki wybranego lokalu: Przegląd,
  Menu i ceny, Dostawy, Magazyn, Ludzie, Sprzęt. Wybór lokalu zostaje przy przechodzeniu między podzakładkami.
- **Kupowanie / najem lokali → Inwestycje.**

## Automatyczne zamawianie (auto-dostawca)
- Włączane dla **całego lokalu naraz** (lokal albo na auto-dostawach, albo zaopatrywany samemu).
- Gracz wpisuje ilość każdego składnika na tydzień i **płaci za całość wpisanej ilości**. Dostawca co rano przywozi
  tyle, ile lokal zużyje danego dnia (w lokalu nic się nie psuje); reszta leży u dostawcy i przechodzi na następny
  tydzień – **wysoki koszt przechowania** (zł/l/dzień); termin dalej biegnie. Za mało → sprzedaż stracona.
- Mniej korzystne niż samodzielnie: **abonament tygodniowy** za lokal, **opłata za przechowanie**, kupuje po
  nienajlepszej cenie („lubi Auchan”) i dolicza **prowizję 10%**.
- **Auchan** – nowy hipermarket na mapie dla wszystkich (szeroki wybór, ceny wyższe od hurtowni, odbiór osobisty za
  czas właściciela); auto-dostawca kupuje głównie tam.

## Reklama – emisje
- Struktura jak w REVAS (opis w `dokumentacja/WIEDZA_O_GRZE.md` §10 i reklama tradycyjna w `dane/katalog.yaml` –
  autor pozwolił wziąć ten mechanizm): kampania agencja × kanał × strefa ma **liczbę emisji w tej rundzie**; cena za
  emisję, **zniżki od progów** (np. 4–10 −15%, 11+ −30%, progi własne dla kanału), efekt nasyca się
  (1 − e^(−k·emisje)). „Trwa N rund” znika; po rundzie efekt wygasa jak dziś.

## Motywy
Zostają trzy: **Klasyczny** (menu poziome jak dziś), **Klasyczny – menu z boku** (po lewej pionowo grupy i sekcje;
kliknięcie grupy pokazuje jej podzakładki w pasku u góry treści) i **Grafik zmian**. „Talerze z kebabem” i „Kebab
nocą” – usunąć.

## Nowy układ zakładek (wariant A, ustalony w 3 etapach)
```
Mapa miasta
Wyniki            Karta wyników · Wnioski z rundy
── TWOJE LOKALE ──
Lokale            [kafelki lokali drużyny + porównanie lokali]
                  Przegląd · Menu i ceny · Dostawy i magazyn · Ludzie · Sprzęt
── MIASTO ──
Rynek             Klienci i strefy · Kalendarz · Konkurencja · Dostawcy (katalog, bez decyzji) · Rynek pracy
Parki i zdarzenia (osobna pozycja, znaczek, gdy czeka historia)
Marketing         Agencje reklamowe · Promocje
Inwestycje        Kupno i najem lokali · Licytacje i przejęcia · Środki trwałe
Handel z drużynami
── FIRMA ──
Firma             Czas właściciela · Urząd i sanepid · Ubezpieczenia
Finanse           Raport · Bank · Harpagon · Portfel właściciela
Księgowość        Biuro rachunkowe · KPiR · VAT · PIT i ZUS
Nocna 13          (ukryta, po zaproszeniu)
────────
Lista błędów
Wyślij decyzje
```
Podzakładki lokalu:
- **Przegląd** – kafelki z liczbami (klienci ostatnio i prognoza, utarg, koszty, zysk lokalu, chłodnia, obsada),
  braki tego lokalu z listy błędów (linki do podzakładek), umowa (najem/własność, czynsz, kaucja, wypowiedzenie,
  sprzedaż) i odbiór sanepidu; nad kafelkami lokali – tabela porównania lokali.
- **Menu i ceny** – dania, ceny, prognoza (dawne Menu + Sprzedaż).
- **Dostawy i magazyn** – zamówienia albo auto-dostawy, partie, chłodnia, przewóz towaru do innego lokalu.
- **Ludzie** – pracownicy lokalu, zatrudnianie do lokalu, szkolenia, udogodnienia.
- **Sprzęt** – stanowiska, sprzęt, wyposażenie.

## Kolejność wdrażania
1. Interfejs bez zmian silnika: pasek podsumowania, Analiza, motywy, kółka „i”, kalendarz.
2. Silnik per lokal (menu/ceny, zamówienia/partie, HR/sprzęt; przewóz towaru), boty, testy.
3. Zakładka Lokale z podzakładkami i nowe menu (wariant A); kupno lokali w Inwestycjach.
4. Auto-dostawca i Auchan.
5. Reklama z emisjami i progami zniżek.
6. Infografiki, instrukcja dla graczy (`gra/INSTRUKCJA.md`, PDF), opisy w `notebooklm\`.
