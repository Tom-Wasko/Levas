[[Plan działania]] · [[Główny obraz]] · [[Ustalenia gry]] · [[Technologia]]

> **Nieużywany od 28.10.2026 – archiwum.** Kroki 1–4 są zrobione (wszystkie zadania F, P i Q odhaczone w `POSTEP.md`). Aktualny plan: [[Plan optymalizacji]].

# Plan implementacji – kroki 1–4

Plan technicznej części [[Plan działania]]: od opisu projektu do pełnej gry gotowej do kalibracji. Pełna mapa, układ UI i ilustracje (kroki 8–10) oraz kalibracja (krok 5) są poza tym planem; w 3a powstaje tylko prototyp mapy (F3a.3).

## 1. Cel i ustalenia
- **Cel kroków 1–4:** grywalny Levas w przeglądarce – drużyny i boty prowadzą kebaby na wspólnym rynku Lublina przez 26 tygodni, z prawdziwą księgowością JDG i kartą wyników Revasa. Wygląd: zakładki w stylu Revasa.
- **Rdzeń = silnik lokalnego Revasa** (`revas_26/revas_gra/silnik`). Model gry Revasa jest rozbudowywany o nowe mechaniki. Gotowe moduły starego Levasa (`Pulpit/Levas/levas_gra`) są **przenoszone, ale przepisywane** pod model Revasa (p. 3.1).
- **Przy sprzeczności wygrywają nowe ustalenia**, nie zachowanie starego kodu. Przykłady: menu ze stałej listy (stary Levas miał własne receptury), reklama z listy (stary: własne kampanie i głosowanie), limity 3 pracowników na rundę i lokal co 3 rundy (stary: inne), krótsze czasy budowy.
- Wszystkie parametry: [[Ustalenia gry]]. Zasady świata: [[Prawidła świata]], [[Elementy mapy]], [[Menu i składniki]].
- Kod: `Pulpit/Revas/Levas/gra`. Technologia: [[Technologia]].

## 2. Źródła
| Źródło | Co z niego bierzemy |
|---|---|
| `revas_26/revas_gra` (silnik ok. 2100 linii, serwer, zakładki JS, testy) | rdzeń: przebieg rundy, event sourcing, model firmy, kandydaci, operacje, magazyn FIFO, karta wyników, boty, „co jeśli”, zakładki |
| `revas_26/revas_gra/WIEDZA_O_GRZE.md`, `PLAN_IMPLEMENTACJI.md` | zasady Revasa, harmonogram odblokowań, format planu |
| `Pulpit/Levas/levas_gra` (silnik ok. 15 400 linii, 464 testy, dane YAML) | moduły do przeniesienia (p. 3.2), dane (strefy, lokale, sklepy, menu, banki, biura, podatki 2026, parki, kalendarz), scenariusze testowe |
| `Pulpit/Levas/LEVAS` (notatki starego projektu) | opisy mechanik do sprawdzenia przy przenoszeniu |
| `STACK.md` | technologia i konwencje ([[Technologia]]) |
| `Levas/notatki` | ustalenia tego projektu |

## 3. Architektura
Pełny opis: [[Technologia]]. Najważniejsze:
- Silnik w czystym Pythonie, bez Django. Django daje logowanie, bazę, panel mistrza gry i widoki JSON dla zakładek Revasa.
- **Event sourcing jak w Revasie:** w bazie są konfiguracja gry, ziarno i decyzje drużyn. Stan rundy N to przeliczenie rund 1…N. Migawki stanu są tylko pamięcią podręczną. Cofnięcie rundy = usunięcie decyzji od tej rundy.
- Kwoty w groszach (`int`), losowość z nazwanych strumieni PCG64, liczby gry tylko w `dane/*.yaml`.

### 3.1 Co znaczy „stary stan Levasa”
W starym projekcie cały stan gry opisuje jeden plik **`silnik/stan.py` (827 linii)**: drzewo klas pydantic `StanGry` → `Firma` → `LokalFirmy`, `Pracownik`, `Ksiegi` (`ZapisKPiR`, `ZapisVAT`), `Kredyt`, `Lokata`, `Kampania`, `Promocja`, `Partia`, `PozycjaMenu`, `OfertaNajmu`, `OfertaPodkupienia`, `Kontroferta`, `SesjaKasyna` i inne. **Każdy stary moduł czyta i zapisuje właśnie te klasy**, więc żadnego nie da się po prostu skopiować obok silnika Revasa – Revas ma własny, mniejszy model (`silnik/model.py`: `Firma`, `Pracownik`, `Stanowisko`, `Kredyt`, `Lokata`, `StanGry`).

