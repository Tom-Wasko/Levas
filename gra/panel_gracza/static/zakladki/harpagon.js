// Lichwiarz Harpagon (gra z lokalami, silnik/lichwiarz.py): pożyczka „na czarno” od ręki, poza KPiR.
// Po terminie rośnie presja: przypomnienia, odsetki karne, wizyty (szkody, odpływ klientów, odejście pracownika).
import { esc, okno, proc, tabela, toast, zamknijOkno, zl2 } from "./wspolne.js";

const WIZYTA = { szkody: "Szkody w lokalu", klienci: "Odpływ klientów", pracownik: "Odejście pracownika" };

function stanHtml(P, tytul) {
  if (!P) return `<p class="podpowiedz">Nie masz długu u Harpagona. Harpagon to zauważył i jest tym głęboko zasmucony.</p>`;
  const po = P.po_terminie;
  const termin = po < 0 ? `za ${-po} ${-po === 1 ? "rundę" : "rundy"}` : po === 0 ? "w tej rundzie" : `${po} ${po === 1 ? "rundę" : "rund"} temu`;
  return tabela(tytul, ["Pożyczka", "Dług (z odsetkami)", "Naliczone odsetki", "Termin spłaty", "Etap", "Odsetki w rundzie", "Wizyty"],
    [[zl2(P.kwota), `<b>${zl2(P.dlug)}</b>`, zl2(P.odsetki), `runda ${P.termin} (${termin})`,
      po > 0 ? `<span class="minus">${esc(P.etap_nazwa)}</span>` : esc(P.etap_nazwa), proc(P.stopa), P.wizyty]]);
}

function decyzjaHtml(d, D) {
  const wiersze = [];
  if (d.harpagon_splac) wiersze.push([`Spłata ${zl2(d.harpagon_splac)}`, D?.splata ? (D.splacona ? "dług spłacony w całości" : "spłata częściowa") : "",
    `<button class="btn jasny" data-akcja="hp-usun" data-k="harpagon_splac">Usuń</button>`]);
  if (d.harpagon_wez) wiersze.push([`Pożyczka ${zl2(d.harpagon_wez)}`, D?.pozyczka ? "gotówka od razu w kasie" : "",
    `<button class="btn jasny" data-akcja="hp-usun" data-k="harpagon_wez">Usuń</button>`]);
  return wiersze.length ? tabela("Decyzje w tej rundzie", ["Co", "Skutek", ""], wiersze, { klasy: ["l", "l"] }) : "";
}

function odrzuconeHtml(D) {
  return D?.odrzucone?.length ? `<div class="komunikat">${D.odrzucone.map((o) => `${esc(o.co)}: ${esc(o.powod)}.`).join("<br>")}</div>` : "";
}

