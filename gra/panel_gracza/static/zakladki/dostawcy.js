// Dostawcy: zakup składników i magazyn (bez zwrotów). Zamówienie ma dzień dostawy (świeżość – zakładka
// „Magazyn i świeżość”, silnik/kuchnia/swiezosc.py), a dostawcy mają swoje zasady (silnik/kuchnia/dostawcy.py: zasady_dostaw):
// dni dostaw, opłata za dowóz, minimalne zamówienie, odbiór osobisty w dyskontach i gazetki.
import { esc, OKRES, gw, kafelkiLiczb, licz, nazwaFirmy, okno, podsumowanie, tabela, toast, ulamek, wykres, zl, zl2, zwinTabela } from "./wspolne.js";
import { IG_AUTO } from "./infografiki.js";
import { glownyLokal, idWybranego, lokalPartii, lokalWybrany, menuLokalu, nazwaLokalu, zapiszWLokalu } from "./lokal_wybor.js";

// Z3: przy kilku lokalach magazyn i zamówienia wybranego lokalu (zamówienie bez pola "lokal" – lokal główny)
function stan(v, z, q) {
  const id = idWybranego(v);
  if (!id) return v.stan_przed.magazyn[`${z}|${q}`] || 0;
  return (v.stan_przed.partie || []).filter((p) => p.zasob === z && +p.jakosc === q && lokalPartii(v, p) === id).reduce((s, p) => s + p.ilosc, 0);
}
const lokalZam = (v, x) => x.lokal || glownyLokal(v);
const mojeZam = (v) => { const id = idWybranego(v); return (v.decyzje.zamowienia || []).filter((x) => !id || lokalZam(v, x) === id); };
const tenLokal = (v, x) => { const id = idWybranego(v); return !id || lokalZam(v, x) === id; };
const zamowienia = (v, d, z, q) => mojeZam(v).filter((x) => x.dostawca === d && x.zasob === z && +x.jakosc === q);
const zamowione = (v, d, z, q, dz) => zamowienia(v, d, z, q).filter((x) => dz === undefined || (+x.dzien || 0) === dz).reduce((s, x) => s + x.ilosc, 0);
const dniDostaw = (v) => (v.lokale && v.swiezosc?.dni) || null;
const DNI = ["pn", "wt", "śr", "czw", "pt", "sob", "nd"];
const RODZAJ = { dyskont: "Dyskont", hurtownia: "Hurtownia", producent: "Producent", piekarnia: "Piekarnia", hipermarket: "Hipermarket" };
const info = (v, d) => (v.dostawcy_info || {})[d] || { dni_dostaw: [0, 1, 2, 3, 4, 5, 6], koszt_dostawy: 0, minimalne_zamowienie: 0 };
const dzienTyg = (iso) => (new Date(iso).getUTCDay() + 6) % 7;
// indeksy dni rundy, w które dostawca dowozi (null – gra bez lokali)
const dniDostawcy = (v, d) => { const dni = dniDostaw(v); return dni && dni.map((x, i) => i).filter((i) => info(v, d).dni_dostaw.includes(dzienTyg(dni[i].data))); };
const rabat = (v, d, z) => (v.gazetki || {})[d]?.[z];

// Podział zamówienia na dostawy (jak planowanie._dostawy w silniku): co `krok` dni – krótki termin albo chłodnia /
// zamrażarka; każda dostawa na dni do następnej, zapas z magazynu zmniejsza pierwszą. dozwolone – dni dostaw
// dostawcy: dostawa przesuwa się na ostatni dzień dostaw przed planowanym (albo pierwszy).
function dostawy(kat, z, potrzeba, stan, udzialy, dozwolone) {
  const zas = kat.zasoby[z], n = udzialy.length;
  const termin = zas.termin_dni || n;
  let krok = Math.min(termin, n);
  if ((zas.przechowywanie || "suche") !== "suche") krok = Math.min(krok, 3);
  const suma = udzialy.reduce((s, x) => s + x, 0) || 1, wynik = [];
  let punkty = [];
  for (let j = 0; j < n; j += krok) punkty.push(j);
  if (dozwolone && dozwolone.length) {
    punkty = [...new Set(punkty.map((j) => { const p = dozwolone.filter((d) => d <= j); return p.length ? p[p.length - 1] : dozwolone[0]; }))].sort((a, b) => a - b);
  }
  const granice = [0, ...punkty.slice(1), n];
  let zapas = stan;
  punkty.forEach((j, i) => {
    const ile = potrzeba * udzialy.slice(granice[i], granice[i + 1]).reduce((s, x) => s + x, 0) / suma - zapas;
    const k = Math.ceil(Math.max(0, ile) - 1e-9);
    zapas = krok < termin ? Math.max(0, k - ile) : 0;
    if (k > 0) wynik.push([j, k]);
  });
  return wynik;
}

