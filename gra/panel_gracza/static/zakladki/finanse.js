// Finanse: raport finansowy, KPiR, bank, biuro rachunkowe.
import { esc, okno, proc, tabela, toast, wykres, zamknijOkno, zl, zl2 } from "./wspolne.js";

const GRUPY = [
  ["Zakup składników", (p) => p.towary],
  ["Wynagrodzenia", (p) => p.wynagrodzenia],
  ["Składki ZUS pracodawcy", (p) => p.opis.startsWith("Składki ZUS") ? p.pozostale : 0],
  ["Rekrutacja i odprawy", (p) => /^Koszt (zatrudnienia|odprawy)/.test(p.opis) ? p.pozostale : 0],
  ["Stanowiska", (p) => p.opis.startsWith("Uruchomienie stanowiska") ? p.pozostale : 0],
  ["Sprzęt (zakup)", (p) => p.opis.startsWith("Koszt zakupu: ") ? p.pozostale : 0],
  ["Udogodnienia i wyposażenie (zakup)", (p) => /^Koszt zakupu (udogodnień|wyposażenia)/.test(p.opis) ? p.pozostale : 0],
  ["Utrzymanie sprzętu, udogodnień i wyposażenia", (p) => /^Koszty utrzymania/.test(p.opis) ? p.pozostale : 0],
  ["Marketing", (p) => /reklam/i.test(p.opis) ? p.pozostale : 0],
  ["Szkolenia", (p) => p.opis.startsWith("Szkolenie") ? p.pozostale : 0],
  ["Utrzymanie lokalu i magazynu", (p) => /utrzymania lokalu|magazynowania/.test(p.opis) ? p.pozostale : 0],
  ["Bank (opłaty, odsetki)", (p) => /^(Opłata za konto|Odsetki)/.test(p.opis) ? p.pozostale : 0],
  ["Biuro rachunkowe", (p) => /biura rachunkowego|kadrowo/.test(p.opis) ? p.pozostale : 0],
];

function koszty(k) {
  const wynik = GRUPY.map(([n, f]) => [n, k.pozycje.reduce((s, p) => s + f(p), 0)]);
  const znane = wynik.reduce((s, [, x]) => s + x, 0);
  wynik.push(["Inne", k.koszty - znane]);
  return wynik.filter(([, x]) => Math.abs(x) > 0.004);
}

export const raport = {
  tytul: "Raport finansowy", tytulPelny: "Finanse - raport finansowy", ikona: "📊", odblokowanie: (v) => v.runda >= 2,
  info: "Podsumowanie wyników finansowych poprzedniego miesiąca i wszystkich dotychczasowych rund.",
  wyniki({ v }) {
    const k = v.wyniki.kpir;
    const przych = k.pozycje.filter((p) => p.przychod || p.przychod_pozostaly).map((p) => [esc(p.opis), zl2(p.przychod + p.przychod_pozostaly)]);
    const kos = koszty(k).map(([n, x]) => [n, zl2(x)]);
    const h = v.historia || [];
    const skum = h.reduce((s, x) => s + x.dochod_netto, 0);
    return `<div class="dwie">
      <div>${tabela("Przychody", ["Pozycja", "Kwota"], przych, { klasy: ["l", "r"], stopka: ["Razem", zl2(k.przychody)] })}</div>
      <div>${tabela("Koszty", ["Pozycja", "Kwota"], kos, { klasy: ["l", "r"], stopka: ["Razem", zl2(k.koszty)] })}</div></div>
      ${tabela("Wynik", ["", "Ostatni miesiąc", "Wszystkie rundy"], [
        ["Dochód do opodatkowania", zl2(k.dochod), ""], ["Podatek dochodowy", zl2(k.podatek), ""],
        ["<b>Dochód netto</b>", `<b>${zl2(k.dochod_netto)}</b>`, `<b>${zl2(skum)}</b>`],
        ["Saldo konta na koniec miesiąca", zl2(v.wyniki.gotowka), ""], ["Lokaty", zl2(v.wyniki.lokaty), ""],
        ["Zadłużenie (kredyty)", zl2(v.wyniki.zadluzenie), ""]], { klasy: ["l", "r", "r"] })}
      <div class="wykres"><canvas id="w-wynik"></canvas></div>`;
  },
  po({ v }) {
    const h = v.historia || [];
    wykres("w-wynik", "bar", h.map((x) => x.miesiac), [{ label: "Dochód netto", data: h.map((x) => x.dochod_netto) },
      { label: "Saldo konta", data: h.map((x) => x.gotowka), type: "line" }]);
  },
};

