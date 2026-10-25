// Wspólne funkcje interfejsu: formatowanie, okna dialogowe, wykresy.

export const MIESIACE = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień",
  "Październik", "Listopad", "Grudzień"];

const fmt = (min, max) => new Intl.NumberFormat("pl-PL", { minimumFractionDigits: min, maximumFractionDigits: max });
const F0 = fmt(0, 0), F2 = fmt(2, 2), F3 = fmt(0, 3);

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const zl = (x, grosze = false) => x == null ? "–" : (grosze ? F2 : F0).format(x) + " PLN";
export const zl2 = (x) => zl(x, true);
export const licz = (x, max = 0) => x == null ? "–" : fmt(0, max).format(x);
export const ulamek = (x) => x == null ? "–" : F3.format(x);
export const proc = (x, miejsca = 1) => x == null ? "–" : fmt(miejsca, miejsca).format(x * 100) + "%";
export const wsk = (x) => x == null ? "–" : fmt(3, 3).format(x);
export const gw = (n) => {
  const g = Math.round(n || 0);
  return `<span class="gwiazdki">${"★".repeat(g)}<span class="p">${"★".repeat(Math.max(0, 3 - g))}</span></span>`;
};
export const inicjaly = (imie) => esc(String(imie || "?").split(" ").map((x) => x[0]).join("").slice(0, 2));

export function info(tekst) {
  return `<div class="info"><span class="i">i</span><span>${tekst}</span></div>`;
}

export function tabela(tytul, naglowki, wiersze, { stopka = null, klasy = [] } = {}) {
  const th = naglowki.map((h, i) => `<th class="${klasy[i] || ""}">${h}</th>`).join("");
  const tr = wiersze.map((w) => `<tr>${w.map((c, i) => `<td class="${klasy[i] || ""}">${c ?? ""}</td>`).join("")}</tr>`).join("");
  const tf = stopka ? `<tfoot><tr>${stopka.map((c, i) => `<td class="${klasy[i] || ""}">${c ?? ""}</td>`).join("")}</tr></tfoot>` : "";
  const brak = wiersze.length ? "" : `<tr><td colspan="${naglowki.length}">Brak danych</td></tr>`;
  return `${tytul ? `<div class="tabela-tytul">${tytul}</div>` : ""}<div class="tab-wrap"><table class="t"><thead><tr>${th}</tr></thead><tbody>${tr}${brak}</tbody>${tf}</table></div>`;
}

let _okno = null;
export function okno(tytul, html, { male = false, przyciski = "" } = {}) {
  zamknijOkno();
  const z = document.createElement("div");
  z.className = "zaslona";
  z.innerHTML = `<div class="okno ${male ? "male" : ""}"><div class="og"><span>${tytul}</span><span class="x" data-akcja="zamknij-okno">✕</span></div>
    <div class="ot">${html}</div>${przyciski ? `<div class="ost">${przyciski}</div>` : ""}</div>`;
  z.addEventListener("click", (e) => { if (e.target === z) zamknijOkno(); });
  document.body.appendChild(z);
  _okno = z;
  return z;
}
export function zamknijOkno() { if (_okno) { _okno.remove(); _okno = null; } }

export function toast(tekst) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = tekst;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

const wykresy = [];
export function wyczyscWykresy() { while (wykresy.length) wykresy.pop().destroy(); }
export const KOLORY = ["#e45f26", "#2d73d6", "#00c06a", "#9b51e0", "#f2b705", "#e5333f", "#17a2b8", "#795548"];
// kolory wykresów z bieżącego motywu (zmienne CSS --wykres-*); kolor serii może być nazwą zmiennej, np. "--wykres-linia"
const zmienna = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function paleta() {
  const p = zmienna("--wykres-paleta");
  return p ? p.split(",").map((x) => x.trim()) : KOLORY;
}
export function wykres(id, typ, etykiety, serie, opcje = {}) {
  const el = document.getElementById(id);
  if (!el || !window.Chart) return;
  const kolory = paleta(), tekst = zmienna("--wykres-tekst"), siatka = zmienna("--wykres-siatka"), font = zmienna("--wykres-font");
  if (tekst) Chart.defaults.color = tekst;
  if (siatka) Chart.defaults.borderColor = siatka;
  Chart.defaults.font.family = font || "Montserrat, sans-serif";
  const kolor = (s, i) => (s.kolor && s.kolor.startsWith("--") ? zmienna(s.kolor) : s.kolor) || kolory[i % kolory.length];
  wykresy.push(new Chart(el, {
    type: typ,
    data: { labels: etykiety, datasets: serie.map((s, i) => ({ ...s, backgroundColor: kolor(s, i), borderColor: kolor(s, i),
      borderWidth: (s.type || typ) === "line" ? 2 : 0, borderRadius: (s.type || typ) === "bar" ? 3 : 0 })) },
    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: "top" } }, ...opcje },
  }));
}

export const nazwaUslugi = (kat, u) => kat.uslugi[u]?.nazwa ?? u;
export const nazwaFirmy = (v, f) => v.rynek?.firmy?.[f] ?? f;
