// Mapa miasta (prototyp): izometryczny Lublin ze strefami, lokalami i budynkami – alternatywa dla menu.
// Kliknięcie budynku otwiera jego zakładkę, kliknięcie lokalu – opis i najem/kupno, własnego lokalu – zakładki firmy.
import { esc, marka, nazwaFirmy, okno, toast, zamknijOkno } from "./wspolne.js";
import { nazwaStrefy, opisLokalu, przyciskiLokalu, wybranyLokal } from "./lokale.js";

const PW = 22, PH = 11;  // połowa pola siatki na ekranie (romb 44 × 22 px)
const MARGINES = 16, NAD = 70;  // miejsce nad mapą na wysokie budynki

const BUDYNKI = {  // rodzaj → kolor dachu i wysokość
  bank: ["#2d73d6", 30], urzad: ["#9b51e0", 40], poczta: ["#f2b705", 22], biuro: ["#17a2b8", 26], nieruchomosci: ["#e5333f", 24],
  praca: ["#795548", 24], dostawca: ["#a0522d", 18], sklep: ["#5c6bc0", 20], szkola: ["#26a69a", 26], reklama: ["#ec407a", 22],
  uczelnia: ["#3f51b5", 34], media: ["#455a64", 28], lichwiarz: ["#3b2f2f", 16],
  ubezpieczenia: ["#43a047", 26], detektyw: ["#5d4037", 18],
};
const LOKAL = { moj: "#1e9e5a", wybrany: "#e45f26", wolny: "#ffffff", zajety: "#9aa0a8" };
const FIRMA = ["oferta", "stanowiska", "sprzet", "zatrudnienie", "sprzedaz", "kpir"];

function geometria(siatka) {
  const ox = MARGINES + siatka.gl * PW;
  const p = (x, y, h = 0) => [ox + (x - y) * PW, NAD + (x + y) * PH - h];
  return { p, szer: 2 * MARGINES + (siatka.szer + siatka.gl) * PW, wys: NAD + MARGINES + (siatka.szer + siatka.gl) * PH };
}

const pkt = (lista) => lista.map(([a, b]) => `${a.toFixed(1)},${b.toFixed(1)}`).join(" ");
const romb = (g, x, y, s, l, h = 0) => [g.p(x, y, h), g.p(x + s, y, h), g.p(x + s, y + l, h), g.p(x, y + l, h)];

// prostopadłościan: dwie widoczne ściany (ciemniejsze) i dach
function bryla(g, x, y, s, l, h, kolor, obrys = "rgba(0,0,0,.25)") {
  const lewa = [g.p(x, y + l), g.p(x + s, y + l), g.p(x + s, y + l, h), g.p(x, y + l, h)];
  const prawa = [g.p(x + s, y), g.p(x + s, y + l), g.p(x + s, y + l, h), g.p(x + s, y, h)];
  const sciana = (pts, cien) => `<polygon points="${pkt(pts)}" fill="${kolor}" stroke="${obrys}" stroke-width=".8"/>`
    + `<polygon points="${pkt(pts)}" fill="#000" opacity="${cien}"/>`;
  return sciana(lewa, 0.18) + sciana(prawa, 0.32)
    + `<polygon points="${pkt(romb(g, x, y, s, l, h))}" fill="${kolor}" stroke="${obrys}" stroke-width=".8"/>`;
}

function drzewa(g, x, y, s, l) {
  let html = "";
  for (let i = 0; i < s; i++) for (let j = 0; j < l; j++) {
    const [a, b] = g.p(x + i + 0.5, y + j + 0.5);
    html += `<line x1="${a}" y1="${b}" x2="${a}" y2="${b - 8}" stroke="#6d4c2f" stroke-width="2"/><circle cx="${a}" cy="${b - 13}" r="7" fill="#3f9b4b"/>`;
  }
  return html;
}

