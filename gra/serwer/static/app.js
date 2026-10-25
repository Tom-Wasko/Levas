// Interfejs gry: menu, nawigacja po rundach, DECYZJE / WYNIKI, zapisywanie roboczych decyzji.
import { esc, info, MIESIACE, okno, toast, wyczyscWykresy, zamknijOkno, zl } from "./zakladki/wspolne.js";
import ZAKLADKI, { IKONY, MENU, OD_RUNDY } from "./zakladki/index.js";
import { ikona } from "./zakladki/ikony.js";

const S = { v: null, kat: null, zakladka: "dashboard", tryb: "decyzje", runda: null, d: {}, zapis: Promise.resolve(),
  nrZapytania: 0, odliczanie: null };

const postep = document.createElement("div");
postep.className = "postep";
document.body.appendChild(postep);
let aktywne = 0;
function trwa(tak) { aktywne += tak ? 1 : -1; postep.classList.toggle("trwa", aktywne > 0); }

async function api(sciezka, opcje = {}) {
  trwa(true);
  try {
    const r = await fetch(sciezka, { headers: { "Content-Type": "application/json" }, ...opcje });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.blad || `Błąd ${r.status}`);
    return j;
  } finally { trwa(false); }
}

const kopia = (x) => JSON.parse(JSON.stringify(x ?? {}));

// Wczytanie widoku rundy. Szybkie klikanie strzałek: liczy się tylko ostatnie zapytanie.
async function wczytaj(runda = S.runda) {
  const nr = ++S.nrZapytania;
  const q = runda ? `?runda=${runda}` : "";
  const v = await api(`/api/gry/${GRA}/widok/${encodeURIComponent(FIRMA)}${q}`);
  if (nr === S.nrZapytania) ustaw(v);
}

function ustaw(v) {
  S.v = v;
  S.runda = v.runda;
  S.d = kopia(v.decyzje);
  const z = ZAKLADKI[S.zakladka];
  if (!z || !dostepna(z)) S.zakladka = "dashboard";
  if (S.tryb === "wyniki" && !maWyniki(ZAKLADKI[S.zakladka])) S.tryb = "decyzje";
  if (S.tryb === "decyzje" && !ZAKLADKI[S.zakladka].decyzje && maWyniki(ZAKLADKI[S.zakladka])) S.tryb = "wyniki";
  rysuj();
}

// --- zmiana decyzji: fn modyfikuje roboczy szkic, potem zapis i odświeżenie widoku --------------
async function zmien(fn) {
  if (!S.v.edycja) return toast("Podgląd poprzedniej rundy – decyzji nie można zmieniać.");
  if (S.v.wyslane) return toast("Decyzje są wysłane. Wróć do podejmowania decyzji w zakładce „Wyślij decyzje”.");
  fn(S.d);
  S.zapis = S.zapis.then(async () => {
    const nr = ++S.nrZapytania;
    try {
      const v = await api(`/api/gry/${GRA}/decyzje/${encodeURIComponent(FIRMA)}`, { method: "PUT", body: JSON.stringify(S.d) });
      if (nr === S.nrZapytania) ustaw(v);
    } catch (e) { toast(e.message); await wczytaj(); }
  });
  return S.zapis;
}

const odbl = (k) => S.v.odblokowane.includes(k);
function dostepna(z) { return !z.odblokowanie || (typeof z.odblokowanie === "function" ? z.odblokowanie(S.v) : odbl(z.odblokowanie)); }
const maWyniki = (z) => !!(z && z.wyniki && S.v.wyniki && (!z.wynikiOd || S.v.runda >= z.wynikiOd));
const kluczZakladki = (z) => Object.keys(ZAKLADKI).find((k) => ZAKLADKI[k] === z);

const ctx = () => ({ v: S.v, kat: S.kat, d: S.d, edycja: S.v.edycja && !S.v.wyslane, zmien, api, wczytaj, ustaw,
  idz: (k, tryb) => { S.zakladka = k; S.tryb = tryb || (ZAKLADKI[k].decyzje ? "decyzje" : "wyniki"); rysuj(); } });

