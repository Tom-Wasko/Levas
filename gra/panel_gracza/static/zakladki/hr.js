// Ludzie: zatrudnienie (obsada stanowisk w Mój lokal), zespół, udogodnienia, szkolenia.
// UF20 (gra z lokalami): nowych ludzi zatrudnia się w Rynku pracy (od razu z lokalem i stanowiskiem), a obsada w Moim
// lokalu przypisuje osoby już zatrudnione – z tego lokalu od razu, z innego za zgodą pracownika (decyzja `przenosiny`).
import { esc, naOkres, naRunde, OKRES, gw, inicjaly, licz, nazwaFirmy, okno, ponadLimitPracownikow, podsumowanie, kafelkiLiczb, proc, tabela, tekstLimituPracownikow, toast,
  wykres, zamknijOkno, zl, zwinTabela } from "./wspolne.js";
import { kafleUdogodnien, przelaczUdog } from "./inwestycje.js";
import { kolko } from "./dymki.js";
import { idWybranego, nazwaLokalu, stanowiskaLokalu, wyborLokaluKrotki } from "./lokal_wybor.js";
import { forma, kosztMiesieczny, minimum, nazwaFormy, oczekiwana, opcjeForm, opisFormy, pigulkaStudenta } from "./formy.js";

const TYPY = ["kuchnia", "kasa"];  // nazwy i zawody typów: kat.oferty.stanowiska.typy (katalog.yaml)
const NIEZADOWOLENIE = "niezadowolenie";   // silnik/ludzie/zadowolenie.py: powód wypowiedzenia (U20)

// UF18: „oferty: 2 drużyny” – ile innych drużyn złożyło już ofertę dla tej osoby (bez kwot; silnik: rynek_pracy.zainteresowanie)
const druzyn = (n) => `${n} ${n === 1 ? "drużyna" : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? "drużyny" : "drużyn"}`;
export function pigulkaOfert(v, rodzaj, id) {
  const n = v.agencja?.zainteresowanie?.[rodzaj]?.[id];
  return n ? ` <span class="pigulka nie" title="Tyle innych drużyn chce już zatrudnić tę osobę w tej rundzie – wygra wyższa pensja">oferty: ${druzyn(n)}</span>` : "";
}
// UF18: próba podkupienia mojego pracownika (oferty innych drużyn zapisane w tej rundzie)
function pigulkaPodkupienia(v, p) {
  const o = (v.agencja?.oferty_dla_mnie || []).filter((x) => x.pracownik === p.id && x.pensja > x.obecna_pensja);
  if (!o.length) return "";
  const kto = [...new Set(o.map((x) => nazwaFirmy(v, x.od)))].map(esc).join(", ");
  return ` <a class="pigulka nie" data-zakladka-k="rynek_pracy" title="Złóż kontrofertę w zakładce Rynek pracy">chce go podkupić: ${kto}</a>`;
}

// U20: krótki żartobliwy opis osoby pod „i” – z niego gracz zgaduje ukrytą cechę
const opisOsoby = (o) => kolko(esc(o.opis || ""));
const zadowolenieOsoby = (p) => p.zadowolenie == null ? "–"
  : `<span class="${p.niezadowolony ? "minus" : ""}">${licz(p.zadowolenie, 2)}</span>`;

// koszt za rundę: pensje miesięczne z ZUS pracodawcy (wg formy zatrudnienia, UF21) przeliczone na rundę + premie (bez ZUS)
function kosztWynagrodzen(v, kat) {
  return v.stan.pracownicy.reduce((s, p) => s + naRunde(kosztMiesieczny(kat, p)) + (p.premia || 0), 0);
}

// UF21: pensja w oknie zatrudnienia/profilu musi spełnić minimum formy (pół etatu – połowa, B2B i staż – bez)
function zlaPensja(kat, pensja, umowa, osoba) {
  const min = minimum(kat, umowa, osoba?.student);
  return pensja < min ? `Pensja w tej formie nie może być niższa niż ${licz(min)} PLN.` : null;
}

