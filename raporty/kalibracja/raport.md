# Raport końcowy kalibracji (B15, 7.11.2026, gałąź `kalibracja-b`)

Kalibracja B1–B14 według `notatki/Plan optymalizacji.md`, krok 5. Stan „przed” to tag `kalibracja-start` (29.10.2026,
po B4, opis w `stan_poczatkowy.md`), stan „po” to gałąź `kalibracja-b` po B14. Między nimi na main weszły też
zmiany zasad z części A (U1–U24) i przebudowa zakładek (Z2, Z4, Z5). Nie są one kalibracją, ale zmieniają liczby, więc
w tabelach „po” je widać. Szczegóły każdego kroku – `dziennik.md`, pomiary – `pomiary/`, propozycje dla autora –
`notatki_do_zmiany.md`.

Pomiary jak w B4: badana firma (bot) wśród rywali średnich, 18 rund, 6 firm, kapitał 40 tys. zł, 20 ziaren na
strategię. Karta to średni wynik działalności z rund 2…N. „Pary” to ta sama gra i ziarno z inną decyzją albo innym
poziomem badanej.

## 1. Cele planu – przed i po

| cel | przed (B4) | B5 (zatw. autor) | K (po części A) | po (B12–B14) | cel |
|---|---|---|---|---|---|
| pierwszy plus „jak człowiek” średniego w rundach 4–6 | 19/100 (w rundzie 2: 62) | 65/100 | 51/100 | 43/100 (reszta w rundzie 3, w 2: 0) | 4–6 |
| alarmy debetu wersji słabej | 17/100 | 8/100 | 0/100 | 1/100 (151 zł, przypadek graniczny) | 0 |
| dobra > średnia (pary) | 95/100 | 92/100 | 74/100 | 87/100 | ≥ 80% |
| słaba < średnia (pary) | 96/100 | 89/100 | 89/100 | 99/100 | – |
| karta słaba / średnia / dobra | 0,11 / 0,42 / 0,62 | −0,01 / 0,23 / 0,34 | 0,09 / 0,32 / 0,35 | 0,10 / 0,45 / 0,52 | – |
| majątek netto średniej | 115 tys. zł | 93 tys. zł | 99 tys. zł | 110 tys. zł | – |
| łatwy < średni < trudny (pary) | 88 / 93 | 83 / 88 | – | 99 / 84 (trudny < niemożliwy 100) | wyraźnie różne |
| każda strategia wygrywa w jakimś kontekście | tani i agresywny nigdy | – | – | tak (turniej B14) | tak |

Przebieg kontroli trudności (`pomiary/bNN_trudnosc`, 300 gier każda):

| po kroku | 1. plus w 4–6 | alarmy słabej | dobra > średnia | karta słaba / średnia / dobra |
|---|---|---|---|---|
| K (4.11) | 51 | 0 | 74 | 0,09 / 0,32 / 0,35 |
| B6 lokale | 33 | 0 | 86 | 0,07 / 0,28 / 0,35 |
| B7 menu i ceny | 37 | 0 | 87 | 0,06 / 0,29 / 0,36 |
| B8 zaopatrzenie | 43 | 0 | 90 | 0,06 / 0,29 / 0,37 |
| B9 ludzie | 43 | 0 | 88 | 0,11 / 0,38 / 0,46 |
| B10 marketing | 43 | 0 | 85 | 0,10 / 0,45 / 0,52 |
| B12 urzędy i polisy | 43 | 1 | 87 | 0,10 / 0,45 / 0,52 |

B11 i B13 nie zmieniły danych gry ani domyślnych strategii, B14 zmienił tylko poziom `trudny` – kontrola z B12
obowiązuje (potwierdzone: gry bazowe `b14_dobry` identyczne z `b12_trudnosc`).

**Czego nie osiągnięto:** pierwszy plus średniej w rundach 4–6 tylko w 43/100 gier (w pozostałych w rundzie 3).
Od B5 spadło to przez U20–U24 (K: 51) i B6 (konkurencja stref: 33). Dźwignia to rozruch nowego lokalu – liczba
z B5, którą zatwierdził autor, więc tylko propozycja („B6 – rozruch” w `notatki_do_zmiany.md`).

## 2. Strategie (poziom średni, 6 firm, 18 rund)

