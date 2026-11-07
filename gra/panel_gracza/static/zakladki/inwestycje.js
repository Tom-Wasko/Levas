// Inwestycje: stanowiska, sprzęt, wyposażenie dla klientów.
import { kosztLokali, miejscaLokali } from "./lokale.js";
import { esc, naOkres, naRunde, gw, kafelkiLiczb, licz, nazwaFirmy, nazwaUslugi, okno, podsumowanie, proc, tabela, toast, wykres, zamknijOkno, zl, zwinTabela } from "./wspolne.js";
import { decyzjaLokalu, idWybranego, listaLokalu, nazwaLokalu, opisLokalu, stanowiskaLokalu } from "./lokal_wybor.js";

// Z3: miejsca na stanowiska – przy kilku lokalach tylko w wybranym lokalu
function miejscaWybranego(v, typ) {
  const id = idWybranego(v), l = id && opisLokalu(v, id);
  return l ? { wszystkie: l.miejsca[typ], zajete: l.zajete[typ] } : miejscaLokali(v, typ);
}

const TYPY = ["kuchnia", "kasa"];  // nazwy typów: kat.oferty.stanowiska.typy (katalog.yaml)
const suma = (pozycje, start) => pozycje.filter((p) => p.opis.startsWith(start)).reduce((s, p) => s + p.pozostale, 0);