export const zatrudnienie = {
  tytul: "Zatrudnienie", tytulPelny: "HR - zatrudnienie", ikona: "☺", odblokowanie: "hr_zatrudnienie",
  info: "Zatrudnij pracowników potrzebnych do przygotowania i sprzedaży wybranych dań. Pracownik potrzebuje stanowiska (Wnętrze ▸ Stanowiska i sprzęt).",
  decyzje({ v, kat, edycja }) {
    let html = `<div class="pasek ciemny"><span>Koszty wynagrodzeń: <span class="kwota">${zl(kosztWynagrodzen(v, kat), true)}</span>${naOkres()} brutto (z ZUS pracodawcy; pensje w umowach – miesięczne)</span></div>`;
    if (v.nieudane_zatrudnienia?.length) html += `<div class="komunikat zly">Część kandydatów zatrudniła już inna firma – wybierz innych.</div>`;
    for (const typ of TYPY) {
      const st = stanowiskaLokalu(v, v.stan.stanowiska).filter((s) => s.typ === typ);
      html += `<div class="pasek">${esc(kat.oferty.stanowiska.typy[typ].nazwa)}${idWybranego(v) ? ` – ${esc(nazwaLokalu(v, idWybranego(v)))}` : ""}</div>`;
      if (!st.length) { html += `<p class="podpowiedz">Brak stanowisk – uruchom je w zakładce Wnętrze ▸ Stanowiska i sprzęt.</p>`; continue; }
      html += `<div class="siatka waska">${st.map((s) => {
        const p = v.stan.pracownicy.find((x) => x.id === s.pracownik);
        const wl = v.decyzje.wlasciciel_stanowisko;
        if (!p && wl && wl.typ === typ && wl.nr === s.nr) return kafelWlasciciela(v, s, edycja);
        if (!p && v.lokale) return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}</div><div class="kt srodek"><div class="awatar pusty">+</div>
          <button class="btn jasny" data-akcja="przypisz" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Przypisz osobę →</button>
          <button class="btn jasny maly" style="margin-top:6px" data-akcja="wlasciciel" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Stań sam (właściciel)</button>
          <span class="podpowiedz" style="margin-top:6px">Nowa osoba: <a data-zakladka-k="rynek_pracy">Rynek pracy</a></span></div></div>`;
        if (!p) return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}</div><div class="kt srodek"><div class="awatar pusty">+</div>
          <button class="btn jasny" data-akcja="kandydaci" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Zatrudnij pracownika →</button>
          ${v.lokale ? `<button class="btn jasny maly" style="margin-top:6px" data-akcja="wlasciciel" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Stań sam (właściciel)</button>` : ""}</div></div>`;
        const nowy = p.od_rundy === v.runda, prz = (v.decyzje.przenosiny || []).find((x) => x.pracownik === p.id);
        const ruch = prz ? `<span class="pigulka inf">${przenosinyMiedzyLokalami(v, prz) ? "czeka na zgodę" : "przeniesiony"}</span>` : "";
        const wyp = p.odchodzi ? `<span class="pigulka${p.odchodzi.powod === NIEZADOWOLENIE ? " nie" : ""}">wypowiedzenie do r. ${p.odchodzi.runda}</span>`
          : p.niezadowolony ? '<span class="pigulka nie">niezadowolony</span>' : "";
        return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}${nowy ? '<span class="pigulka inf">nowy</span>' : ""}${ruch}${wyp}${opisOsoby(p)}</div>
          <div class="kt srodek" data-akcja="profil" data-id="${esc(p.id)}" style="cursor:pointer"><div class="awatar">${inicjaly(p.imie_nazwisko)}</div>
          <b>${esc(p.imie_nazwisko)}</b>${pigulkaStudenta(p)}<br><span class="podpowiedz">${esc(p.zawod)} · ${nazwaFormy(kat, p.umowa)}</span><br>${gw(p.gwiazdki)}<br>
          <b class="akcent">${zl(p.pensja)}</b>${p.premia ? `<br><span class="podpowiedz">premia ${zl(p.premia)}</span>` : ""}</div>
          ${prz ? `<button class="btn jasny maly" data-akcja="cofnij-przenosiny" data-id="${esc(p.id)}" ${edycja ? "" : "disabled"}>Cofnij przeniesienie</button>` : ""}</div>`;
      }).join("")}</div>`;
    }
    if (v.lokale) html += `<p class="podpowiedz">Na wolne stanowisko przypiszesz osobę z tego lokalu (od razu) albo z innego Twojego lokalu –
      wtedy pracownik musi się zgodzić (zależy to od jego zadowolenia, odległości i dodatku za przejście; odpowiedź po przeliczeniu rundy).
      Nowych ludzi zatrudniasz w zakładce <a data-zakladka-k="rynek_pracy">Rynek pracy</a>.</p>
      <p class="podpowiedz">Brakuje rąk do pracy? Właściciel może sam stanąć na jednym wolnym stanowisku – pracuje jak
      pracownik 1★, bez pensji, ale każda godzina schodzi z puli <a data-zakladka-k="czas_wlasciciela">czasu właściciela</a>.</p>`;
    return html;
  },
  wyniki({ v, kat }) {
    const r = v.rynek, ZAWODY = kat.zawody;
    const firmy = Object.keys(r.pracownicy || {});
    const liczba = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...ZAWODY.map((z) => {
      const g = r.pracownicy[f][z]; const n = g[1] + g[2] + g[3];
      return n ? `${n} <span class="podpowiedz">(${g[1]}★ ${g[2]}★★ ${g[3]}★★★)</span>` : "0";
    })]);
    const wyk = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...ZAWODY.map((z) => proc(r.wykorzystanie[f][z]))]);
    const pensje = firmy.map((f) => [esc(nazwaFirmy(v, f)), ...ZAWODY.map((z) => r.wynagrodzenia[f][z] ? zl(r.wynagrodzenia[f][z]) : "–")]);
    const moi = (v.wyniki?.pracownicy || []).map((p) => [esc(p.imie_nazwisko), esc(p.zawod), gw(p.gwiazdki), `nr ${p.stanowisko}`, proc(p.wykorzystanie),
      zl(p.pensja), zadowolenieOsoby(p) + (p.powody?.length ? `<br><span class="podpowiedz">${p.powody.map(esc).join(", ")}</span>` : "")]);
    const wl = v.wyniki?.wlasciciel_stanowisko;
    if (wl?.przyjete) moi.push([`<b>Właściciel</b> <span class="podpowiedz">(${licz(wl.godziny, 1)} h)</span>`, esc(kat.oferty.stanowiska.typy[wl.typ]?.kto || wl.typ),
      gw(1), `nr ${wl.nr}`, proc(wl.wykorzystanie || 0), "bez pensji", "–"]);
    const odejscia = (v.wyniki?.odejscia_pracownikow || []).map((o) => [esc(o.imie_nazwisko), licz(o.zadowolenie, 2), o.powody.map(esc).join(", "),
      `runda ${o.runda_odejscia}`]);
    const L = v.wyniki?.pracownicy || [], nzad = L.filter((p) => p.niezadowolony).length, sr = L.length ? L.reduce((a, p) => a + (p.wykorzystanie || 0), 0) / L.length : 0;
    const lead = !L.length ? podsumowanie("Nie masz jeszcze zatrudnionych pracowników.") : podsumowanie([
      `W zespole pracuje <b>${licz(L.length)}</b> ${L.length === 1 ? "osoba" : "osób"}, średnie wykorzystanie czasu to <b>${proc(sr, 0)}</b>.`,
      nzad ? `Niezadowolonych jest ${licz(nzad)} – bez zmian mogą złożyć wypowiedzenie.` : "Nikt nie jest niezadowolony.",
      odejscia.length ? `Z niezadowolenia odchodzi ${licz(odejscia.length)} ${odejscia.length === 1 ? "osoba" : "osób"}.` : ""], nzad || odejscia.length ? "uwaga" : "ok");
    const kafle = L.length ? kafelkiLiczb([{ etykieta: "Pracownicy", wartosc: licz(L.length) }, { etykieta: "Średnie wykorzystanie czasu", wartosc: proc(sr, 0) },
      { etykieta: "Niezadowoleni", wartosc: licz(nzad), ton: nzad ? "minus" : "plus" }, { etykieta: "Wypowiedzenia", wartosc: licz(odejscia.length), ton: odejscia.length ? "minus" : "" }]) : "";
    return lead + kafle + zwinTabela("Twoi pracownicy", ["Pracownik", "Zawód", "Doświadczenie", "Stanowisko", "Wykorzystanie czasu", "Wynagrodzenie", "Zadowolenie"], moi, { klasy: ["l"], otwarte: true })
      + (odejscia.length ? zwinTabela("Wypowiedzenia z niezadowolenia", ["Pracownik", "Zadowolenie", "Powody", "Odchodzi"], odejscia, { klasy: ["l"], otwarte: true }) : "")
      + zwinTabela("Liczba pracowników", ["Zespół", ...ZAWODY], liczba, { klasy: ["l"] })
      + zwinTabela("Wykorzystanie czasu pracowników", ["Zespół", ...ZAWODY], wyk, { klasy: ["l"] })
      + zwinTabela("Średnie wynagrodzenie pracowników", ["Zespół", ...ZAWODY], pensje, { klasy: ["l"] })
      + `<p class="podpowiedz">Wykorzystanie 100% oznacza, że pracownik nie miał czasu na kolejnych klientów (możliwa utracona sprzedaż).</p>`;
  },
  akcje: {
    kandydaci: (el, c) => oknoKandydatow(c, el.dataset.t, +el.dataset.n),
    zatrudnij: (el, c) => {
      const { k, t, n } = el.dataset;   // bez t/n (Rynek pracy) – lokal i stanowisko wybiera się w oknie
      const inne = (c.d.zatrudnij || []).filter((z) => !(z.typ === t && z.nr === +n) && z.kandydat !== k);   // zastąpienie się nie liczy
      if (ponadLimitPracownikow(c.v, inne, c.d.podkup || [])) return toast(tekstLimituPracownikow(c.v));
      return oknoZatrudnienia(c, k, t, t ? +n : null);
    },
    "potwierdz-zatrudnienie": async (el, c) => {
      const umowa = document.getElementById("z-umowa").value;
      const pensja = forma(c.kat, umowa).staz ? 0 : +document.getElementById("z-pensja").value;
      const blad = zlaPensja(c.kat, pensja, umowa, c.v.kandydaci.find((x) => x.id === el.dataset.k));
      if (blad) return toast(blad);
      const miejsce = document.getElementById("z-miejsce");
      if (miejsce && !miejsce.value) return toast("Wybierz lokal i stanowisko dla nowej osoby.");
      const [t, n] = miejsce ? miejsce.value.split(":") : [el.dataset.t, el.dataset.n];
      const { k } = el.dataset, kanal = document.getElementById("z-kanal")?.value;
      zamknijOkno();
      await c.zmien((d) => {
        d.zatrudnij = [...(d.zatrudnij || []).filter((z) => !(z.typ === t && z.nr === +n) && z.kandydat !== k),
          { kandydat: k, typ: t, nr: +n, pensja, umowa, ...(kanal ? { kanal } : {}) }];
      });
    },
    przypisz: (el, c) => oknoPrzypisania(c, el.dataset.t, +el.dataset.n),
    "wybierz-osobe": (el, c) => {
      const { id, t, n } = el.dataset;
      if (el.dataset.inny !== "1") return zapiszPrzenosiny(c, { pracownik: id, typ: t, nr: +n });
      return oknoPrzenosin(c, id, t, +n);
    },
    "potwierdz-przenosiny": (el, c) => {
      const dodatek = Math.max(0, +(document.getElementById("pz-dodatek")?.value || 0));
      return zapiszPrzenosiny(c, { pracownik: el.dataset.id, typ: el.dataset.t, nr: +el.dataset.n, ...(dodatek ? { dodatek } : {}) });
    },
    "cofnij-przenosiny": (el, c) => c.zmien((d) => { d.przenosiny = (d.przenosiny || []).filter((x) => x.pracownik !== el.dataset.id); }),
    wlasciciel: (el, c) => oknoWlasciciela(c, el.dataset.t, +el.dataset.n),
    "potwierdz-wlasciciela": async (el, c) => {
      const godziny = +document.getElementById("w-godziny").value;
      if (!(godziny > 0)) return toast("Podaj liczbę godzin większą od zera.");
      zamknijOkno();
      await c.zmien((d) => { d.wlasciciel_stanowisko = { typ: el.dataset.t, nr: +el.dataset.n, godziny }; });
    },
    "zejdz-wlasciciel": (el, c) => c.zmien((d) => { delete d.wlasciciel_stanowisko; }),
    profil: (el, c) => oknoProfilu(c, el.dataset.id),
    "zapisz-profil": async (el, c) => {
      const id = el.dataset.id, nowy = el.dataset.nowy === "1";
      const umowa = document.getElementById("p-umowa").value;
      const pensja = forma(c.kat, umowa).staz ? 0 : +document.getElementById("p-pensja").value;
      const premia = +(document.getElementById("p-premia")?.value || 0);
      const blad = zlaPensja(c.kat, pensja, umowa, c.v.stan.pracownicy.find((x) => x.id === id));
      if (blad) return toast(blad);
      zamknijOkno();
      await c.zmien((d) => {
        if (nowy) d.zatrudnij = (d.zatrudnij || []).map((z) => z.kandydat === id ? { ...z, pensja, umowa } : z);
        else d.zmiany = { ...(d.zmiany || {}), [id]: { pensja, umowa, premia } };
      });
    },
    zwolnij: async (el, c) => {
      const id = el.dataset.id, nowy = el.dataset.nowy === "1";
      if (!nowy && !confirm("Zwolnić pracownika? Trzeba zapłacić odprawę, a na umowie o pracę przez 2 rundy wypowiedzenia nadal pracuje i dostaje pensję.")) return;
      zamknijOkno();
      await c.zmien((d) => {
        if (nowy) d.zatrudnij = (d.zatrudnij || []).filter((z) => z.kandydat !== id);
        else d.zwolnij = [...new Set([...(d.zwolnij || []), id])];
      });
    },
    "cofnij-zwolnienie": async (el, c) => {
      zamknijOkno();
      await c.zmien((d) => { d.zwolnij = (d.zwolnij || []).filter((x) => x !== el.dataset.id); });
    },
  },
  zmiany: {
    // UF21: zmiana formy w oknie zatrudnienia/profilu – pensja oczekiwana w tej formie, minimum i opis
    "forma-zatrudnienia": (el, c) => {
      const osoba = c.v.kandydaci.find((x) => x.id === el.dataset.k) || c.v.stan.pracownicy.find((x) => x.id === el.dataset.k);
      if (!osoba) return;
      const pole = document.getElementById(el.dataset.pensja), u = el.value, staz = !!forma(c.kat, u).staz;
      if (pole) {
        pole.disabled = staz;
        pole.min = minimum(c.kat, u, osoba.student);
        if (staz) pole.value = 0;   // kandydat – pensja oczekiwana w nowej formie; pracownik – tylko po stażu (0)
        else if (c.v.kandydaci.includes(osoba) || !+pole.value) pole.value = oczekiwana(c.kat, osoba, u);
      }
      const opis = document.getElementById(el.dataset.opis);
      if (opis) opis.innerHTML = opisFormy(c.kat, u, osoba);
    },
  },
};

// P5: właściciel jako pracownik 1★ na jednym wolnym stanowisku (godziny z puli czasu właściciela)
function kafelWlasciciela(v, s, edycja) {
  const wl = v.decyzje.wlasciciel_stanowisko, plan = v.wlasciciel_stanowisko;
  const odrzucone = plan && plan.typ === wl.typ && plan.nr === wl.nr && !plan.przyjete;
  return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}<span class="pigulka inf">właściciel</span></div>
    <div class="kt srodek"><div class="awatar">Ty</div><b>Właściciel</b><br>${gw(1)}<br>
    <span class="podpowiedz">${licz(wl.godziny, 1)} h w tym tygodniu · bez pensji</span>
    ${odrzucone ? `<br><span class="minus">${esc(plan.powod)}</span>` : ""}
    <div style="margin-top:6px"><button class="btn jasny maly" data-akcja="wlasciciel" data-t="${s.typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Zmień godziny</button>
    <button class="btn czarny maly" data-akcja="zejdz-wlasciciel" ${edycja ? "" : "disabled"}>Zejdź</button></div></div></div>`;
}

