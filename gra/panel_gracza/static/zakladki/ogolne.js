// Pulpit, karta wyników, lista błędów, wysyłanie decyzji.
import { esc, godzina, inicjaly, inwestorHtml, RANKING_DLACZEGO, termin as terminSlownie, naOkres, naRunde, OKRES, gw, KOLORY_FIRM, licz, marka, nazwaFirmy, nazwaUslugi, proc, tabela, toast, wsk, wykres, zl, zl2 } from "./wspolne.js";
import { ikona } from "./ikony.js";

const WSKAZNIKI = [["wynik_dzialalnosci", "Wynik działalności"], ["wynik_ekonomiczny", "Wynik ekonomiczny"],
  ["zadowolenie_pracownikow", "Zadowolenie pracowników"], ["zadowolenie_klientow", "Zadowolenie klientów"],
  ["rozwoj_firmy", "Rozwój firmy"], ["wskaznik_zadluzenia", "Wskaźnik zadłużenia"]];

let skumulowana = false;

// U10: co podnosi wskaźnik (INSTRUKCJA rozdz. 3) i ocena według progów z dane/zalozenia.yaml: karta_wynikow.skala
const PODNOSI = {
  wynik_dzialalnosci: "Iloczyn pozostałych – najpierw popraw najsłabszy składnik.",
  wynik_ekonomiczny: "Sprzedawać więcej i z sensowną marżą, pilnować kosztów.",
  zadowolenie_pracownikow: "Uczciwe pensje, dobry sprzęt, udogodnienia, szkolenia, bez przepracowania.",
  zadowolenie_klientow: "Rozsądne ceny, dobra jakość, szersze menu, bez braków dań i kolejek.",
  rozwoj_firmy: "Nowy sprzęt i wyposażenie, kupione lokale, kolejne lokale.",
  wskaznik_zadluzenia: "Nie żyć na kredycie (zwłaszcza u Harpagona) dłużej, niż trzeba.",
};
function ocena(skala, k, x) {
  const p = skala?.[k];
  if (!p || x == null) return null;
  return x >= p[1] ? ["dobry", "dobry"] : x >= p[0] ? ["sredni", "średni"] : ["niski", "niski"];
}
function skalaKarty(v, karta) {
  if (!karta || !v.skala_karty) return "";
  return `<div class="skala-karty">${WSKAZNIKI.map(([k, n]) => {
    const o = ocena(v.skala_karty, k, karta[k]);
    return `<div class="wsk ${o?.[0] || ""}" title="${esc(PODNOSI[k])}"><span class="maly-tekst">${n}</span><b>${wsk(karta[k])}</b>
      ${o ? `<span class="ocena ${o[0]}">${o[1]}</span>` : ""}<div class="maly-tekst">${PODNOSI[k]}</div></div>`;
  }).join("")}</div>`;
}

// U16: „Dlaczego mój wynik się zmienił?” – zdania z silnik/wyniki/wnioski.py: dlaczego (karta ostatniej i poprzedniej rundy)
function dlaczegoHtml(v) {
  if (!v.dlaczego?.length) return "";
  return `<div class="komunikat"><b>Dlaczego wynik się zmienił? (runda ${v.runda - 1})</b> ${v.dlaczego.map(esc).join(" ")}
    <a href="#" data-zakladka-k="karta_wynikow">Karta wyników</a></div>`;
}

// składniki kebabowe karty (gra z lokalami, silnik/wyniki/karta.py → kebab): wskaźnik, miernik, jak pokazać miarę
const SKLADNIKI_KEBABU = [
  ["zadowolenie_klientow", "kolejki", "Klienci, którzy nie doczekali się obsługi", (m) => proc(m.kolejki)],
  ["zadowolenie_klientow", "brakujace_dania", "Dania wyłączone z braku składnika (dania × dni)", (m) => proc(m.brakujace_dania)],
  ["zadowolenie_klientow", "kontrola_z_mandatem", "Mandat sanepidu", (m) => zl(m.mandat)],
  ["zadowolenie_klientow", "wypadki", "Wypadki w lokalu", (m) => licz(m.wypadki)],
  ["zadowolenie_pracownikow", "przepracowanie", "Przepracowanie (wykorzystanie czasu ponad próg)", (m) => proc(m.przepracowanie)],
  ["rozwoj_firmy", "kolejne_lokale", "Lokale", (m) => licz(m.lokale)],
  ["wskaznik_zadluzenia", "dlug_harpagona", "Dług u Harpagona", (m) => zl(m.dlug_harpagona)],
];

