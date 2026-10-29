// Panel mistrza gry: zakładki Decyzje (kto wysłał, zamknięcie i cofnięcie rundy, pauza, harmonogram zamykania rund,
// harmonogram odblokowań gry z lokalami, poziomy botów, alarm debetu i inwestor ratunkowy), Wyniki (ranking, wykresy, eksport CSV) i Drużyny (skład 1–4 uczniów, konta uczniów).
// Dane: GET /api/gry/<id>/mg (api/prezentacja.py: przeglad_mg), GET /api/gry/<id>/druzyny.
import { esc, godzina, info, inicjaly, licz, nazwaRundy, okno, skrotRundy, tabela, termin, toast, ustawKalendarz, wsk, wyczyscWykresy,
  wykres, zamknijOkno, zl }
  from "../zakladki/wspolne.js";

const ID = JSON.parse(document.getElementById("id-gry").textContent);
const URL_GRY = `/api/gry/${encodeURIComponent(ID)}`;
const ODSWIEZANIE_MS = 15000;  // nowe wysłane decyzje drużyn
const S = { p: null, druzyny: null, tryb: "decyzje" };
const karta = document.getElementById("karta");

const csrf = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? "";
async function api(url, metoda = "GET", dane = undefined) {
  const r = await fetch(url, { method: metoda, headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
    body: dane === undefined ? undefined : JSON.stringify(dane) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.blad || "Błąd serwera.");
  return j;
}

async function wczytaj() {
  [S.p, S.druzyny] = await Promise.all([api(`${URL_GRY}/mg`), api(`${URL_GRY}/druzyny`)]);
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
      <div class="przelacznik">${zakladka("decyzje", "Decyzje")}${zakladka("wyniki", "Wyniki", !historia.length)}${zakladka("druzyny", "Drużyny")}</div></div>
    <div class="tresc">${{ decyzje, wyniki, druzyny }[S.tryb]()}</div>`;
  if (S.tryb === "wyniki") wykresy();
}

// --- Decyzje: kto wysłał, zamknięcie rundy -----------------------------------------------------------------------
const strona = (f) => `/gra/${encodeURIComponent(ID)}/${encodeURIComponent(f.nazwa)}`;
const poziomBota = (f) => {
  const poziomy = Object.entries(S.p.prowadzenie.poziomy || {});
  if (!poziomy.length || S.p.gra.zakonczona) return "";
  return ` <select data-zmiana="poziom" data-f="${esc(f.nazwa)}" title="Poziom bota (od następnej rundy)">${poziomy.map(([k, n]) =>
    `<option value="${esc(k)}"${k === (f.poziom || "sredni") ? " selected" : ""}>${esc(n)}</option>`).join("")}</select>`;
};
const prowadzi = (f) => f.bot ? `bot: ${esc(f.strategia || f.bot)}${poziomBota(f)}`
  : f.sklad?.length ? esc(f.sklad.map((o) => o.nazwa).join(", ")) : `<a data-akcja="tryb" data-t="druzyny">dopisz uczniów</a>`;

function statusDecyzji(f, gra) {
  if (gra.zakonczona) return "–";
  if (f.bot) return `<span class="chip">decyduje przy zamknięciu</span>`;
  const a = f.autorzy || {};
  if (f.wyslane) return `<span class="chip ok" title="${a.wyslal ? `Wysłane przez: ${esc(a.wyslal.nazwa)}, ${godzina(a.wyslal.kiedy)}` : ""}">✓ wysłane</span>`;
  return `<span class="chip pom" title="${a.zapisal ? `Ostatni zapis: ${esc(a.zapisal.nazwa)}, ${godzina(a.zapisal.kiedy)}` : "Brak zapisanych decyzji"}">czeka</span>`;
}

// Z3: debet ponad limit – w tej rundzie blokada inwestycji i kredytów; mistrz gry może przysłać inwestora ratunkowego
function alarm(f, gra) {
  if (gra.zakonczona) return "";
  if (f.inwestor_przyslany) return ` <span class="chip ok" title="Wpłata na początku rundy ${gra.runda}">inwestor: ${zl(f.inwestor_przyslany)}</span>
    <a data-akcja="inwestor-odwolaj" data-f="${esc(f.nazwa)}">odwołaj</a>`;
  if (!(f.alarm > 0)) return "";
  const ratunek = f.inwestor ? "" : ` <a data-akcja="inwestor" data-f="${esc(f.nazwa)}">przyślij inwestora</a>`;
  return ` <span class="chip pom" title="W tej rundzie zablokowane inwestycje, kredyty, leasing i lokaty">debet ponad limit ${zl(f.alarm)}</span>${ratunek}`;
}

function przyslijInwestora(nazwa) {
  const { gra, firmy } = S.p;
  const w = gra.inwestor;
  const f = firmy.find((x) => x.nazwa === nazwa);
  okno(`Inwestor dla „${esc(nazwa)}”`, `<p>Inwestor wpłaci pieniądze na początku rundy ${gra.runda}: najpierw spłaci debet, reszta zostanie w kasie.
      Przez ${w.rund} rund weźmie ${Math.round(w.udzial * 100)}% dodatniego dochodu netto. Dopóki wpłata nie wróci, liczy się jak dług
      (wskaźnik zadłużenia w karcie, majątek netto) – ratunek pozwala grać dalej, ale nie poprawia miejsca w rankingu. Jeden inwestor na grę.</p>
    <p><label>Wpłata (najwyżej ${zl(w.max_kwota)}): <input type="number" id="kwota-inwestora" min="1" max="${w.max_kwota}"
      value="${Math.min(w.max_kwota, Math.ceil(f.alarm))}"> zł</label></p>`,
  { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
    <button class="btn pom" data-akcja="inwestor-tak" data-f="${esc(nazwa)}">Przyślij inwestora</button>` });
}