function oknoWlasciciela({ v }, typ, nr) {
  const C = v.czas_wlasciciela, teraz = v.decyzje.wlasciciel_stanowisko;
  const juz = teraz && teraz.typ === typ && teraz.nr === nr && v.wlasciciel_stanowisko?.przyjete ? teraz.godziny : 0;
  const wolne = Math.max(0, (C?.wolne || 0) + juz);
  const inne = teraz && !(teraz.typ === typ && teraz.nr === nr)
    ? `<div class="komunikat">Właściciel stoi już na innym stanowisku (nr ${teraz.nr}) – przejdzie tutaj.</div>` : "";
  okno(`Właściciel na stanowisku nr ${nr}`, `${inne}<p>Właściciel pracuje jak pracownik <b>1★</b> (niższa jakość dań, częstsze
      reklamacje), nie dostaje pensji, ale jego godziny schodzą z puli czasu właściciela – zabraknie ich na zakupy w dyskontach,
      rekrutację i eventy w parkach.</p>
    <label class="pole">Godziny w tym tygodniu (wolne teraz: ${licz(wolne, 1)} h, pełny etat: 40 h)
      <input type="number" id="w-godziny" min="1" max="${Math.max(1, Math.floor(wolne))}" step="1" value="${Math.max(1, Math.min(8, Math.floor(wolne)))}"></label>
    <p class="podpowiedz">W prawdziwym biznesie to częsty start: właściciel sam staje za ladą, zanim stać go na etat. Uważaj tylko,
      żeby nie zabrakło mu czasu na prowadzenie firmy.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="potwierdz-wlasciciela" data-t="${typ}" data-n="${nr}">Potwierdź</button>` });
}

