// HR: zatrudnienie, udogodnienia, szkolenia.
import { esc, gw, inicjaly, licz, nazwaFirmy, okno, proc, tabela, toast, wykres, zamknijOkno, zl } from "./wspolne.js";
import { kafleUdogodnien, przelaczUdog } from "./inwestycje.js";

const TYPY = ["kuchnia", "kasa"];  // nazwy i zawody typów: kat.oferty.stanowiska.typy (katalog.yaml)
const UMOWY = { prace: "Umowa o pracę", zlecenie: "Umowa zlecenie" };

function kosztWynagrodzen(v, kat) {
  return v.stan.pracownicy.reduce((s, p) => s + (p.pensja + (p.premia || 0)) * (p.umowa === "prace" ? 1 + kat.parametry.zus : 1), 0);
}

export const zatrudnienie = {
  tytul: "Zatrudnienie", tytulPelny: "HR - zatrudnienie", ikona: "☺", odblokowanie: "hr_zatrudnienie",
  info: "Zatrudnij pracowników potrzebnych do przygotowania i sprzedaży wybranych dań. Pracownik potrzebuje stanowiska (Inwestycje → Stanowiska).",
  decyzje({ v, kat, edycja }) {
    let html = `<div class="pasek ciemny"><span>Koszty wynagrodzeń: <span class="kwota">${zl(kosztWynagrodzen(v, kat), true)}</span> brutto (z ZUS pracodawcy)</span></div>`;
    if (v.nieudane_zatrudnienia?.length) html += `<div class="komunikat zly">Część kandydatów zatrudniła już inna firma – wybierz innych.</div>`;
    for (const typ of TYPY) {
      const st = v.stan.stanowiska.filter((s) => s.typ === typ);
      html += `<div class="pasek">${esc(kat.oferty.stanowiska.typy[typ].nazwa)}</div>`;
      if (!st.length) { html += `<p class="podpowiedz">Brak stanowisk – uruchom je w zakładce Inwestycje → Stanowiska.</p>`; continue; }
      html += `<div class="siatka waska">${st.map((s) => {
        const p = v.stan.pracownicy.find((x) => x.id === s.pracownik);
        if (!p) return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}</div><div class="kt srodek"><div class="awatar pusty">+</div>
          <button class="btn jasny" data-akcja="kandydaci" data-t="${typ}" data-n="${s.nr}" ${edycja ? "" : "disabled"}>Zatrudnij pracownika →</button></div></div>`;
        const nowy = p.od_rundy === v.runda;
        return `<div class="kafel"><div class="kg">Stanowisko nr ${s.nr}${nowy ? '<span class="pigulka inf">nowy</span>' : ""}</div>
          <div class="kt srodek" data-akcja="profil" data-id="${esc(p.id)}" style="cursor:pointer"><div class="awatar">${inicjaly(p.imie_nazwisko)}</div>
          <b>${esc(p.imie_nazwisko)}</b><br><span class="podpowiedz">${esc(p.zawod)} · ${UMOWY[p.umowa]}</span><br>${gw(p.gwiazdki)}<br>
          <b class="akcent">${zl(p.pensja)}</b>${p.premia ? `<br><span class="podpowiedz">premia ${zl(p.premia)}</span>` : ""}</div></div>`;
      }).join("")}</div>`;
    }
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
    const moi = (v.wyniki?.pracownicy || []).map((p) => [esc(p.imie_nazwisko), esc(p.zawod), gw(p.gwiazdki), `nr ${p.stanowisko}`, proc(p.wykorzystanie), zl(p.pensja)]);
    return tabela("Liczba pracowników", ["Zespół", ...ZAWODY], liczba, { klasy: ["l"] })
      + tabela("Wykorzystanie czasu pracowników", ["Zespół", ...ZAWODY], wyk, { klasy: ["l"] })
      + tabela("Średnie wynagrodzenie pracowników", ["Zespół", ...ZAWODY], pensje, { klasy: ["l"] })
      + tabela("Twoi pracownicy", ["Pracownik", "Zawód", "Doświadczenie", "Stanowisko", "Wykorzystanie czasu", "Wynagrodzenie"], moi, { klasy: ["l"] })
      + `<p class="podpowiedz">Wykorzystanie 100% oznacza, że pracownik nie miał czasu na kolejnych klientów (możliwa utracona sprzedaż).</p>`;
  },
  akcje: {
    kandydaci: (el, c) => oknoKandydatow(c, el.dataset.t, +el.dataset.n),
    zatrudnij: (el, c) => oknoZatrudnienia(c, el.dataset.k, el.dataset.t, +el.dataset.n),
    "potwierdz-zatrudnienie": async (el, c) => {
      const pensja = +document.getElementById("z-pensja").value, umowa = document.getElementById("z-umowa").value;
      if (pensja < c.kat.placa_minimalna) return toast(`Pensja nie może być niższa niż ${c.kat.placa_minimalna} PLN.`);
      const { k, t, n } = el.dataset;
      zamknijOkno();
      await c.zmien((d) => { d.zatrudnij = [...(d.zatrudnij || []).filter((z) => !(z.typ === t && z.nr === +n)), { kandydat: k, typ: t, nr: +n, pensja, umowa }]; });
    },
    profil: (el, c) => oknoProfilu(c, el.dataset.id),
    "zapisz-profil": async (el, c) => {
      const id = el.dataset.id, nowy = el.dataset.nowy === "1";
      const pensja = +document.getElementById("p-pensja").value, umowa = document.getElementById("p-umowa").value;
      const premia = +(document.getElementById("p-premia")?.value || 0);
      if (pensja < c.kat.placa_minimalna) return toast(`Pensja nie może być niższa niż ${c.kat.placa_minimalna} PLN.`);
      zamknijOkno();
      await c.zmien((d) => {
        if (nowy) d.zatrudnij = (d.zatrudnij || []).map((z) => z.kandydat === id ? { ...z, pensja, umowa } : z);
        else d.zmiany = { ...(d.zmiany || {}), [id]: { pensja, umowa, premia } };
      });
    },
    zwolnij: async (el, c) => {
      const id = el.dataset.id, nowy = el.dataset.nowy === "1";
      if (!nowy && !confirm("Zwolnić pracownika? Trzeba zapłacić odprawę.")) return;
      zamknijOkno();
      await c.zmien((d) => {
        if (nowy) d.zatrudnij = (d.zatrudnij || []).filter((z) => z.kandydat !== id);
        else d.zwolnij = [...new Set([...(d.zwolnij || []), id])];
      });
    },
  },
};

function oknoKandydatow({ v, kat }, typ, nr) {
  const typy = kat.oferty.stanowiska.typy, zawody = typy[typ].zawody;
  const lista = v.kandydaci.filter((k) => zawody.includes(k.zawod)).sort((a, b) => b.zadowolenie_klientow - a.zadowolenie_klientow);
  const w = lista.map((k) => [esc(k.imie_nazwisko), gw(k.gwiazdki), esc(k.zawod), licz(k.pensja_preferowana), licz(k.koszt_rekrutacji),
    licz(k.koszt_odprawy), proc(k.zadowolenie_klientow, 0), proc(k.ryzyko_reklamacji, 0),
    `<button class="btn pom maly" data-akcja="zatrudnij" data-k="${esc(k.id)}" data-t="${typ}" data-n="${nr}">Zatrudnij +</button>`]);
  okno(`Zatrudnienie na „Stanowisko nr ${nr}”`, tabela(null, ["Imię i nazwisko", "Doświadczenie", "Zawód", "Preferowane wynagrodzenie",
    "Koszty rekrutacji", "Koszt odprawy", "Zadowolenie klientów", "Ryzyko reklamacji", "Akcje"], w, { klasy: ["l"] })
    + `<p class="podpowiedz">${TYPY.map((t) => `${esc(typy[t].kto)}: ${typy[t].zawody.map(esc).join(", ")}`).join(" · ")}</p>`);
}

function oknoZatrudnienia({ v, kat }, id, typ, nr) {
  const k = v.kandydaci.find((x) => x.id === id);
  okno(`Zatrudnienie: ${esc(k.imie_nazwisko)}`, `<p>${esc(k.zawod)} ${gw(k.gwiazdki)} · preferowane wynagrodzenie <b>${zl(k.pensja_preferowana)}</b>
      · koszt rekrutacji ${zl(k.koszt_rekrutacji)}</p>
    <div class="dwie"><label class="pole">Wynagrodzenie brutto (min. ${licz(kat.placa_minimalna)} PLN)
      <input type="number" id="z-pensja" min="${kat.placa_minimalna}" step="10" value="${k.pensja_preferowana}"></label>
    <label class="pole">Forma zatrudnienia<select id="z-umowa"><option value="prace">Umowa o pracę (+${proc(kat.parametry.zus, 0)} ZUS pracodawcy)</option>
      <option value="zlecenie">Umowa zlecenie</option></select></label></div>
    <p class="podpowiedz">Pensja wyższa od preferowanej i umowa o pracę podnoszą zadowolenie pracowników.</p>`,
    { male: true, przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="potwierdz-zatrudnienie" data-k="${esc(id)}" data-t="${typ}" data-n="${nr}">Potwierdź</button>` });
}