function kartaKebabu(v) {
  const K = v.wyniki?.karta_kebab;
  if (!K || skumulowana) return "";
  const nazwa = Object.fromEntries(WSKAZNIKI);
  const plus = (x) => x ? `<span class="${x > 0 ? "plus" : "minus"}">${x > 0 ? "+" : "−"}${wsk(Math.abs(x))}</span>` : "–";
  const wiersze = [["Zadowolenie klientów", "Cena względem ceny preferowanej w strefie lokalu", proc(K.miary.cena_wzgledem_strefy, 0), "we wzorze"]]
    .concat(SKLADNIKI_KEBABU.map(([s, k, opis, miara]) => [nazwa[s], opis, miara(K.miary), plus(K.skladniki[s]?.[k])]));
  return tabela("Skąd Twoja karta – sprawy kebabowe", ["Wskaźnik", "Miernik", "W minionym tygodniu", "Poprawka"], wiersze,
    { klasy: ["l", "l"], sortuj: false })
    + `<p class="podpowiedz">Kolejki, braki w menu, mandaty i wypadki obniżają zadowolenie klientów. Kolejki, braki,
      reklamacje, cena i jakość trafiają też do opinii o lokalu (gwiazdki na mapie) – a od nich zależy, ilu klientów
      przyjdzie w następnych tygodniach. Przepracowana załoga jest mniej zadowolona, każdy kolejny lokal podnosi
      rozwój firmy, a dług u Harpagona waży w zadłużeniu więcej niż kredyt bankowy.</p>`;
}

const MAKS_LOGO_KB = 300;   // konta/druzyny.py: MAKS_LOGO_KB

// marka firmy z roboczymi decyzjami (nazwa, slogan i kolor wchodzą po przeliczeniu rundy 1)
function mojaMarka(v, d) {
  const m = marka(v, v.firma);
  return { ...m, nazwa: d.nazwa || m.nazwa, slogan: d.misja ?? m.slogan, kolor: d.kolor || m.kolor };
}

const znakFirmy = (m) => m.logo
  ? `<img class="logo-firmy" src="${esc(m.logo)}" alt="Logo firmy ${esc(m.nazwa)}">`
  : `<div class="awatar" style="border-color:${esc(m.kolor)};color:${esc(m.kolor)}">${esc(m.nazwa.slice(0, 2).toUpperCase())}</div>`;

// runda 1: nazwa, slogan, kolor na mapie i logo firmy (logo – osobny zapis, api/widoki.py: api_logo)
function formularzMarki(v, d) {
  const m = mojaMarka(v, d);
  const zajete = Object.fromEntries(v.gra.firmy.filter((f) => f.nazwa !== v.firma).map((f) => [marka(v, f.nazwa).kolor, marka(v, f.nazwa).nazwa]));
  const kolory = KOLORY_FIRM.map((k) => `<button class="kolor-firmy ${k === m.kolor ? "wybrany" : ""}" style="background:${k}" data-akcja="marka-kolor"
    data-kolor="${k}" title="${zajete[k] ? `ten kolor ma ${esc(zajete[k])}` : "wybierz ten kolor"}" ${zajete[k] ? "disabled" : ""}></button>`).join("");
  return `<div class="sekcja-tytul">Runda 1: Twoja marka</div><div class="marka">
    <div class="marka-znak">${znakFirmy(m)}</div>
    <div class="marka-pola">
      <label class="pole">Nazwa firmy<input type="text" maxlength="40" value="${esc(d.nazwa || m.nazwa)}" data-zmiana="marka-nazwa"></label>
      <label class="pole">Slogan<input type="text" maxlength="80" value="${esc(m.slogan)}" placeholder="np. Kebab, do którego się wraca" data-zmiana="marka-slogan"></label>
      <div class="pole">Kolor firmy na mapie<div class="kolory-firmy">${kolory}</div></div>
      <label class="pole">Logo (PNG albo JPG, najwyżej ${MAKS_LOGO_KB} KB)<input type="file" accept="image/png,image/jpeg" data-zmiana="marka-logo"></label>
      ${m.logo ? `<button class="btn jasny maly" data-akcja="marka-bez-logo">Usuń logo</button>` : ""}
      <p class="podpowiedz">Nazwę, slogan, kolor i logo wybieracie w pierwszej rundzie – od drugiej rundy zobaczą je inne firmy,
        a Wasze lokale na mapie będą miały ten kolor.</p>
    </div></div>`;
}

