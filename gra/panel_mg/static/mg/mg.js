// Panel mistrza gry: zakładka Decyzje (kto wysłał, zamknięcie i cofnięcie rundy) i Wyniki (ranking, wykresy).
// Dane: GET /api/gry/<id>/mg (api/prezentacja.py: przeglad_mg).
import { esc, info, licz, nazwaRundy, okno, skrotRundy, tabela, toast, ustawKalendarz, wsk, wyczyscWykresy, wykres, zamknijOkno, zl }
  from "/static/zakladki/wspolne.js";

const ID = JSON.parse(document.getElementById("id-gry").textContent);
const URL_GRY = `/api/gry/${encodeURIComponent(ID)}`;
const ODSWIEZANIE_MS = 15000;  // nowe wysłane decyzje drużyn
const S = { p: null, tryb: "decyzje" };
const karta = document.getElementById("karta");

const csrf = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? "";
async function api(url, metoda = "GET") {
  const r = await fetch(url, { method: metoda, headers: { "X-CSRFToken": csrf() } });
  const j = await r.json();
  if (!r.ok) throw new Error(j.blad || "Błąd serwera.");
  return j;
}

async function wczytaj() {
  S.p = await api(`${URL_GRY}/mg`);
  ustawKalendarz(S.p.gra.kalendarz);
  if (!S.p.historia.length) S.tryb = "decyzje";
  rysuj();
}

function rysuj() {
  const { gra, historia } = S.p;
  wyczyscWykresy();
  const tytul = gra.zakonczona ? `Gra zakończona – ${gra.liczba_rund} rund`
    : `Runda ${gra.runda} / ${gra.liczba_rund} – ${esc(nazwaRundy(gra.runda))}`;
  const zakladka = (t, nazwa, wylaczona = false) =>
    `<a class="${S.tryb === t ? "aktywny" : ""} ${wylaczona ? "wylaczony" : ""}" data-akcja="tryb" data-t="${t}">${nazwa}</a>`;
  karta.innerHTML = `<div class="karta-glowa"><div class="tytul">${tytul}</div><div></div>
      <div class="przelacznik">${zakladka("decyzje", "Decyzje")}${zakladka("wyniki", "Wyniki", !historia.length)}</div></div>
    <div class="tresc">${S.tryb === "decyzje" ? decyzje() : wyniki()}</div>`;
  if (S.tryb === "wyniki") wykresy();
}

// --- Decyzje: kto wysłał, zamknięcie rundy -----------------------------------------------------------------------
const strona = (f) => `/gra/${encodeURIComponent(ID)}/${encodeURIComponent(f.nazwa)}`;
const prowadzi = (f) => f.bot ? `bot: ${esc(f.strategia || f.bot)}` : "drużyna";

function statusDecyzji(f, gra) {
  if (gra.zakonczona) return "–";
  if (f.bot) return `<span class="chip">decyduje przy zamknięciu</span>`;
  return f.wyslane ? `<span class="chip ok">✓ wysłane</span>` : `<span class="chip pom">czeka</span>`;
}

function decyzje() {
  const { gra, firmy } = S.p;
  const druzyny = firmy.filter((f) => !f.bot);
  const wyslaly = druzyny.filter((f) => f.wyslane).length;
  const opis = gra.zakonczona ? "Gra zakończona – wyniki w zakładce „Wyniki”."
    : `Decyzje wysłało ${wyslaly} z ${druzyny.length} ${druzyny.length === 1 ? "drużyny" : "drużyn"}. Runda zamyka się sama, gdy wyślą wszystkie.
       Możesz zamknąć ją wcześniej – drużyny bez wysłanych decyzji zagrają wtedy decyzjami zapisanymi do tej pory.`;
  const wiersze = firmy.map((f) => [`<b>${esc(f.nazwa)}</b>`, prowadzi(f), statusDecyzji(f, gra), zl(f.gotowka),
    `<a class="btn jasny maly" href="${strona(f)}" target="_blank" rel="noopener">Strona firmy</a>`]);
  const ustawienia = [["Kapitał startowy", zl(gra.kapital)], ["Ziarno losowości", esc(gra.ziarno)],
    ["Kredyt odnawialny", gra.kredyt_odnawialny === "na_biezaco" ? "na bieżąco" : "na niedobór na koniec rundy"],
    ["Ceny dostawców", gra.ceny_dostawcow === "losowe" ? "wszystkie generowane" : "z danych, dalej generowane"]];
  return `${info(opis)}
    ${tabela(gra.zakonczona ? "Firmy" : `Decyzje rundy ${gra.runda}`, ["Firma", "Prowadzi", "Decyzje", "Gotówka", ""], wiersze, { klasy: ["l", "l"] })}
    <div class="przyciski-mg">
      ${gra.zakonczona ? "" : `<button class="btn pom" data-akcja="zamknij">Zamknij rundę ${gra.runda}</button>`}
      <button class="btn jasny" data-akcja="cofnij" ${gra.runda > 1 ? "" : "disabled"}>Cofnij rundę ${Math.max(gra.runda - 1, 1)}</button>
      <a class="btn jasny" href="${URL_GRY}/eksport">Pobierz plik gry</a>
      <button class="btn jasny" data-akcja="odswiez">Odśwież</button></div>
    ${tabela("Ustawienia gry", ["", ""], ustawienia, { klasy: ["l", "l"] })}`;
}

