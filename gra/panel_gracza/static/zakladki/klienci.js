// Klienci i strefy: popyt strefowy w grze z lokalami (silnik/rynek/popyt.py, dane/mapa/popyt.yaml) – pule klientów stref,
// dni tygodnia, kalendarz miejski i wyniki dzień po dniu. Bez gotowej prognozy – popyt drużyna liczy sama (test gry 28.10).
import { esc, licz, nazwaFirmy, proc, tabela, wykres } from "./wspolne.js";
import { nazwaStrefy } from "./lokale.js";

const dataKrotka = (iso) => { const [, m, d] = iso.split("-"); return `${+d}.${m}`; };
const POZIOM = (x) => x >= 1.08 ? "wysokie" : x <= 0.92 ? "niskie" : "średnie";
const WRAZLIWOSC = (x) => x >= 1.25 ? "duża" : x <= 0.8 ? "mała" : "średnia";

function wydarzeniaHtml(lista, kat) {
  return lista.map((w) => {
    const strefy = Object.entries(w.strefy).map(([s, m]) => `${s === "wszystkie" ? "całe miasto" : esc(nazwaStrefy(kat, s))} ×${m}`).join(", ");
    return `<div class="komunikat"><b>${esc(w.nazwa)}</b> (${w.dni.map(dataKrotka).join(", ")}) – ${esc(w.opis)}
      <div class="podpowiedz">Klienci: ${strefy}</div></div>`;
  }).join("");
}

function jakLiczyc(P) {
  return `<div class="komunikat"><b>Prognozę popytu liczysz sam</b> (zakładka Menu): weź klientów strefy, w której masz lokal
    (trochę przychodzi też z sąsiednich stref), oceń, jaką ich część przyciągniesz ceną i jakością na tle konkurencji w strefie,
    i pamiętaj, że część klientów zawsze idzie do barów spoza gry. Obsługa liczona jest dzień po dniu – godziny pracowników
    i sprzętu rozkładają się równo na ${P.dni.length} dni, więc w najmocniejszym dniu strefy zbyt mała obsada to utracona sprzedaż.</div>`;
}

function strefyDecyzje(v, kat) {
  const P = v.popyt;
  const najmocniejszy = (s) => s.dni.length ? P.dni[s.dni.indexOf(Math.max(...s.dni))].dzien : "–";
  const wiersze = Object.entries(P.strefy).sort(([, a], [, b]) => b.pula - a.pula).map(([k, s]) => [
    `<span class="kropka" style="background:${esc(kat.mapa.strefy[k].kolor)}"></span>${esc(nazwaStrefy(kat, k))}`,
    licz(s.pula), POZIOM(s.cena), WRAZLIWOSC(s.wrazliwosc_ceny), najmocniejszy(s),
    s.firmy.length ? s.firmy.map((f) => f === v.firma ? "<b>Ty</b>" : esc(nazwaFirmy(v, f))).join(", ") : "–"]);
  return tabela("Strefy miasta", ["Strefa", "Klienci strefy", "Ceny", "Wrażliwość na cenę", "Najwięcej klientów", "Lokale firm"],
    wiersze, { klasy: ["l", "", "l", "l", "l", "l"] })
    + `<p class="podpowiedz">Klienci strefy – wszyscy chętni na dania z Twojego menu w rundzie sprzedaży, zanim podzielą się między lokale
      (Twoje i konkurencji) i bary spoza gry.</p>`;
}

function wynikiDni(k) {
  return tabela("Klienci dzień po dniu", ["Dzień", "Data", "Popyt", "Sprzedaż", "Utracona sprzedaż"],
    k.dni.map((d) => [d.dzien, dataKrotka(d.data), licz(d.popyt), licz(d.sprzedaz), d.utracona ? `<span class="minus">${licz(d.utracona)}</span>` : "0"]),
    { klasy: ["l", "l"], stopka: ["Razem", "", ...["popyt", "sprzedaz", "utracona"].map((x) => licz(k.dni.reduce((s, d) => s + d[x], 0)))] })
    + `<div class="wykres"><canvas id="w-klienci-dni"></canvas></div>`;
}

