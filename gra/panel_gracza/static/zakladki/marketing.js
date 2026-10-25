// Marketing tradycyjny i internetowy.
import { esc, licz, nazwaFirmy, nazwaUslugi, proc, tabela, wykres, zl } from "./wspolne.js";

const KATEGORIE = { billboard_ulotki: "Billboard / ulotki", prasa: "Prasa", radio: "Radio", telewizja: "Telewizja" };

export function kosztEmisji(m, n) {
  let z = 0;
  for (const [od, p] of m.znizki) if (n >= od) z = p;
  return Math.round(n * m.cena * (1 - z / 100) * 100) / 100;
}

function efekty(v, kat) {
  const sp = v.wyniki?.sprzedaz || {};
  return Object.entries(sp).map(([u, s]) => [esc(nazwaUslugi(kat, u)), licz(s.popyt)]);
}

export const tradycyjny = {
  tytul: "Tradycyjny", tytulPelny: "Marketing - tradycyjny", ikona: "📣", odblokowanie: "marketing_tradycyjny",
  info: "Podejmij decyzję o promowaniu Twojej firmy w mediach tradycyjnych. Reklama zwiększa popyt na wszystkie dania w tym miesiącu.",
  decyzje({ v, kat, edycja }) {
    const em = v.decyzje.reklama_tradycyjna || {};
    const media = kat.oferty.media_tradycyjne.pozycje;
    let html = "";
    for (const [k, nazwa] of Object.entries(KATEGORIE)) {
      const poz = media.filter((m) => m.kategoria === k);
      const od = Math.min(...poz.map((m) => m.od_rundy || 1));
      if (od > v.runda) {
        html += `<div class="pasek ciemny niedostepny" style="margin-top:22px"><span>${nazwa}</span><span>Dostępne od rundy ${od}</span></div>`;
        continue;
      }
      const suma = poz.reduce((s, m) => s + kosztEmisji(m, +em[m.nazwa] || 0), 0);
      html += `<div class="pasek ciemny" style="margin-top:22px"><span>${nazwa}</span><span>Koszty całkowite: <span class="kwota">${zl(suma)}</span></span></div>
        <div class="siatka trojka" style="margin-top:14px">${poz.map((m) => `<div class="kafel ${em[m.nazwa] ? "wybrany" : ""}"><div class="kg">${esc(m.nazwa)}
          <span class="pigulka inf">zasięg ${Math.round(m.zasieg * 100)}%</span></div><div class="kt">
          <div class="wiersz"><span>Cena zakupu (emisja)</span><span>${zl(m.cena)}</span></div>
          ${m.znizki.map(([od, p], i) => `<div class="wiersz"><span>${od}${m.znizki[i + 1] ? ` – ${m.znizki[i + 1][0] - 1}` : " – ∞"} emisji</span><span>${p}%</span></div>`).join("")}
          <label class="pole" style="margin-top:8px">Liczba emisji<input type="number" min="0" step="1" value="${em[m.nazwa] || 0}" data-zmiana="emisje" data-m="${esc(m.nazwa)}" ${edycja ? "" : "disabled"}></label>
          <div class="wiersz"><span>Koszt</span><span>${zl(kosztEmisji(m, +em[m.nazwa] || 0))}</span></div></div></div>`).join("")}</div>`;
    }
    return html + `<p class="podpowiedz">Telewizja ma największy zasięg i efekt jednej emisji, ale jest najdroższa. Zniżka zależy od liczby emisji w danym medium.</p>`;
  },
  wyniki({ v, kat }) {
    const r = v.rynek;
    const w = Object.entries(r.reklama_tradycyjna || {}).map(([f, k]) => [esc(nazwaFirmy(v, f)), zl(k)]);
    const ef = v.wyniki?.reklama?.tradycyjna;
    return tabela("Wydatki na reklamę tradycyjną", ["Nazwa firmy", "Wydatki na reklamę"], w, { klasy: ["l"] })
      + tabela(`Efektywność reklamy – wzrost popytu w wyniku wydatków na reklamę: ${proc(ef ?? 0, 2)}`, ["Danie", "Popyt"], efekty(v, kat), { klasy: ["l"] })
      + `<div class="wykres"><canvas id="w-rekl"></canvas></div>`;
  },
  po({ v }, tryb) {
    if (tryb !== "wyniki") return;
    const f = Object.keys(v.rynek.reklama_tradycyjna || {});
    wykres("w-rekl", "bar", f.map((x) => nazwaFirmy(v, x)), [{ label: "Wydatki na reklamę tradycyjną", data: f.map((x) => v.rynek.reklama_tradycyjna[x]) }]);
  },
  zmiany: { emisje: (el, c) => c.zmien((d) => { d.reklama_tradycyjna = { ...(d.reklama_tradycyjna || {}), [el.dataset.m]: Math.max(0, Math.round(+el.value || 0)) }; }) },
};

