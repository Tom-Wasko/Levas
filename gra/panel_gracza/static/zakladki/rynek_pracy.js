// Rynek pracy (gra z lokalami, silnik/ludzie/rynek_pracy.py): kanały rekrutacji, podkupienia przez headhuntera, kontroferty
// i okresy wypowiedzenia. UF20: tu też zatrudnia się kandydatów z puli – od razu z lokalem i stanowiskiem (hr.js: kandydaciRynku).
import { brakWynikow, esc, gw, kafelkiLiczb, licz, nazwaFirmy, okno, podsumowanie, ponadLimitPracownikow, proc, tabela, tekstLimituPracownikow, toast, zamknijOkno, zl, zwinTabela } from "./wspolne.js";
import { kandydaciRynku, pigulkaOfert } from "./hr.js";
import { nazwaLokalu } from "./lokal_wybor.js";
import { minimum, nazwaFormy, opcjeForm } from "./formy.js";

const UMOWA = (kat, u) => nazwaFormy(kat, u).toLowerCase();   // UF21: nazwy form z katalogu
const WYNIK_ZLOZONEJ = { przyjeta: "przyjęta", odrzucona: "odrzucona – pensja nie wyższa od obecnej", kontroferta: "przebita kontrofertą",
  inna_firma: "pracownik wybrał inną firmę", "nieważna": "nieważna" };
const WYNIK_OTRZYMANEJ = { odchodzi: "przyjął ofertę – odchodzi", kontroferta: "został – kontroferta", odrzucona: "odrzucił ofertę" };
const rundy = (n) => `${n} ${n === 1 ? "runda" : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? "rundy" : "rund"}`;

function kosztKanalu(k) {
  const czesci = [k.oplata ? zl(k.oplata) : "", k.mnoznik_rekrutacji ? `${licz(k.mnoznik_rekrutacji, 1)} × koszt rekrutacji` : ""].filter(Boolean);
  return (czesci.join(" + ") || zl(0)) + (k.podkupienie_czesc_pensji ? `; podkupienie: ${licz(k.podkupienie_czesc_pensji * 100)}% oferowanej pensji` : "");
}

function kanalyHtml(A) {
  const w = Object.values(A.kanaly).map((k) => [esc(k.nazwa), k.gwiazdki.map((g) => "★".repeat(g)).join(", "), kosztKanalu(k),
    k.czas_wlasciciela ? `${licz(k.czas_wlasciciela, 1)} h` : "–", k.dostepny ? "dostępny" : `<span class="podpowiedz">od rundy ${k.od_rundy}</span>`]);
  const wyp = A.wypowiedzenie.length === 1 ? rundy(A.wypowiedzenie[0].rund) : A.wypowiedzenie.map((x, i) => {
    const nast = A.wypowiedzenie[i + 1];
    return `staż ${nast ? `${x.staz_od}–${nast.staz_od - 1}` : `od ${x.staz_od}`} rund: ${rundy(x.rund)}`;
  }).join(" · ");
  return tabela("Kanały rekrutacji", ["Kanał", "Kandydaci", "Koszt zatrudnienia", "Czas właściciela", "Dostępność"], w, { klasy: ["l", "l", "l"] })
    + `<p class="podpowiedz">Bez wskazania kanału zatrudnienie idzie najtańszym dostępnym. Okres wypowiedzenia (umowa o pracę, pół etatu): ${wyp};
       przy zleceniu, stażu i B2B osoba odchodzi od razu.
       Wypowiedzenie działa w obie strony: zwolniony pracownik też pracuje (i dostaje pensję) do końca okresu.</p>`;
}