Wybrana opcja (2): **model Revasa jest bazą** i rośnie o nowe klasy (lokal, partia składnika, zapis KPiR i VAT…), wzorowane na `stan.py`, ale dodawane dopiero wtedy, gdy przenosimy moduł, który ich potrzebuje. Stary moduł przenosi się tak:
1. przeczytać moduł i jego testy w starym projekcie,
2. dodać do modelu Revasa brakujące pola i klasy (tylko potrzebne),
3. przepisać logikę na nowy model i nowe ustalenia,
4. przenieść testy i scenariusze liczbowe (co do grosza), poprawić je tam, gdzie ustalenia się zmieniły.

### 3.2 Przenoszone moduły starego Levasa
| Stary moduł | Krok | Uwagi |
|---|---|---|
| `losowosc.py`, `pieniadze`, `dane.py`, `schematy.py` (część) | F2 | fundament: strumienie losowe, grosze, wczytywanie i walidacja YAML |
| `lokale.py`, `koniec_najmu.py` | F3a, F3b | 3 typy lokali, krótsze czasy budowy, limit co 3 rundy |
| `popyt.py`, `operacje.py` | F3a | wspólna pula strefy, wybór lokalu, dni w tygodniu |
| `menu.py`, `swiezosc.py` | F3a | tylko stała lista dań, bez własnych receptur i porcji |
| `zakupy.py`, `sprzet.py`, `srodki_trwale.py` | F3a | dostawcy, sprzęt, amortyzacja |
| `pracownicy.py`, `agencja.py`, `podkupienie.py`, `oferty.py` | F3a | 3 poziomy agencji, limit 3, kontroferta, okres wypowiedzenia |
| `bank.py`, `lichwiarz.py`, `zaleglosci.py` | F3a | 6 banków ze specjalizacjami, Harpagon z rosnącą presją |
| `ksiegowosc.py`, `rozliczenie.py`, `biuro.py` | F3a | KPiR, VAT, ZUS, PIT – co tydzień; samodzielna księgowość |
| `zdarzenia.py`, `awarie.py` | F3b | 1 event w parku na rundę, rzadkie wypadki, ubezpieczenie |
| `marketing.py`, `promocje.py` | F3b | bez własnych kampanii i głosowania |
| `kasyno.py`, `handel.py`, `kalendarz.py` | F3b | kasyno ukryte przed mistrzem gry |
| `ocena.py`, `boty.py` | F4 | łączone z kartą i botami Revasa |
| **nie przenosimy:** `glosowanie.py`, `akcje.py`, `stan.py`, `schematy.py` (całość), `widoki.py`, `dynamika.py`, `eventy_mg.py`, `korekty_mg.py` | – | zastąpione modelem i API Revasa albo usunięte ustaleniami; `dynamika.py` i decyzje mistrza gry – do sprawdzenia przy F3b |

## 4. Przebieg rundy (tydzień)
Kolejność w `silnik/runda.py`, rozbudowanej z Revasa:
1. **Decyzje** wszystkich drużyn i botów, walidacja (limity, lista błędów).
2. **Początek tygodnia:** kalendarz miejski, event w parku i odpowiedzi drużyn, wypadki, zaproszenia.
3. **Rynek pracy:** oferty, podkupienia, kontroferty, licytacje, koniec okresów wypowiedzenia.
4. **Lokale:** najem, kupno, licytacje, postęp budowy i urządzania.
5. **Zakupy:** sprzęt, wyposażenie, składniki (dostawy w dni dostaw).
6. **Dni 1–7** (dzień po dniu, bo świeże składniki żyją 2–4 dni): pula klientów każdej strefy → wybór lokalu → obsługa (kucharze, sprzęt, składniki FIFO) → utracona sprzedaż z przyczyną → wyrzucenie przeterminowanych partii.
7. **Koszty:** płace i ZUS, czynsz, raty, leasing, biuro, opłaty bankowe, ubezpieczenia, reklama.
8. **Księgi:** zapisy KPiR i VAT, rozliczenie tygodnia (PIT, VAT, ZUS) przez biuro albo sprawdzenie samodzielnej księgowości.
9. **Bank i Harpagon:** lokaty, raty, limit w koncie, presja Harpagona.
10. **Karta wyników** i raporty.

