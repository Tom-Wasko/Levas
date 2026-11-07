// Sprzedaż: wyniki sprzedaży na tle konkurencji (tylko wyniki); ceny i rabaty wpisuje się w kafelkach dań w Menu (oferta.js),
// tu – obsługa ich pól (cena, rabat).
import { brakWynikow, esc, kafelkiLiczb, licz, nazwaUslugi, podsumowanie, proc, toast, wykres, zl, zl2, zwinTabela } from "./wspolne.js";
import { cenyLokalu, lokalWybrany, zapiszWLokalu } from "./lokal_wybor.js";

const grosze = (x) => Math.round(x * 100) / 100;

// widełki ceny dania (silnik/kuchnia/menu.py: widelki_ceny) – cena rynkowa = preferowana × średni mnożnik cen stref
export function widelki(kat, u) {
  const g = kat.mapa?.menu?.ceny;
  if (!g) return null;
  const s = Object.values(kat.mapa.popyt.strefy), rynkowa = grosze(kat.uslugi[u].cena_preferowana * s.reduce((a, x) => a + x.cena, 0) / s.length);
  return { rynkowa, min: grosze(rynkowa * g.min), max: grosze(rynkowa * g.max) };
}

export const sprzedaz = {
  tytul: "Sprzedaż", ikona: "🛒", odblokowanie: "sprzedaz", tylkoWyniki: true,
  info: "Popyt, sprzedaż i ceny dań na tle konkurencji. Ceny ustala się w kafelkach dań w części Menu.",
  wyniki({ v, kat }) {
    const r = v.rynek, firmy = Object.keys(r.firmy);
    const uslugi = Object.keys(r.popyt);
    const popyt = uslugi.map((u) => [esc(nazwaUslugi(kat, u)), ...firmy.map((f) => r.popyt[u][f] != null ? licz(r.popyt[u][f]) : "")]);
    const ceny = uslugi.map((u) => [esc(nazwaUslugi(kat, u)), ...firmy.map((f) => r.ceny[u]?.[f] != null ? zl2(r.ceny[u][f]) : "")]);
    const sp = v.wyniki?.sprzedaz || {};
    const own = Object.entries(sp).map(([u, s]) => [esc(nazwaUslugi(kat, u)), licz(s.popyt), licz(s.sprzedaz),
      s.utracona ? `<span class="minus">${licz(s.utracona)}</span>` : "0", esc(s.przyczyna), licz(s.reklamacje), zl(s.przychod)]);
    const nag = firmy.map((f) => `${f === v.firma ? "<u>" : ""}${esc(r.firmy[f])}${f === v.firma ? "</u>" : ""}`);
    // UF23: podsumowanie i kafelki na górze, tabele szczegółów zwijane
    const S = Object.values(sp), suma = (k) => S.reduce((a, s) => a + (s[k] || 0), 0);
    const chetni = suma("popyt"), obsl = suma("sprzedaz"), utr = suma("utracona");
    const najg = Object.entries(sp).sort((a, b) => b[1].utracona - a[1].utracona)[0];
    const lead = !S.length ? brakWynikow("Sprzedaż pojawi się w wynikach, gdy lokal zacznie działać.") : podsumowanie([
      `Obsłużyliście <b>${licz(obsl)}</b> z ${licz(chetni)} chętnych (${proc(chetni ? obsl / chetni : 0, 0)}).`,
      utr >= 1 ? `Najwięcej klientów odeszło przy daniu ${esc(nazwaUslugi(kat, najg[0]))} – ${licz(najg[1].utracona)}, przyczyna: ${esc(najg[1].przyczyna || "–")}.`
        : "Nikt nie odszedł bez kebaba – kuchnia, kasa i składniki dały radę."], utr / (chetni || 1) >= 0.1 ? "uwaga" : "ok");
    const kafle = S.length ? kafelkiLiczb([
      { etykieta: "Chętni", wartosc: licz(chetni) }, { etykieta: "Obsłużeni", wartosc: licz(obsl), opis: proc(chetni ? obsl / chetni : 0, 0) + " chętnych" },
      { etykieta: "Odeszli bez kebaba", wartosc: licz(utr), ton: utr >= 1 ? "minus" : "plus" },
      { etykieta: "Przychód ze sprzedaży", wartosc: zl(suma("przychod")) }, { etykieta: "Reklamacje", wartosc: licz(suma("reklamacje")), ton: suma("reklamacje") ? "minus" : "" }]) : "";
    return lead + kafle
      + `<div class="wykres"><canvas id="w-sprzedaz"></canvas></div>`
      + zwinTabela("Sprzedaż vs utracona sprzedaż", ["Danie", "Popyt", "Sprzedaż", "Utracona sprzedaż", "Przyczyna", "Reklamacje", "Przychód"], own,
        { klasy: ["l"], stopka: ["Razem", licz(Object.values(sp).reduce((a, s) => a + s.popyt, 0)), licz(Object.values(sp).reduce((a, s) => a + s.sprzedaz, 0)),
          licz(Object.values(sp).reduce((a, s) => a + s.utracona, 0)), "", licz(Object.values(sp).reduce((a, s) => a + s.reklamacje, 0)),
          zl(Object.values(sp).reduce((a, s) => a + s.przychod, 0))], otwarte: true })
      + `<div class="wykres"><canvas id="w-popyt"></canvas></div>`
      + zwinTabela("Zestawienie popytu na dania", ["Danie", ...nag], popyt, { klasy: ["l"] })
      + zwinTabela("Ceny dań z rabatem", ["Danie", ...nag], ceny, { klasy: ["l"] });
  },
  po({ v, kat }, tryb) {
    if (tryb !== "wyniki") return;
    const r = v.rynek, firmy = Object.keys(r.firmy), uslugi = Object.keys(r.popyt);
    wykres("w-popyt", "bar", uslugi.map((u) => nazwaUslugi(kat, u)), firmy.map((f) => ({ label: r.firmy[f], data: uslugi.map((u) => r.popyt[u][f] ?? 0) })));
    const sp = v.wyniki?.sprzedaz || {}, us = Object.keys(sp);
    wykres("w-sprzedaz", "bar", us.map((u) => nazwaUslugi(kat, u)), [{ label: "Sprzedaż", data: us.map((u) => sp[u].sprzedaz) },
      { label: "Utracona sprzedaż", data: us.map((u) => sp[u].utracona), kolor: "--wykres-utracona" }], { scales: { x: { stacked: true }, y: { stacked: true } } });
  },
  zmiany: {
    cena: (el, c) => {
      const u = el.dataset.u, wd = widelki(c.kat, u);
      let cena = Math.max(1, +el.value || 1);
      if (wd && (cena < wd.min || cena > wd.max)) {
        cena = Math.min(wd.max, Math.max(wd.min, cena));
        toast(`${nazwaUslugi(c.kat, u)}: cena musi być między ${zl2(wd.min)} a ${zl2(wd.max)} – ustawiono ${zl2(cena)}.`);
      }
      const ceny = cenyLokalu(c.v, lokalWybrany(c.v));
      return c.zmien((d) => { zapiszWLokalu(d, c.v, "sprzedaz", { ...ceny, [u]: { rabat: 0, ...ceny[u], cena } }); });
    },
    rabat: (el, c) => {
      const u = el.dataset.u, ceny = cenyLokalu(c.v, lokalWybrany(c.v));
      return c.zmien((d) => { zapiszWLokalu(d, c.v, "sprzedaz", { ...ceny, [u]: { cena: c.kat.uslugi[u].cena_preferowana, ...ceny[u], rabat: Math.max(0, +el.value || 0) } }); });
    },
  },
};
