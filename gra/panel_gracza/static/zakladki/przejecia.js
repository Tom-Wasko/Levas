// Nowe lokale → Licytacje (wyniki licytacji lokali) i Przejęcia (kupno budynku z najemcą, wypowiedzenia najmu)
// – silnik/nieruchomosci/przejecia.py.
import { esc, nazwaFirmy, naOkres, naRunde, podsumowanie, proc, tabela, zl, zwinTabela } from "./wspolne.js";
import { nazwaStrefy } from "./lokale.js";

const ULEPSZENIA = { zatrzymaj: "zatrzymaj ulepszenia (zapłać najemcy)", przywroc: "przywrócenie stanu (płaci najemca)" };
const nazwaLokalu = (kat, id) => kat.mapa.lokale.find((l) => l.id === id)?.nazwa ?? id;
const wypowiedzenia = (d) => Array.isArray(d.wypowiedz) ? d.wypowiedz : [];

function przyciskKupna(P, d, b, edycja, runda) {
  const wyb = d.przejecie?.id === b.id;
  if (wyb) return `<button class="btn zielony maly" data-akcja="przejecie" data-id="" ${edycja ? "" : "disabled"}>✓ Wybrano – anuluj</button>`;
  return `<button class="btn czarny maly" data-akcja="przejecie" data-id="${esc(b.id)}" ${!edycja || runda < P.od_rundy ? "disabled" : ""}>
    ${b.wykup ? "Wykup" : "Kup"}</button>`;
}

function poleOferty(P, d, b, edycja) {
  if (d.przejecie?.id !== b.id) return zl(b.cena);
  return `<input type="number" min="${b.cena}" max="${b.cena * P.oferta_max}" step="1000" value="${d.przejecie.oferta ?? b.cena}"
    data-zmiana="przejecie-oferta" style="width:110px" ${edycja ? "" : "disabled"}>`;
}

function budynekWlasny(P, d, b, edycja, v) {
  const w = wypowiedzenia(d).find((x) => x.id === b.id);
  if (b.najem_do != null) return `<span class="pigulka inf">wypowiedziany – do rundy ${b.najem_do}</span>`;
  const wybor = Object.entries(ULEPSZENIA).map(([k, t]) => `<option value="${k}" ${(w?.ulepszenia ?? "zatrzymaj") === k ? "selected" : ""}>${t}</option>`).join("");
  return w ? `<select data-zmiana="wypowiedz-ulepszenia" data-id="${esc(b.id)}" ${edycja ? "" : "disabled"}>${wybor}</select>
      <button class="btn zielony maly" data-akcja="wypowiedz" data-id="${esc(b.id)}" ${edycja ? "" : "disabled"}>✓ Wypowiadasz – anuluj</button>`
    : `<button class="btn jasny maly" data-akcja="wypowiedz" data-id="${esc(b.id)}" ${edycja ? "" : "disabled"}>Wypowiedz najem</button>`;
}

function stanBudynkow(v, kat, P, d, edycja) {
  let html = "";
  const tab = d ? tabela : zwinTabela;   // w wynikach (bez decyzji) tabele są zwijane
  if (P.budynki.length) {
    html += tab("Twoje budynki z najemcami", ["Budynek", "Najemca", `Czynsz${naOkres()}`, "Nakłady najemcy", "Kupiony", "Najem"],
      P.budynki.map((b) => [`${esc(b.nazwa)}<div class="podpowiedz">${esc(b.adres)}</div>`, esc(nazwaFirmy(v, b.najemca)),
        zl(naRunde(b.czynsz)), zl(b.naklady), `runda ${b.od_rundy} – ${zl(b.cena)}`, d ? budynekWlasny(P, d, b, edycja, v)
          : b.najem_do != null ? `wypowiedziany – do rundy ${b.najem_do}` : "trwa"]), { klasy: ["l", "l"] });
  }
  if (P.najmy.length) {
    html += tab("Twoje lokale w budynkach innych drużyn", ["Lokal", "Właściciel", `Czynsz${naOkres()}`, "Twoje nakłady", "Najem"],
      P.najmy.map((n) => [esc(n.nazwa), esc(nazwaFirmy(v, n.wlasciciel)), zl(naRunde(n.czynsz)), zl(n.naklady),
        n.najem_do != null ? `<span class="pigulka">wypowiedziany – ostatnia runda ${n.najem_do}</span>` : "trwa"]), { klasy: ["l", "l"] });
  }
  return html;
}

