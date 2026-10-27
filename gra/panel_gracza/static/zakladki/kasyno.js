// Adres z wizytówki (silnik/kasyno.py): zakładka widoczna tylko w rundzie z zaproszeniem albo z wynikami gier.
// Decyzja `kasyno`: lista {gra, zaklad, stawka} – stawki z portfela właściciela, wynik dopiero po zamknięciu rundy.
import { esc, tabela, toast, zl2 } from "./wspolne.js";

function zakladyHtml(Z, edycja) {
  if (!Z?.zaklady?.length) return "";
  const wiersze = Z.zaklady.map((z, i) => [esc(z.nazwa), z.zaklad_nazwa ? esc(z.zaklad_nazwa) : "–", zl2(z.stawka),
    Z.ukryte ? `<span class="podpowiedz">wynik po zamknięciu rundy</span>`
      : `<span class="${z.wyplata ? "plus" : "minus"}">${zl2(z.wyplata)}</span>`,
    edycja ? `<button class="btn jasny" data-akcja="ks-usun" data-i="${i}">Wycofaj</button>` : ""]);
  return tabela(Z.ukryte ? "Postawione zakłady" : "Zakłady", ["Gra", "Zakład", "Stawka", "Wypłata", ""], wiersze,
    { klasy: ["l", "l"], sortuj: false, stopka: ["Razem", "", zl2(Z.stawki), Z.ukryte ? "" : zl2(Z.wyplaty), ""] });
}

function odrzuconeHtml(Z) {
  return (Z?.odrzucone || []).map((o) => `<p class="minus">${esc(o.co)}: ${esc(o.powod)}.</p>`).join("");
}

function grafHtml(id, g, L) {
  const stawka = `<label class="pole">Stawka<input type="number" id="ks-stawka-${esc(id)}" min="${L.min_stawka}" max="${L.maks_stawka}" step="10" value="${L.min_stawka * 5}"></label>`;
  const wybor = g.typ === "ruletka" ? `<label class="pole">Zakład<select id="ks-zaklad-${esc(id)}">${Object.entries(g.zaklady)
    .map(([k, z]) => `<option value="${esc(k)}">${esc(z.nazwa)} (×${String(z.mnoznik).replace(".", ",")})</option>`).join("")}</select></label>` : "";
  return `<div class="kafel"><div class="kg">${esc(g.nazwa)}</div><div class="kt"><p>${esc(g.opis)}</p>
    <div class="przyciski">${wybor}${stawka}<button class="btn" data-akcja="ks-postaw" data-g="${esc(id)}">${g.typ === "ruletka" ? "Postaw" : "Pociągnij za wajchę"}</button></div></div></div>`;
}

export const kasyno = {
  tytul: "Nocna 13", tytulPelny: "ul. Nocna 13, wejście od podwórza", ikona: "klucz", odblokowanie: (v) => !!v.kasyno, ukryta: (v) => !v.kasyno,
  info: `Adres z tajemniczej wizytówki. Drzwi są otwarte tylko w tej jednej rundzie. Gra się prywatnymi pieniędzmi
    z <a data-zakladka-k="wlasciciel">portfela właściciela</a> – firma nic o tym nie wie, chyba że wpłacisz do niej wygraną.`,
  decyzje({ v, d, edycja }) {
    const K = v.kasyno;
    if (!K) return `<p class="podpowiedz">Brak danych.</p>`;
    if (!K.otwarte) return `<div class="karta"><p>Pod adresem ${esc(K.adres)} drzwi są zamknięte. Na dzwonek nikt nie odpowiada,
      a kot z parteru patrzy na ciebie z wyższością. Wyniki ostatniej wizyty są w zakładce Wyniki.</p></div>`;
    const L = K.limity, D = K.decyzja, W = v.wlasciciel;
    const ile = (d.kasyno || []).length;
    return `<div class="karta"><p>${esc(K.zaproszenie)}</p></div>
      <div class="karta"><h3>${esc(K.klub.nazwa)}</h3><p>${esc(K.klub.tekst)}</p></div>
      ${W ? `<div class="pasek ciemny"><span>W portfelu na początku rundy: <span class="kwota">${zl2(W.portfel_przed)}</span></span>
        ${D ? `<span>Po stawkach: <span class="kwota">${zl2(W.portfel_po)}</span></span>` : ""}</div>` : ""}`
      + zakladyHtml(D, edycja) + odrzuconeHtml(D)
      + (edycja && ile < L.maks ? Object.entries(K.gry).map(([id, g]) => grafHtml(id, g, L)).join("") : "")
      + `<p class="podpowiedz">Najwyżej ${L.maks} zakładów w rundzie, stawka od ${zl2(L.min_stawka)} do ${zl2(L.maks_stawka)}.
        Stawki schodzą z portfela właściciela, a pan Waldemar ogłasza wyniki dopiero po zamknięciu rundy. Wygraną możesz
        w następnej rundzie wpłacić do firmy – albo zostawić w portfelu na czarną godzinę.</p>`;
  },
  wyniki({ v }) {
    const Z = v.wyniki?.kasyno?.gry;
    if (!Z) return `<p class="podpowiedz">W poprzedniej rundzie nie było cię pod tym adresem.</p>`;
    const teksty = (Z.zaklady || []).map((z) => `<div class="kafel"><div class="kg">${esc(z.nazwa)}${z.zaklad_nazwa ? ` – ${esc(z.zaklad_nazwa)}` : ""}:
      ${zl2(z.stawka)}</div><div class="kt"><p>${esc(z.tekst)}</p></div></div>`).join("");
    return zakladyHtml(Z, false) + teksty + odrzuconeHtml(Z)
      + (Z.zaklady?.length ? `<div class="pasek ciemny"><span>Bilans wieczoru: <span class="kwota ${Z.bilans < 0 ? "minus" : "plus"}">${zl2(Z.bilans)}</span></span></div>` : "");
  },
  akcje: {
    "ks-postaw": async (el, c) => {
      const id = el.dataset.g, L = c.v.kasyno.limity;
      const stawka = +document.getElementById(`ks-stawka-${id}`).value;
      if (!(stawka >= L.min_stawka && stawka <= L.maks_stawka)) return toast(`Stawka od ${zl2(L.min_stawka)} do ${zl2(L.maks_stawka)}.`);
      const zaklad = document.getElementById(`ks-zaklad-${id}`)?.value ?? null;
      await c.zmien((d) => { d.kasyno = [...(d.kasyno || []), { gra: id, zaklad, stawka }]; });
    },
    "ks-usun": (el, c) => c.zmien((d) => {
      d.kasyno = (d.kasyno || []).filter((_, i) => i !== +el.dataset.i);
      if (!d.kasyno.length) delete d.kasyno;
    }),
  },
};