function oknoProfilu({ v, kat, edycja }, id) {
  const p = v.stan.pracownicy.find((x) => x.id === id);
  const nowy = p.od_rundy === v.runda;
  const pole = (etykieta, html) => `<label class="pole">${etykieta}${html}</label>`;
  okno("Profil pracownika", `<div class="dwie"><div class="srodek"><div class="awatar">${inicjaly(p.imie_nazwisko)}</div>${gw(p.gwiazdki)}
      <h3 style="margin:6px 0">${esc(p.imie_nazwisko)}</h3><div class="podpowiedz">${esc(p.zawod)}</div>
      <div style="margin-top:14px;text-align:left">
      <div class="wiersz"><span>Preferowane wynagrodzenie</span><span>${zl(p.pensja_preferowana)}</span></div>
      <div class="wiersz"><span>Koszty rekrutacji</span><span>${zl(p.koszt_rekrutacji)}</span></div>
      <div class="wiersz"><span>Koszt odprawy</span><span>${zl(p.koszt_odprawy)}</span></div>
      <div class="wiersz"><span>Zatrudniony od</span><span>runda ${p.od_rundy}</span></div>
      <div class="wiersz"><span>Ryzyko reklamacji</span><span>${proc(p.ryzyko_reklamacji, 0)}</span></div>
      <div class="wiersz"><span>Zadowolenie klientów</span><span>${proc(p.zadowolenie_klientow, 0)}</span></div></div></div>
    <div style="display:flex;flex-direction:column;gap:12px">
      ${pole("Aktualne wynagrodzenie brutto", `<input type="number" id="p-pensja" step="10" value="${p.pensja}" ${edycja ? "" : "disabled"}>`)}
      ${nowy ? "" : pole("Premia (jednorazowo w tej rundzie)", `<input type="number" id="p-premia" step="50" value="${p.premia || 0}" ${edycja ? "" : "disabled"}>`)}
      ${pole("Forma zatrudnienia", `<select id="p-umowa" ${edycja ? "" : "disabled"}>${Object.entries(UMOWY).map(([k, n]) => `<option value="${k}" ${p.umowa === k ? "selected" : ""}>${n}</option>`).join("")}</select>`)}
      <button class="btn czarny" data-akcja="zwolnij" data-id="${esc(id)}" data-nowy="${nowy ? 1 : 0}" ${edycja ? "" : "disabled"}>${nowy ? "Anuluj zatrudnienie" : "Zwolnij"}</button>
    </div></div>`, { przyciski: `<button class="btn jasny" data-akcja="zamknij-okno">Anuluj</button>
      <button class="btn pom" data-akcja="zapisz-profil" data-id="${esc(id)}" data-nowy="${nowy ? 1 : 0}" ${edycja ? "" : "disabled"}>Zapisz</button>` });
}