function oknoKandydatow({ v, kat }, typ, nr) {
  const typy = kat.oferty.stanowiska.typy, zawody = typy[typ].zawody;
  const lista = v.kandydaci.filter((k) => zawody.includes(k.zawod)).sort((a, b) => b.zadowolenie_klientow - a.zadowolenie_klientow);
  const w = lista.map((k) => [esc(k.imie_nazwisko) + pigulkaStudenta(k) + opisOsoby(k), gw(k.gwiazdki), esc(k.zawod), licz(k.pensja_preferowana), licz(k.koszt_rekrutacji),
    licz(k.koszt_odprawy), proc(k.zadowolenie_klientow, 0), proc(k.ryzyko_reklamacji, 0),
    `<button class="btn pom maly" data-akcja="zatrudnij" data-k="${esc(k.id)}" data-t="${typ}" data-n="${nr}">Zatrudnij +</button>`]);
  okno(`Zatrudnienie na „Stanowisko nr ${nr}”`, tabela(null, ["Imię i nazwisko", "Doświadczenie", "Zawód", "Preferowane wynagrodzenie",
    "Koszty rekrutacji", "Koszt odprawy", "Zadowolenie klientów", "Ryzyko reklamacji", "Akcje"], w, { klasy: ["l"] })
    + `<p class="podpowiedz">${TYPY.map((t) => `${esc(typy[t].kto)}: ${typy[t].zawody.map(esc).join(", ")}`).join(" · ")}</p>`);
}

// gra z lokalami: kandydata szuka się przez kanał rekrutacji (zakładka Rynek pracy) – koszt i czas właściciela zależą od kanału
function kanalyRekrutacji(v, k) {
  const A = v.agencja;
  if (!A) return "";
  const opcje = (A.kanaly_kandydatow[k.id] || []).map((n) => {
    const kn = A.kanaly[n], koszt = kn.oplata + kn.mnoznik_rekrutacji * k.koszt_rekrutacji;
    return `<option value="${esc(n)}">${esc(kn.nazwa)} – ${zl(koszt)}${kn.czas_wlasciciela ? `, ${licz(kn.czas_wlasciciela, 1)} h czasu właściciela` : ""}</option>`;
  }).join("");
  return `<label class="pole">Kanał rekrutacji (<a data-zakladka-k="rynek_pracy">Rynek pracy</a>)<select id="z-kanal">${opcje}</select></label>
    <p class="podpowiedz">Gdy kandydata chce kilka drużyn, wygrywa najwyższa pensja (remis – losowanie).</p>`;
}

