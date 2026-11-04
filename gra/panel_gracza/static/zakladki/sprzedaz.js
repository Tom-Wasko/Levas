// Sprzedaż: wyniki sprzedaży na tle konkurencji (tylko wyniki); ceny i rabaty wpisuje się w kafelkach dań w Menu (oferta.js),
// tu – obsługa ich pól (cena, rabat).
import { esc, licz, nazwaUslugi, tabela, toast, wykres, zl, zl2 } from "./wspolne.js";
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
    return tabela("Zestawienie popytu na dania", ["Danie", ...nag], popyt, { klasy: ["l"] })
      + `<div class="wykres"><canvas id="w-popyt"></canvas></div>`
      + tabela("Sprzedaż vs utracona sprzedaż", ["Danie", "Popyt", "Sprzedaż", "Utracona sprzedaż", "Przyczyna", "Reklamacje", "Przychód"], own,
        { klasy: ["l"], stopka: ["Razem", licz(Object.values(sp).reduce((a, s) => a + s.popyt, 0)), licz(Object.values(sp).reduce((a, s) => a + s.sprzedaz, 0)),
          licz(Object.values(sp).reduce((a, s) => a + s.utracona, 0)), "", licz(Object.values(sp).reduce((a, s) => a + s.reklamacje, 0)),
          zl(Object.values(sp).reduce((a, s) => a + s.przychod, 0))] })
      + `<div class="wykres"><canvas id="w-sprzedaz"></canvas></div>`
      + tabela("Ceny dań z rabatem", ["Danie", ...nag], ceny, { klasy: ["l"] });
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
