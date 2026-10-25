// Inwestycje: stanowiska, sprzęt, wyposażenie dla klientów.
import { esc, naOkres, naRunde, OKRES, gw, licz, nazwaFirmy, nazwaUslugi, okno, proc, tabela, toast, wykres, zamknijOkno, zl } from "./wspolne.js";

const TYPY = ["kuchnia", "kasa"];  // nazwy typów: kat.oferty.stanowiska.typy (katalog.yaml)
const suma = (pozycje, start) => pozycje.filter((p) => p.opis.startsWith(start)).reduce((s, p) => s + p.pozostale, 0);

export const stanowiska = {
  tytul: "Stanowiska", tytulPelny: "Inwestycje - stanowiska", ikona: "▥", odblokowanie: "inwestycje_stanowiska",
  info: "Uruchom potrzebną liczbę stanowisk w Twojej firmie. Stanowisko działa już w rundzie zakupu. Każdy pracownik potrzebuje swojego stanowiska.",
  decyzje({ v, kat, edycja }) {
    const pakiety = kat.oferty.stanowiska.pakiety;
    const nowe = v.decyzje.stanowiska || {};
    const koszt = suma(v.koszty_decyzji, "Uruchomienie stanowiska");
    let html = `<div class="pasek ciemny"><span>${OKRES.przymiotnik} koszt utrzymania lokalu: <span class="kwota">${zl(naRunde(kat.parametry.utrzymanie_klubu))}</span></span>
      <span>Nowe stanowiska: <span class="kwota">${zl(koszt)}</span></span></div><div class="dwie" style="margin-top:20px">`;
    for (const typ of TYPY) {
      const maja = v.stan_przed.stanowiska.filter((s) => s.typ === typ).length;
      html += `<div class="kafel"><div class="kg kg-pelny">
        ${esc(kat.oferty.stanowiska.typy[typ].nazwa)} – liczba posiadanych: <span style="font-size:22px">${maja}</span></div><div class="kt">
        ${Object.entries(pakiety).map(([n, c]) => `<div class="wiersz" style="align-items:center;padding:10px 0;border-bottom:1px solid var(--linia)">
          <span>Koszt uruchomienia (${n} ${n === "1" ? "stanowiska" : "stanowisk"})</span><span>${zl(c)}</span>
          ${+nowe[typ] === +n ? `<button class="btn zielony maly" data-akcja="pakiet" data-t="${typ}" data-n="0" ${edycja ? "" : "disabled"}>✓ Wybrano</button>`
                             : `<button class="btn jasny maly" data-akcja="pakiet" data-t="${typ}" data-n="${n}" ${edycja ? "" : "disabled"}>Wybierz</button>`}</div>`).join("")}
        </div></div>`;
    }
    return html + `</div><p class="podpowiedz">W jednej rundzie można uruchomić jeden pakiet każdego rodzaju (do 5 stanowisk). Puste stanowiska nie generują kosztów.</p>`;
  },
  akcje: { pakiet: (el, c) => c.zmien((d) => { d.stanowiska = { ...(d.stanowiska || {}), [el.dataset.t]: +el.dataset.n }; }) },
};

function sprzetStanowiska(v, typ, nr) {
  const teraz = v.stan.stanowiska.find((s) => s.typ === typ && s.nr === nr) || { sprzet: {} };
  const przed = v.stan_przed.stanowiska.find((s) => s.typ === typ && s.nr === nr) || { sprzet: {} };
  return { teraz: teraz.sprzet, przed: przed.sprzet, st: teraz };
}

