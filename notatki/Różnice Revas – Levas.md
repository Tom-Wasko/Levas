[[Główny obraz]] · [[Ustalenia gry]] · `archiwum/Plan implementacji.md`

# Różnice Revas – Levas

Porównanie lokalnego Revasa (`revas_26/revas_gra`) z Levasem. To krok 1 z [[Plan działania]].

## Co zostaje z Revasa
| Element                                                                                  | Jak w Levasie                                                        |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Rundy: decyzje → „Wyślij decyzje” → przeliczenie rundy                                   | zostaje, ale runda to tydzień, nie miesiąc                           |
| Stan gry = konfiguracja + ziarno + decyzje (event sourcing)                              | zostaje – pozwala cofnąć rundę i odtworzyć każdą grę                 |
| Zakładki, przełącznik Decyzje / Wyniki, nawigacja po rundach                             | zostają do kroku 8 (potem mapa)                                      |
| Stopniowe odblokowywanie zakładek                                                        | zostaje, z harmonogramem w tygodniach; mistrz gry może go zmienić    |
| Karta wyników: iloczyn 5 wskaźników + karta skumulowana                                  | zostaje, wskaźniki dostosowane do kebabu                             |
| Lista błędów przed wysłaniem decyzji                                                     | zostaje, z nowymi regułami                                           |
| Kandydaci z gwiazdkami, płaca, umowa o pracę / zlecenie, premie, zadowolenie pracowników | zostaje, w globalnej puli                                            |
| Magazyn FIFO, dostawcy z ceną i jakością (1–3★)                                          | zostaje, ale składniki mają terminy ważności                         |
| Reklama wybierana z listy                                                                | zostaje, ale poszerza pulę i odbiera klientów; kanały się zagłuszają |
| Boty grające tym samym API co gracz, deterministyczne (ziarno)                           | zostają, z poziomami trudności                                       |
| Analiza „co jeśli” (podgląd skutków decyzji)                                             | zostaje, dla nowego silnika                                          |
| Parametry niepewne w pliku danych z opisem źródła                                        | zostaje (YAML zamiast `zalozenia.json`)                              |

## Co się zmienia
| | Revas | Levas |
|---|---|---|
| Branża | klub fitness / biuro podróży | kebab |
| Runda | miesiąc, 10 rund | tydzień, domyślnie 18 rund, 2–3 rundy na tydzień rzeczywisty |
| Kapitał startowy | 40 000 zł | 40 000 zł |
| Forma prawna i podatki | CIT 19%, rozliczenie miesięczne | JDG: KPiR, VAT, ZUS, PIT, rozliczenie tygodniowe |
| Rynek | firmy nie dzielą puli klientów | wspólna pula klientów w każdej strefie Lublina |
| Oferta | usługi z katalogu | stała lista dań + jakość składników ([[Menu i składniki]]) |
| Inwestycje | stanowiska i sprzęt na stanowisko | lokale (3 typy, czas budowy) i sprzęt kuchenny |
| Zasoby | bez terminów ważności | składniki z terminami ważności, straty |
| Dostawcy | 3–6 fikcyjnych | dyskonty, hurtownie, producent mięsa – prawdziwe marki |
| Bank | jeden bank, automatyczny kredyt odnawialny | 6 banków ze specjalizacjami + lichwiarz Harpagon |
| Biuro rachunkowe | jedno, opłata za dokument | kilka biur albo samodzielna księgowość sprawdzana przez grę |
| Kandydaci | jedna pula, tylko zatrudnianie | globalna pula, 3 poziomy agencji, podkupywanie z okresem wypowiedzenia |
| Losowość | prawie deterministycznie (reklamacje) | eventy w parkach, rzadkie wypadki, kalendarz miejski |
| Gra wieloosobowa | przez GitHub | serwer, logowanie Microsoft / własne, drużyny 1–4 osób |
| Technologia | Flask, dataclasses, kwoty jako float | Django, SQLite, pydantic, kwoty w groszach ([[Technologia]]) |
| Algorytmy popytu | dopasowane do danych z oficjalnych gier | nowe, z innym balansem |

## Co jest nowe
- Lokale: globalna pula, 3 typy, czas budowy, najem i kupno, licytacje, przejęcia z okresem wypowiedzenia.
- Strefy Lublina i popyt ze wspólnej puli.
- Terminy ważności składników.
- Banki ze specjalizacjami, zastaw, Harpagon.
- KPiR i VAT, samodzielna księgowość.
- Agencja pracy (pracuj.pl / agencja / headhunter), podkupywanie, kontroferty.
- Parki z eventami, czas właściciela.
- Promocje z listy z ozdobną nazwą.
- Rzadkie wypadki i ubezpieczyciel, Urząd / Sanepid.
- Handel między drużynami, kalendarz miejski.
- Panel mistrza gry, logowanie.
- Ukryte dodatki – [[Elementy mapy]].

## Czego nie przenosimy
- Z Revasa: kalibracji na danych z oficjalnych gier (`kalibracja/`, raporty ATH i ABC), importu stanu prawdziwej gry (`import_stanu.py`), gry przez GitHub (`multiplayer/`).
- Ze starego Levasa (`Pulpit/Levas`): własnych kampanii reklamowych, głosowania, własnych receptur.
- Giełdy – zajmie się nią kolega.
