# Postęp

Postęp prac według [Planu implementacji](notatki/Plan%20implementacji.md). 1 commit = 1 zadanie (`F2.1: …`).

## Krok 2 – kopia Revasa i przebudowa pod Levas
- [x] F2.1 Kopia `revas_gra` → `gra/` (bez kalibracji, gry przez GitHub, importu stanu i raportów), pyproject + ruff, testy przechodzą
- [x] F2.2 Django zamiast Flaska: aplikacje `gry/` (modele Gra/Runda/Decyzja w SQLite), `api/` (widoki JSON), `panel_gracza/` (strony, zakładki JS bez zmian, komenda `graj`); CSRF w zapytaniach JS; testy API
- [x] F2.3 Model pydantic, grosze, `WERSJA_STANU` – modele stanu w pydantic (`extra="forbid"`), kwoty jako int grosze (pola `…_gr`, silnik liczy w złotych przez właściwości zaokrąglające do grosza), widok w złotych dla zakładek (`do_slownika`), testy własności (hypothesis): zapis → odczyt, to samo ziarno = ten sam wynik; wyniki gry botów bez zmian
- [x] F2.4 Dane w YAML ze schematami i `zrodlo` – `dane/*.yaml` (usługi, sprzęt, zasoby, dostawcy, kandydaci z parametrami losowania, katalog, boty, założenia), każdy plik/sekcja/parametr ze `zrodlo`; schematy pydantic (`silnik/schematy.py`) i odwołania między plikami: `python -m silnik.dane sprawdz`; liczby gry z kodu silnika (rynek pracy, strategie botów, dostawcy, limit stanowisk) przeniesione do danych, test pilnuje, żeby nie wróciły; wyniki gry botów bez zmian
- [x] F2.5 Nazwane strumienie losowości (PCG64) – `silnik/losowosc.py`: `strumien(ziarno, runda, cel, *klucze)` → `Generator(PCG64)` z pełnego skrótu SHA-256 (`SeedSequence`), cele w `CELE`; testy: wartości wzorcowe, niezależność od kolejności, różne klucze = różne liczby, losowość tylko z tego modułu (napisane od zera – kodu starego Levasa nie ma na dysku)
- [x] F2.6 Kebab zamiast klubu fitness – dane kebaba w `dane/` (8 dań z receptur z notatki „Menu i składniki”, kucharz i kasjer, sprzęt kuchni i kasy, 14 składników, 3 dostawcy jedzenia, rynek pracy, nazwy mediów i szkoleń); typy stanowisk `kuchnia`/`kasa` z nazwami i zawodami w danych (silnik bez nazw zawodów); zakładki, szablony i motywy mówią o daniach, kucharzach i kasie; dane Revasa zostały jako wzorzec `dane_revas/`, na którym przechodzą testy mechaniki; słownik nazw kod → gra w `gra/README.md`
- [x] F2.7 Rundy tygodniowe – kalendarz rund w danych (`rundy.kalendarz`: tydzień, 52 rundy w roku, start 5.10.2026); kebab: 26 rund, 100 000 zł, etat i sprzęt 40 h, gotowy lokal na start (`stanowiska.startowe`); kwoty miesięczne z danych silnik księguje na rundę (`na_runde`), oprocentowanie roczne / rundy w roku, sezonowość według miesiąca rundy, ceny dostawców losowane co tydzień; strona gracza: nazwy tygodni w nawigatorze i wykresach, koszty utrzymania „/ tydz.”, strona startowa z danych; Revas (`dane_revas/`) bez zmian – miesiące
- [x] F2.8 Podstawowy panel mistrza gry – `panel_mg/` pod `/mg/` (bez logowania): nowa gra (drużyny, rundy, kapitał startowy – nowa opcja gry `kapital_startowy`, boty tak/nie i wybór strategii), zakładki Decyzje (kto wysłał, zamknięcie rundy także bez decyzji wszystkich, cofnięcie, strony firm, plik gry; odświeżanie co 15 s) i Wyniki (ranking według średniej karty wyników, dochód, gotówka, zadłużenie, wykresy); `GET /api/gry/<id>/mg`; link z listy gier