const wyslijLogo = async (c, logo) => {
  c.ustaw(await c.api(`/api/gry/${GRA}/logo/${encodeURIComponent(FIRMA)}`, { method: "PUT", body: JSON.stringify({ logo }) }));
  toast(logo ? "Logo zapisane." : "Logo usunięte.");
};

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

// U19: tryb podpowiedzi (włącza mistrz gry) – 3 rzeczy do sprawdzenia w pierwszych rundach
function podpowiedziHtml(v) {
  if (!v.podpowiedzi?.length) return "";
  const html = v.podpowiedzi.map((p, i) => `<a data-zakladka-k="${esc(p.zakladka)}"><span class="st inf">${i + 1}</span>
    <span>${esc(p.tytul)}<small>${esc(p.tekst)}</small></span></a>`).join("");
  return `<div class="sekcja-tytul">${v.podpowiedzi.length} rzeczy do sprawdzenia w tej rundzie</div><div class="plan podpowiedzi">${html}</div>`;
}

// U9: rozruch nowego lokalu (dane/mapa/popyt.yaml: model.rozruch) – strata w pierwszych tygodniach sprzedaży jest normalna
function rozruchHtml(v) {
  const R = v.dashboard?.rozruch;
  if (!R || !(R.lokale.length || v.runda === v.gra.runda_startowa)) return "";
  const pr = (m) => `ok. ${Math.round(m * 100)}%`;
  const lokale = R.lokale.map((l) => `<li><b>${esc(l.nazwa)}</b>: ${l.poprzednia != null
    ? `w poprzednim tygodniu przyszło ${pr(l.poprzednia)} klientów, w tym ${l.teraz < 1 ? pr(l.teraz) : "już pełny popyt"}`
    : `pierwszy tydzień sprzedaży – przyjdzie ${pr(l.teraz)} klientów`}.</li>`).join("");
  return `<div class="komunikat"><b>Rozruch nowego lokalu.</b> Nowy lokal dopiero zdobywa klientów: w pierwszym tygodniu
    sprzedaży przychodzi ${pr(R.start)} klientów, potem co tydzień o ${Math.round(R.przyrost * 100)} punktów procentowych więcej,
    aż do pełnego popytu. Czynsz i pensje są od razu pełne, więc strata na starcie jest normalna – pilnuj, żeby była mała:
    zamówienia i grafik dopasuj do mniejszego ruchu.${lokale ? `<ul>${lokale}</ul>` : ""}</div>`;
}