// UF20: wolne stanowiska dla zawodu (bez stanowiska właściciela) – w podglądzie decyzji, więc już po przenosinach
const typyZawodu = (kat, zawod) => TYPY.filter((t) => kat.oferty.stanowiska.typy[t].zawody.includes(zawod));
function wolneStanowiska(v, kat, zawod) {
  const wl = v.decyzje.wlasciciel_stanowisko, typy = typyZawodu(kat, zawod);
  return v.stan.stanowiska.filter((s) => typy.includes(s.typ) && !s.pracownik && !(wl && wl.typ === s.typ && wl.nr === s.nr));
}
function wyborMiejsca(v, kat, zawod) {
  const wolne = wolneStanowiska(v, kat, zawod), T = kat.oferty.stanowiska.typy;
  if (!wolne.length) return `<div class="komunikat zly">Nie masz wolnego stanowiska dla zawodu „${esc(zawod)}”. Uruchom nowe w zakładce
    Wnętrze ▸ Stanowiska i sprzęt albo zwolnij miejsce.</div><input type="hidden" id="z-miejsce" value="">`;
  const opcja = (s) => `<option value="${s.typ}:${s.nr}">${esc(T[s.typ].nazwa)} nr ${s.nr}</option>`;
  const lokale = [...new Set(wolne.map((s) => s.lokal))];
  const opcje = v.lokale && lokale.length > 1
    ? lokale.map((l) => `<optgroup label="${esc(nazwaLokalu(v, l))}">${wolne.filter((s) => s.lokal === l).map(opcja).join("")}</optgroup>`).join("")
    : wolne.map(opcja).join("");
  return `<label class="pole">Lokal i stanowisko${v.lokale && lokale.length === 1 ? ` (${esc(nazwaLokalu(v, lokale[0]))})` : ""}
    <select id="z-miejsce">${opcje}</select></label>`;
}