## 5. Krok 1 – opis projektu i różnice
| Zadanie | Wynik |
|---|---|
| F1.1 Uporządkowanie notatek | [[Główny obraz]], [[Elementy mapy]], [[Prawidła świata]], [[Zarys aplikacji]], [[Plan działania]], [[Artstyle]] – zrobione |
| F1.2 Różnice Revas – Levas | [[Różnice Revas – Levas]] – zrobione |
| F1.3 Ustalenia i menu | [[Ustalenia gry]], [[Menu i składniki]] – zrobione |
| F1.4 Technologia | [[Technologia]] – zrobione |

## 6. Krok 2 – start na bazie lokalnego Revasa
Cel: działająca gra „Revas o kebabie” – jedna firma i boty, rundy tygodniowe, stos Django. Nowych mechanik jeszcze nie ma.

| Zadanie | Co | Gotowe, gdy |
|---|---|---|
| F2.1 Kopia | `revas_gra` → `Levas/gra` **bez** `kalibracja/`, `multiplayer/`, `dane_zrodlowe/`, `zapisy/`, `import_stanu.py`, raportów ATH/ABC/eksperymentów; `git init`, `.gitattributes`, `pyproject.toml`, ruff | `test_mechaniki.py` i `test_zasady_rund.py` przechodzą w nowym miejscu |
| F2.2 Django | projekt `levas/` i aplikacje `gry/`, `api/`, `panel_gracza/`; trasy z `serwer/app.py` przeniesione do widoków JSON; zakładki JS i Chart.js bez zmian; Flask usunięty | każda zakładka działa jak w Revasie |
| F2.3 Model na pydantic | dataclasses z `model.py` → modele pydantic (`extra="forbid"`), kwoty → grosze, `WERSJA_STANU` | testy własności: zapis → odczyt daje ten sam stan; to samo ziarno i decyzje = ten sam wynik |
| F2.4 Dane na YAML | `zalozenia.json` i `dane/*.json` → `dane/*.yaml` ze schematami i polem `zrodlo`; `python -m silnik.dane sprawdz` | w kodzie silnika nie ma liczb gry |
| F2.5 Losowość | strumienie PCG64 ze starego Levasa zamiast `losowosc.py` Revasa | test powtarzalności |
| F2.6 Przebranżowienie | usługi → dania ([[Menu i składniki]]), instruktorzy → kucharze, recepcja → kasa, sprzęt na stanowisko → sprzęt kuchenny lokalu (rożen, frytownica, lodówka), zasoby → składniki, dostawcy → tymczasowo 3 dostawcy jedzenia | zakładki pokazują kebab, nie fitness |
| F2.7 Rundy tygodniowe | miesiąc → tydzień: etat 40 h, płace i koszty tygodniowe, sezonowość tygodniowa, 26 rund, start 100 000 zł, jeden gotowy lokal na start | gra przechodzi 26 rund |
| F2.8 Panel mistrza gry (podstawowy) | `panel_mg/`: nowa gra (rundy, kapitał, boty tak/nie), ręczne zamknięcie rundy, podgląd drużyn; bez logowania (tryb deweloperski) | mistrz gry prowadzi grę z przeglądarki |

**Koniec kroku 2:** jedna drużyna + boty Revasa grają 26 tygodni; pytest i ruff na zielono. Algorytm popytu Revasa działa jeszcze tymczasowo.

## 7. Krok 3a – nowe funkcje: rdzeń
Cel: wspólny rynek Lublina z prawdziwą księgowością – minimum, w które da się grać w kilka drużyn.