export const dashboard = {
  tytul: "Dashboard", ikona: "▦",
  decyzje({ v, kat, d: szkic }) {
    const d = v.dashboard, p = kat.parametry, m = mojaMarka(v, szkic);
    const rundaMarki = v.edycja && v.runda === v.gra.runda_startowa && !v.tylko_odczyt;
    const kafel = (t, ik, tresc) => `<div class="kafel"><div class="kg"><span>${t}</span>${ikona(ik, 18)}</div><div class="kt">${tresc}</div></div>`;
    const ludzie = v.gra.firmy.filter((f) => !f.bot).map((f) => f.nazwa);
    const status = ludzie.length > 1 ? `<div class="komunikat">Gracze w tej grze: ${ludzie.map((n) =>
      `${esc(n)} ${v.gra.wyslane.includes(n) ? '<span class="pigulka ok">wysłał</span>' : '<span class="pigulka nie">decyduje</span>'}`).join(" · ")}
      · <a href="/gra/${GRA}">zmień firmę</a></div>` : "";
    const boty = v.gra.firmy.filter((f) => f.bot).map((f) => esc(f.nazwa));
    const stali = (v.gra.konkurenci_stali || []).map((k) => esc(k.nazwa));
    const rynek = [boty.length ? `boty: ${boty.join(", ")}` : "", stali.length ? `stałe ceny: ${stali.join(", ")}` : ""].filter(Boolean).join(" · ");
    const klub = v.kasyno?.otwarte ? `<div class="komunikat">${esc(v.kasyno.zaproszenie)}
      · <a data-zakladka-k="kasyno">${esc(v.kasyno.adres)}</a></div>` : "";
    const alarm = (v.lista_bledow || []).find((b) => b.alarm);   // U2: debet ponad limit – blokada w tej rundzie
    const pasek = alarm ? `<div class="komunikat zly">${esc(alarm.tekst)}
      <button class="btn jasny maly" data-akcja="popraw" data-z="bank">Przejdź do banku</button></div>` : "";
    const inwestor = v.inwestor && v.runda <= v.inwestor.do_rundy + 1 ? inwestorHtml(v) : "";   // U11: potem tylko w Banku
    return `${pasek}${inwestor}${status}${klub}${rundaMarki ? formularzMarki(v, szkic) : ""}${v.edycja ? planRundy(v, kat) : ""}${podpowiedziHtml(v)}${rozruchHtml(v)}${dlaczegoHtml(v)}<div class="sekcja-tytul">Twoja firma</div><div class="dash">
      ${kafel("Nazwa i logo firmy", "osoba", `<div class="srodek">${znakFirmy(m)}<b>${esc(m.nazwa)}</b>${m.slogan ? `<div class="maly-tekst">„${esc(m.slogan)}”</div>` : ""}</div>`)}
      ${kafel("Miejsce", "karta", d.miejsce ? `${d.miejsce} / ${d.liczba_firm}` : `<span class="maly-tekst">Ranking dostępny od rundy 3</span>`)}
      ${kafel(`Liczba rund w grze`, "zegar", `<div>${Math.min(v.gra.runda, v.gra.liczba_rund)} / ${v.gra.liczba_rund}
        <div class="maly-tekst">${v.gra.zakonczona ? "Gra zakończona" : `Bieżąca runda: ${v.gra.runda}`} · ${v.gra.firmy.length + stali.length} firm na rynku</div>
        ${rynek ? `<div class="podpowiedz">${rynek}</div>` : ""}</div>`)}
      ${kafel("Dochód netto", "wykres", d.dochod_netto == null && v.ksiegowosc?.ukryte   // U7: ukryty do złożenia deklaracji
        ? `<div class="maly-tekst">Księgujesz sam – dochód tej rundy poznasz po złożeniu deklaracji albo wybierz biuro.</div>
           <button class="btn jasny maly" data-akcja="popraw" data-z="biuro">Księgowość ▸ Biuro rachunkowe</button>`
        : `<span class="${d.dochod_netto < 0 ? "minus" : ""}">${zl(d.dochod_netto)}</span>`)}
      ${kafel("Saldo konta", "portfel", zl(d.saldo))}
      ${kafel("Minimalne wynagrodzenie brutto", "zatrudnienie", `${licz(kat.placa_minimalna)} PLN / miesiąc`
        + (OKRES.rund_w_roku === 12 ? "" : `<div class="maly-tekst">≈ ${licz(naRunde(kat.placa_minimalna))} PLN${naOkres()}</div>`))}
      ${kafel("Czas pracy pracownika i sprzętów", "zegar", `<div>${p.godziny}H / ${OKRES.mianownik.toUpperCase()}<div class="maly-tekst">Otwarte: 9:00–17:00</div></div>`)}
      ${kafel("Stawki amortyzacji", "procent", v.amortyzacja
        ? `<div class="maly-tekst">Lokal i budynek: ${proc(v.amortyzacja.stawki.budynek)} rocznie<br>Od ${licz(p.amortyzacja_prog)} PLN: ${proc(v.amortyzacja.stawki.sprzet)} rocznie<br>Do ${licz(p.amortyzacja_prog)} PLN: 100%</div>`
        : `<div class="maly-tekst">Sprzęt powyżej ${licz(p.amortyzacja_prog)} PLN: 10%<br>Sprzęt do ${licz(p.amortyzacja_prog)} PLN: 100%</div>`)}
      ${kafel("Pozostałe informacje", "finanse", `<div class="maly-tekst">PIT liniowy ${proc(v.podatki?.parametry?.pit ?? 0, 0)}<br>Składki ZUS pracodawcy ${proc(p.zus, 0)}
        <br>Kredyt odnawialny: ${v.gra.kredyt_odnawialny === "na_biezaco" ? "na bieżąco" : "jak w grze (jednocześnie)"}
        ${d.lokaty ? `<br>Lokaty: ${zl(d.lokaty)}` : ""}${d.zadluzenie ? `<br>Zadłużenie: ${zl(d.zadluzenie)}` : ""}</div>`)}
    </div>${(v.historia || []).length > 1 ? `<div class="wykres"><canvas id="w-dash"></canvas></div>` : ""}`;
  },
  zmiany: {
    "marka-nazwa": (el, c) => c.zmien((d) => { d.nazwa = el.value.trim().slice(0, 40); }),
    "marka-slogan": (el, c) => c.zmien((d) => { d.misja = el.value.trim().slice(0, 80); }),
    "marka-logo": async (el, c) => {
      const plik = el.files?.[0];
      if (!plik) return;
      if (!["image/png", "image/jpeg"].includes(plik.type)) return toast("Logo musi być obrazkiem PNG albo JPG.");
      if (plik.size > MAKS_LOGO_KB * 1024) return toast(`Logo jest za duże (${Math.ceil(plik.size / 1024)} KB) – najwyżej ${MAKS_LOGO_KB} KB.`);
      const dane = await new Promise((ok, zle) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = zle; r.readAsDataURL(plik); });
      await wyslijLogo(c, dane);
    },
  },
  akcje: {
    "marka-kolor": (el, c) => c.zmien((d) => { d.kolor = el.dataset.kolor; }),
    "marka-bez-logo": (el, c) => wyslijLogo(c, ""),
    popraw: (el, c) => c.idz(el.dataset.z, "decyzje"),
  },
  po({ v }) {
    const h = v.historia || [];
    if (h.length > 1) wykres("w-dash", "bar", h.map((x) => x.skrot || x.miesiac), [{ label: "Dochód netto", data: h.map((x) => x.dochod_netto) },
      { label: "Saldo konta", data: h.map((x) => x.gotowka), type: "line", kolor: "--wykres-linia" }]);
  },
};