function decyzje() {
  const { gra, firmy, prowadzenie: P } = S.p;
  const druzyny = firmy.filter((f) => !f.bot);
  const wyslaly = druzyny.filter((f) => f.wyslane).length;
  const kiedy = P.termin ? ` Termin z harmonogramu: <b>${esc(termin(P.termin))}</b>.` : "";
  const opis = gra.zakonczona ? "Gra zakończona – wyniki w zakładce „Wyniki”."
    : P.pauza ? "<b>Gra wstrzymana.</b> Drużyny widzą decyzje, ale nie mogą ich zmieniać ani wysyłać, runda się nie zamyka. Wznów grę przyciskiem poniżej."
    : `Decyzje wysłało ${wyslaly} z ${druzyny.length} ${druzyny.length === 1 ? "drużyny" : "drużyn"}. Runda zamyka się sama, gdy wyślą wszystkie.${kiedy}
       Możesz zamknąć ją wcześniej – drużyny bez wysłanych decyzji zagrają wtedy decyzjami zapisanymi do tej pory.`;
  const harm = P.harmonogram.length ? esc(P.harmonogram_opis) : "brak – rundę zamykasz sam(a) albo zamyka się, gdy wyślą wszyscy";
  const wiersze = firmy.map((f) => [`<b>${esc(f.nazwa)}</b>`, prowadzi(f), statusDecyzji(f, gra), zl(f.gotowka) + alarm(f, gra),
    `<a class="btn jasny maly" href="${strona(f)}" target="_blank" rel="noopener">Strona firmy</a>`]);
  const ustawienia = [["Kapitał startowy", zl(gra.kapital)], ["Ziarno losowości", esc(gra.ziarno)],
    ["Kredyt odnawialny", gra.kredyt_odnawialny === "na_biezaco" ? "na bieżąco" : "na niedobór na koniec rundy"],
    ["Ceny dostawców", gra.ceny_dostawcow === "losowe" ? "wszystkie generowane" : "z danych, dalej generowane"],
    ["Przycisk „Zamów brakujące” w Dostawcach", `${gra.auto_zamowienia ? "włączony" : "wyłączony"}${gra.zakonczona ? ""
      : ` <a data-akcja="auto-zamowienia">${gra.auto_zamowienia ? "wyłącz" : "włącz"}</a>`}`]];
  const alarmy = gra.zakonczona ? [] : firmy.filter((f) => f.alarm > 0 && !f.inwestor_przyslany);
  const opisAlarmu = alarmy.length ? info(`<b>Alarm – debet ponad limit konta:</b> ${alarmy.map((f) => esc(f.nazwa)).join(", ")}.
    W tej rundzie nie mogą inwestować ani brać kredytów, leasingu i lokat. Drużynę bez inwestora możesz uratować – link „przyślij inwestora” przy gotówce.`) : "";
  return `${info(opis)}${opisAlarmu}
    ${tabela(gra.zakonczona ? "Firmy" : `Decyzje rundy ${gra.runda}`, ["Firma", "Prowadzi", "Decyzje", "Gotówka", ""], wiersze, { klasy: ["l", "l"] })}
    <div class="przyciski-mg">
      ${gra.zakonczona ? "" : `<button class="btn pom" data-akcja="zamknij" ${P.pauza ? "disabled" : ""}>Zamknij rundę ${gra.runda}</button>
        <button class="btn jasny" data-akcja="pauza">${P.pauza ? "Wznów grę" : "Wstrzymaj grę"}</button>`}
      <button class="btn jasny" data-akcja="cofnij" ${gra.runda > 1 ? "" : "disabled"}>Cofnij rundę ${Math.max(gra.runda - 1, 1)}</button>
      <a class="btn jasny" href="${URL_GRY}/eksport">Pobierz plik gry</a>
      <button class="btn jasny" data-akcja="odswiez">Odśwież</button></div>
    ${tabela("Prowadzenie gry", ["", ""], [["Zamykanie rund o stałej porze", `${harm}
        ${gra.zakonczona ? "" : ` <a data-akcja="harmonogram">zmień</a>`}`], ["Najbliższy termin", P.pauza ? "– (gra wstrzymana)" : P.termin ? esc(termin(P.termin)) : "–"],
      ...(P.odblokowanie.length ? [["Odblokowania (tygodnie)", `${opisOdblokowan(P.odblokowanie)}${gra.zakonczona ? "" : ` <a data-akcja="odblokowanie">zmień</a>`}`]] : [])],
    { klasy: ["l", "l"] })}
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

// harmonogram: tygodniowe terminy zamknięcia rundy (gry/harmonogram.py, komenda `zamykaj_rundy`)
function wierszTerminu(t = { dzien: 0, godzina: "08:00" }) {
  return `<div class="termin-mg"><select>${S.p.prowadzenie.dni.map((d, i) => `<option value="${i}"${i === t.dzien ? " selected" : ""}>${esc(d)}</option>`).join("")}</select>
    <input type="time" value="${esc(t.godzina)}"> <a data-akcja="usun-termin" title="Usuń termin">✕</a></div>`;
}

function edytujHarmonogram() {
  okno("Zamykanie rund o stałej porze", `<p>Runda zamknie się w pierwszym terminie po zamknięciu poprzedniej – tak, jakbyś kliknął(-ęła)
      „Zamknij rundę”. Np. lekcje we wtorki i czwartki: terminy <b>wtorek 8:00</b> i <b>czwartek 8:00</b>. Brak terminów – rundy zamykasz sam(a).</p>
    <p class="podpowiedz">Terminy działają, gdy na serwerze co kilka minut uruchamia się <code>python manage.py zamykaj_rundy</code> (README).</p>
    <div id="terminy">${S.p.prowadzenie.harmonogram.map(wierszTerminu).join("")}</div>
    <p><a data-akcja="dodaj-termin">+ termin</a></p>`,
  { przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button><button class="btn pom" data-akcja="zapisz-harmonogram">Zapisz</button>` });
}

