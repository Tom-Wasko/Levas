// Oferta: wybór usług i prognoza popytu.
import { esc, gw, licz, nazwaUslugi, okno, tabela, toast, wykres, zl } from "./wspolne.js";

const KATEGORIE = ["Zajęcia grupowe", "Trening personalny", "Trening siłowy"];
const JAK = { 1: "Niska", 2: "Średnia", 3: "Wysoka" };

function sezon(u, miesiac) {
  const max = Math.max(...u.sezonowosc);
  return `<div class="sezon" title="Sezonowość (styczeń–grudzień)">${u.sezonowosc.map((s, i) =>
    `<i class="${i === miesiac ? "ten" : ""}" style="height:${Math.round((s / max) * 22)}px"></i>`).join("")}</div>`;
}

export const prognozaBazowa = (u, miesiac) => Math.round((u.popyt_roczny / 12) * u.sezonowosc[miesiac]);
const limitNowych = (kat, r) => r === 1 ? kat.oferty.rundy.uslugi_w_rundzie_1
  : r >= kat.oferty.rundy.nowe_uslugi_od_rundy ? kat.oferty.rundy.nowe_uslugi_na_runde : 0;

export const oferta = {
  tytul: "Oferta", ikona: "⚑", odblokowanie: "oferta",
  info: ({ v, kat }) => v.runda === 1
    ? `Wybierz usługi, które chcesz świadczyć w Twojej firmie i określ ich popyt miesięczny. W pierwszej rundzie można wybrać tylko ${kat.oferty.rundy.uslugi_startowe.map((u) => nazwaUslugi(kat, u)).join(", ")}.`
    : v.runda < kat.oferty.rundy.nowe_uslugi_od_rundy ? "W rundzie 2 sprzedajesz usługi wybrane w rundzie 1. Nowe usługi można dodawać od rundy 3."
    : `Wybierz usługi, które chcesz świadczyć w Twojej firmie i określ ich popyt miesięczny. W każdej rundzie będzie można uruchamiać maksymalnie ${kat.oferty.rundy.nowe_uslugi_na_runde} nowe usługi.`,
  decyzje({ v, kat, edycja }) {
    const wybrane = v.stan.oferta, przed = v.stan_przed.oferta, r = v.runda;
    const m = r === 1 ? 1 : r - 1;
    const limit = limitNowych(kat, r);
    const nowe = Object.keys(wybrane).filter((u) => !(u in przed)).length;
    let html = `<div class="komunikat">Nowe usługi w tej rundzie: <b>${nowe} / ${limit}</b>. Prognozowany popyt = popyt roczny / 12 × sezonowość
      (${r === 1 ? "prognoza na luty – sprzedaż zaczyna się w rundzie 2" : `miesiąc: ${v.miesiac}`}).</div>`;
    for (const k of KATEGORIE) {
      const uslugi = Object.entries(kat.uslugi).filter(([, u]) => u.kategoria === k);
      html += `<div class="pasek">${k}</div><div class="siatka trojka">`;
      for (const [klucz, u] of uslugi) {
        const jest = klucz in wybrane;
        const dozwolona = (r > 1 || kat.oferty.rundy.uslugi_startowe.includes(klucz)) && (klucz in przed || nowe < limit || jest);
        const baza = prognozaBazowa(u, m);
        html += `<div class="kafel ${jest ? "wybrany" : ""}">
          <div class="kg"><span>${esc(u.nazwa)}<br><span class="podpowiedz">(wejście jednorazowe)</span></span>${sezon(u, m)}</div>
          <div class="kt">
            <div class="wiersz"><span>Popyt roczny</span><span>${licz(u.popyt_roczny)}</span></div>
            <div class="wiersz"><span>Preferowana cena</span><span>${zl(u.cena_preferowana)}</span></div>
            <div class="wiersz"><span>Liczba godzin instruktora/trenera</span><span>${u.godziny_prowadzacego} H</span></div>
            <div class="wiersz"><span>Liczba godzin recepcjonisty</span><span>${u.godziny_recepcji} H</span></div>
            ${u.grupa > 1 ? `<div class="wiersz"><span>Liczba osób w grupie</span><span>${u.grupa}</span></div>` : ""}
            <div class="wiersz"><span>Prowadzący</span><span>${esc(u.prowadzacy)}</span></div>
          </div>
          <div class="kd">
            <button class="btn pom" data-akcja="szczegoly-uslugi" data-u="${klucz}">Więcej szczegółów</button>
            ${jest ? `<button class="btn zielony" data-akcja="usluga" data-u="${klucz}" ${edycja ? "" : "disabled"}>✓ Wybrano</button>`
                   : `<button class="btn czarny" data-akcja="usluga" data-u="${klucz}" ${edycja && dozwolona ? "" : "disabled"}>Wybierz</button>`}
            ${jest ? `<label class="pole">Prognozowany popyt (na miesiąc)
              <input type="number" min="0" step="1" value="${wybrane[klucz] || ""}" placeholder="${baza}" data-zmiana="prognoza" data-u="${klucz}" ${edycja ? "" : "disabled"}>
              <span class="podpowiedz">Wg wzoru: ${licz(u.popyt_roczny)} / 12 × ${u.sezonowosc[m]} ≈ ${baza}</span></label>` : ""}
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
    return `${tabela("Prognozowany popyt vs popyt", ["Nazwa usługi", "Prognozowany popyt (na miesiąc)", "Popyt", "Różnica"], w, { klasy: ["l"] })}
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
      const sprzet = u.sprzet.map((n) => [esc(n), "Instruktor/Trener", "100%", ...[1, 2, 3].map((q) => zl(kat.sprzet[n].ceny[q]))]);
      const pensje = [[esc(u.prowadzacy), "100%", ...["niska", "srednia", "wysoka"].map((q) => zl(u.pensje_rynkowe[q]))]];
      const zasoby = Object.entries(u.zasoby).map(([n, ile]) => {
        const z = kat.zasoby[n];
        return [esc(n), `${ile} ${z.jednostka}`, `${z.typ_opakowania} (${licz(z.opakowanie)} ${z.jednostka})`,
          ...[1, 2, 3].map((q) => zl(z.srednie_ceny[q], true))];
      });
      okno(`Wymagania dotyczące usługi – ${esc(u.nazwa)}`,
        tabela("Sprzęt", ["Nazwa", "Dla", "Zapotrzebowanie", "★ Niska", "★★ Średnia", "★★★ Wysoka"], sprzet, { klasy: ["l"] })
        + tabela("Pracownicy", ["Typ", "Zaangażowanie", "Wynagrodzenie ★", "★★", "★★★"], pensje, { klasy: ["l"] })
        + tabela("Zasoby na klienta", ["Nazwa", "Zapotrzebowanie na klienta", "Opakowanie", "Średnia cena ★", "★★", "★★★"], zasoby, { klasy: ["l"] })
        + `<p class="podpowiedz">Recepcja: ${u.godziny_recepcji} h na klienta, recepcjonista z kompletem sprzętu recepcji (${kat.sprzet_recepcji.join(", ")}).
           Dokładne ceny zasobów są w zakładce Dostawcy.</p>`);
    },
    usluga: async (el, c) => {
      const u = el.dataset.u, r = c.v.runda;
      const of = { ...c.v.stan.oferta };
      if (u in of) delete of[u];
      else {
        const limit = limitNowych(c.kat, r);
        // limit dotyczy przyrostu liczby usług (usunięta usługa zwalnia miejsce na nową)
        const przyrost = Object.keys(of).length - Object.keys(c.v.stan_przed.oferta).length;
        if (!(u in c.v.stan_przed.oferta) && przyrost >= limit) return toast(`W tej rundzie liczba usług może wzrosnąć najwyżej o ${limit}.`);
        of[u] = prognozaBazowa(c.kat.uslugi[u], r === 1 ? 1 : r - 1);
      }
      await c.zmien((d) => { d.oferta = of; });
    },
  },
  zmiany: {
    prognoza: async (el, c) => c.zmien((d) => { d.oferta = { ...c.v.stan.oferta, [el.dataset.u]: Math.max(0, Math.round(+el.value || 0)) }; }),
  },
};

export { JAK, gw };
