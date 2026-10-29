// Konkurencja (gra z lokalami, silnik/rynek/konkurencja.py, P16): ogólny obraz rywali dla wszystkich, dokładne dane – detektyw.
// Decyzja `detektyw: firma` – zlecenie obserwacji jednego rywala w tej rundzie (koszt w zł i godziny właściciela).
import { esc, gw, licz, nazwaFirmy, nazwaUslugi, proc, tabela, zl2 } from "./wspolne.js";

const tak = (x) => x ? `<span class="plus">tak</span>` : "nie";
const ceny = (r) => r.cena_min == null ? "–" : r.cena_min === r.cena_maks ? zl2(r.cena_min) : `${zl2(r.cena_min)} – ${zl2(r.cena_maks)}`;

function przegladHtml(v, K, tytul) {
  if (!K.przeglad.length) return `<p class="podpowiedz">Obraz rynku pojawi się po pierwszej rundzie.</p>`;
  return tabela(tytul, ["Drużyna", "Lokale", "Dania w menu", "Ceny dań", "Reklama", "Promocje", "Udział w klientach"],
    K.przeglad.map((r) => [r.ja ? `<b>${esc(nazwaFirmy(v, r.firma))} (Wy)</b>` : esc(nazwaFirmy(v, r.firma)), r.lokale, r.dania,
      ceny(r), tak(r.reklama), tak(r.promocje), proc(r.udzial)]), { klasy: ["l"] });
}

function raportHtml(v, kat, R) {
  const kto = esc(nazwaFirmy(v, R.rywal));
  return `<div class="kafel"><div class="kg">Raport detektywa: ${kto}</div><div class="kt"><p>${esc(R.tekst)}</p>
      ${R.wpadka ? `<p class="minus">${esc(R.wpadka)}</p><p class="podpowiedz">${kto} wie, że to Wy.</p>` : ""}</div></div>
    <div class="pasek ciemny"><span>Gotówka: <span class="kwota">${zl2(R.gotowka)}</span></span>
      <span>Przychody: <span class="kwota">${zl2(R.przychody)}</span></span>
      <span>Koszty: <span class="kwota">${zl2(R.koszty)}</span></span>
      <span>Dochód netto: <span class="kwota">${zl2(R.dochod_netto)}</span></span>
      ${R.zadluzenie ? `<span>Zadłużenie: <span class="kwota">${zl2(R.zadluzenie)}</span></span>` : ""}
      ${R.zadowolenie_klientow != null ? `<span>Zadowolenie klientów: <span class="kwota">${licz(R.zadowolenie_klientow, 2)}</span></span>` : ""}</div>`
    + tabela("Menu rywala", ["Danie", "Cena", "Po rabacie", "Popyt", "Sprzedane", "Przychód", "Reklamacje"],
      R.menu.map((m) => [esc(nazwaUslugi(kat, m.usluga)), zl2(m.cena), zl2(m.cena_po_rabacie), licz(m.popyt), licz(m.sprzedaz),
        zl2(m.przychod), m.reklamacje]), { klasy: ["l"] })
    + tabela("Lokale rywala", ["Lokal", "Strefa", "Forma"], R.lokale.map((l) => [esc(l.nazwa), esc(l.strefa), esc(l.forma)]), { klasy: ["l", "l", "l"] })
    + tabela("Załoga rywala", ["Zawód", "Gwiazdki", "Osób", "Średnia pensja"],
      R.zaloga.map((z) => [esc(z.zawod), gw(z.gwiazdki), z.liczba, zl2(z.pensja)]), { klasy: ["l"] })
    + (R.kampanie.length ? tabela("Kampanie reklamowe rywala", ["Kampania", "Agencja", "Strefa", "Koszt"],
      R.kampanie.map((k) => [esc(k.nazwa), esc(k.agencja), esc(k.strefa), zl2(k.koszt)]), { klasy: ["l", "l", "l"] }) : "")
    + (R.promocje.length ? tabela("Promocje rywala", ["Promocja", "Rodzaj", "Danie"],
      R.promocje.map((p) => [esc(p.nazwa), esc(p.rodzaj), p.danie ? esc(nazwaUslugi(kat, p.danie)) : "–"]), { klasy: ["l", "l", "l"] }) : "");
}

