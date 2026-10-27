// Handel między drużynami (gra z lokalami, silnik/handel.py): oferty sprzedaży towaru i sprzętu innej drużynie,
// przyjęcie w następnej rundzie, faktury w KPiR obu stron. Decyzje `handel_oferty` i `handel_przyjmij`.
// P13: negocjacje na żywo w rundzie wystawienia – adresat widzi szkic oferty od razu i odpowiada w `handel_odpowiedzi`
// ({"<sprzedawca>/<klucz>": {kontry, przyjmij, nr, odrzuc}}), sprzedawca dopisuje `ceny` albo `przyjmij_kontre`.
import { esc, okno, tabela, toast, zamknijOkno, zl2 } from "./wspolne.js";

const proc = (x) => `${Math.round(x * 100)}%`;
const klucz = (o, i) => o.klucz || `i${i + 1}`;
const nowyKlucz = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
const STAN = { umowa: "umowa", odrzucona: "odrzucona", ruch_kupujacego: "ruch kupującego", ruch_sprzedawcy: "ruch sprzedawcy" };

function przebieg(N, sprzedawca, kupujacy) {
  return (N?.ruchy || []).map((r) => `${esc(r.kto === "sprzedawca" ? sprzedawca : kupujacy)}: ${zl2(r.cena)}`).join(" → ");
}

function widelkiTekst(w) {
  return w ? `Cena od ${zl2(w[0])} do ${zl2(w[1])}.` : "";
}

function przychodzaceNaZywo(H, edycja) {
  const P = H.na_zywo?.przychodzace || [];
  if (!P.length) return "";
  return tabela("Negocjacje w tej rundzie – oferty dla twojej drużyny", ["Od", "Co", "Przebieg", "Stan", ""],
    P.map((o) => {
      const N = o.negocjacja;
      let akcje = "";
      if (N.stan === "umowa") akcje = `<span class="plus">umowa za ${zl2(N.cena)} – towar przyjdzie na początku następnej rundy</span>`;
      else if (N.stan === "odrzucona") akcje = edycja ? `<button class="btn jasny" data-akcja="hn-cofnij-odrzucenie" data-k="${esc(o.klucz)}">Cofnij odrzucenie</button>` : "";
      else if (N.stan === "ruch_sprzedawcy") akcje = `<span class="podpowiedz">czekasz na odpowiedź sprzedawcy</span>`;
      else if (edycja) {
        akcje = `<button class="btn zielony" data-akcja="hn-przyjmij" data-k="${esc(o.klucz)}">Przyjmij za ${zl2(N.cena)}</button>`
          + (N.kontr_zostalo ? `<button class="btn" data-akcja="hn-kontra-k" data-k="${esc(o.klucz)}">Kontroferta</button>` : "")
          + `<button class="btn jasny" data-akcja="hn-odrzuc" data-k="${esc(o.klucz)}">Odrzuć</button>`;
      }
      return [esc(o.od_nazwa), esc(o.co), przebieg(N, o.od_nazwa, "Ty"), `${STAN[N.stan]}${N.stan.startsWith("ruch") ? ` (kontroferty: ${N.kontr_zostalo})` : ""}`, akcje];
    }), { klasy: ["l", "l", "l", "l"], sortuj: false });
}

function nieudaneHtml(D) {
  return [...(D?.odrzucone || []), ...(D?.nieudane || [])]
    .map((o) => `<p class="minus">${esc(o.co)}: ${esc(o.powod)}.</p>`).join("");
}

function transakcjeHtml(D, tytul) {
  const T = D?.transakcje || [];
  if (!T.length) return "";
  return tabela(tytul, ["Strona", "Z kim", "Co", "Netto", "VAT", "Brutto"],
    T.map((t) => [t.strona === "sprzedaz" ? "Sprzedaż (faktura sprzedaży)" : "Zakup (faktura zakupu)", esc(t.z_kim),
      esc(t.co) + (t.nr ? ` → stanowisko ${t.nr}` : ""), zl2(t.netto), zl2(t.vat),
      `<span class="${t.strona === "sprzedaz" ? "plus" : "minus"}">${zl2(t.strona === "sprzedaz" ? t.cena : -t.cena)}</span>`]),
    { klasy: ["l", "l", "l"] })
    + T.map((t) => `<div class="karta"><p>${esc(t.tekst)}</p></div>`).join("");
}