// Wnioski z poprzedniej rundy (silnik/wyniki/wnioski.py): co się udało i co poprawić – z zakładką, w której to zrobić
export const wnioski = {
  tytul: "Wnioski z rundy", ikona: "ok",
  info: "Co wyszło w poprzedniej rundzie i co zrobić, żeby kolejna poszła lepiej.",
  decyzje({ v, tytulZakladki }) {
    const W = v.wnioski;
    if (!W) return `<div class="komunikat">Wnioski pojawią się po przeliczeniu pierwszej rundy – wtedy zobaczycie, co się udało
      i co warto poprawić.</div>`;
    const dobre = W.dobre.map((t) => `<li>${esc(t)}</li>`).join("");
    const rady = W.do_poprawy.map((r) => `<div class="kafel"><div class="kg">${esc(r.tytul)}</div><div class="kt">
      <p>${esc(r.co)}</p><p><b>Co zrobić:</b> ${esc(r.rada)}</p></div>
      <div class="kd"><a class="btn jasny maly" data-zakladka-k="${esc(r.zakladka)}">Przejdź: ${esc(tytulZakladki(r.zakladka))}</a></div></div>`).join("");
    return `${dlaczegoHtml(v)}<div class="sekcja-tytul">Runda ${v.runda - 1}: co się udało</div><ul class="wnioski-dobre">${dobre}</ul>
      <div class="sekcja-tytul">Co poprawić w rundzie ${v.runda}</div>
      ${rady ? `<div class="siatka">${rady}</div><p class="podpowiedz">Nie wszystko naraz – zacznijcie od pierwszej rady.
        Każda poprawka od razu działa w tej rundzie.</p>` : `<div class="komunikat">Nic nie wymaga poprawy – tak trzymać!</div>`}`;
  },
};