## Krok 3a, 3b, 4
- [x] F3a.1 Konta – `konta/` (django-allauth): logowanie na każdej stronie, własny login (konta zakłada mistrz gry: komenda `konto`, panel Konta `/admin/`), konto Microsoft po ustawieniu `LEVAS_MS_*`; role mistrz gry (grupa `mistrz_gry`) / uczeń; drużyny `gry.Druzyna` (gra + firma + uczniowie); uczeń widzi tylko swoje gry i firmy, zarządzanie grą tylko dla mistrza gry; gra lokalna (`graj`) loguje się sama; test dostępu `test_uczen_nie_odczyta_cudzej_druzyny`

- [x] F3a.2 Drużyny – skład 1–4 uczniów (uczeń w jednej drużynie gry; pilnuje tego API i panel Konta), zakładka **Drużyny** w panelu mistrza gry (dopisywanie, usuwanie, konta uczniów z losowym hasłem, nowe hasło, druk), decyzje drużyny: kto zapisał / wysłał (`Runda.autorzy`), wersja decyzji – 409 przy jednoczesnej zmianie, odświeżanie strony drużyny co 20 s (`/stan`); test `test_cztery_druzyny_i_boty_w_jednej_grze`

- [x] F3a.3 Strefy i lokale, prototyp mapy miasta – mapa Lublina w danych (`dane/mapa/`: 10 stref, 38 lokali – gotowe, do urządzenia, działki, budynki instytucji); drużyna zaczyna bez lokalu i wybiera go: najem (kaucja + czynsz co tydzień) albo kupno, działka – budowa w ratach; wspólna pula lokali (konflikt w rundzie rozstrzyga kolejność rundy), kolejny lokal co 3 rundy; stanowiska tylko na miejscach w działających lokalach; czynsz i media zamiast stałego utrzymania lokalu; boty wynajmują gotowe lokale; zakładka **Lokale** (Decyzje + Wyniki) i **Mapa miasta** (izometryczna, obok menu: budynki → zakładki, lokale → najem/kupno); opcja gry `lokale` (bez – gotowy lokal jak w REVAS); testy `test_lokale.py`

- [x] F3a.4 Popyt strefowy – pule klientów stref (`dane/mapa/popyt.yaml`: pula, poziom cen i wrażliwość na cenę strefy, dni tygodnia, miesiące, kalendarz miejski z 9 wydarzeniami); klienci strefy wybierają lokal (cena względem strefy, jakość, odległość, zadowolenie, wyposażenie, reklama; opcja zewnętrzna – bary spoza gry); dwa lokale w strefie dzielą klientów; obsługa dzień po dniu w każdym lokalu (`silnik/popyt.py`); prognoza strefowa w zakładce Oferta; boty planują obsadę na szczyt tygodnia; nowa zakładka **Klienci i strefy** (Decyzje: prognoza lokali i dni, wydarzenia, potencjał stref; Wyniki: klienci dzień po dniu, skąd przyszli, podział stref); szacunek klientów na kafelkach lokali; testy `test_popyt.py`

- [x] F3a.5 Menu i świeżość – partie składników z terminem przydatności (`silnik/swiezosc.py`, `Firma.partie`): dostawa na wybrany dzień rundy, zużycie FIFO (najkrótszy termin), kosz po terminie (bułka z poniedziałku – we wtorek wieczorem), pojemność szafy chłodniczej i zamrażarki (`sprzet.yaml`: `przechowywanie`, `pojemnosc_l`; `zasoby.yaml`: `przechowywanie`, `termin_dni`, `miejsce_l`) – co się nie zmieści, przepada; mrożona pita i mrożone mięso jako zamienniki (−1★ jakości składnika); jakość dania z wag menu (`dane/mapa/menu.yaml`); danie bez składnika rano wypada z menu, połowa jego klientów bierze inne danie (`silnik/menu.py`); zwroty z partii; boty rozkładają dostawy na dni; zakładka **Magazyn i świeżość** (Decyzje: zajętość chłodni dzień po dniu, partie i terminy; Wyniki: dostawy/zużycie/straty dzień po dniu, kosz, dania wyłączone z menu), zamówienia na dni w zakładce Dostawcy, kolumna „Straty” w wynikach; ostrzeżenia na liście błędów; testy `test_swiezosc.py`