export const kpir = {
  tytul: "KPiR", tytulPelny: "KPiR – księga przychodów i rozchodów", ikona: "📒", odblokowanie: (v) => v.runda >= 2,
  info: ({ v }) => `Księga przychodów i rozchodów za ${v.runda >= 2 ? (v.historia?.[v.runda - 2]?.miesiac || "") : ""}.`,
  wyniki({ v }) {
    const k = v.wyniki.kpir;
    const w = k.pozycje.map((p, i) => [i + 1, esc(p.opis), zl2(p.przychod), zl2(p.przychod_pozostaly), zl2(p.przychod + p.przychod_pozostaly),
      zl2(p.towary), zl2(p.wynagrodzenia), zl2(p.pozostale), zl2(p.wynagrodzenia + p.pozostale)]);
    const s = (f) => k.pozycje.reduce((a, p) => a + f(p), 0);
    return tabela(null, ["Lp.", "Opis zdarzenia gospodarczego", "Wartość sprzedanych towarów i usług", "Pozostałe przychody", "Razem przychód",
      "Zakup towarów i materiałów", "Wynagrodzenia", "Pozostałe wydatki", "Razem wydatki"], w,
      { klasy: ["", "l", "r", "r", "r", "r", "r", "r", "r"], stopka: ["", "Suma", zl2(s((p) => p.przychod)), zl2(s((p) => p.przychod_pozostaly)),
        zl2(k.przychody), zl2(k.towary), zl2(k.wynagrodzenia), zl2(k.pozostale), zl2(k.wynagrodzenia + k.pozostale)] })
      + tabela(null, ["", "Kwota"], [["Dochód do opodatkowania", zl2(k.dochod)], ["Podatek", zl2(k.podatek)], ["Dochód netto", zl2(k.dochod_netto)]], { klasy: ["l", "r"] });
  },
};