// Udziały dni rundy w sprzedaży do rozłożenia dostaw: wagi dni stref lokali firmy, a bez lokali – po równo.
// null – gra bez dni dostaw.
function udzialyDni(v) {
  const dni = dniDostaw(v);
  if (!dni) return null;
  const id = idWybranego(v);
  const wagi = (v.lokale?.moje || []).filter((l) => !id || l.id === id).map((l) => v.popyt?.strefy?.[l.strefa]?.dni).filter((w) => w?.length === dni.length);
  return wagi.length ? dni.map((_, i) => wagi.reduce((s, w) => s + w[i], 0)) : dni.map(() => 1);
}

// Zamówienia na prognozę u najtańszych (jak planowanie.zamowienie_zasobow): z podziałem na dni bez dyskontów
// i bez dostawców, u których któraś dostawa nie osiąga minimalnego zamówienia.
function planZamowien(c, q, zapas) {
  const pot = zapotrzebowanie(c.v, c.kat), ceny = c.v.ceny_dostawcow;
  const udzialy = udzialyDni(c.v);
  const pomin = new Set(udzialy ? Object.keys(ceny).filter((d) => info(c.v, d).odbior_osobisty) : []);
  for (;;) {
    const tanie = najtansze(ceny, pomin), nowe = [];
    for (const [z, p] of Object.entries(pot)) {
      const mag = [1, 2, 3].reduce((s, j) => s + stan(c.v, z, j), 0);
      let jq = q;
      while (!tanie[`${z}|${jq}`] && jq > 1) jq--;
      if (!tanie[`${z}|${jq}`]) continue;
      const d = tanie[`${z}|${jq}`].d;
      if (udzialy) {
        for (const [dzien, ilosc] of dostawy(c.kat, z, p * zapas, mag, udzialy, dniDostawcy(c.v, d))) nowe.push({ dostawca: d, zasob: z, jakosc: jq, ilosc, dzien });
        continue;
      }
      const brak = Math.ceil(Math.max(0, p * zapas - mag) - 1e-9);
      if (brak > 0) nowe.push({ dostawca: d, zasob: z, jakosc: jq, ilosc: brak });
    }
    if (!udzialy) return nowe;
    const wartosc = {};
    for (const x of nowe) { const k = `${x.dostawca}|${x.dzien}`; wartosc[k] = (wartosc[k] || 0) + x.ilosc * ceny[x.dostawca][x.zasob][x.jakosc]; }
    const zaMale = Object.entries(wartosc).filter(([k, w]) => w < (info(c.v, k.split("|")[0]).minimalne_zamowienie || 0) - 1e-9).map(([k]) => k.split("|")[0]);
    if (!zaMale.length) return nowe;
    for (const d of zaMale) pomin.add(d);
  }
}

function kafelInfo(v, d) {
  const x = info(v, d);
  if (!v.dostawcy_info) return "";
  const w = (a, b) => `<div class="wiersz"><span>${a}</span><span>${b}</span></div>`;
  const g = Object.entries((v.gazetki || {})[d] || {});
  return `<div class="podpowiedz" style="margin-bottom:6px">${RODZAJ[x.rodzaj] || ""}${x.opis ? ` – ${esc(x.opis)}` : ""}</div>`
    + w("Dni dostaw", x.dni_dostaw.length === 7 ? "codziennie" : x.dni_dostaw.map((i) => DNI[i]).join(", "))
    + (x.odbior_osobisty ? w("Odbiór osobisty", `${licz(x.godziny_odbioru)} h właściciela / dzień zakupów`) : "")
    + (x.limit_opakowan ? w("Limit na klienta", `${licz(x.limit_opakowan)} opak. składnika dziennie`) : "")
    + (x.koszt_dostawy ? w("Dowóz", `${zl2(x.koszt_dostawy)}${x.darmowa_od ? ` (darmowy od ${zl(x.darmowa_od)})` : ""}`) : "")
    + (x.minimalne_zamowienie ? w("Minimalne zamówienie", `${zl(x.minimalne_zamowienie)} / dostawa`) : "")
    + (g.length ? `<div class="komunikat ok" style="margin:6px 0">Gazetka: ${g.map(([z, r]) => `${esc(z)} −${Math.round(r * 100)}%`).join(", ")}</div>` : "");
}