function oknoZatrudnienia({ v, kat }, id, typ, nr) {
  const k = v.kandydaci.find((x) => x.id === id);
  okno(`Zatrudnienie: ${esc(k.imie_nazwisko)}`, `<p>${esc(k.zawod)} ${gw(k.gwiazdki)} · preferowane wynagrodzenie <b>${zl(k.pensja_preferowana)}</b>
      · ${v.agencja ? "bazowy " : ""}koszt rekrutacji ${zl(k.koszt_rekrutacji)}</p>
    <div class="dwie"><label class="pole">Wynagrodzenie brutto (miesięcznie)
      <input type="number" id="z-pensja" min="${minimum(kat, "prace", k.student)}" step="10" value="${oczekiwana(kat, k, "prace")}"></label>
    <label class="pole">Forma zatrudnienia<select id="z-umowa" data-zmiana="forma-zatrudnienia" data-k="${esc(id)}" data-pensja="z-pensja"
      data-opis="z-opis-formy">${opcjeForm(v, kat, k, "prace")}</select></label></div>
    <p class="podpowiedz" id="z-opis-formy">${opisFormy(kat, "prace", k)}</p>${typ ? "" : wyborMiejsca(v, kat, k.zawod)}${kanalyRekrutacji(v, k)}
    <p class="podpowiedz">Pensja wyższa od oczekiwanej i umowa o pracę podnoszą zadowolenie pracowników.</p>`,
    { srednie: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="potwierdz-zatrudnienie" data-k="${esc(id)}"${typ ? ` data-t="${typ}" data-n="${nr}"` : ""}>Potwierdź</button>` });
}

// UF20: kandydaci w Rynku pracy – zatrudnienie od razu z lokalem i stanowiskiem; niżej zatrudnienia czekające w tej rundzie
export function kandydaciRynku({ v, kat, edycja }) {
  const typy = kat.oferty.stanowiska.typy;
  const czekaja = v.stan.pracownicy.filter((p) => p.od_rundy === v.runda && (v.decyzje.zatrudnij || []).some((z) => z.kandydat === p.id));
  const gdzie = (p) => {
    const s = v.stan.stanowiska.find((x) => x.pracownik === p.id);
    return s ? `${v.lokale ? `${esc(nazwaLokalu(v, s.lokal))} · ` : ""}${esc(typy[s.typ]?.nazwa ?? s.typ)} nr ${s.nr}` : "–";
  };
  const lista = [...v.kandydaci].sort((a, b) => a.zawod.localeCompare(b.zawod) || b.zadowolenie_klientow - a.zadowolenie_klientow);
  const w = lista.map((k) => [esc(k.imie_nazwisko) + pigulkaStudenta(k) + pigulkaOfert(v, "kandydaci", k.id) + opisOsoby(k), esc(k.zawod), gw(k.gwiazdki), zl(k.pensja_preferowana), zl(k.koszt_rekrutacji),
    proc(k.zadowolenie_klientow, 0), proc(k.ryzyko_reklamacji, 0),
    `<button class="btn pom maly" data-akcja="zatrudnij" data-k="${esc(k.id)}" ${edycja ? "" : "disabled"}>Zatrudnij +</button>`]);
  return tabela("Kandydaci", ["Imię i nazwisko", "Zawód", "Doświadczenie", "Preferowane wynagrodzenie", "Bazowy koszt rekrutacji",
    "Zadowolenie klientów", "Ryzyko reklamacji", ""], w.length ? w : [["Na rynku nie ma teraz kandydatów.", "", "", "", "", "", "", ""]], { klasy: ["l", "l"] })
    + `<p class="podpowiedz">Przy zatrudnieniu wybierasz lokal i wolne stanowisko (${TYPY.map((t) => `${esc(typy[t].kto)}: ${typy[t].zawody.map(esc).join(", ")}`).join(" · ")}).
      Obsadę zmienisz potem w zakładce <a data-zakladka-k="lokal_przeglad">Mój lokal</a>.</p>`
    + (czekaja.length ? tabela("Zatrudnienia w tej rundzie", ["Osoba", "Zawód", "Lokal i stanowisko", "Pensja", "Umowa", ""],
      czekaja.map((p) => [esc(p.imie_nazwisko) + pigulkaStudenta(p), `${esc(p.zawod)} ${gw(p.gwiazdki)}`, gdzie(p), zl(p.pensja), nazwaFormy(kat, p.umowa),
        `<button class="btn jasny maly" data-akcja="profil" data-id="${esc(p.id)}" ${edycja ? "" : "disabled"}>Zmień</button>
         <button class="btn czarny maly" data-akcja="zwolnij" data-id="${esc(p.id)}" data-nowy="1" ${edycja ? "" : "disabled"}>Anuluj</button>`]),
      { klasy: ["l", "l", "l"] }) : "");
}

// UF20: szansa zgody na przejście – jak silnik/ludzie/przenosiny.py: szansa (parametry i odległości z v.agencja.przenosiny)
function szansaPrzejscia(v, p, z, doLokalu, dodatek) {
  const P = v.agencja?.przenosiny, u = P?.zasady;
  if (!u) return 1;
  const zad = p.zadowolenie ?? P.prog, odl = P.odleglosci?.[z]?.[doLokalu] ?? 0;
  const x = u.baza + u.za_zadowolenie * (zad - P.prog) - u.kara_za_pole * odl
    + u.za_dodatek * (p.pensja > 0 ? Math.min(1, Math.max(0, dodatek) / p.pensja) : 0);
  return Math.min(u.szansa_maks, Math.max(u.szansa_min, x));
}
// stanowisko osoby przed decyzjami (z niego liczy się przejście) i stanowisko docelowe
const stanowiskoPrzed = (v, id) => (v.stan_przed || v.stan).stanowiska.find((s) => s.pracownik === id);
const stanowiskoNr = (v, typ, nr) => v.stan.stanowiska.find((s) => s.typ === typ && s.nr === nr);
function przenosinyMiedzyLokalami(v, x) {
  const skad = stanowiskoPrzed(v, x.pracownik), cel = stanowiskoNr(v, x.typ, x.nr);
  return !!(skad && cel && skad.lokal !== cel.lokal);
}
function zapiszPrzenosiny(c, x) {
  zamknijOkno();
  return c.zmien((d) => {
    d.przenosiny = [...(d.przenosiny || []).filter((y) => y.pracownik !== x.pracownik && !(y.typ === x.typ && y.nr === x.nr)), x];
  });
}

function oknoPrzypisania({ v, kat }, typ, nr) {
  const cel = stanowiskoNr(v, typ, nr), T = kat.oferty.stanowiska.typy;
  const osoby = v.stan.pracownicy.filter((p) => p.od_rundy !== v.runda && typyZawodu(kat, p.zawod).includes(typ));
  const w = osoby.map((p) => {
    const teraz = v.stan.stanowiska.find((s) => s.pracownik === p.id), skad = stanowiskoPrzed(v, p.id) || teraz;
    const inny = !!(skad && cel && skad.lokal !== cel.lokal);
    const przycisk = inny && p.odchodzi ? `<span class="podpowiedz">w okresie wypowiedzenia</span>`
      : `<button class="btn pom maly" data-akcja="wybierz-osobe" data-id="${esc(p.id)}" data-t="${typ}" data-n="${nr}" data-inny="${inny ? 1 : 0}">Przypisz</button>`;
    return [esc(p.imie_nazwisko) + opisOsoby(p), `${esc(p.zawod)} ${gw(p.gwiazdki)}`,
      teraz ? `${v.lokale ? `${esc(nazwaLokalu(v, teraz.lokal))} · ` : ""}${esc(T[teraz.typ]?.nazwa ?? teraz.typ)} nr ${teraz.nr}` : `<span class="minus">bez stanowiska</span>`,
      zadowolenieOsoby(p), inny ? `ok. ${proc(szansaPrzejscia(v, p, skad?.lokal, cel?.lokal, 0), 0)} bez dodatku` : "od razu", przycisk];
  });
  okno(`Obsada: ${esc(T[typ]?.nazwa ?? typ)} nr ${nr}${cel?.lokal && v.lokale ? ` – ${esc(nazwaLokalu(v, cel.lokal))}` : ""}`,
    (w.length ? tabela(null, ["Osoba", "Zawód", "Pracuje teraz", "Zadowolenie", "Zgoda", ""], w, { klasy: ["l", "l", "l"] })
      : `<div class="komunikat">Nie masz jeszcze nikogo do tej pracy.</div>`)
    + `<p class="podpowiedz">Osoba z tego lokalu zmieni stanowisko od razu. Osoba z innego lokalu musi się zgodzić: chętniej, gdy jest zadowolona,
      lokale są blisko na mapie i dostanie jednorazowy dodatek. Odpowiedź poznasz po przeliczeniu rundy (Rynek pracy ▸ wyniki).
      Nowa osoba: <a data-zakladka-k="rynek_pracy">Rynek pracy</a>.</p>`, { srednie: true });
}

function oknoPrzenosin({ v }, id, typ, nr) {
  const p = v.stan.pracownicy.find((x) => x.id === id), skad = stanowiskoPrzed(v, id), cel = stanowiskoNr(v, typ, nr);
  const odl = v.agencja?.przenosiny?.odleglosci?.[skad?.lokal]?.[cel?.lokal];
  const progi = [0, 0.25, 0.5, 1].map((u) => Math.round(p.pensja * u / 10) * 10);
  okno(`Przeniesienie: ${esc(p.imie_nazwisko)}`, `<p>Z lokalu <b>${esc(nazwaLokalu(v, skad?.lokal))}</b> do <b>${esc(nazwaLokalu(v, cel?.lokal))}</b>
      (stanowisko nr ${nr})${odl != null ? ` · odległość na mapie ok. ${licz(odl, 1)} pola` : ""} · zadowolenie ${zadowolenieOsoby(p)}</p>
    ${tabela("Szansa zgody", ["Dodatek", "Szansa"], progi.map((x) => [zl(x), proc(szansaPrzejscia(v, p, skad?.lokal, cel?.lokal, x), 0)]), {})}
    <label class="pole">Jednorazowy dodatek za przejście (zł, płacisz tylko po zgodzie)
      <input type="number" id="pz-dodatek" min="0" step="50" value="0"></label>
    <p class="podpowiedz">Jeśli pracownik się nie zgodzi, zostaje na swoim stanowisku. Wolne miejsce po nim możesz od razu obsadzić kimś innym.</p>`,
  { srednie: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="potwierdz-przenosiny" data-id="${esc(id)}" data-t="${typ}" data-n="${nr}">Zaproponuj</button>` });
}