// --- rysowanie ---------------------------------------------------------------------------------
function rysujMenu() {
  const czerwone = S.v.lista_bledow.filter((b) => b.poziom === "czerwony").length;
  document.getElementById("menu").innerHTML = MENU.map((poz) => {
    const z = ZAKLADKI[poz.klucz] || {};
    const pod = poz.pod ? `<div class="pod">${poz.pod.map((k) => `<a data-zakladka="${k}" class="${dostepna(ZAKLADKI[k]) ? "" : "zablokowana"} ${k === S.zakladka ? "aktywna" : ""}">
      ${ikona(IKONY[k], 18)}${ZAKLADKI[k].tytul}${!dostepna(ZAKLADKI[k]) && OD_RUNDY[k] ? `<span class="od">od rundy ${OD_RUNDY[k]}</span>` : ""}</a>`).join("")}</div>` : "";
    const aktywna = poz.klucz === S.zakladka || (poz.pod || []).includes(S.zakladka);
    const zablokowana = poz.pod ? !poz.pod.some((k) => dostepna(ZAKLADKI[k])) : !dostepna(z);
    const cel = poz.pod ? poz.pod.find((k) => dostepna(ZAKLADKI[k])) || poz.pod[0] : poz.klucz;
    const znaczek = poz.klucz === "lista_bledow" && czerwone && S.v.edycja ? `<span class="znaczek">${czerwone}</span>` : "";
    const tytulOd = zablokowana && OD_RUNDY[cel] ? ` title="Dostępne od rundy ${OD_RUNDY[cel]}"` : "";
    return `<div class="poz ${poz.klasa || ""}" data-dzial="${poz.klucz}"><a data-zakladka="${cel}" class="${aktywna ? "aktywna" : ""} ${zablokowana ? "zablokowana" : ""}"${tytulOd}>
      ${ikona(poz.ikona)}${poz.tytul}${znaczek}</a>${pod}</div>`;
  }).join("");
}

function podzakladki() {
  const grupa = MENU.find((p) => (p.pod || []).includes(S.zakladka));
  if (!grupa) return "";
  return `<div class="podzakladki">${grupa.pod.map((k) => `<a data-zakladka="${k}" data-pod="1" class="${k === S.zakladka ? "aktywna" : ""} ${dostepna(ZAKLADKI[k]) ? "" : "zablokowana"}">
    ${ikona(IKONY[k], 16)}${ZAKLADKI[k].tytul}</a>`).join("")}</div>`;
}

function podsumowanie(v) {
  if (!v.edycja || S.zakladka === "dashboard") return "";
  const koszty = v.koszty_decyzji.reduce((s, p) => s + p.towary + p.wynagrodzenia + p.pozostale - p.przychod_pozostaly, 0);
  const czerwone = v.lista_bledow.filter((b) => b.poziom === "czerwony").length;
  const status = v.wyslane ? `<span class="chip ok">${ikona("ok", 14)}Wysłane</span>` : `<span class="chip pom">W trakcie</span>`;
  return `<div class="podsumowanie">
    <div>${ikona("portfel")}<div><div class="et">Saldo po decyzjach</div><div class="wa ${v.stan.gotowka < 0 ? "minus" : ""}">${zl(v.stan.gotowka)}</div></div></div>
    <div>${ikona("wykres")}<div><div class="et">Koszty decyzji tej rundy</div><div class="wa">${zl(koszty)}</div></div></div>
    <div><a data-zakladka-k="lista_bledow">${ikona("uwaga")}</a><div><div class="et">Poważne braki</div>
      <div class="wa ${czerwone ? "minus" : ""}"><a data-zakladka-k="lista_bledow">${czerwone ? `${czerwone} – zobacz listę` : "brak"}</a></div></div></div>
    <div>${ikona("zegar")}<div><div class="et">Decyzje rundy ${v.runda}</div><div class="wa">${status}</div></div></div></div>`;
}

// Oś rund: każda runda to jeden element (w motywach: talerz na sztandze, kolumna grafiku, pole tablicy wyników).
function osRund(v, runda) {
  const lmin = v.gra.runda_startowa || 1, lmax = v.gra.zakonczona ? v.gra.runda - 1 : v.gra.runda;
  const dochod = Object.fromEntries((v.historia || []).map((h) => [h.runda, h.dochod_netto]));
  let html = "";
  for (let r = lmin; r <= v.gra.liczba_rund; r++) {
    const rozegrana = r < v.gra.runda, strata = dochod[r] != null && dochod[r] < 0;
    const opis = dochod[r] != null ? `${MIESIACE[r - 1]}: dochód netto ${zl(dochod[r])}`
      : rozegrana ? `${MIESIACE[r - 1]}: rozegrana` : r === v.gra.runda ? `${MIESIACE[r - 1]}: bieżąca runda` : `${MIESIACE[r - 1]}: przed Tobą`;
    const kl = [rozegrana ? "rozegrana" : "", strata ? "strata" : "", r === v.gra.runda && !v.gra.zakonczona ? "biezaca" : "",
      r === runda ? "ogladana" : "", r > lmax ? "przyszla" : ""].filter(Boolean).join(" ");
    html += `<span class="runda-os ${kl}" data-r="${r}" ${r <= lmax ? `data-akcja="runda-idz"` : ""} title="${esc(opis)}"><b>${MIESIACE[r - 1].slice(0, 3)}</b></span>`;
  }
  return `<div class="os-rund" aria-label="Rundy gry">${html}</div>`;
}

