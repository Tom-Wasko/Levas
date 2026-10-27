// Kalendarz miejski (gra z lokalami, silnik/kalendarz.py, dane/kalendarz/kalendarz.yaml): święta, uczelnie, ferie,
// okazje handlowe i wydarzenia w Lublinie – zmiana puli klientów stref w każdym tygodniu gry.
import { esc, licz, nazwaRundy, tabela } from "./wspolne.js";
import { nazwaStrefy } from "./lokale.js";

const dataKrotka = (iso) => { const [, m, d] = iso.split("-"); return `${+d}.${m}`; };
const zakres = (t) => `${dataKrotka(t.od)}–${dataKrotka(t.do)}`;
const zmiana = (x) => `<span class="${x > 0 ? "plus" : "minus"}">${x > 0 ? "+" : "−"}${Math.round(Math.abs(x) * 100)}%</span>`;

function strefyHtml(t, kat) {
  const z = Object.entries(t.strefy).sort((a, b) => b[1] - a[1]);
  if (!z.length) return "";
  return `<div class="podpowiedz">Klienci w tygodniu: ${z.map(([s, x]) => `${esc(nazwaStrefy(kat, s))} ${zmiana(x)}`).join(", ")}</div>`;
}

function wydarzeniaHtml(t, kat, rodzaje) {
  if (!t.wydarzenia.length) return `<p class="podpowiedz">Zwykły tydzień – w mieście nic szczególnego się nie dzieje.</p>`;
  return t.wydarzenia.map((w) => {
    const mn = Object.entries(w.strefy).map(([s, m]) => `${s === "wszystkie" ? "reszta miasta" : esc(nazwaStrefy(kat, s))} ×${m}`).join(", ");
    return `<div class="karta"><b>${esc(w.nazwa)}</b> <span class="podpowiedz">${esc(rodzaje[w.rodzaj] || w.rodzaj)} ·
      ${w.dni.map(dataKrotka).join(", ")}</span><p>${esc(w.opis)}</p><div class="podpowiedz">Pula klientów w dniu wydarzenia: ${mn}</div></div>`;
  }).join("") + strefyHtml(t, kat);
}

function przeglad(K, kat, biezaca) {
  return tabela("Tygodnie gry", ["Runda", "Dni", "Wydarzenia", "Najwięcej klientów", "Najmniej klientów"],
    K.tygodnie.map((t) => {
      const z = Object.entries(t.strefy).sort((a, b) => b[1] - a[1]);
      const gora = z.filter(([, x]) => x > 0).slice(0, 2), dol = z.filter(([, x]) => x < 0).slice(-2).reverse();
      const nr = t.runda === biezaca ? `<b>${esc(nazwaRundy(t.runda))} (teraz)</b>` : esc(nazwaRundy(t.runda));
      return [nr, zakres(t), t.wydarzenia.map((w) => esc(w.nazwa)).join(", ") || "–",
        gora.map(([s, x]) => `${esc(nazwaStrefy(kat, s))} ${zmiana(x)}`).join(", ") || "–",
        dol.map(([s, x]) => `${esc(nazwaStrefy(kat, s))} ${zmiana(x)}`).join(", ") || "–"];
    }), { klasy: ["l", "l", "l", "l", "l"], sortuj: false });
}

export const kalendarz = {
  tytul: "Kalendarz miejski", ikona: "kalendarz", ukryta: (v) => !v.kalendarz_miasta,
  info: `Lublin żyje rytmem uczelni, świąt i wydarzeń. Sesja zapełnia Miasteczko Akademickie głodnymi studentami,
    przerwa świąteczna je wyludnia, a jarmark ściąga tłumy na Stare Miasto. Wydarzenie zmienia liczbę klientów
    strefy w dniu, w którym trwa – zaplanuj obsadę, zamówienia i promocje, zanim tydzień się zacznie.`,
  decyzje({ v, kat }) {
    const K = v.kalendarz_miasta;
    if (!K) return `<p class="podpowiedz">Brak kalendarza miejskiego.</p>`;
    const B = K.biezacy;
    const dalej = K.tygodnie.filter((t) => t.runda > B.runda && t.runda <= B.runda + 4 && t.wydarzenia.length);
    return `<div class="pasek ciemny"><span>${esc(nazwaRundy(B.runda))}: <span class="kwota">${zakres(B)}</span></span>
        <span>Wydarzenia: <span class="kwota">${B.wydarzenia.length || "brak"}</span></span></div>`
      + wydarzeniaHtml(B, kat, K.rodzaje)
      + (dalej.length ? `<div class="pasek">Następne tygodnie</div>` + dalej.map((t) => `<div class="komunikat"><b>${esc(nazwaRundy(t.runda))}</b>
          (${zakres(t)}): ${t.wydarzenia.map((w) => esc(w.nazwa)).join(", ")}${strefyHtml(t, kat)}</div>`).join("") : "")
      + przeglad(K, kat, B.runda)
      + `<p class="podpowiedz">Zmiana klientów w tygodniu uwzględnia dzień tygodnia: święto w sobotę waży więcej niż
        w poniedziałek. Zmiany pór roku (lato nad Zalewem, zima w Centrum) są już w zwykłej puli strefy.</p>`;
  },
  wyniki({ v, kat }) {
    const K = v.kalendarz_miasta, P = K?.poprzedni, R = v.rynek?.strefy;
    if (!P) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie sprzedaży.</p>`;
    return `<div class="pasek ciemny"><span>${esc(nazwaRundy(P.runda))}: <span class="kwota">${zakres(P)}</span></span></div>`
      + wydarzeniaHtml(P, kat, K.rodzaje)
      + (R ? tabela("Klienci stref w minionym tygodniu", ["Strefa", "Klienci (pula)", "Zmiana przez kalendarz"],
        Object.entries(R.strefy).map(([s, x]) => [esc(nazwaStrefy(kat, s)), licz(x.pula), P.strefy[s] ? zmiana(P.strefy[s]) : "–"]),
        { klasy: ["l"] }) : "");
  },
};