| Zadanie | Co | Źródło | Gotowe, gdy |
|---|---|---|---|
| F3a.1 Konta | `konta/`: własny login + konto Microsoft (django-allauth), role uczeń / mistrz gry, uczeń widzi tylko swoją drużynę | nowe | test dostępu: uczeń nie odczyta cudzej drużyny |
| F3a.2 Drużyny | drużyny 1–4 osób, wiele firm w jednej grze, decyzje drużyny, zamknięcie rundy po decyzjach wszystkich albo przez mistrza | model Revasa (`StanGry.firmy`) | 4 drużyny + boty w jednej grze |
| F3a.3 Strefy i lokale | 10 stref, globalna pula lokali, 3 typy, najem i kupno, czas budowy 3–4 / 1 / 0 rund, lokal Tymka, limit co 3 rundy; **prototyp mapy miasta** (izometryczne SVG wg [[Artstyle]], strefy i budynki z [[Elementy mapy]]) obok zwykłego menu jako alternatywa – kliknięcie budynku otwiera jego zakładkę | `lokale.py`, `dane/mapa/` | lokal zajęty przez drużynę znika innym; z mapy da się dojść do każdej zakładki |
| F3a.4 Popyt strefowy | pula klientów strefy × kalendarz → wybór lokalu (cena, jakość, odległość, zadowolenie; reklama w F3b), dni w tygodniu, obsługa i utracona sprzedaż; zastępuje popyt Revasa | `popyt.py`, `operacje.py` + operacje Revasa | dwa lokale w jednej strefie dzielą klientów |
| F3a.5 Menu i świeżość | stała lista dań, jakość dania, partie, terminy w dniach, FIFO, chłodnia i zamrażarka, straty, mrożona pita jako zamiennik; raport sprzedaży, braków i strat dzień po dniu | `menu.py`, `swiezosc.py` | test: przeterminowana partia trafia do strat, nie do sprzedaży |
| F3a.6 Dostawcy i sprzęt | dyskonty, hurtownie, producent mięsa, piekarnia (codziennie); decyzja = plan dostaw na 7 dni (ilość na każdy dzień dostawy); odbiór osobisty, gazetki; sklepy budowlane; sprzęt kuchenny i amortyzacja | `zakupy.py`, `sprzet.py`, `srodki_trwale.py`, `dane/sklepy/` | zamówienie przychodzi w zaplanowany dzień; bułki z poniedziałku są wyrzucane we wtorek wieczorem |
| F3a.7 Czas właściciela | pula godzin na rundę, zużywana przez odbiór osobisty, pracuj.pl, parki | stary Levas | brak godzin blokuje decyzję na liście błędów |
| F3a.8 Agencja pracy | globalna pula, pracuj.pl / agencja / headhunter, limit 3, podkupienie tylko przez headhuntera, kontroferta, okres wypowiedzenia, licytacja pracownika | `agencja.py`, `podkupienie.py`, `oferty.py`, `pracownicy.py` + kandydaci Revasa | scenariusz: podkupiony pracownik odchodzi po 2 rundach |
| F3a.9 Banki | 6 banków ze specjalizacjami (w tym Crédit Agricole), konto, lokaty, kredyt na start, kredyt inwestycyjny z zastawem, leasing, limit w koncie, przejęcie zastawu | `bank.py`, `dane/finanse/banki.yaml` | każdy bank ma inną najlepszą ofertę |
| F3a.10 Harpagon | pożyczka poza KPiR, rosnąca presja, skutki zaległości | `lichwiarz.py`, `zaleglosci.py` | scenariusz presji krok po kroku |
| F3a.11 Księgowość JDG | KPiR, rejestry VAT, ZUS (ulga na start), PIT liniowy, rozliczenie co tydzień; zastępuje CIT Revasa | `ksiegowosc.py`, `rozliczenie.py`, `podatki_2026.yaml` | scenariusze liczbowe co do grosza |
| F3a.12 Uzgodnienie kasy | test hypothesis na losowych grach botów: konto + kasa = start + przychody − wydatki z KPiR ± VAT ± ruchy poza KPiR | nowe (wzór ze starego Levasa) | zgodność co do grosza w każdej rundzie |
| F3a.13 Biura i samodzielna księgowość | biura z ofertami (w tym J.K.Ś.); tryb samodzielny: drużyna wpisuje zapisy i deklaracje, silnik porównuje z poprawnymi, pokazuje błędy, nalicza karę | `biuro.py` | błędny zapis jest wykryty i opisany |
| F3a.14 Panel mistrza gry | zamykanie o ustalonej godzinie (komenda `zamykaj_rundy` z Harmonogramu zadań / crona), cofnięcie rundy, pauza, boty i poziomy, ranking, eksport, wgląd w drużyny | `panel_mg` + nowe | wszystkie funkcje z [[Zarys aplikacji]] |
| F3a.15 Limity | 3 pracowników na rundę, lokal co 3 rundy, podstawowe reguły listy błędów dla nowych decyzji | nowe | próba przekroczenia limitu jest odrzucona |

