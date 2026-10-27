// Marketing: kampanie agencji reklamowych w strefach miasta i promocje.
import { esc, licz, nazwaFirmy, nazwaUslugi, proc, tabela, wykres, zl } from "./wspolne.js";

const RODZAJ = { druk: "druk", internet: "internet", radio_billboard: "radio i billboardy", wydarzenia: "wydarzenia" };
const FAZA = { trwa: "trwa", wygasa: "wygasa" };
const wybor = {};   // wybrana strefa kanału (agencja/kanał → strefa), do przeliczenia kosztu przed zamówieniem

function strefaKanalu(R, a, k) {
  const klucz = `${a.id}/${k.id}`;
  if (k.zasieg === "miasto") return "miasto";
  if (!k.strefy.includes(wybor[klucz])) wybor[klucz] = k.strefy.find((s) => R.moje_strefy.includes(s)) || k.strefy[0];
  return wybor[klucz];
}

function kanalHtml(v, R, a, k, edycja) {
  const s = strefaKanalu(R, a, k), zam = (v.decyzje.kampanie || []).some((x) => x.agencja === a.id && x.kanal === k.id && (x.strefa || "miasto") === s);
  const trwa = k.trwa.includes(s), inni = (R.konkurencja[a.rodzaj] || {})[s] || [];
  const opcje = k.strefy.map((z) => `<option value="${z}" ${z === s ? "selected" : ""}>${esc(R.strefy[z])}${R.moje_strefy.includes(z) ? " (Twój lokal)" : ""}</option>`).join("");
  const przycisk = !k.dostepny ? `Dostępne od rundy ${k.od_rundy}` : trwa ? "Kampania trwa" : zam ? "✓ Zamówiono (anuluj)" : "Zamów";
  return `<div class="kafel ${zam ? "wybrany" : ""} ${k.dostepny ? "" : "niedostepny"}"><div class="kg">${esc(k.nazwa)}
      <span class="pigulka inf">${k.zasieg === "miasto" ? "całe miasto" : "strefa"}</span></div><div class="kt">
    ${k.zasieg === "miasto" ? "" : `<label class="pole">Strefa<select data-zmiana="kampania-strefa" data-k="${a.id}/${k.id}" ${edycja && k.dostepny ? "" : "disabled"}>${opcje}</select></label>`}
    <div class="wiersz"><span>Koszt (netto)</span><span>${zl(k.koszty[s])}</span></div>
    <div class="wiersz"><span>Czas trwania</span><span>${k.rundy} ${k.rundy === 1 ? "runda" : "rundy"}</span></div>
    <div class="wiersz"><span>Więcej klientów w strefie</span><span>+${proc(k.pula * k.sila[s], 1)}</span></div>
    <div class="wiersz"><span>Przyciąganie do Ciebie</span><span>+${proc(k.przyciaganie * k.sila[s], 1)}</span></div>
    ${k.sila[s] < 1 ? `<div class="wiersz"><span>Siła (powtórka – ludzie już to widzieli)</span><span class="minus">${proc(k.sila[s], 0)}</span></div>` : ""}
    ${inni.length ? `<div class="wiersz"><span>Konkurencja w tym rodzaju (poprzednia runda)</span><span>${inni.map((f) => esc(nazwaFirmy(v, f))).join(", ")}</span></div>` : ""}</div>
    <div class="kd"><button class="btn ${zam ? "zielony" : "czarny"}" data-akcja="kampania" data-a="${a.id}" data-k="${k.id}" data-s="${s}"
      ${edycja && k.dostepny && !trwa ? "" : "disabled"}>${przycisk}</button></div></div>`;
}

function trwajaceHtml(v, lista, tytul) {
  if (!lista.length) return "";
  return tabela(tytul, ["Kampania", "Agencja", "Strefa", "Rundy", "Faza", "Zagłuszanie", "Więcej klientów", "Przyciąganie", "Koszt"],
    lista.map((x) => [esc(x.nazwa), esc(x.agencja_nazwa), esc(x.strefa_nazwa), `${x.od_rundy}–${x.do_rundy}`, FAZA[x.faza],
      x.konkurenci ? `<span class="minus">${proc(x.zagluszanie, 0)}</span> (${x.konkurenci} konk.)` : "–",
      `+${proc(x.pula, 1)}`, `+${proc(x.przyciaganie, 1)}`, x.koszt ? zl(x.koszt) : "–"]), { klasy: ["l", "l", "l"] });
}

