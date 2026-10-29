# Postęp

Postęp prac: kroki 1–4 według [Planu implementacji](archiwum/Plan%20implementacji.md) (archiwum), kroki 5–6 według
[Planu optymalizacji](notatki/Plan%20optymalizacji.md) (na dole). 1 commit = 1 zadanie (`F2.1: …`, `B3: …`).

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

- [x] F3a.4 Popyt strefowy – pule klientów stref (`dane/mapa/popyt.yaml`: pula, poziom cen i wrażliwość na cenę strefy, dni tygodnia, miesiące, kalendarz miejski z 9 wydarzeniami); klienci strefy wybierają lokal (cena względem strefy, jakość, odległość, zadowolenie, wyposażenie, reklama; opcja zewnętrzna – bary spoza gry); dwa lokale w strefie dzielą klientów; obsługa dzień po dniu w każdym lokalu (`silnik/rynek/popyt.py`); prognoza strefowa w zakładce Oferta; boty planują obsadę na szczyt tygodnia; nowa zakładka **Klienci i strefy** (Decyzje: prognoza lokali i dni, wydarzenia, potencjał stref; Wyniki: klienci dzień po dniu, skąd przyszli, podział stref); szacunek klientów na kafelkach lokali; testy `test_popyt.py`

- [x] F3a.5 Menu i świeżość – partie składników z terminem przydatności (`silnik/kuchnia/swiezosc.py`, `Firma.partie`): dostawa na wybrany dzień rundy, zużycie FIFO (najkrótszy termin), kosz po terminie (bułka z poniedziałku – we wtorek wieczorem), pojemność szafy chłodniczej i zamrażarki (`sprzet.yaml`: `przechowywanie`, `pojemnosc_l`; `zasoby.yaml`: `przechowywanie`, `termin_dni`, `miejsce_l`) – co się nie zmieści, przepada; mrożona pita i mrożone mięso jako zamienniki (−1★ jakości składnika); jakość dania z wag menu (`dane/mapa/menu.yaml`); danie bez składnika rano wypada z menu, połowa jego klientów bierze inne danie (`silnik/kuchnia/menu.py`); zwroty z partii; boty rozkładają dostawy na dni; zakładka **Magazyn i świeżość** (Decyzje: zajętość chłodni dzień po dniu, partie i terminy; Wyniki: dostawy/zużycie/straty dzień po dniu, kosz, dania wyłączone z menu), zamówienia na dni w zakładce Dostawcy, kolumna „Straty” w wynikach; ostrzeżenia na liście błędów; testy `test_swiezosc.py`

- [x] F3a.6 Dostawcy i sprzęt – 9 dostawców z rodzajem i zasadami (`dane/dostawcy.yaml`: `dostawcy`): piekarnia (dowóz codziennie), dyskonty Biedronka / Lidl / Stokrotka (odbiór osobisty – czas właściciela, limit opakowań dziennie, gazetka z promocjami losowana co tydzień), hurtownie Makro / Selgros / Eurocash (dni dostaw, płatny dowóz poniżej progu), producent mięsa „Rożen” (minimalne zamówienie, od rundy 3); zamówienie przychodzi w zaplanowany dzień, a w dzień bez dostaw jest odrzucane (czerwony błąd) – `silnik/kuchnia/dostawcy.py`: `zasady_dostaw`, `oferta_rundy`, `gazetki`; planowanie dostaw (boty, „Zamów”) w dni dostawcy, bez dyskontów i poniżej minimum; budynki dostawców na mapie; środki trwałe i amortyzacja (`silnik/ksiegowosc/srodki_trwale.py`, `Firma.srodki_trwale`): kupiony lokal i budynek 2,5% rocznie, grunt bez amortyzacji, zakupy od 10 000 zł 20% rocznie, tańsze od razu w koszty, sprzedaż – niezamortyzowana wartość w koszty; sklepy przy wyposażeniu (IKEA, OBI, Jula, Castorama) i park handlowy na mapie; zakładki: **Dostawcy** (Decyzje: dni dostaw, gazetki, limity, plan dostaw rundy; Wyniki: dostawy i opłaty za dowóz) i nowa **Inwestycje → Środki trwałe** (Decyzje: ewidencja po decyzjach, stawki; Wyniki: ewidencja na koniec rundy, odpisy w KPiR); testy `test_zasady_dostaw.py`, `test_srodki_trwale.py`

- [x] F3a.7 Czas właściciela – pula godzin na rundę (`zalozenia.yaml`: `operacje.czas_wlasciciela`, 20 h), `silnik/ludzie/czas_wlasciciela.py`; zużywa ją odbiór osobisty w dyskontach (kolejno po dniach), dzień zakupów bez wolnych godzin jest odrzucony – czerwony błąd na liście błędów (zakładka Dostawcy); nowa zakładka **Czas właściciela** (Decyzje: plan godzin rundy; Wyniki: wykorzystanie i odrzucone decyzje), podpowiedź w Dostawcach; test `test_czas_wlasciciela.py`

- [x] F3a.8 Agencja pracy – `silnik/ludzie/rynek_pracy.py`, `dane/kandydaci.yaml` (`agencja`): kanały rekrutacji pracuj.pl / agencja / headhunter (gwiazdki, opłata, mnożnik kosztu rekrutacji, czas właściciela, od rundy), wspólna pula kandydatów z licytacją (wyższa pensja, remis – losowanie), limit 3 nowych na rundę, podkupienie przez headhuntera z kontrofertą, okres wypowiedzenia wg stażu (`Pracownik.odchodzi`), zwolnieni wracają do puli; nowa zakładka **Rynek pracy** (Decyzje + Wyniki) w HR, wybór kanału w oknie zatrudnienia; test `test_rynek_pracy.py`

