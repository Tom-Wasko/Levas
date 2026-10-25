// Pulpit, karta wyników, lista błędów, wysyłanie decyzji, analiza (podgląd wyniku rundy).
import { esc, gw, licz, nazwaFirmy, nazwaUslugi, proc, tabela, toast, wsk, wykres, zl, zl2 } from "./wspolne.js";
import { ikona } from "./ikony.js";

const WSKAZNIKI = [["wynik_dzialalnosci", "Wynik działalności"], ["wynik_ekonomiczny", "Wynik ekonomiczny"],
  ["zadowolenie_pracownikow", "Zadowolenie pracowników"], ["zadowolenie_klientow", "Zadowolenie klientów"],
  ["rozwoj_firmy", "Rozwój firmy"], ["wskaznik_zadluzenia", "Wskaźnik zadłużenia"]];

let skumulowana = false;

function planRundy(v, kat) {
  // lista kontrolna decyzji bieżącej rundy (na podstawie stanu po roboczych decyzjach)
  const r = v.runda, st = v.stan, braki = Object.values(st.gotowe_uslugi || {}).flat();
  const ile = (typ) => st.stanowiska.filter((s) => s.typ === typ).length;
  const zaw = (tekst) => braki.some((b) => b.includes(tekst));
  const punkty = [
    ["oferta", "Oferta", Object.keys(st.oferta).length > 0, `${Object.keys(st.oferta).length} dań w menu`],
    ["stanowiska", "Stanowiska", ile("kuchnia") > 0 && ile("kasa") > 0, `${ile("kuchnia")} kuchnia · ${ile("kasa")} kasa`],
    ["bank", "Bank i biuro", !!st.bank && !!st.biuro, st.bank && st.biuro ? `${st.bank} · ${st.biuro}` : "wybierz bank i biuro"],
  ];
  if (r >= 2) punkty.push(
    ["sprzet", "Sprzęt i kuchnia", Object.keys(st.oferta).length > 0 && !zaw("stanowiska z pracownikiem"), zaw("stanowiska z pracownikiem") ? "brakuje sprzętu lub kucharza" : "wszystkie dania mają stanowisko"],
    ["zatrudnienie", "Kasa", !zaw("obsadzonego stanowiska"), zaw("obsadzonego stanowiska") ? "brak kasjera z kompletem sprzętu" : "jest"],
    ["dostawcy", "Składniki", !zaw("brak składnika"), zaw("brak składnika") ? "brak składników w magazynie" : "w magazynie"],
    ["sprzedaz", "Ceny", !zaw("włączone do sprzedaży"), zaw("włączone do sprzedaży") ? "nie wszystkie dania mają cenę" : "ustawione"]);
  const html = punkty.map(([k, n, ok, opis]) => `<a data-zakladka-k="${k}"><span class="st ${ok ? "ok" : "nie"}">${ok ? "✓" : "!"}</span>
    <span>${n}<small>${esc(opis)}</small></span></a>`).join("");
  return `<div class="sekcja-tytul">Plan rundy ${r} (${esc(v.miesiac)})</div><div class="plan">${html}
    <a data-zakladka-k="wyslij"><span class="st ${v.wyslane ? "ok" : "inf"}">${v.wyslane ? "✓" : "→"}</span><span>Wyślij decyzje<small>${v.wyslane ? "wysłane" : "gdy wszystko gotowe"}</small></span></a></div>`;
}