function oknoProfilu({ v, kat, edycja }, id) {
  const p = v.stan.pracownicy.find((x) => x.id === id);
  const nowy = p.od_rundy === v.runda;
  const pole = (etykieta, html) => `<label class="pole">${etykieta}${html}</label>`;
  okno("Profil pracownika", `<div class="dwie"><div class="srodek"><div class="awatar">${inicjaly(p.imie_nazwisko)}</div>${gw(p.gwiazdki)}
      <h3 style="margin:6px 0">${esc(p.imie_nazwisko)}</h3><div class="podpowiedz">${esc(p.zawod)}</div>
      ${p.opis ? `<div class="podpowiedz" style="margin-top:6px"><i>„${esc(p.opis)}”</i></div>` : ""}
      <div style="margin-top:14px;text-align:left">
      <div class="wiersz"><span>Preferowane wynagrodzenie</span><span>${zl(p.pensja_preferowana)}</span></div>
      <div class="wiersz"><span>Koszty rekrutacji</span><span>${zl(p.koszt_rekrutacji)}</span></div>
      <div class="wiersz"><span>Koszt odprawy</span><span>${zl(p.koszt_odprawy)}</span></div>
      <div class="wiersz"><span>Zatrudniony od</span><span>runda ${p.od_rundy}</span></div>
      <div class="wiersz"><span>Ryzyko reklamacji</span><span>${proc(p.ryzyko_reklamacji, 0)}</span></div>
      <div class="wiersz"><span>Zadowolenie klientów</span><span>${proc(p.zadowolenie_klientow, 0)}</span></div>
      <div class="wiersz"><span>Zadowolenie z pracy (ostatni tydzień)</span><span>${zadowolenieOsoby(p)}</span></div></div>
      ${p.niezadowolony && !p.odchodzi ? `<p class="minus" style="text-align:left">Niezadowolony od ${p.niezadowolony} tyg. – szczegóły na liście błędów.
        Pomaga podwyżka, lepszy sprzęt albo odciążenie.</p>` : ""}</div>
    <div style="display:flex;flex-direction:column;gap:12px">
      ${pole("Aktualne wynagrodzenie brutto", `<input type="number" id="p-pensja" step="10" value="${p.pensja}" ${edycja && !forma(kat, p.umowa).staz ? "" : "disabled"}>`)}
      ${nowy ? "" : pole("Premia (jednorazowo w tej rundzie)", `<input type="number" id="p-premia" step="50" value="${p.premia || 0}" ${edycja ? "" : "disabled"}>`)}
      ${pole("Forma zatrudnienia", `<select id="p-umowa" data-zmiana="forma-zatrudnienia" data-k="${esc(id)}" data-pensja="p-pensja" data-opis="p-opis-formy"
        ${edycja ? "" : "disabled"}>${opcjeForm(v, kat, p, p.umowa, { nowy })}</select>`)}
      <span class="podpowiedz" id="p-opis-formy">${opisFormy(kat, p.umowa, p)}${forma(kat, p.umowa).staz ? ` Staż do rundy ${p.od_rundy + forma(kat, p.umowa).staz.rund}.` : ""}</span>
      ${(v.decyzje.zwolnij || []).includes(id)
    ? `<button class="btn jasny" data-akcja="cofnij-zwolnienie" data-id="${esc(id)}" ${edycja ? "" : "disabled"}>Cofnij zwolnienie</button>
       <span class="podpowiedz">${forma(kat, p.umowa).wypowiedzenie ? `${nazwaFormy(kat, p.umowa)}: przez okres wypowiedzenia jeszcze pracuje i dostaje pensję.` : `${nazwaFormy(kat, p.umowa)}: odchodzi od razu.`}</span>`
    : p.odchodzi ? `<span class="minus">${p.odchodzi.powod === NIEZADOWOLENIE ? "Złożył(a) wypowiedzenie z niezadowolenia" : "W okresie wypowiedzenia"} – odchodzi w rundzie ${p.odchodzi.runda}.</span>`
      : `<button class="btn czarny" data-akcja="zwolnij" data-id="${esc(id)}" data-nowy="${nowy ? 1 : 0}" ${edycja ? "" : "disabled"}>${nowy ? "Anuluj zatrudnienie" : "Zwolnij"}</button>`}
    </div></div>`, { przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="zapisz-profil" data-id="${esc(id)}" data-nowy="${nowy ? 1 : 0}" ${edycja ? "" : "disabled"}>Zapisz</button>` });
}

// UF15: Ludzie → Zespół – wszyscy pracownicy firmy w jednej tabeli (kliknięcie – profil: pensja, premia, zwolnienie)
export const zespol = {
  tytul: "Zespół", tytulPelny: "Ludzie – zespół", ikona: "zatrudnienie", odblokowanie: "hr_zatrudnienie",
  info: "Wszyscy Twoi pracownicy: gdzie pracują, na jakiej umowie, za ile i czy są zadowoleni. Kliknij osobę, żeby zmienić pensję, dać premię albo zwolnić.",
  decyzje({ v, kat }) {
    const P = v.stan.pracownicy;
    if (!P.length) return `<div class="komunikat">Nie masz jeszcze pracowników – znajdź ich w zakładce <a data-zakladka-k="rynek_pracy">Rynek pracy</a>.</div>`;
    const st = (p) => v.stan.stanowiska.find((s) => s.pracownik === p.id);
    const w = P.map((p) => {
      const s = st(p);
      const gdzie = s ? `${v.lokale ? `${esc(nazwaLokalu(v, s.lokal))} · ` : ""}${esc(kat.oferty.stanowiska.typy[s.typ]?.nazwa ?? s.typ)} nr ${s.nr}` : `<span class="minus">bez stanowiska</span>`;
      const stanOsoby = p.odchodzi ? `<span class="pigulka${p.odchodzi.powod === NIEZADOWOLENIE ? " nie" : ""}">odchodzi w r. ${p.odchodzi.runda}</span>`
        : p.od_rundy === v.runda ? `<span class="pigulka inf">nowy</span>` : p.niezadowolony ? `<span class="pigulka nie">niezadowolony</span>` : "";
      return [`<a data-akcja="profil" data-id="${esc(p.id)}">${esc(p.imie_nazwisko)}</a> ${stanOsoby}${p.odchodzi ? "" : pigulkaPodkupienia(v, p)}`, esc(p.zawod), gw(p.gwiazdki), gdzie,
        nazwaFormy(kat, p.umowa) + pigulkaStudenta(p), zl(p.pensja), p.premia ? zl(p.premia) : "–", zadowolenieOsoby(p)];
    });
    return `<div class="pasek ciemny"><span>Pracownicy: <span class="kwota">${licz(P.length)}</span></span>
      <span>Koszty wynagrodzeń: <span class="kwota">${zl(kosztWynagrodzen(v, kat), true)}</span>${naOkres()} (z ZUS pracodawcy)</span></div>`
      + tabela(null, ["Osoba", "Zawód", "Poziom", "Gdzie pracuje", "Umowa", "Pensja (mies.)", "Premia", "Zadowolenie"], w, { klasy: ["l", "l", "", "l", "l"] });
  },
  wyniki: (c) => zatrudnienie.wyniki(c),
};

export const udogodnienia = {
  tytul: "Udogodnienia", tytulPelny: "HR - udogodnienia", ikona: "♨", odblokowanie: "hr_udogodnienia",
  info: "Kup udogodnienia dla pracowników Twojej firmy. Podnoszą zadowolenie pracowników.",
  decyzje(c) { return wyborLokaluKrotki(c.v) + kafleUdogodnien(c, "udogodnienia", "pracowników"); },
  wyniki({ v }) {
    const w = Object.entries(v.rynek?.udogodnienia || {}).map(([f, n]) => [esc(nazwaFirmy(v, f)), licz(n)]);
    const moje = v.rynek?.udogodnienia?.[v.firma];
    return podsumowanie(moje ? `Twoja firma ma <b>${licz(moje)}</b> ${moje === 1 ? "udogodnienie" : "udogodnień"} dla pracowników.` : "Twoja firma nie ma jeszcze udogodnień dla pracowników.", moje ? "ok" : "")
      + zwinTabela("Posiadane udogodnienia", ["Firma", "Liczba udogodnień"], w, { klasy: ["l"], otwarte: true });
  },
  akcje: {},
};

export const szkolenia = {
  tytul: "Szkolenia", tytulPelny: "HR - szkolenia", ikona: "✎", odblokowanie: "hr_szkolenia",
  info: () => `Zapewnij swoim pracownikom możliwości rozwoju i zaoferuj im udział w szkoleniach (szkolenie obejmuje wszystkich pracowników, działa w tym ${OKRES.miejscownik}).`,
  decyzje({ v, kat, edycja }) {
    const s = kat.oferty.szkolenia, wyb = v.decyzje.szkolenia || [];
    const koszt = wyb.reduce((a, x) => { const p = s.pozycje.find((q) => q.nazwa === x.szkolenie); const i = s.firmy.findIndex((f) => f.nazwa === x.firma); return a + (p && i >= 0 ? naRunde(p.ceny[i]) : 0); }, 0);
    const w = s.pozycje.map((p) => [esc(p.nazwa), `${p.procent}%`, ...s.firmy.map((f, i) => {
      const jest = wyb.some((x) => x.szkolenie === p.nazwa && x.firma === f.nazwa);
      return `${zl(naRunde(p.ceny[i]))}<br><button class="btn ${jest ? "zielony" : "jasny"} maly" data-akcja="szkolenie" data-s="${esc(p.nazwa)}" data-f="${esc(f.nazwa)}" ${edycja ? "" : "disabled"}>${jest ? "✓ Wybrano" : "Wybierz"}</button>`;
    })]);
    return `<div class="pasek ciemny"><span>Koszt zakupu: <span class="kwota">${zl(koszt)}</span>${naOkres()}</span></div>`
      + tabela(null, ["Szkolenie", "% pracowników oczekujących", ...s.firmy.map((f) => `${esc(f.nazwa)}<br><span class="podpowiedz">${f.zadowoleni_klienci}% zadowolonych klientów</span>`)], w, { klasy: ["l"] });
  },
  wyniki({ v }) {
    const l = v.wyniki?.szkolenia || [], k = v.wyniki?.karta;
    const w = l.map((x) => [esc(x.szkolenie), esc(x.firma), `${x.procent}%`, zl(x.koszt)]);
    const razem = l.reduce((a, x) => a + x.koszt, 0), pr = l.reduce((a, x) => a + x.procent, 0);
    const lead = podsumowanie(w.length ? `Szkolenia w tej rundzie: <b>${licz(w.length)}</b>, koszt <b>${zl(razem)}</b>.` : "W tej rundzie nie było szkoleń.");
    return lead + (w.length ? zwinTabela("Szkolenia w tej rundzie", ["Szkolenie", "Firma szkoleniowa", "% pracowników oczekujących", "Koszt"],
      [...w, ["<b>Razem</b>", "", `<b>${pr}%</b>`, `<b>${zl(razem)}</b>`]], { klasy: ["l", "l"], otwarte: true })
      : "")
      + (k ? zwinTabela("Efekt", ["Zadowolenie pracowników (karta wyników)"], [[licz(k.zadowolenie_pracownikow, 3)]]) : "");
  },
  akcje: {
    szkolenie: (el, c) => c.zmien((d) => {
      const l = d.szkolenia || [], s = el.dataset.s, f = el.dataset.f;
      const jest = l.some((x) => x.szkolenie === s && x.firma === f);
      d.szkolenia = jest ? l.filter((x) => !(x.szkolenie === s && x.firma === f)) : [...l.filter((x) => x.szkolenie !== s), { firma: f, szkolenie: s }];
    }),
    "kup-udog": (el, c) => przelaczUdog(el, c), "sprzedaj-udog": (el, c) => przelaczUdog(el, c),
  },
};

export { wykres };
