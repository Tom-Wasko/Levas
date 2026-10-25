# Lokalna gra REVAS Klub Fitness

Symulacja na wzór REVAS „Klub fitness” do rozgrywania i testowania rund na własnym komputerze: z botami, z innymi graczami
przez GitHub albo od stanu Twojej prawdziwej gry („co jeśli”).

## Uruchomienie

Kliknij dwa razy **`start.bat`**. Za pierwszym razem utworzy środowisko Pythona (`.venv`) i zainstaluje pakiety (potrzebny Python 3.11+).
Gra otworzy się w przeglądarce pod adresem **http://127.0.0.1:8765**. Zamknięcie czarnego okna kończy grę (zapis jest automatyczny).

Ręcznie (z folderu `revas_gra`): `.venv\Scripts\python -m serwer.app`

## Tryby gry

| Tryb | Jak zacząć |
|---|---|
| **Trening z botami** | Strona startowa → „Nowa gra”: Twoja firma + boty (strategie: Zrównoważony, Tani masowy, Premium, Agresywny marketing, Naśladowca). Domyślnie 12 rund od stycznia, 40 000 PLN na start. |
| **Kilku graczy na jednym komputerze** | Dodaj kilka firm „Gracz (ten komputer)”. Każdy wybiera swoją firmę, decyduje i klika „Wyślij decyzje”. Runda przelicza się, gdy wyślą wszyscy. |
| **Gra przez GitHub** | Patrz niżej. Każdy gra u siebie, decyzje idą przez wspólne repozytorium. |
| **Co jeśli (prawdziwa gra)** | Strona startowa → „Co jeśli: start ze stanu prawdziwej gry”. Przepisz stan swojej firmy z REVAS i ceny konkurentów, a potem testuj warianty decyzji w zakładce **Analiza**. |

## Jak się gra

Zakładki i ich kolejność są jak w REVAS: Oferta → Inwestycje (stanowiska, sprzęt, wyposażenie) → HR (zatrudnienie, udogodnienia,
szkolenia) → Dostawcy → Marketing → Sprzedaż → Finanse → Lista błędów → **Wyślij decyzje**. Przełącznik **Decyzje / Wyniki**
pokazuje wyniki poprzedniego miesiąca. Strzałki ‹ › przy miesiącu przełączają podgląd poprzednich rund.

- **Runda 1** (styczeń): nazwa, oferta (tylko Step, TBC, Zumba), stanowiska, bank, biuro. Sprzedaż zaczyna się w rundzie 2.
- **Runda 2**: sprzęt, zatrudnienie, zasoby, ceny. Nowe usługi można dodawać od rundy 3 (maks. 3 na rundę).
- Kolejne zakładki odblokowują się jak w grze: udogodnienia (r3), wyposażenie i karta skumulowana (r4), marketing tradycyjny (r5),
  internetowy (r6), szkolenia (r7).
- **Analiza** (dodatek): przewidywany wynik bieżącej rundy dla Twoich decyzji. Można zapisać kilka wariantów i porównać je obok siebie.
- **Wygląd** (lista „Wygląd” w nagłówku każdej strony): *Klasyczny REVAS*, *Talerze olimpijskie* (kolory działów jak talerze obciążeniowe, rundy jako talerze na sztandze), *Grafik zajęć* (menu z boku, oś rund jak nagłówek grafiku), *Siłownia nocą* (ciemny). Wybór zapamiętuje przeglądarka; można też dodać do adresu `?motyw=talerze` (albo `grafik`, `noc`, `klasyczny`). Pliki: `serwer/static/motywy/*.css`, przełącznik `serwer/static/motyw.js`.
- **Kredyt odnawialny** (przy tworzeniu gry): *jak w oficjalnej grze* – przychody i wydatki miesiąca jednocześnie, kredyt tylko na niedobór; *na bieżąco* – zakupy opłacane przed wpływem przychodów.
- **Wyślij decyzje → Cofnij ostatnią rundę**: w treningu można cofnąć rundę i spróbować inaczej (niedostępne w grze przez GitHub).