function budynek(g, b) {
  const { x, y, szer: s, gl: l } = b.mapa;
  const tytul = `<title>${esc(b.nazwa)} – ${esc(b.opis)}</title>`;
  let ksztalt;
  if (b.rodzaj === "park") ksztalt = `<polygon points="${pkt(romb(g, x, y, s, l))}" fill="#9fd48a" stroke="#6fa85c"/>` + drzewa(g, x, y, s, l);
  else if (b.rodzaj === "woda") ksztalt = `<polygon points="${pkt(romb(g, x + 0.1, y + 0.1, s - 0.2, l - 0.2))}" fill="#7cc3e8" stroke="#4d9cc6"/>`;
  else {
    const [kolor, h] = BUDYNKI[b.rodzaj] || ["#888", 22];
    ksztalt = bryla(g, x + 0.08, y + 0.08, s - 0.16, l - 0.16, h, kolor);
  }
  return { klucz: x + y + s + l, html: `<g class="klik" data-akcja="mapa-budynek" data-id="${esc(b.id)}">${tytul}${ksztalt}</g>` };
}

function lokal(g, v, d, kat, lok) {
  const { x, y } = lok.mapa;
  const moje = (v.lokale.moje || []).find((l) => l.id === lok.id);
  const wyb = wybranyLokal(d)?.id === lok.id;
  const kto = v.lokale.zajete[lok.id];
  const stan = moje ? (wyb ? "wybrany" : "moj") : kto ? "zajety" : "wolny";
  const kolor = stan === "zajety" ? marka(v, kto).kolor : LOKAL[stan];   // lokal innej firmy – w jej kolorze
  const ktoNapis = moje ? (wyb ? "wybrany przez Ciebie w tej rundzie" : "Twój lokal") : kto ? `zajęty: ${nazwaFirmy(v, kto)}` : "wolny";
  const tytul = `<title>${esc(lok.nazwa)} (${esc(nazwaStrefy(kat, lok.strefa))}) – ${esc(ktoNapis)}</title>`;
  let ksztalt;
  if (lok.typ === "dzialka" && (stan === "wolny" || (moje && !moje.dziala))) {
    ksztalt = `<polygon points="${pkt(romb(g, x + 0.1, y + 0.1, 0.8, 0.8))}" fill="${stan === "wolny" ? "#d8bf8f" : kolor}"
      stroke="#8a6d3b" stroke-dasharray="3 2" stroke-width="1.2"/>`;
  } else {
    const h = moje && !moje.dziala ? 8 : 16;
    ksztalt = bryla(g, x + 0.18, y + 0.18, 0.64, 0.64, h, kolor, stan === "wolny" ? "#555" : "rgba(0,0,0,.3)");
  }
  const znacznik = stan === "wolny" || stan === "wybrany" || stan === "moj"
    ? (() => { const [a, b] = g.p(x + 0.5, y + 0.5, lok.typ === "dzialka" ? 6 : 26); return `<circle cx="${a}" cy="${b}" r="3.2" fill="${LOKAL[stan === "wolny" ? "moj" : stan]}" stroke="#fff"/>`; })() : "";
  return { klucz: x + y + 2, html: `<g class="klik lokal-${stan}" data-akcja="mapa-lokal" data-id="${esc(lok.id)}">${tytul}${ksztalt}${znacznik}</g>` };
}

function rysujMape(c) {
  const { v, kat, d } = c;
  const M = kat.mapa, g = geometria(M.siatka);
  let teren = `<polygon points="${pkt(romb(g, 0, 0, M.siatka.szer, M.siatka.gl))}" fill="#dfe8d2" stroke="#c4cfb4"/>`;
  let napisy = "";
  for (const s of Object.values(M.strefy)) {
    const { x, y, szer, gl } = s.mapa;
    teren += `<polygon points="${pkt(romb(g, x, y, szer, gl))}" fill="${esc(s.kolor)}" opacity=".55" stroke="#fff" stroke-width="1.5"/>`;
    const [a, b] = g.p(x + szer / 2, y + gl);
    napisy += `<text x="${a}" y="${b - 4}" class="strefa-napis">${esc(s.nazwa)}</text>`;
  }
  const obiekty = M.budynki.map((b) => budynek(g, b));
  if (v.lokale) obiekty.push(...M.lokale.filter((l) => (l.od_rundy || 1) <= v.runda).map((l) => lokal(g, v, d, kat, l)));
  obiekty.sort((a, b) => a.klucz - b.klucz);
  return `<svg class="mapa-svg" viewBox="0 0 ${g.szer} ${g.wys}" role="img" aria-label="Mapa miasta">
    ${teren}${obiekty.map((o) => o.html).join("")}${napisy}</svg>`;
}

