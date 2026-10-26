// Magazyn i świeżość: partie składników z terminami, pojemność chłodni i zamrażarki (silnik/swiezosc.py,
// dane/zasoby.yaml, dane/sprzet.yaml) – w decyzjach plan dostaw, w wynikach dzień po dniu: dostawy, zużycie, straty.
import { esc, gw, licz, nazwaUslugi, tabela, ulamek, wykres, zl2 } from "./wspolne.js";

const dataKrotka = (iso) => { const [, m, d] = iso.split("-"); return `${+d}.${m}`; };
const MIEJSCE = { chlodnia: "Chłodnia", zamrazarka: "Zamrażarka", suche: "Suchy magazyn" };
const POWOD = { termin: "minął termin przydatności", miejsce: "nie zmieściło się – dostawca zostawił pod drzwiami" };

function zajetoscHtml(S) {
  const typy = Object.keys(S.pojemnosc);
  const wiersze = typy.map((t) => [MIEJSCE[t], licz(S.pojemnosc[t]),
    ...S.zajetosc.map((z) => z[t] > S.pojemnosc[t] + 1e-6 ? `<span class="minus">${licz(z[t])}</span>` : licz(z[t]))]);
  return tabela("Zajętość chłodni i zamrażarki (litry, bez sprzedaży – najwięcej, ile może być w środku)",
    ["Miejsce", "Pojemność", ...S.dni.map((d) => `${d.dzien}<div class="podpowiedz">${dataKrotka(d.data)}</div>`)], wiersze, { klasy: ["l"] });
}

function partieHtml(S, dni) {
  const koniec = dni[dni.length - 1].data;
  const wiersze = S.partie.map((p) => [esc(p.zasob) + (p.nowa ? ' <span class="podpowiedz">(zamówione teraz)</span>' : ""), gw(p.jakosc), ulamek(p.ilosc),
    dataKrotka(p.dostawa), p.termin ? (p.termin <= koniec ? `<span class="minus">${dataKrotka(p.termin)}</span>` : dataKrotka(p.termin)) : "–",
    MIEJSCE[p.przechowywanie], p.miejsce_l ? licz(p.miejsce_l) : "–", zl2(p.wartosc)]);
  return tabela("Partie składników (najpierw zużywane te z najkrótszym terminem)", ["Składnik", "Jakość", "Opakowania", "Dostawa", "Ostatni dzień", "Przechowywanie", "Miejsce (l)", "Wartość"],
    wiersze, { klasy: ["l", "", "", "", "", "l"], stopka: ["Razem", "", "", "", "", "", "", zl2(S.partie.reduce((s, p) => s + p.wartosc, 0))] });
}

function wynikiZasoby(W) {
  const wiersze = Object.entries(W.zasoby).map(([z, x]) => {
    const suma = (k) => x[k].reduce((s, v) => s + v, 0);
    return [esc(z), ulamek(suma("dostawy")), ...x.zuzycie.map((v) => ulamek(v)), ulamek(suma("zuzycie")),
      suma("straty") ? `<span class="minus">${ulamek(suma("straty"))}</span>` : "0"];
  });
  return tabela("Składniki dzień po dniu – zużycie (opakowania)", ["Składnik", "Dostawy", ...W.dni.map((d) => dataKrotka(d)), "Zużycie", "Straty"], wiersze, { klasy: ["l"] });
}

function wynikiStraty(W) {
  if (!W.straty.length) return `<p class="podpowiedz">Nic się nie zmarnowało – sanepid byłby dumny.</p>`;
  return tabela("Do kosza", ["Dzień", "Składnik", "Jakość", "Opakowania", "Wartość", "Powód"],
    W.straty.map((s) => [dataKrotka(s.data), esc(s.zasob), gw(s.jakosc), ulamek(s.ilosc), `<span class="minus">${zl2(s.wartosc)}</span>`, POWOD[s.powod] || esc(s.powod)]),
    { klasy: ["l", "l", "", "", "", "l"], stopka: ["Razem", "", "", "", zl2(W.wartosc_strat), ""] });
}