## Gra przez GitHub (różne komputery)

1. Jedna osoba zakłada **prywatne** repozytorium na GitHubie (może być puste, np. `revas-gra`).
2. Tworzy token: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → *Generate new token*.
   Repository access: *Only select repositories* → to repo. Permissions → Repository → **Contents: Read and write**. Kopiuje token
   i przekazuje go graczom (ustalenie: jeden wspólny token).
3. Każdy gracz na stronie startowej, w sekcji „Gra przez GitHub”, wpisuje repo (`właściciel/nazwa`), token i swoje imię → *Zapisz i sprawdź*.
   Token zapisuje się tylko lokalnie w `revas_gra/lokalne.json`.
4. Założyciel tworzy grę z zaznaczonym **„Gra przez GitHub”**. Firmy pozostałych graczy oznacza jako „Gracz na innym komputerze”,
   boty dodaje jak zwykle.
5. Pozostali klikają *Pokaż gry w repozytorium* → wybierają swoją firmę → **Dołącz**.
6. Każdy podejmuje decyzje i klika **Wyślij decyzje**. Gra sprawdza repo co 15 s. Gdy decyzje wyślą wszyscy, runda przelicza się
   sama na każdym komputerze. Boty liczy każdy komputer u siebie, a wyniki są identyczne.
   Pierwszy komputer zapisuje skrót wyników w repo, a kolejne go porównują. Różnica oznacza inną wersję gry lub danych.

Wszyscy muszą mieć **ten sam folder `revas_gra`** (te same dane i `zalozenia.json`). Decyzje w repo są jawne (zgodnie z ustaleniem).
Do zmiany komputera wystarczy dołączyć ponownie do tej samej firmy. Gra pobierze z repo wszystkie rundy.

## Pliki

| Plik / folder | Co zawiera |
|---|---|
| `WIEDZA_O_GRZE.md` | wszystkie ustalenia o mechanikach REVAS (źródło + pewność) |
| `POROWNANIE_ABC.md` | **sprawozdanie z testu** na prawdziwej grze A/B/C/Apex/Vela (REVAS online): dokładność, poprawione różnice w mechanice, kalibracja, co nadal odbiega |
| `SPRAWOZDANIE_ODTWORZENIA.html` | **sprawozdanie z analizy od zera i porównania gry lokalnej z przeszłymi grami** (ATH cały rok, A/B/C) – przed i po zmianach, z wykresami |
| `WYNIKI_EKSPERYMENTOW_ATH.md` | **wyniki eksperymentów na grze ATH (rundy 9–12)**: jak REVAS liczy reklamę, popyt, podział braków, kartę wyników |
| `PLAN_EKSPERYMENTOW_ATH.md`, `INSTRUKCJA_KLIKANIA_ATH.md` | plan eksperymentów i lista decyzji, które wykonano |
| `POROWNANIE_ATH.md` | wcześniejsze odtworzenie gry ATH (stan sprzed kalibracji online) |
| `PLAN_IMPLEMENTACJI.md` | plan i stan prac |
| `zalozenia.json` | **parametry niepewne** (popyt, reklama, karta wyników, losowość) – zmiana tu zmienia grę bez programowania |
| `dane/` | dane gry: usługi, sprzęt, zasoby, dostawcy, kandydaci, `katalog.json` (stanowiska, udogodnienia, media, banki, szkolenia…) |
| `silnik/` | silnik gry (Python): rynek, operacje, finanse, karta wyników, boty, import stanu |
| `serwer/` | serwer WWW i interfejs w przeglądarce |
| `multiplayer/` | gra przez GitHub (`github.py` – API, `sync.py` – wymiana decyzji) |
| `kalibracja/` | skrypty dopasowania parametrów do danych z gier (odczyt tabel z PDF-ów, KPiR, popyt, ceny dostawców) |
| `narzedzia/buduj_dane.py` | odtwarza pliki w `dane/` z `revas_26/dane` i materiałów |
| `testy/` | testy mechanik potwierdzonych na danych z gry i gry przez GitHub (`.venv\Scripts\python -m pytest testy`) |
| `zapisy/` | zapisane gry (pliki JSON: konfiguracja + decyzje; stan liczy się od nowa z decyzji) |

