// Oferta: wybór dań (menu) i prognoza popytu.
import { esc, gw, licz, miesiacRundy, nazwaRundy, nazwaUslugi, OKRES, okno, tabela, toast, wykres, zl } from "./wspolne.js";

const kategorie = (kat) => [...new Set(Object.values(kat.uslugi).map((u) => u.kategoria))];  // kolejność jak w uslugi.yaml
const JAK = { 1: "Niska", 2: "Średnia", 3: "Wysoka" };

function sezon(u, miesiac) {
  const max = Math.max(...u.sezonowosc);
  return `<div class="sezon" title="Sezonowość (styczeń–grudzień)">${u.sezonowosc.map((s, i) =>
    `<i class="${i === miesiac ? "ten" : ""}" style="height:${Math.round((s / max) * 22)}px"></i>`).join("")}</div>`;
}

export const prognozaBazowa = (u, miesiac) => Math.round((u.popyt_roczny / OKRES.rund_w_roku) * u.sezonowosc[miesiac]);
// gra z lokalami: prognoza popytu strefowego dla lokali firmy (v.popyt, silnik/popyt.py); bez lokalu – 0
const prognozaStrefowa = (v, klucz) => Math.round(v.popyt.prognoza.dania[klucz] || 0);
const prognozaDania = (v, kat, klucz, m) => v.popyt ? prognozaStrefowa(v, klucz) : prognozaBazowa(kat.uslugi[klucz], m);
// miesiąc (sezonowość), w którym sprzedaje się dania wybrane w rundzie r – runda 1 przygotowuje sprzedaż w rundzie 2
const miesiacSprzedazy = (r) => miesiacRundy(Math.max(r, 2));
const popytOkresu = () => `popyt ${OKRES.przymiotnik.toLowerCase()}`;
const limitNowych = (kat, r) => r === 1 ? kat.oferty.rundy.uslugi_w_rundzie_1
  : r >= kat.oferty.rundy.nowe_uslugi_od_rundy ? kat.oferty.rundy.nowe_uslugi_na_runde : 0;

