// Oferta: wybór dań (menu), prognoza popytu i cena – wybrane danie jest w sprzedaży (silnik: _ceny_domyslne).
import { esc, gw, licz, miesiacRundy, nazwaRundy, nazwaUslugi, OKRES, okno, proc, tabela, toast, wykres, zl, zl2 } from "./wspolne.js";
import { kolko } from "./dymki.js";
import { cenyLokalu, lokalWybrany, menuLokalu, nazwaLokalu, wieleLokali, zapiszWLokalu } from "./lokal_wybor.js";
import { widelki } from "./sprzedaz.js";

const kategorie = (kat) => [...new Set(Object.values(kat.uslugi).map((u) => u.kategoria))];  // kolejność jak w uslugi.yaml
const JAK = { 1: "Niska", 2: "Średnia", 3: "Wysoka" };

export const prognozaBazowa = (u, miesiac) => Math.round((u.popyt_roczny / OKRES.rund_w_roku) * u.sezonowosc[miesiac]);
// gra z lokalami: bez podpowiedzi – popyt drużyna liczy sama z pul klientów stref (zakładka Klienci i strefy)
const prognozaDania = (v, kat, klucz, m) => v.popyt ? 0 : prognozaBazowa(kat.uslugi[klucz], m);
// miesiąc (sezonowość), w którym sprzedaje się dania wybrane w rundzie r – runda 1 przygotowuje sprzedaż w rundzie 2
const miesiacSprzedazy = (r) => miesiacRundy(Math.max(r, 2));
const popytOkresu = () => `popyt ${OKRES.przymiotnik.toLowerCase()}`;
const MIESIACE = ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"];
const sprzedazOtwarta = (v) => v.odblokowane.includes("sprzedaz");

// instrukcja liczenia prognozy na rundę (silnik/rynek/popyt.py: pule i udział lokalu)
function jakPrognoza(u, m) {
  const tyg = Math.round(u.popyt_roczny / OKRES.rund_w_roku), sez = u.sezonowosc[m];
  return `<b>Popyt roczny</b> – tyle porcji dania zjadają w roku klienci przeciętnej strefy miasta.<br><b>Jak policzyć prognozę na ${OKRES.mianownik}:</b>
    <br>1. ${licz(u.popyt_roczny)} ÷ ${OKRES.rund_w_roku} ≈ ${licz(tyg)} – przeciętny ${OKRES.mianownik} bez pory roku.
    <br>2. × sezonowość dania w miesiącu sprzedaży (${MIESIACE[m]}: × ${licz(sez, 2)}) ≈ ${licz(Math.round(tyg * sez))}.
    <br>3. × wielkość strefy Twojego lokalu – kolumna „Wielkość strefy” w zakładce Klienci i strefy (z porą roku: np. kampusy pustoszeją w wakacje).
    Wydarzenia w mieście i upodobania grup klientów strefy mogą to podbić albo obniżyć.
    <br>4. × część, którą przyciągniesz: klienci strefy dzielą się między lokale z tym daniem (Twoje i konkurencji) i bary spoza gry.
    Przy cenie i jakości jak u innych dostajesz mniej więcej równą część; niższa cena, lepsza jakość i dobre opinie – więcej. Nowy lokal na początku ma mniej klientów.
    <br>5. Wynik wpisz w pole „Prognozowany popyt”. Z prognozy wychodzą zakupy składników (Zaopatrzenie ▸ Dostawy: „Wpisz wg prognozy”) i potrzebna obsada – za mała to utracona sprzedaż, za duża to zmarnowany towar.`;
}

