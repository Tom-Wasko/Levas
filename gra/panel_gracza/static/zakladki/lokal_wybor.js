// Wybrany lokal (Z3, przebudowa 2.11.2026): kafelki lokali na górze zakładki Lokale – wybór zostaje przy zmianie
// podzakładek. Przy kilku lokalach menu, ceny, magazyn, stanowiska, wyposażenie i udogodnienia są osobne w każdym
// lokalu (silnik/nieruchomosci/per_lokal.py), więc decyzje idą do "w_lokalu": {lokal: {klucz: wartość}}; przy jednym
// lokalu – jak dawniej, decyzja główna (d.oferta, d.sprzedaz, …).
import { esc, licz } from "./wspolne.js";

let wybrany = null;   // id lokalu wybranego kafelkiem (null – pierwszy)

export const mojeLokale = (v) => v.stan?.lokale || [];
export const wieleLokali = (v) => mojeLokale(v).length > 1;
export function lokalWybrany(v) {
  const l = mojeLokale(v);
  return l.find((x) => x.id === wybrany) || l[0] || null;
}
export const idWybranego = (v) => (wieleLokali(v) ? lokalWybrany(v).id : null);
export const opisLokalu = (v, id) => (v.lokale?.moje || []).find((l) => l.id === id) || null;
export const nazwaLokalu = (v, id) => opisLokalu(v, id)?.nazwa || id;
// lokal domyślny zamówień bez pola "lokal" (jak per_lokal.glowny): pierwszy działający, inaczej pierwszy
export function glownyLokal(v) {
  const l = mojeLokale(v);
  return (l.find((x) => x.dziala_od <= v.runda) || l[0])?.id ?? null;
}

// menu i ceny lokalu (None w starym zapisie – jak w całej firmie)
export const menuLokalu = (v, lok) => (lok && lok.menu) || v.stan.oferta;
export const cenyLokalu = (v, lok) => (lok && lok.ceny) || v.stan.ceny;

// wyposażenie / udogodnienia lokalu w stanie `stan` (v.stan albo v.stan_przed) – jak per_lokal.lista
export function listaLokalu(stan, rodzaj, id) {
  const l = stan.lokale || [], lok = l.find((x) => x.id === id);
  if (!lok) return id && l.length ? [] : stan[rodzaj] || [];
  if (lok[rodzaj]) return lok[rodzaj];
  return !l.some((x) => x[rodzaj]) && lok === l[0] ? stan[rodzaj] || [] : [];
}

// stanowiska wybranego lokalu (przy jednym lokalu – wszystkie)
export const stanowiskaLokalu = (v, lista) => {
  const id = idWybranego(v);
  return id ? lista.filter((s) => s.lokal === id) : lista;
};

// partie z lokalem (bez lokalu – pierwszy lokal, jak per_lokal.lokal_partii)
export const lokalPartii = (v, p) => (p.lokal && mojeLokale(v).some((l) => l.id === p.lokal) ? p.lokal : mojeLokale(v)[0]?.id);

// Zapis decyzji wybranego lokalu. Przy kilku lokalach decyzja główna oferty / cen (dla wszystkich lokali) zamienia się
// najpierw na decyzje każdego lokalu wg obecnego stanu – inaczej silnik dzieliłby prognozę po równo między lokale.
const OBECNA = { oferta: menuLokalu, sprzedaz: cenyLokalu };
export function zapiszWLokalu(d, v, klucz, wartosc) {
  if (!wieleLokali(v)) { d[klucz] = wartosc; return; }
  const id = lokalWybrany(v).id;
  d.w_lokalu = d.w_lokalu || {};
  if (OBECNA[klucz] && klucz in d) {
    for (const l of mojeLokale(v)) {
      if (l.id !== id && !(d.w_lokalu[l.id] && klucz in d.w_lokalu[l.id])) d.w_lokalu[l.id] = { ...(d.w_lokalu[l.id] || {}), [klucz]: OBECNA[klucz](v, l) };
    }
    delete d[klucz];
  }
  d.w_lokalu[id] = { ...(d.w_lokalu[id] || {}), [klucz]: wartosc };
}
// decyzja wybranego lokalu (lista zakupów, pakiet stanowisk) – przy jednym lokalu decyzja główna
export const decyzjaLokalu = (d, v, klucz) => (wieleLokali(v) ? (d.w_lokalu?.[lokalWybrany(v).id] || {})[klucz] : d[klucz]);

// kafelki lokali (gra z lokalami); aktywny – wybrany
export function kafelkiLokali(v) {
  const l = mojeLokale(v);
  if (!l.length) return "";
  const akt = lokalWybrany(v).id;
  return `<div class="kafelki-lokali" role="tablist" aria-label="Twoje lokale">${l.map((x) => {
    const o = opisLokalu(v, x.id) || {}, menu = Object.keys(menuLokalu(v, x));
    const status = x.dziala_od <= v.runda ? "działa" : `rusza w rundzie ${x.dziala_od}`;
    return `<button class="kafel-lokalu ${x.id === akt ? "aktywny" : ""}" role="tab" aria-selected="${x.id === akt}" data-akcja="wybierz-lokal" data-id="${esc(x.id)}">
      <b>${esc(o.nazwa || x.id)}</b><span>${esc(o.adres || "")}</span>
      <span class="podpowiedz">${status} · ${licz(menu.length)} ${menu.length === 1 ? "danie" : "dań"} w menu</span></button>`;
  }).join("")}</div>${l.length > 1 ? `<p class="podpowiedz">Menu, ceny, magazyn, stanowiska, sprzęt, wyposażenie i udogodnienia ustawiasz
    osobno dla każdego lokalu – kliknij kafelek, żeby przełączyć lokal. Pracownik pracuje na stanowisku jednego lokalu; szkolenia, czas właściciela i dostawcy są wspólni dla firmy.</p>` : ""}`;
}

// UF15: krótki wybór lokalu w zakładkach Firmy, które mimo to działają na jednym lokalu (Udogodnienia) – tylko przy kilku lokalach
export function wyborLokaluKrotki(v) {
  if (!wieleLokali(v)) return "";
  const akt = lokalWybrany(v).id;
  return `<div class="wybor-lokalu-krotki">Lokal: ${mojeLokale(v).map((x) => `<button class="btn maly ${x.id === akt ? "pom" : "jasny"}"
    data-akcja="wybierz-lokal" data-id="${esc(x.id)}">${esc(opisLokalu(v, x.id)?.nazwa || x.id)}</button>`).join(" ")}</div>`;
}

export const akcjeWyboru = {
  "wybierz-lokal": (el, c) => { wybrany = el.dataset.id; c.rysuj(); },
};
