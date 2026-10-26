// Bank w grze z lokalami (silnik/banki.py, dane/mapa/banki.yaml): sześć banków, konto firmowe z terminalem
// i limitem, lokaty, kredyty (na start, inwestycyjny pod zastaw, obrotowy) i leasing sprzętu w dowolnym banku.
import { esc, OKRES, okno, proc, tabela, toast, zamknijOkno, zl, zl2 } from "./wspolne.js";

const PRODUKTY = { start: "na start", inwestycyjny: "inwestycyjny", obrotowy: "obrotowy" };
const KATEGORIE = { konto: "Najtańsze konto i terminal", lokata: "Najlepsza lokata", kredyt_bez_historii: "Kredyt bez historii firmy",
  kredyt_inwestycyjny: "Najtańszy kredyt pod zastaw", leasing: "Najtańszy leasing", limit: "Największy limit w koncie" };
const rundy = (n) => `${n} ${n === 1 ? "runda" : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? "rundy" : "rund"}`;
const tak = (b) => b ? `<span class="plus">✓</span>` : `<span class="minus">✗</span>`;

let podzakladka = "historia", wyborBanku = false;

const ustawienia = (kat) => kat.mapa.banki;
const bankiLista = (kat) => ustawienia(kat).banki;
const najlepszyW = (v, nazwa) => Object.entries(v.banki.najlepsze).filter(([, b]) => b === nazwa).map(([k]) => KATEGORIE[k]);
const najLokata = (b) => Math.max(...Object.values(b.lokaty));
const oferty = (kat) => bankiLista(kat).flatMap((b) => b.kredyty.map((p) => ({ ...p, bank: b.nazwa })));

function kafel(v, b, wybrany, edycja) {
  const naj = najlepszyW(v, b.nazwa);
  return `<div class="kafel ${b.nazwa === wybrany ? "wybrany" : ""}"><div class="kg">${esc(b.nazwa)}
      <span class="pigulka inf">${esc(b.specjalizacja)}</span></div><div class="kt">
      <p class="podpowiedz">${esc(b.opis)}</p>
      <div class="wiersz"><span>Konto firmowe</span><span>${zl(b.konto)} / mies.</span></div>
      <div class="wiersz"><span>Terminal</span><span>${zl(b.terminal.abonament)} / mies. + ${proc(b.terminal.prowizja, 2)} od kart</span></div>
      <div class="wiersz"><span>Lokata (najlepsza)</span><span>${proc(najLokata(b), 1)}</span></div>
      <div class="wiersz"><span>Limit w koncie</span><span>${zl(b.limit.kwota)} · ${proc(b.limit.oprocentowanie, 1)}</span></div>
      ${b.kredyty.map((p) => `<div class="wiersz"><span>${esc(p.nazwa)}</span><span>${proc(p.oprocentowanie, 1)}</span></div>`).join("")}
      ${b.leasing ? `<div class="wiersz"><span>Leasing sprzętu</span><span>${proc(b.leasing.oprocentowanie, 1)}</span></div>` : ""}
      ${naj.length ? `<p><b>Najlepszy:</b> ${naj.map(esc).join(", ")}</p>` : ""}</div>
      <div class="kd">${b.nazwa === wybrany ? `<button class="btn zielony">✓ Konto firmowe</button>`
        : `<button class="btn czarny" data-akcja="bk-konto" data-b="${esc(b.nazwa)}" ${edycja ? "" : "disabled"}>Otwórz konto firmowe</button>`}</div></div>`;
}

