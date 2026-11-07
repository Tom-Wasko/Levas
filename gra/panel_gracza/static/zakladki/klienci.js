// Klienci i strefy: popyt strefowy w grze z lokalami (silnik/rynek/popyt.py, dane/mapa/popyt.yaml) – pule klientów stref,
// dni tygodnia, kalendarz miejski i wyniki dzień po dniu. Bez gotowej prognozy – popyt drużyna liczy sama (test gry 28.10).
import { brakWynikow, esc, kafelkiLiczb, licz, podsumowanie, proc, tabela, wykres, zwinTabela } from "./wspolne.js";
import { nazwaStrefy } from "./lokale.js";
import { IG_KLIENCI } from "./infografiki.js";

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
  return `<div class="komunikat"><b>Prognozę popytu liczysz sam</b> (zakładka Menu, krok po kroku w dymku ⓘ przy „Popyt roczny”):
    popyt roczny dania ÷ liczba rund w roku × sezonowość dania × wielkość strefy Twojego lokalu (kolumna niżej), a z tego część,
    którą przyciągniesz ceną i jakością na tle konkurencji w strefie (trochę klientów przychodzi z sąsiednich stref, część zawsze
    idzie do barów spoza gry). Obsługa liczona jest dzień po dniu – godziny pracowników
    i sprzętu rozkładają się równo na ${P.dni.length} dni, więc w najmocniejszym dniu strefy zbyt mała obsada to utracona sprzedaż.</div>`;
}

// dni rundy sprzedaży w strefie: s.dni – mnożnik dnia względem średniego dnia strefy (dni tygodnia × kalendarz,
// silnik/rynek/popyt.py: wagi_dni); słupek na dzień (najmocniejszy ciemny), dymek z mnożnikiem i klientami dnia
function dniStrefy(P, s) {
  const max = Math.max(...s.dni), suma = s.dni.reduce((a, x) => a + x, 0);
  if (!s.dni.length || max <= 0) return "–";
  return `<div class="slupki">${s.dni.map((x, i) =>
    `<i class="${x === max ? "ten" : ""}" data-dymek="${esc(P.dni[i].dzien)} ${dataKrotka(P.dni[i].data)}: popyt × ${licz(x, 2)} (ok. ${licz(s.pula * x / suma)} klientów)"
      ><b style="height:${Math.max(1, Math.round((x / max) * 22))}px"></b></i>`).join("")}</div>`;
}

// U24: najliczniejsze grupy klientów strefy (opis grupy w dymku)
function grupyStrefy(P, s) {
  return Object.entries(s.grupy || {}).slice(0, 3).map(([g, x]) =>
    `<span data-dymek="${esc(P.grupy[g]?.opis || "")}">${esc(P.grupy[g]?.nazwa || g)} ${proc(x)}</span>`).join(", ") || "–";
}

function grupyOpis(P) {
  const g = Object.values(P.grupy || {});
  if (!g.length) return "";
  return `<details class="komunikat"><summary><b>Kim są klienci?</b> Każda grupa ma swoje ulubione dania, inną wrażliwość na cenę
    i cierpliwość w kolejce – to widać potem w opiniach o lokalu.</summary>`
    + g.map((x) => `<p><b>${esc(x.nazwa)}</b> – ${esc(x.opis)}</p>`).join("") + `</details>`;
}

