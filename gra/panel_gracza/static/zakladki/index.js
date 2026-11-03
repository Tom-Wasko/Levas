// Rejestr zakładek i układ menu (układ jak w REVAS; każda nowa funkcja ma decyzje i wyniki).
import { dashboard, karta_wynikow, lista_bledow, wnioski, wyslij } from "./ogolne.js";
import { oferta } from "./oferta.js";
import { sprzet, srodki_trwale, stanowiska, wyposazenie } from "./inwestycje.js";
import { szkolenia, udogodnienia, zatrudnienie } from "./hr.js";
import { dostawcy } from "./dostawcy.js";
import { agencje, promocje } from "./marketing.js";
import { sprzedaz } from "./sprzedaz.js";
import { bank, biuro, kpir, raport } from "./finanse.js";
import { lokale } from "./lokale.js";
import { przejecia } from "./przejecia.js";
import { mapa } from "./mapa.js";
import { klienci } from "./klienci.js";
import { swiezosc } from "./swiezosc.js";
import { czas_wlasciciela } from "./czas.js";
import { rynek_pracy } from "./rynek_pracy.js";
import { harpagon } from "./harpagon.js";
import { podatki, vat } from "./podatki.js";
import { zdarzenia } from "./zdarzenia.js";
import { ubezpieczenia } from "./ubezpieczenia.js";
import { urzad } from "./urzad.js";
import { wlasciciel } from "./wlasciciel.js";
import { kasyno } from "./kasyno.js";
import { handel } from "./handel.js";
import { kalendarz } from "./kalendarz.js";
import { konkurencja } from "./konkurencja.js";
import { lokal_przeglad, zlozona } from "./lokal.js";

const ZAKLADKI = { dashboard, mapa, karta_wynikow, wnioski, lokale, przejecia, urzad, klienci, kalendarz, konkurencja, oferta, stanowiska, sprzet, wyposazenie, srodki_trwale, zatrudnienie, rynek_pracy, udogodnienia, szkolenia,
  dostawcy, swiezosc, czas_wlasciciela, zdarzenia, agencje, promocje, sprzedaz, handel, raport, kpir, vat, podatki, bank, harpagon, biuro, ubezpieczenia, wlasciciel, kasyno, lista_bledow, wyslij };

// nazwa ikony (zakladki/ikony.js) dla każdej zakładki
export const IKONY = { lokal_przeglad: "lokale", lokal_menu: "oferta", lokal_dostawy: "dostawcy", lokal_ludzie: "zatrudnienie", lokal_sprzet: "sprzet",
  dashboard: "dashboard", mapa: "mapa", wnioski: "ok", lokale: "lokale", przejecia: "lokale", urzad: "urzad", klienci: "klienci", kalendarz: "kalendarz", konkurencja: "analiza", karta_wynikow: "karta", oferta: "oferta", stanowiska: "stanowiska", sprzet: "sprzet",
  wyposazenie: "wyposazenie", srodki_trwale: "srodki_trwale", zatrudnienie: "zatrudnienie", rynek_pracy: "rynek_pracy", udogodnienia: "udogodnienia", szkolenia: "szkolenia", dostawcy: "dostawcy", swiezosc: "swiezosc", czas_wlasciciela: "zegar", zdarzenia: "zdarzenia",
  agencje: "tradycyjny", promocje: "procent", sprzedaz: "sprzedaz", handel: "handel", raport: "raport", kpir: "kpir", vat: "procent", podatki: "podatki", bank: "bank", harpagon: "harpagon",
  biuro: "biuro", ubezpieczenia: "tarcza", wlasciciel: "portfel", kasyno: "klucz", lista_bledow: "bledy", wyslij: "wyslij" };

// od której rundy zakładka jest dostępna (podpowiedź w menu)
export const OD_RUNDY = { karta_wynikow: 3, agencje: 3, promocje: 2, udogodnienia: 3, wyposazenie: 4, szkolenia: 7,
  przejecia: 4, sprzet: 2, zatrudnienie: 2, rynek_pracy: 2, dostawcy: 2, swiezosc: 2, sprzedaz: 2, raport: 2, kpir: 2, vat: 2, zdarzenia: 2, ubezpieczenia: 2, handel: 5 };

// zakładka → element harmonogramu gry z lokalami (silnik/harmonogram.py); tydzień z widoku zastępuje OD_RUNDY
export const ELEMENT = { karta_wynikow: "karta_wynikow", agencje: "reklama", promocje: "promocje", udogodnienia: "hr_udogodnienia",
  wyposazenie: "inwestycje_wyposazenie", szkolenia: "hr_szkolenia", przejecia: "przejecia", sprzet: "inwestycje_sprzet",
  zatrudnienie: "hr_zatrudnienie", dostawcy: "dostawcy", sprzedaz: "sprzedaz", zdarzenia: "parki", handel: "handel" };