| strategia | karta przed (B4) | karta po (B14) | 1. miejsce w turnieju B14 |
|---|---|---|---|
| zrównoważony | 0,72 | 0,72 | krótka gra (10 rund) i tłok (8 firm) |
| premium | 0,73 | 0,64 | długa gra z małą konkurencją (13/20) |
| naśladowca | 0,60 | 0,63 | pojedyncze gry (do 5/20), zgodnie z rolą |
| tani | 0,32 | 0,58 | poziom trudny, 8 firm (10/20) |
| agresywny | 0,06 (alarmy 9/30) | 0,37 (bez alarmów) | poziom trudny, 5 firm (7/20) |

Rozrzut strategii zmalał z 0,06–0,73 do 0,37–0,72. Tani i agresywny przestały przegrywać zawsze: tani dostał kuchnię
dwóch miejsc (B7) i wyposażenie (B10), a agresywny – mniej udogodnień i jedno szkolenie (B9, B10). Zapas zamówień
1,2 (B8) usunął braki towaru wszystkich strategii.

## 3. Dominacje i hipotezy – przed i po

| | hipoteza (B1, A, K) | przed (B4/K) | po | co zmieniono |
|---|---|---|---|---|
| H1 | gra za łatwa | 1. plus w rundzie 2 w 62% | rundy 3–6, marża zob. pkt 4 | B5: pule stref, rozruch |
| H3, H27 | umowa zlecenie dominuje | 99% par, +9,8 tys. zł | −0,003…−0,008 karty, bez dominacji | B9: P1 – ZUS pracodawcy 20,48% na zleceniu |
| H4 | mBank dominuje | inne banki 5–7% par | dalej najtańszy, różnica 1–3 tys. zł, karta −0,02 | bez zmian – lekcja „porównaj opłaty”, mały wybór |
| H5 | e-Księgi24 dominuje | inne biura 3–6% | nieznacznie najlepsze (jks −0,4 tys. zł), samodzielnie +3 tys. zł | bez zmian (B12) |
| H6, H21 | drugi lokal zawsze / nigdy | B4 85% par; K −0,23 | opłaca się, bardziej w długiej grze; z kredytem +0,30 | B6: konkurencja stref, magazyn lokalu |
| H7, H25 | reklama ponad przepustowość | agresywny bez kampanii 100% | brak kampanii zawsze traci, emisje 3–15 ≈ | Z5 (emisje), B10: ceny kanałów |
| H8, H28 | jakość 3★ dominuje | 3★ +0,25 (12/12 par) | 3★ +0,05, 1★ −0,13 | B7: krzywa jakości |
| H9 | lokata bije gotówkę | nie mierzona | grosze (+0,1 tys. zł) | B11: boty z lokatą |
| H10 | Harpagon darmową dźwignią | nie mierzona | średnio traci (premium −11,8 tys. zł), czasem ratuje | B11: spłata częściowa bota |
| H11 | sprzęt pompuje kartę | nie mierzona | brak „nabijania” (B13, 35 wariantów) | Z1 (przed B4) |
| H12 | kupno lokalu bije najem | B6 ×1: 75% par | najem i kupno prawie równe; kupno na peryferiach −0,16 | B6: ceny kupna ×1,5 |
| H13, H29 | promocje | szkodzą taniemu i premium | z rabatem nadal przegrywają; zestaw premium +0,16 | B10: strategie botów; **propozycja B7** |
| H14, H26 | polisy | komplet +1,67 tys. zł, 82% | lekko ujemna wartość, mniejszy rozrzut | B12: składki |
| H15 | higiena podstawowa wystarcza | tak; „brak” = bankructwo | tak; „brak” po odbiorze −2,5 tys. zł (ryzyko) | B12: bot obniża po odbiorze |
| H16 | dyskont dominuje | nie mierzona | +0,03…+0,05 karty za ok. 10 h właściciela | bez zmian (B8) |
| H17 | łatwy agresywny bankrutuje | alarmy 4/8 | łatwy agresywny 12/20 alarmów (łatwy wolno), słaby bez | H17, B8 |
| H18 | premium × 1,2 lepsze | 0,69–0,96 wobec 0,34–0,49 (A) | 1,15–1,3 bez istotnej różnicy (+0,06 ± 0,07); ceny strategii blisko optimum | B6, B7 |
| H19 | „nic nie rób” bije słabych | −0,02 | −0,016; słaba nad zerem poza agresywną | decyzja autora: bez zmian |
| H20 | kredyt na koncie karze | 0,18 / 0,55 | bez celu −0,14, na drugi lokal +0,30 | U22; **propozycja B11** |
| H22 | wypłaty nie obniżają karty | – | opis w instrukcji | decyzja autora: bez zmian |
| H23 | płaca minimalna za słaba | +0,01 | dominuje u premium (+0,05, 6/6) | **propozycja B9** |
| H24 | dobra ≈ średnia | 74/100 | 87/100; agresywny dobry ≈ średni | **propozycja B14** |