- [x] F3a.9 Banki – sześć banków z mapy (`dane/mapa/banki.yaml`, `silnik/pieniadze/banki.py`), każdy z inną najlepszą ofertą: Crédit Agricole (kredyt na start bez historii), PKO BP (kredyt inwestycyjny pod zastaw), Pekao (leasing sprzętu), ING (lokaty), mBank (tanie konto i terminal), Santander (limit w koncie); konto firmowe z terminalem (abonament + prowizja od płatności kartą), lokaty i kredyty w dowolnym banku, historia firmy, zastaw lokalu lub sprzętu i przejęcie po zaległościach, odsetki karne, leasing (sprzęt bez prawa sprzedaży do wykupu), debet ponad limit; zakładka **Finanse → Bank** w grze z lokalami (Decyzje + nowe Wyniki); boty wybierają najtańsze konto; test `test_banki.py`
- [x] F3a.10 Harpagon – lichwiarz z mapy (`dane/mapa/harpagon.yaml`, `silnik/pieniadze/lichwiarz.py`): pożyczka „na czarno” od ręki, bez sprawdzania zdolności i poza KPiR (gotówka i spłata tylko na rachunku z `poza_ksiegami`), jedna naraz, odsetki od całego długu co rundę; po terminie rosnąca presja z komicznymi historiami (Harpagon i Mistrz Jakub ze „Skąpca”): życzenia w rundzie terminu, przypomnienia, odsetki karne, wizyty; skutki zaległości w `silnik/pieniadze/zaleglosci.py` (szkody w lokalu – koszt w KPiR, odpływ klientów, odejście pracownika do puli) do użycia później przy ZUS/US; nowa zakładka **Finanse → Harpagon** (Decyzje + Wyniki) i kantor na mapie przy dworcu; test `test_harpagon.py` (scenariusz presji krok po kroku)
- [x] F3a.11 Księgowość JDG – `dane/podatki_2026.yaml` (schemat `PlikPodatkow`), ceny brutto → KPiR netto + rejestr VAT w `Ksiega` (`ksieguj` ze stawką, stawkami albo z reguł po opisie; sprzedaż dań 8%, napoje 23%, żywność 5%, opakowania i usługi 23%, usługi finansowe i płace bez VAT; środki trwałe – VAT naliczony, ewidencja netto; korekta VAT przy zwrotach), `silnik/ksiegowosc/rozliczenie.py` co rundę zamiast CIT: ZUS społeczny po uldze na start (26 rund), zdrowotna 4,9% z minimum, zaliczka PIT 19% narastająco, VAT z nadwyżką przenoszoną; ZUS pracodawcy 20,48%; `Firma.rozliczenie`; wyniki `rozliczenie` i `vat`, widok `podatki`; nowa zakładka **Finanse → Podatki** (Decyzje: parametry, stan rozliczeń, VAT z decyzji, stawki; Wyniki: rozliczenie rundy, zaliczka PIT narastająco, deklaracja VAT, rejestr), KPiR netto z zaliczką PIT i zdrowotną zamiast „Podatek”; test `test_ksiegowosc.py` (scenariusze co do grosza)
- [x] F3a.12 Uzgodnienie kasy – każda operacja rachunku ma rodzaj (`RODZAJE_OPERACJI`: KPiR, korekty, podatki, inwestycje, kredyty, lokaty, kaucje, Harpagon), koszty bez wydatku (`bez_gotowki`) i VAT od inwestycji oznaczone; `silnik/ksiegowosc/uzgodnienie.py` co rundę: początek + przychody − koszty + koszty bez wydatku + VAT należny − naliczony ± operacje poza KPiR = koniec, do tego KPiR ↔ operacje „kpir” i saldo ↔ suma operacji; wynik `uzgodnienie`; zwijana sekcja „Uzgodnienie kasy z KPiR” w **Finanse → Raport**; test `test_uzgodnienie.py` (hypothesis na losowych grach botów z kredytami, lokatami, Harpagonem, lokalami, sprzedażą sprzętu i zwrotami + scenariusz ze wszystkimi rodzajami). Znalezione i naprawione błędy: `ksieguj` zaokrąglał kwotę dwa razy (grosz różnicy przy końcówce ½ gr) – teraz raz, handlowo; `Rachunek.zapisz` liczył saldo z niezaokrąglonej kwoty; zwrot zasobów – brutto zaokrąglane wg stawek; zwrot zabierający ostatnią partię wywracał grę (`KeyError` w magazynie)

- [x] F3a.13 Biura rachunkowe i samodzielna księgowość – pięć biur z mapy (`dane/mapa/biura.yaml`: J.K.Ś., Pod Trybunałem, Pani Halinka, e-Księgi24.pl, Debet & Kredyt) z ryczałtem, limitem dokumentów, opłatą za dokument, minimum, kadrami (osoby w cenie, etat, zlecenie), ryzykiem błędu i OC – błąd biura bez OC kosztuje mandat (komiczne historie), z OC – zwrot; opłata liczona od liczby dokumentów rundy (`silnik/ksiegowosc/biuro.py`: `oplata`, `nalicz`, `najtansze`); **samodzielna księgowość**: po rundzie drużyna dostaje paczkę dokumentów z rachunku (faktury sprzedaży i zakupu, raporty kasy, listy płac, deklaracje ZUS, wyciągi, środki trwałe, operacje poza KPiR), w następnej rundzie księguje je do kolumn KPiR ze stawką VAT i składa deklaracje VAT, zaliczki PIT i składki zdrowotnej; silnik sprawdza: błędny zapis – wyjaśnienie, błędna deklaracja – korekta do poprawnej kwoty i mandat 200 zł, brak deklaracji – rozliczenie z urzędu i mandat 500 zł; ostatnia runda rozliczana od razu; do czasu złożenia deklaracji widok drużyny ukrywa KPiR, podatki i dochód netto rundy (także w podglądzie); boty wybierają najtańsze biuro; zakładka **Finanse → Biuro rachunkowe** (Decyzje: oferty z szacunkiem opłaty, dokumenty do zaksięgowania z podpowiedziami, podsumowanie i deklaracje; Wyniki: opłata biura albo sprawdzenie deklaracji i zapisów); test `test_biuro.py`, test uzgodnienia kasy obejmuje biura i samodzielne deklaracje (także błędne) oraz sprawdza, że dokumenty pokrywają cały rachunek rundy. Naprawione przy okazji: kredyt odnawialny uruchamiany na koniec rundy nie trafiał do dokumentów