export const karta_wynikow = {
  tytul: "Karta wyników", ikona: "☷", wynikiOd: 3, odblokowanie: "karta_wynikow",
  info: () => "Karta wyników pokazuje rezultaty decyzji podjętych w poprzedniej rundzie.",
  wyniki({ v }) {
    const karty = skumulowana ? v.karta_skumulowana : v.rynek.karta;
    const firmy = Object.keys(karty || {}).sort((a, b) => karty[b].wynik_dzialalnosci - karty[a].wynik_dzialalnosci);
    const wiersze = firmy.map((f) => [`${f === v.firma ? "<b>" : ""}${esc(nazwaFirmy(v, f))}${f === v.firma ? "</b>" : ""}`,
      ...WSKAZNIKI.map(([k]) => `<span class="ocena-tekst ${ocena(v.skala_karty, k, karty[f][k])?.[0] || ""}">${wsk(karty[f][k])}</span>`),
      zl(v.majatek_firm?.[f])]);
    return `<div style="display:flex;gap:10px;justify-content:center">
        <button class="btn ${skumulowana ? "jasny" : "pom"}" data-akcja="karta-skum" data-s="0">Karta wyników</button>
        <button class="btn ${skumulowana ? "pom" : "jasny"}" data-akcja="karta-skum" data-s="1" ${v.odblokowane.includes("karta_skumulowana") ? "" : "disabled"}>Skumulowana karta wyników</button></div>
      ${karty?.[v.firma] ? `<div class="sekcja-tytul">${skumulowana ? "Twoja skumulowana karta" : "Twoja karta"} – niski, średni czy dobry?</div>
        ${skalaKarty(v, karty[v.firma])}` : ""}
      ${tabela("Ranking zespołów", ["Firma", ...WSKAZNIKI.map(([, n]) => n), "Majątek netto"], wiersze, { klasy: ["l"] })}
      <p class="podpowiedz">${RANKING_DLACZEGO} Majątek netto – stan na koniec ostatniej przeliczonej rundy.</p>
      ${kartaKebabu(v)}
      <div class="wykres"><canvas id="w-karta"></canvas></div>
      <div class="wykres"><canvas id="w-historia"></canvas></div>
      <p class="podpowiedz">Ocena „niski / średni / dobry” porównuje wskaźnik z typowymi wynikami firm w grze
      (dolna i górna ćwiartka). Wynik działalności = iloczyn pozostałych wskaźników; przy stracie ujemny, proporcjonalny do straty. Wynik ekonomiczny = (dochód netto rundy − odsetki Harpagona) / ${zl(v.dzielnik_karty)}.
      Zadowolenie i rozwój liczone są ze skalibrowanych wzorów (dane/zalozenia.yaml) – mogą odbiegać od prawdziwej gry.</p>`;
  },
  po({ v }) {
    const karty = skumulowana ? v.karta_skumulowana : v.rynek.karta;
    const firmy = Object.keys(karty || {});
    wykres("w-karta", "bar", WSKAZNIKI.map(([, n]) => n), firmy.map((f) => ({ label: nazwaFirmy(v, f), data: WSKAZNIKI.map(([k]) => karty[f][k]) })));
    const h = (v.historia || []).filter((x) => x.karta);
    wykres("w-historia", "line", h.map((x) => x.skrot || x.miesiac), [{ label: "Twój wynik działalności", data: h.map((x) => x.karta.wynik_dzialalnosci) },
      { label: "Wynik ekonomiczny", data: h.map((x) => x.karta.wynik_ekonomiczny) }]);
  },
  akcje: { "karta-skum": (el, c) => { skumulowana = el.dataset.s === "1"; c.idz("karta_wynikow", "wyniki"); } },
};

const DOKAD = { lokale: "lokale", stanowiska: "stanowiska", oferta: "oferta", finanse_bank: "bank", finanse_biuro: "biuro", hr_zatrudnienie: "zatrudnienie",
  inwestycje_sprzet: "sprzet", dostawcy: "dostawcy", sprzedaz: "sprzedaz", wlasciciel: "wlasciciel", kasyno: "kasyno", handel: "handel" };