- [x] F3a.6 Dostawcy i sprzęt – 9 dostawców z rodzajem i zasadami (`dane/dostawcy.yaml`: `dostawcy`): piekarnia (dowóz codziennie), dyskonty Biedronka / Lidl / Stokrotka (odbiór osobisty – czas właściciela, limit opakowań dziennie, gazetka z promocjami losowana co tydzień), hurtownie Makro / Selgros / Eurocash (dni dostaw, płatny dowóz poniżej progu), producent mięsa „Rożen” (minimalne zamówienie, od rundy 3); zamówienie przychodzi w zaplanowany dzień, a w dzień bez dostaw jest odrzucane (czerwony błąd) – `silnik/dostawcy.py`: `zasady_dostaw`, `oferta_rundy`, `gazetki`; planowanie dostaw (boty, „Zamów”) w dni dostawcy, bez dyskontów i poniżej minimum; budynki dostawców na mapie; środki trwałe i amortyzacja (`silnik/srodki_trwale.py`, `Firma.srodki_trwale`): kupiony lokal i budynek 2,5% rocznie, grunt bez amortyzacji, zakupy od 10 000 zł 20% rocznie, tańsze od razu w koszty, sprzedaż – niezamortyzowana wartość w koszty; sklepy przy wyposażeniu (IKEA, OBI, Jula, Castorama) i park handlowy na mapie; zakładki: **Dostawcy** (Decyzje: dni dostaw, gazetki, limity, plan dostaw rundy; Wyniki: dostawy i opłaty za dowóz) i nowa **Inwestycje → Środki trwałe** (Decyzje: ewidencja po decyzjach, stawki; Wyniki: ewidencja na koniec rundy, odpisy w KPiR); testy `test_zasady_dostaw.py`, `test_srodki_trwale.py`

- [x] F3a.7 Czas właściciela – pula godzin na rundę (`zalozenia.yaml`: `operacje.czas_wlasciciela`, 20 h), `silnik/czas_wlasciciela.py`; zużywa ją odbiór osobisty w dyskontach (kolejno po dniach), dzień zakupów bez wolnych godzin jest odrzucony – czerwony błąd na liście błędów (zakładka Dostawcy); nowa zakładka **Czas właściciela** (Decyzje: plan godzin rundy; Wyniki: wykorzystanie i odrzucone decyzje), podpowiedź w Dostawcach; test `test_czas_wlasciciela.py`

- [x] F3a.8 Agencja pracy – `silnik/rynek_pracy.py`, `dane/kandydaci.yaml` (`agencja`): kanały rekrutacji pracuj.pl / agencja / headhunter (gwiazdki, opłata, mnożnik kosztu rekrutacji, czas właściciela, od rundy), wspólna pula kandydatów z licytacją (wyższa pensja, remis – losowanie), limit 3 nowych na rundę, podkupienie przez headhuntera z kontrofertą, okres wypowiedzenia wg stażu (`Pracownik.odchodzi`), zwolnieni wracają do puli; nowa zakładka **Rynek pracy** (Decyzje + Wyniki) w HR, wybór kanału w oknie zatrudnienia; test `test_rynek_pracy.py`