- [x] F3a.14 Panel mistrza gry – **pauza** gry (drużyny nie zmieniają ani nie wysyłają decyzji, runda się nie zamyka – także z harmonogramu; cofnięcie działa); **zamykanie rund o stałej porze**: tygodniowe terminy (`Gra.harmonogram`, `gry/harmonogram.py`), runda zamyka się w pierwszym terminie po zamknięciu poprzedniej, komenda `manage.py zamykaj_rundy` (raz albo `--petla 60`; Harmonogram zadań Windows / cron w README), termin widoczny dla drużyn na pasku i w *Wyślij decyzje*, strona drużyny odświeża się po pauzie i zmianie terminu; **wgląd mistrza gry w drużyny uczniów tylko do odczytu** (API: 403, strona: komunikat; drużynę bez uczniów i grę lokalną prowadzi nadal mistrz gry); **poziom botów** (łatwy / średni / trudny, `dane/boty.yaml: poziomy`) przy zakładaniu gry i w trakcie (od następnej rundy) – na razie zapisany bez wpływu na decyzje (zachowanie poziomów w F4.4); **eksport do arkusza**: ranking i wyniki firm w rundach (CSV, średnik, przecinek dziesiętny, BOM – Excel); migracja `0004_prowadzenie_gry`; test `test_prowadzenie.py`. Odblokowywanie zakładek – w F4.3 (jak w planie)

- [x] F3a.15 Limity – `silnik/limity.py`: najwyżej 3 nowych pracowników na rundę (zatrudnienia + oferty podkupienia pracowników innych drużyn) i kolejny lokal co 3 rundy; **zapis decyzji z przekroczeniem jest odrzucony** (API 400 z opisem, strona pokazuje komunikat i wczytuje poprzednie decyzje), przyciski *Zatrudnij +* i *Złóż ofertę* sprawdzają limit od razu; lista błędów: niebieskie „wykorzystany limit nowych pracowników” i „kolejny lokal od rundy N” (czerwone – jak dotąd z przeliczenia, które nadal przycina nadmiar u botów i w starych zapisach); test `test_limity.py`. Pełna lista błędów dla nowych decyzji – w F4.2 (jak w planie)

**Krok 3a zakończony.**

- [x] F3b.1 Parki – `dane/zdarzenia/parki.yaml`: 14 historii w 7 parkach (12 komicznych, 2 poważne; 4 nowe parki na mapie), sceny z opcjami (koszt: godziny właściciela, gotówka, porcje jedzenia), opcja domyślna, ciąg dalszy za N rund z szansą; schematy z kontrolą grafu (każda ścieżka się kończy, brak scen nieosiągalnych); `silnik/swiat/zdarzenia.py`: od rundy 2 co rundę jedna historia dla wszystkich drużyn (kolejność losowana bez powtórzeń w cyklu), skutki – gotówka (bez VAT), mnożnik popytu, mniej godzin właściciela w kolejnych rundach, kandydat na rynku pracy tylko dla tej drużyny; boty wybierają losowo spośród opcji do 3 h; zakładka **Zdarzenia** (Decyzje: sceny i wybór reakcji, Wyniki: reakcje, skutki, „ciąg dalszy nastąpi”, trwające efekty, dziennik); lista błędów: niebieski brak wyboru, czerwony brak czasu właściciela (gra bierze opcję domyślną); test `test_zdarzenia.py`
- [x] Zmiany 26.10 (polecenia użytkownika): kapitał startowy 40 000 zł (dane, README, notatki); sortowanie tabel
  kliknięciem w nagłówek (rosnąco, malejąco, kolejność pierwotna; liczby w polskim zapisie, gwiazdki, puste na końcu;
  działa też w oknach, np. baza składników) i lista „Sortuj” w ofercie lokali; testy kupna lokali dostają jawnie
  kapitał 100 000 zł
- [x] Magazyn bez kosztu magazynowania i zwrotów (gra z lokalami; gra bez lokali i `dane_revas/` bez zmian):
  wynajęta chłodnia „Mroźnia u Mietka” – nadmiar ponad chłodnię/zamrażarkę lokalu przy dostawie (`swiezosc.przyjmij`,
  `Partia.wynajem`) za 1 zł/l z VAT 23%, termin krótszy o 2 dni, nie zajmuje miejsca w lokalu; kontrola sanepidu co
  rundę (`silnik/kuchnia/magazyn.py`, strumień „sanepid”): szansa 3% + za litry w wynajmie i złotówki przeterminowanego
  towaru, mandat 300–3000 zł poza KPiR (nowy rodzaj operacji „kary”, w uzgodnieniu kasy i biurze rachunkowym) i −7%
  popytu na 2 rundy, komiczne teksty kontroli w `dane/zdarzenia/magazyn.yaml`; historia „Pani Halina z banku
  żywności” (zapas z krótkim terminem ≥ 200 zł, szansa 40%; oddanie zabiera partie – strata z powodem „bank”, +3% lub
  +5% popytu, podziękowanie w następnej rundzie); zwroty i koszt magazynowania ukryte w zakładce Dostawcy;
  zakładka **Świeżość**: Decyzje – nadmiar do wynajmu dzień po dniu i ryzyko kontroli, Wyniki – wynajęte partie i
  karta kontroli; testy `test_magazyn.py`, `test_swiezosc.py`