function potwierdzZamkniecie() {
  const { gra } = S.p;
  const brak = gra.brakujace.length
    ? `<p>Decyzji nie wysłały: <b>${gra.brakujace.map(esc).join(", ")}</b>. Zagrają decyzjami zapisanymi do tej pory.</p>` : "";
  okno(`Zamknąć rundę ${gra.runda}?`, `${brak}<p>Silnik przeliczy rundę ${gra.runda} (${esc(nazwaRundy(gra.runda))}) dla wszystkich firm,
    boty podejmą swoje decyzje. Pomyłkę można cofnąć przyciskiem „Cofnij rundę”.</p>`,
  { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
    <button class="btn pom" data-akcja="zamknij-tak">Zamknij rundę</button>` });
}

function potwierdzCofniecie() {
  const r = S.p.gra.runda - 1;
  okno(`Cofnąć rundę ${r}?`, `<p>Wyniki rundy ${r} zostaną usunięte, drużyny wrócą do jej decyzji (zapisane decyzje drużyn zostają,
    decyzje botów zostaną podjęte od nowa).</p>`,
  { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
    <button class="btn pom" data-akcja="cofnij-tak">Cofnij rundę</button>` });
}

// --- Wyniki: ranking i wykresy -----------------------------------------------------------------------------------
function wyniki() {
  const { firmy, historia } = S.p;
  const ostatnia = historia[historia.length - 1];
  const kolejnosc = [...firmy].sort((a, b) => (a.miejsce ?? 1e9) - (b.miejsce ?? 1e9) || (b.dochod_suma - a.dochod_suma));
  const wiersze = kolejnosc.map((f) => [f.miejsce ?? "–", `<b>${esc(f.nazwa)}</b>${f.bot ? ` <span class="podpowiedz">(bot)</span>` : ""}`,
    wsk(f.wynik_skumulowany), wsk(f.wynik_ostatni), zl(f.dochod_ostatni), zl(f.dochod_suma), zl(f.gotowka), zl(f.zadluzenie),
    zl(f.lokaty), licz(f.pracownicy), licz(f.stanowiska)]);
  return `${info(`Ranking według wyniku działalności (karta wyników) – średnia z rund od 2, jak w Revasie.
      Ostatnia przeliczona runda: ${esc(nazwaRundy(ostatnia.runda))}.`)}
    ${tabela("Ranking", ["Miejsce", "Firma", "Wynik działalności (średnia)", `Wynik działalności (${esc(skrotRundy(ostatnia.runda))})`,
      `Dochód netto (${esc(skrotRundy(ostatnia.runda))})`, "Dochód netto (suma)", "Gotówka", "Zadłużenie", "Lokaty", "Pracownicy", "Stanowiska"],
    wiersze, { klasy: ["", "l"] })}
    <div class="wykresy-mg"><div class="wykres"><div class="tabela-tytul">Dochód netto w rundach</div><canvas id="w-dochod"></canvas></div>
      <div class="wykres"><div class="tabela-tytul">Gotówka na koniec rundy</div><canvas id="w-gotowka"></canvas></div></div>`;
}

function wykresy() {
  const { firmy, historia } = S.p;
  const etykiety = historia.map((h) => h.skrot);
  const serie = (pole) => firmy.map((f) => ({ label: f.nazwa, data: historia.map((h) => h[pole][f.nazwa] ?? null), type: "line" }));
  wykres("w-dochod", "line", etykiety, serie("dochod"));
  wykres("w-gotowka", "line", etykiety, serie("gotowka"));
}

// --- akcje -------------------------------------------------------------------------------------------------------
async function wykonaj(akcja, el) {
  if (akcja === "tryb") { S.tryb = el.dataset.t; return rysuj(); }
  if (akcja === "zamknij-okno") return zamknijOkno();
  if (akcja === "odswiez") return wczytaj();
  if (akcja === "zamknij") return potwierdzZamkniecie();
  if (akcja === "cofnij") return potwierdzCofniecie();
  if (akcja === "zamknij-tak" || akcja === "cofnij-tak") {
    zamknijOkno();
    const przed = S.p.gra.runda;
    const j = await api(`${URL_GRY}/${akcja === "zamknij-tak" ? "przelicz" : "cofnij"}`, "POST");
    toast(akcja === "zamknij-tak" ? `Runda ${przed} zamknięta.` : `Runda ${j.runda} cofnięta – drużyny znów podejmują jej decyzje.`);
    return wczytaj();
  }
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-akcja]");
  if (!el) return;
  e.preventDefault();
  wykonaj(el.dataset.akcja, el).catch((b) => toast(b.message));
});

// drużyny wysyłają decyzje ze swoich stron – odświeżamy, gdy nie jest otwarte okno
setInterval(() => {
  if (S.tryb === "decyzje" && !document.querySelector(".zaslona") && !document.hidden) wczytaj().catch(() => {});
}, ODSWIEZANIE_MS);

wczytaj().catch((b) => { karta.innerHTML = `<div class="tresc">${info(esc(b.message))}</div>`; });