function glowa(v, z, tryb, decyzje, wyniki, runda) {
  const lmin = v.gra.runda_startowa || 1, lmax = v.gra.zakonczona ? v.gra.runda - 1 : v.gra.runda;
  return `<div class="karta-glowa">
      <div class="tytul">${ikona(IKONY[S.zakladka])}${z.tytulPelny || z.tytul}</div>
      <div class="nawigator">
        <span class="strzalka ${runda <= lmin ? "wylaczona" : ""}" data-akcja="runda" data-d="-1" title="Poprzednia runda">${ikona("lewo", 18)}</span>
        <span class="miesiac" id="nawigator-miesiac">${MIESIACE[runda - 1]} (<b>runda nr ${runda}</b>)${runda === v.gra.runda && !v.gra.zakonczona ? "" : " · podgląd"}</span>
        <span class="strzalka ${runda >= lmax ? "wylaczona" : ""}" data-akcja="runda" data-d="1" title="Następna runda">${ikona("prawo", 18)}</span>
        ${osRund(v, runda)}
      </div>
      <div class="przelacznik">
        ${decyzje ? `<a class="${tryb === "decyzje" ? "aktywny" : ""}" data-akcja="tryb" data-t="decyzje">Decyzje</a>` : ""}
        ${z.wyniki ? `<a class="${tryb === "wyniki" ? "aktywny" : ""} ${wyniki ? "" : "wylaczony"}" data-akcja="tryb" data-t="wyniki">Wyniki</a>` : ""}
      </div>
    </div>`;
}

// zapamiętanie pola z kursorem, żeby po odświeżeniu widoku wrócić do niego (wpisywanie kilku wartości z rzędu)
function kluczPola(el) {
  if (!el || !el.dataset || !el.matches("input, select")) return null;
  return JSON.stringify({ ...el.dataset, id: el.id || "" });
}
function znajdzPole(klucz) {
  if (!klucz) return null;
  return [...document.querySelectorAll("#karta input, #karta select")].find((el) => kluczPola(el) === klucz);
}

function rysuj() {
  const fokus = kluczPola(document.activeElement);
  const przewiniecie = window.scrollY;
  wyczyscWykresy();
  rysujMenu();
  const v = S.v, z = ZAKLADKI[S.zakladka];
  const grupa = MENU.find((p) => p.klucz === S.zakladka || (p.pod || []).includes(S.zakladka));
  document.body.dataset.dzial = grupa ? grupa.klucz : "dashboard";
  document.getElementById("nazwa-firmy").textContent = v.dashboard.nazwa;
  const st = document.getElementById("status-gry");
  st.innerHTML = `<span class="chip">${esc(v.gra.nazwa)}</span><span class="chip pom">${ikona("portfel", 14)}${zl(v.dashboard.saldo)}</span>`
    + (v.gra.zakonczona ? `<span class="chip">Gra zakończona</span>` : v.wyslane && v.edycja
      ? `<span class="chip ok">Czekamy na: ${esc(v.gra.brakujace.join(", ") || "–")}</span>` : "");
  const c = ctx();
  const wyniki = maWyniki(z), decyzje = !!z.decyzje;
  const tryb = S.tryb === "wyniki" && wyniki ? "wyniki" : decyzje ? "decyzje" : "wyniki";
  const tresc = tryb === "wyniki" ? z.wyniki(c) : z.decyzje(c);
  const podglad = !v.edycja && v.runda < v.gra.runda
    ? `<div class="komunikat">Podgląd rundy ${v.runda} (${v.miesiac}) – decyzje z tej rundy są tylko do odczytu. Wyniki pokazują skutki poprzedniego miesiąca.</div>` : "";
  const wyslane = v.edycja && v.wyslane && tryb === "decyzje" && S.zakladka !== "wyslij"
    ? `<div class="komunikat ok">Decyzje tej rundy są wysłane. Aby je zmienić, wróć do podejmowania decyzji w zakładce „Wyślij decyzje”.</div>` : "";
  document.getElementById("karta").innerHTML = glowa(v, z, tryb, decyzje, wyniki, v.runda) + podzakladki()
    + (tryb === "decyzje" ? podsumowanie(v) : "")
    + `${z.info ? info(typeof z.info === "function" ? z.info(c, tryb) : z.info) : ""}<div class="tresc">${podglad}${wyslane}${tresc}</div>`;
  history.replaceState(null, "", `#${S.zakladka}${tryb === "wyniki" ? "/wyniki" : ""}`);
  if (z.po) z.po(c, tryb);
  const pole = znajdzPole(fokus);
  if (pole) pole.focus({ preventScroll: true });
  window.scrollTo({ top: przewiniecie });
}