export const lista_bledow = {
  tytul: "Lista błędów", ikona: "☰",
  info: "Sprawdź, czy podjęto wszystkie najważniejsze decyzje. Do zrobienia – poważne braki, Uwaga – ostrzeżenia, Dla informacji – podpowiedzi (zwinięte).",
  decyzje(c) {
    const v = c.v;
    // klucze Revasa (finanse_bank…) → zakładka; w grze z lokalami silnik podaje od razu klucz zakładki (swiezosc, zatrudnienie…)
    const dokad = (z) => DOKAD[z] || (c.dostepna(z) ? z : null);
    if (!v.lista_bledow.length) return `<div class="komunikat ok">Brak uwag – wszystkie najważniejsze decyzje są podjęte.</div>`;
    const wiersz = (b) => `<div class="blad ${b.poziom}"><span class="tx">${esc(b.tekst)}</span>
       ${dokad(b.zakladka) ? `<button class="btn jasny maly" data-akcja="popraw" data-z="${dokad(b.zakladka)}">Popraw</button>` : ""}</div>`;
    // U5: trzy grupy – „Dla informacji” domyślnie zwinięte
    const grupy = [["czerwony", "Do zrobienia"], ["pomaranczowy", "Uwaga"], ["niebieski", "Dla informacji"]].map(([poziom, nazwa]) => {
      const g = v.lista_bledow.filter((b) => b.poziom === poziom);
      if (!g.length) return "";
      return poziom === "niebieski"
        ? `<details class="grupa-bledow"><summary>${nazwa} (${g.length})</summary>${g.map(wiersz).join("")}</details>`
        : `<div class="grupa-bledow ${poziom}">${nazwa} (${g.length})</div>${g.map(wiersz).join("")}`;
    });
    const brak = v.lista_bledow.some((b) => b.poziom === "czerwony") ? ""
      : `<div class="komunikat ok">Nic do poprawienia – poniżej tylko uwagi i podpowiedzi.</div>`;
    return brak + grupy.join("");
  },
  akcje: { popraw: (el, c) => c.idz(el.dataset.z, "decyzje") },
};

const kto = (a, przed) => a ? `${przed} ${esc(a.nazwa)} (${godzina(a.kiedy)})` : "";
function skladDruzyny(v) {
  const sklad = v.druzyna?.sklad || [];
  if (!sklad.length) return "";
  return `<div class="tabela-tytul">Twoja drużyna – ${esc(v.firma)}</div>
    <p class="sklad">${sklad.map((o) => `<span class="osoba-druzyny"><span class="inicjaly">${inicjaly(o.nazwa)}</span>${esc(o.nazwa)}</span>`).join("")}</p>`;
}

// U17: refleksja drużyny przy wysyłaniu decyzji – widzi ją mistrz gry (panel i eksport CSV).
// Szkic trzymany w pamięci strony, żeby odświeżenie zakładki (zapis kolegi z drużyny) go nie skasowało.
let szkicRefleksji = null;
document.addEventListener("input", (e) => { if (e.target.id === "refleksja") szkicRefleksji = e.target.value; });
function refleksjaHtml(v) {
  const tryb = v.gra.refleksja || "opcjonalna";
  if (tryb === "wylaczona") return "";
  if (v.wyslane || v.tylko_odczyt || v.prowadzenie?.pauza) {
    return v.refleksja ? `<p class="podpowiedz">Wasza refleksja do tej rundy: „${esc(v.refleksja)}”</p>` : "";
  }
  return `<label class="pole" style="margin:14px 0">Co zmieniamy w tej rundzie i dlaczego? (1–2 zdania${tryb === "wymagana" ? ", wymagane" : ", nieobowiązkowe"})
      <textarea id="refleksja" rows="3" maxlength="500" placeholder="Np. Obniżamy ceny, bo w zeszłym tygodniu sprzedaliśmy tylko połowę porcji.">${esc(szkicRefleksji ?? v.refleksja ?? "")}</textarea></label>
    <p class="podpowiedz">Przeczyta to mistrz gry – przyda się przy omawianiu rundy. Na wynik gry nie wpływa.</p>`;
}

