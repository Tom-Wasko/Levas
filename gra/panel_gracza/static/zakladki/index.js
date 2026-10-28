// Rejestr zakładek i układ menu (układ jak w REVAS; każda nowa funkcja ma decyzje i wyniki).
import { analiza, dashboard, karta_wynikow, lista_bledow, wnioski, wyslij } from "./ogolne.js";
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

const ZAKLADKI = { dashboard, mapa, karta_wynikow, wnioski, lokale, przejecia, urzad, klienci, kalendarz, konkurencja, oferta, stanowiska, sprzet, wyposazenie, srodki_trwale, zatrudnienie, rynek_pracy, udogodnienia, szkolenia,
  dostawcy, swiezosc, czas_wlasciciela, zdarzenia, agencje, promocje, sprzedaz, handel, raport, kpir, vat, podatki, bank, harpagon, biuro, ubezpieczenia, wlasciciel, kasyno, lista_bledow, wyslij, analiza };

// nazwa ikony (zakladki/ikony.js) dla każdej zakładki
export const IKONY = { dashboard: "dashboard", mapa: "mapa", wnioski: "ok", lokale: "lokale", przejecia: "lokale", urzad: "urzad", klienci: "klienci", kalendarz: "kalendarz", konkurencja: "analiza", karta_wynikow: "karta", oferta: "oferta", stanowiska: "stanowiska", sprzet: "sprzet",
  wyposazenie: "wyposazenie", srodki_trwale: "srodki_trwale", zatrudnienie: "zatrudnienie", rynek_pracy: "rynek_pracy", udogodnienia: "udogodnienia", szkolenia: "szkolenia", dostawcy: "dostawcy", swiezosc: "swiezosc", czas_wlasciciela: "zegar", zdarzenia: "zdarzenia",
  agencje: "tradycyjny", promocje: "procent", sprzedaz: "sprzedaz", handel: "handel", raport: "raport", kpir: "kpir", vat: "procent", podatki: "podatki", bank: "bank", harpagon: "harpagon",
  biuro: "biuro", ubezpieczenia: "tarcza", wlasciciel: "portfel", kasyno: "klucz", lista_bledow: "bledy", wyslij: "wyslij", analiza: "analiza" };

// od której rundy zakładka jest dostępna (podpowiedź w menu)
export const OD_RUNDY = { karta_wynikow: 3, agencje: 3, promocje: 2, udogodnienia: 3, wyposazenie: 4, szkolenia: 7,
  przejecia: 4, sprzet: 2, zatrudnienie: 2, rynek_pracy: 2, dostawcy: 2, swiezosc: 2, sprzedaz: 2, raport: 2, kpir: 2, vat: 2, analiza: 2, zdarzenia: 2, ubezpieczenia: 2, handel: 5 };

// zakładka → element harmonogramu gry z lokalami (silnik/harmonogram.py); tydzień z widoku zastępuje OD_RUNDY
export const ELEMENT = { karta_wynikow: "karta_wynikow", agencje: "reklama", promocje: "promocje", udogodnienia: "hr_udogodnienia",
  wyposazenie: "inwestycje_wyposazenie", szkolenia: "hr_szkolenia", przejecia: "przejecia", sprzet: "inwestycje_sprzet",
  zatrudnienie: "hr_zatrudnienie", dostawcy: "dostawcy", sprzedaz: "sprzedaz", zdarzenia: "parki", handel: "handel" };

export const MENU = [
  { klucz: "mapa", tytul: "Mapa miasta", ikona: "mapa", klasa: "mapa" },
  { klucz: "karta_wynikow", tytul: "Karta wyników", ikona: "karta" },
  { klucz: "wnioski", tytul: "Wnioski z rundy", ikona: "ok" },
  { klucz: "lokale", tytul: "Lokale", ikona: "lokale", pod: ["lokale", "przejecia", "urzad"] },
  { klucz: "klienci", tytul: "Klienci i strefy", ikona: "klienci", pod: ["klienci", "kalendarz", "konkurencja"] },
  { klucz: "oferta", tytul: "Menu", ikona: "oferta" },
  { klucz: "inwestycje", tytul: "Inwestycje", ikona: "inwestycje", pod: ["stanowiska", "sprzet", "wyposazenie", "srodki_trwale"] },
  { klucz: "hr", tytul: "HR", ikona: "hr", pod: ["zatrudnienie", "rynek_pracy", "udogodnienia", "szkolenia"] },
  { klucz: "dostawcy", tytul: "Dostawcy", ikona: "dostawcy", pod: ["dostawcy", "swiezosc"] },
  { klucz: "czas_wlasciciela", tytul: "Czas właściciela", ikona: "zegar" },
  { klucz: "zdarzenia", tytul: "Parki", ikona: "zdarzenia" },
  { klucz: "marketing", tytul: "Marketing", ikona: "marketing", pod: ["agencje", "promocje"] },
  { klucz: "sprzedaz", tytul: "Sprzedaż", ikona: "sprzedaz" },
  { klucz: "handel", tytul: "Handel z drużynami", ikona: "handel" },
  { klucz: "finanse", tytul: "Finanse", ikona: "finanse", pod: ["raport", "kpir", "vat", "podatki", "bank", "harpagon", "biuro", "ubezpieczenia", "wlasciciel"] },
  { klucz: "kasyno", tytul: "Nocna 13", ikona: "klucz" },   // widoczna tylko z zaproszeniem (ukryta)
  { klucz: "lista_bledow", tytul: "Lista błędów", ikona: "bledy" },
  { klucz: "wyslij", tytul: "Wyślij decyzje", ikona: "wyslij", klasa: "wyslij" },
  { klucz: "analiza", tytul: "Analiza", ikona: "analiza" },
];

export default ZAKLADKI;