// Z3: podzakładki Lokali złożone z dawnych zakładek (części działają na wybranym lokalu – lokal_wybor.js)
const odRundyCzesci = (v, k) => v.harmonogram?.[ELEMENT[k]] ?? OD_RUNDY[k];
Object.assign(ZAKLADKI, {
  lokal_przeglad,
  lokal_menu: zlozona({ tytul: "Menu i ceny", tytulPelny: "Lokale – menu i ceny", odRundy: odRundyCzesci,
    info: "Dania w menu wybranego lokalu, prognoza sprzedaży i ceny. Każdy lokal może mieć inne menu i inne ceny.",
    czesci: { oferta, sprzedaz } }),
  lokal_dostawy: zlozona({ tytul: "Dostawy i magazyn", tytulPelny: "Lokale – dostawy i magazyn", odRundy: odRundyCzesci,
    info: "Zamówienia składników z dostawą do wybranego lokalu, jego magazyn i świeżość oraz przewozy towaru między lokalami.",
    czesci: { dostawcy, swiezosc } }),
  lokal_ludzie: zlozona({ tytul: "Ludzie", tytulPelny: "Lokale – ludzie", odRundy: odRundyCzesci,
    info: "Pracownicy na stanowiskach wybranego lokalu, szkolenia (dla całej firmy) i udogodnienia dla pracowników lokalu.",
    czesci: { zatrudnienie, szkolenia, udogodnienia } }),
  lokal_sprzet: zlozona({ tytul: "Sprzęt", tytulPelny: "Lokale – stanowiska, sprzęt i wyposażenie", odRundy: odRundyCzesci,
    info: "Stanowiska, sprzęt kuchni i kasy oraz wyposażenie dla klientów w wybranym lokalu.",
    czesci: { stanowiska, sprzet, wyposazenie } }),
});

// dawny klucz zakładki → podzakładka Lokali, w której jest teraz (linki, „Popraw” z listy błędów, adres #…)
export const ALIAS = { oferta: "lokal_menu", sprzedaz: "lokal_menu", dostawcy: "lokal_dostawy", swiezosc: "lokal_dostawy",
  zatrudnienie: "lokal_ludzie", szkolenia: "lokal_ludzie", udogodnienia: "lokal_ludzie",
  stanowiska: "lokal_sprzet", sprzet: "lokal_sprzet", wyposazenie: "lokal_sprzet" };

// Układ menu (przebudowa 2.11.2026, raporty/przebudowa_zakladek.md): sekcje Twoje lokale / Miasto / Firma.
// { sekcja } – nagłówek sekcji (w menu poziomym kreska), { sekcja: "" } – sama kreska.
export const MENU = [
  { klucz: "mapa", tytul: "Mapa miasta", ikona: "mapa", klasa: "mapa" },
  { klucz: "wyniki", tytul: "Wyniki", ikona: "karta", pod: ["karta_wynikow", "wnioski"] },
  { sekcja: "Twoje lokale" },
  { klucz: "lokal", tytul: "Lokale", ikona: "lokale", pod: ["lokal_przeglad", "lokal_menu", "lokal_dostawy", "lokal_ludzie", "lokal_sprzet"] },
  { sekcja: "Miasto" },
  { klucz: "rynek", tytul: "Rynek", ikona: "klienci", pod: ["klienci", "kalendarz", "konkurencja", "rynek_pracy"] },
  { klucz: "zdarzenia", tytul: "Parki i zdarzenia", ikona: "zdarzenia" },
  { klucz: "marketing", tytul: "Marketing", ikona: "marketing", pod: ["agencje", "promocje"] },
  { klucz: "inwestycje", tytul: "Inwestycje", ikona: "inwestycje", pod: ["lokale", "przejecia", "srodki_trwale"] },
  { klucz: "handel", tytul: "Handel z drużynami", ikona: "handel" },
  { sekcja: "Firma" },
  { klucz: "firma", tytul: "Firma", ikona: "zegar", pod: ["czas_wlasciciela", "urzad", "ubezpieczenia"] },
  { klucz: "finanse", tytul: "Finanse", ikona: "finanse", pod: ["raport", "bank", "harpagon", "wlasciciel"] },
  { klucz: "ksiegowosc", tytul: "Księgowość", ikona: "kpir", pod: ["biuro", "kpir", "vat", "podatki"] },
  { klucz: "kasyno", tytul: "Nocna 13", ikona: "klucz" },   // widoczna tylko z zaproszeniem (ukryta)
  { sekcja: "" },
  { klucz: "lista_bledow", tytul: "Lista błędów", ikona: "bledy" },
  { klucz: "wyslij", tytul: "Wyślij decyzje", ikona: "wyslij", klasa: "wyslij" },
];

export default ZAKLADKI;