export const sprzet = {
  tytul: "Sprzęt", tytulPelny: "Inwestycje - sprzęt", ikona: "⚙", odblokowanie: "inwestycje_sprzet",
  info: "Kup sprzęt potrzebny do przygotowania wybranych przez Ciebie dań. Sprzęt kupuje się na konkretne stanowisko.",
  decyzje({ v, kat, edycja }) {
    const koszt = suma(v.koszty_decyzji, "Koszt zakupu: ");
    const utrz = v.stan.stanowiska.reduce((s, st) => s + Object.entries(st.sprzet).reduce((a, [n, q]) => a + kat.sprzet[n].utrzymanie[q], 0), 0);
    let html = `<div class="pasek ciemny"><span>Koszty całkowite zakupu: <span class="kwota">${zl(koszt)}</span></span>
      <span>Koszt utrzymania sprzętu: <span class="kwota">${zl(naRunde(utrz))}</span>${naOkres()}</span></div>`;
    for (const typ of TYPY) {
      const st = v.stan.stanowiska.filter((s) => s.typ === typ);
      html += `<div class="pasek">${esc(kat.oferty.stanowiska.typy[typ].nazwa)}</div>`;
      if (!st.length) { html += `<p class="podpowiedz">Brak stanowisk – uruchom je w zakładce Inwestycje → Stanowiska.</p>`; continue; }
      html += `<div class="siatka">${st.map((s) => {
        const { przed } = sprzetStanowiska(v, typ, s.nr);
        const p = v.stan.pracownicy.find((x) => x.id === s.pracownik);
        const lista = Object.entries(s.sprzet).map(([n, q]) => `<div class="wiersz"><span>${esc(n)}</span><span>${gw(q)}${n in przed ? "" : ' <span class="pigulka inf">nowy</span>'}</span></div>`).join("")
          || `<p class="podpowiedz">Brak sprzętu</p>`;
        const uslugi = typ === "kuchnia" ? Object.entries(kat.uslugi).filter(([, u]) => u.sprzet.every((n) => n in s.sprzet)).map(([k]) => nazwaUslugi(kat, k)) : [];
        return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}<span class="podpowiedz">${p ? esc(p.imie_nazwisko) : "bez pracownika"}</span></div>
          <div class="kt">${lista}${uslugi.length ? `<p class="podpowiedz">Można przygotować: ${uslugi.map(esc).join(", ")}</p>` : ""}</div>
          <div class="kd"><button class="btn czarny" data-akcja="kup-sprzet" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Kup sprzęt</button>
          ${Object.keys(przed).length ? `<button class="btn pom" data-akcja="sprzedaj-sprzet" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Sprzedaj sprzęt</button>` : ""}</div></div>`;
      }).join("")}</div>`;
    }
    return html;
  },
  wyniki({ v, kat }) {
    const own = (v.wyniki?.sprzet || []).map((s) => [`${esc(kat.oferty.stanowiska.typy[s.typ]?.kto || s.typ)} nr ${s.stanowisko}`, esc(s.nazwa), gw(s.jakosc), proc(s.oblozenie)]);
    const firmy = Object.keys(v.rynek?.sprzet || {});
    const ile = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...[1, 2, 3].map((q) => licz(v.rynek.sprzet[f][q])),
      licz([1, 2, 3].reduce((a, q) => a + v.rynek.sprzet[f][q], 0))]);
    return tabela("Liczba i jakość sprzętów", ["Firma", "Niska ★", "Średnia ★★", "Wysoka ★★★", "Razem"], ile, { klasy: ["l"] })
      + tabela("Obłożenie sprzętu (Twoja firma)", ["Stanowisko", "Sprzęt", "Jakość", "Obłożenie"], own, { klasy: ["l", "l"] })
      + `<p class="podpowiedz">Obłożenie = godziny pracy sprzętu / 160 h. 100% oznacza, że sprzęt nie mógł obsłużyć kolejnych klientów.</p>`;
  },
  akcje: {
    "kup-sprzet": (el, c) => oknoZakupu(c, el.dataset.t, +el.dataset.n),
    "sprzedaj-sprzet": (el, c) => oknoSprzedazy(c, el.dataset.t, +el.dataset.n),
    "kup-poz": async (el, c) => {
      const { t, n, nazwa, q } = el.dataset;
      await c.zmien((d) => {
        d.sprzet_kup = (d.sprzet_kup || []).filter((x) => !(x.typ === t && x.nr === +n && x.nazwa === nazwa));
        if (q !== "0") d.sprzet_kup.push({ typ: t, nr: +n, nazwa, jakosc: +q });
      });
      oknoZakupu(c, t, +n);
    },
    "kup-komplet": async (el, c) => {
      const { t, n } = el.dataset;
      const u = document.getElementById("komplet-usluga").value, q = +document.getElementById("komplet-jakosc").value;
      const nazwy = t === "kasa" ? c.kat.sprzet_kasy : c.kat.uslugi[u].sprzet;
      const { teraz } = sprzetStanowiska(c.v, t, +n);
      const brak = nazwy.filter((x) => !(x in teraz));
      if (!brak.length) return toast("Stanowisko ma już cały ten sprzęt.");
      await c.zmien((d) => { d.sprzet_kup = [...(d.sprzet_kup || []), ...brak.map((nazwa) => ({ typ: t, nr: +n, nazwa, jakosc: q }))]; });
      oknoZakupu(c, t, +n);
    },
    "sprzedaj-poz": async (el, c) => {
      const { t, n, nazwa } = el.dataset;
      await c.zmien((d) => {
        const l = d.sprzet_sprzedaj || [];
        const jest = l.some((x) => x.typ === t && x.nr === +n && x.nazwa === nazwa);
        d.sprzet_sprzedaj = jest ? l.filter((x) => !(x.typ === t && x.nr === +n && x.nazwa === nazwa)) : [...l, { typ: t, nr: +n, nazwa }];
      });
      oknoSprzedazy(c, t, +n);
    },
  },
};

function oknoZakupu(c, typ, nr) {
  const { v, kat } = c;
  const { teraz, przed } = sprzetStanowiska(v, typ, nr);
  const nazwy = Object.keys(kat.sprzet).filter((n) => kat.sprzet[n].dla === typ);
  const wiersze = [];
  for (const n of nazwy) for (const q of [1, 2, 3]) {
    const kupione = (v.decyzje.sprzet_kup || []).some((x) => x.typ === typ && x.nr === nr && x.nazwa === n && x.jakosc === q);
    const posiadany = n in przed;
    const przycisk = posiadany ? `<span class="pigulka ok">w posiadaniu ${gw(przed[n])}</span>`
      : kupione ? `<button class="btn zielony maly" data-akcja="kup-poz" data-t="${typ}" data-n="${nr}" data-nazwa="${esc(n)}" data-q="0">✓ Kupione</button>`
      : `<button class="btn pom maly" data-akcja="kup-poz" data-t="${typ}" data-n="${nr}" data-nazwa="${esc(n)}" data-q="${q}" ${n in teraz ? "disabled" : ""}>Kup</button>`;
    wiersze.push([esc(n), gw(q), esc(kat.oferty.stanowiska.typy[typ].kto), zl(kat.sprzet[n].ceny[q]), zl(naRunde(kat.sprzet[n].utrzymanie[q])), przycisk]);
  }
  const uslugi = Object.entries(kat.uslugi).map(([k, u]) => `<option value="${k}">${esc(u.nazwa)}</option>`).join("");
  const komplet = `<div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap;margin-bottom:12px">
    ${typ === "kuchnia" ? `<label class="pole" style="flex:1">Komplet sprzętu dla dania<select id="komplet-usluga">${uslugi}</select></label>` : `<input type="hidden" id="komplet-usluga" value="">`}
    <label class="pole">Jakość<select id="komplet-jakosc"><option value="3">★★★ wysoka</option><option value="2">★★ średnia</option><option value="1">★ niska</option></select></label>
    <button class="btn czarny" data-akcja="kup-komplet" data-t="${typ}" data-n="${nr}">Kup brakujący ${typ === "kasa" ? "komplet kasy" : "komplet"}</button></div>`;
  okno(`Zakup sprzętu na stanowisko „Stanowisko nr ${nr}”`, komplet + tabela(null,
    ["Nazwa sprzętu", "Jakość", "Wykorzystanie sprzętu", "Koszt zakupu", `Koszt utrzymania${naOkres()}`, ""], wiersze, { klasy: ["l"] }),
    { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">OK</button>` });
}