function porownanie(v, kat) {
  const naj = v.banki.najlepsze;
  const kom = (kategoria, b, tekst) => naj[kategoria] === b.nazwa ? `<b class="akcent">${tekst}</b>` : tekst;
  return tabela("Porównanie ofert", ["Bank", "Konto + terminal / mies.", "Prowizja od kart", "Lokaty", "Kredyt bez historii", "Kredyt pod zastaw", "Leasing", "Limit w koncie"],
    bankiLista(kat).map((b) => {
      const bezHist = b.kredyty.find((p) => !p.historia), zastaw = b.kredyty.find((p) => p.zastaw);
      return [esc(b.nazwa), kom("konto", b, zl(b.konto + b.terminal.abonament)), proc(b.terminal.prowizja, 2),
        kom("lokata", b, Object.entries(b.lokaty).map(([r, o]) => `${r} r.: ${proc(o, 1)}`).join(" · ")),
        bezHist ? kom("kredyt_bez_historii", b, proc(bezHist.oprocentowanie, 1)) : "–",
        zastaw ? kom("kredyt_inwestycyjny", b, `${proc(zastaw.oprocentowanie, 1)} (do ${proc(zastaw.zastaw, 0)} wartości)`) : "–",
        b.leasing ? kom("leasing", b, proc(b.leasing.oprocentowanie, 1)) : "–",
        kom("limit", b, `${zl(b.limit.kwota)} · ${proc(b.limit.oprocentowanie, 1)}`)];
    }), { klasy: ["l"] })
    + `<p class="podpowiedz">Konto firmowe może być w jednym banku, a lokaty, kredyty i leasing – w dowolnych. Oprocentowanie roczne,
      w ${OKRES.miejscownik} naliczana część: 1/${OKRES.rund_w_roku}. Pogrubione – najlepsza oferta w kategorii.</p>`;
}

function lokaty(v, kat, edycja) {
  const zerw = v.decyzje.lokaty_zerwij || [];
  const nowe = v.decyzje.lokaty_zaloz || [];
  return tabela("Lokaty", ["Nazwa", "Bank", "Założona", "Okres", "Oprocentowanie", "Kwota", ""], v.stan_przed.lokaty.map((l) => [`Lokata nr ${l.id}`, esc(l.bank),
    `runda ${l.od_rundy}`, rundy(l.miesiecy), proc(l.oprocentowanie, 1), zl2(l.kwota),
    `<button class="btn ${zerw.includes(l.id) ? "zielony" : "czarny"} maly" data-akcja="bk-zerwij" data-id="${l.id}" ${edycja ? "" : "disabled"}>${zerw.includes(l.id) ? "✓ Zerwana" : "Zerwij"}</button>`]), { klasy: ["l", "l"] })
    + (nowe.length ? `<p>Nowe lokaty: ${nowe.map((l, i) => `${zl(l.kwota)} w ${esc(l.bank)} na ${rundy(l.rund)} <a href="#" data-akcja="bk-usun" data-co="lokaty_zaloz" data-i="${i}">usuń</a>`).join(", ")}</p>` : "")
    + `<p><button class="btn zielony" data-akcja="bk-nowa-lokata" ${edycja ? "" : "disabled"}>Załóż lokatę</button>
      <span class="podpowiedz">Odsetki wypłacane na koniec okresu. Zerwanie – zwrot kwoty bez odsetek.</span></p>`;
}

function kredyty(v, kat, edycja) {
  const u = ustawienia(kat);
  const spl = v.decyzje.kredyty_splac || [];
  const nowe = v.decyzje.kredyty_wez || [];
  const zastawy = Object.fromEntries(v.banki.zastawy.map((z) => [z.id, z.nazwa]));
  return tabela("Kredyty", ["Nazwa", "Bank", "Rodzaj", "Od rundy", "Kwota", "Okres", "Rata kapitałowa", "Do spłaty", "Zaległe", "Zastaw", ""],
    v.stan_przed.kredyty.map((k) => [`Kredyt nr ${k.id}`, esc(k.bank), PRODUKTY[k.produkt] || "–", k.od_rundy, zl2(k.kwota), rundy(k.miesiecy),
      zl2(k.kwota / k.miesiecy), zl2(k.pozostalo), k.zalegle ? `<span class="minus">${rundy(k.zalegle)} (${zl2(k.zaleglosc)})</span>` : "–",
      k.zastaw ? esc(zastawy[k.zastaw] || k.zastaw.split(":").slice(1).join(" ")) : "–",
      `<button class="btn ${spl.includes(k.id) ? "zielony" : "czarny"} maly" data-akcja="bk-splac" data-id="${k.id}" ${edycja ? "" : "disabled"}>${spl.includes(k.id) ? "✓ Spłacony" : "Spłać"}</button>`]),
    { klasy: ["l", "l", "l"] })
    + (nowe.length ? `<p>Nowe kredyty: ${nowe.map((k, i) => `${esc(k.bank)} – ${PRODUKTY[k.produkt]} ${zl(k.kwota)} na ${rundy(k.rund)} <a href="#" data-akcja="bk-usun" data-co="kredyty_wez" data-i="${i}">usuń</a>`).join(", ")}</p>` : "")
    + `<p><button class="btn zielony" data-akcja="bk-nowy-kredyt" ${edycja ? "" : "disabled"}>Weź kredyt</button>
      <span class="podpowiedz">Historia firmy: ${rundy(v.banki.historia)} (kredyty poza startowym wymagają co najmniej ${rundy(u.historia_rund)}).
      Raty kapitałowe równe + odsetki, od następnej rundy; prowizja od razu w koszty. Brak środków na ratę – odsetki karne
      ${proc(u.stopa_karna, 0)}, a gdy zaległość trwa ${rundy(u.przejecie_po)}, bank przejmuje zastaw (wycena ${proc(u.wycena_zastawu, 0)} wartości netto).</span></p>`;
}