Dominacje, które zostały (wszystkie opisane jako propozycje, bo naprawa to nowa mechanika albo liczba autora):
szerokie menu bez kosztu (menu 8 dań u premium +0,53…+0,74 karty), płaca minimalna u premium, promocje z rabatem
przegrywają, udogodnienia bez skutku przy uczciwej płacy, księgowość bez deklaracji +0,01 karty przy −6,6 tys. zł.

## 4. Realia (gra 6 botów średnich, 18 rund, ziarna 7 i 11, rundy 3–18, wszystkie firmy)

Ten sam skrypt (`skrypty/realia.py [poziom]`) na kodzie i danych z tagu `kalibracja-start` (przed) i z gałęzi po B14 (po), udziały w przychodzie
z KPiR. W nawiasie gra sześciu botów „jak człowiek – średni”.

| wielkość | przed | po | realia (B4) | ocena |
|---|---|---|---|---|
| marża netto | 18,8% (17,3%) | 21,6% (19,6%) | kilka do kilkunastu procent | **za wysoko**, wzrosła |
| składniki | 33,7% (34,1%) | 34,6% (35,4%) | 25–35% | w widełkach |
| praca (pensje + ZUS pracodawcy) | 20,0% (20,2%) | 19,6% (20,6%) | 25–35% | **za nisko**, bez zmian |
| czynsz | 3,5% (3,6%) | 4,0% (4,2%) | 8–15% | za nisko (czynsz w zł realny) |
| reklama | 3,6% (3,8%) | 1,3% (1,4%) | – | Z5: emisje, B10: ceny kanałów |
| szkolenia | 3,3% (3,6%) | 1,1% | – | B9: cena szkolenia za tydzień, nie za miesiąc |
| przychód firmy (1 lokal) na tydzień | 22,7 tys. zł (21,8) | 22,2 tys. zł (20,9) | mały kebab: kilkadziesiąt tys. zł / mies. | za wysoko |
| cena dania głównego po rabacie | 23,5 zł | 23,3 zł | 25–40 zł | dolna granica |
| dania główne na lokal dziennie | 119 (115) | 118 (111) | kilkadziesiąt do kilkuset | w widełkach |

B4 podawał marżę 19,0%, pracę 20,7% i czynsz 4,2% innym liczeniem; tabela wyżej porównuje jednym skryptem.

Wniosek: **gra dla botów jest dziś bardziej opłacalna niż w realiach i niż przed kalibracją**. Przychód lokalu
spadł o 2–4% (B5: pule ×0,9 i rozruch), ale koszty spadły bardziej: reklama i szkolenia kosztowały za dużo
(błędy cen poprawione w Z5 i B9), a boty kupują rozsądniej (zapas 1,2, wyposażenie, mniej udogodnień). Cele B5
liczone są dla jednej badanej firmy wśród rywali średnich – tam karta średniej wersji to 0,45, a pierwszy plus
wypada w rundach 3–6. Dźwignie marży to pule stref i rozruch (liczby B5) albo udział pracy (obsada i pensje
z U20) – zmiana wymaga zgody autora, propozycja w `notatki_do_zmiany.md` („B15 – marża wyżej niż realia”).

## 5. Zmiany parametrów (od tagu `kalibracja-start`)

391 zmienionych liczb w 13 plikach `gra/dane/` (bez pól `zrodlo`, `pewnosc`, `opis`, `nazwa`). Większość to nowe
struktury z części A i przebudowy (grupy klientów U24 – 193 wartości, cechy kandydatów U20 – 29, emisje reklamy Z5,
auto-dostawca Z4) – w tabeli zbiorczo. Każda zmiana ma powód w `zrodlo` albo w komentarzu przy liczbie w YAML.

### 5.1. Kalibracja (B5–B14)