export const stanowiska = {
  tytul: "Stanowiska", tytulPelny: "Inwestycje - stanowiska", ikona: "▥", odblokowanie: "inwestycje_stanowiska",
  info: "Uruchom potrzebną liczbę stanowisk w Twojej firmie. Stanowisko działa już w rundzie zakupu. Każdy pracownik potrzebuje swojego stanowiska.",
  decyzje({ v, kat, edycja }) {
    const pakiety = kat.oferty.stanowiska.pakiety;
    const id = idWybranego(v), nowe = decyzjaLokalu(v.decyzje, v, "stanowiska") || {};
    const koszt = suma(v.koszty_decyzji, "Uruchomienie stanowiska");
    let html = `<div class="pasek ciemny"><span>Koszt lokali (czynsz i media): <span class="kwota">${zl(kosztLokali(v))}</span></span>
      <span>Nowe stanowiska: <span class="kwota">${zl(koszt)}</span></span></div><div class="dwie" style="margin-top:20px">`;
    for (const typ of TYPY) {
      const maja = stanowiskaLokalu(v, v.stan_przed.stanowiska).filter((s) => s.typ === typ).length;
      const m = miejscaWybranego(v, typ);
      const miejsca = m ? `<div class="podpowiedz" style="padding:8px 0">Miejsca w lokalach: zajęte ${m.zajete} z ${m.wszystkie}${m.wszystkie ? "" : " – najpierw wybierz lokal (zakładka Nowe lokale)"}</div>` : "";
      html += `<div class="kafel"><div class="kg kg-pelny">
        ${esc(kat.oferty.stanowiska.typy[typ].nazwa)} – liczba posiadanych: <span style="font-size:22px">${maja}</span></div><div class="kt">${miejsca}
        ${Object.entries(pakiety).map(([n, c]) => `<div class="wiersz" style="align-items:center;padding:10px 0;border-bottom:1px solid var(--linia)">
          <span>Koszt uruchomienia (${n} ${n === "1" ? "stanowiska" : "stanowisk"})</span><span>${zl(c)}</span>
          ${+nowe[typ] === +n ? `<button class="btn zielony maly" data-akcja="pakiet" data-t="${typ}" data-n="0" ${edycja ? "" : "disabled"}>✓ Wybrano</button>`
                             : `<button class="btn jasny maly" data-akcja="pakiet" data-t="${typ}" data-n="${n}" ${edycja ? "" : "disabled"}>Wybierz</button>`}</div>`).join("")}
        </div></div>`;
    }
    return html + `</div><p class="podpowiedz">${id ? `Stanowiska powstaną w lokalu <b>${esc(nazwaLokalu(v, id))}</b>. ` : ""}W jednej rundzie można uruchomić jeden pakiet każdego rodzaju (do 5 stanowisk). Puste stanowiska nie generują kosztów.</p>`;
  },
  wyniki({ v, kat }) {
    const typy = kat.oferty.stanowiska.typy, sprzet = v.wyniki?.sprzet || [];
    let razemSt = 0;
    const own = TYPY.map((typ) => {
      const st = stanowiskaLokalu(v, v.stan.stanowiska).filter((s) => s.typ === typ), m = miejscaWybranego(v, typ);
      razemSt += st.length;
      const ob = sprzet.filter((s) => s.typ === typ).map((s) => s.oblozenie);
      return [esc(typy[typ].nazwa), licz(st.length), m ? `${licz(m.zajete)} z ${licz(m.wszystkie)}` : "–",
        ob.length ? proc(ob.reduce((a, x) => a + x, 0) / ob.length) : "–", ob.length ? proc(Math.max(...ob)) : "–"];
    });
    const rs = v.rynek?.stanowiska || {};
    const firmy = Object.keys(rs).map((f) => [esc(nazwaFirmy(v, f)), ...TYPY.map((t) => licz(rs[f][t] || 0))]);
    const obl = sprzet.map((s) => s.oblozenie), srOb = obl.length ? obl.reduce((a, x) => a + x, 0) / obl.length : null, maxOb = obl.length ? Math.max(...obl) : null;
    const lead = podsumowanie([`Firma ma ${razemSt} ${razemSt === 1 ? "stanowisko" : razemSt >= 2 && razemSt <= 4 ? "stanowiska" : "stanowisk"}.`,
      maxOb == null ? "" : maxOb >= 0.95 ? "Któryś sprzęt pracował niemal na pełnych obrotach – to wąskie gardło." : `Najbardziej obciążony sprzęt pracował na ${proc(maxOb)} swoich możliwości.`], maxOb >= 0.95 ? "uwaga" : "");
    const kafle = kafelkiLiczb([{ etykieta: "Stanowiska", wartosc: licz(razemSt) }, srOb != null && { etykieta: "Średnie obłożenie sprzętu", wartosc: proc(srOb) },
      maxOb != null && { etykieta: "Najwyższe obłożenie", wartosc: proc(maxOb), ton: maxOb >= 0.95 ? "minus" : "" }]);
    return lead + kafle + zwinTabela("Twoje stanowiska", ["Rodzaj", "Liczba", "Miejsca w lokalach (zajęte)", "Średnie obłożenie sprzętu", "Najwyższe obłożenie"], own, { klasy: ["l"], otwarte: true })
      + (firmy.length ? zwinTabela("Stanowiska konkurencji", ["Firma", ...TYPY.map((t) => esc(typy[t].nazwa))], firmy, { klasy: ["l"] }) : "")
      + `<p class="podpowiedz">Obłożenie blisko 100% oznacza, że sprzęt był wąskim gardłem – kolejne stanowisko (i pracownik) przyjmie więcej klientów.</p>`;
  },
  akcje: {
    pakiet: (el, c) => c.zmien((d) => {
      const id = idWybranego(c.v), wpis = { [el.dataset.t]: +el.dataset.n };
      if (!id) { d.stanowiska = { ...(d.stanowiska || {}), ...wpis }; return; }
      d.w_lokalu = d.w_lokalu || {};
      d.w_lokalu[id] = { ...(d.w_lokalu[id] || {}), stanowiska: { ...(d.w_lokalu[id]?.stanowiska || {}), ...wpis } };
    }),
  },
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
    const utrz = stanowiskaLokalu(v, v.stan.stanowiska).reduce((s, st) => s + Object.entries(st.sprzet).reduce((a, [n, q]) => a + kat.sprzet[n].utrzymanie[q], 0), 0);
    let html = `<div class="pasek ciemny"><span>Koszty całkowite zakupu: <span class="kwota">${zl(koszt)}</span></span>
      <span>Koszt utrzymania sprzętu: <span class="kwota">${zl(naRunde(utrz))}</span>${naOkres()}</span></div>`;
    for (const typ of TYPY) {
      const st = stanowiskaLokalu(v, v.stan.stanowiska).filter((s) => s.typ === typ);
      html += `<div class="pasek">${esc(kat.oferty.stanowiska.typy[typ].nazwa)}</div>`;
      if (!st.length) { html += `<p class="podpowiedz">Brak stanowisk${idWybranego(v) ? " w tym lokalu" : ""} – uruchom je w części Stanowiska.</p>`; continue; }
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
    const sp = v.wyniki?.sprzet || [], top = sp.length ? sp.reduce((a, s) => (s.oblozenie > a.oblozenie ? s : a)) : null;
    const lead = podsumowanie(top ? [`Firma ma ${sp.length} ${sp.length === 1 ? "sprzęt" : "sprzętów"} w użyciu; najbardziej obciążony to ${esc(top.nazwa)} (${proc(top.oblozenie)}).`,
      top.oblozenie >= 0.95 ? "Ten sprzęt nie nadążał z obsługą – warto dołożyć drugi albo lepszy." : "Żaden sprzęt nie był wąskim gardłem."] : "Firma nie ma jeszcze sprzętu, który pracował w tej rundzie.", top && top.oblozenie >= 0.95 ? "uwaga" : "");
    return lead + zwinTabela("Obłożenie sprzętu (Twoja firma)", ["Stanowisko", "Sprzęt", "Jakość", "Obłożenie"], own, { klasy: ["l", "l"], otwarte: true })
      + zwinTabela("Liczba i jakość sprzętów", ["Firma", "Niska ★", "Średnia ★★", "Wysoka ★★★", "Razem"], ile, { klasy: ["l"] })
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
    + `<p><b>Przychody ze sprzedaży: ${zl(przychod)}</b></p>`
    + `<p class="podpowiedz">Sprzęt kupiony od progu amortyzacji to środek trwały: przy sprzedaży jego niezamortyzowana wartość idzie w koszty (Księgowość ▸ KPiR).</p>`, { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">OK</button>` });
}

export const wyposazenie = {
  tytul: "Wyposażenie", tytulPelny: "Inwestycje - wyposażenie", ikona: "☕", odblokowanie: "inwestycje_wyposazenie",
  info: "Kup dodatkowe wyposażenie dla klientów Twojej firmy. Wyposażenie podnosi zadowolenie klientów i przyciąga ich do lokalu.",
  decyzje(c) { return kafleUdogodnien(c, "wyposazenie", "klientów"); },
  wyniki({ v }) {
    const w = Object.entries(v.rynek?.wyposazenie || {}).map(([f, n]) => [esc(nazwaFirmy(v, f)), licz(n)]);
    const moje = v.rynek?.wyposazenie?.[v.firma];
    return podsumowanie(moje != null ? `Firma ma ${licz(moje)} ${moje === 1 ? "pozycję" : moje >= 2 && moje <= 4 ? "pozycje" : "pozycji"} wyposażenia dla klientów.` : "Poniżej porównanie wyposażenia firm.")
      + zwinTabela("Posiadane wyposażenie", ["Firma", "Liczba pozycji wyposażenia"], w, { klasy: ["l"], otwarte: true });
  },
  akcje: { "kup-udog": (el, c) => przelaczUdog(el, c), "sprzedaj-udog": (el, c) => przelaczUdog(el, c) },
};

export const RODZAJ_ST = { lokal: "lokal", budynek: "budynek", grunt: "grunt (bez amortyzacji)", sprzet: "sprzęt", wyposazenie: "wyposażenie" };

// UF12: ewidencja środków trwałych jest w Księgowość ▸ KPiR (zakładka Środki trwałe usunięta)
export function ewidencja(lista, tytul) {
  const w = (lista || []).map((s) => [esc(s.nazwa), esc(RODZAJ_ST[s.rodzaj] || s.rodzaj), licz(s.od_rundy), proc(s.stawka),
    zl(s.wartosc), zl(s.umorzenie), zl(s.netto)]);
  const suma = (k) => (lista || []).reduce((a, s) => a + s[k], 0);
  if (w.length) w.push(["<b>Razem</b>", "", "", "", `<b>${zl(suma("wartosc"))}</b>`, `<b>${zl(suma("umorzenie"))}</b>`, `<b>${zl(suma("netto"))}</b>`]);
  return tabela(tytul, ["Środek trwały", "Rodzaj", "Od rundy", "Stawka roczna", "Wartość początkowa", "Umorzenie", "Wartość netto"],
    w.length ? w : [["Brak środków trwałych – wynajęty lokal i tańsze zakupy idą od razu w koszty.", "", "", "", "", "", ""]], { klasy: ["l", "l"] });
}

export function kafleUdogodnien({ v, kat, edycja }, rodzaj, kogo) {
  const pozycje = kat.oferty[rodzaj].pozycje.filter((p) => p.od_rundy <= v.runda);
  // Z3: przy kilku lokalach – wyposażenie / udogodnienia wybranego lokalu
  const id = idWybranego(v), przed = listaLokalu(v.stan_przed, rodzaj, id), teraz = listaLokalu(v.stan, rodzaj, id);
  const kupno = pozycje.filter((p) => teraz.includes(p.nazwa) && !przed.includes(p.nazwa)).reduce((s, p) => s + p.cena, 0);
  const utrz = pozycje.filter((p) => teraz.includes(p.nazwa)).reduce((s, p) => s + p.utrzymanie, 0);
  const sprzedaz = pozycje.filter((p) => przed.includes(p.nazwa) && !teraz.includes(p.nazwa)).reduce((s, p) => s + p.cena / 2, 0);
  return `${id ? `<div class="komunikat ok">${rodzaj === "wyposazenie" ? "Wyposażenie" : "Udogodnienia"} lokalu <b>${esc(nazwaLokalu(v, id))}</b>.</div>` : ""}
    <div class="pasek ciemny"><span>Koszt zakupu: <span class="kwota">${zl(kupno)}</span></span>
    <span>Koszt utrzymania: <span class="kwota">${zl(naRunde(utrz))}</span>${naOkres()}</span><span>Przychody ze sprzedaży: <span class="kwota">${zl(sprzedaz)}</span></span></div>
    <div class="siatka trojka" style="margin-top:20px">${pozycje.map((p) => {
      const mial = przed.includes(p.nazwa), ma = teraz.includes(p.nazwa);
      const przycisk = mial
        ? `<button class="btn ${ma ? "pom" : "zielony"}" data-akcja="sprzedaj-udog" data-r="${rodzaj}" data-nazwa="${esc(p.nazwa)}" ${edycja ? "" : "disabled"}>${ma ? "Sprzedaj" : "✓ Sprzedane"}</button>`
        : `<button class="btn ${ma ? "zielony" : "czarny"}" data-akcja="kup-udog" data-r="${rodzaj}" data-nazwa="${esc(p.nazwa)}" ${edycja ? "" : "disabled"}>${ma ? "✓ Wybrano" : "Wybierz"}</button>`;
      return `<div class="kafel ${ma ? "wybrany" : ""}"><div class="kg">${esc(p.nazwa)}<span class="pigulka inf" title="% ${kogo} oczekujących">${p.procent}%</span></div>
        <div class="kt">${p.opis ? `<p class="podpowiedz" style="margin:0 0 8px">${esc(p.opis)}</p>` : ""}${p.sklep ? `<div class="wiersz"><span>Sklep</span><span>${esc(p.sklep)}</span></div>` : ""}<div class="wiersz"><span>${mial ? "Cena sprzedaży" : "Cena zakupu"}</span><span>${zl(mial ? p.cena / 2 : p.cena)}</span></div>
        <div class="wiersz"><span>Koszt utrzymania</span><span>${zl(naRunde(p.utrzymanie))}${naOkres()}</span></div>
        <div class="wiersz"><span>% ${kogo} oczekujących</span><span>${p.procent}%</span></div></div><div class="kd">${przycisk}</div></div>`;
    }).join("")}</div>`;
}

export async function przelaczUdog(el, c) {
  const r = el.dataset.r, n = el.dataset.nazwa;
  const id = idWybranego(c.v), mial = listaLokalu(c.v.stan_przed, r, id).includes(n);
  await c.zmien((d) => {
    const k = mial ? `${r}_sprzedaj` : `${r}_kup`;
    const cel = id ? ((d.w_lokalu = d.w_lokalu || {})[id] = d.w_lokalu[id] || {}) : d;
    const l = cel[k] || [];
    cel[k] = l.includes(n) ? l.filter((x) => x !== n) : [...l, n];
  });
}

export { zamknijOkno, wykres };