- [x] F3a.9 Banki – sześć banków z mapy (`dane/mapa/banki.yaml`, `silnik/banki.py`), każdy z inną najlepszą ofertą: Crédit Agricole (kredyt na start bez historii), PKO BP (kredyt inwestycyjny pod zastaw), Pekao (leasing sprzętu), ING (lokaty), mBank (tanie konto i terminal), Santander (limit w koncie); konto firmowe z terminalem (abonament + prowizja od płatności kartą), lokaty i kredyty w dowolnym banku, historia firmy, zastaw lokalu lub sprzętu i przejęcie po zaległościach, odsetki karne, leasing (sprzęt bez prawa sprzedaży do wykupu), debet ponad limit; zakładka **Finanse → Bank** w grze z lokalami (Decyzje + nowe Wyniki); boty wybierają najtańsze konto; test `test_banki.py`
- [x] F3a.10 Harpagon – lichwiarz z mapy (`dane/mapa/harpagon.yaml`, `silnik/lichwiarz.py`): pożyczka „na czarno” od ręki, bez sprawdzania zdolności i poza KPiR (gotówka i spłata tylko na rachunku z `poza_ksiegami`), jedna naraz, odsetki od całego długu co rundę; po terminie rosnąca presja z komicznymi historiami (Harpagon i Mistrz Jakub ze „Skąpca”): życzenia w rundzie terminu, przypomnienia, odsetki karne, wizyty; skutki zaległości w `silnik/zaleglosci.py` (szkody w lokalu – koszt w KPiR, odpływ klientów, odejście pracownika do puli) do użycia później przy ZUS/US; nowa zakładka **Finanse → Harpagon** (Decyzje + Wyniki) i kantor na mapie przy dworcu; test `test_harpagon.py` (scenariusz presji krok po kroku)
- [x] F3a.11 Księgowość JDG – `dane/podatki_2026.yaml` (schemat `PlikPodatkow`), ceny brutto → KPiR netto + rejestr VAT w `Ksiega` (`ksieguj` ze stawką, stawkami albo z reguł po opisie; sprzedaż dań 8%, napoje 23%, żywność 5%, opakowania i usługi 23%, usługi finansowe i płace bez VAT; środki trwałe – VAT naliczony, ewidencja netto; korekta VAT przy zwrotach), `silnik/rozliczenie.py` co rundę zamiast CIT: ZUS społeczny po uldze na start (26 rund), zdrowotna 4,9% z minimum, zaliczka PIT 19% narastająco, VAT z nadwyżką przenoszoną; ZUS pracodawcy 20,48%; `Firma.rozliczenie`; wyniki `rozliczenie` i `vat`, widok `podatki`; nowa zakładka **Finanse → Podatki** (Decyzje: parametry, stan rozliczeń, VAT z decyzji, stawki; Wyniki: rozliczenie rundy, zaliczka PIT narastająco, deklaracja VAT, rejestr), KPiR netto z zaliczką PIT i zdrowotną zamiast „Podatek”; test `test_ksiegowosc.py` (scenariusze co do grosza)
- [x] F3a.12 Uzgodnienie kasy – każda operacja rachunku ma rodzaj (`RODZAJE_OPERACJI`: KPiR, korekty, podatki, inwestycje, kredyty, lokaty, kaucje, Harpagon), koszty bez wydatku (`bez_gotowki`) i VAT od inwestycji oznaczone; `silnik/uzgodnienie.py` co rundę: początek + przychody − koszty + koszty bez wydatku + VAT należny − naliczony ± operacje poza KPiR = koniec, do tego KPiR ↔ operacje „kpir” i saldo ↔ suma operacji; wynik `uzgodnienie`; zwijana sekcja „Uzgodnienie kasy z KPiR” w **Finanse → Raport**; test `test_uzgodnienie.py` (hypothesis na losowych grach botów z kredytami, lokatami, Harpagonem, lokalami, sprzedażą sprzętu i zwrotami + scenariusz ze wszystkimi rodzajami). Znalezione i naprawione błędy: `ksieguj` zaokrąglał kwotę dwa razy (grosz różnicy przy końcówce ½ gr) – teraz raz, handlowo; `Rachunek.zapisz` liczył saldo z niezaokrąglonej kwoty; zwrot zasobów – brutto zaokrąglane wg stawek; zwrot zabierający ostatnią partię wywracał grę (`KeyError` w magazynie)

