// Podatki i ZUS jednoosobowej działalności (gra z lokalami, silnik/rozliczenie.py): rejestr VAT, składki
// właściciela, zaliczka PIT liniowego – rozliczenie co rundę zamiast CIT Revasa. Ceny w grze są brutto.
import { esc, proc, tabela, zl2 } from "./wspolne.js";

const RODZAJ = { nalezny: "należny (sprzedaż)", naliczony: "naliczony (zakupy)" };

function stawkiHtml(R, tytul) {
  if (!R?.stawki?.length) return `<p class="podpowiedz">${tytul}: brak pozycji z VAT.</p>`;
  return tabela(tytul, ["VAT", "Stawka", "Netto", "VAT", "Brutto"],
    R.stawki.map((s) => [RODZAJ[s.rodzaj], proc(s.stawka, 0), zl2(s.netto), `<b>${zl2(s.vat)}</b>`, zl2(s.brutto)]),
    { klasy: ["l", "r", "r", "r", "r"], stopka: ["Należny − naliczony", "", "", zl2(R.nalezny - R.naliczony), ""] });
}

function rejestrHtml(R) {
  if (!R?.pozycje?.length) return "";
  return `<details><summary>Rejestr VAT – ${R.pozycje.length} pozycji</summary>`
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

export const podatki = {
  tytul: "Podatki", tytulPelny: "Podatki i ZUS – rozliczenie JDG", ikona: "podatki", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Prowadzisz jednoosobową działalność: KPiR, czynny VAT i PIT liniowy. Wszystkie ceny w grze są <b>brutto</b> – z każdej
    sprzedaży i z większości zakupów wydzielany jest VAT (do KPiR trafia netto). Na koniec każdej rundy biuro rachunkowe
    rozlicza: VAT (należny − naliczony; nadwyżka przechodzi na następną rundę), składkę zdrowotną, zaliczkę na PIT
    (narastająco od początku gry) i – po uldze na start – preferencyjny ZUS. Wszystko płaci się z konta, automatycznie.`,
  decyzje({ v }) {
    const T = v.podatki;
    if (!T) return `<p class="podpowiedz">Brak danych.</p>`;
    const P = T.parametry, S = T.stan;
    const uslugi = Object.entries(P.vat_uslug).map(([u, s]) => [esc(v.kat?.uslugi?.[u]?.nazwa || u), proc(s, 0)]);
    return `<div class="karta"><p>Urząd skarbowy w Levasie mieści się w budynku, który – jak głosi legenda – sam siebie
        rozliczył z podatku od nieruchomości. Pani naczelnik nie ma nic przeciwko Tobie. Ma tylko kalkulator.</p></div>`
      + parametryHtml(P, T.ulga_na_start)
      + tabela("Stan rozliczeń na początku rundy", ["Dochód narastająco", "Zdrowotna odliczona", "Zaliczki PIT wpłacone", "Nadwyżka VAT do przeniesienia", "Razem zapłacone"],
        [[zl2(S.dochod), zl2(S.zdrowotna_odliczona), zl2(S.zaliczki), zl2(S.vat_nadwyzka), zl2(S.zaplacone)]])
      + stawkiHtml(T.rejestr, "VAT z decyzji tej rundy (przed sprzedażą)") + rejestrHtml(T.rejestr)
      + `<details><summary>Stawki VAT</summary>`
      + tabela("Sprzedaż", ["Danie", "VAT"], uslugi, { klasy: ["l", "r"] })
      + tabela("Zakup składników", ["Składnik", "VAT"], Object.entries(P.vat_zasobow).map(([z, s]) => [esc(z), proc(s, 0)]), { klasy: ["l", "r"] })
      + tabela("Pozostałe koszty (wg opisu w KPiR; reszta bez VAT)", ["Opis zawiera", "VAT"], P.vat_kosztow.map((r) => [esc(r.zawiera), proc(r.stawka, 0)]), { klasy: ["l", "r"] })
      + `<p class="podpowiedz">Środki trwałe (sprzęt, wyposażenie, stanowiska od progu amortyzacji): VAT ${proc(P.vat_srodkow_trwalych, 0)},
        do ewidencji idzie netto. Lokal, działka i budynek – bez VAT. Odliczenie zdrowotnej do ${zl2(P.limit_odliczenia)} rocznie.</p></details>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.rozliczenie;
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
      + tabela("Deklaracja VAT", ["Należny", "Naliczony", "Nadwyżka z poprzedniej rundy", "Saldo", "Do zapłaty", "Nadwyżka na następną rundę"],
        [[zl2(W.vat_nalezny), zl2(W.vat_naliczony), zl2(W.vat_nadwyzka_poprzednia), zl2(W.vat_saldo), `<b>${zl2(W.vat_do_zaplaty)}</b>`, zl2(W.vat_nadwyzka)]])
      + stawkiHtml(v.wyniki.vat, "VAT wg stawek") + rejestrHtml(v.wyniki.vat)
      + (W.zaliczka === 0 && W.dochod < 0 ? `<p class="podpowiedz">Strata pomniejsza dochód narastająco, ale wpłaconych zaliczek urząd w trakcie gry
          nie oddaje – „rozliczymy się w zeznaniu rocznym”, mówi pani naczelnik i dopisuje coś ołówkiem.</p>` : "");
  },
};
