// Dostawcy: zakup składników, magazyn, zwroty. W grze z lokalami zamówienie ma dzień dostawy (świeżość – zakładka
// „Magazyn i świeżość”, silnik/swiezosc.py).
import { esc, OKRES, gw, licz, nazwaFirmy, okno, tabela, toast, ulamek, wykres, zl, zl2 } from "./wspolne.js";

const stan = (v, z, q) => v.stan_przed.magazyn[`${z}|${q}`] || 0;
const zamowienia = (v, d, z, q) => (v.decyzje.zamowienia || []).filter((x) => x.dostawca === d && x.zasob === z && +x.jakosc === q);
const zamowione = (v, d, z, q, dz) => zamowienia(v, d, z, q).filter((x) => dz === undefined || (+x.dzien || 0) === dz).reduce((s, x) => s + x.ilosc, 0);
const dniDostaw = (v) => (v.lokale && v.swiezosc?.dni) || null;

// Podział zamówienia na dostawy (jak planowanie._dostawy w silniku): co `krok` dni – krótki termin albo chłodnia /
// zamrażarka; każda dostawa na dni do następnej, zapas z magazynu zmniejsza pierwszą.
function dostawy(kat, z, potrzeba, stan, udzialy) {
  const zas = kat.zasoby[z], n = udzialy.length;
  const termin = zas.termin_dni || n;
  let krok = Math.min(termin, n);
  if ((zas.przechowywanie || "suche") !== "suche") krok = Math.min(krok, 3);
  const suma = udzialy.reduce((s, x) => s + x, 0) || 1, wynik = [];
  let zapas = stan;
  for (let j = 0; j < n; j += krok) {
    const ile = potrzeba * udzialy.slice(j, j + krok).reduce((s, x) => s + x, 0) / suma - zapas;
    const k = Math.ceil(Math.max(0, ile) - 1e-9);
    zapas = krok < termin ? Math.max(0, k - ile) : 0;
    if (k > 0) wynik.push([j, k]);
  }
  return wynik;
}

function zapotrzebowanie(v, kat) {
  const wynik = {};
  for (const [u, p] of Object.entries(v.stan.oferta)) {
    for (const [z, ile] of Object.entries(kat.uslugi[u].zasoby)) wynik[z] = (wynik[z] || 0) + (p || 0) * ile / kat.zasoby[z].opakowanie;
  }
  return wynik;
}

function najtansze(ceny) {
  const w = {};
  for (const [d, zas] of Object.entries(ceny)) for (const [z, jak] of Object.entries(zas)) for (const [q, c] of Object.entries(jak)) {
    if (!w[`${z}|${q}`] || c < w[`${z}|${q}`].c) w[`${z}|${q}`] = { c, d };
  }
  return w;
}