let zakladkaBanku = "historia", wyborBanku = false;
export const bank = {
  tytul: "Bank", tytulPelny: "Finanse - bank", ikona: "🏦", odblokowanie: "finanse_bank",
  info: "Wybierz bank, w którym Twoja firma będzie prowadzić konto firmowe. Zarządzaj lokatami i kredytami.",
  decyzje({ v, kat, edycja }) {
    const banki = kat.oferty.banki.pozycje;
    const wybrany = v.stan.bank;
    const dostepny = (b) => (b.od_rundy || 1) <= v.runda;
    const karta = (b) => `<div class="kafel ${b.nazwa === wybrany ? "wybrany" : ""} ${dostepny(b) ? "" : "niedostepny"}"><div class="kg">${esc(b.nazwa)}
      ${dostepny(b) ? "" : `<span class="pigulka inf">od rundy ${b.od_rundy}</span>`}</div><div class="kt">
      <div class="wiersz"><span>Opłata za konto</span><span>${zl(b.konto)}</span></div><div class="wiersz"><span>Opłata za kartę</span><span>${zl(b.karta)}</span></div>
      <div class="wiersz"><span>Oprocentowanie lokaty</span><span>${proc(b.lokata, 0)}</span></div>
      <div class="wiersz"><span>Oprocentowanie kredytu odnawialnego</span><span>${proc(b.kredyt_odnawialny, 0)}</span></div>
      <div class="wiersz"><span>Oprocentowanie kredytu</span><span>${proc(b.kredyt, 0)}</span></div></div>
      <div class="kd">${b.nazwa === wybrany ? `<button class="btn zielony">✓ Wybrano</button>` : `<button class="btn czarny" data-akcja="bank" data-b="${esc(b.nazwa)}" ${edycja && dostepny(b) ? "" : "disabled"}>${dostepny(b) ? "Wybierz" : `Dostępny od rundy ${b.od_rundy}`}</button>`}</div></div>`;
    if (!wybrany || wyborBanku) return `${wybrany ? `<button class="btn pom" data-akcja="bank-powrot">Powrót do banku</button>` : ""}<div class="siatka trojka" style="margin-top:16px">${banki.map(karta).join("")}</div>`;
    const b = banki.find((x) => x.nazwa === wybrany);
    const zak = { historia: "Historia rachunku", lokaty: "Lokaty", kredyt: "Kredyt", odnawialny: "Kredyt odnawialny" };
    let html = `<div class="kafel"><div class="kt" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;align-items:center">
      <div><h3 style="margin:0 0 6px">${esc(b.nazwa)}</h3>Waluta: PLN<br>Dostępne saldo: <b class="akcent">${zl2(v.stan.gotowka)}</b>
        <span class="podpowiedz">(po decyzjach tej rundy, przed sprzedażą)</span></div>
      <button class="btn pom" data-akcja="zmien-bank" ${edycja ? "" : "disabled"}>Zmień bank</button></div></div>
      <div class="przelacznik" style="justify-content:flex-end;margin:16px 0">${Object.entries(zak).map(([k, n]) => `<a class="${zakladkaBanku === k ? "aktywny" : ""}" data-akcja="bank-zak" data-k="${k}">${n}</a>`).join("")}</div>`;
    if (zakladkaBanku === "historia") {
      const op = v.wyniki?.rachunek || [];
      html += tabela(null, ["Operacja", "Kwota", "Saldo"], op.map((o) => [esc(o.opis), `<span class="${o.kwota < 0 ? "minus" : "plus"}">${zl2(o.kwota)}</span>`, zl2(o.saldo)]), { klasy: ["l", "r", "r"] })
        + `<p class="podpowiedz">Historia rachunku z poprzedniego miesiąca.</p>`;
    } else if (zakladkaBanku === "lokaty") {
      const doKonca = v.gra.liczba_rund - v.runda;
      const zerw = v.decyzje.lokaty_zerwij || [];
      html += tabela(null, ["Nazwa", "Miesiąc założenia", "Okres", "Oprocentowanie", "Kwota", ""], v.stan_przed.lokaty.map((l) => [`Lokata nr ${l.id}`, `runda ${l.od_rundy}`,
        `${l.miesiecy} mies.`, proc(l.oprocentowanie, 2), zl2(l.kwota), `<button class="btn ${zerw.includes(l.id) ? "zielony" : "czarny"} maly" data-akcja="zerwij" data-id="${l.id}" ${edycja ? "" : "disabled"}>${zerw.includes(l.id) ? "✓ Zerwana" : "Zerwij"}</button>`]), { klasy: ["l"] })
        + ((v.decyzje.lokaty_zaloz || []).length ? `<p>Nowe lokaty w tej rundzie: ${(v.decyzje.lokaty_zaloz || []).map((l, i) => `${zl(l.kwota)} na ${l.miesiecy} mies. <a href="#" data-akcja="usun-lokate" data-i="${i}">usuń</a>`).join(", ")}</p>` : "")
        + (doKonca >= 1 ? `<p><button class="btn zielony" data-akcja="nowa-lokata" data-max="${doKonca}" ${edycja ? "" : "disabled"}>Załóż lokatę</button>
          <span class="podpowiedz">Odsetki ${proc(b.lokata, 0)} rocznie, wypłacane na koniec okresu (najpóźniej w ostatniej rundzie). Zerwanie = utrata odsetek.</span></p>` : "");
    } else if (zakladkaBanku === "kredyt") {
      const spl = v.decyzje.kredyty_splac || [];
      html += tabela(null, ["Nazwa", "Miesiąc zaciągnięcia", "Kwota", "Okres", "Rata kapitałowa", "Do spłaty", ""], v.stan_przed.kredyty.map((k) => [`Kredyt nr ${k.id}`,
        `runda ${k.od_rundy}`, zl2(k.kwota), `${k.miesiecy} mies.`, zl2(k.kwota / k.miesiecy), zl2(k.pozostalo),
        `<button class="btn ${spl.includes(k.id) ? "zielony" : "czarny"} maly" data-akcja="splac" data-id="${k.id}" ${edycja ? "" : "disabled"}>${spl.includes(k.id) ? "✓ Spłacony" : "Spłać"}</button>`]), { klasy: ["l"] })
        + ((v.decyzje.kredyty_wez || []).length ? `<p>Nowe kredyty: ${(v.decyzje.kredyty_wez || []).map((k, i) => `${zl(k.kwota)} na ${k.miesiecy} mies. <a href="#" data-akcja="usun-kredyt" data-i="${i}">usuń</a>`).join(", ")}</p>` : "")
        + `<p><button class="btn zielony" data-akcja="nowy-kredyt" ${edycja ? "" : "disabled"}>Weź kredyt</button>
          <span class="podpowiedz">Oprocentowanie ${proc(b.kredyt, 0)} rocznie, raty kapitałowe równe + odsetki od pozostałej kwoty, od następnego miesiąca.</span></p>`;
    } else {
      html += tabela(null, ["", "Kwota"], [["Aktualny stan zadłużenia", zl2(v.stan_przed.kredyt_odnawialny)], ["Oprocentowanie", proc(b.kredyt_odnawialny, 0)]], { klasy: ["l", "r"] })
        + `<p class="podpowiedz">Kredyt odnawialny uruchamia się sam, gdy zabraknie gotówki, i jest spłacany automatycznie z nadwyżki gotówki.</p>`;
    }
    return html;
  },
  akcje: {
    bank: (el, c) => { wyborBanku = false; return c.zmien((d) => { d.bank = el.dataset.b; }); },
    "zmien-bank": (el, c) => { wyborBanku = true; c.idz("bank", "decyzje"); },
    "bank-powrot": (el, c) => { wyborBanku = false; c.idz("bank", "decyzje"); },
    "bank-zak": (el, c) => { zakladkaBanku = el.dataset.k; c.idz("bank", "decyzje"); },
    zerwij: (el, c) => c.zmien((d) => { const id = +el.dataset.id, l = d.lokaty_zerwij || []; d.lokaty_zerwij = l.includes(id) ? l.filter((x) => x !== id) : [...l, id]; }),
    splac: (el, c) => c.zmien((d) => { const id = +el.dataset.id, l = d.kredyty_splac || []; d.kredyty_splac = l.includes(id) ? l.filter((x) => x !== id) : [...l, id]; }),
    "usun-lokate": (el, c, e) => { e.preventDefault(); return c.zmien((d) => { d.lokaty_zaloz.splice(+el.dataset.i, 1); }); },
    "usun-kredyt": (el, c, e) => { e.preventDefault(); return c.zmien((d) => { d.kredyty_wez.splice(+el.dataset.i, 1); }); },
    "nowa-lokata": (el, c) => okno("Zakładanie lokaty", `<div class="dwie"><label class="pole">Kwota lokaty<input type="number" id="l-kwota" min="1" step="100" value="${Math.max(0, Math.floor(c.v.stan.gotowka))}"></label>
      <label class="pole">Okres (miesiące)<input type="number" id="l-mies" min="1" max="${el.dataset.max}" value="1"></label></div>
      <p class="podpowiedz">Dostępne saldo: ${zl2(c.v.stan.gotowka)}. Pieniądze na lokacie nie są dostępne na bieżące wydatki.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="zaloz" data-max="${el.dataset.max}">Załóż</button>` }),
    zaloz: async (el, c) => {
      const kwota = +document.getElementById("l-kwota").value, m = Math.min(+el.dataset.max, Math.max(1, +document.getElementById("l-mies").value));
      if (!(kwota > 0)) return toast("Podaj kwotę.");
      zamknijOkno();
      await c.zmien((d) => { d.lokaty_zaloz = [...(d.lokaty_zaloz || []), { kwota, miesiecy: m }]; });
    },
    "nowy-kredyt": (el, c) => okno("Kredyt", `<div class="dwie"><label class="pole">Kwota kredytu<input type="number" id="k-kwota" min="100" step="1000" value="10000"></label>
      <label class="pole">Okres (miesiące)<input type="number" id="k-mies" min="1" max="${c.kat.oferty.banki.kredyt_maks_miesiecy}" value="6"></label></div>
      <p class="podpowiedz">Kredyt obniża wskaźnik zadłużenia w karcie wyników.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="wez-kredyt">Weź kredyt</button>` }),
    "wez-kredyt": async (el, c) => {
      const kwota = +document.getElementById("k-kwota").value, m = Math.max(1, Math.min(c.kat.oferty.banki.kredyt_maks_miesiecy, +document.getElementById("k-mies").value));
      if (!(kwota > 0)) return toast("Podaj kwotę.");
      zamknijOkno();
      await c.zmien((d) => { d.kredyty_wez = [...(d.kredyty_wez || []), { kwota, miesiecy: m }]; });
    },
  },
};