- [x] F3a.13 Biura rachunkowe i samodzielna księgowość – pięć biur z mapy (`dane/mapa/biura.yaml`: J.K.Ś., Pod Trybunałem, Pani Halinka, e-Księgi24.pl, Debet & Kredyt) z ryczałtem, limitem dokumentów, opłatą za dokument, minimum, kadrami (osoby w cenie, etat, zlecenie), ryzykiem błędu i OC – błąd biura bez OC kosztuje mandat (komiczne historie), z OC – zwrot; opłata liczona od liczby dokumentów rundy (`silnik/biuro.py`: `oplata`, `nalicz`, `najtansze`); **samodzielna księgowość**: po rundzie drużyna dostaje paczkę dokumentów z rachunku (faktury sprzedaży i zakupu, raporty kasy, listy płac, deklaracje ZUS, wyciągi, środki trwałe, operacje poza KPiR), w następnej rundzie księguje je do kolumn KPiR ze stawką VAT i składa deklaracje VAT, zaliczki PIT i składki zdrowotnej; silnik sprawdza: błędny zapis – wyjaśnienie, błędna deklaracja – korekta do poprawnej kwoty i mandat 200 zł, brak deklaracji – rozliczenie z urzędu i mandat 500 zł; ostatnia runda rozliczana od razu; do czasu złożenia deklaracji widok drużyny ukrywa KPiR, podatki i dochód netto rundy (także w podglądzie); boty wybierają najtańsze biuro; zakładka **Finanse → Biuro rachunkowe** (Decyzje: oferty z szacunkiem opłaty, dokumenty do zaksięgowania z podpowiedziami, podsumowanie i deklaracje; Wyniki: opłata biura albo sprawdzenie deklaracji i zapisów); test `test_biuro.py`, test uzgodnienia kasy obejmuje biura i samodzielne deklaracje (także błędne) oraz sprawdza, że dokumenty pokrywają cały rachunek rundy. Naprawione przy okazji: kredyt odnawialny uruchamiany na koniec rundy nie trafiał do dokumentów

- [x] F3a.14 Panel mistrza gry – **pauza** gry (drużyny nie zmieniają ani nie wysyłają decyzji, runda się nie zamyka – także z harmonogramu; cofnięcie działa); **zamykanie rund o stałej porze**: tygodniowe terminy (`Gra.harmonogram`, `gry/harmonogram.py`), runda zamyka się w pierwszym terminie po zamknięciu poprzedniej, komenda `manage.py zamykaj_rundy` (raz albo `--petla 60`; Harmonogram zadań Windows / cron w README), termin widoczny dla drużyn na pasku i w *Wyślij decyzje*, strona drużyny odświeża się po pauzie i zmianie terminu; **wgląd mistrza gry w drużyny uczniów tylko do odczytu** (API: 403, strona: komunikat; drużynę bez uczniów i grę lokalną prowadzi nadal mistrz gry); **poziom botów** (łatwy / średni / trudny, `dane/boty.yaml: poziomy`) przy zakładaniu gry i w trakcie (od następnej rundy) – na razie zapisany bez wpływu na decyzje (zachowanie poziomów w F4.4); **eksport do arkusza**: ranking i wyniki firm w rundach (CSV, średnik, przecinek dziesiętny, BOM – Excel); migracja `0004_prowadzenie_gry`; test `test_prowadzenie.py`. Odblokowywanie zakładek – w F4.3 (jak w planie)

- [x] F3a.15 Limity – `silnik/limity.py`: najwyżej 3 nowych pracowników na rundę (zatrudnienia + oferty podkupienia pracowników innych drużyn) i kolejny lokal co 3 rundy; **zapis decyzji z przekroczeniem jest odrzucony** (API 400 z opisem, strona pokazuje komunikat i wczytuje poprzednie decyzje), przyciski *Zatrudnij +* i *Złóż ofertę* sprawdzają limit od razu; lista błędów: niebieskie „wykorzystany limit nowych pracowników” i „kolejny lokal od rundy N” (czerwone – jak dotąd z przeliczenia, które nadal przycina nadmiar u botów i w starych zapisach); test `test_limity.py`. Pełna lista błędów dla nowych decyzji – w F4.2 (jak w planie)

**Krok 3a zakończony.**