// strzałki miesięcy: natychmiastowa zmiana napisu, wczytanie po krótkiej pauzie (można klikać szybko)
function przesunRunde(o) { idzDoRundy((S.celRundy ?? S.v.runda) + o); }

function idzDoRundy(r) {
  const v = S.v;
  const lmin = v.gra.runda_startowa || 1, lmax = v.gra.zakonczona ? v.gra.runda - 1 : v.gra.runda;
  const cel = Math.min(lmax, Math.max(lmin, r));
  S.celRundy = cel;
  document.querySelectorAll(".os-rund .runda-os").forEach((s) => s.classList.toggle("ogladana", +s.dataset.r === cel));
  const napis = document.getElementById("nawigator-miesiac");
  if (napis) napis.innerHTML = `${MIESIACE[cel - 1]} (<b>runda nr ${cel}</b>)${cel === v.gra.runda && !v.gra.zakonczona ? "" : " · podgląd"}`;
  document.querySelectorAll(".nawigator .strzalka").forEach((s) => {
    s.classList.toggle("wylaczona", (+s.dataset.d < 0 && cel <= lmin) || (+s.dataset.d > 0 && cel >= lmax));
  });
  clearTimeout(S.odliczanie);
  S.odliczanie = setTimeout(async () => {
    try { await wczytaj(cel); } catch (e) { toast(e.message); }
    S.celRundy = null;
  }, 220);
}

// --- zdarzenia (delegacja) -----------------------------------------------------------------------
document.addEventListener("click", async (e) => {
  const zak = e.target.closest("[data-zakladka], [data-zakladka-k]");
  if (zak && (zak.closest("#menu") || zak.dataset.pod || zak.dataset.zakladkaK)) {
    const k = zak.dataset.zakladka || zak.dataset.zakladkaK;
    if (!dostepna(ZAKLADKI[k])) return;
    S.zakladka = k;
    S.tryb = ZAKLADKI[k].decyzje ? (S.v.edycja ? "decyzje" : maWyniki(ZAKLADKI[k]) ? "wyniki" : "decyzje") : "wyniki";
    rysuj();
    if (zak.closest("#menu")) window.scrollTo({ top: 0 });
    return;
  }
  if (e.target.closest(".logo")) { S.zakladka = "dashboard"; rysuj(); return; }
  const el = e.target.closest("[data-akcja]");
  if (!el) return;
  const a = el.dataset.akcja;
  try {
    if (a === "zamknij-okno") return zamknijOkno();
    if (a === "runda") return przesunRunde(+el.dataset.d);
    if (a === "runda-idz") return idzDoRundy(+el.dataset.r);
    if (a === "tryb") { S.tryb = el.dataset.t; return rysuj(); }
    for (const z of Object.values(ZAKLADKI)) {
      if (z.akcje && z.akcje[a]) return await z.akcje[a](el, ctx(), e);
    }
  } catch (err) { toast(err.message); console.error(err); }
});

document.addEventListener("change", async (e) => {
  const el = e.target.closest("[data-zmiana]");
  if (!el) return;
  try {
    for (const z of Object.values(ZAKLADKI)) {
      if (z.zmiany && z.zmiany[el.dataset.zmiana]) return await z.zmiany[el.dataset.zmiana](el, ctx(), e);
    }
  } catch (err) { toast(err.message); console.error(err); }
});

// Enter w polu liczbowym = zatwierdzenie (jak Tab)
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.matches("#karta input[data-zmiana]")) e.target.dispatchEvent(new Event("change", { bubbles: true }));
});

// --- start ---------------------------------------------------------------------------------------
(async () => {
  try {
    S.kat = await api("/api/katalogi");
    const [h, tryb] = location.hash.slice(1).split("/");
    if (ZAKLADKI[h]) S.zakladka = h;
    if (tryb === "wyniki") S.tryb = "wyniki";
    await wczytaj();
  } catch (e) {
    document.getElementById("karta").innerHTML = `<div class="ladowanie">Nie udało się wczytać gry: ${esc(e.message)}</div>`;
  }
})();

// zmiana motywu: wykresy biorą kolory z motywu, więc widok rysujemy od nowa
document.addEventListener("motyw", () => { if (S.v) rysuj(); });

window.addEventListener("hashchange", () => {
  const [h, tryb] = location.hash.slice(1).split("/");
  if (ZAKLADKI[h] && h !== S.zakladka) { S.zakladka = h; S.tryb = tryb === "wyniki" ? "wyniki" : "decyzje"; rysuj(); }
});
export { S, okno, kluczZakladki };