export const oferta = {
  tytul: "Menu", tytulPelny: "Menu – dania, ceny i prognoza", ikona: "⚑", odblokowanie: "oferta",
  info: ({ v, kat }) => v.runda === 1
    ? `Wybierz dania do menu i określ ich ${popytOkresu()}. W pierwszej rundzie można wybrać tylko ${kat.oferty.rundy.uslugi_startowe.map((u) => nazwaUslugi(kat, u)).join(", ")}.`
    : v.runda < kat.oferty.rundy.nowe_uslugi_od_rundy ? "W rundzie 2 sprzedajesz dania wybrane w rundzie 1. Nowe dania można dodawać od rundy 3."
    : `Wybierz dania do menu i określ ich ${popytOkresu()}. W każdej rundzie będzie można uruchamiać maksymalnie ${kat.oferty.rundy.nowe_uslugi_na_runde} nowe dania.`,
  decyzje({ v, kat, edycja }) {
    const wybrane = v.stan.oferta, przed = v.stan_przed.oferta, r = v.runda;
    const m = miesiacSprzedazy(r);
    const limit = limitNowych(kat, r);
    const nowe = Object.keys(wybrane).filter((u) => !(u in przed)).length;
    const okres = r === 1 ? `prognoza na ${esc(nazwaRundy(2))} – sprzedaż zaczyna się w rundzie 2` : esc(v.miesiac);
    let html = `<div class="komunikat">Nowe dania w tej rundzie: <b>${nowe} / ${limit}</b>. ${v.popyt
      ? `Podpowiedź prognozy – klienci stref, którzy wybraliby Twoje lokale przy obecnych cenach konkurencji (${okres}); szczegóły w zakładce <a data-zakladka-k="klienci">Klienci i strefy</a>.`
      : `Prognozowany popyt = popyt roczny / ${OKRES.rund_w_roku} × sezonowość (${okres}).`}</div>`;
    for (const k of kategorie(kat)) {
      const uslugi = Object.entries(kat.uslugi).filter(([, u]) => u.kategoria === k);
      html += `<div class="pasek">${k}</div><div class="siatka trojka">`;
      for (const [klucz, u] of uslugi) {
        const jest = klucz in wybrane;
        const dozwolona = (r > 1 || kat.oferty.rundy.uslugi_startowe.includes(klucz)) && (klucz in przed || nowe < limit || jest);
        const baza = prognozaDania(v, kat, klucz, m);
        html += `<div class="kafel ${jest ? "wybrany" : ""}">
          <div class="kg"><span>${esc(u.nazwa)}<br><span class="podpowiedz">(porcja)</span></span>${sezon(u, m)}</div>
          <div class="kt">
            <div class="wiersz"><span>Popyt roczny</span><span>${licz(u.popyt_roczny)}</span></div>
            <div class="wiersz"><span>Preferowana cena</span><span>${zl(u.cena_preferowana)}</span></div>
            <div class="wiersz"><span>Czas przygotowania</span><span>${Math.round(u.godziny_prowadzacego * 600) / 10} min</span></div>
            <div class="wiersz"><span>Czas obsługi przy kasie</span><span>${Math.round(u.godziny_kasy * 600) / 10} min</span></div>
            ${u.grupa > 1 ? `<div class="wiersz"><span>Porcji naraz</span><span>${u.grupa}</span></div>` : ""}
            <div class="wiersz"><span>Przygotowuje</span><span>${esc(u.prowadzacy)}</span></div>
          </div>
          <div class="kd">
            <button class="btn pom" data-akcja="szczegoly-uslugi" data-u="${klucz}">Więcej szczegółów</button>
            ${jest ? `<button class="btn zielony" data-akcja="usluga" data-u="${klucz}" ${edycja ? "" : "disabled"}>✓ Wybrano</button>`
                   : `<button class="btn czarny" data-akcja="usluga" data-u="${klucz}" ${edycja && dozwolona ? "" : "disabled"}>Wybierz</button>`}
            ${jest ? `<label class="pole">Prognozowany popyt (na ${OKRES.mianownik})
              <input type="number" min="0" step="1" value="${wybrane[klucz] || ""}" placeholder="${baza}" data-zmiana="prognoza" data-u="${klucz}" ${edycja ? "" : "disabled"}>
              <span class="podpowiedz">${v.popyt ? `Klienci stref dla Twoich lokali ≈ ${licz(baza)}`
                : `Wg wzoru: ${licz(u.popyt_roczny)} / ${OKRES.rund_w_roku} × ${u.sezonowosc[m]} ≈ ${baza}`}</span></label>` : ""}
          </div></div>`;
      }
      html += `</div>`;
    }
    return html;
  },
  wyniki({ v, kat }) {
    const sp = v.wyniki?.sprzedaz || {};
    const w = Object.entries(sp).map(([u, s]) => [esc(nazwaUslugi(kat, u)), licz(s.prognoza), licz(s.popyt),
      s.popyt > s.prognoza ? `<span class="plus">+${licz(s.popyt - s.prognoza)}</span>` : `<span class="minus">${licz(s.popyt - s.prognoza)}</span>`]);
    return `${tabela("Prognozowany popyt vs popyt", ["Danie", `Prognozowany popyt (na ${OKRES.mianownik})`, "Popyt", "Różnica"], w, { klasy: ["l"] })}
      <div class="wykres"><canvas id="w-prognoza"></canvas></div>`;
  },
  po({ v, kat }, tryb) {
    if (tryb !== "wyniki") return;
    const sp = v.wyniki?.sprzedaz || {};
    const u = Object.keys(sp);
    wykres("w-prognoza", "bar", u.map((x) => nazwaUslugi(kat, x)), [{ label: "Prognozowany popyt", data: u.map((x) => sp[x].prognoza) },
      { label: "Popyt", data: u.map((x) => sp[x].popyt) }]);
  },
  akcje: {
    "szczegoly-uslugi": (el, { kat }) => {
      const u = kat.uslugi[el.dataset.u];
      const sprzet = u.sprzet.map((n) => [esc(n), esc(kat.oferty.stanowiska.typy.kuchnia.kto), "100%", ...[1, 2, 3].map((q) => zl(kat.sprzet[n].ceny[q]))]);
      const pensje = [[esc(u.prowadzacy), "100%", ...["niska", "srednia", "wysoka"].map((q) => zl(u.pensje_rynkowe[q]))]];
      const zasoby = Object.entries(u.zasoby).map(([n, ile]) => {
        const z = kat.zasoby[n];
        return [esc(n), `${ile} ${z.jednostka}`, `${z.typ_opakowania} (${licz(z.opakowanie)} ${z.jednostka})`,
          ...[1, 2, 3].map((q) => zl(z.srednie_ceny[q], true))];
      });
      okno(`Wymagania dotyczące dania – ${esc(u.nazwa)}`,
        tabela("Sprzęt", ["Nazwa", "Dla", "Zapotrzebowanie", "★ Niska", "★★ Średnia", "★★★ Wysoka"], sprzet, { klasy: ["l"] })
        + tabela("Pracownicy", ["Typ", "Zaangażowanie", "Wynagrodzenie ★", "★★", "★★★"], pensje, { klasy: ["l"] })
        + tabela("Składniki na porcję", ["Nazwa", "Zużycie na porcję", "Opakowanie", "Średnia cena ★", "★★", "★★★"], zasoby, { klasy: ["l"] })
        + `<p class="podpowiedz">${esc(kat.oferty.stanowiska.typy.kasa.kto)}: ${u.godziny_kasy} h na klienta, pracownik z kompletem sprzętu
           (${kat.sprzet_kasy.map(esc).join(", ")}). Dokładne ceny składników są w zakładce Dostawcy.</p>`);
    },
    usluga: async (el, c) => {
      const u = el.dataset.u, r = c.v.runda;
      const of = { ...c.v.stan.oferta };
      if (u in of) delete of[u];
      else {
        const limit = limitNowych(c.kat, r);
        // limit dotyczy przyrostu liczby dań (usunięte danie zwalnia miejsce na nowe)
        const przyrost = Object.keys(of).length - Object.keys(c.v.stan_przed.oferta).length;
        if (!(u in c.v.stan_przed.oferta) && przyrost >= limit) return toast(`W tej rundzie liczba dań może wzrosnąć najwyżej o ${limit}.`);
        of[u] = prognozaDania(c.v, c.kat, u, miesiacSprzedazy(r));
      }
      await c.zmien((d) => { d.oferta = of; });
    },
  },
  zmiany: {
    prognoza: async (el, c) => c.zmien((d) => { d.oferta = { ...c.v.stan.oferta, [el.dataset.u]: Math.max(0, Math.round(+el.value || 0)) }; }),
  },
};

export { JAK, gw };