function planDostaw(P, tytul) {
  if (!P || (!P.dostawy.length && !P.uwagi.length)) return "";
  const godziny = Object.values(P.czas_wlasciciela).reduce((s, x) => s + x, 0);
  return tabela(tytul, ["Dzień", "Dostawca", "Wartość", "Opłata za dowóz", "Czas właściciela"],
    P.dostawy.map((x) => [`${DNI[dzienTyg(x.data)]} <span class="podpowiedz">${+x.data.slice(8)}.${x.data.slice(5, 7)}</span>`, esc(x.dostawca), zl2(x.wartosc),
      x.oplata ? `<span class="minus">${zl2(x.oplata)}</span>` : "0", x.godziny ? `${licz(x.godziny)} h` : "–"]),
    { klasy: ["l", "l"], stopka: ["Razem", "", zl2(P.dostawy.reduce((s, x) => s + x.wartosc, 0)), zl2(P.dostawy.reduce((s, x) => s + x.oplata, 0)), godziny ? `${licz(godziny)} h` : "–"] })
    + P.uwagi.map((u) => `<div class="komunikat">${esc(u)}</div>`).join("");
}

// Zamówienia rundy – każda pozycja z przyciskiem usunięcia (pozycja = dostawca, składnik, jakość i dzień dostawy).
function listaZamowien(v, edycja) {
  const ceny = v.ceny_dostawcow, dni = dniDostaw(v), zam = mojeZam(v), id = idWybranego(v);
  if (!zam.length) return "";
  const dzien = (x) => { const d = dni && dni[+x.dzien || 0]; return d ? `${DNI[dzienTyg(d.data)]} <span class="podpowiedz">${+d.data.slice(8)}.${d.data.slice(5, 7)}</span>` : "–"; };
  const wartosc = (x) => (ceny[x.dostawca]?.[x.zasob]?.[x.jakosc] || 0) * x.ilosc;
  const usun = (i) => `<button class="btn jasny maly" data-akcja="zam-usun" data-i="${i}" title="Usuń pozycję" ${edycja ? "" : "disabled"}>✕ Usuń</button>`;
  return tabela(`Twoje zamówienia w tej rundzie${id ? ` – dostawa do lokalu ${esc(nazwaLokalu(v, id))}` : ""} (${zam.length})`, ["Dostawca", "Składnik", "Jakość", ...(dni ? ["Dostawa"] : []), "Ilość (opak.)", "Wartość", ""],
    zam.map((x, i) => [esc(x.dostawca), esc(x.zasob), gw(+x.jakosc), ...(dni ? [dzien(x)] : []), licz(x.ilosc), zl2(wartosc(x)), usun(i)]),
    { klasy: ["l", "l"], stopka: ["Razem", "", "", ...(dni ? [""] : []), "", zl2(zam.reduce((s, x) => s + wartosc(x), 0)),
      edycja ? `<button class="btn jasny maly" data-akcja="zam-wyczysc">Usuń wszystkie</button>` : ""] });
}

function zapotrzebowanie(v, kat) {
  const wynik = {};
  for (const [u, p] of Object.entries(menuLokalu(v, lokalWybrany(v)))) {
    for (const [z, ile] of Object.entries(kat.uslugi[u].zasoby)) wynik[z] = (wynik[z] || 0) + (p || 0) * ile / kat.zasoby[z].opakowanie;
  }
  return wynik;
}

function najtansze(ceny, pomin = new Set()) {
  const w = {};
  for (const [d, zas] of Object.entries(ceny)) for (const [z, jak] of Object.entries(zas)) for (const [q, c] of Object.entries(jak)) {
    if (pomin.has(d)) continue;
    if (!w[`${z}|${q}`] || c < w[`${z}|${q}`].c) w[`${z}|${q}`] = { c, d };
  }
  return w;
}

// Z4: auto-dostawca (silnik/kuchnia/auto_dostawca.py) – lokal jest na auto-dostawach albo zaopatruje się sam, całość naraz.
// Decyzja "auto_dostawy": {pozycje: [{zasob, jakosc, ilosc}]} wybranego lokalu (decyzja główna – lokal główny); null – wyłączone.
function autoDecyzja(v) {
  const d = v.decyzje, id = idWybranego(v);
  if (!id) return d.auto_dostawy;
  const w = d.w_lokalu?.[id];
  if (w && "auto_dostawy" in w) return w.auto_dostawy;
  return id === glownyLokal(v) ? d.auto_dostawy : undefined;
}
const naAuto = (v) => { const a = autoDecyzja(v); return !!a && typeof a === "object"; };
const cenyAuto = (v) => (v.ceny_dostawcow || {})[v.auto_dostawca?.zasady?.dostawca] || {};
const jakosciAuto = (v, z) => Object.keys(cenyAuto(v)[z] || {}).map(Number);
const domyslnaJakosc = (v, z) => { const j = jakosciAuto(v, z); return j.includes(2) ? 2 : j[0]; };
const zapasLokalu = (v, z) => [1, 2, 3].reduce((s, q) => s + stan(v, z, q), 0);