**Koniec kroku 3a:** 4 drużyny i boty grają 26 tygodni na wspólnym rynku, kasa zgadza się z KPiR, mistrz gry prowadzi grę z logowaniem.

## 8. Krok 3b – nowe funkcje: reszta
| Zadanie | Co | Źródło |
|---|---|---|
| F3b.1 Parki | 1 event na rundę, ten sam dla wszystkich, koszt czasu właściciela, opóźnione skutki; eventy jako łańcuchy scen ([[Zdarzenia i historie]]) | `zdarzenia.py`, `dane/zdarzenia/parki.yaml` |
| F3b.2 Agencje reklamowe | kampanie z listy (agencja × kanał × strefa), poszerzenie puli strefy + odebranie klientów konkurencji, zagłuszanie przy kilku drużynach w tym samym kanale i strefie, nasycenie i wygasanie | `marketing.py` (bez własnych kampanii i głosowania), reklama Revasa |
| F3b.3 Promocje | promocje z listy + ozdobna nazwa (bez wpływu na wynik) | `promocje.py` |
| F3b.4 Licytacje i przejęcia lokali | kupno budynku z najemcą, wypowiedzenie 4 rundy, rozliczenie ulepszeń, remis = losowanie | `oferty.py`, `koniec_najmu.py` |
| F3b.5 Wypadki i ubezpieczyciel | rzadkie wypadki jako historie w 2–4 scenach z wyborem reakcji, ok. 80% komicznych ([[Zdarzenia i historie]]); zakładka Zdarzenia (Decyzje / Wyniki); polisy na lokal, sprzęt i OC | `awarie.py`, `dane/zdarzenia/losowe.yaml` |
| F3b.6 Urząd / Sanepid | rejestracja, zgoda na otwarcie, kontrole (przeterminowany towar, higiena), mandaty | `zdarzenia.py` |
| F3b.7 Kasyno | zaproszenie z losowego eventu bez sugestii, otwarte na 1 rundę; wygrane i przegrane w prywatnym portfelu właściciela, do firmy trafiają jako zwykła wpłata albo wypłata własna; ukryte przed mistrzem gry (widoki, ranking, eksport, dziennik zdarzeń), bez nalotów i wiadomości w mediach; wyłącznik w konfiguracji serwera | `kasyno.py` |
| F3b.8 Handel między drużynami | oferta → akceptacja → faktura w KPiR obu stron | `handel.py` |
| F3b.9 Kalendarz miejski | 26 tygodni od daty startu gry: święta, sesja, wakacje, wydarzenia; wpływ na pulę stref | `kalendarz.py`, `dane/kalendarz/` |

Każde zadanie kończy się testami i przejściem pełnej gry botów. Dla F3b.7 dodatkowy test: odpowiedzi API dla roli mistrza gry nie zawierają żadnych danych kasyna.

