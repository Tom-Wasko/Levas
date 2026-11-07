// Rejestr zakładek i układ menu (UF15, 6.11.2026: Miasto · Twój lokal · Firma · Wyniki; każda funkcja ma decyzje i wyniki).
import { dashboard, karta_wynikow, lista_bledow, ranking, wnioski, wyslij } from "./ogolne.js";
import { oferta } from "./oferta.js";
import { sprzet, stanowiska, wyposazenie } from "./inwestycje.js";
import { szkolenia, udogodnienia, zatrudnienie, zespol } from "./hr.js";
import { dostawcy } from "./dostawcy.js";
import { agencje, internet, promocje } from "./marketing.js";
import { sprzedaz } from "./sprzedaz.js";
import { bank, biuro, kpir, raport } from "./finanse.js";
import { lokale } from "./lokale.js";
import { licytacje, przejecia } from "./przejecia.js";
import { mapa } from "./mapa.js";
import { klienci } from "./klienci.js";
import { przewozy, swiezosc } from "./swiezosc.js";
import { czas_wlasciciela } from "./czas.js";
import { rynek_pracy } from "./rynek_pracy.js";
import { harpagon } from "./harpagon.js";
import { podatki, vat } from "./podatki.js";
import { sprawy } from "./zdarzenia.js";
import { ubezpieczenia } from "./ubezpieczenia.js";
import { sanepid, urzad } from "./urzad.js";
import { wlasciciel } from "./wlasciciel.js";
import { kasyno } from "./kasyno.js";
import { handel } from "./handel.js";
import { kalendarz } from "./kalendarz.js";
import { konkurencja } from "./konkurencja.js";
import { stan_lokalu, zlozona } from "./lokal.js";
import { gielda } from "./gielda.js";

const ZAKLADKI = { dashboard, mapa, karta_wynikow, wnioski, ranking, lokale, licytacje, przejecia, urzad, sanepid, klienci, kalendarz, konkurencja, oferta,
  stanowiska, sprzet, wyposazenie, zatrudnienie, zespol, rynek_pracy, udogodnienia, szkolenia, dostawcy, swiezosc, przewozy,
  czas_wlasciciela, sprawy, agencje, internet, promocje, sprzedaz, handel, raport, kpir, vat, podatki, bank, harpagon, biuro, ubezpieczenia,
  wlasciciel, gielda, kasyno, lista_bledow, wyslij };

// nazwa ikony (zakladki/ikony.js) dla każdej zakładki
export const IKONY = { lokal_przeglad: "lokale", lokal_menu: "oferta", zaop_dostawy: "dostawcy", zaop_magazyn: "swiezosc", zaop_przewozy: "dostawcy",
  wnetrze_sprzet: "sprzet", wnetrze_wyposazenie: "wyposazenie", stan_lokalu: "lokale",
  dashboard: "dashboard", mapa: "mapa", wnioski: "ok", lokale: "lokale", licytacje: "lokale", przejecia: "lokale", urzad: "urzad", sanepid: "swiezosc",
  klienci: "klienci", kalendarz: "kalendarz", konkurencja: "analiza", karta_wynikow: "karta", ranking: "wykres", oferta: "oferta", stanowiska: "stanowiska", sprzet: "sprzet",
  wyposazenie: "wyposazenie", zatrudnienie: "zatrudnienie", zespol: "zatrudnienie", rynek_pracy: "rynek_pracy",
  udogodnienia: "udogodnienia", szkolenia: "szkolenia", dostawcy: "dostawcy", swiezosc: "swiezosc", przewozy: "dostawcy", czas_wlasciciela: "zegar",
  sprawy: "zdarzenia", agencje: "tradycyjny", internet: "marketing", promocje: "procent", sprzedaz: "sprzedaz", handel: "handel", raport: "raport", kpir: "kpir",
  vat: "procent", podatki: "podatki", bank: "bank", harpagon: "harpagon", biuro: "biuro", ubezpieczenia: "tarcza", wlasciciel: "portfel",
  gielda: "wykres", kasyno: "klucz", lista_bledow: "bledy", wyslij: "wyslij" };