// lokale innych firm – w kolorze firmy (marka z rundy 1)
const firmyNaMapie = (v) => [...new Set(Object.values(v.lokale.zajete))].filter((f) => f !== v.firma)
  .map((f) => `<span><i style="background:${esc(marka(v, f).kolor)}"></i>${esc(marka(v, f).nazwa)}</span>`).join("");

const legenda = (v) => `<div class="mapa-legenda">
  ${v.lokale ? Object.entries({ moj: "Twój lokal", wybrany: "wybrany w tej rundzie", wolny: "wolny lokal" })
    .map(([k, n]) => `<span><i style="background:${LOKAL[k]}"></i>${n}</span>`).join("") + `<span><i style="background:#d8bf8f"></i>wolna działka</span>` + firmyNaMapie(v) : ""}
  ${Object.entries({ bank: "bank", urzad: "ratusz", dostawca: "dostawcy", sklep: "sklepy", reklama: "reklama", szkola: "szkolenia" })
    .map(([k, n]) => `<span><i style="background:${BUDYNKI[k][0]}"></i>${n}</span>`).join("")}</div>`;

export const mapa = {
  tytul: "Mapa miasta", ikona: "mapa",
  info: "Mapa Lublina: kliknij budynek, żeby przejść do jego zakładki (bank, ratusz, dostawcy, agencje…), albo lokal, żeby go obejrzeć i wynająć lub kupić. Menu po lewej działa jak dotąd.",
  decyzje(c) {
    const brak = c.v.lokale && !c.v.lokale.moje.length
      ? `<div class="komunikat">Nie masz jeszcze lokalu – kliknij wolny lokal (biały) albo działkę na mapie.</div>` : "";
    return brak + `<div class="mapa-ramka">${rysujMape(c)}</div>${legenda(c.v)}`;
  },
  akcje: {
    "mapa-budynek": (el, c) => {
      const b = c.kat.mapa.budynki.find((x) => x.id === el.dataset.id);
      if (!b.zakladka) return toast(`${b.nazwa}: ${b.opis}`);
      if (!c.dostepna(b.zakladka)) return toast(`${b.nazwa} – ta zakładka nie jest jeszcze dostępna w tej rundzie.`);
      c.idz(b.zakladka);
    },
    "mapa-lokal": (el, c) => {
      const lok = c.kat.mapa.lokale.find((x) => x.id === el.dataset.id);
      const moje = c.v.lokale.moje.find((l) => l.id === lok.id);
      const oferta = c.v.lokale.oferta.find((l) => l.id === lok.id);
      const kto = c.v.lokale.zajete[lok.id];
      let html = opisLokalu(c.kat, lok), przyciski = "";
      if (oferta) {
        przyciski = przyciskiLokalu(c.v, c.d, oferta, c.edycja);
        if (c.v.runda < c.v.lokale.nowy_od) html += `<p class="podpowiedz">${esc(c.v.lokale.odpoczynek || `Kolejny lokal możesz wziąć od rundy ${c.v.lokale.nowy_od}.`)}</p>`;
      }
      if (moje && !oferta) {
        html += `<p><b>Twój lokal</b> (${moje.forma === "najem" ? "najem" : "własność"}) – ${moje.dziala ? "działa" : `zacznie działać w rundzie ${moje.dziala_od}`}.</p>`;
        przyciski = FIRMA.filter((k) => c.dostepna(k)).map((k) => `<button class="btn jasny maly" data-akcja="mapa-idz" data-z="${k}">${esc(c.tytulZakladki(k))}</button>`).join("");
      } else if (kto && !oferta) html += `<p class="podpowiedz">Lokal zajmuje firma ${esc(nazwaFirmy(c.v, kto))}.</p>`;
      okno(esc(lok.nazwa), html, { przyciski });
    },
    "mapa-idz": (el, c) => { zamknijOkno(); c.idz(el.dataset.z); },
  },
};