function wynikiMenu(W, kat) {
  const z = Object.entries(W.zamiany);
  if (!z.length) return "";
  const brak = {};
  for (const x of W.wylaczone) (brak[x.danie] = brak[x.danie] || new Set()).add(x.skladnik);
  return tabela("Dania wyłączone z menu (brak składnika rano)", ["Danie", "Brakujący składnik", "Dni bez dania", "Wzięli inne danie", "Odeszli"],
    z.map(([u, x]) => [esc(nazwaUslugi(kat, u)), [...brak[u]].map(esc).join(", "), licz(W.wylaczone.filter((w) => w.danie === u).length), licz(x.przeszli),
      `<span class="minus">${licz(x.odeszli)}</span>`]), { klasy: ["l", "l"] })
    + `<p class="podpowiedz">Gdy dania nie ma w menu, część klientów zamawia coś innego, reszta idzie do konkurencji.</p>`;
}

export const swiezosc = {
  tytul: "Świeżość", tytulPelny: "Magazyn i świeżość", ikona: "swiezosc", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Składniki mają termin przydatności: bułka z poniedziałku ląduje w koszu we wtorek wieczorem, mięso wytrzyma cztery dni, mrożonki – miesiące.
    Dzień dostawy wybierasz w zakładce <a data-zakladka-k="dostawcy">Dostawcy</a> (baza składników dostawcy). Chłodzone i mrożone składniki muszą się zmieścić
    w szafie chłodniczej i zamrażarce – czego nie zmieścisz, to się zepsuje. Mrożona pita i mrożone mięso zastępują świeże, gdy tych zabraknie,
    ale klienci to czują (−1★ jakości składnika).`,
  decyzje({ v }) {
    const S = v.swiezosc;
    if (!S) return `<p class="podpowiedz">Brak danych o magazynie.</p>`;
    const koniec = S.dni[S.dni.length - 1].data;
    const wygasa = S.partie.filter((p) => p.termin && p.termin <= koniec);
    return `<div class="pasek ciemny"><span>Chłodnia: <span class="kwota">${licz(S.pojemnosc.chlodnia)} l</span></span>
      <span>Zamrażarka: <span class="kwota">${licz(S.pojemnosc.zamrazarka)} l</span></span>
      <span>Partie kończące termin w tej rundzie: <span class="kwota">${wygasa.length}</span></span></div>`
      + (S.pojemnosc.chlodnia || S.pojemnosc.zamrazarka ? "" : `<div class="komunikat">Nie masz szafy chłodniczej ani zamrażarki – kup je w zakładce Sprzęt, inaczej mięso będzie trzymane na parapecie.</div>`)
      + zajetoscHtml(S) + (S.partie.length ? partieHtml(S, S.dni) : `<p class="podpowiedz">Magazyn jest pusty.</p>`);
  },
  wyniki({ v, kat }) {
    const W = v.wyniki?.swiezosc;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie sprzedaży.</p>`;
    return `<div class="pasek ciemny"><span>Wartość strat: <span class="kwota">${zl2(W.wartosc_strat)}</span></span>
      <span>Wyrzucone partie: <span class="kwota">${W.straty.length}</span></span></div>`
      + wynikiZasoby(W) + `<div class="wykres"><canvas id="w-swiezosc"></canvas></div>` + wynikiStraty(W) + wynikiMenu(W, kat);
  },
  po({ v }, tryb) {
    const W = v.wyniki?.swiezosc;
    if (tryb !== "wyniki" || !W || !W.zajetosc.length) return;
    wykres("w-swiezosc", "bar", W.dni.map((d) => dataKrotka(d)), [
      { label: "Chłodnia – zajęte litry (wieczorem)", data: W.zajetosc.map((z) => z.chlodnia) },
      { label: "Zamrażarka – zajęte litry (wieczorem)", data: W.zajetosc.map((z) => z.zamrazarka) }]);
  },
};
