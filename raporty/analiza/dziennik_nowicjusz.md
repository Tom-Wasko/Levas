# Dziennik – persona „Nowicjusz, 16 lat”

Gra „A2 nowicjusz”, ziarno 101, 18 rund, 4 firmy (Z4: mało lokali na mapie). Ja: **Kebab u Ziomka**.
Rywale: Sułtan (bot tani, „jak człowiek – słaby”), Bafra (zrównoważony, „jak człowiek – średni”),
Döner Max (premium, średni). Skrypt: `skrypty/nowicjusz.py`, pełny log: `log_nowicjusz.json`,
zrzuty: `zrzuty/nowicjusz_*.png`.

Jak grałem: tam, gdzie nowicjusz klika „to, co podpowiada gra”, użyłem kalkulatora botów „jak człowiek –
słaby” (podobny poziom). Na to nałożyłem typowe błędy: najtańszy gotowy lokal, księgowość samodzielnie
bez zapisów, za dużo dań w rundzie 1, ceny +20% zaokrąglone w górę, wypłata dla siebie, Harpagon,
zawsze pierwsza opcja zdarzenia, drugi lokal „bo idzie dobrze”.

**Wynik:** 4. miejsce z 4. Karta skumulowana **−0,297** (Sułtan 0,149, Bafra 0,44, Döner Max 1,109).
Majątek netto 36 328 zł (start 40 000) – „na minusie”. Alarmu nie było.

## Runda po rundzie

**R1 (tydzień 1, przygotowanie).** Widzę Dashboard z planem rundy i czerwoną liczbę na Liście błędów.
Pierwszy zapis (tylko nazwa, misja, kolor) – lista mówi wprost: nie masz lokalu, menu puste, nie wybrano
banku ani biura. To jest dobre – wiem, co zrobić. Biorę najtańszy gotowy lokal (Budka pod Areną,
Zygmuntowskie, 2200 zł czynszu), księgowość „samodzielnie”, do menu dokładam rollo, falafela i talerz.
- *Czego nie rozumiem:* zaraz po wybraniu **pierwszego** lokalu Lista błędów pokazuje: „Właściciel leży
  na kanapie z mrożonym kebabem na czole… Kolejny lokal można wziąć co 3 rundy – najwcześniej w rundzie 4”.
  Nic nie zrobiłem źle, a wygląda to na błąd. Myślę, że lokal nie został przyjęty.
- Dodatkowe dania znikają z komunikatem „W rundzie 1 można wybrać tylko dania: Kebab w bułce, Frytki,
  Napój” i „liczba dań może wzrosnąć najwyżej o 3 – nadmiarowe nie zostały dodane”. Dwa komunikaty o tym
  samym, a w zakładce Menu i ceny (zrzut `nowicjusz_r01_lokal_menu.png`) przyciski „Wybierz” przy innych
  daniach są tylko wyszarzone, bez podpisu „od tygodnia 3”.
- Menu i ceny pokazuje „Popyt roczny 36 000” i „czas obsługi przy kasie 1,2 min” – dla 16-latka to
  liczby bez punktu zaczepienia (popyt roczny czego? w całym mieście?).

**R2 (otwarcie).** Podnoszę ceny o 20% i zaokrąglam w górę. Pierwsza sprzedaż: dochód −3430 zł, karta
−0,743, 3. miejsce. Lista błędów: „Nie złożono deklaracji za rundę 1 – urząd rozliczy z urzędu i wystawi
mandat 500 zł” i „Niezaksięgowane dokumenty za rundę 1: 7 z 7”.
- *Rozumiem*, że czegoś nie zrobiłem w księgowości. Przycisk „Popraw” prowadzi do Księgowość ▸ Biuro
  (wybór biura), ale ani komunikat, ani przycisk nie mówią, że zamiast biura mogę zaksięgować dokumenty
  w Księgowość ▸ KPiR – i że biuro jest tańsze od mandatu.
- Ludzie (zrzut `nowicjusz_r02_lokal_ludzie.png`) odblokowują się dopiero w tygodniu 2 – w tygodniu
  przygotowawczym nie mogłem nikogo zatrudnić, więc pierwszy tydzień sprzedaży startuje z rekrutacją
  „na wczoraj”. Puste stanowiska z „+” i „Stań sam (właściciel)” są za to bardzo czytelne.
- Ostrzeżenia o przeterminowaniu w ułamkach opakowań („ok. 0,8 opak. bułki, 37 zł”) – są co rundę do
  końca gry, po kilka sztuk. Po 3 rundach przestałem je czytać.

**R3.** Wypłacam sobie 2000 zł. Karta 0,026 (dochód +237 zł). Zakładka Karta wyników (zrzut
`nowicjusz_r03_karta_wynikow_wyniki.png`) – tabela „Skąd Twoja karta” jest bardzo dobra: widzę, że
„Dania wyłączone z braku składnika 9,5%” kosztuje −0,029. Ale pięć kolumn wskaźników 0,914 / 0,928 / 0,535
bez skali – nie wiem, czy 0,535 rozwoju to dużo czy mało.
- Mandat za deklarację znowu (R1–R5 łącznie 5 × 500 zł). W widoku `v` pole `wyniki.kpir.dochod_netto`
  w rundach 2–6 jest puste (`None`). To celowe (`api/prezentacja.py:284`): przy samodzielnej księgowości
  wynik podatkowy jest ukryty do złożenia deklaracji. Skutek dla nowicjusza, który deklaracji nie składa:
  przez 5 rund nie widzi na Dashboardzie swojego dochodu, a karta i panel mistrza gry go znają.