export const dostawcy = {
  tytul: "Dostawcy", ikona: "⛟", odblokowanie: "dostawcy",
  info: "Kup składniki potrzebne do wybranych dań. Składniki możesz kupować u jednego lub kilku dostawców. Niezużyte zostają w magazynie.",
  decyzje({ v, kat, edycja }) {
    const ceny = v.ceny_dostawcow;
    const koszt = (v.decyzje.zamowienia || []).reduce((s, z) => s + (ceny[z.dostawca]?.[z.zasob]?.[z.jakosc] || 0) * z.ilosc, 0);
    const pot = zapotrzebowanie(v, kat), tanie = najtansze(ceny);
    const wiersze = Object.keys(kat.zasoby).filter((z) => pot[z] || [1, 2, 3].some((q) => stan(v, z, q))).map((z) => {
      const magazyn = [1, 2, 3].reduce((s, q) => s + stan(v, z, q), 0);
      const zam = (v.decyzje.zamowienia || []).filter((x) => x.zasob === z).reduce((s, x) => s + x.ilosc, 0);
      const brak = Math.max(0, (pot[z] || 0) - magazyn - zam);
      return [esc(z), `${kat.zasoby[z].typ_opakowania} (${licz(kat.zasoby[z].opakowanie)} ${kat.zasoby[z].jednostka})`, ulamek(pot[z] || 0),
        ulamek(magazyn), licz(zam), brak > 0 ? `<span class="minus">${ulamek(brak)}</span>` : '<span class="plus">0</span>',
        [1, 2, 3].map((q) => tanie[`${z}|${q}`] ? `${gw(q)} ${zl2(tanie[`${z}|${q}`].c)} <span class="podpowiedz">${esc(tanie[`${z}|${q}`].d)}</span>` : "").join("<br>")];
    });
    let html = `<div class="pasek ciemny"><span>Koszt zakupu: <span class="kwota">${zl2(koszt)}</span></span>
      <span style="display:flex;gap:8px;align-items:center">Zamów brakujące u najtańszych w jakości
      <select id="auto-jakosc" style="width:auto"><option value="3">★★★</option><option value="2">★★</option><option value="1">★</option></select>
      <select id="auto-zapas" style="width:auto"><option value="1">bez zapasu</option><option value="1.05" selected>+5% zapasu</option><option value="1.1">+10% zapasu</option></select>
      <button class="btn pom maly" data-akcja="auto-zamow" ${edycja ? "" : "disabled"}>Zamów</button></span></div>`;
    html += tabela("Zapotrzebowanie na prognozowanych klientów (opakowania)", ["Zasób", "Opakowanie", "Potrzeba wg prognoz", "W magazynie",
      "Zamówione teraz", "Brakuje", "Najtańsze oferty"], wiersze, { klasy: ["l", "l"] });
    html += `<div class="pasek">Dostawcy</div><div class="siatka trojka">`;
    for (const d of Object.keys(ceny)) {
      const wartosc = (v.decyzje.zamowienia || []).filter((x) => x.dostawca === d).reduce((s, x) => s + (ceny[d]?.[x.zasob]?.[x.jakosc] || 0) * x.ilosc, 0);
      const zwrot = !!(v.decyzje.zwrot_nadmiaru || {})[d];
      html += `<div class="kafel"><div class="kg">${esc(d)}</div><div class="kt">
        <div class="wiersz"><span>Koszt zwrotu</span><span>${Math.round(kat.parametry.koszt_zwrotu * 100)}%</span></div>
        <div class="wiersz"><span>Koszt magazynowania</span><span>${zl2(kat.parametry.koszt_magazynowania)}</span></div>
        <label class="pole" style="margin-top:8px">Zwrot składników nadmiarowych
          <select data-zmiana="zwrot" data-d="${esc(d)}" ${edycja ? "" : "disabled"}><option value="0" ${zwrot ? "" : "selected"}>Nie – zostają w magazynie</option>
          <option value="1" ${zwrot ? "selected" : ""}>Tak – zwrot niezużytych (koszt 10%)</option></select></label></div>
        <div class="kd"><button class="btn czarny" data-akcja="baza" data-d="${esc(d)}">Baza składników</button>
        <div class="wiersz"><span>Zamówienie</span><span>${zl2(wartosc)}</span></div></div></div>`;
    }
    return html + `</div>`;
  },
  wyniki({ v }) {
    const straty = (v.wyniki?.zasoby || []).some((x) => "straty" in x);
    const z = (v.wyniki?.zasoby || []).map((x) => [esc(x.zasob), gw(x.jakosc), ulamek(x.poczatek), ulamek(x.zamowione), ulamek(x.wykorzystane),
      ...(straty ? [x.straty ? `<span class="minus">${ulamek(x.straty)}</span>` : "0"] : []), ulamek(x.zwroty), ulamek(x.koniec), zl2(x.wartosc)]);
    const suma = (v.wyniki?.zasoby || []).reduce((s, x) => s + x.wartosc, 0);
    const firmy = Object.keys(v.rynek?.jakosc_zasobow || {});
    const jak = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...[1, 2, 3].map((q) => ulamek(v.rynek.jakosc_zasobow[f][q]))]);
    return tabela("Składniki", ["Składnik", "Jakość", `Magazyn na początek ${OKRES.dopelniacz}`, "Zamówione", "Wykorzystane", ...(straty ? ["Straty"] : []), "Zwroty",
      `Magazyn na koniec ${OKRES.dopelniacz}`, "Wartość"], z, { klasy: ["l"], stopka: ["Suma", "", "", "", "", ...(straty ? [""] : []), "", "", zl2(suma)] })
      + tabela("Jakość składników (zamówione opakowania)", ["Firma", "Niska ★", "Średnia ★★", "Wysoka ★★★"], jak, { klasy: ["l"] })
      + `<div class="wykres"><canvas id="w-jakosc"></canvas></div>`;
  },
  po({ v }, tryb) {
    if (tryb !== "wyniki") return;
    const f = Object.keys(v.rynek?.jakosc_zasobow || {});
    wykres("w-jakosc", "bar", ["Niska", "Średnia", "Wysoka"], f.map((x) => ({ label: nazwaFirmy(v, x), data: [1, 2, 3].map((q) => v.rynek.jakosc_zasobow[x][q]) })));
  },
  akcje: {
    baza: (el, c) => oknoBazy(c, el.dataset.d),
    "auto-zamow": async (el, c) => {
      const q = +document.getElementById("auto-jakosc").value, zapas = +document.getElementById("auto-zapas").value;
      const pot = zapotrzebowanie(c.v, c.kat), tanie = najtansze(c.v.ceny_dostawcow);
      const nowe = [];
      for (const [z, p] of Object.entries(pot)) {
        const mag = [1, 2, 3].reduce((s, j) => s + stan(c.v, z, j), 0);
        let jq = q;
        while (!tanie[`${z}|${jq}`] && jq > 1) jq--;
        if (!tanie[`${z}|${jq}`]) continue;
        const udzialy = dniDostaw(c.v) && c.v.popyt?.prognoza?.dni?.length ? c.v.popyt.prognoza.dni : null;
        if (udzialy) {
          for (const [dzien, ilosc] of dostawy(c.kat, z, p * zapas, mag, udzialy)) nowe.push({ dostawca: tanie[`${z}|${jq}`].d, zasob: z, jakosc: jq, ilosc, dzien });
          continue;
        }
        const brak = Math.ceil(Math.max(0, p * zapas - mag) - 1e-9);
        if (brak > 0) nowe.push({ dostawca: tanie[`${z}|${jq}`].d, zasob: z, jakosc: jq, ilosc: brak });
      }
      if (!nowe.length) return toast("Zapas w magazynie wystarcza na prognozowanych klientów.");
      await c.zmien((d) => { d.zamowienia = nowe; });
      toast(dniDostaw(c.v) ? "Zamówienia ustawione – dostawy rozłożone na dni wg terminów przydatności (poprzednie zastąpione)."
        : "Zamówienia ustawione (poprzednie zamówienia zastąpione).");
    },
  },
  zmiany: {
    zwrot: (el, c) => c.zmien((d) => { d.zwrot_nadmiaru = { ...(d.zwrot_nadmiaru || {}), [el.dataset.d]: el.value === "1" }; }),
    ilosc: async (el, c) => {
      const { d: dost, z, q, dz } = el.dataset, ilosc = Math.max(0, +el.value || 0);
      const tenDzien = (x) => dz === undefined || (+x.dzien || 0) === +dz;
      await c.zmien((d) => {
        d.zamowienia = (d.zamowienia || []).filter((x) => !(x.dostawca === dost && x.zasob === z && +x.jakosc === +q && tenDzien(x)));
        if (ilosc > 0) d.zamowienia.push({ dostawca: dost, zasob: z, jakosc: +q, ilosc, ...(dz === undefined ? {} : { dzien: +dz }) });
      });
      oknoBazy(c, dost);
    },
  },
};