export const internetowy = {
  tytul: "Internetowy", tytulPelny: "Marketing - internetowy", ikona: "⌨", odblokowanie: "marketing_internetowy",
  info: "Uruchom narzędzia reklamy internetowej. Uruchomienie kosztuje jednorazowo, utrzymanie co miesiąc. Efekt jest największy w miesiącu uruchomienia.",
  decyzje({ v, kat, edycja }) {
    const narz = kat.oferty.narzedzia_internetowe.pozycje;
    const przed = v.stan_przed.internet, teraz = v.stan.internet;
    const uruch = narz.filter((n) => n.nazwa in teraz && !(n.nazwa in przed)).reduce((s, n) => s + n.uruchomienie, 0);
    const utrz = narz.filter((n) => n.nazwa in teraz).reduce((s, n) => s + n.utrzymanie, 0);
    return `<div class="pasek ciemny"><span>Koszt uruchomienia: <span class="kwota">${zl(uruch)}</span></span><span>Koszt utrzymania: <span class="kwota">${zl(utrz)}</span> / mies.</span></div>
      <div class="siatka trojka" style="margin-top:18px">${narz.map((n) => {
        const ma = n.nazwa in teraz, mial = n.nazwa in przed, dost = (n.od_rundy || 1) <= v.runda;
        return `<div class="kafel ${ma ? "wybrany" : ""} ${dost ? "" : "niedostepny"}"><div class="kg">${esc(n.nazwa)}${n.zalozenie ? '<span class="pigulka inf" title="koszt szacunkowy">≈</span>' : ""}</div><div class="kt">
          <div class="wiersz"><span>Koszt uruchomienia</span><span>${zl(n.uruchomienie)}</span></div>
          <div class="wiersz"><span>Koszt utrzymania</span><span>${zl(n.utrzymanie)}</span></div>
          ${mial ? `<div class="wiersz"><span>Uruchomione</span><span>runda ${przed[n.nazwa]}</span></div>` : ""}</div>
          <div class="kd"><button class="btn ${ma ? (mial ? "pom" : "zielony") : "czarny"}" data-akcja="internet" data-n="${esc(n.nazwa)}" ${edycja && dost ? "" : "disabled"}>
            ${!dost ? `Dostępne od rundy ${n.od_rundy}` : ma ? (mial ? "Wyłącz" : "✓ Wybrano") : mial ? "✓ Wyłączone (włącz)" : "Wybierz"}</button></div></div>`;
      }).join("")}</div>`;
  },
  wyniki({ v, kat }) {
    const w = Object.entries(v.rynek.reklama_internetowa || {}).map(([f, k]) => [esc(nazwaFirmy(v, f)), zl(k)]);
    const ef = v.wyniki?.reklama?.internetowa;
    return tabela("Nakłady na marketing interaktywny", ["Nazwa firmy", "Wydatki"], w, { klasy: ["l"] })
      + tabela(`Efektywność reklamy – wzrost popytu w wyniku wydatków na reklamę: ${proc(ef ?? 0, 2)}`, ["Danie", "Popyt"], efekty(v, kat), { klasy: ["l"] });
  },
  akcje: {
    internet: (el, c) => c.zmien((d) => {
      const n = el.dataset.n, mial = n in c.v.stan_przed.internet;
      const k = mial ? "internet_wylacz" : "internet_uruchom", l = d[k] || [];
      d[k] = l.includes(n) ? l.filter((x) => x !== n) : [...l, n];
    }),
  },
};