## 9. Krok 4 – dopasowanie funkcji Revasa do nowych
| Zadanie | Co |
|---|---|
| F4.1 Karta wyników | 5 wskaźników Revasa dla kebabu ([[Ustalenia gry]]), iloczyn, karta skumulowana; połączenie `karta.py` Revasa z `ocena.py` starego Levasa |
| F4.2 Lista błędów | reguły dla nowych decyzji: danie bez sprzętu, za mała chłodnia, cena poniżej kosztu składników, brak kucharza, brak pieniędzy na zamówienie, przekroczony limit, brak czasu właściciela, składnik przeterminuje się przed użyciem |
| F4.3 Odblokowywanie zakładek | harmonogram w tygodniach z YAML, edytowany przez mistrza gry dla każdej gry |
| F4.4 Boty | strategie Revasa (Tani masowy, Premium, Zrównoważony, Agresywny marketing, Naśladowca) przepisane na kebab, poziomy łatwy / średni / trudny (od prostych reguł do planowania zapasów, reklamy i przejęć); część logiki z `boty.py` starego Levasa |
| F4.5 „Co jeśli” | podgląd skutków decyzji na kopii stanu (`planowanie.py` Revasa); przy wspólnym rynku zakłada, że inne drużyny powtarzają decyzje z poprzedniej rundy |
| F4.6 Sprzątanie | usunięcie popytu Revasa (`rynek.py`), CIT, miesięcznej sezonowości i resztek fitness |
| F4.7 Zakładki | zakładki Revasa dla nowych funkcji: Lokale, Menu, Dostawcy, HR, Marketing, Finanse ▸ KPiR / VAT / Bank / Biuro, Parki, Handel; tylko funkcjonalnie – wygląd w krokach 9–10 |

**Koniec kroku 4:** pełna gra 26 tygodni z botami na trzech poziomach, karta wyników i lista błędów; `balans/symuluj.py` daje raport do kalibracji w kroku 5.

## 10. Czego nie robimy
- Giełda – kolega (`gielda/` zostaje pustym zaczepem).
- Własne kampanie reklamowe, głosowanie, własne receptury i porcje.
- Gra przez GitHub, kalibracja na danych z oficjalnego Revasa, import prawdziwej gry.
- Pełna mapa, układ UI i ilustracje – kroki 8–10 (w 3a tylko prototyp mapy).

## 11. Do decyzji później (nie blokuje kroków 2 i 3a)
- Serwer produkcyjny (hosting).
- Ile godzin czasu właściciela na rundę i czy zależy od liczby osób w drużynie.
- Nazwa producenta mięsa kebab.
- Gdzie na mapie kupuje się sprzęt kuchenny (propozycja: hurtownie gastronomiczne Stalgast i Hendi, są w danych starego Levasa).
- Co z udogodnieniami, wyposażeniem i szkoleniami Revasa (propozycja: udogodnienia dla pracowników, wyposażenie sali ze sklepów budowlanych, szkolenia kucharzy).

## 12. Ryzyka
- **Wielkość przenoszenia.** Stary silnik ma ok. 15 400 linii, a każdy moduł trzeba przepisać pod model Revasa. Krok 3a jest najdłuższy – przenosimy moduł po module, każdy z testami, w kolejności z tabeli.
- **Balans.** W starym Levasie na początku przegrywały wszystkie strategie. `balans/symuluj.py` uruchamiamy już od kroku 3a, żeby wcześnie wychwycić rozjazdy.
- **Tygodniowe rozliczenia** są świadomym uproszczeniem (naprawdę płace, ZUS i podatki rozlicza się co miesiąc). Warto to napisać w instrukcji dla uczniów.
- **Przepisy i stawki z pamięci** (KP, KC, u.z.n.k., ZUS, VAT) – do sprawdzenia przed kalibracją.
- **Prawdziwe marki i osoby.** Prawdziwe nazwy firm, Jakub Klimek-Ślęzak i Tymek to wybór autora. Przy publicznym serwerze warto mieć zgodę tych osób i nie używać logotypów marek ([[Artstyle]]).
- **Logowanie Microsoft** wymaga zarejestrowania aplikacji w Microsoft Entra ID (zwykle przez administratora szkolnych kont). Do tego czasu działa własny login.
- **Kasyno** to hazard (na wirtualne pieniądze) w grze dla uczniów, ukryty przed nauczycielem. Odkrycie go może zaszkodzić projektowi – dlatego jest wyłącznik w konfiguracji serwera.
- **Wydajność event sourcingu:** 26 rund × kilka drużyn × 7 dni w każdej rundzie. Migawki po każdej rundzie zapobiegają liczeniu wszystkiego od początku.
- **„Co jeśli” na wspólnym rynku** jest tylko przybliżeniem, bo nie zna przyszłych decyzji innych drużyn.