function licytacjaHtml(v, kat, p, zwijane = false) {
  return (zwijane ? zwinTabela : tabela)(`${p.rodzaj === "lokal" ? "Lokal" : "Budynek z najemcą"}: ${nazwaLokalu(kat, p.id)}${p.remis ? " – remis, losowanie" : ""}`,
    ["Firma", "Forma", "Oferta", "Cena wywoławcza", "Przebicie", "Wynik"],
    p.oferty.map((o) => [esc(nazwaFirmy(v, o.firma)), o.forma === "najem" ? "najem" : "kupno", zl(o.kwota), zl(o.wywolawcza),
      `+${proc(o.stosunek - 1, 0)}`, o.firma === p.zwyciezca ? `<span class="pigulka ok">wygrana</span>` : "przegrana"]),
    { klasy: ["l", "l"], sortuj: false, ...(zwijane ? { otwarte: p.oferty.some((o) => o.firma === v.firma) } : {}) });
}

export const przejecia = {
  tytul: "Przejęcia", tytulPelny: "Nowe lokale – przejęcia budynków", ikona: "lokale",
  odblokowanie: (v) => !!v.przejecia && v.runda >= v.przejecia.od_rundy, ukryta: (v) => !v.przejecia,
  info: (c) => {
    const P = c.v.przejecia;
    return `Budynek wynajmowany przez inną drużynę możesz kupić – najemca płaci wtedy czynsz Tobie. Właściciel może wypowiedzieć najem: najemca zostaje jeszcze
      ${P.wypowiedzenie_rund} rundy, potem się wyprowadza, a nakłady rozlicza się wg wyboru właściciela
      (zatrzymanie: ${proc(P.ulepszenia_zwrot, 0)} nakładów dla najemcy, przywrócenie: ${proc(P.przywrocenie_koszt, 0)} nakładów płaci najemca).`;
  },
  decyzje({ v, kat, d, edycja }) {
    const P = v.przejecia;
    let html = `<div class="pasek ciemny"><span>Twoje budynki z najemcami: <span class="kwota">${P.budynki.length}</span></span>
      <span>Czynsz od najemców: <span class="kwota">${zl(P.budynki.reduce((s, b) => s + naRunde(b.czynsz), 0))}</span>${naOkres()}</span></div>`;
    const dec = P.decyzja?.przejecie;
    if (dec?.id && dec.przyjety === false) html += `<div class="komunikat">${esc(dec.powod)}</div>`;
    for (const w of P.decyzja?.wypowiedzenia || []) if (!w.przyjete) html += `<div class="komunikat">${esc(w.powod)}</div>`;
    if (d.przejecie?.id) html += `<div class="komunikat ok">Kupujesz budynek: <b>${esc(nazwaLokalu(kat, d.przejecie.id))}</b>.
      Jeśli w tej rundzie chce go też inna drużyna, wygrywa wyższa oferta (najwyżej ${P.oferta_max} × cena), przy remisie – losowanie.</div>`;
    html += stanBudynkow(v, kat, P, d, edycja);
    html += P.do_kupienia.length ? tabela("Budynki z najemcami na sprzedaż", ["Budynek", "Strefa", "Najemca", `Czynsz${naOkres()}`, "Cena / Twoja oferta", ""],
      P.do_kupienia.map((b) => [`${esc(b.nazwa)}<div class="podpowiedz">${esc(b.adres)}</div>`, esc(nazwaStrefy(kat, b.strefa)),
        b.wykup ? "<b>Twoja firma</b> (wykup)" : esc(nazwaFirmy(v, b.najemca)), zl(naRunde(b.czynsz)), poleOferty(P, d, b, edycja),
        przyciskKupna(P, d, b, edycja, v.runda)]), { klasy: ["l", "l", "l"] })
      : `<p class="podpowiedz">Żaden wynajmowany budynek nie jest teraz na sprzedaż.</p>`;
    return html;
  },
  wyniki({ v, kat }) {
    const W = v.wyniki?.przejecia;
    if (!W) return `<p class="podpowiedz">Wyniki pojawią się po rundzie z licytacją albo przejęciem.</p>`;
    let html = "";
    const p = W.przejecie;
    if (p?.id) html += `<div class="komunikat ${p.przyjety ? "ok" : ""}">${p.przyjety
      ? `${p.wykup ? "Wykupiony lokal" : "Kupiony budynek"}: ${esc(nazwaLokalu(kat, p.id))} za ${zl(p.kwota)}.`
      : `Budynek nie został kupiony: ${esc(p.powod)}`}</div>`;
    for (const w of W.wypowiedzenia.filter((x) => x.przyjete)) html += `<div class="komunikat ok">Wypowiedziano najem: ${esc(nazwaLokalu(kat, w.id))}
      – najemca ${esc(nazwaFirmy(v, w.najemca))} zostaje do rundy ${w.najem_do}.</div>`;
    for (const x of W.wyprowadzki) html += `<div class="kafel"><div class="kg">Wyprowadzka: ${esc(nazwaLokalu(kat, x.id))}</div><div class="kt">
      <p>Najemca ${esc(nazwaFirmy(v, x.najemca))} oddał budynek firmie ${esc(nazwaFirmy(v, x.wlasciciel))}.
      Nakłady ${zl(x.naklady)} – ${x.ulepszenia === "zatrzymaj" ? `właściciel zapłacił ${zl(x.rozliczenie)}` : `najemca zapłacił ${zl(-x.rozliczenie)} za przywrócenie stanu`}.
      Sprzedany sprzęt: ${zl(x.sprzedany_sprzet)}, zwrot kaucji ${zl(x.kaucja)}.</p>
      ${x.przeniesieni.length ? `<p>Przeniesieni: ${x.przeniesieni.map(esc).join(", ")}.</p>` : ""}
      ${x.zwolnieni.length ? `<p>Zwolnieni (z odprawą): ${x.zwolnieni.map(esc).join(", ")}.</p>` : ""}</div></div>`;
    html += stanBudynkow(v, kat, W, null, false);
    if (!html) return `<p class="podpowiedz">W tej rundzie nie było przejęć ani wypowiedzeń.</p>`;
    const zdarzenia = [p?.id && (p.przyjety ? `${p.wykup ? "wykupiono lokal" : "kupiono budynek"} ${esc(nazwaLokalu(kat, p.id))}` : "próba zakupu budynku nie powiodła się"),
      W.wypowiedzenia.some((x) => x.przyjete) && "wypowiedziano najem", W.wyprowadzki.length && "najemca wyprowadził się z budynku"].filter(Boolean);
    return (zdarzenia.length ? podsumowanie(`W tej rundzie: ${zdarzenia.join(", ")}.`, p?.id && !p.przyjety ? "uwaga" : "") : "") + html;
  },
  akcje: {
    przejecie: (el, c) => c.zmien((d) => {
      const b = c.v.przejecia.do_kupienia.find((x) => x.id === el.dataset.id);
      d.przejecie = b ? { id: b.id, oferta: b.cena } : null;
    }),
    wypowiedz: (el, c) => c.zmien((d) => {
      const l = wypowiedzenia(d);
      d.wypowiedz = l.some((x) => x.id === el.dataset.id) ? l.filter((x) => x.id !== el.dataset.id)
        : [...l, { id: el.dataset.id, ulepszenia: "zatrzymaj" }];
    }),
  },
  zmiany: {
    "przejecie-oferta": (el, c) => c.zmien((d) => { d.przejecie = { ...d.przejecie, oferta: Number(el.value) }; }),
    "wypowiedz-ulepszenia": (el, c) => c.zmien((d) => {
      d.wypowiedz = wypowiedzenia(d).map((x) => x.id === el.dataset.id ? { ...x, ulepszenia: el.value } : x);
    }),
  },
};