export const dashboard = {
  tytul: "Dashboard", ikona: "▦",
  decyzje({ v, kat }) {
    const d = v.dashboard, p = kat.parametry;
    const kafel = (t, ik, tresc) => `<div class="kafel"><div class="kg"><span>${t}</span>${ikona(ik, 18)}</div><div class="kt">${tresc}</div></div>`;
    const ludzie = v.gra.firmy.filter((f) => !f.bot).map((f) => f.nazwa);
    const status = ludzie.length > 1 ? `<div class="komunikat">Gracze w tej grze: ${ludzie.map((n) =>
      `${esc(n)} ${v.gra.wyslane.includes(n) ? '<span class="pigulka ok">wysłał</span>' : '<span class="pigulka nie">decyduje</span>'}`).join(" · ")}
      · <a href="/gra/${GRA}">zmień firmę</a></div>` : "";
    const boty = v.gra.firmy.filter((f) => f.bot).map((f) => esc(f.nazwa));
    const stali = (v.gra.konkurenci_stali || []).map((k) => esc(k.nazwa));
    const rynek = [boty.length ? `boty: ${boty.join(", ")}` : "", stali.length ? `stałe ceny: ${stali.join(", ")}` : ""].filter(Boolean).join(" · ");
    return `${status}${v.edycja ? planRundy(v, kat) : ""}<div class="sekcja-tytul">Twoja firma</div><div class="dash">
      ${kafel("Nazwa i logo firmy", "osoba", `<div><div class="awatar">${esc(d.nazwa.slice(0, 2).toUpperCase())}</div>${esc(d.nazwa)}</div>`)}
      ${kafel("Miejsce", "karta", d.miejsce ? `${d.miejsce} / ${d.liczba_firm}` : `<span class="maly-tekst">Ranking dostępny od rundy 3</span>`)}
      ${kafel(`Liczba rund w grze`, "zegar", `<div>${Math.min(v.gra.runda, v.gra.liczba_rund)} / ${v.gra.liczba_rund}
        <div class="maly-tekst">${v.gra.zakonczona ? "Gra zakończona" : `Bieżąca runda: ${v.gra.runda}`} · ${v.gra.firmy.length + stali.length} firm na rynku</div>
        ${rynek ? `<div class="podpowiedz">${rynek}</div>` : ""}</div>`)}
      ${kafel("Dochód netto", "wykres", `<span class="${d.dochod_netto < 0 ? "minus" : ""}">${zl(d.dochod_netto)}</span>`)}
      ${kafel("Saldo konta", "portfel", zl(d.saldo))}
      ${kafel("Minimalne wynagrodzenie brutto", "zatrudnienie", `${licz(kat.placa_minimalna)} PLN / miesiąc`)}
      ${kafel("Czas pracy pracownika i sprzętów", "zegar", `<div>${p.godziny}H / MIESIĄC<div class="maly-tekst">Otwarte: 9:00–17:00</div></div>`)}
      ${kafel("Stawki amortyzacji", "procent", `<div class="maly-tekst">Sprzęt powyżej ${licz(p.amortyzacja_prog)} PLN: 10%<br>Sprzęt do ${licz(p.amortyzacja_prog)} PLN: 100%</div>`)}
      ${kafel("Pozostałe informacje", "finanse", `<div class="maly-tekst">Podatek dochodowy ${proc(p.cit, 0)}<br>Składki ZUS pracodawcy ${proc(p.zus, 0)}
        <br>Kredyt odnawialny: ${v.gra.kredyt_odnawialny === "na_biezaco" ? "na bieżąco" : "jak w grze (jednocześnie)"}
        ${d.lokaty ? `<br>Lokaty: ${zl(d.lokaty)}` : ""}${d.zadluzenie ? `<br>Zadłużenie: ${zl(d.zadluzenie)}` : ""}</div>`)}
    </div>${(v.historia || []).length > 1 ? `<div class="wykres"><canvas id="w-dash"></canvas></div>` : ""}`;
  },
  po({ v }) {
    const h = v.historia || [];
    if (h.length > 1) wykres("w-dash", "bar", h.map((x) => x.miesiac), [{ label: "Dochód netto", data: h.map((x) => x.dochod_netto) },
      { label: "Saldo konta", data: h.map((x) => x.gotowka), type: "line", kolor: "--wykres-linia" }]);
  },
};