function wpadkiHtml(v, W) {
  return (W || []).map((x) => `<div class="kafel"><div class="kg">Ktoś Was śledził: ${esc(nazwaFirmy(v, x.kto))}</div>
    <div class="kt"><p>${esc(x.tekst)}</p></div></div>`).join("");
}

export const konkurencja = {
  tytul: "Konkurencja", tytulPelny: "Konkurencja i detektyw", ikona: "analiza",
  odblokowanie: (v) => !!v.konkurencja, ukryta: (v) => !v.konkurencja,
  info: `Ogólny obraz rywali z poprzedniej rundy widzi każdy: ile mają lokali, w jakim przedziale są ich ceny, czy się
    reklamują i mają promocje oraz jaką część klientów miasta przyciągnęli. Dokładne dane jednego rywala – gotówkę, ceny
    i sprzedaż każdego dania, załogę, kampanie, przychody i dochód – zbierze detektyw z biura przy dworcu. Zlecenie kosztuje
    pieniądze i godziny właściciela (<a data-zakladka-k="czas_wlasciciela">Czas właściciela</a>), a raport przychodzi
    w wynikach po rundzie. Detektyw czasem wpada – wtedy śledzona drużyna dowiaduje się, kto go wysłał.`,
  decyzje({ v, edycja }) {
    const K = v.konkurencja;
    if (!K) return `<p class="podpowiedz">Brak danych.</p>`;
    const Z = K.decyzja, wybrany = Z?.rywal ?? v.decyzje?.detektyw;
    let html = przegladHtml(v, K, "Rynek w poprzedniej rundzie – co widać z ulicy");
    html += `<div class="karta"><p><b>${esc(K.nazwa)}</b></p><p>${esc(K.powitanie)}</p></div>`;
    if (!K.otwarty) return html + `<p class="podpowiedz">Detektyw przyjmuje zlecenia od rundy ${K.od_rundy}.</p>`;
    const rywale = K.przeglad.filter((r) => !r.ja);
    html += `<div class="pasek ciemny"><span>Cena zlecenia w tej rundzie: <span class="kwota">${zl2(K.koszt)}</span></span>
      <span>Czas właściciela: <span class="kwota">${licz(K.godziny, 1)} h</span></span>
      <span>Szansa wpadki: <span class="kwota">${proc(K.szansa_wpadki, 0)}</span></span></div>`;
    html += rywale.length ? tabela("Kogo śledzić? (jedno zlecenie na rundę)", ["Drużyna", ""], rywale.map((r) => [esc(nazwaFirmy(v, r.firma)),
      r.firma === wybrany ? `<span class="plus">zlecone</span>${edycja ? ` <button class="btn jasny maly" data-akcja="det-anuluj">Odwołaj</button>` : ""}`
        : edycja ? `<button class="btn jasny" data-akcja="det-zlec" data-f="${esc(r.firma)}">Zleć obserwację</button>` : ""]),
      { klasy: ["l"], sortuj: false }) : `<p class="podpowiedz">Nie ma jeszcze kogo śledzić.</p>`;
    if (Z && !Z.przyjete) html += `<p class="minus">Zlecenie odrzucone: ${esc(Z.powod)}.</p>`;
    return html + `<p class="podpowiedz">Raport dotyczy tygodnia, w którym działa detektyw – przyjdzie w wynikach po tej rundzie.
      Cena zmienia się co rundę („z pogodą”, jak mówi Lupa).</p>`;
  },
  wyniki({ v, kat }) {
    const W = v.wyniki?.konkurencja, K = v.konkurencja;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    let html = wpadkiHtml(v, W.wpadki);
    if (W.raport) html += raportHtml(v, kat, W.raport);
    else if (W.zlecenie && !W.zlecenie.przyjete) html += `<p class="minus">Zlecenie detektywa odrzucone: ${esc(W.zlecenie.powod)}.</p>`;
    else if (!W.wpadki.length) html += `<p class="podpowiedz">W poprzedniej rundzie nie zlecaliście obserwacji i nikt Was nie śledził (a przynajmniej nikt nie wpadł).</p>`;
    return html + (K ? przegladHtml(v, K, "Ogólny obraz rynku w poprzedniej rundzie") : "");
  },
  akcje: {
    "det-zlec": (el, c) => c.zmien((d) => { d.detektyw = el.dataset.f; }),
    "det-anuluj": (el, c) => c.zmien((d) => { delete d.detektyw; }),
  },
};