function ofertyHtml(lista, tytul, kto) {
  if (!lista?.length) return "";
  return tabela(tytul, [kto === "od" ? "Od" : "Dla", "Co", "Termin", "Netto", "VAT", "Brutto"],
    lista.map((o) => [esc(kto === "od" ? o.od_nazwa : o.do_nazwa), esc(o.co), o.termin ? esc(o.termin) : "–",
      zl2(o.netto), zl2(o.vat), zl2(o.cena)]), { klasy: ["l", "l", "l"] });
}

export const handel = {
  tytul: "Handel z drużynami", ikona: "handel", odblokowanie: (v) => !!v.handel?.otwarty, ukryta: (v) => !v.handel,
  info: `Drużyny mogą sprzedawać sobie towar z magazynu i sprzęt ze stanowisk – po uzgodnionej cenie, z fakturą.
    Ofertę wystawiasz w tej rundzie (sprawdzana po tygodniu sprzedaży), adresat przyjmuje ją w następnej – wtedy towar
    i pieniądze zmieniają właściciela na początku rundy. Sprzedawca księguje przychód i VAT należny, kupujący – koszt
    i VAT naliczony. Cena musi mieścić się w widełkach wartości – nie da się „podarować” pieniędzy innej drużynie.`,
  decyzje({ v, d, edycja }) {
    const H = v.handel;
    if (!H) return `<p class="podpowiedz">Brak danych.</p>`;
    if (!H.otwarty) return `<p class="podpowiedz">Handel między drużynami od rundy ${H.od_rundy}.</p>`;
    const D = H.decyzja;
    const przyjete = new Set((d.handel_przyjmij || []).map((p) => p.id));
    const L = H.limity;
    let h = `<div class="pasek ciemny"><span>Widełki ceny: ${proc(L.cena_min)}–${proc(L.cena_maks)} wartości
        (towar – koszt zakupu, sprzęt – cena katalogowa)</span><span>Najwyżej ${L.maks_ofert} ofert w rundzie</span></div>`;
    // oferty od innych drużyn – do przyjęcia teraz
    if (H.przychodzace.length) {
      h += tabela("Oferty dla twojej drużyny (ważne w tej rundzie)", ["Od", "Co", "Termin", "Brutto", "VAT", ""],
        H.przychodzace.map((o) => {
          const p = (d.handel_przyjmij || []).find((x) => x.id === o.id);
          return [esc(o.od_nazwa), esc(o.co) + (p?.nr ? ` → stanowisko ${p.nr}` : ""), o.termin ? esc(o.termin) : "–",
            zl2(o.cena), zl2(o.vat), o.uzgodniona ? `<span class="plus">umowa – realizowana automatycznie</span>`
              : !edycja ? (przyjete.has(o.id) ? "przyjęta" : "")
              : przyjete.has(o.id) ? `<button class="btn jasny" data-akcja="hd-odrzuc" data-id="${esc(o.id)}">Cofnij</button>`
                : `<button class="btn zielony" data-akcja="hd-przyjmij" data-id="${esc(o.id)}">Przyjmij</button>`];
        }), { klasy: ["l", "l", "l"], sortuj: false });
    } else {
      h += `<p class="podpowiedz">Żadna drużyna nie złożyła ci oferty w poprzedniej rundzie.</p>`;
    }
    h += transakcjeHtml(D, "Przyjęte oferty – po przeliczeniu (podgląd)");
    // własne oferty na tę rundę
    h += przychodzaceNaZywo(H, edycja);
    const moje = d.handel_oferty || [];
    if (moje.length) {
      h += tabela("Twoje oferty w tej rundzie – adresat widzi je od razu i może negocjować", ["Dla", "Co", "Przebieg", "Stan", ""],
        moje.map((o, i) => {
          const dla = H.druzyny.find((x) => x.nazwa === o.do)?.wyswietlana || o.do;
          const N = H.na_zywo?.moje?.[klucz(o, i)];
          let akcje = edycja && N?.stan !== "umowa" ? `<button class="btn jasny" data-akcja="hd-usun" data-i="${i}">Wycofaj</button>` : "";
          if (edycja && N?.stan === "ruch_sprzedawcy") {
            akcje = `<button class="btn zielony" data-akcja="hn-przyjmij-kontre" data-i="${i}">Przyjmij ${zl2(N.cena)}</button>`
              + (N.kontr_zostalo ? `<button class="btn" data-akcja="hn-kontra-s" data-i="${i}">Kontroferta</button>` : "") + akcje;
          }
          const stan = !N ? "" : N.stan === "umowa" ? `<span class="plus">umowa za ${zl2(N.cena)}</span>`
            : `${STAN[N.stan]}${N.stan.startsWith("ruch") ? ` (kontroferty: ${N.kontr_zostalo})` : ""}`;
          return [esc(dla), esc(o.typ === "towar" ? `${o.zasob} ${o.jakosc}★ × ${o.ilosc} opak.` : `${o.nazwa} (${o.stanowisko} ${o.nr})`),
            N ? przebieg(N, "Ty", dla) : zl2(o.cena), stan, akcje];
        }), { klasy: ["l", "l", "l", "l"], sortuj: false });
    }
    h += ofertyHtml(H.wystawione, "Oferty z poprzedniej rundy – czekają na decyzję adresata", "do");
    h += nieudaneHtml(D);
    if (edycja && H.druzyny.length) {
      h += `<div class="przyciski">${H.towary.length ? `<button class="btn" data-akcja="hd-towar">Sprzedaj towar</button>` : ""}
        ${H.sprzet.length ? `<button class="btn" data-akcja="hd-sprzet">Sprzedaj sprzęt</button>` : ""}</div>`;
    }
    if (!H.druzyny.length) h += `<p class="podpowiedz">W grze nie ma innych drużyn (boty nie handlują).</p>`;
    h += `<p class="podpowiedz">Negocjacje na żywo: adresat widzi twoją ofertę od razu, może ją przyjąć, odrzucić albo
      złożyć kontrofertę; potem twój ruch – i tak na przemian, najwyżej ${L.maks_kontr ?? 3} kontroferty razem. Przyjęta
      cena to umowa: towar i pieniądze zmienią właściciela na początku następnej rundy, bez dodatkowego klikania.
      Oferta bez umowy czeka jeszcze rundę po twojej ostatniej cenie. Ruchy drugiej drużyny pojawiają się same po kilku
      sekundach – negocjować można, dopóki żadna z drużyn nie wyśle decyzji.</p>`;
    return h + `<p class="podpowiedz">Oferta jest sprawdzana na stanie po tygodniu sprzedaży: towaru musi wystarczyć
      w magazynie na koniec rundy. Kupujący płaci z konta firmy – bez pieniędzy transakcji nie będzie. Towar przychodzi
      z terminem przydatności sprzedawcy, sprzęt trafia na wybrane stanowisko (sprzętu z najmu lokalu i w leasingu nie
      można sprzedać).</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.handel;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po rundzie z handlem.</p>`;
    const puste = !W.transakcje?.length && !W.wystawione?.length && !W.odrzucone?.length && !W.nieudane?.length;
    return transakcjeHtml(W, "Transakcje w rundzie")
      + ofertyHtml((W.wystawione || []).filter((o) => o.uzgodniona), "Umowy z negocjacji (transakcja na początku następnej rundy)", "do")
      + ofertyHtml((W.wystawione || []).filter((o) => !o.uzgodniona), "Oferty wystawione (do przyjęcia w następnej rundzie)", "do")
      + ((W.odrzucone_przez_adresata || []).length ? `<p class="podpowiedz">Odrzucone przez adresata: ${W.odrzucone_przez_adresata.map((o) => esc(o.co)).join(", ")}.</p>` : "")
      + nieudaneHtml(W)
      + (puste ? `<p class="podpowiedz">W tej rundzie nie było handlu z innymi drużynami.</p>` : "");
  },
  akcje: {
    // --- negocjacje na żywo: kupujący
    "hn-przyjmij": (el, c) => {
      const H = c.v.handel, o = H.na_zywo.przychodzace.find((x) => x.klucz === el.dataset.k);
      const wolne = o.typ === "sprzet" ? H.stanowiska.filter((s) => s.typ === o.stanowisko && !s.sprzet.includes(o.nazwa)) : [];
      if (o.typ === "sprzet" && !wolne.length) return toast(`Nie masz stanowiska (${o.stanowisko}) bez ${o.nazwa} – kup najpierw stanowisko.`);
      okno(`Przyjąć ofertę: ${o.co}?`, (wolne.length ? `<label class="pole">Stanowisko<select id="hn-nr">${wolne.map((s) =>
        `<option value="${s.nr}">${esc(s.typ)} ${s.nr}</option>`).join("")}</select></label>` : "")
        + `<p>Cena ${zl2(o.negocjacja.cena)} brutto od drużyny ${esc(o.od_nazwa)}. Przyjęcie to umowa – nie da się go cofnąć,
          a pieniądze zejdą z konta na początku następnej rundy.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Jeszcze nie</button><button class="btn zielony" data-akcja="hn-przyjmij-ok" data-k="${esc(o.klucz)}">Przyjmuję</button>` });
    },
    "hn-przyjmij-ok": async (el, c) => {
      const o = c.v.handel.na_zywo.przychodzace.find((x) => x.klucz === el.dataset.k);
      const nr = document.getElementById("hn-nr")?.value;
      zamknijOkno();
      await c.zmien((d) => {
        const odp = (d.handel_odpowiedzi = d.handel_odpowiedzi || {});
        odp[o.klucz] = { ...(odp[o.klucz] || {}), przyjmij: o.negocjacja.cena, ...(nr ? { nr: +nr } : {}) };
        delete odp[o.klucz].odrzuc;
      });
    },
    "hn-kontra-k": (el, c) => {
      const o = c.v.handel.na_zywo.przychodzace.find((x) => x.klucz === el.dataset.k);
      okno(`Kontroferta: ${o.co}`, `<label class="pole">Twoja cena brutto<input type="number" id="hn-cena" min="0.01" step="10"
        value="${Math.round(o.negocjacja.cena * 0.9)}"></label><p class="podpowiedz">Sprzedawca chce ${zl2(o.negocjacja.cena)}.
        ${widelkiTekst(o.widelki)} Zostało kontrofert: ${o.negocjacja.kontr_zostalo}.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hn-kontra-k-ok" data-k="${esc(o.klucz)}">Wyślij kontrofertę</button>` });
    },
    "hn-kontra-k-ok": async (el, c) => {
      const o = c.v.handel.na_zywo.przychodzace.find((x) => x.klucz === el.dataset.k);
      const cena = +document.getElementById("hn-cena").value;
      if (!(cena > 0)) return toast("Podaj cenę.");
      if (o.widelki && (cena < o.widelki[0] || cena > o.widelki[1])) return toast(widelkiTekst(o.widelki));
      zamknijOkno();
      await c.zmien((d) => {
        const odp = (d.handel_odpowiedzi = d.handel_odpowiedzi || {});
        const x = odp[o.klucz] || {};
        odp[o.klucz] = { ...x, kontry: [...(x.kontry || []), cena] };
        delete odp[o.klucz].przyjmij;
      });
    },
    "hn-odrzuc": (el, c) => c.zmien((d) => {
      const odp = (d.handel_odpowiedzi = d.handel_odpowiedzi || {});
      odp[el.dataset.k] = { ...(odp[el.dataset.k] || {}), odrzuc: true };
    }),
    "hn-cofnij-odrzucenie": (el, c) => c.zmien((d) => { delete (d.handel_odpowiedzi || {})[el.dataset.k]?.odrzuc; }),
    // --- negocjacje na żywo: sprzedawca
    "hn-przyjmij-kontre": (el, c) => {
      const i = +el.dataset.i, o = c.d.handel_oferty[i], N = c.v.handel.na_zywo.moje[klucz(o, i)];
      okno("Przyjąć kontrofertę?", `<p>Sprzedajesz za ${zl2(N.cena)} brutto. Przyjęcie to umowa – nie da się go cofnąć.</p>`,
        { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Jeszcze nie</button><button class="btn zielony" data-akcja="hn-przyjmij-kontre-ok" data-i="${i}">Przyjmuję</button>` });
    },
    "hn-przyjmij-kontre-ok": async (el, c) => {
      const i = +el.dataset.i, N = c.v.handel.na_zywo.moje[klucz(c.d.handel_oferty[i], i)];
      zamknijOkno();
      await c.zmien((d) => { d.handel_oferty[i].przyjmij_kontre = N.cena; });
    },
    "hn-kontra-s": (el, c) => {
      const i = +el.dataset.i, o = c.d.handel_oferty[i], N = c.v.handel.na_zywo.moje[klucz(o, i)];
      okno("Twoja kontroferta", `<label class="pole">Cena brutto<input type="number" id="hn-cena" min="0.01" step="10"
        value="${Math.round((N.cena + o.cena) / 2)}"></label><p class="podpowiedz">Kupujący proponuje ${zl2(N.cena)}, ty
        chciałeś ${zl2(o.cena)}. ${widelkiTekst(N.widelki)} Zostało kontrofert: ${N.kontr_zostalo}.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hn-kontra-s-ok" data-i="${i}">Wyślij kontrofertę</button>` });
    },
    "hn-kontra-s-ok": async (el, c) => {
      const i = +el.dataset.i, N = c.v.handel.na_zywo.moje[klucz(c.d.handel_oferty[i], i)];
      const cena = +document.getElementById("hn-cena").value;
      if (!(cena > 0)) return toast("Podaj cenę.");
      if (N.widelki && (cena < N.widelki[0] || cena > N.widelki[1])) return toast(widelkiTekst(N.widelki));
      zamknijOkno();
      await c.zmien((d) => {
        const o = d.handel_oferty[i];
        o.ceny = [...(o.ceny || [o.cena]), cena];
        o.cena = cena;
        delete o.przyjmij_kontre;
      });
    },
    "hd-przyjmij": (el, c) => {
      const H = c.v.handel;
      const o = H.przychodzace.find((x) => x.id === el.dataset.id);
      if (o.typ !== "sprzet") return c.zmien((d) => { (d.handel_przyjmij = d.handel_przyjmij || []).push({ id: o.id }); });
      const wolne = H.stanowiska.filter((s) => s.typ === o.stanowisko && !s.sprzet.includes(o.nazwa));
      if (!wolne.length) return toast(`Nie masz stanowiska (${o.stanowisko}) bez ${o.nazwa} – kup najpierw stanowisko.`);
      okno(`Przyjmij: ${o.co}`, `<label class="pole">Stanowisko<select id="hd-nr">${wolne.map((s) =>
        `<option value="${s.nr}">${esc(s.typ)} ${s.nr}</option>`).join("")}</select></label>
        <p class="podpowiedz">Cena ${zl2(o.cena)} (w tym VAT ${zl2(o.vat)}). Sprzęt kupiony w tej rundzie zajmuje stanowisko
        dopiero po przeliczeniu – wybierz stanowisko, na którym go nie będzie.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hd-przyjmij-ok" data-id="${esc(o.id)}">Przyjmij</button>` });
    },
    "hd-przyjmij-ok": async (el, c) => {
      const nr = +document.getElementById("hd-nr").value;
      zamknijOkno();
      await c.zmien((d) => { (d.handel_przyjmij = d.handel_przyjmij || []).push({ id: el.dataset.id, nr }); });
    },
    "hd-odrzuc": (el, c) => c.zmien((d) => { d.handel_przyjmij = (d.handel_przyjmij || []).filter((p) => p.id !== el.dataset.id); }),
    "hd-usun": (el, c) => c.zmien((d) => { d.handel_oferty.splice(+el.dataset.i, 1); }),
    "hd-towar": (el, c) => {
      const H = c.v.handel;
      okno("Sprzedaj towar innej drużynie", `<label class="pole">Drużyna<select id="hd-do">${H.druzyny.map((x) =>
        `<option value="${esc(x.nazwa)}">${esc(x.wyswietlana)}</option>`).join("")}</select></label>
        <label class="pole">Towar<select id="hd-co">${H.towary.map((t, i) => `<option value="${i}">${esc(t.zasob)} ${t.jakosc}★ – ${t.ilosc} opak.
          (koszt ${zl2(t.wartosc)}/opak.${t.termin ? `, termin ${esc(t.termin)}` : ""})</option>`).join("")}</select></label>
        <label class="pole">Ilość opakowań<input type="number" id="hd-ilosc" min="0.1" step="1" value="10"></label>
        <label class="pole">Cena brutto za całość<input type="number" id="hd-cena" min="0.01" step="10"></label>
        <p class="podpowiedz">Stan magazynu z początku rundy – oferta przejdzie, jeśli towaru wystarczy na koniec rundy.
        Cena: ${proc(H.limity.cena_min)}–${proc(H.limity.cena_maks)} kosztu zakupu.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hd-towar-ok">Wystaw ofertę</button>` });
    },
    "hd-towar-ok": async (el, c) => {
      const t = c.v.handel.towary[+document.getElementById("hd-co").value];
      const ilosc = +document.getElementById("hd-ilosc").value, cena = +document.getElementById("hd-cena").value;
      if (!(ilosc > 0) || !(cena > 0)) return toast("Podaj ilość i cenę.");
      const doKogo = document.getElementById("hd-do").value;
      zamknijOkno();
      await c.zmien((d) => { (d.handel_oferty = d.handel_oferty || []).push({ klucz: nowyKlucz(), do: doKogo, typ: "towar", zasob: t.zasob, jakosc: t.jakosc, ilosc, cena, ceny: [cena] }); });
    },
    "hd-sprzet": (el, c) => {
      const H = c.v.handel;
      okno("Sprzedaj sprzęt innej drużynie", `<label class="pole">Drużyna<select id="hd-do">${H.druzyny.map((x) =>
        `<option value="${esc(x.nazwa)}">${esc(x.wyswietlana)}</option>`).join("")}</select></label>
        <label class="pole">Sprzęt<select id="hd-co">${H.sprzet.map((s, i) => `<option value="${i}">${esc(s.nazwa)} ${s.jakosc}★
          (${esc(s.stanowisko)} ${s.nr}, katalog ${zl2(s.katalog)})</option>`).join("")}</select></label>
        <label class="pole">Cena brutto<input type="number" id="hd-cena" min="0.01" step="50"></label>
        <p class="podpowiedz">Cena: ${proc(H.limity.cena_min)}–${proc(H.limity.cena_maks)} ceny katalogowej. Do przyjęcia
        oferty sprzęt zostaje u ciebie i pracuje.</p>`,
      { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="hd-sprzet-ok">Wystaw ofertę</button>` });
    },
    "hd-sprzet-ok": async (el, c) => {
      const s = c.v.handel.sprzet[+document.getElementById("hd-co").value];
      const cena = +document.getElementById("hd-cena").value;
      if (!(cena > 0)) return toast("Podaj cenę.");
      const doKogo = document.getElementById("hd-do").value;
      zamknijOkno();
      await c.zmien((d) => { (d.handel_oferty = d.handel_oferty || []).push({ klucz: nowyKlucz(), do: doKogo, typ: "sprzet", stanowisko: s.stanowisko, nr: s.nr, nazwa: s.nazwa, cena, ceny: [cena] }); });
    },
  },
};