export const karta_wynikow = {
  tytul: "Karta wyników", ikona: "☷", wynikiOd: 3, odblokowanie: (v) => v.runda >= 3,
  info: () => "Karta wyników pokazuje rezultaty decyzji podjętych w poprzedniej rundzie.",
  wyniki({ v }) {
    const karty = skumulowana ? v.karta_skumulowana : v.rynek.karta;
    const firmy = Object.keys(karty || {}).sort((a, b) => karty[b].wynik_dzialalnosci - karty[a].wynik_dzialalnosci);
    const wiersze = firmy.map((f) => [`${f === v.firma ? "<b>" : ""}${esc(nazwaFirmy(v, f))}${f === v.firma ? "</b>" : ""}`,
      ...WSKAZNIKI.map(([k]) => wsk(karty[f][k]))]);
    return `<div style="display:flex;gap:10px;justify-content:center">
        <button class="btn ${skumulowana ? "jasny" : "pom"}" data-akcja="karta-skum" data-s="0">Karta wyników</button>
        <button class="btn ${skumulowana ? "pom" : "jasny"}" data-akcja="karta-skum" data-s="1" ${v.runda >= 4 ? "" : "disabled"}>Skumulowana karta wyników</button></div>
      ${tabela("Ranking zespołów", ["Firma", ...WSKAZNIKI.map(([, n]) => n)], wiersze, { klasy: ["l"] })}
      <div class="wykres"><canvas id="w-karta"></canvas></div>
      <div class="wykres"><canvas id="w-historia"></canvas></div>
      <p class="podpowiedz">Wynik działalności = iloczyn pozostałych wskaźników (0 przy stracie). Wynik ekonomiczny = dochód netto / 20 000 PLN.
      Zadowolenie i rozwój liczone są ze skalibrowanych wzorów (dane/zalozenia.yaml) – mogą odbiegać od prawdziwej gry.</p>`;
  },
  po({ v }) {
    const karty = skumulowana ? v.karta_skumulowana : v.rynek.karta;
    const firmy = Object.keys(karty || {});
    wykres("w-karta", "bar", WSKAZNIKI.map(([, n]) => n), firmy.map((f) => ({ label: nazwaFirmy(v, f), data: WSKAZNIKI.map(([k]) => karty[f][k]) })));
    const h = (v.historia || []).filter((x) => x.karta);
    wykres("w-historia", "line", h.map((x) => x.miesiac), [{ label: "Twój wynik działalności", data: h.map((x) => x.karta.wynik_dzialalnosci) },
      { label: "Wynik ekonomiczny", data: h.map((x) => x.karta.wynik_ekonomiczny) }]);
  },
  akcje: { "karta-skum": (el, c) => { skumulowana = el.dataset.s === "1"; c.idz("karta_wynikow", "wyniki"); } },
};

const DOKAD = { oferta: "oferta", finanse_bank: "bank", finanse_biuro: "biuro", hr_zatrudnienie: "zatrudnienie",
  inwestycje_sprzet: "sprzet", dostawcy: "dostawcy", sprzedaz: "sprzedaz" };

export const lista_bledow = {
  tytul: "Lista błędów", ikona: "☰",
  info: "Sprawdź, czy podjęto wszystkie najważniejsze decyzje. Czerwone – poważne braki, pomarańczowe i niebieskie – informacyjne.",
  decyzje({ v }) {
    if (!v.lista_bledow.length) return `<div class="komunikat ok">Brak uwag – wszystkie najważniejsze decyzje są podjęte.</div>`;
    const kol = { czerwony: 0, pomaranczowy: 1, niebieski: 2 };
    return [...v.lista_bledow].sort((a, b) => kol[a.poziom] - kol[b.poziom]).map((b) =>
      `<div class="blad ${b.poziom}"><span class="tx">${esc(b.tekst)}</span>
       ${DOKAD[b.zakladka] ? `<button class="btn jasny maly" data-akcja="popraw" data-z="${DOKAD[b.zakladka]}">Popraw</button>` : ""}</div>`).join("");
  },
  akcje: { popraw: (el, c) => c.idz(el.dataset.z, "decyzje") },
};

