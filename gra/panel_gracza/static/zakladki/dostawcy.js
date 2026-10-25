// Dostawcy: zakup składników, magazyn, zwroty.
import { esc, gw, licz, nazwaFirmy, okno, tabela, toast, ulamek, wykres, zl, zl2 } from "./wspolne.js";

const stan = (v, z, q) => v.stan_przed.magazyn[`${z}|${q}`] || 0;
const zamowienie = (v, d, z, q) => (v.decyzje.zamowienia || []).find((x) => x.dostawca === d && x.zasob === z && +x.jakosc === q);

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
    const z = (v.wyniki?.zasoby || []).map((x) => [esc(x.zasob), gw(x.jakosc), ulamek(x.poczatek), ulamek(x.zamowione), ulamek(x.wykorzystane),
      ulamek(x.zwroty), ulamek(x.koniec), zl2(x.wartosc)]);
    const suma = (v.wyniki?.zasoby || []).reduce((s, x) => s + x.wartosc, 0);
    const firmy = Object.keys(v.rynek?.jakosc_zasobow || {});
    const jak = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...[1, 2, 3].map((q) => ulamek(v.rynek.jakosc_zasobow[f][q]))]);
    return tabela("Składniki", ["Składnik", "Jakość", "Magazyn na początek miesiąca", "Zamówione", "Wykorzystane", "Zwroty",
      "Magazyn na koniec miesiąca", "Wartość"], z, { klasy: ["l"], stopka: ["Suma", "", "", "", "", "", "", zl2(suma)] })
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
        const brak = Math.ceil(Math.max(0, p * zapas - mag) - 1e-9);
        let jq = q;
        while (!tanie[`${z}|${jq}`] && jq > 1) jq--;
        if (brak > 0 && tanie[`${z}|${jq}`]) nowe.push({ dostawca: tanie[`${z}|${jq}`].d, zasob: z, jakosc: jq, ilosc: brak });
      }
      if (!nowe.length) return toast("Zapas w magazynie wystarcza na prognozowanych klientów.");
      await c.zmien((d) => { d.zamowienia = nowe; });
      toast("Zamówienia ustawione (poprzednie zamówienia zastąpione).");
    },
  },
  zmiany: {
    zwrot: (el, c) => c.zmien((d) => { d.zwrot_nadmiaru = { ...(d.zwrot_nadmiaru || {}), [el.dataset.d]: el.value === "1" }; }),
    ilosc: async (el, c) => {
      const { d: dost, z, q } = el.dataset, ilosc = Math.max(0, +el.value || 0);
      await c.zmien((d) => {
        d.zamowienia = (d.zamowienia || []).filter((x) => !(x.dostawca === dost && x.zasob === z && +x.jakosc === +q));
        if (ilosc > 0) d.zamowienia.push({ dostawca: dost, zasob: z, jakosc: +q, ilosc });
      });
      oknoBazy(c, dost);
    },
  },
};

function oknoBazy({ v, kat, edycja }, dost) {
  const ceny = v.ceny_dostawcow[dost] || {};
  const w = [];
  for (const [z, jak] of Object.entries(ceny)) for (const [q, c] of Object.entries(jak)) {
    const zam = zamowienie(v, dost, z, +q);
    w.push([`${esc(z)}<br><span class="podpowiedz">${kat.zasoby[z].typ_opakowania} (${licz(kat.zasoby[z].opakowanie)} ${kat.zasoby[z].jednostka})</span>`,
      gw(+q), ulamek(stan(v, z, +q)), zl2(c),
      `<input type="number" class="krotkie" min="0" step="1" value="${zam ? zam.ilosc : 0}" data-zmiana="ilosc" data-d="${esc(dost)}" data-z="${esc(z)}" data-q="${q}" ${edycja ? "" : "disabled"}>`,
      zl2((zam ? zam.ilosc : 0) * c)]);
  }
  okno(`Dostawca „${esc(dost)}”`, tabela(null, ["Składnik", "Jakość", "Na magazynie", "Cena", "Zamówienie (opakowania)", "Wartość"], w, { klasy: ["l"] })
    + `<p class="podpowiedz">Ceny w tym miesiącu. Ilości wpisujesz w opakowaniach (np. napój: opakowanie 24 szt.).</p>`,
    { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">Zapisz</button>` });
}