function leasing(v, kat, edycja) {
  const nowe = v.decyzje.leasing_wez || [];
  return tabela("Sprzęt w leasingu", ["Nazwa", "Bank", "Sprzęt", "Stanowisko", "Rata", "Pozostało rat", "Wykup", "Zaległe"],
    (v.stan_przed.leasingi || []).map((l) => [`Leasing nr ${l.id}`, esc(l.bank), `${esc(l.nazwa)} (jakość ${l.jakosc})`, `${l.typ} ${l.nr}`,
      zl2(l.rata), l.pozostalo_rat, zl2(l.wykup), l.zalegle ? `<span class="minus">${rundy(l.zalegle)}</span>` : "–"]), { klasy: ["l", "l", "l", "l"] })
    + (nowe.length ? `<p>Nowy leasing: ${nowe.map((l, i) => `${esc(l.nazwa)} (${l.typ} ${l.nr}) w ${esc(l.bank)} na ${rundy(l.rund)} <a href="#" data-akcja="bk-usun" data-co="leasing_wez" data-i="${i}">usuń</a>`).join(", ")}</p>` : "")
    + `<p><button class="btn zielony" data-akcja="bk-nowy-leasing" ${edycja ? "" : "disabled"}>Weź sprzęt w leasing</button>
      <span class="podpowiedz">Sprzęt od razu na stanowisku, ale do wykupu należy do banku – nie można go sprzedać. Wpłata własna
      i raty idą w koszty (bez amortyzacji), po ostatniej racie wykup za symboliczną kwotę.</span></p>`;
}

function limit(v, kat, b) {
  const u = ustawienia(kat);
  return tabela("Limit w koncie", ["", "Kwota"], [["Limit", zl2(b.limit.kwota)], ["Wykorzystany", zl2(v.stan_przed.kredyt_odnawialny)],
    ["Wolny", zl2(v.banki.wolny_limit)], ["Oprocentowanie limitu", proc(b.limit.oprocentowanie, 1)], ["Debet ponad limit – odsetki karne", proc(u.stopa_karna, 0)]], { klasy: ["l", "r"] })
    + `<p class="podpowiedz">Limit uruchamia się sam, gdy na koniec ${OKRES.dopelniacz} zabraknie gotówki, i jest spłacany z nadwyżki.
      Wolny limit liczy się też przy ratach kredytów i leasingu.</p>`;
}

