// Kalendarz miejski (gra z lokalami, silnik/rynek/kalendarz.py, dane/kalendarz/kalendarz.yaml): święta, uczelnie, ferie,
// okazje handlowe, mecze Motoru na Arenie i wydarzenia w Lublinie – zmiana puli klientów stref w każdym tygodniu gry
// i popytu na konkretne dania (P14). Układ (przebudowa 2.11.2026): tabela tygodnia dzień po dniu + siatka miesiąca.
import { brakWynikow, esc, licz, nazwaRundy, nazwaUslugi, podsumowanie, tabela, zwinTabela } from "./wspolne.js";
import { kolko } from "./dymki.js";
import { nazwaStrefy } from "./lokale.js";

const DNI = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"];
const MIESIACE = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień",
  "Październik", "Listopad", "Grudzień"];

const dataKrotka = (iso) => { const [, m, d] = iso.split("-"); return `${+d}.${m}`; };
const zakres = (t) => `${dataKrotka(t.od)}–${dataKrotka(t.do)}`;
const zmiana = (x) => `<span class="${x > 0 ? "plus" : "minus"}">${x > 0 ? "+" : "−"}${Math.round(Math.abs(x) * 100)}%</span>`;
// data ISO → Date w południe (bez przesunięć strefy czasowej)
const naDate = (iso) => new Date(`${iso}T12:00:00`);
const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const dzienTyg = (d) => (d.getDay() + 6) % 7;   // 0 = poniedziałek

// treść dymka wydarzenia: rodzaj, dni, opis, pula klientów i dania
function opisWydarzenia(w, kat, rodzaje) {
  const mn = Object.entries(w.strefy || {}).map(([s, m]) => `${s === "wszystkie" ? "reszta miasta" : esc(nazwaStrefy(kat, s))} ×${m}`).join(", ");
  const dania = Object.entries(w.dania || {}).sort((a, b) => b[1] - a[1])
    .map(([u, m]) => `<span class="${m > 1 ? "plus" : "minus"}">${esc(nazwaUslugi(kat, u))} ×${m}</span>`).join(", ");
  return `<p><b>${esc(w.nazwa)}</b> · ${esc(rodzaje[w.rodzaj] || w.rodzaj)}<br>${w.dni.map(dataKrotka).join(", ")}</p>`
    + (w.opis ? `<p>${esc(w.opis)}</p>` : "") + (mn ? `<p>Pula klientów w dniu wydarzenia: ${mn}</p>` : "")
    + (dania ? `<p>Popyt na dania w tych strefach: ${dania}</p>` : "");
}

const strefyLista = (z, kat) => z.map(([s, x]) => `${esc(nazwaStrefy(kat, s))} ${zmiana(x)}`).join(", ") || "–";

// tabela tygodnia: wiersz = dzień; wydarzenia z dymkiem, strefy z większą / mniejszą liczbą klientów, dania
function tabelaTygodnia(t, kat, rodzaje, tytul, zw = false) {
  const poNazwie = Object.fromEntries(t.wydarzenia.map((w) => [w.nazwa, w]));
  const wiersze = (t.dni || []).map((d) => {
    const dt = naDate(d.data), z = Object.entries(d.strefy).sort((a, b) => b[1] - a[1]);
    const dania = Object.entries(d.dania).filter(([, m]) => m > 1).sort((a, b) => b[1] - a[1])
      .map(([u, m]) => `${esc(nazwaUslugi(kat, u))} <span class="plus">×${m}</span>`).join(", ");
    const wyd = d.wydarzenia.map((n) => { const w = poNazwie[n];
      return `<span class="kal-etykieta r-${esc(w?.rodzaj || "")}">${esc(n)}${w ? kolko(opisWydarzenia(w, kat, rodzaje)) : ""}</span>`; }).join(" ");
    return [`<b>${DNI[dzienTyg(dt)]}</b> ${dataKrotka(d.data)}`, wyd || "–", strefyLista(z.filter(([, x]) => x > 0), kat),
      strefyLista(z.filter(([, x]) => x < 0).reverse(), kat), dania || "–"];
  });
  return (zw ? zwinTabela : tabela)(tytul, ["Dzień", "Wydarzenie", "Więcej klientów", "Mniej klientów", "Dania z większym popytem"],
    wiersze, { klasy: ["l", "l", "l", "l", "l"], sortuj: false, ...(zw ? { otwarte: true } : {}) });
}

// --- siatka miesiąca -----------------------------------------------------------------------------------------
let ogladany = null;   // "RRRR-MM" oglądanego miesiąca (null – miesiąc bieżącego tygodnia)