function strefyDecyzje(v, kat) {
  const P = v.popyt;
  const zGrupami = Object.keys(P.grupy || {}).length > 0;
  const wiersze = Object.entries(P.strefy).sort(([, a], [, b]) => b.pula - a.pula).map(([k, s]) => [
    `<span class="kropka" style="background:${esc(kat.mapa.strefy[k].kolor)}"></span>${esc(nazwaStrefy(kat, k))}`,
    `× ${licz(s.wielkosc, 2)}`, licz(s.pula), POZIOM(s.cena), WRAZLIWOSC(s.wrazliwosc_ceny), ...(zGrupami ? [grupyStrefy(P, s)] : []), dniStrefy(P, s)]);
  return grupyOpis(P) + tabela("Strefy miasta", ["Strefa", "Wielkość strefy", "Klienci strefy", "Ceny", "Wrażliwość na cenę",
    ...(zGrupami ? ["Najwięcej klientów"] : []), "Klienci w dni tygodnia"],
    wiersze, { klasy: ["l", "", "", "l", "l", "l", "l"] })
    + `<p class="podpowiedz">Wielkość strefy – mnożnik popytu rocznego dania w miesiącu sprzedaży (× 1 = przeciętna strefa; z porą roku).
      Klienci strefy – wszyscy chętni na dania z Twojego menu w rundzie sprzedaży, zanim podzielą się między lokale
      (Twoje i konkurencji) i bary spoza gry.</p>`;
}

function wynikiDni(k) {
  return zwinTabela("Klienci dzień po dniu", ["Dzień", "Data", "Popyt", "Sprzedaż", "Utracona sprzedaż"],
    k.dni.map((d) => [d.dzien, dataKrotka(d.data), licz(d.popyt), licz(d.sprzedaz), d.utracona ? `<span class="minus">${licz(d.utracona)}</span>` : "0"]),
    { klasy: ["l", "l"], stopka: ["Razem", "", ...["popyt", "sprzedaz", "utracona"].map((x) => licz(k.dni.reduce((s, d) => s + d[x], 0)))], otwarte: true });
}

function wynikiLokale(k, kat, P) {
  const zGrupami = k.lokale.some((l) => l.grupy && Object.keys(l.grupy).length);
  return zwinTabela("Lokale – skąd przyszli klienci", ["Lokal", "Strefa", "Popyt", "Sprzedaż", "Klienci ze stref",
    ...(zGrupami ? ["Grupy klientów"] : [])],
    k.lokale.map((l) => [esc(l.nazwa), esc(nazwaStrefy(kat, l.strefa)), licz(l.popyt), licz(l.sprzedaz),
      Object.entries(l.strefy).slice(0, 4).map(([s, n]) => `${esc(nazwaStrefy(kat, s))}: ${licz(n)}`).join(", "),
      ...(zGrupami ? [Object.entries(l.grupy || {}).slice(0, 3).map(([g, n]) => `${esc(P?.grupy?.[g]?.nazwa || g)}: ${licz(n)}`).join(", ")] : [])]),
    { klasy: ["l", "l", "", "", "l", "l"] });
}

// U24: ocena lokali z opinii klientów i jej powody (gwiazdki za jakość, cenę, kolejkę…)
const POWODY = { jakosc: "Jakość", cena: "Cena", kolejka: "Kolejka", brak: "Brak dań", reklamacje: "Reklamacje", wyposazenie: "Wyposażenie" };
const gw = (x) => x == null ? "–" : x.toFixed(1).replace(".", ",");
function wynikiOpinie(v, k) {
  const o = v.wyniki?.opinie;
  if (!o || !Object.keys(o).length) return "";
  const nazwa = Object.fromEntries(k.lokale.map((l) => [l.id, l.nazwa]));
  const znak = (x) => x >= 0.05 ? `<span class="plus">+${gw(x)}</span>` : x <= -0.05 ? `<span class="minus">${gw(x)}</span>` : "0";
  return zwinTabela("Opinie klientów o Twoich lokalach", ["Lokal", "Ocena tygodnia", ...Object.values(POWODY), "Nowe opinie", "Ocena na mapie", "Mnożnik popytu"],
    Object.entries(o).map(([id, x]) => [esc(nazwa[id] || id), `★ ${gw(x.ocena_tygodnia)}`, ...Object.keys(POWODY).map((p) => znak(x.powody[p])),
      licz(x.nowe), `★ ${gw(x.ocena)} (${licz(x.liczba)})`, `× ${licz(x.mnoznik, 2)}`]), { klasy: ["l"], sortuj: false })
    + `<p class="podpowiedz">Ocena tygodnia to ocena wyjściowa ± powody (w gwiazdkach): jakość dań, cena wobec cen w strefie, klienci odesłani
      z kolejki albo bez dania, reklamacje, wyposażenie. Ocena na mapie to średnia z opinii – nowe ważą więcej, stare z czasem tracą znaczenie.
      Im więcej opinii, tym mocniej ocena działa na klientów: lokal z oceną powyżej przeciętnej przyciąga ich więcej.</p>`;
}