export function decyzjeBanku({ v, kat, edycja }) {
  const wybrany = v.stan.bank;
  const b = bankiLista(kat).find((x) => x.nazwa === wybrany);
  if (!b || wyborBanku) {
    return `${b ? `<button class="btn pom" data-akcja="bk-powrot">Powrót do banku</button>` : `<div class="komunikat">Wybierz bank, w którym firma otworzy konto firmowe. Kredyty, lokaty i leasing można potem brać w dowolnym banku.</div>`}
      <div class="siatka trojka" style="margin-top:16px">${bankiLista(kat).map((x) => kafel(v, x, wybrany, edycja)).join("")}</div>`;
  }
  const zak = { historia: "Historia rachunku", porownanie: "Porównanie banków", lokaty: "Lokaty", kredyty: "Kredyty", leasing: "Leasing", limit: "Limit w koncie" };
  let html = `<div class="kafel"><div class="kt" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;align-items:center">
    <div><h3 style="margin:0 0 6px">Konto firmowe: ${esc(b.nazwa)}</h3>Dostępne saldo: <b class="akcent">${zl2(v.stan.gotowka)}</b>
      <span class="podpowiedz">(po decyzjach tej rundy, przed sprzedażą)</span><br>Wolny limit: ${zl2(v.banki.wolny_limit)} · historia firmy: ${rundy(v.banki.historia)}</div>
    <button class="btn pom" data-akcja="bk-zmien" ${edycja ? "" : "disabled"}>Zmień bank konta</button></div></div>
    <div class="przelacznik" style="justify-content:flex-end;margin:16px 0;flex-wrap:wrap">${Object.entries(zak).map(([k, n]) => `<a class="${podzakladka === k ? "aktywny" : ""}" data-akcja="bk-zak" data-k="${k}">${n}</a>`).join("")}</div>`;
  if (podzakladka === "historia") {
    const op = v.wyniki?.rachunek || [];
    html += tabela(null, ["Operacja", "Kwota", "Saldo"], op.map((o) => [esc(o.opis), `<span class="${o.kwota < 0 ? "minus" : "plus"}">${zl2(o.kwota)}</span>`, zl2(o.saldo)]), { klasy: ["l", "r", "r"] })
      + `<p class="podpowiedz">Historia rachunku z poprzedniego ${OKRES.dopelniacz}.</p>`;
  } else if (podzakladka === "porownanie") html += porownanie(v, kat);
  else if (podzakladka === "lokaty") html += lokaty(v, kat, edycja);
  else if (podzakladka === "kredyty") html += kredyty(v, kat, edycja);
  else if (podzakladka === "leasing") html += leasing(v, kat, edycja);
  else html += limit(v, kat, b);
  return html;
}

export function wynikiBanku({ v }) {
  const w = v.wyniki?.bank;
  if (!w) return `<p class="podpowiedz">Brak wyników banku z poprzedniego ${OKRES.dopelniacz}.</p>`;
  const k = w.koniec || {}, o = k.oplaty || {};
  const odrzucone = [...(w.poczatek?.odrzucone || []), ...(w.leasing?.odrzucone || [])];
  let html = tabela("Opłaty konta firmowego", ["", "Kwota"], [["Konto", zl2(o.konto)], ["Abonament terminala", zl2(o.terminal)],
    ["Prowizja od płatności kartą", zl2(o.prowizja)]], { klasy: ["l", "r"], stopka: ["Razem", zl2((o.konto || 0) + (o.terminal || 0) + (o.prowizja || 0))] });
  if ((k.raty || []).length) {
    html += tabela("Raty kredytów", ["Kredyt", "Bank", "Odsetki", "Rata kapitałowa", "Zaległość", "Zapłacona"],
      k.raty.map((r) => [`nr ${r.kredyt}`, esc(r.bank), zl2(r.odsetki), zl2(r.rata), zl2(r.zaleglosc), tak(r.zaplacona)]), { klasy: ["l", "l"] });
  }
  if ((k.leasing || []).length) {
    html += tabela("Raty leasingu", ["Leasing", "Bank", "Sprzęt", "Rata", "Rat", "Zapłacona"],
      k.leasing.map((r) => [`nr ${r.leasing}`, esc(r.bank), esc(r.sprzet), zl2(r.rata), r.rat, tak(r.zaplacona)]), { klasy: ["l", "l", "l"] });
  }
  if ((k.lokaty || []).length) {
    html += tabela("Zakończone lokaty", ["Lokata", "Bank", "Kwota", "Odsetki"], k.lokaty.map((l) => [`nr ${l.lokata}`, esc(l.bank), zl2(l.kwota), zl2(l.odsetki)]), { klasy: ["l", "l"] });
  }
  if ((k.przejecia || []).length) {
    html += tabela("Przejęcia przez bank", ["Bank", "Co", "Wycena", "Dług", "Nadwyżka na konto"],
      k.przejecia.map((p) => [esc(p.bank), esc(p.zastaw), zl2(p.wycena), zl2(p.dlug), zl2(p.nadwyzka)]), { klasy: ["l", "l"] });
  }
  if ((k.wykupy || []).length) html += `<p>Wykupiony z leasingu: ${k.wykupy.map((x) => esc(x.sprzet)).join(", ")}.</p>`;
  const nowe = [...(w.poczatek?.nowe_kredyty || []).map((id) => `kredyt nr ${id}`), ...(w.poczatek?.nowe_lokaty || []).map((id) => `lokata nr ${id}`),
    ...(w.leasing?.nowe || []).map((id) => `leasing nr ${id}`)];
  if (nowe.length) html += `<p>Nowe produkty: ${nowe.join(", ")}.</p>`;
  if (odrzucone.length) html += tabela("Odrzucone przez bank", ["Decyzja", "Powód"], odrzucone.map((x) => [esc(x.co), esc(x.powod)]), { klasy: ["l", "l"] });
  const uwagi = [...(k.zaleglosci || []), ...(w.debet_ponad_limit > 0 ? [`Debet ponad limit w koncie: ${zl2(w.debet_ponad_limit)} – odsetki karne.`] : [])];
  if (uwagi.length) html += `<div class="komunikat">${uwagi.map(esc).join("<br>")}</div>`;
  return html + `<p class="podpowiedz">Historia firmy na koniec ${OKRES.dopelniacz}: ${rundy(w.historia)}.</p>`;
}

