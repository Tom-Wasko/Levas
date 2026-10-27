// Podatki jednoosobowej działalności (silnik/rozliczenie.py) – dwie zakładki Finansów: VAT (rejestr, stawki,
// deklaracja) oraz Podatki (składki właściciela, zaliczka PIT liniowego). Rozliczenie co rundę, ceny w grze są brutto.
import { UKRYTE } from "./finanse.js";
import { esc, nazwaUslugi, proc, tabela, zl2 } from "./wspolne.js";

const RODZAJ = { nalezny: "należny (sprzedaż)", naliczony: "naliczony (zakupy)" };

function stawkiHtml(R, tytul) {
  if (!R?.stawki?.length) return `<p class="podpowiedz">${tytul}: brak pozycji z VAT.</p>`;
  return tabela(tytul, ["VAT", "Stawka", "Netto", "VAT", "Brutto"],
    R.stawki.map((s) => [RODZAJ[s.rodzaj], proc(s.stawka, 0), zl2(s.netto), `<b>${zl2(s.vat)}</b>`, zl2(s.brutto)]),
    { klasy: ["l", "r", "r", "r", "r"], stopka: ["Należny − naliczony", "", "", zl2(R.nalezny - R.naliczony), ""] });
}

function rejestrHtml(R) {
  if (!R?.pozycje?.length) return "";
  const n = R.pozycje.length, j = n % 10, d = n % 100;
  const slowo = n === 1 ? "pozycja" : j >= 2 && j <= 4 && (d < 12 || d > 14) ? "pozycje" : "pozycji";
  return `<details><summary>Rejestr VAT – ${n} ${slowo}</summary>`
    + tabela(null, ["Opis", "Rodzaj", "Stawka", "Netto", "VAT", "Brutto"],
      R.pozycje.map((p) => [esc(p.opis), RODZAJ[p.rodzaj], proc(p.stawka, 0), zl2(p.netto), zl2(p.vat), zl2(p.brutto)]),
      { klasy: ["l", "l", "r", "r", "r", "r"] }) + `</details>`;
}

function parametryHtml(P, ulga) {
  return `<div class="pasek ciemny"><span>PIT liniowy: <span class="kwota">${proc(P.pit, 0)}</span></span>
    <span>Zdrowotna: <span class="kwota">${proc(P.zdrowotna, 1)}</span> dochodu, min. ${zl2(P.zdrowotna_minimum)} na rundę</span>
    <span>ZUS społeczny: <span class="kwota">${ulga ? `0 zł – ulga na start (do rundy ${P.ulga_rund})` : `${zl2(P.spoleczne)} na rundę`}</span></span>
    <span>ZUS pracodawcy: <span class="kwota">${proc(P.zus_pracodawcy, 2)}</span> pensji na etacie</span></div>`;
}

function stawkiVatHtml(P, kat) {
  const uslugi = Object.entries(P.vat_uslug).map(([u, s]) => [esc(kat.uslugi[u] ? nazwaUslugi(kat, u) : u), proc(s, 0)]);
  return tabela("Sprzedaż", ["Danie", "VAT"], uslugi, { klasy: ["l", "r"] })
    + tabela("Zakup składników", ["Składnik", "VAT"], Object.entries(P.vat_zasobow).map(([z, s]) => [esc(z), proc(s, 0)]), { klasy: ["l", "r"] })
    + tabela("Pozostałe koszty (wg opisu w KPiR; reszta bez VAT)", ["Opis zawiera", "VAT"], P.vat_kosztow.map((r) => [esc(r.zawiera), proc(r.stawka, 0)]), { klasy: ["l", "r"] })
    + `<p class="podpowiedz">Środki trwałe (sprzęt, wyposażenie, stanowiska od progu amortyzacji): VAT ${proc(P.vat_srodkow_trwalych, 0)},
      do ewidencji idzie netto. Lokal, działka i budynek – bez VAT.</p>`;
}