export const udogodnienia = {
  tytul: "Udogodnienia", tytulPelny: "HR - udogodnienia", ikona: "♨", odblokowanie: "hr_udogodnienia",
  info: "Kup udogodnienia dla pracowników Twojej firmy. Podnoszą zadowolenie pracowników.",
  decyzje(c) { return kafleUdogodnien(c, "udogodnienia", "pracowników"); },
  wyniki({ v }) {
    const w = Object.entries(v.rynek?.udogodnienia || {}).map(([f, n]) => [esc(nazwaFirmy(v, f)), licz(n)]);
    return tabela("Posiadane udogodnienia", ["Firma", "Liczba udogodnień"], w, { klasy: ["l"] });
  },
  akcje: {},
};

export const szkolenia = {
  tytul: "Szkolenia", tytulPelny: "HR - szkolenia", ikona: "✎", odblokowanie: "hr_szkolenia",
  info: "Zapewnij swoim pracownikom możliwości rozwoju i zaoferuj im udział w szkoleniach (szkolenie obejmuje wszystkich pracowników, działa w tym miesiącu).",
  decyzje({ v, kat, edycja }) {
    const s = kat.oferty.szkolenia, wyb = v.decyzje.szkolenia || [];
    const koszt = wyb.reduce((a, x) => { const p = s.pozycje.find((q) => q.nazwa === x.szkolenie); const i = s.firmy.findIndex((f) => f.nazwa === x.firma); return a + (p && i >= 0 ? p.ceny[i] : 0); }, 0);
    const w = s.pozycje.map((p) => [esc(p.nazwa), `${p.procent}%`, ...s.firmy.map((f, i) => {
      const jest = wyb.some((x) => x.szkolenie === p.nazwa && x.firma === f.nazwa);
      return `${zl(p.ceny[i])}<br><button class="btn ${jest ? "zielony" : "jasny"} maly" data-akcja="szkolenie" data-s="${esc(p.nazwa)}" data-f="${esc(f.nazwa)}" ${edycja ? "" : "disabled"}>${jest ? "✓ Wybrano" : "Wybierz"}</button>`;
    })]);
    return `<div class="pasek ciemny"><span>Koszt zakupu: <span class="kwota">${zl(koszt)}</span></span></div>`
      + tabela(null, ["Szkolenie", "% pracowników oczekujących", ...s.firmy.map((f) => `${esc(f.nazwa)}<br><span class="podpowiedz">${f.zadowoleni_klienci}% zadowolonych klientów</span>`)], w, { klasy: ["l"] });
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