// UF15: licytacje lokali osobno – kto, ile i za ile licytował w mieście (oferty wpisuje się w Nowe lokale → Do wynajęcia)
function licytacjeMiasta(v, kat, zwijane = false) {
  const przetargi = v.rynek?.przejecia?.przetargi || [];
  const moje = przetargi.filter((x) => x.oferty.some((o) => o.firma === v.firma)), wygrane = moje.filter((x) => x.zwyciezca === v.firma).length;
  const lead = zwijane && przetargi.length ? podsumowanie(`W mieście odbyło się ${przetargi.length} ${przetargi.length === 1 ? "licytacja" : przetargi.length < 5 ? "licytacje" : "licytacji"}. `
    + (moje.length ? `Twoja firma brała udział w ${moje.length}, a wygrała ${wygrane}.` : "Twoja firma w żadnej nie startowała."), moje.length && !wygrane ? "uwaga" : "") : "";
  return przetargi.length ? lead + przetargi.map((x) => licytacjaHtml(v, kat, x, zwijane)).join("")
    : `<p class="podpowiedz">W poprzedniej rundzie nikt się nie licytował – każdy chętny dostał swój lokal.</p>`;
}

export const licytacje = {
  tytul: "Licytacje", tytulPelny: "Nowe lokale – licytacje", ikona: "lokale",
  odblokowanie: (v) => !!v.przejecia && v.runda >= (v.przejecia.licytacje_od_rundy ?? 1), ukryta: (v) => !v.przejecia,
  info: (c) => `Gdy kilka drużyn chce w jednej rundzie ten sam lokal, wygrywa najwyższa oferta względem ceny wywoławczej
    (od rundy ${c.v.przejecia.licytacje_od_rundy} – wpisz ją przy lokalu w zakładce Do wynajęcia), remis rozstrzyga losowanie.`,
  decyzje({ v, kat }) {
    return `<div class="komunikat">Ofertę za lokal wpisujesz przy lokalu w zakładce <a data-zakladka-k="lokale">Do wynajęcia</a>.
      Tu widać, jak poszły licytacje w poprzedniej rundzie – kto przebił i o ile.</div>` + licytacjeMiasta(v, kat);
  },
  wyniki({ v, kat }) { return licytacjeMiasta(v, kat, true); },
};