function sekcjaAuto(v, kat, edycja) {
  const A = v.auto_dostawca, Z = A?.zasady;
  if (!Z) return "";
  const lok = nazwaLokalu(v, idWybranego(v) || glownyLokal(v)), od = v.runda < Z.od_rundy, wl = naAuto(v);
  const dis = edycja && !od ? "" : "disabled";
  let html = `<div class="pasek">Auto-dostawca</div>
    <label class="pole-wyboru"><input type="checkbox" data-zmiana="auto-wl" ${wl ? "checked" : ""} ${dis}> <b>Auto-dostawy w lokalu ${esc(lok)}</b></label>
    <p class="podpowiedz">Auto-dostawca kupuje za Ciebie w ${esc(Z.dostawca)} (drożej niż w hurtowni) i co rano przywozi do lokalu tyle, ile tego dnia zużyjesz –
    nic nie psuje się w lokalu i nie zajmuje chłodni. Płacisz z góry za całą wpisaną ilość + ${Math.round(Z.prowizja * 100)}% prowizji
    i ${zl2(Z.abonament)} abonamentu za tydzień. Co zostanie, czeka u dostawcy na następny tydzień: ${zl2(Z.przechowanie_zl_za_litr_dzien)} za litr dziennie,
    a termin przydatności biegnie. Za mało towaru – dania wypadają z menu. Lokal na auto-dostawach nie przyjmuje Twoich zamówień od innych dostawców.
    ${od ? `<b>Auto-dostawca – od rundy ${Z.od_rundy}.</b>` : ""}${IG_AUTO}</p>`;
  if (!wl) return html;
  const ceny = cenyAuto(v), poz = autoDecyzja(v).pozycje || [], pot = zapotrzebowanie(v, kat);
  const zasoby = [...new Set([...Object.keys(pot), ...poz.map((x) => x.zasob)])].filter((z) => ceny[z]);
  let towar = 0;
  const wiersze = zasoby.map((z) => {
    const p = poz.find((x) => x.zasob === z) || {}, q = +p.jakosc || domyslnaJakosc(v, z);
    const c = ceny[z][q] || 0, ile = +p.ilosc || 0;
    towar += c * ile;
    const k = kat.zasoby[z];
    return [esc(z), `${k.typ_opakowania} (${licz(k.opakowanie)} ${k.jednostka})`, ulamek(pot[z] || 0), ulamek(zapasLokalu(v, z)),
      `<select data-zmiana="auto-jakosc" data-z="${esc(z)}" style="width:auto" ${dis}>${jakosciAuto(v, z).map((j) => `<option value="${j}" ${j === q ? "selected" : ""}>${"★".repeat(j)}</option>`).join("")}</select>`,
      `<input type="number" class="krotkie" min="0" step="1" value="${ile}" data-zmiana="auto-ilosc" data-z="${esc(z)}" ${dis}>`,
      zl2(c), zl2(c * ile * (1 + Z.prowizja))];
  });
  const prow = towar * Z.prowizja;
  html += `<div class="pasek ciemny"><span>Towar: <span class="kwota">${zl2(towar)}</span></span><span>Prowizja: <span class="kwota">${zl2(prow)}</span></span>
    <span>Abonament: <span class="kwota">${zl2(Z.abonament)}</span></span><span>Razem: <span class="kwota">${zl2(towar + prow + Z.abonament)}</span></span>
    <span style="display:flex;gap:8px;align-items:center">Wpisz wg prognozy
      <select id="auto-ad-zapas" style="width:auto"><option value="1">bez zapasu</option><option value="1.1" selected>+10% zapasu</option><option value="1.2">+20% zapasu</option></select>
      <button class="btn pom maly" data-akcja="auto-prognoza" ${dis}>Wpisz</button></span></div>`;
  html += tabela(`Zakupy auto-dostawcy na ten tydzień – ${esc(lok)} (opakowania)`, ["Składnik", "Opakowanie", "Potrzeba wg prognoz", "Zapas (lokal i u dostawcy)",
    "Jakość", "Ilość na tydzień", `Cena ${esc(Z.dostawca)}`, "Z prowizją"], wiersze, { klasy: ["l", "l"] });
  const uwagi = A.przyjete?.uwagi || [];
  html += uwagi.map((u) => `<div class="komunikat">${esc(u)}</div>`).join("");
  const zam = mojeZam(v);
  if (zam.length) html += `<div class="komunikat">Masz ${zam.length} ${zam.length === 1 ? "zamówienie" : "zamówień"} do tego lokalu u innych dostawców –
    na auto-dostawach zostaną odrzucone. <button class="btn jasny maly" data-akcja="zam-wyczysc" ${edycja ? "" : "disabled"}>Usuń je</button></div>`;
  return html;
}