- [x] F3b.1 Parki – `dane/zdarzenia/parki.yaml`: 14 historii w 7 parkach (12 komicznych, 2 poważne; 4 nowe parki na mapie), sceny z opcjami (koszt: godziny właściciela, gotówka, porcje jedzenia), opcja domyślna, ciąg dalszy za N rund z szansą; schematy z kontrolą grafu (każda ścieżka się kończy, brak scen nieosiągalnych); `silnik/zdarzenia.py`: od rundy 2 co rundę jedna historia dla wszystkich drużyn (kolejność losowana bez powtórzeń w cyklu), skutki – gotówka (bez VAT), mnożnik popytu, mniej godzin właściciela w kolejnych rundach, kandydat na rynku pracy tylko dla tej drużyny; boty wybierają losowo spośród opcji do 3 h; zakładka **Zdarzenia** (Decyzje: sceny i wybór reakcji, Wyniki: reakcje, skutki, „ciąg dalszy nastąpi”, trwające efekty, dziennik); lista błędów: niebieski brak wyboru, czerwony brak czasu właściciela (gra bierze opcję domyślną); test `test_zdarzenia.py`
- [x] Zmiany 26.10 (polecenia użytkownika): kapitał startowy 40 000 zł (dane, README, notatki); sortowanie tabel
  kliknięciem w nagłówek (rosnąco, malejąco, kolejność pierwotna; liczby w polskim zapisie, gwiazdki, puste na końcu;
  działa też w oknach, np. baza składników) i lista „Sortuj” w ofercie lokali; testy kupna lokali dostają jawnie
  kapitał 100 000 zł
- [x] Magazyn bez kosztu magazynowania i zwrotów (gra z lokalami; gra bez lokali i `dane_revas/` bez zmian):
  wynajęta chłodnia „Mroźnia u Mietka” – nadmiar ponad chłodnię/zamrażarkę lokalu przy dostawie (`swiezosc.przyjmij`,
  `Partia.wynajem`) za 1 zł/l z VAT 23%, termin krótszy o 2 dni, nie zajmuje miejsca w lokalu; kontrola sanepidu co
  rundę (`silnik/magazyn.py`, strumień „sanepid”): szansa 3% + za litry w wynajmie i złotówki przeterminowanego
  towaru, mandat 300–3000 zł poza KPiR (nowy rodzaj operacji „kary”, w uzgodnieniu kasy i biurze rachunkowym) i −7%
  popytu na 2 rundy, komiczne teksty kontroli w `dane/zdarzenia/magazyn.yaml`; historia „Pani Halina z banku
  żywności” (zapas z krótkim terminem ≥ 200 zł, szansa 40%; oddanie zabiera partie – strata z powodem „bank”, +3% lub
  +5% popytu, podziękowanie w następnej rundzie); zwroty i koszt magazynowania ukryte w zakładce Dostawcy;
  zakładka **Świeżość**: Decyzje – nadmiar do wynajmu dzień po dniu i ryzyko kontroli, Wyniki – wynajęte partie i
  karta kontroli; testy `test_magazyn.py`, `test_swiezosc.py`
- [x] F3b.2 Agencje reklamowe (gra z lokalami) – `dane/mapa/reklama.yaml`: 4 agencje na mapie (drukarnia „Papier
  Przyjmie”, „Lajk i Spółka”, „Fala Koziołka”, „Kozi Gród Events” – 2 nowe budynki), 8 kanałów (od rundy 3 część,
  od rundy 5 wszystkie), zasięg strefa albo całe miasto (radio), Noc Kebaba tylko w strefach akademickich, komiczne
  raporty agencji; `silnik/reklama.py`: zamówienie `kampanie: [{agencja, kanal, strefa}]` z góry (koszt × pula strefy,
  VAT 23%), kampania trwa N rund, poszerza pulę strefy (`popyt.pule`, korzystają wszyscy) i przyciąga mieszkańców
  strefy (`reklama_strefy` w `popyt.atrakcyjnosc`), zagłuszanie przez inne firmy z kampanią tego samego rodzaju
  w strefie, nasycenie przy powtórkach w oknie 4 rund, wygasanie ×0,5 po końcu; reklama tradycyjna i internetowa
  z Revasa wyłączona w grze z lokalami (zakładki ukryte, boty kupują kampanie ze strategii – `boty.yaml: kampanie`,
  `bufor_kampanii`, `min_sila_kampanii`); prognoza popytu uwzględnia kampanie; dane rynku: kto i za ile się
  reklamował; zakładka **Agencje reklamowe** w Marketingu (Decyzje: agencje, kanały, koszt i siła w wybranej
  strefie, konkurencja; Wyniki: raporty agencji, efekty kampanii, kampanie na mieście z wykresem); podzakładki
  ukryte w menu nie są pokazywane; test `test_reklama.py`