**R4.** Gotówka 28 525 zł – boję się, biorę 5000 zł od Harpagona (zrzut `nowicjusz_r04_harpagon.png`).
Gra mnie przed tym nie zatrzymuje (dobrze – to lekcja), ale nie pokazuje też, ile wyniesie dług za 4 rundy
w złotych przy przycisku. Dochód +1197 zł, karta 0,002.

**R5.** Dochód +2671 zł, karta 0,04. Piąty mandat za deklarację. Myślę: „po co mi to biuro, mandat to
tylko 500 zł”. A to nieprawda – biura kosztują ok. 160–230 zł na tydzień (ryczałty miesięczne 690–984 zł
× 12/52, Trybunał 6,15 zł za dokument), więc mandat jest ponad dwa razy droższy. Nigdzie tego nie widzę
obok siebie.

**R6.** Zmieniam na najtańsze biuro (Księgowość Pod Trybunałem). Mandaty znikają. Spadam na 4. miejsce,
chociaż mam dochód +1836 zł – rywale rosną szybciej. Urząd i sanepid (zrzut `nowicjusz_r06_urzad.png`) –
bardzo czytelne, z humorem; wiem, że „Mop i grafik na lodówce” wystarcza.

**R7–R11.** Najlepszy okres: dochód 400–4500 zł, karta 0,005–0,444. Mięso kebab przeterminowuje się co
rundę (do 1077 zł w R8 – „3,5 opak.”). W R8 ulotki (10 emisji) – nie widzę w wynikach, czy pomogły.
W R9 spłacam Harpagona: 5000 → 6381 zł po 5 rundach (+28%). Zdarzenie „Zaginął Kebab”: wybrałem pierwszą
opcję (5 h szukania jamnika), ale „nie starcza czasu właściciela” – gra wybrała drugą za mnie. Dowiaduję się
tego dopiero z listy błędów po fakcie.

**R12.** Mam 46 058 zł – „idzie mi lepiej”, biorę drugi lokal: Pawilon na Witosa (Felin, niewyposażony).
Komunikat mówi wprost, co zrobić („kup stanowiska kuchni i kasy (Inwestycje), sprzęt na stanowiska
i zatrudnij pracowników (Kadry)”) – ale nazwy zakładek są stare: nie ma już zakładki „Kadry”,
a stanowiska są w Lokale ▸ Sprzęt.

**R13–R14.** Pawilon stoi pusty, płacę czynsz. Lista błędów: po **dwie linijki na każde danie**
(„brak sprzętu (Rożen)”, „w kuchni nie ma nikogo z zawodem kucharz”) – 12+ linijek o jednym problemie
„lokal niewyposażony”. Nie wiem, od czego zacząć.

**R15.** Kalkulator kupuje sprzęt i stanowiska w Pawilonie (Rożen 4500, Kasa 1500, Lada 2500, Tablica 600,
stanowiska po 1000 zł). Wszystko to poniżej progu 10 000 zł, więc idzie od razu w koszty KPiR: **dochód
−11 448 zł, karta −2,481** w jednym tygodniu. To więcej niż suma wszystkich moich dodatnich tygodni
(R3–R14 razem ok. +2,2). Skumulowana spada z 0,109 na −0,076. *Tego w ogóle nie rozumiem* – instrukcja
(rozdz. 3, tabela karty) mówi, że nowy sprzęt, wyposażenie i kolejne lokale **podnoszą** rozwój firmy, a karta mnie za to ukarała.
Dowiaduję się też, że Pawilon nie ma chłodni – dostawy jadą do płatnej wynajętej chłodni.

**R16–R18.** Dwa lokale, braki składników w obu, straty −5471, −9841, −3109 zł. Wracam do cen
rynkowych – nie pomaga. Kończę 4., gotówka 15 728 zł, majątek netto 36 328 zł.

## Podsumowanie nowicjusza
- **Wiem, co zrobić w rundzie 1** – Lista błędów i Dashboard prowadzą dobrze (poza fałszywym alarmem
  o „kanapie”).
- **W rundzie 2** nie rozumiem, czemu mam stratę – karta pokazuje −0,743 bez słowa, że pierwszy tydzień
  sprzedaży z rozruchem (40% klientów) prawie zawsze jest na minusie.
- **W rundzie 5** płacę piąty mandat i nikt mi nie mówi wprost: „wybierz biuro albo zaksięguj dokumenty
  w KPiR”. Samodzielna księgowość bez zapisów kosztuje 500 zł/tydz. – ponad dwa razy więcej niż biuro.
- **Największa frustracja:** drugi lokal. Gra zachęca do rozwoju, a karta za zakup wyposażenia daje
  jednorazowy ogromny minus (strata liczona z wagą 1,0, a zysk mnożony przez wskaźniki ok. 0,55).
- **Zniechęca:** lista błędów, w której ostrzeżenia, humor, zdarzenia i prawdziwe błędy wyglądają tak samo
  (5–20 pozycji co rundę).
- **Wynik był zrozumiały?** Rundy R3–R11 – tak (karta rośnie z dochodem). R2 i R15 – nie.