export const agencje = {
  tytul: "Agencje reklamowe", tytulPelny: "Marketing – agencje reklamowe", ikona: "tradycyjny",
  odblokowanie: (v) => !!v.reklama && v.runda >= (v.harmonogram?.reklama ?? 1), ukryta: (v) => !v.reklama,
  info: () => `Zamów kampanię w jednej z agencji na mieście. Kampania w strefie przyciąga do miasta więcej głodnych (korzystają też sąsiedzi)
    i podbiera klientów konkurencji. Kilka firm reklamujących się tak samo w tej samej strefie zagłusza się nawzajem, a ta sama kampania powtórzona
    zaraz po poprzedniej działa słabiej. Po końcu kampania jeszcze przez chwilę wygasa. Kampanie się sumują, ale z sufitem:
    jedna daje zwykle kilka procent popytu więcej, kilka naraz – ok. +10% … +30%, a dalsze dokładanie już prawie nic nie zmienia.`,
  decyzje({ v, edycja }) {
    const R = v.reklama;
    if (!R) return `<p class="podpowiedz">Agencje reklamowe działają w grze z lokalami.</p>`;
    const zam = R.zamowione || [];
    let html = `<div class="pasek ciemny"><span>Zamówione kampanie: <span class="kwota">${zam.length}</span></span>
      <span>Koszt (netto): <span class="kwota">${zl(zam.reduce((s, x) => s + x.koszt, 0))}</span></span></div>`;
    html += trwajaceHtml(v, R.trwajace.filter((x) => x.od_rundy < v.runda), "Twoje kampanie z poprzednich rund – działają w tej rundzie");
    if (R.model?.maks_przyciagania) html += `<p class="podpowiedz">Sufit reklamy: przyciąganie wszystkich Twoich kampanii w jednej strefie
      nasyca się do +${proc(R.model.maks_przyciagania, 0)} (to ok. +30% popytu), poszerzenie puli strefy – do +${proc(R.model.maks_puli, 0)}.
      Pierwsze kampanie działają prawie w pełni, każda kolejna – coraz słabiej.</p>`;
    for (const a of R.agencje) {
      html += `<div class="pasek ciemny" style="margin-top:22px"><span>${esc(a.nazwa)}</span><span>${RODZAJ[a.rodzaj] || esc(a.rodzaj)}</span></div>
        <p class="podpowiedz">${esc(a.opis)}</p>
        <div class="siatka trojka" style="margin-top:10px">${a.kanaly.map((k) => kanalHtml(v, R, a, k, edycja)).join("")}</div>`;
    }
    return html;
  },
  wyniki({ v }) {
    const W = v.wyniki?.reklama_agencje;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie z kampanią.</p>`;
    const raporty = W.kampanie.filter((x) => x.tekst);
    let html = raporty.map((x) => `<div class="kafel"><div class="kg">${esc(x.nazwa)} – ${esc(x.strefa_nazwa)}</div>
      <div class="kt"><p>${esc(x.tekst)}</p></div></div>`).join("");
    html += trwajaceHtml(v, W.kampanie, "Twoje kampanie w tej rundzie") || `<p class="podpowiedz">W tej rundzie nie działała żadna Twoja kampania.</p>`;
    const L = Object.entries(W.laczne || {});
    if (L.length) html += tabela("Łączne przyciąganie w strefach (po sufocie)", ["Strefa", "Suma kampanii", "Działa naprawdę", "Uciekło przez sufit"],
      L.map(([z, x]) => [esc(v.reklama?.strefy?.[z] ?? z), `+${proc(x.suma, 1)}`, `+${proc(x.dziala, 1)}`,
        x.suma - x.dziala > 0.005 ? `<span class="minus">${proc(x.suma - x.dziala, 1)}</span>` : "–"]), { klasy: ["l"] });
    const k = v.rynek?.kampanie || {};
    html += tabela("Kampanie na mieście (widać je na słupach i w radiu)", ["Firma", "Wydatki w rundzie", "Kampanie"],
      Object.entries(k).map(([f, x]) => [esc(nazwaFirmy(v, f)), zl(x.wydatki),
        x.kampanie.map((y) => `${esc(y.kanal)} (${esc(y.strefa ? v.reklama?.strefy?.[y.strefa] ?? y.strefa : "całe miasto")}, ${FAZA[y.faza]})`).join(", ")]),
      { klasy: ["l", "", "l"] });
    return html + `<div class="wykres"><canvas id="w-agencje"></canvas></div>`;
  },
  po({ v }, tryb) {
    const k = v.rynek?.kampanie;
    if (tryb !== "wyniki" || !k) return;
    const f = Object.keys(k);
    wykres("w-agencje", "bar", f.map((x) => nazwaFirmy(v, x)), [{ label: "Wydatki na kampanie reklamowe", data: f.map((x) => k[x].wydatki) }]);
  },
  zmiany: { "kampania-strefa": (el, c) => { wybor[el.dataset.k] = el.value; c.rysuj(); } },
  akcje: {
    kampania: (el, c) => c.zmien((d) => {
      const { a, k, s } = el.dataset, strefa = s === "miasto" ? null : s;
      const l = d.kampanie || [];
      const jest = l.some((x) => x.agencja === a && x.kanal === k && (x.strefa ?? null) === strefa);
      d.kampanie = jest ? l.filter((x) => !(x.agencja === a && x.kanal === k && (x.strefa ?? null) === strefa)) : [...l, { agencja: a, kanal: k, strefa }];
    }),
  },
};

function listaPromocji(v) {
  return v.decyzje.promocje ?? (v.promocje?.aktywne || []).map(({ typ, nazwa, danie }) => ({ typ, nazwa, danie }));
}

function promocjaHtml(v, R, t, edycja) {
  const lista = listaPromocji(v), moja = lista.find((x) => x.typ === t.id), akt = R.aktywne.find((x) => x.typ === t.id);
  const dostepna = v.runda >= R.od_rundy, pelno = !moja && lista.length >= R.limit;
  const dis = edycja && dostepna ? "" : "disabled";
  const inni = Object.entries(R.konkurencja).filter(([, l]) => l.some((x) => x.typ === t.id)).map(([f]) => esc(nazwaFirmy(v, f)));
  const wiersz = (a, b) => `<div class="wiersz"><span>${a}</span><span>${b}</span></div>`;
  const przyc = t.przyrost ? `${proc(t.przyciaganie, 0)} → ${proc(t.przyrost < 0 ? t.przyciaganie_min : t.przyciaganie_max, 0)} (${t.przyrost < 0 ? "znużenie" : "przywiązanie"} ${proc(Math.abs(t.przyrost), 0)}/rundę)` : proc(t.przyciaganie, 0);
  const przycisk = !dostepna ? `Dostępne od rundy ${R.od_rundy}` : moja ? "✓ Włączona (wyłącz)" : pelno ? `Limit ${R.limit} promocji` : "Włącz";
  return `<div class="kafel ${moja ? "wybrany" : ""} ${dostepna ? "" : "niedostepny"}"><div class="kg">${esc(t.nazwa)}
      <span class="pigulka inf">${t.zakres === "danie" ? "jedno danie" : "całe menu"}</span></div><div class="kt">
    <p class="podpowiedz">${esc(t.opis)}</p>
    ${t.rabat ? wiersz("Rabat dla objętych", proc(t.rabat, 0)) : ""}
    ${t.porcje > 1 ? wiersz("Porcji na klienta", `${t.porcje} (składniki i kuchnia ×${t.porcje})`) : ""}
    ${t.doplata ? wiersz("Dopłata klienta / koszt dodatku", `${zl(t.doplata)} / ${zl(t.koszt_dodatku)} netto`) : ""}
    ${wiersz("Przyciąganie objętych klientów", `+${przyc}`)}
    ${t.dni ? wiersz("Dni", esc(t.dni.join(", "))) : ""}
    ${t.strefy ? wiersz("Klienci ze stref", esc(t.strefy.join(", "))) : ""}
    ${wiersz("Koszt włączenia (netto)", zl(t.koszt_startu))}
    ${akt ? wiersz("Trwa od rundy", `${akt.od_rundy}${akt.nowa ? " (nowa)" : ""}, teraz +${proc(akt.przyciaganie, 0)}`) : ""}
    ${inni.length ? wiersz("U konkurencji (poprzednia runda)", inni.join(", ")) : ""}
    ${moja ? `<label class="pole">Twoja nazwa promocji<input type="text" maxlength="${R.nazwa_max}" value="${esc(moja.nazwa)}" data-zmiana="promocja-nazwa" data-t="${t.id}" ${dis}></label>
      ${t.zakres === "danie" ? `<label class="pole">Danie<select data-zmiana="promocja-danie" data-t="${t.id}" ${dis}>${R.dania.map((u) =>
        `<option value="${u.id}" ${u.id === moja.danie ? "selected" : ""}>${esc(u.nazwa)}</option>`).join("")}</select></label>` : ""}` : ""}</div>
    <div class="kd"><button class="btn ${moja ? "zielony" : "czarny"}" data-akcja="promocja" data-t="${t.id}" ${dis} ${pelno ? "disabled" : ""}>${przycisk}</button></div></div>`;
}

export const promocje = {
  tytul: "Promocje", tytulPelny: "Marketing – promocje", ikona: "procent",
  odblokowanie: (v) => !!v.promocje && v.runda >= v.promocje.od_rundy, ukryta: (v) => !v.promocje,
  info: () => `Włącz promocję z listy i nadaj jej własną, ozdobną nazwę (nazwa nie wpływa na wynik – tylko na humor klientów).
    Promocja przyciąga objętych nią klientów, ale obcina cenę: włączaj ją, gdy masz wolne ręce w kuchni i miejsca w lokalu.
    Trwa, dopóki jej nie wyłączysz; zmiana nazwy jest darmowa, zmiana dania to nowa promocja (znów koszt włączenia).`,
  decyzje({ v, edycja }) {
    const R = v.promocje;
    if (!R) return `<p class="podpowiedz">Promocje działają w grze z lokalami.</p>`;
    const lista = listaPromocji(v);
    let html = `<div class="pasek ciemny"><span>Włączone promocje: <span class="kwota">${lista.length} / ${R.limit}</span></span>
      <span>Koszt nowych (netto): <span class="kwota">${zl((R.nowe || []).reduce((s, x) => s + (R.rodzaje.find((t) => t.id === x.typ)?.koszt_startu || 0), 0))}</span></span></div>`;
    html += `<div class="siatka trojka" style="margin-top:10px">${R.rodzaje.map((t) => promocjaHtml(v, R, t, edycja)).join("")}</div>`;
    return html;
  },
  wyniki({ v, kat }) {
    const W = v.wyniki?.promocje;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie z promocją.</p>`;
    let html = W.promocje.filter((x) => x.tekst).map((x) => `<div class="kafel"><div class="kg">${esc(x.rodzaj)} „${esc(x.nazwa)}”</div>
      <div class="kt"><p>${esc(x.tekst)}</p></div></div>`).join("");
    html += W.promocje.length ? tabela("Twoje promocje w tej rundzie", ["Promocja", "Nazwa", "Danie", "Rund", "Przyciąganie", "Objętych porcji", "Rabat", "Porcje gratis", "Dopłaty", "Koszt dodatków"],
      W.promocje.map((x) => [esc(x.rodzaj), `„${esc(x.nazwa)}”`, x.danie ? esc(nazwaUslugi(kat, x.danie)) : "całe menu", x.rund, `+${proc(x.przyciaganie, 0)}`,
        licz(x.objeci), zl(x.rabat), licz(x.gratis), zl(x.doplaty), zl(x.koszt_dodatkow)]), { klasy: ["l", "l", "l"] })
      : `<p class="podpowiedz">W tej rundzie nie działała żadna Twoja promocja.</p>`;
    if (W.wylaczone?.length) html += `<p class="podpowiedz">Wyłączone: ${W.wylaczone.map((x) => `„${esc(x.nazwa)}”`).join(", ")}.</p>`;
    const k = v.rynek?.promocje || {};
    html += tabela("Promocje na mieście (plakaty na drzwiach lokali)", ["Firma", "Promocje"],
      Object.entries(k).map(([f, l]) => [esc(nazwaFirmy(v, f)), l.map((y) => `${esc(y.rodzaj)} „${esc(y.nazwa)}”${y.danie ? ` – ${esc(nazwaUslugi(kat, y.danie))}` : ""}`).join(", ")]),
      { klasy: ["l", "l"] });
    return html;
  },
  zmiany: {
    "promocja-nazwa": (el, c) => c.zmien((d) => { d.promocje = listaPromocji(c.v).map((x) => x.typ === el.dataset.t ? { ...x, nazwa: el.value } : x); }),
    "promocja-danie": (el, c) => c.zmien((d) => { d.promocje = listaPromocji(c.v).map((x) => x.typ === el.dataset.t ? { ...x, danie: el.value } : x); }),
  },
  akcje: {
    promocja: (el, c) => c.zmien((d) => {
      const l = listaPromocji(c.v), t = c.v.promocje.rodzaje.find((x) => x.id === el.dataset.t);
      d.promocje = l.some((x) => x.typ === t.id) ? l.filter((x) => x.typ !== t.id)
        : [...l, { typ: t.id, nazwa: t.nazwa, danie: t.zakres === "danie" ? c.v.promocje.dania[0]?.id ?? null : null }];
    }),
  },
};