export const wyslij = {
  tytul: "Wyślij decyzje", ikona: "✉", odblokowanie: (v) => !v.gra.zakonczona,
  decyzje({ v }) {
    const czerwone = v.lista_bledow.filter((b) => b.poziom === "czerwony").length;
    const ludzie = v.gra.firmy.filter((f) => !f.bot);
    const stan = ludzie.map((f) => `<tr><td class="l">${esc(f.nazwa)}</td><td>${v.gra.wyslane.includes(f.nazwa) ? '<span class="pigulka ok">wysłane</span>' : '<span class="pigulka nie">w trakcie</span>'}</td></tr>`).join("");
    if (!v.edycja) return `<div class="komunikat">To podgląd poprzedniej rundy.</div>`;
    return `${czerwone ? `<div class="komunikat zly">Na liście błędów jest ${czerwone} poważnych uwag. Możesz mimo to wysłać decyzje.</div>` : ""}
      ${v.wyslane
        ? `<div class="komunikat ok">Decyzje wysłane. Runda przeliczy się, gdy wszyscy gracze wyślą decyzje.</div>
           <button class="btn czarny" data-akcja="cofnij-wyslanie">Wróć do podejmowania decyzji w bieżącej rundzie</button>`
        : `<p>Po wysłaniu decyzji gra czeka, aż wszyscy gracze wyślą swoje. Wtedy runda przelicza się automatycznie
           (boty decydują same).</p><button class="btn zielony" data-akcja="wyslij">Wyślij decyzje</button>`}
      ${ludzie.length > 1 ? `<div class="tabela-tytul">Gracze</div><div class="tab-wrap"><table class="t">${stan}</table></div>
        <p><button class="btn jasny" data-akcja="wymus">Przelicz rundę bez czekania (brakujący gracze: puste decyzje)</button></p>` : ""}
      <hr style="margin:28px 0;border:0;border-top:1px solid var(--linia)">
      <p class="podpowiedz">Tryb treningowy: możesz cofnąć ostatnią przeliczoną rundę i zmienić swoje decyzje (decyzje botów zostaną policzone od nowa).</p>
      <button class="btn jasny" data-akcja="cofnij-runde" ${v.gra.runda > (v.gra.runda_startowa || 1) ? "" : "disabled"}>Cofnij ostatnią rundę</button>`;
  },
  akcje: {
    wyslij: async (el, c) => {
      const v = await c.api(`/api/gry/${GRA}/wyslij/${encodeURIComponent(FIRMA)}`, { method: "POST", body: JSON.stringify({ wyslane: true }) });
      if (v.przeliczono) { toast(`Runda przeliczona – teraz ${v.miesiac} (runda ${v.runda}).`); c.ustaw(v); c.idz("dashboard"); }
      else c.ustaw(v);
    },
    "cofnij-wyslanie": async (el, c) => c.ustaw(await c.api(`/api/gry/${GRA}/wyslij/${encodeURIComponent(FIRMA)}`, { method: "POST", body: JSON.stringify({ wyslane: false }) })),
    wymus: async (el, c) => { await c.api(`/api/gry/${GRA}/przelicz`, { method: "POST" }); toast("Runda przeliczona."); await c.wczytaj(null); c.idz("dashboard"); },
    "cofnij-runde": async (el, c) => {
      if (!confirm("Cofnąć ostatnią przeliczoną rundę?")) return;
      await c.api(`/api/gry/${GRA}/cofnij`, { method: "POST" }); toast("Cofnięto rundę."); await c.wczytaj(null);
    },
  },
};

let podglad = null;
const METRYKI = [
  ["Klienci (popyt)", (w) => licz(Object.values(w.sprzedaz).reduce((a, s) => a + s.popyt, 0))],
  ["Obsłużeni klienci", (w) => licz(Object.values(w.sprzedaz).reduce((a, s) => a + s.sprzedaz, 0))],
  ["Utracona sprzedaż", (w) => licz(Object.values(w.sprzedaz).reduce((a, s) => a + s.utracona, 0))],
  ["Przychody", (w) => zl(w.kpir.przychody)], ["Koszty", (w) => zl(w.kpir.koszty)],
  ["Dochód do opodatkowania", (w) => zl(w.kpir.dochod)], ["Podatek", (w) => zl(w.kpir.podatek)],
  ["<b>Dochód netto</b>", (w) => `<b>${zl(w.kpir.dochod_netto)}</b>`], ["Saldo po rundzie", (w) => zl(w.gotowka)],
  ...WSKAZNIKI.map(([k, n]) => [n, (w) => wsk(w.karta?.[k])]),
];

