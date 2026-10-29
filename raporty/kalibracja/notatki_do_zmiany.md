# Propozycje zmian w notatkach autora (kalibracja B)

Notatki (`notatki/`) zmienia się tylko za zgodą autora. Tu są proponowane teksty – do akceptacji albo poprawki.

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