// cena, rabat i podpowiedzi przy wybranym daniu (dawniej osobna część „Sprzedaż”)
function cenaDania(v, kat, klucz, edycja) {
  const u = kat.uslugi[klucz];
  if (!sprzedazOtwarta(v)) {
    return `<span class="podpowiedz">Cenę ustalisz od rundy, w której zaczyna się sprzedaż – na start danie ma cenę preferowaną ${zl(u.cena_preferowana)}.</span>`;
  }
  const c = cenyLokalu(v, lokalWybrany(v))[klucz] || { cena: u.cena_preferowana, rabat: 0 }, wd = widelki(kat, klucz);
  const inni = Object.entries(v.rynek?.ceny?.[klucz] || {}).filter(([f]) => f !== v.firma).map(([, x]) => x);
  const braki = (v.stan.gotowe_uslugi[klucz] || []).filter((b) => !b.includes("włączona"));
  const dis = edycja ? "" : "disabled";
  return `<div class="pola-dania">
      <label class="pole">Cena (zł)<input type="number" min="${wd ? wd.min : 1}" ${wd ? `max="${wd.max}"` : ""} step="0.5" value="${c.cena}" data-zmiana="cena" data-u="${klucz}" ${dis}></label>
      <label class="pole">Rabat (zł)<input type="number" min="0" step="0.5" value="${c.rabat}" data-zmiana="rabat" data-u="${klucz}" ${dis}></label>
    </div>
    <span class="podpowiedz">Dla klienta: <b>${zl2(c.cena - c.rabat)}</b> (${proc((c.cena - c.rabat) / u.cena_preferowana, 0)} preferowanej)${wd ? ` · dozwolone ${zl2(wd.min)}–${zl2(wd.max)}` : ""}
      · konkurencja: ${inni.length ? `średnio ${zl2(inni.reduce((a, b) => a + b, 0) / inni.length)}` : "brak danych"}</span>
    ${braki.length ? `<span class="podpowiedz" style="color:var(--czerwony)">${braki.map(esc).join("; ")}</span>` : ""}`;
}

const limitNowych = (kat, r) => r === 1 ? kat.oferty.rundy.uslugi_w_rundzie_1
  : r >= kat.oferty.rundy.nowe_uslugi_od_rundy ? kat.oferty.rundy.nowe_uslugi_na_runde : 0;