export const rynek_pracy = {
  tytul: "Rynek pracy", tytulPelny: "HR - rynek pracy i agencje", ikona: "rynek_pracy",
  odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Pula pracowników jest wspólna dla wszystkich drużyn. Zatrudniasz tutaj: wybierz kandydata, pensję, kanał rekrutacji
    (pracuj.pl, agencja pracy) oraz lokal i stanowisko. Obsadę stanowisk zmienisz w zakładce Mój lokal. Tylko headhunter złoży ofertę
    pracownikowi innej drużyny – jego szef może odpowiedzieć kontrofertą w tej samej rundzie.`,
  decyzje(c) {
    const { v, kat, edycja } = c;
    const A = v.agencja, d = v.decyzje || {};
    if (!A) return `<p class="podpowiedz">Brak danych.</p>`;
    const nowi = (d.zatrudnij || []).length + (d.podkup || []).length;
    let html = `<div class="pasek ciemny"><span>Nowi pracownicy w tej rundzie: <span class="kwota">${nowi} / ${A.limit}</span>
      (zatrudnienia i oferty podkupienia)</span></div>` + kandydaciRynku(c) + kanalyHtml(A);

    const kf = d.kontroferty || {};
    html += tabela("Oferty innych drużyn dla twoich pracowników", ["Pracownik", "Od", "Oferowana pensja", "Obecna pensja", "Twoja kontroferta", ""],
      A.oferty_dla_mnie.length ? A.oferty_dla_mnie.map((o) => [esc(o.imie_nazwisko), esc(nazwaFirmy(v, o.od)), zl(o.pensja), zl(o.obecna_pensja),
        `<input type="number" id="kf-${esc(o.pracownik)}" step="10" style="width:110px" value="${kf[o.pracownik] || ""}" ${edycja ? "" : "disabled"}>`,
        `<button class="btn pom maly" data-akcja="kontroferta" data-id="${esc(o.pracownik)}" ${edycja ? "" : "disabled"}>Zapisz</button>`])
        : [["Nikt nie składa ofert twoim pracownikom.", "", "", "", "", ""]], { klasy: ["l", "l"] })
      + `<p class="podpowiedz">Pracownik przyjmie najwyższą ofertę, jeśli jest wyższa od jego pensji i od twojej kontroferty.
         Wygrana kontroferta staje się jego nową pensją. Oferty widać, gdy druga drużyna zapisze decyzje.</p>`;

    html += tabela("Twoi pracownicy – staż i okres wypowiedzenia", ["Pracownik", "Zawód", "Umowa", "Staż", "Okres wypowiedzenia", "Status"],
      A.moi.length ? A.moi.map((p) => [esc(p.imie_nazwisko), `${esc(p.zawod)} ${gw(p.gwiazdki)}`, UMOWA(kat, p.umowa), rundy(p.staz),
        p.okres ? rundy(p.okres) : "od razu",
        p.odchodzi ? `<span class="minus">${p.odchodzi.do ? `odchodzi do ${esc(nazwaFirmy(v, p.odchodzi.do))}` : "zwolniony – odchodzi"} w rundzie ${p.odchodzi.runda}</span>` : "pracuje"])
        : [["Nie masz jeszcze pracowników.", "", "", "", "", ""]], { klasy: ["l", "l", "l"] });

    if (!A.headhunter) {
      return html + `<p class="podpowiedz">Headhunter (podkupywanie pracowników innych drużyn) – od rundy ${A.kanaly.headhunter.od_rundy}.</p>`;
    }
    const moje = Object.fromEntries((d.podkup || []).map((o) => [o.pracownik, o]));
    html += tabela("Headhunter – pracownicy innych drużyn", ["Pracownik", "Drużyna", "Zawód", "Pensja", "Umowa", "Okres wypowiedzenia", "Twoja oferta"],
      A.cudzy.length ? A.cudzy.map((p) => [esc(p.imie_nazwisko) + pigulkaOfert(v, "pracownicy", p.id), esc(nazwaFirmy(v, p.firma)), `${esc(p.zawod)} ${gw(p.gwiazdki)}`, zl(p.pensja),
        UMOWA(kat, p.umowa), p.okres ? rundy(p.okres) : "od razu",
        p.odchodzi ? `<span class="podpowiedz">w okresie wypowiedzenia</span>`
          : moje[p.id] ? `${zl(moje[p.id].pensja)} <button class="btn jasny maly" data-akcja="wycofaj-oferte" data-id="${esc(p.id)}" ${edycja ? "" : "disabled"}>Wycofaj</button>`
            : `<button class="btn pom maly" data-akcja="oferta-podkupienia" data-id="${esc(p.id)}" ${edycja ? "" : "disabled"}>Złóż ofertę</button>`])
        : [["Inne drużyny nie mają jeszcze pracowników.", "", "", "", "", "", ""]], { klasy: ["l", "l", "l"] });
    return html;
  },
  wyniki({ v }) {
    const R = v.wyniki?.rynek_pracy;
    if (!R) return brakWynikow("Wyniki pojawią się po pierwszej rundzie.");
    const pusto = (n, t) => [[t, ...Array(n - 1).fill("")]];
    const kanaly = v.agencja?.kanaly || {};
    const ruchy = [...R.odejscia.map((o) => [esc(o.imie_nazwisko), `<span class="minus">odejście</span>`, o.do ? esc(nazwaFirmy(v, o.do)) : "koniec wypowiedzenia – pula kandydatów"]),
      ...R.przyjscia.map((o) => [esc(o.imie_nazwisko), `przyjście (stanowisko nr ${o.stanowisko})`, esc(nazwaFirmy(v, o.od))])];
    const nZ = R.zatrudnieni.length, wygr = R.licytacje.filter((l) => l.wygrana).length, odch = R.odejscia.length, przy = R.przyjscia.length;
    const lead = podsumowanie([nZ ? `W tej rundzie zatrudniono <b>${licz(nZ)}</b> ${nZ === 1 ? "osobę" : "osób"}.` : "W tej rundzie nikogo nie zatrudniono.",
      R.licytacje.length ? `Wygrano ${licz(wygr)} z ${licz(R.licytacje.length)} licytacji o kandydatów.` : "",
      odch || przy ? `Z zespołu odeszło ${licz(odch)}, dołączyło ${licz(przy)} osób przejętych od innych drużyn.` : ""], odch > przy ? "uwaga" : "");
    const kafle = kafelkiLiczb([{ etykieta: "Zatrudnieni", wartosc: licz(nZ) }, R.licytacje.length && { etykieta: "Wygrane licytacje", wartosc: `${licz(wygr)} / ${licz(R.licytacje.length)}` },
      { etykieta: "Odejścia", wartosc: licz(odch), ton: odch ? "minus" : "" }, { etykieta: "Przyjścia", wartosc: licz(przy), ton: przy ? "plus" : "" }]);
    return lead + kafle + zwinTabela("Zatrudnieni w rundzie", ["Pracownik", "Kanał", "Koszt zatrudnienia", "Pensja"],
      R.zatrudnieni.length ? R.zatrudnieni.map((z) => [esc(z.imie_nazwisko), esc(kanaly[z.kanal]?.nazwa || z.kanal), zl(z.koszt), zl(z.pensja)])
        : pusto(4, "Nikogo nie zatrudniono."), { klasy: ["l", "l"], otwarte: nZ > 0 })
      + zwinTabela("Licytacje kandydatów", ["Kandydat", "Drużyn", "Twoja pensja", "Wygrała", "Za ile", "Wynik"],
        R.licytacje.length ? R.licytacje.map((l) => [esc(l.imie_nazwisko), l.druzyn ? licz(l.druzyn) : "–", zl(l.pensja),
          l.wygral ? esc(nazwaFirmy(v, l.wygral)) : "–", zl(l.najwyzsza),
          l.wygrana ? `wygrana${l.remis ? " (remis – losowanie)" : ""}` : `<span class="minus">przegrana${l.remis ? " (remis – losowanie)" : ""}</span>`])
          : pusto(6, "Nikt inny nie chciał twoich kandydatów."), { klasy: ["l", "", "", "l"] })
      + `<p class="podpowiedz">Pensje porównuje się w przeliczeniu na umowę o pracę (B2B ÷ 1,25, pół etatu × 2).</p>`
      + zwinTabela("Twoje oferty podkupienia", ["Pracownik", "Drużyna", "Pensja", "Wynik"],
        R.oferty_zlozone.length ? R.oferty_zlozone.map((o) => [esc(o.imie_nazwisko), esc(nazwaFirmy(v, o.firma)), zl(o.pensja),
          esc(WYNIK_ZLOZONEJ[o.wynik] || o.wynik) + (o.powod ? `: ${esc(o.powod)}` : "")
            + (o.runda_przejscia ? ` – przejdzie w rundzie ${o.runda_przejscia}` : "")
            + (o.wynik === "inna_firma" && o.wygral ? ` (${esc(nazwaFirmy(v, o.wygral))} za ${zl(o.najwyzsza)})` : "")
            + (o.wynik === "kontroferta" && o.najwyzsza ? ` (szef dał ${zl(o.najwyzsza)})` : "")])
          : pusto(4, "Bez ofert."), { klasy: ["l", "l", "r", "l"] })
      + zwinTabela("Oferty dla twoich pracowników", ["Pracownik", "Od", "Najwyższa oferta", "Kontroferta", "Wynik"],
        R.oferty_otrzymane.length ? R.oferty_otrzymane.map((o) => [esc(o.imie_nazwisko), o.od.map((f) => esc(nazwaFirmy(v, f))).join(", "),
          zl(o.najwyzsza), o.kontroferta ? zl(o.kontroferta) : "–",
          esc(WYNIK_OTRZYMANEJ[o.wynik] || o.wynik) + (o.runda_odejscia ? ` do ${esc(nazwaFirmy(v, o.do))} w rundzie ${o.runda_odejscia}` : "")])
          : pusto(5, "Nikt nie składał ofert."), { klasy: ["l", "l", "r", "r", "l"] })
      + zwinTabela("Odejścia i przyjścia", ["Pracownik", "Ruch", "Drużyna"], ruchy.length ? ruchy : pusto(3, "Bez zmian w zespole."), { klasy: ["l", "l", "l"] })
      + przenosinyWyniki(v, R)
      + (R.uwagi.length ? `<div class="komunikat zly">${R.uwagi.map(esc).join("<br>")}</div>` : "");
  },
  akcje: {
    kontroferta: async (el, c) => {
      const id = el.dataset.id, x = +document.getElementById(`kf-${id}`).value || 0;
      const moj = c.v.agencja.moi.find((p) => p.id === id), min = minimum(c.kat, moj?.umowa || "prace", moj?.student);
      if (x && x < min) return toast(`Kontroferta nie może być niższa niż ${licz(min)} PLN.`);
      await c.zmien((d) => {
        const kf = { ...(d.kontroferty || {}) };
        if (x) kf[id] = x; else delete kf[id];
        d.kontroferty = kf;
      });
    },
    "oferta-podkupienia": (el, c) => {
      const inne = (c.d.podkup || []).filter((o) => o.pracownik !== el.dataset.id);
      if (ponadLimitPracownikow(c.v, c.d.zatrudnij || [], inne)) return toast(tekstLimituPracownikow(c.v));
      return oknoOferty(c, el.dataset.id);
    },
    "potwierdz-oferte": async (el, c) => {
      const p = c.v.agencja.cudzy.find((x) => x.id === el.dataset.id);
      const pensja = +document.getElementById("o-pensja").value, umowa = document.getElementById("o-umowa").value;
      const min = minimum(c.kat, umowa, p.student);
      if (pensja < min) return toast(`Pensja w tej formie nie może być niższa niż ${licz(min)} PLN.`);
      zamknijOkno();
      await c.zmien((d) => {
        d.podkup = [...(d.podkup || []).filter((o) => o.pracownik !== p.id), { pracownik: p.id, firma: p.firma, pensja, umowa }];
      });
    },
    "wycofaj-oferte": async (el, c) => {
      await c.zmien((d) => { d.podkup = (d.podkup || []).filter((o) => o.pracownik !== el.dataset.id); });
    },
  },
};

// UF20: obsada i przenosiny w rundzie – przeniesieni, odmowy (brak zgody) i nieudane (np. zajęte stanowisko)
function przenosinyWyniki(v, R) {
  const wiersz = (x, wynik) => [esc(x.imie_nazwisko), x.z_lokalu ? esc(nazwaLokalu(v, x.z_lokalu)) : "–",
    `${x.do_lokalu ? `${esc(nazwaLokalu(v, x.do_lokalu))} · ` : ""}nr ${x.nr}`, x.dodatek ? zl(x.dodatek) : "–", wynik];
  const w = [...(R.przeniesieni || []).map((x) => wiersz(x, x.wynik === "przeniesiony" ? "przeniesiony"
    : `<span class="minus">nieudane: ${esc(x.powod)}</span>`)),
  ...(R.przenosiny || []).filter((x) => !x.zgoda).map((x) => wiersz({ ...x, dodatek: 0 }, `<span class="minus">odmowa${x.powod ? ` – ${esc(x.powod)}` : ""}</span>
      <span class="podpowiedz">(szansa była ok. ${proc(x.szansa, 0)})</span>`))];
  return w.length ? tabela("Obsada i przenosiny", ["Pracownik", "Skąd", "Dokąd", "Dodatek", "Wynik"], w, { klasy: ["l", "l", "l", "r", "l"] }) : "";
}

function oknoOferty({ v, kat }, id) {
  const p = v.agencja.cudzy.find((x) => x.id === id), hh = v.agencja.kanaly.headhunter;
  const krok = 10, propozycja = Math.ceil(p.pensja * 1.1 / krok) * krok;
  okno(`Oferta przez headhuntera: ${esc(p.imie_nazwisko)}`, `<p>${esc(p.zawod)} ${gw(p.gwiazdki)} · ${esc(nazwaFirmy(v, p.firma))} ·
      obecna pensja <b>${zl(p.pensja)}</b> · ${UMOWA(kat, p.umowa)} (okres wypowiedzenia: ${p.okres ? rundy(p.okres) : "od razu"})</p>
    <div class="dwie"><label class="pole">Oferowane wynagrodzenie brutto
      <input type="number" id="o-pensja" min="${minimum(kat, "prace", p.student)}" step="10" value="${propozycja}"></label>
    <label class="pole">Forma zatrudnienia u ciebie<select id="o-umowa">${opcjeForm(v, kat, p, "prace", { nowy: false })}</select></label></div>
    <p class="podpowiedz">Pracownik porównuje oferty w przeliczeniu na umowę o pracę (pół etatu × 2, B2B ÷ narzut kontraktu).</p>
    <p class="podpowiedz">Opłata headhuntera po przyjęciu oferty: ${licz(hh.podkupienie_czesc_pensji * 100)}% oferowanej pensji.
      Obecny pracodawca może złożyć kontrofertę. Gdy pracownik przyjdzie, potrzebuje wolnego stanowiska.</p>`,
  { srednie: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="potwierdz-oferte" data-id="${esc(id)}">Złóż ofertę</button>` });
}
