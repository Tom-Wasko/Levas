// Ubezpieczenia (gra z lokalami, silnik/awarie.py): polisy TUW na wypadki w lokalu. Decyzja `polisy: [rodzaj]` – pełna
// lista; polisa chroni po karencji i trwa, dopóki drużyna jej nie wypowie. Same wypadki – w zakładce Zdarzenia.
import { esc, naOkres, proc, tabela, zl2 } from "./wspolne.js";

const rund = (n) => `${n} ${n === 1 ? "runda" : n < 5 ? "rundy" : "rund"}`;

function szkodyHtml(S, tytul) {
  return S?.length ? tabela(tytul, ["Runda", "Wypadek", "Szkoda", "Koszt", "Odszkodowanie", "Uwagi"], S.map((s) => [s.runda, esc(s.tytul),
    esc(s.opis), `<span class="minus">${zl2(-s.kwota)}</span>`, s.odszkodowanie ? `<span class="plus">${zl2(s.odszkodowanie)}</span>` : "–",
    esc(s.powod || "")]), { klasy: ["", "l", "l", "", "", "l"] }) : "";
}

const nazwaPolisy = (U, r) => U.oferta.find((p) => p.rodzaj === r)?.nazwa ?? r;

export const ubezpieczenia = {
  tytul: "Ubezpieczenia", tytulPelny: "Ubezpieczenia lokalu", ikona: "tarcza", odblokowanie: (v) => !!v.ubezpieczenia, ukryta: (v) => !v.ubezpieczenia,
  info: `W lokalu zdarzają się wypadki – zwykle śmieszne, czasem poważne – i każdy kosztuje. Polisa nie zapobiegnie wypadkowi,
    ale zwraca część szkody: (koszt − franszyza) × pokrycie, jako przychód pozostały w KPiR. Chroni dopiero po karencji
    i tylko przed wypadkami, które zaczęły się, gdy już chroniła. Składka jest kosztem co rundę, dopóki polisy nie wypowiesz.
    Ubezpieczyciel ma siedzibę na <a data-zakladka-k="mapa">mapie miasta</a>.`,
  decyzje({ v, edycja }) {
    const U = v.ubezpieczenia;
    if (!U) return `<p class="podpowiedz">Brak danych.</p>`;
    const maLokal = !!v.stan?.lokale?.length;
    const wiersze = U.oferta.map((p) => {
      const od = U.posiadane[p.rodzaj];
      const stan = od == null ? "–" : od <= v.runda ? `<span class="plus">chroni</span>` : `chroni od rundy ${od}`;
      const btn = edycja && maLokal ? `<button class="btn ${od == null ? "zielony" : "jasny"}" data-akcja="ub-przelacz" data-r="${esc(p.rodzaj)}">${od == null ? "Kup" : "Wypowiedz"}</button>` : "";
      return [`<b>${esc(p.nazwa)}</b><br><small>${esc(p.opis)}</small>`, proc(p.pokrycie, 0), zl2(p.franszyza), zl2(p.skladka), stan, btn];
    });
    const D = U.decyzja;
    const zmiany = D ? [...D.nowe.map((r) => `Nowa polisa: ${esc(nazwaPolisy(U, r))}.`),
      ...D.wypowiedziane.map((r) => `Wypowiedziana: ${esc(nazwaPolisy(U, r))}.`)] : [];
    return `<div class="karta"><p>W ${esc(U.nazwa)} pachnie kawą z ekspresu i papierem. Agent wita Cię jak starego znajomego, choć
        widzi Cię pierwszy raz, i od razu pyta, czy w lokalu bywają gołębie. „Pytam rutynowo” – mówi i coś notuje.</p></div>
      <div class="pasek ciemny"><span>Karencja: <span class="kwota">${rund(U.karencja_rund)}</span></span>
        <span>Wypadki od rundy: <span class="kwota">${U.od_rundy}</span></span>
        <span>Najwyższa szkoda: <span class="kwota">${zl2(U.max_strata)}</span></span>
        ${D ? `<span>Składki w tej rundzie: <span class="kwota">${zl2(D.skladki)}</span></span>` : ""}</div>`
      + tabela("Polisy", ["Polisa", "Pokrycie", "Franszyza", `Składka${naOkres()}`, "Stan", ""], wiersze, { klasy: ["l"], sortuj: false })
      + (maLokal ? "" : `<p class="podpowiedz">Polisy są dla firm z lokalem.</p>`)
      + (zmiany.length ? `<div class="komunikat">${zmiany.join("<br>")}</div>` : "")
      + `<p class="podpowiedz">Składka zależy od liczby lokali (polisa na lokal) i wartości majątku (polisa na sprzęt) – po decyzjach tej rundy.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.ubezpieczenia, U = v.ubezpieczenia;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    const razem = [["Składki", `<span class="minus">${zl2(-W.skladki)}</span>`], ["Szkody z wypadków", `<span class="minus">${zl2(-W.szkody_razem)}</span>`],
      ["Odszkodowania", `<span class="plus">${zl2(W.odszkodowania)}</span>`]];
    const dawne = (U?.szkody || []).filter((s) => s.runda < v.runda - 1);
    return tabela("Ubezpieczenia w rundzie", ["Co", "Kwota"], razem, { klasy: ["l"], sortuj: false })
      + (W.polisy.length ? tabela("Polisy w rundzie", ["Polisa", "Chroni od rundy", "Składka"], W.polisy.map((p) => [esc(p.nazwa), p.od_rundy, zl2(p.skladka)]), { klasy: ["l"] })
        : `<p class="podpowiedz">W tej rundzie nie miałeś żadnej polisy.</p>`)
      + (szkodyHtml(W.szkody, "Szkody w rundzie") || `<p class="podpowiedz">W poprzedniej rundzie obyło się bez szkód.</p>`)
      + szkodyHtml(dawne, "Wcześniejsze szkody")
      + (U ? `<p class="podpowiedz">Od początku gry: składki ${zl2(U.skladki_razem)}, odszkodowania ${zl2(U.odszkodowania_razem)}.</p>` : "");
  },
  akcje: {
    "ub-przelacz": (el, c) => c.zmien((d) => {
      const teraz = d.polisy ?? Object.keys(c.v.ubezpieczenia.posiadane), r = el.dataset.r;
      d.polisy = teraz.includes(r) ? teraz.filter((x) => x !== r) : [...teraz, r];
    }),
  },
};