// od której rundy zakładka jest dostępna (w menu: szara pozycja z kłódką i „od rundy N”)
export const OD_RUNDY = { karta_wynikow: 3, ranking: 3, agencje: 5, internet: 7, promocje: 3, udogodnienia: 3, wyposazenie: 4, szkolenia: 7,
  przejecia: 4, sprzet: 2, zatrudnienie: 1, zespol: 1, rynek_pracy: 1, dostawcy: 2, swiezosc: 2, sprzedaz: 2, raport: 2, kpir: 2, vat: 2,
  sprawy: 2, ubezpieczenia: 4, handel: 6 };

// zakładka → element harmonogramu gry z lokalami (silnik/harmonogram.py); tydzień z widoku zastępuje OD_RUNDY
export const ELEMENT = { karta_wynikow: "karta_wynikow", ranking: "karta_wynikow", agencje: "reklama", internet: "internet", promocje: "promocje", udogodnienia: "hr_udogodnienia",
  wyposazenie: "inwestycje_wyposazenie", szkolenia: "hr_szkolenia", przejecia: "przejecia", sprzet: "inwestycje_sprzet",
  zatrudnienie: "hr_zatrudnienie", zespol: "hr_zatrudnienie", dostawcy: "dostawcy", sprzedaz: "sprzedaz", sprawy: "parki", handel: "handel",
  ubezpieczenia: "ubezpieczenia" };

// Twój lokal: zakładki złożone z dawnych zakładek (części działają na wybranym lokalu – lokal_wybor.js; wybór lokalu tylko tu)
const odRundyCzesci = (v, k) => v.harmonogram?.[ELEMENT[k]] ?? OD_RUNDY[k];
// w Moim lokalu zatrudnienie to sama obsada stanowisk (wyniki rynku pracy są w Ludzie → Zespół)
const obsada = { ...zatrudnienie, tytul: "Obsada stanowisk", tytulPelny: null, wynikiGdy: () => false };
Object.assign(ZAKLADKI, {
  lokal_przeglad: zlozona({ tytul: "Mój lokal", tytulPelny: "Mój lokal – stan, sprzedaż i obsada", odRundy: odRundyCzesci,
    info: "Wszystko o wybranym lokalu: liczby z poprzedniej rundy, braki, umowa, sprawy w lokalu (bank żywności, wypadki), kto stoi na którym stanowisku i jak szła sprzedaż.",
    czesci: { stan_lokalu, sprawy, zatrudnienie: obsada, sprzedaz } }),
  lokal_menu: zlozona({ tytul: "Kuchnia", tytulPelny: "Kuchnia – menu i ceny", odRundy: odRundyCzesci,
    info: "Dania w menu wybranego lokalu, prognoza sprzedaży i ceny. Każdy lokal może mieć inne menu i inne ceny.",
    czesci: { oferta } }),
  zaop_dostawy: zlozona({ tytul: "Dostawy", tytulPelny: "Zaopatrzenie – dostawy", odRundy: odRundyCzesci,
    info: "Zamówienia składników z dostawą do wybranego lokalu: dostawca, jakość, ilość i dzień dostawy.",
    czesci: { dostawcy } }),
  zaop_magazyn: zlozona({ tytul: "Magazyn i świeżość", tytulPelny: "Zaopatrzenie – magazyn i świeżość", odRundy: odRundyCzesci,
    info: "Co leży w chłodni i zamrażarce wybranego lokalu, co się kończy i ile kosztuje wynajęta chłodnia.",
    czesci: { swiezosc } }),
  zaop_przewozy: zlozona({ tytul: "Przewozy", tytulPelny: "Zaopatrzenie – przewozy między lokalami", odRundy: odRundyCzesci,
    info: "Przewóz towaru z wybranego lokalu do innego Twojego lokalu.", czesci: { przewozy } }),
  wnetrze_sprzet: zlozona({ tytul: "Stanowiska i sprzęt", tytulPelny: "Wnętrze – stanowiska i sprzęt", odRundy: odRundyCzesci,
    info: "Stanowiska kuchni i kasy oraz sprzęt wybranego lokalu – kupno, wynajem i sprzedaż.",
    czesci: { stanowiska, sprzet } }),
  wnetrze_wyposazenie: zlozona({ tytul: "Wyposażenie", tytulPelny: "Wnętrze – wyposażenie dla klientów", odRundy: odRundyCzesci,
    info: "Stoliki, telewizor, klimatyzacja i inne rzeczy dla klientów wybranego lokalu.", czesci: { wyposazenie } }),
});
// nazwy w nowych grupach menu (plan.md, UF15); pliki zakładek mają swoje tytuły pełne
Object.assign(raport, { tytul: "Wyniki finansowe" });
Object.assign(agencje, { tytul: "Ulotki i radio" });
Object.assign(wlasciciel, { tytul: "Portfel" });
Object.assign(klienci, { tytul: "Strefy" });