function wynikiStrefy(v, kat, R) {
  const wiersze = Object.entries(R.strefy).sort(([, a], [, b]) => b.pula - a.pula).map(([k, s]) => {
    const moi = s.klienci[v.firma] || 0;
    const inni = Object.entries(s.klienci).filter(([f]) => f !== v.firma).reduce((x, [, n]) => x + n, 0);
    return [esc(nazwaStrefy(kat, k)), licz(s.pula), licz(moi), s.pula ? proc(moi / s.pula) : "–", licz(inni), s.pula ? proc(1 - (moi + inni) / s.pula) : "–"];
  });
  return zwinTabela("Strefy – podział klientów", ["Strefa", "Klienci strefy", "Twoje lokale", "Udział", "Konkurencja", "Poza grą (inne bary, dom)"], wiersze, { klasy: ["l"] });
}

export const klienci = {
  tytul: "Klienci", tytulPelny: "Klienci i strefy", ikona: "klienci", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Każda strefa miasta ma własnych klientów – ich liczba zależy od dania, pory roku, dnia tygodnia i wydarzeń w mieście.
    Klienci strefy to różne grupy (studenci, pracownicy biur, rodziny, turyści…) – każda ma ulubione dania i inną wrażliwość na cenę.
    Wybierając lokal, patrzą na cenę względem cen w strefie, jakość, odległość lokalu (sąsiednie strefy też przychodzą, ale mniej)
    i opinie innych klientów o lokalu (gwiazdki na mapie). Dwa lokale w jednej strefie dzielą tych samych klientów, a część klientów zawsze wybiera bary spoza gry albo obiad w domu.${IG_KLIENCI}`,
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
    if (!k || !R) return brakWynikow("Wyniki pojawią się po pierwszej rundzie sprzedaży.");
    const S = (x) => k.dni.reduce((a, d) => a + d[x], 0), chetni = S("popyt"), obsl = S("sprzedaz"), utr = S("utracona");
    const lead = podsumowanie([`W tej rundzie do Twoich lokali przyszło <b>${licz(chetni)}</b> chętnych, obsłużyliście <b>${licz(obsl)}</b> (${proc(chetni ? obsl / chetni : 0, 0)}).`,
      utr >= 1 ? `${licz(utr)} klientów odeszło bez dania.` : "Nikt nie odszedł bez dania."], chetni && utr / chetni >= 0.1 ? "uwaga" : "ok");
    const kafle = kafelkiLiczb([{ etykieta: "Chętni", wartosc: licz(chetni) }, { etykieta: "Obsłużeni", wartosc: licz(obsl) },
      { etykieta: "Odeszli bez dania", wartosc: licz(utr), ton: utr >= 1 ? "minus" : "plus" }]);
    return lead + kafle + (R.wydarzenia.length ? `<div class="pasek">Wydarzenia w mieście</div>${wydarzeniaHtml(R.wydarzenia, kat)}` : "")
      + `<div class="wykres"><canvas id="w-klienci-dni"></canvas></div>` + wynikiDni(k) + wynikiLokale(k, kat, v.popyt) + wynikiOpinie(v, k) + wynikiStrefy(v, kat, R);
  },
  po({ v }, tryb) {
    const k = v.wyniki?.klienci;
    if (tryb !== "wyniki" || !k) return;
    wykres("w-klienci-dni", "bar", k.dni.map((d) => `${d.dzien} ${dataKrotka(d.data)}`),
      [{ label: "Sprzedaż", data: k.dni.map((d) => d.sprzedaz), stack: "a" }, { label: "Utracona sprzedaż", data: k.dni.map((d) => d.utracona), stack: "a" }],
      { scales: { x: { stacked: true }, y: { stacked: true } } });
  },
};