- [x] F3b.2 Agencje reklamowe (gra z lokalami) – `dane/mapa/reklama.yaml`: 4 agencje na mapie (drukarnia „Papier
  Przyjmie”, „Lajk i Spółka”, „Fala Koziołka”, „Kozi Gród Events” – 2 nowe budynki), 8 kanałów (od rundy 3 część,
  od rundy 5 wszystkie), zasięg strefa albo całe miasto (radio), Noc Kebaba tylko w strefach akademickich, komiczne
  raporty agencji; `silnik/rynek/reklama.py`: zamówienie `kampanie: [{agencja, kanal, strefa}]` z góry (koszt × pula strefy,
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
  po 2 komiczne teksty na rodzaj; `silnik/rynek/promocje.py`: decyzja `promocje: [{typ, nazwa, danie}]` (pełna lista,
  bez klucza – trwają), koszt włączenia netto + VAT 23% (KPiR – pozostałe), zmiana nazwy bez kosztu, zmiana dania =
  nowa promocja, danie zdjęte ze sprzedaży wyłącza promocję; w popycie (`popyt.podzial`) przyciąganie ×(1 +
  przyciąganie) u objętych klientów w dniach z maski, 2 za 1 – podwójne porcje (składniki i czas kuchni); przychód
  z rabatami, dopłaty do zestawu jako sprzedaż napojów (VAT napoju), napoje do zestawów w towarach; znużenie
  (przyciąganie spada co rundę) i przywiązanie (karta rośnie); dane rynku: promocje na mieście; boty ze strategii
  (`boty.yaml: promocje`, `min_obsluga_promocji` – bez wolnych mocy promocji nie włączają); zakładka **Promocje**
  w Marketingu (Decyzje: rodzaje z liczbami, włącz/wyłącz, nazwa, danie, konkurencja; Wyniki: komiczne teksty,
  liczby promocji, promocje na mieście); test `test_promocje.py`

- [x] F3b.4 Licytacje i przejęcia lokali (gra z lokalami) – zamiast planowanych `oferty.py` i `koniec_najmu.py` jeden
  moduł `silnik/nieruchomosci/przejecia.py`; zasady w `dane/mapa/lokale.yaml` (`licytacje_od_rundy` 4, `oferta_max` 3,
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

- [x] F3b.5 Wypadki w lokalu i ubezpieczyciel (gra z lokalami) – `silnik/swiat/awarie.py`, dane `dane/zdarzenia/losowe.yaml`
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
- [x] F3b.6 Urząd i sanepid (gra z lokalami) – `silnik/ksiegowosc/urzad.py`, dane `dane/zdarzenia/urzad.yaml` (schemat
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

- [x] F3b.7 Kasyno (ukryte przed MG) i portfel właściciela (gra z lokalami) – `silnik/pieniadze/wlasciciel.py`
  (`dane/zdarzenia/wlasciciel.yaml`, schemat `PlikWlasciciela`): prywatny portfel (`Firma.portfel_gr`, start
  z oszczędności 2000 zł), decyzje `wyplata_wlasna` / `wplata_wlasna` poza KPiR (rodzaj „wlasciciel” na rachunku,
  przycinane do gotówki firmy / portfela); kolejność: wypłata → klub → wpłata. `silnik/pieniadze/kasyno.py`
  (`dane/zdarzenia/kasyno.yaml`, schemat `PlikKasyna`): klub „Pod Złotym Kaflem”, ul. Nocna 13 – bez budynku na
  mapie i pozycji w menu; od rundy 4 szansa 8% na zaproszenie na następną rundę (najwyżej 2 w grze, boty nie
  dostają, `Firma.zaproszenia`, strumień `kasyno`); decyzja `kasyno: [{gra, zaklad, stawka}]` – ruletka
  (37 pól, kolory, parzyste, tuziny, zero) i automat „Jednoręki Zenek”, do 5 zakładów, 10–2000 zł, z portfela;
  podgląd zdejmuje stawki bez wyniku. Mistrz gry nie widzi klubu ani portfela (`kas.ukryj` w `api/widoki.py`:
  widok, warianty, podgląd, eksport; przegląd i CSV i tak bez nich), `LEVAS_KASYNO=0` wyłącza klub na serwerze.
  Zakładki **Finanse → Portfel właściciela** i **Nocna 13** (ukryta poza rundą z zaproszeniem i rundą po niej;
  Decyzje/Wyniki), komunikat z zaproszeniem na Dashboardzie; test `test_kasyno.py`

- [x] F3b.8 Handel między drużynami (gra z lokalami) – `silnik/rynek/handel.py` (`dane/zdarzenia/handel.yaml`, schemat
  `PlikHandlu`): od rundy 5 decyzja `handel_oferty` – sprzedaż innej drużynie (nie botowi) towaru z magazynu albo
  sprzętu ze stanowiska (nie z najmu lokalu, nie w leasingu), cena brutto za całość w widełkach 50–200% wartości
  (koszt zakupu / cena katalogowa), najwyżej 5 ofert; oferta sprawdzana po tygodniu sprzedaży (`Firma.oferty_handlu`),
  adresat przyjmuje ją w następnej rundzie (`handel_przyjmij`, nr stanowiska na sprzęt) – transakcja na początku
  przeliczenia, przed zakupami, jeśli sprzedawca ma towar, a kupujący pieniądze. Faktury w KPiR obu stron (towar:
  przychód kol. 7 z VAT należnym / zakup towarów kol. 10; sprzęt: jak sprzedaż i zakup sprzętu), partie przechodzą
  z terminem przydatności; komiczny tekst przekazania (strumień `handel`); w biurze sprzedaż towaru to faktura
  sprzedaży. Podgląd liczy przyjęcie na kopii stanu. Zakładka **Handel z drużynami** (Decyzje/Wyniki); test
  `test_handel.py`

- [x] F3b.9 Kalendarz miejski (gra z lokalami) – `silnik/rynek/kalendarz.py` (`dane/kalendarz/kalendarz.yaml`, schemat
  `PlikKalendarza`; kalendarz przeniesiony z `mapa/popyt.yaml`): 23 wydarzenia na 26 tygodni od 5.10 – święta
  (Wszystkich Świętych, 11 listopada, Boże Narodzenie, Nowy Rok, Trzech Króli, Tłusty czwartek, Wielkanoc), uczelnie
  (otrzęsiny, Andrzejki, przerwy, sesja zimowa), ferie, okazje handlowe (Black Friday, Walentynki, Dzień Kobiet)
  i wydarzenia w mieście (Konfrontacje Teatralne, Halloween, jarmark, Mikołajki, Sylwester, pierwszy dzień wiosny),
  każde z komiczną historią. Daty stałe 'MM-DD' albo ruchome (`wzgledem`: Wielkanoc, Black Friday, ferie – daty na
  każdy rok, sprawdzane na lata gry); mnożniki dziennej puli stref (`popyt.wagi_dni`), zmiana tygodniowej puli stref
  (`kalendarz.tydzien`). Zakładka **Kalendarz miejski** w grupie Klienci i strefy (Decyzje: bieżący tydzień,
  następne 4 i przegląd wszystkich tygodni; Wyniki: miniony tydzień i klienci stref); test `test_kalendarz.py`

## F4 – dopasowanie starych funkcji (bez giełdy)
- [x] F4.1 Karta wyników dla kebabu – `silnik/wyniki/karta.py` (`kebab`, `miary_kebabu`, `cena_wzgledem_strefy`; parametry
  `zalozenia.yaml → karta_wynikow.kebab`). W grze z lokalami 5 wskaźników Revasa dostaje składniki kebabowe z wyników
  tygodnia: zadowolenie klientów – cena względem ceny preferowanej strefy lokalu (zamiast średniej rynku), kolejki
  (klienci utraceni z braku rąk lub sprzętu), dania wyłączone z braku składnika, mandat sanepidu, wypadki w lokalu;
  zadowolenie pracowników – przepracowanie (wykorzystanie czasu ponad próg); rozwój – kolejne lokale; zadłużenie –
  dług u Harpagona z wagą 1,5. Iloczyn liczony od nowa (0 przy stracie), karta skumulowana = średnia kart (od rundy 4),
  zadowolenie klientów nadal wpływa na popyt następnej rundy. Wyniki rundy: `karta_kebab` (miary i poprawki);
  zakładka **Karta wyników** – tabela „Skąd Twoja karta – sprawy kebabowe” i dzielnik wyniku ekonomicznego z danych
  (4 615 zł tygodniowo zamiast „20 000”). Kodu `ocena.py` starego Levasa nie ma na dysku – wzory z notatki
  „Ustalenia gry”; test `test_karta.py`

- [x] F4.2 Lista błędów dla nowych decyzji – `silnik/kuchnia/menu.py` (`bledy`, `koszt_porcji`): danie bez sprzętu, brak
  kucharza (konkretne powody zamiast ogólnego „brak stanowiska”), cena poniżej kosztu składników (czerwone) i składniki
  ponad 50% ceny (pomarańczowe); `silnik/kuchnia/swiezosc.py` (`przeterminowanie`): partie, które przy prognozie popytu
  przeterminują się w tygodniu (FIFO, wagi dni strefy, próg 20 zł); zamówienia u dostawców ponad saldo konta. Progi
  w `zalozenia.yaml → lista_bledow`. Brak czasu właściciela, limity, chłodnia – były już wcześniej (F3a/F3b).
  Przycisk „Popraw” prowadzi też do nowych zakładek (Magazyn i świeżość, Zatrudnienie, Zdarzenia…); test
  `test_lista_bledow.py`

- [x] F4.3 Odblokowywanie zakładek – `silnik/harmonogram.py`: elementy harmonogramu (zakładki z
  `katalog.yaml → rundy.harmonogram_lokali` i elementy mapy z własnym `od_rundy`: kanały rekrutacji, późniejsi
  dostawcy, licytacje, przejęcia, promocje, kanały agencji, eventy w parkach, wypadki, handel); gra z lokalami liczy
  się na widoku danych z tygodniami mistrza gry (`konfiguracja.odblokowanie`, tylko zmiany), wspólne dane się nie
  zmieniają; `Gra.ustaw_odblokowanie` (tylko przyszłe elementy, nie wcześniej niż bieżący tydzień, `liczba_rund + 1`
  = wyłączone); API: opcja `odblokowanie` przy zakładaniu gry i `POST prowadzenie {"odblokowanie": …}`; panel MG:
  okno „Harmonogram odblokowań”; strona drużyny: „od rundy N” z harmonogramu gry; test `test_harmonogram.py`
- [x] F4.4 Boty – poziomy (`dane/boty.yaml → poziomy`, schemat `PoziomBota`, `boty.poziom`): łatwy – proste
  reguły (kuchnia na danie, zamówienia na cały popyt, błąd prognozy, losowy kandydat, bez kampanii i promocji);
  średni – planer przepustowości (`_plan_firmy`/`_plan_lokalu`: kucharze każdego zawodu, sztuki sprzętu i kasjerzy
  na popyt dzień po dniu, kolejna osoba tylko, gdy dodatkowa sprzedaż × marża pokrywa jej koszt; zamówienia
  i udziały dni z planu; lokal z co najmniej `min_kuchnia` miejscami); trudny – korekta prognozy o wynik
  poprzedniej rundy, wybór ceny o największej oczekiwanej marży, kampanie tylko przy nadążającej obsłudze,
  drugi lokal (`kolejny_lokal`); narzędzie `gra/balans_botow.py`; test `test_boty.py`. Bez przejęć i licytacji
  przez boty (pytanie 25)
- [x] F4.5 „Co jeśli” – `silnik/co_jesli.py`: podgląd bieżącej rundy na kopii stanu dla kilku wariantów decyzji;
  boty decydują jak zwykle, inne drużyny powtarzają decyzje z poprzedniej rundy (`POWTARZANE`: ceny, prognoza,
  zamówienia, kampanie, reklama, promocje, polisy, higiena – bez jednorazowych), więc podgląd nie zdradza
  roboczych decyzji rywali; API `podglad` korzysta z modułu; zakładka Analiza: opis założenia i wiersz „Towar
  przeterminowany”; test `test_co_jesli.py` (m.in. podgląd = wynik, gdy rywal naprawdę powtarza decyzje)
- [x] F4.6 Sprzątanie – usunięty tryb „gra bez lokali” (Revas): jedyny tryb to gra z mapą miasta (`Gra.nowa`
  wymaga danych z mapą, stare zapisy bez lokali – czytelny błąd; tryb do odzyskania z commita `9930e14`);
  usunięte `silnik/rynek.py` (popyt i reklama Revasa), `oczekiwany_popyt`, reklama tradycyjna/internetowa,
  zwroty do dostawców (silnik i zakładka Dostawcy), startowe stanowiska; wspólne mnożniki jakości w
  `silnik/kuchnia/jakosc.py`; nazwy po fitnessie: `godziny_kasy`, `pensje_rynkowe_kasy`, `liczba_kasjerow`;
  `gra/balans_botow.py` → `gra/balans/symuluj.py` (`python -X utf8 -m balans.symuluj`); testy Revasa
  przeniesione na dane Levasa albo usunięte (pytanie 27)
- [x] F4.7 Zakładki – menu jak w Revasie dla nowych funkcji: Lokale (lokale, przejęcia, urząd), Menu (dawna
  Oferta), Dostawcy ▸ Dostawcy / Magazyn i świeżość, HR, Marketing ▸ Agencje / Promocje (usunięte martwe zakładki
  reklamy tradycyjnej i internetowej Revasa), Finanse ▸ Raport / KPiR / **VAT** (nowa: rejestr, stawki,
  deklaracja) / Podatki (PIT i ZUS) / Bank / Harpagon / Biuro / Ubezpieczenia / Właściciel, Parki (eventy,
  zdarzenia, wypadki), Handel; nowe wyniki w Inwestycje ▸ Stanowiska (liczba, miejsca w lokalach, obłożenie,
  stanowiska konkurencji – `rynek.stanowiska`) i HR ▸ Szkolenia (`wyniki.szkolenia`, efekt w karcie);
  z panelu MG usunięty wybór „bez lokali”; wszystkie zakładki sprawdzone w node na widoku prawdziwej gry
  (pytanie 28); dosprzątanie po F4.6: z danych Levasa usunięte nieużywane parametry Revasa (`podatek_cit`,
  `utrzymanie_klubu`, `koszt_magazynowania`, `koszt_zwrotu`), na pulpicie „PIT liniowy” zamiast CIT

Plan kroków 1–4 (bez giełdy) zrealizowany.

## Poprawki 27.10 (odpowiedzi w archiwum/PRACA_NOCNA.md i na czacie)

Kolejność: P1 → P2 → … Po każdym: testy, ruff, `sprawdz`, migracje, POSTEP + PRACA_NOCNA, commit i push.

- [x] P1 Tworzenie gier – `graj` nie startuje drugiego serwera na zajętym porcie (dwa serwery na 8765, stary
  z nieaktualnym kodem)
- [x] P2 Domyślne ustawienia: start pon. 1.09.2025, 18 pełnych rund (do 4.01.2026), kapitał 40 000 zł, kredyt
  „na bieżąco”, przycisk „Zamów brakujące” w Dostawcach domyślnie wyłączony – opcja MG (nowa gra i trwająca gra);
  wrzesień – wprowadzenie (studenci wracają w październiku)
- [x] P3 Tutorial dla graczy: strona „Jak grać” w panelu + `INSTRUKCJA.md` + PDF
- [x] P4 Instrukcja logowania kontem Microsoft (`gra/LOGOWANIE_MICROSOFT.md`) – pytanie 3
- [x] P5 Właściciel jako pracownik 1★ (ręcznie, godziny z puli 20 h, bez pensji) – pytanie 4
- [x] P6 Jedno wypowiedzenie: 2 rundy dla wszystkich – pytanie 5
- [x] P7 Krótkie opisy dydaktyczne w zakładkach finansów (VAT, KPiR, PIT, ZUS, bank…) – pytanie 8
- [x] P8 Lokal „co 3 rundy”: komunikat, że właściciel musi odpocząć – pytanie 11
- [x] P9 Parki: co rundę kilka eventów (te same dla wszystkich, każdy może wziąć każdy, ta sama nagroda), każdy
  kosztuje czas właściciela – wszystkie naraz nie zmieszczą się w 20 h – pytanie 12
- [x] P10 Reklama: suma kampanii daje kebabowi ok. +10% … +30% popytu – pytanie 14
- [x] P11 Wypadki: +4 pp. szansy za każdą rundę bez wypadku (reset po wypadku) – pytanie 17
- [x] P12 Kasyno: wypłata z konta kebaba w panelu klubu + ironiczna „zasada milczenia” – pytanie 19
- [x] P13 Handel: negocjacje na żywo w rundzie (oferta → kontroferta, maks. 3) – pytanie 20
- [x] P14 Kalendarz wrzesień–grudzień: mecze (Motor Lublin), wpływ wydarzeń na konkretne dania, sezonowość
  tygodniowa dopasowana do wydarzeń – pytania 21 i 27
- [x] P15 Harmonogram: tydzień 1 przygotowawczy, MG nie przesuwa zakładek tygodnia 1 – pytanie 24
- [x] P16 Konkurencja: ogólny obraz rywali dla wszystkich (Decyzje/Wyniki), dokładne dane – detektyw z mapy
  (300–800 zł + 2 h, 15% wpadki) – pytanie 26
- [x] P17 Sprzątanie: usunąć zbędne pozostałości Revasa (`dane_revas/`, martwy kod) – pytanie 27
- [x] P18 Nowe historyjki (parki, zdarzenia) – do 15:00, po wszystkim innym – pytanie 12
- [x] P19 (jeśli czas) bot „niemożliwy”; inaczej wpis w rzeczach na przyszłość – pytanie 25
- [x] P20 (jeśli czas) przegląd starego Levasa (`Tom-Wasko/Levas-stary`, branch `kod`) – lista różnic – pytanie 1

## Poprawki 28.10 (uwagi z testu gry, odpowiedzi na czacie)

Kolejność: Q1 → Q2 → … Po każdym: testy, ruff, `sprawdz`, POSTEP, commit i push.

- [x] Q1 Szybkie zmiany decyzji gubią się (np. stawka VAT w KPiR „czasem się nie wybiera”) – wyścig zapisów
- [x] Q2 HR: większe okno składania oferty
- [x] Q3 Dostawcy: lista zamówień rundy z usuwaniem pozycji
- [x] Q4 Dostawcy: „Zamów brakujące” rozkłada dostawy na dni także bez prognozy dziennej (nie wszystko na 1 dzień)
- [x] Q5 Lokale: komunikat, jak wyposażyć działkę i lokal niewyposażony; stanowiska, sprzęt i zatrudnienie już
  w ostatniej rundzie budowy/urządzania – lokal rusza gotowy do sprzedaży
- [x] Q6 Lokale niewyposażone tańsze (czynsz, cena, adaptacja)
- [x] Q7 Licytacja lokali od rundy 1 (wyższa oferta wygrywa, przegrany dostaje wyjaśnienie)
- [x] Q8 Kredyt inwestycyjny bez 4 rund historii – od wzięcia lokalu, także na zakup lokalu w tej samej rundzie
  (kupowany lokal jako zastaw)
- [x] Q9 Ceny dań: od 50% do 200% ceny rynkowej (procenty w YAML)
- [x] Q10 Popyt liczony samodzielnie: bez gotowej prognozy w Menu i w Klientach i strefach
- [x] Q11 Runda 1: nazwa firmy, wgrane logo, kolor, slogan; mapa pokazuje, kto ma który lokal
- [x] Q12 Samouczek KPiR (kroki) przy samodzielnej księgowości
- [x] Q13 Zakładka „Wnioski z rundy” – co nie wyszło i co zrobić, żeby się udało (zachęcająco)

## Krok 5 – kalibracja, część pierwsza: B1–B5 (Plan optymalizacji, część B; instrukcja: `zadania/B_kalibracja.md`)

Po każdym: testy, ruff, `sprawdz`, wpis w `raporty/kalibracja/dziennik.md`, POSTEP, commit, `git pull --rebase` i push.
Kolejność (zmiana z 29.10.2026): B1, B2, Z1–Z7, B3 (część do pomiaru), B4, B5 (**zatwierdza autor**), potem część A,
**STOP** (autor wybiera pozycje U), U, K, B6–B12 (każdy z dokończeniem B3 dla obszaru), B13, B14, B15.

- [x] B1 Inwentarz decyzji, opcji, parametrów i zamierzonych kompromisów + hipotezy „za dobrych” strategii (`raporty/kalibracja/inwentarz.md`); uzupełnić docstring `silnik/decyzje.py` o harpagon, kasyno, detektyw, leasing, przejecie, higiena, wlasciciel_stanowisko, wypowiedz — zrobione 29.10.2026: inwentarz wszystkich decyzji z kompromisami (obszary B6–B12), 17 hipotez (H1–H17) z 9 gier botów i kodu, docstring uzupełniony, dziennik z pytaniem P1 (ZUS przy zleceniu).
- [x] B2 Testy mechanik na zamrożonej kopii danych (`testy/dane_zamrozone/`); profilowanie silnika; wymuszanie decyzji bota; narzędzie porównań par gier `balans/warianty.py` (konteksty, 4/6/8 firm, wiele ziaren, równolegle, CSV + md, wznawianie pełnego pomiaru) z testami; szybki pomiar „punkt zero” na dzisiejszych zasadach — zrobione 29.10.2026: zamrożone dane testów mechanik (znacznik `dane_gry` dla testów zasad), `balans/odcisk.py`, `balans/warianty.py` z 28 wariantami i testami, profil (40% czasu w `linprog`), punkt zero 522 gier w 9,7 min (dominują zlecenie, mBank, e-Księgi24 i pełne polisy; dziennik).

### Zmiany zasad (ustalone z autorem 29.10.2026, przed pomiarem startowym)

- [x] Z1 Karta wyników: strata daje ujemny wynik działalności (proporcjonalnie; lepsze wskaźniki nie pogłębiają minusa); budynek w majątku; majątek po amortyzacji; zakup sprzętu nie pompuje rozwoju; odsetki Harpagona obniżają kartę — zrobione 29.10.2026: strata = waga × wynik ekonomiczny (`karta_wynikow → strata`), majątek do karty po amortyzacji z lokalami, budynkami i gruntem, inwestycje tylko ponad dawny szczyt majątku, odsetki Harpagona w karcie; testy, instrukcja, propozycja do notatki w `raporty/kalibracja/notatki_do_zmiany.md`.
- [x] Z2 Majątek netto w wynikach firmy, panelu mistrza gry i eksporcie CSV (lokal po amortyzacji, lokaty i kaucje, wpłata inwestora jako dług) — zrobione 29.10.2026: `silnik/wyniki/majatek.py` (składniki w `wyniki[r][firma]["majatek_netto"]`), kolumna i wykres w panelu mistrza gry, kolumna w obu CSV; portfel właściciela tylko w pomiarach (ukryty klub).
- [x] Z3 Debet ponad limit: blokada inwestycji i kredytów, alarm u mistrza gry, inwestor ratunkowy (gotówka za udział w przyszłych dochodach, wpłata liczona jak dług); bez odsetek karnych i zajęcia majątku — zrobione 29.10.2026: `silnik/pieniadze/inwestor.py` (alarm `w["alarm"]`, blokada w następnej rundzie, inwestor od mistrza gry przez `Gra.ustaw_inwestora` i panel, udział 30% dochodu przez 8 rund, niezwrócona wpłata jako dług); warunki w `finanse.inwestor_ratunkowy`, odsetki karne banku zostają.
- [x] Z4 Liczba lokali na mapie zależna od liczby firm (4–8), popyt bez zmian — zrobione 29.10.2026: klucz `od_firm` w `dane/mapa/lokale.yaml` (8 firm – 38 lokali, 6–7 – 29, 4–5 – 20, wszystkie strefy), filtr `lokale.na_mapie` w ofercie, decyzjach, botach i mapie.
- [x] Z5 Bot „jak człowiek” (prognoza z zeszłotygodniowej sprzedaży zamiast `pp.prognoza`), wersje słaba / średnia / dobra — zrobione 29.10.2026: poziomy `czlowiek_slaby/sredni/dobry` (tylko do pomiarów) prognozują z popytu w raportach i potencjału z zakładki Klienci (`boty._prognoza_czlowieka`), `warianty.py --rywale`; dobra > średnia w 8/8 par.
- [x] Z6 Kalendarz miejski i święta do kwietnia 2026 (`dane/kalendarz/kalendarz.yaml`) — zrobione 29.10.2026: 6 domowych meczów Motoru wiosną 2026 (prawdziwy terminarz), Finał WOŚP, Popielec, semestr letni, Jarmark Wielkanocny, Wielki Piątek – 01–04.2026 ma 23 wydarzenia, tyle co jesień.
- [x] Z7 Miejsce na pulpicie drużyny liczone jak ranking mistrza gry (karta skumulowana, `api/prezentacja.py`) — zrobione 29.10.2026: wspólna funkcja `miejsca` dla pulpitu i rankingu mistrza gry (średnia karta z rund 2…N); pytanie do autora o widok drużyny po końcu gry – w dzienniku.

### Pomiar i kalibracja

- [x] B3 Boty potrafią użyć każdej opcji (kupno, niewyposażony, działka, banki, dostawcy, biuro…) z zachowaniem charakteru; przed B4 – część do pomiaru i poziomy łatwy < średni < trudny — zrobione 29.10.2026 (część przed B4): poprawiona korekta prognozy trudnego, średni z prognozą ±10%, trudny otwiera drugi lokal, gdy stać – średni < trudny w 37/40 par (było 19/40), przy każdej strategii; reszta B3 to krok 0 obszarów B6–B12
- [x] B4 Pomiar startowy: dominacje, hipotezy z B1, krzywa trudności, strategie, 4/6/8 firm, realia (`raporty/kalibracja/stan_poczatkowy.md`); tag `kalibracja-start` — zrobione 29.10.2026: 7090 gier; gra za łatwa (pierwszy plus człowieka średniego w rundzie 2 w 62% gier), dominują umowa zlecenie, drugi lokal, mBank i e-Księgi24, przy 4 firmach gra wyraźnie łatwiejsza (pytanie do autora w dzienniku)
- [x] B5 Gospodarka i trudność (popyt, koszty poza prawem, kapitał; pierwszy plus bota „jak człowiek” średniego w rundzie 4–6) – **do zatwierdzenia przez autora; część A czeka na zatwierdzenie**
  - Zrobione i zatwierdzone przez autora 29.10.2026: nowa mechanika rozruchu nowego lokalu (40% popytu w 1. tygodniu, +10 p.p. co tydzień), pule stref ×0,9 i zakupy botów w budżecie – pierwszy plus średniego w rundach 4–6 w 65/100 gier (było 19/100), słaby bez alarmu poza strategią agresywną (dziennik B5).
  - Dopisek H17 (29.10.2026, wybór autora „poprawić bota agresywnego”): słaby „jak człowiek” zamawia najwyżej zeszłotygodniową sprzedaż × 1,1 dania, które traciło klientów w kolejce – alarmy słabego agresywnego 8/100 → 0/100, psucie towaru 27% → 7% przychodu, słaba < średnia w 85/100 par (dziennik H17).

## Krok 6 – analiza oczami gracza (Plan optymalizacji, część A; instrukcja: `zadania/A_analiza_gracza.md`)

Fable 5.1 w OpenCode, po zatwierdzeniu B5; gra na wersji po zmianach zasad Z i gospodarce z B5. Polecenia: `zadania/README.md`.

- [ ] A1 Przygotowanie: notatki, instrukcja gracza, zakładki JS i widok `v`, uruchomienie gry
- [ ] A2 Trzy pełne gry (nowicjusz, optymalizator, nauczyciel z drużynami o zaplanowanych błędach) z dziennikami w `raporty/analiza/`
- [ ] A3 Raport `raporty/analiza_gracza.md` – problemy, zmiany, nowe funkcje, „za dobre” strategie, pytania
- [ ] **STOP:** autor czyta raport z A i wybiera pozycje U

## Ulepszenia z analizy (zatwierdzone przez autora – dopisywane po A3 jako U1, U2…)

- [ ] K Kontrola po U: szybki pomiar wszystkich obszarów i celów trudności z B5; poprawka liczb B5 tylko za zgodą autora; „za dobre” strategie z A w inwentarzu

## Krok 5 – kalibracja, część druga: obszary B6–B15

- [ ] B6 Lokale (typ × forma × strefa, licytacje, przejęcia)
- [ ] B7 Menu i ceny (dania, marże, widełki, promocje)
- [ ] B8 Zaopatrzenie (dostawcy, gwiazdki, świeżość, magazyn, auto-zamawianie, handel)
- [ ] B9 Ludzie (rekrutacja, umowy, pensje, premie, szkolenia, headhunter, czas właściciela); decyzja autora z 29.10.2026 (P1): umowa zlecenie dostaje składki ZUS pracodawcy jak w prawie 2026 (bez składek tylko student do 26 lat) – to część zamrożonego prawa, nie kalibracja
- [ ] B10 Marketing (reklama, agencje, promocje, udogodnienia, wyposażenie)
- [ ] B11 Finanse (banki, kredyty, lokaty, odnawialny bez limitu; Harpagon i kasyno – ryzykowne, ale czasem opłacalne)
- [ ] B12 Księgowość i urzędy (samodzielnie / biuro z OC i bez, kary, sanepid, higiena, ubezpieczenia; łamanie zasad średnio się nie opłaca)
- [ ] B13 Karta wyników – tylko wagi składowych (brak „nabijania”, zgodność z majątkiem netto), potem szybki pomiar wszystkich obszarów
- [ ] B14 Boty po kalibracji (poziomy wyraźnie różne, każda strategia wygrywa w jakimś kontekście; cele B5 nadal spełnione)
- [ ] B15 Raport końcowy (przed/po od tagu `kalibracja-start`), `zrodlo`/`pewnosc` w YAML, propozycje zmian w notatkach, instrukcja gracza