- [x] F3b.3 Promocje (gra z lokalami) – `dane/mapa/promocje.yaml`: 5 rodzajów (2 za 1 i zestaw z napojem na jedno
  danie; happy hours pn–czw, karta stałego klienta, zniżka studencka dla stref Akademickie i Politechnika – na całe
  menu), od rundy 2, najwyżej 2 naraz, każdy rodzaj raz; ozdobna nazwa drużyny (do 40 znaków, bez wpływu na wynik),
  po 2 komiczne teksty na rodzaj; `silnik/promocje.py`: decyzja `promocje: [{typ, nazwa, danie}]` (pełna lista,
  bez klucza – trwają), koszt włączenia netto + VAT 23% (KPiR – pozostałe), zmiana nazwy bez kosztu, zmiana dania =
  nowa promocja, danie zdjęte ze sprzedaży wyłącza promocję; w popycie (`popyt.podzial`) przyciąganie ×(1 +
  przyciąganie) u objętych klientów w dniach z maski, 2 za 1 – podwójne porcje (składniki i czas kuchni); przychód
  z rabatami, dopłaty do zestawu jako sprzedaż napojów (VAT napoju), napoje do zestawów w towarach; znużenie
  (przyciąganie spada co rundę) i przywiązanie (karta rośnie); dane rynku: promocje na mieście; boty ze strategii
  (`boty.yaml: promocje`, `min_obsluga_promocji` – bez wolnych mocy promocji nie włączają); zakładka **Promocje**
  w Marketingu (Decyzje: rodzaje z liczbami, włącz/wyłącz, nazwa, danie, konkurencja; Wyniki: komiczne teksty,
  liczby promocji, promocje na mieście); test `test_promocje.py`

- [x] F3b.4 Licytacje i przejęcia lokali (gra z lokalami) – zamiast planowanych `oferty.py` i `koniec_najmu.py` jeden
  moduł `silnik/przejecia.py`; zasady w `dane/mapa/lokale.yaml` (`licytacje_od_rundy` 4, `oferta_max` 3,
  `przejecia_od_rundy` 4, `wypowiedzenie_rund` 4, `ulepszenia_zwrot` 0,5, `przywrocenie_koszt` 0,3). Licytacja:
  ten sam lokal / budynek chce kilka drużyn → wygrywa najwyższa oferta względem ceny wywoławczej (pole oferty
  w decyzji `lokal`), remis – losowanie (strumień `licytacje`), wcześniej zawsze losowanie (zamiast kolejności rundy);
  decyzja `przejecie: {id, oferta}` – kupno budynku z ceną, który wynajmuje drużyna (KC art. 678: najemca płaci
  czynsz nowemu właścicielowi – jego przychód z VAT), najemca kupujący swój lokal – wykup (własność, zwrot kaucji,
  sprzęt wynajmującego jego); decyzja `wypowiedz: [{id, ulepszenia}]` – najem trwa jeszcze 4 rundy, potem
  wyprowadzka: sprzedaż sprzętu najemcy, zwrot kaucji, pracownicy na wolne stanowiska w innych lokalach albo
  zwolnienie z odprawą (do puli), nakłady najemcy (adaptacja, stanowiska – nowe pole `Lokal.naklady`) rozliczone
  wg KC art. 676 (właściciel zatrzymuje i płaci 50% albo najemca płaci 30% za przywrócenie stanu), budynek staje się
  lokalem właściciela; numery nowych stanowisk `Firma.nowy_nr` (bez kolizji po wyprowadzce); boty nie licytują,
  po wypowiedzeniu szukają nowego lokalu; lista błędów (odrzucone decyzje, wypowiedzenie, nowy właściciel); dane
  rynku: przetargi i właściciele; zakładka **Licytacje i przejęcia** w grupie Lokale (Decyzje: budynki na sprzedaż
  z ofertą, własne budynki z wypowiedzeniem, najmy u innych; Wyniki: przejęcie, wyprowadzki, licytacje w mieście);
  test `test_licytacje.py`