const pole = (id, etykieta, html) => `<label class="pole">${etykieta}${html.replace("<select", `<select id="${id}"`).replace("<input", `<input id="${id}"`)}</label>`;
const wartosc = (id) => document.getElementById(id)?.value;
const przyciski = (akcja, tekst) => `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="${akcja}">${tekst}</button>`;

export const akcjeBanku = {
  "bk-konto": (el, c) => { wyborBanku = false; return c.zmien((d) => { d.bank = el.dataset.b; }); },
  "bk-zmien": (el, c) => { wyborBanku = true; c.idz("bank", "decyzje"); },
  "bk-powrot": (el, c) => { wyborBanku = false; c.idz("bank", "decyzje"); },
  "bk-zak": (el, c) => { podzakladka = el.dataset.k; c.idz("bank", "decyzje"); },
  "bk-zerwij": (el, c) => c.zmien((d) => { const id = +el.dataset.id, l = d.lokaty_zerwij || []; d.lokaty_zerwij = l.includes(id) ? l.filter((x) => x !== id) : [...l, id]; }),
  "bk-splac": (el, c) => c.zmien((d) => { const id = +el.dataset.id, l = d.kredyty_splac || []; d.kredyty_splac = l.includes(id) ? l.filter((x) => x !== id) : [...l, id]; }),
  "bk-usun": (el, c, e) => { e.preventDefault(); return c.zmien((d) => { d[el.dataset.co].splice(+el.dataset.i, 1); }); },
  "bk-nowa-lokata": (el, c) => {
    const opcje = bankiLista(c.kat).flatMap((b) => Object.entries(b.lokaty).map(([r, o]) => `<option value="${esc(b.nazwa)}|${r}">${esc(b.nazwa)} – ${rundy(+r)} – ${proc(o, 1)}</option>`));
    okno("Zakładanie lokaty", `<div class="dwie">${pole("bk-l-oferta", "Bank i okres", `<select>${opcje.join("")}</select>`)}
      ${pole("bk-l-kwota", "Kwota", `<input type="number" min="1" step="100" value="${Math.max(0, Math.floor(c.v.stan.gotowka))}">`)}</div>
      <p class="podpowiedz">Dostępne saldo: ${zl2(c.v.stan.gotowka)}. Pieniądze na lokacie nie są dostępne na bieżące wydatki.</p>`,
    { male: true, przyciski: przyciski("bk-zaloz", "Załóż") });
  },
  "bk-zaloz": async (el, c) => {
    const [bank, r] = wartosc("bk-l-oferta").split("|"), kwota = +wartosc("bk-l-kwota");
    if (!(kwota > 0)) return toast("Podaj kwotę.");
    zamknijOkno();
    await c.zmien((d) => { d.lokaty_zaloz = [...(d.lokaty_zaloz || []), { bank, kwota, rund: +r }]; });
  },
  "bk-nowy-kredyt": (el, c) => {
    const lista = oferty(c.kat);
    const opcje = lista.map((p, i) => `<option value="${i}">${esc(p.bank)} – ${esc(p.nazwa)} – ${proc(p.oprocentowanie, 1)}, prowizja ${proc(p.prowizja, 1)}, do ${zl(p.maks_kwota)} / ${rundy(p.maks_rund)}${p.historia ? " (wymaga historii)" : ""}${p.zastaw ? " (pod zastaw)" : ""}</option>`);
    const zastawy = c.v.banki.zastawy.map((z) => `<option value="${esc(z.id)}">${esc(z.nazwa)} – wartość ${zl(z.wartosc)}</option>`);
    okno("Kredyt", `${pole("bk-k-oferta", "Oferta", `<select>${opcje.join("")}</select>`)}
      <div class="dwie">${pole("bk-k-kwota", "Kwota", `<input type="number" min="100" step="1000" value="10000">`)}
      ${pole("bk-k-rund", `Okres (${OKRES.mnoga})`, `<input type="number" min="1" value="26">`)}</div>
      ${pole("bk-k-zastaw", "Zastaw (kredyt inwestycyjny)", `<select><option value="">– bez zastawu –</option>${zastawy.join("")}</select>`)}
      <p class="podpowiedz">Pod zastaw można dać kupiony lokal albo kupiony sprzęt (wartość netto po amortyzacji).</p>`,
    { male: true, przyciski: przyciski("bk-wez-kredyt", "Weź kredyt") });
  },
  "bk-wez-kredyt": async (el, c) => {
    const p = oferty(c.kat)[+wartosc("bk-k-oferta")], kwota = +wartosc("bk-k-kwota"), rund = +wartosc("bk-k-rund");
    if (!(kwota > 0) || !(rund > 0)) return toast("Podaj kwotę i okres.");
    if (p.zastaw && !wartosc("bk-k-zastaw")) return toast("Kredyt inwestycyjny wymaga zastawu.");
    zamknijOkno();
    await c.zmien((d) => {
      d.kredyty_wez = [...(d.kredyty_wez || []), { bank: p.bank, produkt: p.produkt, kwota, rund, ...(p.zastaw ? { zastaw: wartosc("bk-k-zastaw") } : {}) }];
    });
  },
  "bk-nowy-leasing": (el, c) => {
    const banki = bankiLista(c.kat).filter((b) => b.leasing);
    const opcje = banki.flatMap((b) => b.leasing.rund.map((r) => `<option value="${esc(b.nazwa)}|${r}">${esc(b.nazwa)} – ${rundy(r)} – ${proc(b.leasing.oprocentowanie, 1)}, wpłata ${proc(b.leasing.wplata, 0)}, wykup ${proc(b.leasing.wykup, 0)}</option>`));
    const stan = c.v.stan.stanowiska.map((s) => `<option value="${s.typ}|${s.nr}">${s.typ} ${s.nr}</option>`);
    const sprzet = Object.entries(c.kat.sprzet).map(([n, s]) => `<option value="${esc(n)}">${esc(n)} (${s.dla})</option>`);
    okno("Leasing sprzętu", `${pole("bk-s-oferta", "Bank i okres", `<select>${opcje.join("")}</select>`)}
      <div class="dwie">${pole("bk-s-stan", "Stanowisko", `<select>${stan.join("")}</select>`)}
      ${pole("bk-s-sprzet", "Sprzęt", `<select>${sprzet.join("")}</select>`)}</div>
      ${pole("bk-s-jakosc", "Jakość", `<select><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option></select>`)}`,
    { male: true, przyciski: przyciski("bk-wez-leasing", "Weź w leasing") });
  },
  "bk-wez-leasing": async (el, c) => {
    const [bank, r] = wartosc("bk-s-oferta").split("|"), [typ, nr] = (wartosc("bk-s-stan") || "|").split("|");
    if (!typ) return toast("Najpierw potrzebne jest stanowisko.");
    zamknijOkno();
    await c.zmien((d) => { d.leasing_wez = [...(d.leasing_wez || []), { bank, typ, nr: +nr, nazwa: wartosc("bk-s-sprzet"), jakosc: +wartosc("bk-s-jakosc"), rund: +r }]; });
  },
};