function oknoBazy({ v, kat, edycja }, dost) {
  const ceny = v.ceny_dostawcow[dost] || {}, dni = dniDostaw(v);
  const pole = (z, q, ile, dz) => `<input type="number" class="krotkie" min="0" step="1" value="${ile}" data-zmiana="ilosc" data-d="${esc(dost)}" data-z="${esc(z)}" data-q="${q}"
    ${dz === undefined ? "" : `data-dz="${dz}"`} ${edycja ? "" : "disabled"}>`;
  const w = [];
  for (const [z, jak] of Object.entries(ceny)) for (const [q, c] of Object.entries(jak)) {
    const zas = kat.zasoby[z];
    const miejsce = zas.przechowywanie && zas.przechowywanie !== "suche" ? ` · ${zas.przechowywanie === "chlodnia" ? "chłodnia" : "zamrażarka"} ${licz(zas.miejsce_l)} l` : "";
    const termin = zas.termin_dni ? `<br><span class="podpowiedz">termin ${zas.termin_dni} dni${miejsce}</span>` : "";
    w.push([`${esc(z)}<br><span class="podpowiedz">${zas.typ_opakowania} (${licz(zas.opakowanie)} ${zas.jednostka})</span>${dni ? termin : ""}`,
      gw(+q), ulamek(stan(v, z, +q)), zl2(c),
      ...(dni ? dni.map((_, i) => pole(z, q, zamowione(v, dost, z, +q, i), i)) : [pole(z, q, zamowione(v, dost, z, +q))]),
      zl2(zamowione(v, dost, z, +q) * c)]);
  }
  const kolumny = dni ? dni.map((d) => `${d.dzien}<div class="podpowiedz">${+d.data.slice(8)}.${d.data.slice(5, 7)}</div>`) : ["Zamówienie (opakowania)"];
  okno(`Dostawca „${esc(dost)}”`, tabela(null, ["Składnik", "Jakość", "Na magazynie", "Cena", ...kolumny, "Wartość"], w, { klasy: ["l"] })
    + `<p class="podpowiedz">Ceny w tym ${OKRES.miejscownik}. Ilości wpisujesz w opakowaniach (np. napój: opakowanie 24 szt.).
      ${dni ? "Kolumny dni – dostawa rano tego dnia; termin przydatności liczy się od dnia dostawy (zakładka Magazyn i świeżość)." : ""}</p>`,
    { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">Zapisz</button>` });
}