function oknoSprzedazy(c, typ, nr) {
  const { v, kat } = c;
  const { przed } = sprzetStanowiska(v, typ, nr);
  const sprzedawane = (v.decyzje.sprzet_sprzedaj || []).filter((x) => x.typ === typ && x.nr === nr).map((x) => x.nazwa);
  const w = Object.entries(przed).map(([n, q]) => [esc(n), gw(q), zl(v.ceny_sprzedazy_sprzetu[n][q]), zl(naRunde(kat.sprzet[n].utrzymanie[q])),
    `<button class="btn ${sprzedawane.includes(n) ? "zielony" : "pom"} maly" data-akcja="sprzedaj-poz" data-t="${typ}" data-n="${nr}" data-nazwa="${esc(n)}">${sprzedawane.includes(n) ? "✓ Sprzedane" : "Sprzedaj"}</button>`]);
  const przychod = Object.entries(przed).filter(([n]) => sprzedawane.includes(n)).reduce((s, [n, q]) => s + v.ceny_sprzedazy_sprzetu[n][q], 0);
  okno(`Sprzedaż sprzętu ze stanowiska „Stanowisko nr ${nr}”`, tabela(null, ["Nazwa", "Jakość", "Przychody ze sprzedaży", `Koszt utrzymania${naOkres()}`, ""], w, { klasy: ["l"] })
    + `<p><b>Przychody ze sprzedaży: ${zl(przychod)}</b></p>`, { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">OK</button>` });
}

export const wyposazenie = {
  tytul: "Wyposażenie", tytulPelny: "Inwestycje - wyposażenie", ikona: "☕", odblokowanie: "inwestycje_wyposazenie",
  info: "Kup dodatkowe wyposażenie dla klientów Twojej firmy. Wyposażenie podnosi zadowolenie klientów i przyciąga ich do lokalu.",
  decyzje(c) { return kafleUdogodnien(c, "wyposazenie", "klientów"); },
  wyniki({ v }) {
    const w = Object.entries(v.rynek?.wyposazenie || {}).map(([f, n]) => [esc(nazwaFirmy(v, f)), licz(n)]);
    return tabela("Posiadane wyposażenie", ["Firma", "Liczba pozycji wyposażenia"], w, { klasy: ["l"] });
  },
  akcje: { "kup-udog": (el, c) => przelaczUdog(el, c), "sprzedaj-udog": (el, c) => przelaczUdog(el, c) },
};

export function kafleUdogodnien({ v, kat, edycja }, rodzaj, kogo) {
  const pozycje = kat.oferty[rodzaj].pozycje.filter((p) => p.od_rundy <= v.runda);
  const przed = v.stan_przed[rodzaj], teraz = v.stan[rodzaj];
  const kupno = pozycje.filter((p) => teraz.includes(p.nazwa) && !przed.includes(p.nazwa)).reduce((s, p) => s + p.cena, 0);
  const utrz = pozycje.filter((p) => teraz.includes(p.nazwa)).reduce((s, p) => s + p.utrzymanie, 0);
  const sprzedaz = pozycje.filter((p) => przed.includes(p.nazwa) && !teraz.includes(p.nazwa)).reduce((s, p) => s + p.cena / 2, 0);
  return `<div class="pasek ciemny"><span>Koszt zakupu: <span class="kwota">${zl(kupno)}</span></span>
    <span>Koszt utrzymania: <span class="kwota">${zl(naRunde(utrz))}</span>${naOkres()}</span><span>Przychody ze sprzedaży: <span class="kwota">${zl(sprzedaz)}</span></span></div>
    <div class="siatka trojka" style="margin-top:20px">${pozycje.map((p) => {
      const mial = przed.includes(p.nazwa), ma = teraz.includes(p.nazwa);
      const przycisk = mial
        ? `<button class="btn ${ma ? "pom" : "zielony"}" data-akcja="sprzedaj-udog" data-r="${rodzaj}" data-nazwa="${esc(p.nazwa)}" ${edycja ? "" : "disabled"}>${ma ? "Sprzedaj" : "✓ Sprzedane"}</button>`
        : `<button class="btn ${ma ? "zielony" : "czarny"}" data-akcja="kup-udog" data-r="${rodzaj}" data-nazwa="${esc(p.nazwa)}" ${edycja ? "" : "disabled"}>${ma ? "✓ Wybrano" : "Wybierz"}</button>`;
      return `<div class="kafel ${ma ? "wybrany" : ""}"><div class="kg">${esc(p.nazwa)}<span class="pigulka inf" title="% ${kogo} oczekujących">${p.procent}%</span></div>
        <div class="kt"><div class="wiersz"><span>${mial ? "Cena sprzedaży" : "Cena zakupu"}</span><span>${zl(mial ? p.cena / 2 : p.cena)}</span></div>
        <div class="wiersz"><span>Koszt utrzymania</span><span>${zl(naRunde(p.utrzymanie))}${naOkres()}</span></div>
        <div class="wiersz"><span>% ${kogo} oczekujących</span><span>${p.procent}%</span></div></div><div class="kd">${przycisk}</div></div>`;
    }).join("")}</div>`;
}

export async function przelaczUdog(el, c) {
  const r = el.dataset.r, n = el.dataset.nazwa;
  const mial = c.v.stan_przed[r].includes(n);
  await c.zmien((d) => {
    const k = mial ? `${r}_sprzedaj` : `${r}_kup`;
    const l = d[k] || [];
    d[k] = l.includes(n) ? l.filter((x) => x !== n) : [...l, n];
  });
}

export { zamknijOkno, wykres };