| plik | parametr | było | jest | krok | powód (pomiar) |
|---|---|---|---|---|---|
| `mapa/popyt.yaml` | `strefy.*.pula` (10 stref) | 1,0 / 1,2 / 1,1 / 0,7 / 0,8 / 0,6 / 0,9 / 0,7 / 0,5 / 0,4 | × 0,9 | B5 | gra za łatwa (H1), zatwierdzone przez autora |
| `mapa/popyt.yaml` | `model.rozruch` | – | start 0,4, przyrost 0,1 | B5 | nowy lokal rusza od 40% popytu (zatw. autor) |
| `mapa/popyt.yaml` | `strefy.*.konkurencja` | – | 0,75 (Felin) … 1,4 (Centrum) | B6 | centrum dominowało; lokale miasta spoza gry (`b6_strefy3`) |
| `mapa/lokale.yaml` | `cena` 15 lokali | ≈ 40 czynszów (45–218 tys. zł) | × 1,5 (68–327 tys. zł) | B6 | kupno wygrywało z najmem w 75% par (`b6_kupno3`) |
| `zalozenia.yaml` | `popyt.wspolczynniki_jakosci` 1★ / 3★ | 0,616 / 1,0 | 0,55 / 0,82 | B7 | 3★ wygrywało 12/12 par (+0,25), 1★ ≈ 2★ (`b7_jakosc2`) |
| `boty.yaml` | `ustawienia.zapas_zasobow` | 1,05 | 1,2 | B8 | boty traciły 9% sprzedaży na brakach (`b8_zaopatrzenie`) |
| `boty.yaml` | `latwy`, `czlowiek_slaby.zapas_zasobow` | (1,05 z ustawień) | 1,05 | B8 | proste planowanie bez zapasu (przy 1,2 słaby bankrutował) |
| `podatki_2026.yaml` | `zus_pracodawcy_zlecenie` | – (0) | 0,2048 | B9 | P1, decyzja autora 29.10.2026 (H3) |
| `boty.yaml` | `szkolenia` zrównoważony / premium / agresywny | 0 / 2 / 2 | 1 / 1 / 1 | B9 | jedno szkolenie +0,02, drugie traci (`b9_po`) |
| `zalozenia.yaml` | `popyt.wyposazenie_nasycenie` | – (liniowo) | 3,0 | B10 | komplet wyposażenia +31% popytu, wygrywał zawsze (`b10_marketing`) |
| `mapa/reklama.yaml` | radio / degustacja / noc kebaba – `cena_emisji` | 180 / 110 / 400 zł (pierwsze ceny Z5) | 70 / 80 / 200 zł | B10 | przegrywały z każdym kanałem (`b10_kanaly`) |
| `boty.yaml` | `wyposazenie` zrównoważony / tani | 2 / 0 | 6 / 3 | B10 | komplet +0,06, tani +0,05 (`b10_po`) |
| `boty.yaml` | `udogodnienia` premium / agresywny | 9 / 6 | 3 / 3 | B10 | przy uczciwej płacy nic nie dają (+0,055 / +0,024) |
| `boty.yaml` | `promocje` premium / tani | karta stałego klienta / happy hours + studencka | zestaw / studencka | B10 | zestaw +0,16, bez happy hours +0,04 (`b10_promocje`) |
| `boty.yaml` | `tani.min_kuchnia` | 1 | 2 | B7 | kolejka zjadała połowę popytu (`b7_cena`) |
| `boty.yaml` | `rezerwa_po_sprzecie` | – | 10 000 zł | B6 | bot finansuje sprzęt ponad gotówkę kredytem bez historii |
| `zdarzenia/losowe.yaml` | składka lokalu / sprzęt (stała) / OC | 140 / 0 / 80 zł | 300 / 400 / 60 zł | B12 | odszkodowania 1,9× / 24× / 0,63× składki (`b12_polisy2`) |
| `zalozenia.yaml` | `karta_wynikow.skala` – progi słów | 0,1 / 0,7, 0,15 / 1,1, 0,56 / 0,67 | 0,2 / 0,9, 0,35 / 1,4, 0,54 / 0,64 | B13 | percentyle kart po kalibracji (80 gier mieszanych) |
| `boty.yaml` | `trudny.kolejny_lokal.gotowka` | 60 000 | 50 000 | B14 | trudny > średni 80 → 84/100 (`b14_trudny3`) |

Wagi karty wyników bez zmian (B13: Spearman karta ~ majątek 0,935, żadna wersja nie lepsza ponad szum).

### 5.2. Zmiany zasad z części A i przebudowy (nie kalibracja – decyzje autora i projekt)

