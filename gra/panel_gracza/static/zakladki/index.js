// Rejestr zakładek i układ menu (układ jak w REVAS).
import { analiza, dashboard, karta_wynikow, lista_bledow, wyslij } from "./ogolne.js";
import { oferta } from "./oferta.js";
import { sprzet, srodki_trwale, stanowiska, wyposazenie } from "./inwestycje.js";
import { szkolenia, udogodnienia, zatrudnienie } from "./hr.js";
import { dostawcy } from "./dostawcy.js";
import { agencje, internetowy, promocje, tradycyjny } from "./marketing.js";
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
import { podatki } from "./podatki.js";
import { zdarzenia } from "./zdarzenia.js";
import { ubezpieczenia } from "./ubezpieczenia.js";
import { urzad } from "./urzad.js";

const ZAKLADKI = { dashboard, mapa, karta_wynikow, lokale, przejecia, urzad, klienci, oferta, stanowiska, sprzet, wyposazenie, srodki_trwale, zatrudnienie, rynek_pracy, udogodnienia, szkolenia,
  dostawcy, swiezosc, czas_wlasciciela, zdarzenia, agencje, promocje, tradycyjny, internetowy, sprzedaz, raport, kpir, podatki, bank, harpagon, biuro, ubezpieczenia, lista_bledow, wyslij, analiza };

// nazwa ikony (zakladki/ikony.js) dla każdej zakładki
export const IKONY = { dashboard: "dashboard", mapa: "mapa", lokale: "lokale", przejecia: "lokale", urzad: "urzad", klienci: "klienci", karta_wynikow: "karta", oferta: "oferta", stanowiska: "stanowiska", sprzet: "sprzet",
  wyposazenie: "wyposazenie", srodki_trwale: "srodki_trwale", zatrudnienie: "zatrudnienie", rynek_pracy: "rynek_pracy", udogodnienia: "udogodnienia", szkolenia: "szkolenia", dostawcy: "dostawcy", swiezosc: "swiezosc", czas_wlasciciela: "zegar", zdarzenia: "zdarzenia",
  agencje: "tradycyjny", promocje: "procent", tradycyjny: "tradycyjny", internetowy: "internetowy", sprzedaz: "sprzedaz", raport: "raport", kpir: "kpir", podatki: "podatki", bank: "bank", harpagon: "harpagon",
  biuro: "biuro", ubezpieczenia: "tarcza", lista_bledow: "bledy", wyslij: "wyslij", analiza: "analiza" };

// od której rundy zakładka jest dostępna (podpowiedź w menu)
export const OD_RUNDY = { karta_wynikow: 3, agencje: 3, promocje: 2, udogodnienia: 3, wyposazenie: 4, tradycyjny: 5, internetowy: 6, szkolenia: 7,
  przejecia: 4, sprzet: 2, zatrudnienie: 2, rynek_pracy: 2, dostawcy: 2, swiezosc: 2, sprzedaz: 2, raport: 2, kpir: 2, analiza: 2, zdarzenia: 2, ubezpieczenia: 2 };

export const MENU = [
  { klucz: "mapa", tytul: "Mapa miasta", ikona: "mapa", klasa: "mapa" },
  { klucz: "karta_wynikow", tytul: "Karta wyników", ikona: "karta" },
  { klucz: "lokale", tytul: "Lokale", ikona: "lokale", pod: ["lokale", "przejecia", "urzad"] },
  { klucz: "klienci", tytul: "Klienci i strefy", ikona: "klienci" },
  { klucz: "oferta", tytul: "Oferta", ikona: "oferta" },
  { klucz: "inwestycje", tytul: "Inwestycje", ikona: "inwestycje", pod: ["stanowiska", "sprzet", "wyposazenie", "srodki_trwale"] },
  { klucz: "hr", tytul: "HR", ikona: "hr", pod: ["zatrudnienie", "rynek_pracy", "udogodnienia", "szkolenia"] },
  { klucz: "dostawcy", tytul: "Dostawcy", ikona: "dostawcy" },
  { klucz: "swiezosc", tytul: "Magazyn i świeżość", ikona: "swiezosc" },
  { klucz: "czas_wlasciciela", tytul: "Czas właściciela", ikona: "zegar" },
  { klucz: "zdarzenia", tytul: "Zdarzenia", ikona: "zdarzenia" },
  { klucz: "marketing", tytul: "Marketing", ikona: "marketing", pod: ["agencje", "promocje", "tradycyjny", "internetowy"] },
  { klucz: "sprzedaz", tytul: "Sprzedaż", ikona: "sprzedaz" },
  { klucz: "finanse", tytul: "Finanse", ikona: "finanse", pod: ["raport", "kpir", "podatki", "bank", "harpagon", "biuro", "ubezpieczenia"] },
  { klucz: "lista_bledow", tytul: "Lista błędów", ikona: "bledy" },
  { klucz: "wyslij", tytul: "Wyślij decyzje", ikona: "wyslij", klasa: "wyslij" },
  { klucz: "analiza", tytul: "Analiza", ikona: "analiza" },
];

export default ZAKLADKI;
