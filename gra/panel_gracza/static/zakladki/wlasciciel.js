// Portfel właściciela (gra z lokalami, silnik/pieniadze/wlasciciel.py): wypłata własna z firmy i wpłata własna do firmy – poza KPiR.
// Decyzje `wyplata_wlasna` i `wplata_wlasna` (kwoty); kolejność: wypłata → wydatki prywatne → wpłata.
import { esc, okno, tabela, toast, zamknijOkno, zl2 } from "./wspolne.js";

function odrzuconeHtml(D) {
  return (D?.odrzucone || []).map((o) => `<p class="minus">${esc(o.co)}: ${esc(o.powod)}.</p>`).join("");
}

function ruchyHtml(D, tytul) {
  if (!D || (!D.wyplata && !D.wplata)) return "";
  const w = [];
  if (D.wyplata) w.push(["Wypłata własna z firmy do portfela", `<span class="plus">${zl2(D.wyplata)}</span>`, `<span class="minus">${zl2(-D.wyplata)}</span>`]);
  if (D.wplata) w.push(["Wpłata własna z portfela do firmy", `<span class="minus">${zl2(-D.wplata)}</span>`, `<span class="plus">${zl2(D.wplata)}</span>`]);
  return tabela(tytul, ["Operacja", "Portfel", "Konto firmy"], w, { klasy: ["l"], sortuj: false });
}

export const wlasciciel = {
  tytul: "Portfel właściciela", ikona: "portfel", odblokowanie: (v) => !!v.wlasciciel, ukryta: (v) => !v.wlasciciel,
  info: `Firma to nie skarbonka właściciela – ale w jednoosobowej działalności można z niej wypłacić pieniądze na własne
    potrzeby albo dołożyć do niej własne oszczędności. Wypłata i wpłata własna są poza KPiR: nie są kosztem ani przychodem,
    nie zmieniają podatku i widać je tylko na koncie firmy. Pieniądze w portfelu nie liczą się do wyniku firmy.`,
  decyzje({ v, d, edycja }) {
    const W = v.wlasciciel;
    if (!W) return `<p class="podpowiedz">Brak danych.</p>`;
    const D = W.decyzja;
    const wiersze = [];
    if (d.wyplata_wlasna) wiersze.push([`Wypłata własna ${zl2(d.wyplata_wlasna)}`, "z konta firmy do portfela",
      edycja ? `<button class="btn jasny" data-akcja="wl-usun" data-k="wyplata_wlasna">Usuń</button>` : ""]);
    if (d.wplata_wlasna) wiersze.push([`Wpłata własna ${zl2(d.wplata_wlasna)}`, "z portfela na konto firmy",
      edycja ? `<button class="btn jasny" data-akcja="wl-usun" data-k="wplata_wlasna">Usuń</button>` : ""]);
    return `<div class="karta"><p>Prywatny portfel właściciela: trochę oszczędności, paragon z kebaba sprzed miesiąca i zdjęcie
        kota kierownika „na szczęście”. Wszystko, co tu jest, należy do ciebie, a nie do firmy.</p></div>
      <div class="pasek ciemny"><span>W portfelu na początku rundy: <span class="kwota">${zl2(W.portfel_przed)}</span></span>
        <span>Na koncie firmy: <span class="kwota">${zl2(W.gotowka_firmy)}</span></span>
        ${D ? `<span>W portfelu po decyzjach: <span class="kwota">${zl2(W.portfel_po)}</span></span>` : ""}</div>`
      + (wiersze.length ? tabela("Decyzje w tej rundzie", ["Co", "Kierunek", ""], wiersze, { klasy: ["l", "l"], sortuj: false }) : "")
      + odrzuconeHtml(D)
      + (edycja ? `<div class="przyciski">${d.wyplata_wlasna ? "" : `<button class="btn" data-akcja="wl-wyplata">Wypłać z firmy</button>`}
          ${d.wplata_wlasna ? "" : `<button class="btn" data-akcja="wl-wplata">Wpłać do firmy</button>`}</div>` : "")
      + `<p class="podpowiedz">Kolejność na początku rundy: najpierw wypłata własna (najwyżej tyle, ile jest na koncie firmy),
        potem wydatki prywatne, na końcu wpłata własna (najwyżej tyle, ile jest w portfelu). Wpłacone pieniądze firma może
        wydać już w tej rundzie.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.wlasciciel;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
    return ruchyHtml(W, "Portfel właściciela w rundzie") + odrzuconeHtml(W)
      + `<div class="pasek ciemny"><span>W portfelu na koniec rundy: <span class="kwota">${zl2(W.portfel)}</span></span></div>`
      + (!W.wyplata && !W.wplata ? `<p class="podpowiedz">W tej rundzie nie było wpłat ani wypłat własnych.</p>` : "");
  },
  akcje: {
    "wl-wyplata": (el, c) => okno("Wypłata własna", `<label class="pole">Kwota<input type="number" id="wl-kwota" min="1" step="100" value="500"></label>
      <p class="podpowiedz">Na koncie firmy: ${zl2(c.v.wlasciciel.gotowka_firmy)}. Wypłata nie jest kosztem – podatek się nie zmienia.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="wl-ok" data-k="wyplata_wlasna">Wypłać</button>` }),
    "wl-wplata": (el, c) => okno("Wpłata własna", `<label class="pole">Kwota<input type="number" id="wl-kwota" min="1" step="100" value="${Math.floor(c.v.wlasciciel.portfel_przed)}"></label>
      <p class="podpowiedz">W portfelu: ${zl2(c.v.wlasciciel.portfel_przed)}. Wpłata nie jest przychodem – podatek się nie zmienia.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Zamknij</button><button class="btn zielony" data-akcja="wl-ok" data-k="wplata_wlasna">Wpłać</button>` }),
    "wl-ok": async (el, c) => {
      const kwota = +document.getElementById("wl-kwota").value;
      if (!(kwota > 0)) return toast("Podaj kwotę.");
      zamknijOkno();
      await c.zmien((d) => { d[el.dataset.k] = kwota; });
    },
    "wl-usun": (el, c) => c.zmien((d) => { delete d[el.dataset.k]; }),
  },
};
