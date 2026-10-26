// Wspólne funkcje interfejsu: formatowanie, okna dialogowe, wykresy.

// Kalendarz rund (katalog.yaml: rundy.kalendarz) – ustawiany z widoku gry (v.gra.kalendarz) przy każdym wczytaniu.
// Kwoty miesięczne z danych (utrzymanie, czynsz) silnik księguje na rundę: naRunde.
export const OKRES = { mianownik: "miesiąc", dopelniacz: "miesiąca", miejscownik: "miesiącu", skrot: "mies.",
  przymiotnik: "Miesięczny", mnoga: "miesiące", rund_w_roku: 12 };
let KAL = null;
export function ustawKalendarz(k) {
  if (!k) return;
  KAL = k;
  Object.assign(OKRES, k.okres, { rund_w_roku: k.rund_w_roku });
}
export const nazwaRundy = (r) => KAL?.nazwy[r - 1] ?? `Runda ${r}`;
export const skrotRundy = (r) => KAL?.skroty[r - 1] ?? `R${r}`;
export const miesiacRundy = (r) => KAL?.miesiace[r - 1] ?? (r - 1) % 12;
export const naRunde = (kwotaMiesieczna) => OKRES.rund_w_roku === 12 ? kwotaMiesieczna : kwotaMiesieczna * 12 / OKRES.rund_w_roku;
export const naOkres = () => ` / ${OKRES.skrot}`;

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
// godzina z czasu ISO (zapis decyzji przez kogoś z drużyny)
export const godzina = (iso) => iso ? new Date(iso).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) : "";
// limit nowych pracowników na rundę (silnik/limity.py): czy po dodaniu jeszcze jednego będzie przekroczony
export const ponadLimitPracownikow = (v, zatrudnij, podkup) => !!v.agencja && zatrudnij.length + podkup.length >= v.agencja.limit;
export const tekstLimituPracownikow = (v) => `W jednej rundzie możesz przyjąć najwyżej ${v.agencja.limit} nowych pracowników
  (zatrudnienia i oferty podkupienia razem). Zrezygnuj z któregoś albo poczekaj do następnej rundy.`;
// termin zamknięcia rundy z harmonogramu mistrza gry, np. „środa, 28 października, 08:00”
export const termin = (iso) => iso ? new Date(iso).toLocaleString("pl-PL",
  { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }) : "";
export const inicjaly = (imie) => esc(String(imie || "?").split(" ").map((x) => x[0]).join("").slice(0, 2));

export function info(tekst) {
  return `<div class="info"><span class="i">i</span><span>${tekst}</span></div>`;
}

// --- sortowanie tabel: klik w nagłówek – rosnąco, malejąco, kolejność pierwotna. Stan per tabela (tytuł + nagłówki)
// zostaje po przerysowaniu widoku; w oknach (np. baza składników) wiersze układa się od razu w DOM.
const _sort = {};
const _tekst = (h) => String(h ?? "").replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").trim();

// wartość komórki do porównania: liczba („1 234,56 PLN”, „−3%”, „≈ 120”, „★★”), tekst albo null (pusta, „–”)
export function kluczSortu(html) {
  const t = _tekst(html);
  if (!t || t === "–" || t === "-") return null;
  if (/^★+$/.test(t)) return t.length;
  const m = t.replace(/[\s\u00a0\u202f≈~]/g, "").replace(/^−/, "-").match(/^[-+]?\d+(?:,\d+)?/);
  return m ? parseFloat(m[0].replace(",", ".")) : t.toLowerCase();
}

function porownaj(a, b, kier) {
  if (a === null || b === null) return a === b ? 0 : a === null ? 1 : -1;   // puste zawsze na końcu
  if (typeof a !== typeof b) return typeof a === "number" ? -kier : kier;
  return (typeof a === "number" ? a - b : a.localeCompare(b, "pl", { numeric: true })) * kier;
}

function ulozone(lista, komorka, s) {
  if (!s) return lista;
  return lista.map((x, i) => [x, kluczSortu(komorka(x)), i])
    .sort(([, ka, ia], [, kb, ib]) => porownaj(ka, kb, s.kier) || ia - ib).map(([x]) => x);
}

export function przelaczSortowanie(th) {
  const klucz = th.dataset.sort, k = +th.dataset.k, s = _sort[klucz];
  const nowy = _sort[klucz] = !s || s.k !== k ? { k, kier: 1 } : s.kier === 1 ? { k, kier: -1 } : null;
  const tab = th.closest("table"), tb = tab.tBodies[0];
  tab.querySelectorAll("th[data-sort]").forEach((h) => h.classList.remove("rosnaco", "malejaco"));
  if (nowy) th.classList.add(nowy.kier === 1 ? "rosnaco" : "malejaco");
  const rzedy = [...tb.rows].sort((a, b) => a.dataset.i - b.dataset.i);
  ulozone(rzedy, (r) => r.cells[k]?.innerHTML, nowy).forEach((r) => tb.appendChild(r));
}

export function tabela(tytul, naglowki, wiersze, { stopka = null, klasy = [], sortuj = true } = {}) {
  const klucz = sortuj && wiersze.length > 1 ? _tekst(`${tytul || ""}|${naglowki.join("|")}`) : null;
  const s = klucz ? _sort[klucz] : null;
  const th = naglowki.map((h, i) => {
    const kier = s && s.k === i ? (s.kier === 1 ? " rosnaco" : " malejaco") : "";
    return klucz ? `<th class="${klasy[i] || ""}${kier}" data-sort="${esc(klucz)}" data-k="${i}" title="Kliknij, aby posortować">${h}</th>`
      : `<th class="${klasy[i] || ""}">${h}</th>`;
  }).join("");
  const wi = ulozone(wiersze.map((w, i) => [w, i]), ([w]) => s && w[s.k], s);
  const tr = wi.map(([w, n]) => `<tr data-i="${n}">${w.map((c, i) => `<td class="${klasy[i] || ""}">${c ?? ""}</td>`).join("")}</tr>`).join("");
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