// dawny klucz zakładki → zakładka, w której jest teraz (linki, „Popraw” z listy błędów, adres #…, budynki mapy)
export const ALIAS = { oferta: "lokal_menu", sprzedaz: "lokal_przeglad", zatrudnienie: "lokal_przeglad", stan_lokalu: "lokal_przeglad",
  dostawcy: "zaop_dostawy", swiezosc: "zaop_magazyn", przewozy: "zaop_przewozy",
  stanowiska: "wnetrze_sprzet", sprzet: "wnetrze_sprzet", wyposazenie: "wnetrze_wyposazenie",
  lokal_dostawy: "zaop_dostawy", lokal_sprzet: "wnetrze_sprzet", lokal_ludzie: "zespol", srodki_trwale: "kpir",
  zdarzenia: "mapa", sprawy: "lokal_przeglad" };   // UF13: parki tylko z mapy, sprawy w lokalu – w Moim lokalu

// Układ menu (UF15, raporty/ufajnianie/plan.md). { sekcja } – nagłówek sekcji (w menu poziomym kreska), { sekcja: "" } – sama kreska.
// Bez pozycji w menu: Kasyno (ukryte). Parki – klik w park na mapie (UF13).
export const MENU = [
  { klucz: "mapa", tytul: "Mapa miasta", ikona: "mapa", klasa: "mapa" },
  { sekcja: "Miasto" },
  { klucz: "nowe_lokale", tytul: "Nowe lokale", ikona: "lokale", pod: ["lokale", "licytacje", "przejecia"] },
  { klucz: "rynek", tytul: "Klienci", ikona: "klienci", pod: ["klienci", "konkurencja", "kalendarz"] },
  { sekcja: "Twój lokal" },
  { klucz: "lokal_przeglad", tytul: "Mój lokal", ikona: "lokale" },
  { klucz: "lokal_menu", tytul: "Kuchnia", ikona: "oferta" },
  { klucz: "zaopatrzenie", tytul: "Zaopatrzenie", ikona: "dostawcy", pod: ["zaop_dostawy", "zaop_magazyn", "zaop_przewozy"] },
  { klucz: "wnetrze", tytul: "Wnętrze", ikona: "sprzet", pod: ["wnetrze_sprzet", "wnetrze_wyposazenie"] },
  { sekcja: "Firma" },
  { klucz: "ludzie", tytul: "Ludzie", ikona: "zatrudnienie", pod: ["rynek_pracy", "zespol", "szkolenia", "udogodnienia"] },
  { klucz: "marketing", tytul: "Marketing", ikona: "marketing", pod: ["promocje", "agencje", "internet"] },
  { klucz: "handel", tytul: "Handel", ikona: "handel" },
  { klucz: "finanse", tytul: "Pieniądze", ikona: "finanse", pod: ["raport", "bank", "harpagon"] },
  { klucz: "ksiegowosc", tytul: "Księgowość", ikona: "kpir", pod: ["biuro", "kpir", "vat", "podatki"] },
  { klucz: "urzedy", tytul: "Urzędy", ikona: "urzad", pod: ["urzad", "sanepid", "ubezpieczenia"] },
  { klucz: "szef", tytul: "Właściciel", ikona: "portfel", pod: ["czas_wlasciciela", "wlasciciel", "gielda"] },
  { klucz: "kasyno", tytul: "Nocna 13", ikona: "klucz" },   // widoczna tylko z zaproszeniem (ukryta)
  { sekcja: "" },
  { klucz: "wyniki", tytul: "Wyniki", ikona: "karta", pod: ["karta_wynikow", "wnioski", "ranking"] },
  { klucz: "lista_bledow", tytul: "Lista błędów", ikona: "bledy" },
  { klucz: "wyslij", tytul: "Wyślij decyzje", ikona: "wyslij", klasa: "wyslij" },
];

export default ZAKLADKI;