export const harpagon = {
  tytul: "Harpagon", tytulPelny: "Lichwiarz Harpagon", ikona: "harpagon", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Harpagon pożycza od ręki – bez sprawdzania zdolności kredytowej, bez umowy i <b>poza księgami</b>: gotówka nie jest
    przychodem w KPiR, a spłata i odsetki nie są kosztem. Odsetki liczy co rundę od całego długu. Po terminie robi się
    nieprzyjemnie: najpierw przypomnienia, potem odsetki karne, a w końcu wizyty – szkody w lokalu, odpływ klientów,
    odejście pracownika. Harpagon jest też na <a data-zakladka-k="mapa">mapie miasta</a>, przy dworcu.`,
  decyzje({ v, edycja }) {
    const H = v.harpagon;
    if (!H) return `<p class="podpowiedz">Brak danych.</p>`;
    const W = H.warunki, d = v.decyzje || {}, P = H.przed;
    const przyciski = edycja ? `<div class="przyciski">${P ? `<button class="btn zielony" data-akcja="hp-splac">Spłać</button>` : ""}
      ${!P && !d.harpagon_wez ? `<button class="btn" data-akcja="hp-wez">Pożycz od Harpagona</button>` : ""}</div>` : "";
    return `<div class="karta"><p>W ciasnym kantorku przy dworcu, między zegarem, który zatrzymał się, „bo szkoda mu się
        zużywać”, a szkatułką zakopaną w doniczce, siedzi Harpagon i liczy. Na Twój widok przestaje liczyć – to dobry znak
        tylko dla niego.</p></div>
      <div class="pasek ciemny"><span>Pożycza: <span class="kwota">${zl2(W.min_kwota)} – ${zl2(W.maks_kwota)}</span></span>
        <span>Odsetki: <span class="kwota">${proc(W.oprocentowanie_rundy)} na rundę</span></span>
        <span>Termin: <span class="kwota">${W.termin_rund} rundy</span></span>
        <span>Po terminie: <span class="kwota">${proc(W.odsetki_karne_rundy)}</span> od ${W.karne_od}. rundy, wizyty od ${W.wizyty_od}.</span></div>`
      + stanHtml(P, "Dług na początku rundy") + decyzjaHtml(d, H.decyzja) + odrzuconeHtml(H.decyzja)
      + (H.po && (d.harpagon_wez || d.harpagon_splac) ? stanHtml(H.po, "Dług po decyzjach (przed odsetkami tej rundy)") : "")
      + przyciski;
  },
  wyniki({ v }) {
    const H = v.wyniki?.harpagon;
    if (!H) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    const D = H.poczatek || {}, Pr = H.presja || {}, O = H.odsetki;
    const ruchy = [];
    if (D.pozyczka) ruchy.push(["Gotówka od Harpagona (poza księgami)", `<span class="plus">${zl2(D.pozyczka)}</span>`]);
    if (D.splata) ruchy.push([D.splacona ? "Spłata – dług zamknięty" : "Spłata częściowa", `<span class="minus">${zl2(-D.splata)}</span>`]);
    if (O) ruchy.push([`Odsetki doliczone do długu (${proc(O.stopa)})`, zl2(O.odsetki)]);
    const W = Pr.wizyta;
    return (ruchy.length ? tabela("Harpagon w rundzie", ["Co", "Kwota"], ruchy, { klasy: ["l"] }) : "")
      + odrzuconeHtml(D)
      + (Pr.teksty || []).map((t) => `<div class="karta"><p>${esc(t)}</p></div>`).join("")
      + (W ? `<div class="karta"><h3>Wizyta: ${esc(WIZYTA[W.rodzaj] || W.rodzaj)}</h3><p>${esc(W.tekst)}</p>
          <p class="podpowiedz">${W.rodzaj === "szkody" ? `Naprawa ${zl2(W.koszt)} – zwykły koszt w KPiR.`
            : W.rodzaj === "klienci" ? `Atrakcyjność lokali niższa o ${proc(W.odplyw, 0)} w tej rundzie.`
              : `${esc(W.pracownik)} odchodzi bez wypowiedzenia i wraca na rynek pracy; stanowisko jest wolne.`}</p></div>` : "")
      + stanHtml(H.stan, "Dług na następną rundę")
      + (!ruchy.length && !H.stan && !(Pr.teksty || []).length ? `<p class="podpowiedz">W tej rundzie Harpagon się nie pojawił.</p>` : "");
  },
  akcje: {
    "hp-wez": (el, c) => okno("Pożyczka od Harpagona", `<label class="pole">Kwota<input type="number" id="hp-kwota"
        min="${c.v.harpagon.warunki.min_kwota}" max="${c.v.harpagon.warunki.maks_kwota}" step="500" value="${c.v.harpagon.warunki.min_kwota}"></label>
      <p class="podpowiedz">Gotówka trafia do kasy od razu. Spłata w ciągu ${c.v.harpagon.warunki.termin_rund} rund – potem Harpagon zaczyna
      „przypominać”. Pożyczka nie obniża wskaźnika zadłużenia w karcie wyników, ale Harpagon pamięta.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hp-wez-ok">Pożycz</button>` }),
    "hp-wez-ok": async (el, c) => {
      const kwota = +document.getElementById("hp-kwota").value, W = c.v.harpagon.warunki;
      if (!(kwota >= W.min_kwota && kwota <= W.maks_kwota)) return toast(`Harpagon pożycza od ${zl2(W.min_kwota)} do ${zl2(W.maks_kwota)}.`);
      zamknijOkno();
      await c.zmien((d) => { d.harpagon_wez = kwota; });
    },
    "hp-splac": (el, c) => okno("Spłata u Harpagona", `<label class="pole">Kwota spłaty<input type="number" id="hp-splata" min="1" step="100"
        value="${c.v.harpagon.przed.dlug}"></label>
      <p class="podpowiedz">Dług: ${zl2(c.v.harpagon.przed.dlug)}. Spłata całości kończy presję. Harpagon nie przyjmuje obietnic –
      tylko gotówkę z konta.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hp-splac-ok">Spłać</button>` }),
    "hp-splac-ok": async (el, c) => {
      const kwota = +document.getElementById("hp-splata").value;
      if (!(kwota > 0)) return toast("Podaj kwotę.");
      zamknijOkno();
      await c.zmien((d) => { d.harpagon_splac = kwota; });
    },
    "hp-usun": (el, c) => c.zmien((d) => { delete d[el.dataset.k]; }),
  },
};
