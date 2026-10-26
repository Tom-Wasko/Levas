// Rejestr zakładek i układ menu (układ jak w REVAS).
import { analiza, dashboard, karta_wynikow, lista_bledow, wyslij } from "./ogolne.js";
import { oferta } from "./oferta.js";
import { sprzet, stanowiska, wyposazenie } from "./inwestycje.js";
import { szkolenia, udogodnienia, zatrudnienie } from "./hr.js";
import { dostawcy } from "./dostawcy.js";
import { internetowy, tradycyjny } from "./marketing.js";
import { sprzedaz } from "./sprzedaz.js";
import { bank, biuro, kpir, raport } from "./finanse.js";
import { lokale } from "./lokale.js";
import { mapa } from "./mapa.js";
import { klienci } from "./klienci.js";
import { swiezosc } from "./swiezosc.js";

const ZAKLADKI = { dashboard, mapa, karta_wynikow, lokale, klienci, oferta, stanowiska, sprzet, wyposazenie, zatrudnienie, udogodnienia, szkolenia,
  dostawcy, swiezosc, tradycyjny, internetowy, sprzedaz, raport, kpir, bank, biuro, lista_bledow, wyslij, analiza };

// nazwa ikony (zakladki/ikony.js) dla każdej zakładki
export const IKONY = { dashboard: "dashboard", mapa: "mapa", lokale: "lokale", klienci: "klienci", karta_wynikow: "karta", oferta: "oferta", stanowiska: "stanowiska", sprzet: "sprzet",
  wyposazenie: "wyposazenie", zatrudnienie: "zatrudnienie", udogodnienia: "udogodnienia", szkolenia: "szkolenia", dostawcy: "dostawcy", swiezosc: "swiezosc",
  tradycyjny: "tradycyjny", internetowy: "internetowy", sprzedaz: "sprzedaz", raport: "raport", kpir: "kpir", bank: "bank",
  biuro: "biuro", lista_bledow: "bledy", wyslij: "wyslij", analiza: "analiza" };

// od której rundy zakładka jest dostępna (podpowiedź w menu)
export const OD_RUNDY = { karta_wynikow: 3, udogodnienia: 3, wyposazenie: 4, tradycyjny: 5, internetowy: 6, szkolenia: 7,
  sprzet: 2, zatrudnienie: 2, dostawcy: 2, swiezosc: 2, sprzedaz: 2, raport: 2, kpir: 2, analiza: 2 };

export const MENU = [
  { klucz: "mapa", tytul: "Mapa miasta", ikona: "mapa", klasa: "mapa" },
  { klucz: "karta_wynikow", tytul: "Karta wyników", ikona: "karta" },
  { klucz: "lokale", tytul: "Lokale", ikona: "lokale" },
  { klucz: "klienci", tytul: "Klienci i strefy", ikona: "klienci" },
  { klucz: "oferta", tytul: "Oferta", ikona: "oferta" },
  { klucz: "inwestycje", tytul: "Inwestycje", ikona: "inwestycje", pod: ["stanowiska", "sprzet", "wyposazenie"] },
  { klucz: "hr", tytul: "HR", ikona: "hr", pod: ["zatrudnienie", "udogodnienia", "szkolenia"] },
  { klucz: "dostawcy", tytul: "Dostawcy", ikona: "dostawcy" },
  { klucz: "swiezosc", tytul: "Magazyn i świeżość", ikona: "swiezosc" },
  { klucz: "marketing", tytul: "Marketing", ikona: "marketing", pod: ["tradycyjny", "internetowy"] },
  { klucz: "sprzedaz", tytul: "Sprzedaż", ikona: "sprzedaz" },
  { klucz: "finanse", tytul: "Finanse", ikona: "finanse", pod: ["raport", "kpir", "bank", "biuro"] },
  { klucz: "lista_bledow", tytul: "Lista błędów", ikona: "bledy" },
  { klucz: "wyslij", tytul: "Wyślij decyzje", ikona: "wyslij", klasa: "wyslij" },
  { klucz: "analiza", tytul: "Analiza", ikona: "analiza" },
];

export default ZAKLADKI;