// harmonogram odblokowań (gra z lokalami, silnik/harmonogram.py): tydzień każdego elementu, zmiany tylko przyszłych
const WYLACZONE = () => S.p.gra.liczba_rund + 1;
function opisOdblokowan(el) {
  const zmienione = el.filter((e) => e.tydzien !== e.domyslny);
  const nast = el.filter((e) => !e.odblokowany && e.tydzien < WYLACZONE()).sort((a, b) => a.tydzien - b.tydzien)[0];
  return `${zmienione.length ? `zmienione: ${zmienione.length}` : "jak w danych"}${nast ? ` · następne: ${esc(nast.nazwa)} (tydz. ${nast.tydzien})` : ""}`;
}

function edytujOdblokowanie() {
  const el = S.p.prowadzenie.odblokowanie;
  const grupy = [...new Set(el.map((e) => e.grupa))];
  const od = Math.max(S.p.gra.runda, 2);   // tydzień 1 – przygotowawczy (silnik/harmonogram.py)
  const blokada = (e) => e.staly ? "disabled title=\"Tydzień przygotowawczy – nie do zmiany\"" : e.odblokowany ? "disabled title=\"Już odblokowane\"" : "";
  const wiersz = (e) => `<tr><td class="l">${esc(e.nazwa)}</td><td><input type="number" class="tydz-mg" data-k="${esc(e.klucz)}"
      min="${od}" max="${WYLACZONE()}" value="${e.tydzien}" ${blokada(e)}></td>
      <td class="podpowiedz">${e.staly ? "tydzień przygotowawczy" : e.tydzien === e.domyslny ? "" : `dane: ${e.domyslny}`}</td></tr>`;
  okno("Harmonogram odblokowań", `<p>Tydzień, od którego drużyny mogą korzystać z elementu. Tydzień 1 jest przygotowawczy –
      jego zakładek nie przesuniesz ani nie przeniesiesz nic do niego. Zmienić można tylko to, co jeszcze się nie odblokowało,
      i najwcześniej na tydzień ${od}. Tydzień ${WYLACZONE()} – element wyłączony w tej grze.</p>
    ${grupy.map((g) => `<div class="tabela-tytul">${esc(g)}</div><div class="tab-wrap"><table class="t"><tbody>${el.filter((e) => e.grupa === g).map(wiersz).join("")}</tbody></table></div>`).join("")}`,
  { przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button><button class="btn pom" data-akcja="zapisz-odblokowanie">Zapisz</button>` });
}

// --- Drużyny: skład (1–4 uczniów), nowe konta i hasła ------------------------------------------------------------
function druzyny() {
  const { druzyny: lista, uczniowie, maks } = S.druzyny;
  const zajeci = new Set(lista.flatMap((d) => d.sklad.map((o) => o.login)));
  const wolni = uczniowie.filter((o) => !zajeci.has(o.login));
  const wiersze = lista.map((d) => {
    const osoby = d.sklad.map((o) => `<span class="osoba-mg" title="login: ${esc(o.login)}"><span class="inicjaly">${inicjaly(o.nazwa)}</span>${esc(o.nazwa)}
      <a data-akcja="haslo" data-login="${esc(o.login)}" title="Nadaj nowe hasło">hasło</a><a data-akcja="usun-z" data-f="${esc(d.firma)}" data-login="${esc(o.login)}" title="Usuń z drużyny">✕</a></span>`).join("");
    const dodaj = d.sklad.length >= maks ? `<span class="podpowiedz">pełna (${maks} os.)</span>`
      : wolni.length ? `<select data-f="${esc(d.firma)}"><option value="">– uczeń –</option>${wolni.map((o) =>
        `<option value="${esc(o.login)}">${esc(o.nazwa)}${o.nazwa !== o.login ? ` (${esc(o.login)})` : ""}</option>`).join("")}</select>
        <button class="btn jasny maly" data-akcja="dodaj-do" data-f="${esc(d.firma)}">Dodaj</button>`
      : `<span class="podpowiedz">brak wolnych kont – załóż poniżej</span>`;
    return [`<b>${esc(d.firma)}</b>`, osoby || `<span class="podpowiedz">nikt – drużynę prowadzi na razie mistrz gry</span>`, dodaj];
  });
  const adres = `${location.origin}/konta/login/`;
  return `${info(`Drużyna to 1–${maks} uczniów prowadzących jedną firmę. Uczeń widzi tylko swoją drużynę i gra w jednej drużynie w grze.
      Uczniowie logują się na <b>${esc(adres)}</b>.`)}
    ${tabela("Skład drużyn", ["Drużyna (firma)", "Uczniowie", "Dopisz"], wiersze, { klasy: ["l", "l", "l"] })}
    <div class="tabela-tytul">Nowe konta uczniów</div>
    <p class="podpowiedz">Jedna osoba w wierszu (imię i nazwisko). Login powstanie z imienia i nazwiska, hasło jest losowe –
      zobaczysz je tylko raz, potem możesz nadać nowe („hasło” przy uczniu). Konta Microsoft zakładają się same przy pierwszym logowaniu.</p>
    <textarea id="nowe-osoby" rows="4" placeholder="Ala Nowak&#10;Jan Kowalski"></textarea>
    <p><button class="btn pom" data-akcja="nowe-konta">Załóż konta</button></p>`;
}

function pokazHasla(konta, tytul) {
  const wiersze = konta.map((k) => [esc(k.nazwa), `<b>${esc(k.login)}</b>`, `<code class="haslo">${esc(k.haslo)}</code>`]);
  okno(tytul, `<p>Przekaż uczniom login i hasło (adres: <b>${esc(location.origin)}/konta/login/</b>).
      Po zamknięciu tego okna haseł nie da się odczytać – można tylko nadać nowe.</p>
    ${tabela(null, ["Uczeń", "Login", "Hasło"], wiersze, { klasy: ["l", "l", "l"] })}`,
  { przyciski: `<button class="btn jasny" data-akcja="drukuj">Drukuj</button><button class="btn pom" data-akcja="zamknij-okno">Gotowe</button>` });
}

// --- Wyniki: ranking i wykresy -----------------------------------------------------------------------------------
function wyniki() {
  const { firmy, historia } = S.p;
  const ostatnia = historia[historia.length - 1];
  const kolejnosc = [...firmy].sort((a, b) => (a.miejsce ?? 1e9) - (b.miejsce ?? 1e9) || (b.dochod_suma - a.dochod_suma));
  const wiersze = kolejnosc.map((f) => [f.miejsce ?? "–", `<b>${esc(f.nazwa)}</b>${f.bot ? ` <span class="podpowiedz">(bot)</span>` : ""}`,
    wsk(f.wynik_skumulowany), wsk(f.wynik_ostatni), zl(f.dochod_ostatni), zl(f.dochod_suma), zl(f.majatek_netto), zl(f.gotowka), zl(f.zadluzenie),
    zl(f.lokaty), licz(f.pracownicy), licz(f.stanowiska)]);
  return `${info(`Ranking według wyniku działalności (karta wyników) – średnia z rund od 2, jak w Revasie.
      Ostatnia przeliczona runda: ${esc(nazwaRundy(ostatnia.runda))}.`)}
    <p class="przyciski-mg"><a class="btn jasny" href="${URL_GRY}/ranking.csv">Ranking do arkusza (CSV)</a>
      <a class="btn jasny" href="${URL_GRY}/wyniki.csv">Wyniki firm w rundach (CSV)</a></p>
    ${tabela("Ranking", ["Miejsce", "Firma", "Wynik działalności (średnia)", `Wynik działalności (${esc(skrotRundy(ostatnia.runda))})`,
      `Dochód netto (${esc(skrotRundy(ostatnia.runda))})`, "Dochód netto (suma)", "Majątek netto", "Gotówka", "Zadłużenie", "Lokaty", "Pracownicy", "Stanowiska"],
    wiersze, { klasy: ["", "l"] })}
    <div class="wykresy-mg"><div class="wykres"><div class="tabela-tytul">Dochód netto w rundach</div><canvas id="w-dochod"></canvas></div>
      <div class="wykres"><div class="tabela-tytul">Majątek netto na koniec rundy</div><canvas id="w-majatek"></canvas></div>
      <div class="wykres"><div class="tabela-tytul">Gotówka na koniec rundy</div><canvas id="w-gotowka"></canvas></div></div>
    <p class="podpowiedz">Majątek netto = gotówka, lokaty, kaucje, nadwyżka VAT, zapasy, lokale i sprzęt po amortyzacji
      i portfel właściciela minus kredyty, debet, zaległe raty leasingu i dług u Harpagona.</p>`;
}

function wykresy() {
  const { firmy, historia } = S.p;
  const etykiety = historia.map((h) => h.skrot);
  const serie = (pole) => firmy.map((f) => ({ label: f.nazwa, data: historia.map((h) => h[pole][f.nazwa] ?? null), type: "line" }));
  wykres("w-dochod", "line", etykiety, serie("dochod"));
  wykres("w-majatek", "line", etykiety, serie("majatek"));
  wykres("w-gotowka", "line", etykiety, serie("gotowka"));
}

// --- akcje -------------------------------------------------------------------------------------------------------
async function wykonaj(akcja, el) {
  if (akcja === "tryb") { S.tryb = el.dataset.t; return rysuj(); }
  if (akcja === "drukuj") return window.print();
  if (akcja === "dodaj-do" || akcja === "usun-z") {
    const f = el.dataset.f;
    const login = akcja === "dodaj-do" ? document.querySelector(`select[data-f="${CSS.escape(f)}"]`).value : el.dataset.login;
    if (!login) return toast("Wybierz ucznia z listy.");
    S.druzyny = await api(`${URL_GRY}/druzyny/${encodeURIComponent(f)}`, "POST", { [akcja === "dodaj-do" ? "dodaj" : "usun"]: login });
    return wczytaj();
  }
  if (akcja === "nowe-konta") {
    const osoby = document.getElementById("nowe-osoby").value.split("\n").map((x) => x.trim()).filter(Boolean);
    if (!osoby.length) return toast("Wpisz imię i nazwisko co najmniej jednej osoby.");
    const j = await api("/api/konta", "POST", { osoby });
    pokazHasla(j.konta, j.konta.length === 1 ? "Nowe konto" : `Nowe konta (${j.konta.length})`);
    S.druzyny = await api(`${URL_GRY}/druzyny`);
    return rysuj();
  }
  if (akcja === "haslo") {
    const j = await api(`/api/konta/${encodeURIComponent(el.dataset.login)}/haslo`, "POST");
    return pokazHasla([j], "Nowe hasło");
  }
  if (akcja === "zamknij-okno") return zamknijOkno();
  if (akcja === "pauza") {
    const pauza = !S.p.prowadzenie.pauza;
    await api(`${URL_GRY}/prowadzenie`, "POST", { pauza });
    toast(pauza ? "Gra wstrzymana – drużyny nie zmieniają decyzji." : "Gra wznowiona.");
    return wczytaj();
  }
  if (akcja === "harmonogram") return edytujHarmonogram();
  if (akcja === "dodaj-termin") return document.getElementById("terminy").insertAdjacentHTML("beforeend", wierszTerminu());
  if (akcja === "usun-termin") return el.closest(".termin-mg").remove();
  if (akcja === "zapisz-harmonogram") {
    const harmonogram = [...document.querySelectorAll("#terminy .termin-mg")].map((w) =>
      ({ dzien: +w.querySelector("select").value, godzina: w.querySelector("input").value }));
    await api(`${URL_GRY}/prowadzenie`, "POST", { harmonogram });
    zamknijOkno();
    toast(harmonogram.length ? "Harmonogram zapisany." : "Harmonogram usunięty – rundy zamykasz sam(a).");
    return wczytaj();
  }
  if (akcja === "odblokowanie") return edytujOdblokowanie();
  if (akcja === "zapisz-odblokowanie") {
    const stare = Object.fromEntries(S.p.prowadzenie.odblokowanie.map((e) => [e.klucz, e.tydzien]));
    const odblokowanie = Object.fromEntries([...document.querySelectorAll(".tydz-mg:not([disabled])")]
      .map((i) => [i.dataset.k, +i.value]).filter(([k, t]) => t !== stare[k]));
    if (!Object.keys(odblokowanie).length) { zamknijOkno(); return toast("Bez zmian."); }
    await api(`${URL_GRY}/prowadzenie`, "POST", { odblokowanie });
    zamknijOkno();
    toast("Harmonogram odblokowań zapisany.");
    return wczytaj();
  }
  if (akcja === "auto-zamowienia") {
    const auto = !S.p.gra.auto_zamowienia;
    await api(`${URL_GRY}/prowadzenie`, "POST", { auto_zamowienia: auto });
    toast(auto ? "Drużyny mogą zamawiać brakujące składniki jednym przyciskiem." : "Przycisk „Zamów brakujące” wyłączony.");
    return wczytaj();
  }
  if (akcja === "inwestor") return przyslijInwestora(el.dataset.f);
  if (akcja === "inwestor-tak" || akcja === "inwestor-odwolaj") {
    const kwota = akcja === "inwestor-tak" ? +document.getElementById("kwota-inwestora").value : 0;
    await api(`${URL_GRY}/prowadzenie`, "POST", { inwestor: { firma: el.dataset.f, kwota } });
    zamknijOkno();
    toast(kwota ? `Inwestor wpłaci ${zl(kwota)} na początku rundy ${S.p.gra.runda}.` : "Inwestor odwołany.");
    return wczytaj();
  }
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

document.addEventListener("change", (e) => {
  const el = e.target.closest("[data-zmiana=poziom]");
  if (!el) return;
  api(`${URL_GRY}/prowadzenie`, "POST", { poziom: { firma: el.dataset.f, poziom: el.value } })
    .then(() => { toast(`Poziom bota „${el.dataset.f}” zmieniony – od następnej rundy.`); return wczytaj(); })
    .catch((b) => toast(b.message));
});

// drużyny wysyłają decyzje ze swoich stron – odświeżamy, gdy nie jest otwarte okno
setInterval(() => {
  if (S.tryb === "decyzje" && !document.querySelector(".zaslona") && !document.hidden) wczytaj().catch(() => {});  // Drużyny: bez odświeżania (wpisywanie)
}, ODSWIEZANIE_MS);

wczytaj().catch((b) => { karta.innerHTML = `<div class="tresc">${info(esc(b.message))}</div>`; });