## Kalibracja (gdy dojdą nowe materiały)

```
.venv\Scripts\python kalibracja\zrzut_danych.py         # odczyt wszystkich PDF/KPiR z revas_26/materialy
.venv\Scripts\python kalibracja\kalibracja_popytu.py    # dopasowanie modelu popytu (wynik → zalozenia.json, sekcja popyt)
.venv\Scripts\python kalibracja\analiza_cen_dostawcow.py
.venv\Scripts\python kalibracja\odtworzenie_ath.py      # gra ATH w silniku vs oryginał
# dane z REVAS online (materialy/revas_online, zrzut: narzedzia/revas_online):
.venv\Scripts\python kalibracja\online_fitness.py       # zbiór danych firm gry A/B/C
.venv\Scripts\python kalibracja\decyzje_online.py       # decyzje 5 zespołów w formacie silnika
.venv\Scripts\python kalibracja\odtworzenie_abc.py      # gra A/B/C w silniku vs oryginał (POROWNANIE_ABC.md)
.venv\Scripts\python kalibracja\kalibracja_online.py    # wzory zadowolenia, rozwoju, mnożnik i jakość popytu
# kalibracja\wizualizacja_kalibracji.ipynb (kernel .venv): wykresy kalibracji popytu (krzywe ceny, kropki znormalizowane,
#   błąd na różne sposoby, własne parametry suwakami) + karta wyników i reklama; dane: kalibracja\zbior_obserwacji.py;
#   przełącznik fitness / wycieczki (9 gier biura podróży z materialy\revas_online), wybór w wizualizacja_kalibracji_wybor.json
.venv\Scripts\python kalibracja\reklama_biuro.py        # reklama w biurze podróży (tylko wskazówki, nie fitness)
.venv\Scripts\python kalibracja\reklama_ath.py          # reklama tradycyjna i internetowa – gra ATH (eksperymenty r9–r12)
.venv\Scripts\python kalibracja\popyt_ath.py            # struktura popytu – gra ATH (panel 3 firm × 11 miesięcy)
.venv\Scripts\python kalibracja\dane_fitness.py         # wspólny zbiór danych fitness (ATH + A/B/C, z botami) → dane_fitness.json
.venv\Scripts\python kalibracja\analiza_od_nowa.py      # analiza od zera: reklama, internet, popyt (warianty + walidacja krzyżowa)
.venv\Scripts\python kalibracja\porownanie_przed_po.py  # gra lokalna vs przeszłe gry, parametry przed i po analizie
# ath_jesien.py – decyzje ATH wrzesień–grudzień i boty z pełnego zrzutu (używa go odtworzenie_ath.py, 12 miesięcy)
# ustaw_zalozenia.py – zmiana parametrów zalozenia.json bez przeformatowania pliku
```

## Ograniczenia (ważne przy „co jeśli”)

Gra odtwarza mechaniki REVAS z danych i może się różnić od oryginału. Test na prawdziwej grze A/B/C (`POROWNANIE_ABC.md`):
przy prawdziwym popycie finanse zgadzają się co do złotówki w większości miesięcy, wykorzystanie pracowników co do 0,1 pkt proc.,
zadowolenie pracowników ±0,001. Popyt odbiega średnio o 5–6% na usługę, zadowolenie klientów o ±0,01–0,02. Najsłabiej:
rozwój firmy (±0,07), spadek popytu w listopadzie–grudniu (przyczyna nieznana), styczeń (brak danych), podział braków
zasobów (reguła z 2 miesięcy). Cały rok gry ATH odtwarza się z błędem popytu 4,6–6,0% na usługę i dochodem rocznym −0,6%
(`SPRAWOZDANIE_ODTWORZENIA.html`, `WIEDZA_O_GRZE.md` rozdz. 17).
Szczegóły i otwarte pytania są w `WIEDZA_O_GRZE.md`.
