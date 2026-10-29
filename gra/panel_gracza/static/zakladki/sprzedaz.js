// Sprzedaż: cennik i rabaty, wyniki sprzedaży na tle konkurencji.
import { esc, licz, nazwaFirmy, nazwaUslugi, proc, tabela, toast, wykres, zl, zl2 } from "./wspolne.js";

const grosze = (x) => Math.round(x * 100) / 100;

// widełki ceny dania (silnik/kuchnia/menu.py: widelki_ceny) – cena rynkowa = preferowana × średni mnożnik cen stref
function widelki(kat, u) {
  const g = kat.mapa?.menu?.ceny;
  if (!g) return null;
  const s = Object.values(kat.mapa.popyt.strefy), rynkowa = grosze(kat.uslugi[u].cena_preferowana * s.reduce((a, x) => a + x.cena, 0) / s.length);
  return { rynkowa, min: grosze(rynkowa * g.min), max: grosze(rynkowa * g.max) };
}

export const sprzedaz = {
  tytul: "Sprzedaż", ikona: "🛒", odblokowanie: "sprzedaz",
  info: "Ustal ceny dań gotowych do sprzedaży. Danie jest gotowe, gdy masz sprzęt, pracowników, obsadzoną kasę i składniki. Klient płaci cenę pomniejszoną o rabat.",
  decyzje({ v, kat, edycja }) {
    const gotowe = v.stan.gotowe_uslugi, ceny = v.stan.ceny;
    if (!Object.keys(v.stan.oferta).length) return `<div class="komunikat">Najpierw wybierz dania w zakładce Oferta.</div>`;
    const rynek = v.rynek?.ceny || {};
    const w = Object.keys(v.stan.oferta).map((u) => {
      const k = kat.uslugi[u], c = ceny[u], braki = gotowe[u] || [];
      const inni = Object.entries(rynek[u] || {}).filter(([f]) => f !== v.firma).map(([, x]) => x);
      const sr = inni.length ? inni.reduce((a, b) => a + b, 0) / inni.length : null;
      const wl = !!c, wd = widelki(kat, u);
      return [`${esc(k.nazwa)}${braki.filter((b) => !b.includes("włączona")).length ? `<br><span class="podpowiedz" style="color:var(--czerwony)">${braki.filter((b) => !b.includes("włączona")).map(esc).join("; ")}</span>` : ""}`,
        `${zl(k.cena_preferowana)}${wd ? `<br><span class="podpowiedz">dozwolone ${zl2(wd.min)}–${zl2(wd.max)}</span>` : ""}`, sr ? zl2(sr) : "–",
        `<button class="btn ${wl ? "zielony" : "czarny"} maly" data-akcja="wlacz-sprzedaz" data-u="${u}" ${edycja ? "" : "disabled"}>${wl ? "✓ Wybrano" : "Wybierz"}</button>`,
        wl ? `<input type="number" class="krotkie" min="${wd ? wd.min : 1}" ${wd ? `max="${wd.max}"` : ""} step="0.5" value="${c.cena}" data-zmiana="cena" data-u="${u}" ${edycja ? "" : "disabled"}>` : "",
        wl ? `<input type="number" class="krotkie" min="0" step="0.5" value="${c.rabat}" data-zmiana="rabat" data-u="${u}" ${edycja ? "" : "disabled"}>` : "",
        wl ? `${zl2(c.cena - c.rabat)} <span class="podpowiedz">(${proc((c.cena - c.rabat) / k.cena_preferowana, 0)} pref.)</span>` : ""];
    });
    const g = kat.mapa?.menu?.ceny;
    return tabela(null, ["Danie", "Preferowana cena", "Średnia cena konkurencji (poprz. runda)", "Sprzedaż", "Cena", "Rabat", "Cena dla klienta"], w, { klasy: ["l"] })
      + `<p class="podpowiedz">Cena wpływa na popyt i na zadowolenie klientów. Niższa cena od konkurencji przyciąga klientów, a im więcej lokali ma danie w menu, tym mniej klientów przypada na każdą.${g ? ` Cena musi mieścić się w widełkach: od ${proc(g.min, 0)} do ${proc(g.max, 0)} ceny rynkowej (cena dla klienta po rabacie – nie niżej niż dolna granica).` : ""}</p>`;
  },
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
  akcje: {
    "wlacz-sprzedaz": (el, c) => c.zmien((d) => {
      const u = el.dataset.u, ceny = { ...c.v.stan.ceny };
      if (ceny[u]) delete ceny[u];
      else ceny[u] = { cena: c.kat.uslugi[u].cena_preferowana, rabat: 0 };
      d.sprzedaz = ceny;
    }),
  },
  zmiany: {
    cena: (el, c) => {
      const u = el.dataset.u, wd = widelki(c.kat, u);
      let cena = Math.max(1, +el.value || 1);
      if (wd && (cena < wd.min || cena > wd.max)) {
        cena = Math.min(wd.max, Math.max(wd.min, cena));
        toast(`${nazwaUslugi(c.kat, u)}: cena musi być między ${zl2(wd.min)} a ${zl2(wd.max)} – ustawiono ${zl2(cena)}.`);
      }
      return c.zmien((d) => { d.sprzedaz = { ...c.v.stan.ceny, [u]: { ...c.v.stan.ceny[u], cena } }; });
    },
    rabat: (el, c) => c.zmien((d) => { d.sprzedaz = { ...c.v.stan.ceny, [el.dataset.u]: { ...c.v.stan.ceny[el.dataset.u], rabat: Math.max(0, +el.value || 0) } }; }),
  },
};