export const analiza = {
  tytul: "Analiza", tytulPelny: "Analiza – co jeśli", ikona: "◎", odblokowanie: (v) => v.edycja && v.runda >= 2,
  info: "Dodatek spoza REVAS: przewidywany wynik bieżącej rundy dla Twoich decyzji (boty decydują jak zwykle). Zapisz kilka wariantów decyzji i porównaj je. To przewidywanie modelu, nie wynik gry.",
  decyzje({ v, kat }) {
    const warianty = v.warianty || [];
    let html = `<div class="kafel"><div class="kg">Warianty decyzji tej rundy</div><div class="kt">
      ${warianty.length ? warianty.map((n) => `<div class="wiersz" style="align-items:center"><span>${esc(n)}</span><span>
        <button class="btn jasny maly" data-akcja="wczytaj-wariant" data-n="${esc(n)}">Wczytaj do decyzji</button>
        <button class="btn jasny maly" data-akcja="usun-wariant" data-n="${esc(n)}">Usuń</button></span></div>`).join("")
        : `<p class="podpowiedz">Brak zapisanych wariantów. Ustaw decyzje w zakładkach i zapisz je tutaj jako wariant, potem zmień decyzje i zapisz kolejny.</p>`}
      </div><div class="kd" style="flex-direction:row;flex-wrap:wrap">
        <button class="btn czarny" data-akcja="zapisz-wariant" ${v.wyslane ? "disabled" : ""}>Zapisz bieżące decyzje jako wariant</button>
        <button class="btn pom" data-akcja="porownaj">Policz i porównaj (bieżące + warianty)</button></div></div>`;
    const p = podglad && podglad.runda === v.runda ? podglad.warianty : null;
    if (!p) return html;
    html += tabela("Porównanie wariantów (przewidywanie)", ["", ...p.map((x) => esc(x.nazwa))],
      METRYKI.map(([n, f]) => [n, ...p.map((x) => f(x.wyniki))]), { klasy: ["l"] });
    const uslugi = [...new Set(p.flatMap((x) => Object.keys(x.wyniki.sprzedaz)))];
    html += tabela("Sprzedaż dań: popyt / obsłużeni (przewidywanie)", ["Danie", ...p.map((x) => esc(x.nazwa))],
      uslugi.map((u) => [esc(nazwaUslugi(kat, u)), ...p.map((x) => { const s = x.wyniki.sprzedaz[u];
        return s ? `${licz(s.popyt)} / ${licz(s.sprzedaz)}${s.utracona ? ` <span class="minus">(−${licz(s.utracona)}: ${esc(s.przyczyna)})</span>` : ""}` : "–"; })]), { klasy: ["l"] });
    return html + `<div class="wykres"><canvas id="w-warianty"></canvas></div>`;
  },
  po({ v }) {
    const p = podglad && podglad.runda === v.runda ? podglad.warianty : null;
    if (!p) return;
    wykres("w-warianty", "bar", p.map((x) => x.nazwa), [{ label: "Dochód netto", data: p.map((x) => x.wyniki.kpir.dochod_netto) },
      { label: "Przychody", data: p.map((x) => x.wyniki.kpir.przychody) }]);
  },
  akcje: {
    "zapisz-wariant": async (el, c) => {
      const nazwa = prompt("Nazwa wariantu (np. „Niższe ceny”):", `Wariant ${(c.v.warianty || []).length + 1}`);
      if (!nazwa) return;
      c.ustaw(await c.api(`/api/gry/${GRA}/warianty/${encodeURIComponent(FIRMA)}`, { method: "PUT", body: JSON.stringify({ nazwa }) }));
      c.idz("analiza", "decyzje");
    },
    "usun-wariant": async (el, c) => {
      c.ustaw(await c.api(`/api/gry/${GRA}/warianty/${encodeURIComponent(FIRMA)}?nazwa=${encodeURIComponent(el.dataset.n)}`, { method: "DELETE" }));
      c.idz("analiza", "decyzje");
    },
    "wczytaj-wariant": async (el, c) => {
      if (!confirm(`Zastąpić bieżące decyzje wariantem „${el.dataset.n}”?`)) return;
      const d = await c.api(`/api/gry/${GRA}/warianty-dane/${encodeURIComponent(FIRMA)}?nazwa=${encodeURIComponent(el.dataset.n)}`);
      await c.zmien((dd) => { Object.keys(dd).forEach((k) => delete dd[k]); Object.assign(dd, d); });
      toast("Wczytano wariant do decyzji."); c.idz("analiza", "decyzje");
    },
    porownaj: async (el, c) => {
      el.disabled = true; el.textContent = "Liczę…";
      podglad = await c.api(`/api/gry/${GRA}/podglad/${encodeURIComponent(FIRMA)}`, { method: "POST",
        body: JSON.stringify({ warianty: ["biezace", ...(c.v.warianty || [])] }) });
      c.idz("analiza", "decyzje");
    },
  },
};

export { WSKAZNIKI, gw };