export const wyslij = {
  tytul: "Wyślij decyzje", ikona: "✉", odblokowanie: (v) => !v.gra.zakonczona,
  decyzje({ v }) {
    const czerwone = v.lista_bledow.filter((b) => b.poziom === "czerwony").length;
    const ludzie = v.gra.firmy.filter((f) => !f.bot);
    const stan = ludzie.map((f) => `<tr><td class="l">${esc(f.nazwa)}</td><td>${v.gra.wyslane.includes(f.nazwa) ? '<span class="pigulka ok">wysłane</span>' : '<span class="pigulka nie">w trakcie</span>'}</td></tr>`).join("");
    if (!v.edycja) return `<div class="komunikat">To podgląd poprzedniej rundy.</div>`;
    const P = v.prowadzenie || {};
    const termin = P.termin && !P.pauza ? `<p>Runda zamknie się sama: <b>${esc(terminSlownie(P.termin))}</b> – decyzje niewysłane do tej pory
      zagrają w takiej postaci, w jakiej są zapisane.</p>` : "";
    if (v.tylko_odczyt || P.pauza) {
      return `<div class="komunikat">${v.tylko_odczyt ? "Podgląd mistrza gry – decyzje tej drużyny wysyłają uczniowie."
        : "Gra jest wstrzymana przez mistrza gry – decyzji nie można teraz zmieniać ani wysyłać."}</div>
        ${v.wyslane ? `<div class="komunikat ok">Decyzje wysłane${kto(v.druzyna?.autorzy?.wyslal, " przez")}.</div>` : ""}
        ${refleksjaHtml(v)}${termin}${skladDruzyny(v)}
        ${ludzie.length > 1 ? `<div class="tabela-tytul">Drużyny</div><div class="tab-wrap"><table class="t">${stan}</table></div>` : ""}`;
    }
    return `${termin}${czerwone ? `<div class="komunikat zly">Na liście błędów jest ${czerwone} poważnych uwag. Możesz mimo to wysłać decyzje.</div>` : ""}
      ${v.wyslane
        ? `<div class="komunikat ok">Decyzje wysłane${kto(v.druzyna?.autorzy?.wyslal, " przez")}. Runda przeliczy się, gdy wszystkie drużyny wyślą decyzje.</div>
           ${refleksjaHtml(v)}
           <button class="btn czarny" data-akcja="cofnij-wyslanie">Wróć do podejmowania decyzji w bieżącej rundzie</button>`
        : `<p>Po wysłaniu decyzji gra czeka, aż wszystkie drużyny wyślą swoje. Wtedy runda przelicza się automatycznie
           (boty decydują same).${(v.druzyna?.sklad || []).length > 1 ? " Decyzje wysyła jedna osoba za całą drużynę." : ""}</p>
           ${v.druzyna?.autorzy?.zapisal ? `<p class="podpowiedz">Ostatni zapis decyzji${kto(v.druzyna.autorzy.zapisal, ":")}.</p>` : ""}
           ${refleksjaHtml(v)}
           <button class="btn zielony" data-akcja="wyslij">Wyślij decyzje</button>`}
      ${skladDruzyny(v)}
      ${ludzie.length > 1 ? `<div class="tabela-tytul">Drużyny</div><div class="tab-wrap"><table class="t">${stan}</table></div>` : ""}
      ${window.MG ? `${ludzie.length > 1 ? `<p><button class="btn jasny" data-akcja="wymus">Przelicz rundę bez czekania (brakujące drużyny: zapisane decyzje)</button></p>` : ""}
      <hr style="margin:28px 0;border:0;border-top:1px solid var(--linia)">
      <p class="podpowiedz">Mistrz gry: możesz cofnąć ostatnią przeliczoną rundę i zmienić decyzje (decyzje botów zostaną policzone od nowa).</p>
      <button class="btn jasny" data-akcja="cofnij-runde" ${v.gra.runda > (v.gra.runda_startowa || 1) ? "" : "disabled"}>Cofnij ostatnią rundę</button>`
      : `<p class="podpowiedz">Rundę może też zamknąć mistrz gry – drużyny bez wysłanych decyzji zagrają wtedy decyzjami zapisanymi do tej pory.</p>`}`;
  },
  akcje: {
    wyslij: async (el, c) => {
      const pole = document.getElementById("refleksja");
      if (pole && c.v.gra.refleksja === "wymagana" && !pole.value.trim()) { pole.focus(); return toast("Napiszcie najpierw 1–2 zdania: co zmieniacie w tej rundzie i dlaczego."); }
      const v = await c.api(`/api/gry/${GRA}/wyslij/${encodeURIComponent(FIRMA)}`, { method: "POST",
        body: JSON.stringify({ wyslane: true, ...(pole ? { refleksja: pole.value } : {}) }) });
      szkicRefleksji = null;
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

export { WSKAZNIKI, gw };