function zapiszPozycje(c, zmiana) {
  const a = autoDecyzja(c.v) || {};
  const poz = zmiana((a.pozycje || []).map((x) => ({ ...x })));
  return c.zmien((d) => { zapiszWLokalu(d, c.v, "auto_dostawy", { ...a, pozycje: poz }); });
}
function ustawPozycje(lista, z, zmiany, v) {
  let p = lista.find((x) => x.zasob === z);
  if (!p) lista.push(p = { zasob: z, jakosc: domyslnaJakosc(v, z), ilosc: 0 });
  Object.assign(p, zmiany);
  return lista;
}

function wynikiAuto(v) {
  const A = v.wyniki?.auto_dostawy;
  if (!A?.lokale || !Object.keys(A.lokale).length) return "";
  const w = Object.entries(A.lokale).map(([l, x]) => [esc(nazwaLokalu(v, l)), licz(x.pozycje.length), zl2(x.towar), zl2(x.prowizja), zl2(x.abonament),
    zl2(x.towar + x.prowizja + x.abonament)]);
  return tabela("Auto-dostawca – zakupy tygodnia", ["Lokal", "Pozycje", "Towar", "Prowizja", "Abonament", "Razem"], w, { klasy: ["l"] });
}

export const dostawcy = {
  tytul: "Dostawcy", ikona: "⛟", odblokowanie: "dostawcy",
  info: `Kup składniki potrzebne do wybranych dań. Składniki możesz kupować u jednego lub kilku dostawców. Niezużyte zostają w magazynie.
    Hurtownie dowożą w swoje dni (za darmo od progu), piekarnia codziennie, producent mięsa ma minimalne zamówienie,
    a w dyskoncie kupujesz sam – taniej przy małych ilościach i z gazetką, ale tracisz czas i nie wyniesiesz więcej niż limit.`,
  decyzje({ v, kat, edycja }) {
    const ceny = v.ceny_dostawcow;
    const auto = sekcjaAuto(v, kat, edycja);
    if (naAuto(v)) return auto;
    const koszt = mojeZam(v).reduce((s, z) => s + (ceny[z.dostawca]?.[z.zasob]?.[z.jakosc] || 0) * z.ilosc, 0);
    const pot = zapotrzebowanie(v, kat), tanie = najtansze(ceny);
    const C = v.czas_wlasciciela;
    const plan = planDostaw(v.dostawy_plan, "Dostawy w tej rundzie") + (C && C.wykorzystane
      ? `<p class="podpowiedz">Czas właściciela: wolne ${licz(C.wolne, 1)} h z ${licz(C.pula, 1)} h w tej rundzie (<a data-zakladka-k="czas_wlasciciela">szczegóły</a>).</p>` : "");
    const wiersze = Object.keys(kat.zasoby).filter((z) => pot[z] || [1, 2, 3].some((q) => stan(v, z, q))).map((z) => {
      const magazyn = [1, 2, 3].reduce((s, q) => s + stan(v, z, q), 0);
      const zam = mojeZam(v).filter((x) => x.zasob === z).reduce((s, x) => s + x.ilosc, 0);
      const brak = Math.max(0, (pot[z] || 0) - magazyn - zam);
      return [esc(z), `${kat.zasoby[z].typ_opakowania} (${licz(kat.zasoby[z].opakowanie)} ${kat.zasoby[z].jednostka})`, ulamek(pot[z] || 0),
        ulamek(magazyn), licz(zam), brak > 0 ? `<span class="minus">${ulamek(brak)}</span>` : '<span class="plus">0</span>',
        [1, 2, 3].map((q) => tanie[`${z}|${q}`] ? `${gw(q)} ${zl2(tanie[`${z}|${q}`].c)} <span class="podpowiedz">${esc(tanie[`${z}|${q}`].d)}</span>` : "").join("<br>")];
    });
    // „Zamów brakujące” – tylko gdy mistrz gry go włączył (domyślnie drużyny liczą zamówienia same)
    const autoZam = v.gra.auto_zamowienia ? `<span style="display:flex;gap:8px;align-items:center">Zamów brakujące u najtańszych w jakości
      <select id="auto-jakosc" style="width:auto"><option value="3">★★★</option><option value="2">★★</option><option value="1">★</option></select>
      <select id="auto-zapas" style="width:auto"><option value="1">bez zapasu</option><option value="1.05" selected>+5% zapasu</option><option value="1.1">+10% zapasu</option></select>
      <button class="btn pom maly" data-akcja="auto-zamow" ${edycja ? "" : "disabled"}>Zamów</button></span>` : "";
    let html = `<div class="pasek ciemny"><span>Koszt zakupu${idWybranego(v) ? " (ten lokal)" : ""}: <span class="kwota">${zl2(koszt)}</span></span>${autoZam}</div>`;
    html += tabela("Zapotrzebowanie na prognozowanych klientów (opakowania)", ["Zasób", "Opakowanie", "Potrzeba wg prognoz", "W magazynie",
      "Zamówione teraz", "Brakuje", "Najtańsze oferty"], wiersze, { klasy: ["l", "l"] });
    html += listaZamowien(v, edycja);
    if (dniDostaw(v)) html += `<p class="podpowiedz">„Zamów” w grze z lokalami pomija dyskonty (odbiór osobisty, limity) – w nich kupujesz ręcznie w bazie składników.</p>`;
    html += plan;
    const wyn = v.swiezosc?.wynajem;
    if (wyn) html += `<p class="podpowiedz">Dostawcy nie przyjmują zwrotów. Co nie zmieści się w chłodni lub zamrażarce lokalu,
      jedzie do wynajętej chłodni (${zl2(wyn.zl_za_litr)} za litr, termin krótszy o ${wyn.skrocenie_dni} dni) – szczegóły w zakładce
      <a data-zakladka-k="swiezosc">Świeżość</a>.</p>`;
    html += auto + `<div class="pasek">Dostawcy</div><div class="siatka trojka">`;
    for (const d of Object.keys(ceny)) {
      const wartosc = mojeZam(v).filter((x) => x.dostawca === d).reduce((s, x) => s + (ceny[d]?.[x.zasob]?.[x.jakosc] || 0) * x.ilosc, 0);
      html += `<div class="kafel"><div class="kg">${esc(d)}</div><div class="kt">${kafelInfo(v, d)}</div>
        <div class="kd"><button class="btn czarny" data-akcja="baza" data-d="${esc(d)}">Baza składników</button>
        <div class="wiersz"><span>Zamówienie</span><span>${zl2(wartosc)}</span></div></div></div>`;
    }
    return html + `</div>`;
  },
  wyniki({ v }) {
    const straty = (v.wyniki?.zasoby || []).some((x) => "straty" in x);
    const z = (v.wyniki?.zasoby || []).map((x) => [esc(x.zasob), gw(x.jakosc), ulamek(x.poczatek), ulamek(x.zamowione), ulamek(x.wykorzystane),
      ...(straty ? [x.straty ? `<span class="minus">${ulamek(x.straty)}</span>` : "0"] : []), ulamek(x.koniec), zl2(x.wartosc)]);
    const suma = (v.wyniki?.zasoby || []).reduce((s, x) => s + x.wartosc, 0);
    const firmy = Object.keys(v.rynek?.jakosc_zasobow || {});
    const jak = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...[1, 2, 3].map((q) => ulamek(v.rynek.jakosc_zasobow[f][q]))]);
    const ze = (v.wyniki?.zasoby || []).filter((x) => x.straty), n = (v.wyniki?.zasoby || []).length;
    const lead = !n ? podsumowanie("W tej rundzie nie było składników w magazynie.") : podsumowanie([
      `W magazynie na koniec ${OKRES.dopelniacz} leży <b>${licz(n)}</b> ${n === 1 ? "pozycja" : "pozycji"} składników wartych <b>${zl2(suma)}</b>.`,
      ze.length ? `Straty (zepsute lub przeterminowane) dotyczą ${licz(ze.length)} pozycji.` : straty ? "Nic się nie zepsuło." : ""], ze.length ? "uwaga" : "ok");
    const kafle = n ? kafelkiLiczb([{ etykieta: "Pozycje w magazynie", wartosc: licz(n) }, { etykieta: "Wartość magazynu", wartosc: zl2(suma) },
      straty && { etykieta: "Pozycje ze stratami", wartosc: licz(ze.length), ton: ze.length ? "minus" : "plus" }]) : "";
    return lead + kafle + wynikiAuto(v) + planDostaw(v.wyniki?.dostawy, "Dostawy, opłaty za dowóz i zakupy w dyskontach") + zwinTabela("Składniki", ["Składnik", "Jakość", `Magazyn na początek ${OKRES.dopelniacz}`, "Zamówione", "Wykorzystane", ...(straty ? ["Straty"] : []),
      `Magazyn na koniec ${OKRES.dopelniacz}`, "Wartość"], z, { klasy: ["l"], stopka: ["Suma", "", "", "", "", ...(straty ? [""] : []), "", zl2(suma)], otwarte: true })
      + `<div class="wykres"><canvas id="w-jakosc"></canvas></div>`
      + zwinTabela("Jakość składników (zamówione opakowania)", ["Firma", "Niska ★", "Średnia ★★", "Wysoka ★★★"], jak, { klasy: ["l"] });
  },
  po({ v }, tryb) {
    if (tryb !== "wyniki") return;
    const f = Object.keys(v.rynek?.jakosc_zasobow || {});
    wykres("w-jakosc", "bar", ["Niska", "Średnia", "Wysoka"], f.map((x) => ({ label: nazwaFirmy(v, x), data: [1, 2, 3].map((q) => v.rynek.jakosc_zasobow[x][q]) })));
  },
  akcje: {
    baza: (el, c) => oknoBazy(c, el.dataset.d),
    "zam-usun": (el, c) => {
      const x = mojeZam(c.v)[+el.dataset.i];
      if (!x) return;
      const ta = (y) => y.dostawca === x.dostawca && y.zasob === x.zasob && +y.jakosc === +x.jakosc && (+y.dzien || 0) === (+x.dzien || 0)
        && lokalZam(c.v, y) === lokalZam(c.v, x);
      return c.zmien((d) => { d.zamowienia = (d.zamowienia || []).filter((y) => !ta(y)); });
    },
    "zam-wyczysc": (el, c) => c.zmien((d) => { d.zamowienia = (d.zamowienia || []).filter((x) => !tenLokal(c.v, x)); }),
    "auto-prognoza": (el, c) => {
      const zapas = +document.getElementById("auto-ad-zapas").value, pot = zapotrzebowanie(c.v, c.kat), ceny = cenyAuto(c.v);
      if (!Object.values(pot).some((p) => p > 0)) return toast("Najpierw wpisz prognozę popytu dań w zakładce Menu.");
      return zapiszPozycje(c, (lista) => {
        for (const [z, p] of Object.entries(pot)) if (ceny[z]) ustawPozycje(lista, z, { ilosc: Math.ceil(Math.max(0, p * zapas - zapasLokalu(c.v, z)) - 1e-9) }, c.v);
        return lista;
      });
    },
    "auto-zamow": async (el, c) => {
      const q = +document.getElementById("auto-jakosc").value, zapas = +document.getElementById("auto-zapas").value;
      if (!Object.values(menuLokalu(c.v, lokalWybrany(c.v))).some((p) => p > 0)) return toast("Najpierw wpisz prognozę popytu dań w zakładce Menu – zamówienia liczone są na prognozowanych klientów.");
      const nowe = planZamowien(c, q, zapas);
      if (!nowe.length) return toast("Zapas w magazynie wystarcza na prognozowanych klientów.");
      const id = idWybranego(c.v);   // kilka lokali – zastępuje tylko zamówienia wybranego lokalu
      await c.zmien((d) => { d.zamowienia = [...(d.zamowienia || []).filter((x) => !tenLokal(c.v, x)), ...nowe.map((x) => (id ? { ...x, lokal: id } : x))]; });
      toast(dniDostaw(c.v) ? "Zamówienia ustawione – dostawy rozłożone na dni wg terminów przydatności (poprzednie zastąpione)."
        : "Zamówienia ustawione (poprzednie zamówienia zastąpione).");
    },
  },
  zmiany: {
    "auto-wl": (el, c) => c.zmien((d) => { zapiszWLokalu(d, c.v, "auto_dostawy", el.checked ? { pozycje: [] } : null); }),
    "auto-ilosc": (el, c) => zapiszPozycje(c, (l) => ustawPozycje(l, el.dataset.z, { ilosc: Math.max(0, Math.round(+el.value || 0)) }, c.v)),
    "auto-jakosc": (el, c) => zapiszPozycje(c, (l) => ustawPozycje(l, el.dataset.z, { jakosc: +el.value }, c.v)),
    ilosc: async (el, c) => {
      const { d: dost, z, q, dz } = el.dataset, ilosc = Math.max(0, +el.value || 0);
      const tenDzien = (x) => dz === undefined || (+x.dzien || 0) === +dz, id = idWybranego(c.v);
      await c.zmien((d) => {
        d.zamowienia = (d.zamowienia || []).filter((x) => !(x.dostawca === dost && x.zasob === z && +x.jakosc === +q && tenDzien(x) && tenLokal(c.v, x)));
        if (ilosc > 0) d.zamowienia.push({ dostawca: dost, zasob: z, jakosc: +q, ilosc, ...(dz === undefined ? {} : { dzien: +dz }), ...(id ? { lokal: id } : {}) });
      });
      oknoBazy(c, dost);
    },
  },
};

