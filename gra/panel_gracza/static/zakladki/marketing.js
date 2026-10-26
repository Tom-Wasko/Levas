// Marketing tradycyjny i internetowy.
import { esc, naOkres, naRunde, OKRES, licz, nazwaFirmy, nazwaUslugi, proc, tabela, wykres, zl } from "./wspolne.js";

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
  ukryta: (v) => !!v.reklama,   // gra z lokalami: agencje reklamowe
  info: () => `Podejmij decyzję o promowaniu Twojej firmy w mediach tradycyjnych. Reklama zwiększa popyt na wszystkie dania w tym ${OKRES.miejscownik}.`,
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
  ukryta: (v) => !!v.reklama,
  info: () => `Uruchom narzędzia reklamy internetowej. Uruchomienie kosztuje jednorazowo, utrzymanie co rundę. Efekt jest największy w rundzie uruchomienia.`,
  decyzje({ v, kat, edycja }) {
    const narz = kat.oferty.narzedzia_internetowe.pozycje;
    const przed = v.stan_przed.internet, teraz = v.stan.internet;
    const uruch = narz.filter((n) => n.nazwa in teraz && !(n.nazwa in przed)).reduce((s, n) => s + n.uruchomienie, 0);
    const utrz = narz.filter((n) => n.nazwa in teraz).reduce((s, n) => s + n.utrzymanie, 0);
    return `<div class="pasek ciemny"><span>Koszt uruchomienia: <span class="kwota">${zl(uruch)}</span></span><span>Koszt utrzymania: <span class="kwota">${zl(naRunde(utrz))}</span>${naOkres()}</span></div>
      <div class="siatka trojka" style="margin-top:18px">${narz.map((n) => {
        const ma = n.nazwa in teraz, mial = n.nazwa in przed, dost = (n.od_rundy || 1) <= v.runda;
        return `<div class="kafel ${ma ? "wybrany" : ""} ${dost ? "" : "niedostepny"}"><div class="kg">${esc(n.nazwa)}${n.zalozenie ? '<span class="pigulka inf" title="koszt szacunkowy">≈</span>' : ""}</div><div class="kt">
          <div class="wiersz"><span>Koszt uruchomienia</span><span>${zl(n.uruchomienie)}</span></div>
          <div class="wiersz"><span>Koszt utrzymania</span><span>${zl(naRunde(n.utrzymanie))}${naOkres()}</span></div>
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

// Agencje reklamowe (gra z lokalami, silnik/reklama.py): kampanie agencja × kanał × strefa zamiast reklamy z Revasa.
const RODZAJ = { druk: "druk", internet: "internet", radio_billboard: "radio i billboardy", wydarzenia: "wydarzenia" };
const FAZA = { trwa: "trwa", wygasa: "wygasa" };
const wybor = {};   // wybrana strefa kanału (agencja/kanał → strefa), do przeliczenia kosztu przed zamówieniem

function strefaKanalu(R, a, k) {
  const klucz = `${a.id}/${k.id}`;
  if (k.zasieg === "miasto") return "miasto";
  if (!k.strefy.includes(wybor[klucz])) wybor[klucz] = k.strefy.find((s) => R.moje_strefy.includes(s)) || k.strefy[0];
  return wybor[klucz];
}

function kanalHtml(v, R, a, k, edycja) {
  const s = strefaKanalu(R, a, k), zam = (v.decyzje.kampanie || []).some((x) => x.agencja === a.id && x.kanal === k.id && (x.strefa || "miasto") === s);
  const trwa = k.trwa.includes(s), inni = (R.konkurencja[a.rodzaj] || {})[s] || [];
  const opcje = k.strefy.map((z) => `<option value="${z}" ${z === s ? "selected" : ""}>${esc(R.strefy[z])}${R.moje_strefy.includes(z) ? " (Twój lokal)" : ""}</option>`).join("");
  const przycisk = !k.dostepny ? `Dostępne od rundy ${k.od_rundy}` : trwa ? "Kampania trwa" : zam ? "✓ Zamówiono (anuluj)" : "Zamów";
  return `<div class="kafel ${zam ? "wybrany" : ""} ${k.dostepny ? "" : "niedostepny"}"><div class="kg">${esc(k.nazwa)}
      <span class="pigulka inf">${k.zasieg === "miasto" ? "całe miasto" : "strefa"}</span></div><div class="kt">
    ${k.zasieg === "miasto" ? "" : `<label class="pole">Strefa<select data-zmiana="kampania-strefa" data-k="${a.id}/${k.id}" ${edycja && k.dostepny ? "" : "disabled"}>${opcje}</select></label>`}
    <div class="wiersz"><span>Koszt (netto)</span><span>${zl(k.koszty[s])}</span></div>
    <div class="wiersz"><span>Czas trwania</span><span>${k.rundy} ${k.rundy === 1 ? "runda" : "rundy"}</span></div>
    <div class="wiersz"><span>Więcej klientów w strefie</span><span>+${proc(k.pula * k.sila[s], 1)}</span></div>
    <div class="wiersz"><span>Przyciąganie do Ciebie</span><span>+${proc(k.przyciaganie * k.sila[s], 1)}</span></div>
    ${k.sila[s] < 1 ? `<div class="wiersz"><span>Siła (powtórka – ludzie już to widzieli)</span><span class="minus">${proc(k.sila[s], 0)}</span></div>` : ""}
    ${inni.length ? `<div class="wiersz"><span>Konkurencja w tym rodzaju (poprzednia runda)</span><span>${inni.map((f) => esc(nazwaFirmy(v, f))).join(", ")}</span></div>` : ""}</div>
    <div class="kd"><button class="btn ${zam ? "zielony" : "czarny"}" data-akcja="kampania" data-a="${a.id}" data-k="${k.id}" data-s="${s}"
      ${edycja && k.dostepny && !trwa ? "" : "disabled"}>${przycisk}</button></div></div>`;
}

function trwajaceHtml(v, lista, tytul) {
  if (!lista.length) return "";
  return tabela(tytul, ["Kampania", "Agencja", "Strefa", "Rundy", "Faza", "Zagłuszanie", "Więcej klientów", "Przyciąganie", "Koszt"],
    lista.map((x) => [esc(x.nazwa), esc(x.agencja_nazwa), esc(x.strefa_nazwa), `${x.od_rundy}–${x.do_rundy}`, FAZA[x.faza],
      x.konkurenci ? `<span class="minus">${proc(x.zagluszanie, 0)}</span> (${x.konkurenci} konk.)` : "–",
      `+${proc(x.pula, 1)}`, `+${proc(x.przyciaganie, 1)}`, x.koszt ? zl(x.koszt) : "–"]), { klasy: ["l", "l", "l"] });
}

export const agencje = {
  tytul: "Agencje reklamowe", tytulPelny: "Marketing - agencje reklamowe", ikona: "tradycyjny",
  odblokowanie: (v) => !!v.reklama && v.runda >= 3, ukryta: (v) => !v.reklama,
  info: () => `Zamów kampanię w jednej z agencji na mieście. Kampania w strefie przyciąga do miasta więcej głodnych (korzystają też sąsiedzi)
    i podbiera klientów konkurencji. Kilka firm reklamujących się tak samo w tej samej strefie zagłusza się nawzajem, a ta sama kampania powtórzona
    zaraz po poprzedniej działa słabiej. Po końcu kampania jeszcze przez chwilę wygasa.`,
  decyzje({ v, edycja }) {
    const R = v.reklama;
    if (!R) return `<p class="podpowiedz">Agencje reklamowe działają w grze z lokalami.</p>`;
    const zam = R.zamowione || [];
    let html = `<div class="pasek ciemny"><span>Zamówione kampanie: <span class="kwota">${zam.length}</span></span>
      <span>Koszt (netto): <span class="kwota">${zl(zam.reduce((s, x) => s + x.koszt, 0))}</span></span></div>`;
    html += trwajaceHtml(v, R.trwajace.filter((x) => x.od_rundy < v.runda), "Twoje kampanie z poprzednich rund – działają w tej rundzie");
    for (const a of R.agencje) {
      html += `<div class="pasek ciemny" style="margin-top:22px"><span>${esc(a.nazwa)}</span><span>${RODZAJ[a.rodzaj] || esc(a.rodzaj)}</span></div>
        <p class="podpowiedz">${esc(a.opis)}</p>
        <div class="siatka trojka" style="margin-top:10px">${a.kanaly.map((k) => kanalHtml(v, R, a, k, edycja)).join("")}</div>`;
    }
    return html;
  },
  wyniki({ v }) {
    const W = v.wyniki?.reklama_agencje;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie z kampanią.</p>`;
    const raporty = W.kampanie.filter((x) => x.tekst);
    let html = raporty.map((x) => `<div class="kafel"><div class="kg">${esc(x.nazwa)} – ${esc(x.strefa_nazwa)}</div>
      <div class="kt"><p>${esc(x.tekst)}</p></div></div>`).join("");
    html += trwajaceHtml(v, W.kampanie, "Twoje kampanie w tej rundzie") || `<p class="podpowiedz">W tej rundzie nie działała żadna Twoja kampania.</p>`;
    const k = v.rynek?.kampanie || {};
    html += tabela("Kampanie na mieście (widać je na słupach i w radiu)", ["Firma", "Wydatki w rundzie", "Kampanie"],
      Object.entries(k).map(([f, x]) => [esc(nazwaFirmy(v, f)), zl(x.wydatki),
        x.kampanie.map((y) => `${esc(y.kanal)} (${esc(y.strefa ? v.reklama?.strefy?.[y.strefa] ?? y.strefa : "całe miasto")}, ${FAZA[y.faza]})`).join(", ")]),
      { klasy: ["l", "", "l"] });
    return html + `<div class="wykres"><canvas id="w-agencje"></canvas></div>`;
  },
  po({ v }, tryb) {
    const k = v.rynek?.kampanie;
    if (tryb !== "wyniki" || !k) return;
    const f = Object.keys(k);
    wykres("w-agencje", "bar", f.map((x) => nazwaFirmy(v, x)), [{ label: "Wydatki na kampanie reklamowe", data: f.map((x) => k[x].wydatki) }]);
  },
  zmiany: { "kampania-strefa": (el, c) => { wybor[el.dataset.k] = el.value; c.rysuj(); } },
  akcje: {
    kampania: (el, c) => c.zmien((d) => {
      const { a, k, s } = el.dataset, strefa = s === "miasto" ? null : s;
      const l = d.kampanie || [];
      const jest = l.some((x) => x.agencja === a && x.kanal === k && (x.strefa ?? null) === strefa);
      d.kampanie = jest ? l.filter((x) => !(x.agencja === a && x.kanal === k && (x.strefa ?? null) === strefa)) : [...l, { agencja: a, kanal: k, strefa }];
    }),
  },
};