- [x] F3b.5 Wypadki w lokalu i ubezpieczyciel (gra z lokalami) – `silnik/awarie.py`, dane `dane/zdarzenia/losowe.yaml`
  (schemat `PlikWypadkow`): 10 historii w 2–3 scenach (8 komicznych – Gołąb Zenon, Pani Halina z drugiego piętra,
  Najazd koziołków, Zalanie z góry, Śpiewająca frytkownica, hulajnoga, kot kierownik, ząb pana Ryszarda; 2 poważne
  bez żartów – pożar kuchni, włamanie), rozgrywane jak eventy w parkach, ale tylko w jednej drużynie: od rundy 4
  szansa 8% na rundę (strumień `wypadki`), naraz jeden otwarty, bez powtórek (`Firma.wypadki`); nowy skutek
  `szkoda` (koszt w KPiR bez VAT, najwyżej 8000 zł, pole `polisa`). Ubezpieczyciel TUW „Pod Koziołkiem” (budynek
  na mapie): polisy na lokal, sprzęt i OC (pokrycie, franszyza, składka miesięczna stała + za lokal + od majątku,
  zwolniona z VAT), decyzja `polisy: [rodzaj]` (pełna lista, `Firma.polisy`: rodzaj → runda początku ochrony,
  karencja 1 runda); odszkodowanie (szkoda − franszyza) × pokrycie jako przychód pozostały, gdy polisa chroniła
  w rundzie początku wypadku; boty z polisami wg strategii (`boty.yaml` → `polisy`); wyniki rundy `ubezpieczenia`;
  zakładka **Finanse → Ubezpieczenia** (Decyzje: kup/wypowiedz, składki; Wyniki: składki, szkody, odszkodowania,
  historia szkód), zakładka Zdarzenia pokazuje wypadki i szkody; test `test_awarie.py`
- [x] F3b.6 Urząd i sanepid (gra z lokalami) – `silnik/urzad.py`, dane `dane/zdarzenia/urzad.yaml` (schemat
  `PlikUrzedu`): rejestracja w CEIDG (PKD 56.10.A, bezpłatna, tylko opis); odbiór lokalu przez sanepid w rundzie,
  w której lokal ma zacząć działać – przy higienie bez odbioru odmowa i lokal rusza rundę później, do skutku
  (`Firma.odbiory`, strumień `odbior`); decyzja `higiena: poziom` (`Firma.higiena`, trwa do zmiany): 4 poziomy
  (brak / mop i grafik – domyślny / firma „Błysk-Pol” / Błysk-Pol + HACCP) z kosztem miesięcznym za działający lokal
  (KPiR, VAT 23%) i wpływem na kontrolę sanepidu (dodatek do szansy, mnożnik części z problemów, dodatek do
  mandatu); nowy skutek historii `kontrola` (skarga do sanepidu – `Efekt` „kontrola”, dodatek do szansy kontroli
  przez kilka rund; dodany do historii Gołąb Zenon i Pani Halina); boty z higieną wg strategii; ratusz na mapie
  otwiera zakładkę **Lokale → Urząd i sanepid** (Decyzje: rejestracja, lokale i odbiory, poziomy higieny, ryzyko
  kontroli, skargi; Wyniki: koszt, odbiory, kontrola, historia kontroli), odmowa odbioru na liście błędów; test
  `test_urzad.py`

Zadania F3b.7–F3b.9, F4.1–F4.7 – jeszcze nie zaczęte.