export const vat = {
  tytul: "VAT", tytulPelny: "Finanse – VAT: rejestr, stawki i deklaracja", ikona: "procent", odblokowanie: (v) => !!v.podatki, ukryta: (v) => !v.podatki,
  info: `Jesteś czynnym podatnikiem VAT. Wszystkie ceny w grze są <b>brutto</b> – z każdej sprzedaży i z większości zakupów
    wydzielany jest VAT, a do KPiR trafia kwota netto. Na koniec rundy biuro rachunkowe składa deklarację: VAT należny
    (ze sprzedaży) minus naliczony (z zakupów); nadwyżka naliczonego przechodzi na następną rundę.`,
  decyzje({ v, kat }) {
    const T = v.podatki;
    if (!T) return `<p class="podpowiedz">Brak danych.</p>`;
    return `<div class="karta"><p>W urzędzie skarbowym VAT liczy pan Zenon. Pan Zenon nie je kebabów, bo „z sosem czosnkowym
        stawka robi się niejasna”. Twoje paragony przegląda jednak z wyraźnym apetytem.</p></div>`
      + tabela("Nadwyżka VAT z poprzednich rund", ["Do odliczenia w tej rundzie"], [[zl2(T.stan.vat_nadwyzka)]])
      + stawkiHtml(T.rejestr, "VAT z decyzji tej rundy (przed sprzedażą)") + rejestrHtml(T.rejestr)
      + `<details open><summary>Stawki VAT</summary>${stawkiVatHtml(T.parametry, kat)}</details>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.rozliczenie;
    if (v.wyniki?.kpir?.ukryte) return UKRYTE;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    return tabela("Deklaracja VAT", ["Należny", "Naliczony", "Nadwyżka z poprzedniej rundy", "Saldo", "Do zapłaty", "Nadwyżka na następną rundę"],
      [[zl2(W.vat_nalezny), zl2(W.vat_naliczony), zl2(W.vat_nadwyzka_poprzednia), zl2(W.vat_saldo), `<b>${zl2(W.vat_do_zaplaty)}</b>`, zl2(W.vat_nadwyzka)]])
      + stawkiHtml(v.wyniki.vat, "VAT wg stawek") + rejestrHtml(v.wyniki.vat);
  },
};

export const podatki = {
  tytul: "Podatki", tytulPelny: "Finanse – PIT i ZUS (rozliczenie JDG)", ikona: "podatki", odblokowanie: (v) => !!v.podatki, ukryta: (v) => !v.podatki,
  info: `Prowadzisz jednoosobową działalność: KPiR i PIT liniowy (VAT – w zakładce obok). Na koniec każdej rundy biuro
    rachunkowe rozlicza składkę zdrowotną, zaliczkę na PIT (narastająco od początku gry) i – po uldze na start –
    preferencyjny ZUS. Wszystko płaci się z konta, automatycznie.`,
  decyzje({ v }) {
    const T = v.podatki;
    if (!T) return `<p class="podpowiedz">Brak danych.</p>`;
    const P = T.parametry, S = T.stan;
    return `<div class="karta"><p>Urząd skarbowy w Levasie mieści się w budynku, który – jak głosi legenda – sam siebie
        rozliczył z podatku od nieruchomości. Pani naczelnik nie ma nic przeciwko Tobie. Ma tylko kalkulator.</p></div>`
      + parametryHtml(P, T.ulga_na_start)
      + tabela("Stan rozliczeń na początku rundy", ["Dochód narastająco", "Zdrowotna odliczona", "Zaliczki PIT wpłacone", "Nadwyżka VAT do przeniesienia", "Razem zapłacone"],
        [[zl2(S.dochod), zl2(S.zdrowotna_odliczona), zl2(S.zaliczki), zl2(S.vat_nadwyzka), zl2(S.zaplacone)]])
      + `<p class="podpowiedz">Odliczenie zdrowotnej do ${zl2(P.limit_odliczenia)} rocznie.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.rozliczenie;
    if (v.wyniki?.kpir?.ukryte) return UKRYTE;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    return tabela("Rozliczenie rundy", ["Pozycja", "Kwota"], [
      ["Dochód z KPiR w rundzie", zl2(W.dochod)],
      [W.ulga_na_start ? "ZUS społeczny (ulga na start)" : "ZUS społeczny właściciela (koszt w KPiR)", zl2(W.zus_spoleczne)],
      [`Składka zdrowotna (${W.zdrowotna === W.zdrowotna_minimum ? "minimalna" : "od dochodu"})`, zl2(W.zdrowotna)],
      ["Zaliczka na PIT", zl2(W.zaliczka)],
      ["VAT do zapłaty", zl2(W.vat_do_zaplaty)],
      ["<b>Razem do urzędu i ZUS</b>", `<b>${zl2(W.razem)}</b>`],
      ["Dochód netto rundy (po PIT i zdrowotnej)", zl2(W.dochod_netto)]], { klasy: ["l", "r"] })
      + tabela("Zaliczka PIT – narastająco od początku gry", ["Dochód", "− zdrowotna odliczona", "Podstawa (zł)", `Podatek ${proc(W.stawka_pit, 0)}`, "− wpłacone wcześniej", "Zaliczka"],
        [[zl2(W.dochod_narastajaco), zl2(W.zdrowotna_odliczona), W.podstawa, zl2(W.podatek_narastajaco),
          zl2(W.zaliczki_narastajaco - W.zaliczka), `<b>${zl2(W.zaliczka)}</b>`]])
      + (W.zaliczka === 0 && W.dochod < 0 ? `<p class="podpowiedz">Strata pomniejsza dochód narastająco, ale wpłaconych zaliczek urząd w trakcie gry
          nie oddaje – „rozliczymy się w zeznaniu rocznym”, mówi pani naczelnik i dopisuje coś ołówkiem.</p>` : "");
  },
};