function wynikiLokale(k, kat) {
  return tabela("Lokale – skąd przyszli klienci", ["Lokal", "Strefa", "Popyt", "Sprzedaż", "Klienci ze stref"],
    k.lokale.map((l) => [esc(l.nazwa), esc(nazwaStrefy(kat, l.strefa)), licz(l.popyt), licz(l.sprzedaz),
      Object.entries(l.strefy).slice(0, 4).map(([s, n]) => `${esc(nazwaStrefy(kat, s))}: ${licz(n)}`).join(", ")]), { klasy: ["l", "l", "", "", "l"] });
}

function wynikiStrefy(v, kat, R) {
  const wiersze = Object.entries(R.strefy).sort(([, a], [, b]) => b.pula - a.pula).map(([k, s]) => {
    const moi = s.klienci[v.firma] || 0;
    const inni = Object.entries(s.klienci).filter(([f]) => f !== v.firma).reduce((x, [, n]) => x + n, 0);
    return [esc(nazwaStrefy(kat, k)), licz(s.pula), licz(moi), s.pula ? proc(moi / s.pula) : "–", licz(inni), s.pula ? proc(1 - (moi + inni) / s.pula) : "–"];
  });
  return tabela("Strefy – podział klientów", ["Strefa", "Klienci strefy", "Twoje lokale", "Udział", "Konkurencja", "Poza grą (inne bary, dom)"], wiersze, { klasy: ["l"] });
}

export const klienci = {
  tytul: "Klienci", tytulPelny: "Klienci i strefy", ikona: "klienci", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Każda strefa miasta ma własnych klientów – ich liczba zależy od dania, pory roku, dnia tygodnia i wydarzeń w mieście.
    Klienci strefy wybierają lokal: liczy się cena względem cen w strefie, jakość, odległość lokalu (sąsiednie strefy też przychodzą, ale mniej)
    i zadowolenie klientów firmy. Dwa lokale w jednej strefie dzielą tych samych klientów, a część klientów zawsze wybiera bary spoza gry albo obiad w domu.`,
  decyzje({ v, kat }) {
    const P = v.popyt;
    if (!P) return `<p class="podpowiedz">Brak danych o klientach.</p>`;
    const dni = `${dataKrotka(P.dni[0].data)}–${dataKrotka(P.dni[P.dni.length - 1].data)}`;
    return `<div class="pasek ciemny"><span>Runda sprzedaży: <span class="kwota">${P.runda}</span></span><span>Dni: <span class="kwota">${dni}</span></span>
      <span>Wydarzenia w mieście: <span class="kwota">${P.wydarzenia.length || "brak"}</span></span></div>`
      + wydarzeniaHtml(P.wydarzenia, kat) + jakLiczyc(P) + strefyDecyzje(v, kat);
  },
  wyniki({ v, kat }) {
    const k = v.wyniki?.klienci, R = v.rynek?.strefy;
    if (!k || !R) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie sprzedaży.</p>`;
    return (R.wydarzenia.length ? `<div class="pasek">Wydarzenia w mieście</div>${wydarzeniaHtml(R.wydarzenia, kat)}` : "")
      + wynikiDni(k) + wynikiLokale(k, kat) + wynikiStrefy(v, kat, R);
  },
  po({ v }, tryb) {
    const k = v.wyniki?.klienci;
    if (tryb !== "wyniki" || !k) return;
    wykres("w-klienci-dni", "bar", k.dni.map((d) => `${d.dzien} ${dataKrotka(d.data)}`),
      [{ label: "Sprzedaż", data: k.dni.map((d) => d.sprzedaz), stack: "a" }, { label: "Utracona sprzedaż", data: k.dni.map((d) => d.utracona), stack: "a" }],
      { scales: { x: { stacked: true }, y: { stacked: true } } });
  },
};