function oknoBazy({ v, kat, edycja }, dost) {
  const ceny = v.ceny_dostawcow[dost] || {}, dni = dniDostaw(v), moje = dniDostawcy(v, dost) || [];
  const pole = (z, q, ile, dz) => `<input type="number" class="krotkie" min="0" step="1" value="${ile}" data-zmiana="ilosc" data-d="${esc(dost)}" data-z="${esc(z)}" data-q="${q}"
    ${dz === undefined ? "" : `data-dz="${dz}"`} ${edycja ? "" : "disabled"}>`;
  const w = [];
  for (const [z, jak] of Object.entries(ceny)) for (const [q, c] of Object.entries(jak)) {
    const zas = kat.zasoby[z];
    const miejsce = zas.przechowywanie && zas.przechowywanie !== "suche" ? ` · ${zas.przechowywanie === "chlodnia" ? "chłodnia" : "zamrażarka"} ${licz(zas.miejsce_l)} l` : "";
    const termin = zas.termin_dni ? `<br><span class="podpowiedz">termin ${zas.termin_dni} dni${miejsce}</span>` : "";
    const r = rabat(v, dost, z);
    w.push([`${esc(z)}<br><span class="podpowiedz">${zas.typ_opakowania} (${licz(zas.opakowanie)} ${zas.jednostka})</span>${dni ? termin : ""}`,
      gw(+q), ulamek(stan(v, z, +q)), zl2(c) + (r ? `<br><span class="plus">gazetka −${Math.round(r * 100)}%</span>` : ""),
      ...(dni ? moje.map((i) => pole(z, q, zamowione(v, dost, z, +q, i), i)) : [pole(z, q, zamowione(v, dost, z, +q))]),
      zl2(zamowione(v, dost, z, +q) * c)]);
  }
  const kolumny = dni ? moje.map((i) => `${dni[i].dzien}<div class="podpowiedz">${+dni[i].data.slice(8)}.${dni[i].data.slice(5, 7)}</div>`) : ["Zamówienie (opakowania)"];
  const x = info(v, dost);
  const id = idWybranego(v);
  okno(`Dostawca „${esc(dost)}”${id ? ` – dostawa do lokalu ${esc(nazwaLokalu(v, id))}` : ""}`, tabela(null, ["Składnik", "Jakość", "Na magazynie", "Cena", ...kolumny, "Wartość"], w, { klasy: ["l"] })
    + `<p class="podpowiedz">Ceny w tym ${OKRES.miejscownik}. Ilości wpisujesz w opakowaniach (np. napój: opakowanie 24 szt.).
      ${dni ? "Kolumny dni – dostawa rano tego dnia (tylko dni dostaw tego dostawcy); termin przydatności liczy się od dnia dostawy (Zaopatrzenie ▸ Dostawy)." : ""}
      ${dni && x.limit_opakowan ? ` Najwyżej ${licz(x.limit_opakowan)} opakowań składnika dziennie, każdy dzień zakupów to ${licz(x.godziny_odbioru)} h właściciela.` : ""}
      ${dni && x.minimalne_zamowienie ? ` Dostawa poniżej ${zl(x.minimalne_zamowienie)} nie zostanie zrealizowana.` : ""}
      ${dni && x.koszt_dostawy ? ` Dowóz ${zl2(x.koszt_dostawy)} za dostawę${x.darmowa_od ? `, darmowy od ${zl(x.darmowa_od)}` : ""}.` : ""}</p>`,
    { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">Zapisz</button>` });
}