export const oferta = {
  tytul: "Menu", tytulPelny: "Menu – dania, ceny i prognoza", ikona: "⚑", odblokowanie: "oferta",
  info: ({ v, kat }) => (v.runda === 1
    ? `Wybierz dania do menu i określ ich ${popytOkresu()}. W pierwszej rundzie można wybrać tylko ${kat.oferty.rundy.uslugi_startowe.map((u) => nazwaUslugi(kat, u)).join(", ")}.`
    : v.runda < kat.oferty.rundy.nowe_uslugi_od_rundy ? "W rundzie 2 sprzedajesz dania wybrane w rundzie 1. Nowe dania można dodawać od rundy 3."
    : `Wybierz dania do menu i określ ich ${popytOkresu()}. W każdej rundzie będzie można uruchamiać maksymalnie ${kat.oferty.rundy.nowe_uslugi_na_runde} nowe dania.`)
    + " Danie wybrane do menu jest w sprzedaży – cenę i rabat ustalasz w jego kafelku. Klient płaci cenę pomniejszoną o rabat.",
  decyzje({ v, kat, edycja }) {
    // Z3: przy kilku lokalach – menu wybranego lokalu; limit nowych dań liczony dla całej firmy (suma menu lokali)
    const wybrane = menuLokalu(v, lokalWybrany(v)), przed = v.stan_przed.oferta, r = v.runda;
    const m = miesiacSprzedazy(r);
    const limit = limitNowych(kat, r);
    const nowe = Object.keys(v.stan.oferta).filter((u) => !(u in przed)).length;
    const okres = r === 1 ? `prognoza na ${esc(nazwaRundy(2))} – sprzedaż zaczyna się w rundzie 2` : esc(v.miesiac);
    let html = `${wieleLokali(v) ? `<div class="komunikat ok">Menu lokalu <b>${esc(nazwaLokalu(v, lokalWybrany(v).id))}</b> – prognoza popytu tylko dla tego lokalu.</div>` : ""}
      <div class="komunikat">Nowe dania w tej rundzie (cała firma): <b>${nowe} / ${limit}</b>. ${v.popyt
      ? `Prognozę popytu (${okres}) policz sam – krok po kroku w dymku ⓘ przy „Popyt roczny” w kafelku dania; wielkość stref, konkurencja i dni tygodnia są w zakładce <a data-zakladka-k="klienci">Klienci i strefy</a>.`
      : `Prognozowany popyt = popyt roczny / ${OKRES.rund_w_roku} × sezonowość (${okres}).`}</div>`;
    for (const k of kategorie(kat)) {
      const uslugi = Object.entries(kat.uslugi).filter(([, u]) => u.kategoria === k);
      html += `<div class="pasek">${k}</div><div class="siatka trojka">`;
      for (const [klucz, u] of uslugi) {
        const jest = klucz in wybrane;
        const dozwolona = (r > 1 || kat.oferty.rundy.uslugi_startowe.includes(klucz)) && (klucz in przed || klucz in v.stan.oferta || nowe < limit || jest);
        const baza = prognozaDania(v, kat, klucz, m);
        // U14: czemu „Wybierz” jest wyszarzone – nowe dania dopiero od rundy nowe_uslugi_od_rundy albo limit wyczerpany
        const od = kat.oferty.rundy.nowe_uslugi_od_rundy;
        const czemu = !edycja || dozwolona || jest ? ""
          : r < od && !(r === 1 && kat.oferty.rundy.uslugi_startowe.includes(klucz)) ? `od ${OKRES.dopelniacz} ${od}` : "limit nowych dań wyczerpany";
        html += `<div class="kafel ${jest ? "wybrany" : ""}">
          <div class="kg"><span>${esc(u.nazwa)}<br><span class="podpowiedz">(porcja)</span></span></div>
          <div class="kt">
            <div class="wiersz"><span>Popyt roczny ${kolko(jakPrognoza(u, m))}</span><span>${licz(u.popyt_roczny)} porcji</span></div>
            <div class="wiersz"><span>Sezonowość (${MIESIACE[m]})</span><span>× ${licz(u.sezonowosc[m], 2)}</span></div>
            <div class="wiersz"><span>Preferowana cena</span><span>${zl(u.cena_preferowana)}</span></div>
            <div class="wiersz"><span>Czas przygotowania</span><span>${Math.round(u.godziny_prowadzacego * 600) / 10} min</span></div>
            <div class="wiersz"><span>Czas obsługi przy kasie</span><span>${Math.round(u.godziny_kasy * 600) / 10} min</span></div>
            ${u.grupa > 1 ? `<div class="wiersz"><span>Porcji naraz</span><span>${u.grupa}</span></div>` : ""}
            <div class="wiersz"><span>Przygotowuje</span><span>${esc(u.prowadzacy)}</span></div>
          </div>
          <div class="kd">
            <button class="btn pom" data-akcja="szczegoly-uslugi" data-u="${klucz}">Więcej szczegółów</button>
            ${jest ? `<button class="btn zielony" data-akcja="usluga" data-u="${klucz}" ${edycja ? "" : "disabled"}>✓ Wybrano</button>`
                   : `<button class="btn czarny" data-akcja="usluga" data-u="${klucz}" ${edycja && dozwolona ? "" : "disabled"}>Wybierz</button>${czemu ? `<span class="podpowiedz">${czemu}</span>` : ""}`}
            ${jest ? `<label class="pole">Prognozowany popyt (na ${OKRES.mianownik})
              <input type="number" min="0" step="1" value="${wybrane[klucz] || ""}" ${v.popyt ? "" : `placeholder="${baza}"`} data-zmiana="prognoza" data-u="${klucz}" ${edycja ? "" : "disabled"}>
              ${v.popyt ? "" : `<span class="podpowiedz">Wg wzoru: ${licz(u.popyt_roczny)} / ${OKRES.rund_w_roku} × ${u.sezonowosc[m]} ≈ ${baza}</span>`}</label>
              ${cenaDania(v, kat, klucz, edycja)}` : ""}
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
      const of = { ...menuLokalu(c.v, lokalWybrany(c.v)) };
      if (u in of) delete of[u];
      else {
        const limit = limitNowych(c.kat, r);
        // limit dotyczy przyrostu liczby dań firmy (usunięte danie zwalnia miejsce na nowe; danie z innego lokalu – bez limitu)
        const przyrost = Object.keys(c.v.stan.oferta).length - Object.keys(c.v.stan_przed.oferta).length;
        if (!(u in c.v.stan_przed.oferta) && !(u in c.v.stan.oferta) && przyrost >= limit) return toast(`W tej rundzie liczba dań może wzrosnąć najwyżej o ${limit}.`);
        of[u] = prognozaDania(c.v, c.kat, u, miesiacSprzedazy(r));
      }
      // wybrane danie od razu w sprzedaży – po cenie preferowanej, dopóki drużyna jej nie zmieni
      const ceny = { ...cenyLokalu(c.v, lokalWybrany(c.v)) };
      const nowaCena = u in of && !ceny[u] && sprzedazOtwarta(c.v);
      if (nowaCena) ceny[u] = { cena: c.kat.uslugi[u].cena_preferowana, rabat: 0 };
      await c.zmien((d) => {
        zapiszWLokalu(d, c.v, "oferta", of);
        if (nowaCena) zapiszWLokalu(d, c.v, "sprzedaz", ceny);
      });
    },
  },
  zmiany: {
    prognoza: async (el, c) => c.zmien((d) => {
      zapiszWLokalu(d, c.v, "oferta", { ...menuLokalu(c.v, lokalWybrany(c.v)), [el.dataset.u]: Math.max(0, Math.round(+el.value || 0)) });
    }),
  },
};

export { JAK, gw };