const miesiacZ = (isoData) => isoData.slice(0, 7);
function przesunMiesiac(m, o) {
  const [r, mm] = m.split("-").map(Number), d = new Date(r, mm - 1 + o, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function siatka(K, kat, biezaca) {
  const T = K.tygodnie, min = miesiacZ(T[0].od), max = miesiacZ(T[T.length - 1].do);
  let m = ogladany || miesiacZ(K.biezacy.od);
  if (m < min) m = min;
  if (m > max) m = max;
  ogladany = m;
  // dzień → runda i wydarzenia
  const runda = {}, wyd = {};
  for (const t of T) {
    for (let d = naDate(t.od); iso(d) <= t.do; d.setDate(d.getDate() + 1)) runda[iso(d)] = t.runda;
    for (const w of t.wydarzenia) for (const dz of w.dni) { if (!wyd[dz]) wyd[dz] = new Map(); wyd[dz].set(w.nazwa, w); }
  }
  const [r, mm] = m.split("-").map(Number);
  const pierwszy = new Date(r, mm - 1, 1, 12), start = new Date(pierwszy);
  start.setDate(1 - dzienTyg(pierwszy));
  const wiersze = [];
  for (let tydz = new Date(start); tydz.getMonth() === mm - 1 || tydz < pierwszy; tydz.setDate(tydz.getDate() + 7)) {
    const dni = [...Array(7)].map((_, i) => { const d = new Date(tydz); d.setDate(d.getDate() + i); return d; });
    const rundy = [...new Set(dni.map((d) => runda[iso(d)]).filter(Boolean))];
    const teraz = rundy.includes(biezaca);
    const komorki = dni.map((d) => {
      const k = iso(d), poza = d.getMonth() !== mm - 1, gra = !!runda[k];
      const etykiety = [...(wyd[k]?.values() || [])].map((w) => `<span class="kal-etykieta ma-dymek r-${esc(w.rodzaj)}" tabindex="0">${esc(w.nazwa)}<span class="dymek-tresc">${opisWydarzenia(w, kat, K.rodzaje)}</span></span>`).join("");
      return `<td class="${poza ? "poza" : ""} ${gra ? "" : "bez-gry"}"><div class="kal-dzien">${d.getDate()}</div>${etykiety}</td>`;
    }).join("");
    wiersze.push(`<tr class="${teraz ? "teraz" : ""}"><th class="kal-runda">${rundy.map((x) => esc(nazwaRundy(x))).join("<br>") || ""}${teraz ? "<br><small>teraz</small>" : ""}</th>${komorki}</tr>`);
  }
  const legenda = Object.entries(K.rodzaje).map(([k, n]) => `<span class="kal-etykieta r-${esc(k)}">${esc(n)}</span>`).join(" ");
  return `<div class="kal-glowa"><button class="btn jasny maly" data-akcja="kal-miesiac" data-d="-1" ${m <= min ? "disabled" : ""} aria-label="Poprzedni miesiąc">‹</button>
      <b>${MIESIACE[mm - 1]} ${r}</b>
      <button class="btn jasny maly" data-akcja="kal-miesiac" data-d="1" ${m >= max ? "disabled" : ""} aria-label="Następny miesiąc">›</button></div>
    <div class="tab-wrap"><table class="t kal-siatka"><thead><tr><th>Runda</th>${DNI.map((d) => `<th>${d}</th>`).join("")}</tr></thead>
      <tbody>${wiersze.join("")}</tbody></table></div><div class="kal-legenda">${legenda}</div>`;
}

export const kalendarz = {
  tytul: "Kalendarz miejski", ikona: "kalendarz", ukryta: (v) => !v.kalendarz_miasta,
  info: `<p>Lublin żyje rytmem uczelni, świąt i wydarzeń. Powrót studentów zapełnia Miasteczko Akademickie, przerwa
    świąteczna je wyludnia, jarmark ściąga tłumy na Stare Miasto, a w dzień meczu Motoru kolejka pod Areną sięga
    horyzontu.</p><p>Wydarzenie zmienia liczbę klientów strefy w dniu, w którym trwa, a często też to, co jedzą (kibice –
    kebab w bułce i frytki, Wigilia – falafel). Zaplanuj obsadę, zamówienia i promocje, zanim tydzień się zacznie.</p>
    <p>Zmiana klientów w tygodniu uwzględnia dzień tygodnia: święto w sobotę waży więcej niż w poniedziałek. Pory roku
    (lato nad Zalewem, zima w Centrum) są już w zwykłej puli strefy; im zimniej, tym więcej kebabów i mniej zimnych
    napojów.</p>`,
  decyzje({ v, kat }) {
    const K = v.kalendarz_miasta;
    if (!K) return `<p class="podpowiedz">Brak kalendarza miejskiego.</p>`;
    const B = K.biezacy;
    return tabelaTygodnia(B, kat, K.rodzaje, `${esc(nazwaRundy(B.runda))} – bieżący tydzień (${zakres(B)})`)
      + `<div class="pasek">Kalendarz${kolko("Wiersz to tydzień gry (runda). Najedź na wydarzenie, żeby zobaczyć szczegóły. Dni poza grą są wyszarzone.")}</div>`
      + siatka(K, kat, B.runda);
  },
  wyniki({ v, kat }) {
    const K = v.kalendarz_miasta, P = K?.poprzedni, R = v.rynek?.strefy;
    if (!P) return brakWynikow("Wyniki pojawią się po pierwszej rundzie sprzedaży.");
    const nazwy = [...new Set(P.wydarzenia.map((w) => w.nazwa))];
    const lead = podsumowanie(nazwy.length ? `W minionym tygodniu w mieście działo się: <b>${nazwy.map(esc).join("</b>, <b>")}</b>.`
      : "W minionym tygodniu w mieście nie było większych wydarzeń – klienci przychodzili w zwykłym rytmie.");
    return lead + tabelaTygodnia(P, kat, K.rodzaje, `${esc(nazwaRundy(P.runda))} – miniony tydzień (${zakres(P)})`, true)
      + (R ? zwinTabela("Klienci stref w minionym tygodniu", ["Strefa", "Klienci (pula)", "Zmiana przez kalendarz"],
        Object.entries(R.strefy).map(([s, x]) => [esc(nazwaStrefy(kat, s)), licz(x.pula), P.strefy[s] ? zmiana(P.strefy[s]) : "–"]),
        { klasy: ["l"] }) : "");
  },
  akcje: {
    "kal-miesiac": (el, c) => { ogladany = przesunMiesiac(ogladany || miesiacZ(c.v.kalendarz_miasta.biezacy.od), +el.dataset.d); c.rysuj(); },
  },
};