| plik | co | krok |
|---|---|---|
| `zalozenia.yaml` | `karta_wynikow.wskaznik_zadluzenia.wzor` – dług i gotówka w mianowniku | U22 (decyzja autora) |
| `zalozenia.yaml` | `pracownicy.odejscia` (próg zadowolenia 0,87, szansa 5% na setną, maks. 50%) | U20 |
| `kandydaci.yaml` | `cechy` – 10 ukrytych cech z wagami i mnożnikami | U20 |
| `boty.yaml` | `dba_o_ludzi` (podwyżka do 115%), `tylko_pomiar` usunięte z wersji „jak człowiek” | U20, Z5 |
| `mapa/klienci.yaml` | 8 grup klientów z koszykiem i opinie | U24 |
| `katalog.yaml` | zatrudnianie od tygodnia 1 | U23 (decyzja autora) |
| `zalozenia.yaml` | `lista_bledow.scal_dania_od`, `wnioski.dlaczego_min` | U5, U16 |
| `zalozenia.yaml` | `magazyn.przewoz`, `magazyn.auto_dostawca`; `dostawcy.yaml` i `mapa/budynki.yaml` – Auchan | Z2, Z4 |
| `mapa/reklama.yaml` | kampanie z emisjami i progami zniżek zamiast kosztu za rundy; `model.tempo_emisji` 0,265 | Z5 |
| `boty.yaml` | `emisje_kampanii`, `przerwa_kampanii` zamiast `min_sila_kampanii` | Z5 |
| `podatki_2026.yaml` | `vat.koszty` – nowe pozycje (przewóz, auto-dostawy) | Z2, Z4 |
| `zdarzenia/parki.yaml` | teksty dwóch scen – nowa nazwa zakładki | U4 |

### 5.3. `zrodlo` i `pewnosc`

Przy każdej liczbie z tabeli 5.1 `zrodlo` (albo komentarz w wierszu) podaje krok, starą wartość i pomiar. W B15
poprawione: `popyt.wyposazenie_nasycenie` – `pewnosc: skalibrowane` (było `zalozenie`, liczba wybrana pomiarem B10),
`boty.yaml` – komentarz przy `emisje_kampanii`/`przerwa_kampanii` (pomiar B10). `pewnosc` pozostałych liczb
kalibracji była już ustawiona; liczby wybrane pomiarem gier botów, a nie danymi z gier ATH, mają w `zrodlo` nazwę
pomiaru. Progi słów karty zostają `zalozenie` (progi zadłużenia z Revasa, boty nie mają długu).

## 6. Propozycje czekające na autora (`notatki_do_zmiany.md`)

| krok | propozycja | skutek w pomiarze |
|---|---|---|
| B6, Z1 | kupiony lokal w „rozwoju firmy” z wagą 0,5 | kupno podnosi rozwój 0,535 → 0,764; tani wygrywa kartą 28–29/30 par, majątkiem 25–27/30 |
| B5/B6 | rozruch nowego lokalu (liczba B5) | 1. plus w rundach 4–6: 43/100 |
| B6 | lokal niewyposażony – tańszy start bez kary za czas | po poprawkach −0,03…−0,06 karty (było −0,68), nie wygrywa |
| B6 | wykup najmowanego lokalu na kredyt | – |
| B7 | szerokie menu bez kosztu (koszt kuchni na danie) | menu 8 dań u premium +0,53…+0,74 karty |
| B7, B10 | promocje bez trwałego skutku – z rabatem przegrywają zawsze | żadna z rabatem nie bije braku promocji |
| B9 | płaca minimalna bez kosztu rotacji | premium +0,05 karty, 6/6 |
| B9 | szkolenie działa tylko w tygodniu zakupu | drugie szkolenie nic nie daje |
| B10 | udogodnienia bez skutku przy uczciwej płacy | premium 9 → 3 udogodnień +0,055 |
| B11 | kredyt bez celu obniża kartę mimo gotówki (U22) | kredyt 50 tys. zł bez celu −0,14 karty |
| B12 | mandaty skarbowe nie obniżają karty (Z1) | bez deklaracji +0,01 karty, −6,6 tys. zł |
| B14 | „jak człowiek – dobry” kupuje drugi lokal jak trudny (50 tys. zł) | karta dobrej 0,52 → 0,61, dobra > średnia 87 → 86 |
| B15 | marża wyżej niż realia (pule ×0,9, obsada albo pensje) | marża 21,6% wobec kilku–kilkunastu procent w realiach |

Poza tym: merge `kalibracja-b` → main (sesja „ufajnianie” na zlecenie autora) i pytanie z B4 o grę przy 4 firmach
(łatwiejsza: karta człowieka średniego 0,50 wobec 0,23 przy 6 – po B5).

## 7. Instrukcja gracza

Liczby z kalibracji, które gracz widzi w `gra/INSTRUKCJA.md`, zmieniały się w B9 (ZUS na zleceniu, premia i
szkolenie za tydzień) i B10 (wyposażenie) – PDF odświeżony wtedy (aed5a75, 8b0262d). B13 zmienił tylko tekst (H22:
wypłaty właściciela) – PDF odświeżony w B15. Ceny lokali, składki polis i ceny kanałów reklamy gracz widzi w grze,
instrukcja ich nie podaje.