export const biuro = {
  tytul: "Biuro rachunkowe", tytulPelny: "Finanse - biuro rachunkowe", ikona: "🗂", odblokowanie: "finanse_biuro",
  info: "Wybierz biuro rachunkowe, które będzie prowadziło księgowość Twojej firmy. Opłata = księgowanie × liczba pozycji KPiR + opłata kadrowa za każdego pracownika.",
  decyzje({ v, kat, edycja }) {
    return `<div class="siatka trojka">${kat.oferty.biura_rachunkowe.pozycje.map((b) => `<div class="kafel ${b.nazwa === v.stan.biuro ? "wybrany" : ""}"><div class="kg">${esc(b.nazwa)}</div><div class="kt">
      <div class="wiersz"><span>Opłata za pojedyncze księgowanie</span><span>${zl2(b.ksiegowanie)}</span></div>
      <div class="wiersz"><span>Opłata kadrowa za pracownika etatowego</span><span>${zl(b.etat)}</span></div>
      <div class="wiersz"><span>Opłata kadrowa za pracownika na umowie cywilno-prawnej</span><span>${zl(b.zlecenie)}</span></div></div>
      <div class="kd">${b.nazwa === v.stan.biuro ? `<button class="btn zielony">✓ Wybrano</button>` : `<button class="btn czarny" data-akcja="biuro" data-b="${esc(b.nazwa)}" ${edycja ? "" : "disabled"}>Wybierz</button>`}</div></div>`).join("")}</div>`;
  },
  akcje: { biuro: (el, c) => c.zmien((d) => { d.biuro = el.dataset.b; }) },
};
