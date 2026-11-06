// Zakładka „Lokale” (Z3, przebudowa 2.11.2026, raporty/przebudowa_zakladek.md): kafelki lokali na górze i pięć
// podzakładek – Przegląd, Menu i ceny, Dostawy i magazyn, Ludzie, Sprzęt. Podzakładka (poza Przeglądem) składa się
// z dawnych zakładek („części”), które działają na wybranym lokalu (lokal_wybor.js); dawne klucze zakładek prowadzą
// tu przez ALIAS (index.js), a część ma kotwicę #czesc-<klucz>.
import { esc, licz, naOkres, naRunde, proc, tabela, zl } from "./wspolne.js";
import { ikona } from "./ikony.js";
import { kolko } from "./dymki.js";
import { nazwaStrefy } from "./lokale.js";
import { akcjeWyboru, idWybranego, kafelkiLokali, lokalWybrany, menuLokalu, mojeLokale, nazwaLokalu, opisLokalu, wieleLokali }
  from "./lokal_wybor.js";

const dostepnaCzesc = (v, z) => !z.odblokowanie
  || (typeof z.odblokowanie === "function" ? z.odblokowanie(v) : v.odblokowane.includes(z.odblokowanie));
const maWynikiCzesci = (v, z) => !!(z.wyniki && v.wyniki && (!z.wynikiOd || v.runda >= z.wynikiOd) && (!z.wynikiGdy || z.wynikiGdy(v)));

// Podzakładka złożona z części {klucz: zakładka}; odRundy(v, klucz) – od której rundy część będzie dostępna.
export function zlozona({ tytul, tytulPelny, info, czesci, odRundy }) {
  const widoczne = (v) => Object.entries(czesci).filter(([, z]) => !z.ukryta?.(v));
  const sekcja = (c, k, z, tryb, tresc) => {
    const opis = typeof z.info === "function" ? z.info(c, tryb) : z.info;
    return `<section class="czesc" id="czesc-${k}"><div class="czesc-tytul">${ikona(k, 20)}<span>${z.tytulPelny || z.tytul}</span>${kolko(opis)}</div>
      ${tresc}</section>`;
  };
  const rysowane = (v, tryb) => widoczne(v).filter(([, z]) => dostepnaCzesc(v, z) && (tryb === "wyniki" ? maWynikiCzesci(v, z) : true));
  return {
    tytul, tytulPelny, info, czesci: Object.keys(czesci),
    odblokowanie: (v) => widoczne(v).some(([, z]) => dostepnaCzesc(v, z)),
    ukryta: (v) => !widoczne(v).length,
    decyzje(c) {
      // część tylkoWyniki (Sprzedaż – ceny są w kafelkach Menu) nie ma osobnego nagłówka w decyzjach
      return kafelkiLokali(c.v) + widoczne(c.v).filter(([, z]) => !z.tylkoWyniki).map(([k, z]) => {
        if (!dostepnaCzesc(c.v, z)) {
          const od = odRundy(c.v, k);
          return sekcja(c, k, z, "decyzje", `<p class="podpowiedz">${od ? `Dostępne od rundy ${od}.` : "Jeszcze niedostępne."}</p>`);
        }
        return sekcja(c, k, z, "decyzje", z.decyzje ? z.decyzje(c) : maWynikiCzesci(c.v, z) ? z.wyniki(c) : "");
      }).join("");
    },
    wyniki(c) {
      return kafelkiLokali(c.v) + rysowane(c.v, "wyniki").map(([k, z]) => sekcja(c, k, z, "wyniki", z.wyniki(c))).join("");
    },
    wynikiGdy: (v) => widoczne(v).some(([, z]) => dostepnaCzesc(v, z) && maWynikiCzesci(v, z)),
    po(c, tryb) {
      for (const [, z] of rysowane(c.v, tryb)) {
        if (!z.po) continue;
        try { z.po(c, tryb); } catch (e) { console.error(e); }
      }
    },
    akcje: akcjeWyboru,
  };
}

// --- Przegląd ---------------------------------------------------------------------------------------

const magazynLokalu = (v, id) => (id && v.swiezosc?.lokale?.[id]) || v.swiezosc || null;
const STATUS = (l, v) => (l.dziala_od <= v.runda ? `<span class="pigulka ok">działa</span>` : `<span class="pigulka inf">rusza w rundzie ${l.dziala_od}</span>`);

// pensje za rundę (miesięczne z ZUS pracodawcy przeliczone na rundę, premia za rundę bez ZUS) ludzi lokalu
function pensjeLokalu(v, kat, id) {
  const st = v.stan.stanowiska.filter((s) => !wieleLokali(v) || s.lokal === id);
  return st.reduce((suma, s) => {
    const p = v.stan.pracownicy.find((x) => x.id === s.pracownik);
    return suma + (p ? naRunde(p.pensja * (1 + (p.umowa === "prace" ? kat.parametry.zus : kat.parametry.zus_zlecenie || 0))) + (p.premia || 0) : 0);
  }, 0);
}
const kosztLokalu = (o) => (o ? (o.forma === "najem" ? naRunde(o.czynsz) : 0) + (o.dziala ? naRunde(o.utrzymanie) : 0) : 0);

function porownanie(v, kat) {
  const l = mojeLokale(v);
  if (l.length < 2) return "";
  const w = l.map((x) => {
    const o = opisLokalu(v, x.id) || {}, menu = menuLokalu(v, x), S = magazynLokalu(v, x.id);
    const st = (t) => `${licz(o.zajete?.[t] ?? 0)} / ${licz(o.miejsca?.[t] ?? 0)}`;
    const kl = (v.wyniki?.klienci?.lokale || []).find((k) => k.id === x.id);
    return [`<a data-akcja="wybierz-lokal" data-id="${esc(x.id)}">${esc(o.nazwa || x.id)}</a>`, esc(nazwaStrefy(kat, o.strefa)), STATUS(x, v),
      licz(Object.keys(menu).length), licz(Object.values(menu).reduce((s, p) => s + (+p || 0), 0)), st("kuchnia"), st("kasa"),
      S?.pojemnosc?.chlodnia != null ? `${licz(S.pojemnosc.chlodnia)} l` : "–", kl ? licz(kl.sprzedaz) : "–", zl(kosztLokalu(o))];
  });
  return tabela("Porównanie lokali", ["Lokal", "Strefa", "Status", "Dania", "Prognoza (porcje)", "Kuchnia (zajęte / miejsca)",
    "Kasa (zajęte / miejsca)", "Chłodnia", "Sprzedaż w poprz. rundzie", `Czynsz i media${naOkres()}`], w, { klasy: ["l", "l", "l"] });
}

function liczby(v, kat, id) {
  const o = opisLokalu(v, id) || {}, kl = (v.wyniki?.klienci?.lokale || []).find((k) => k.id === id) || (!wieleLokali(v) ? v.wyniki?.klienci?.lokale?.[0] : null);
  const S = magazynLokalu(v, wieleLokali(v) ? id : null);
  const lokal = kosztLokalu(o), pensje = pensjeLokalu(v, kat, id);
  const maxZaj = S?.zajetosc?.length ? Math.max(...S.zajetosc.map((z) => z.chlodnia || 0)) : null;
  const wklad = kl?.przychod != null ? kl.przychod - (kl.skladniki || 0) - lokal - pensje : null;
  const kafel = (etykieta, wartosc, opis = "", klasa = "") => `<div class="liczba ${klasa}"><span class="etykieta">${etykieta}</span><b>${wartosc}</b>${opis ? `<span class="podpowiedz">${opis}</span>` : ""}</div>`;
  return `<div class="liczby-lokalu">
    ${kafel("Klienci", kl ? licz(kl.popyt) : "–", "chcieli kupić w poprzedniej rundzie")}
    ${kafel("Obsłużeni", kl ? licz(kl.sprzedaz) : "–", kl?.popyt ? `${proc(kl.sprzedaz / kl.popyt, 0)} chętnych` : "")}
    ${kafel("Przychód", kl?.przychod != null ? zl(kl.przychod) : "–", "brutto, ceny po rabacie")}
    ${kafel("Składniki", kl?.skladniki != null ? zl(kl.skladniki) : "–", "zużyte w lokalu")}
    ${kafel("Czynsz i media", zl(lokal), "w tej rundzie")}
    ${kafel("Pensje", zl(pensje), "ludzie na stanowiskach lokalu, z ZUS")}
    ${kafel("Wkład lokalu", wklad != null ? zl(wklad) : "–", "przychód − składniki − lokal − pensje (bez VAT, podatków i reklamy)", wklad != null ? (wklad >= 0 ? "plus" : "minus") : "")}
    ${kafel("Chłodnia", S?.pojemnosc?.chlodnia != null ? `${licz(S.pojemnosc.chlodnia)} l` : "–", maxZaj != null ? `do ${licz(maxZaj)} l zajęte w tej rundzie` : "")}
    ${kafel("Obsada", `${licz((o.zajete?.kuchnia ?? 0) + (o.zajete?.kasa ?? 0))} / ${licz((o.miejsca?.kuchnia ?? 0) + (o.miejsca?.kasa ?? 0))}`, "stanowiska zajęte / miejsca")}
  </div>`;
}

// braki z listy błędów dotyczące części zakładki Lokale (przy kilku lokalach – tego lokalu albo całej firmy)
const KLUCZE_CZESCI = ["oferta", "sprzedaz", "dostawcy", "swiezosc", "zatrudnienie", "szkolenia", "udogodnienia", "stanowiska", "sprzet", "wyposazenie", "lokale"];
function braki(v, id) {
  const nazwy = mojeLokale(v).map((l) => nazwaLokalu(v, l.id));
  const moja = id ? nazwaLokalu(v, id) : null;
  const tego = (b) => {
    if (!id) return true;
    const cudzy = nazwy.find((n) => b.tekst.startsWith(`${n} – `));
    return !cudzy || cudzy === moja;
  };
  const kol = { czerwony: 0, pomaranczowy: 1, niebieski: 2 };
  const lista = v.lista_bledow.filter((b) => KLUCZE_CZESCI.includes(b.zakladka) && tego(b)).sort((a, b) => kol[a.poziom] - kol[b.poziom]);
  if (!v.edycja) return "";
  if (!lista.length) return `<div class="komunikat ok">Brak uwag do ${id ? "tego lokalu" : "lokalu"} na liście błędów.</div>`;
  return `<div class="tabela-tytul">Braki i uwagi${id ? ` – ${esc(moja)}` : ""}</div>` + lista.map((b) =>
    `<div class="blad ${b.poziom}"><span class="tx">${esc(id ? b.tekst.replace(`${moja} – `, "") : b.tekst)}</span>
     <button class="btn jasny maly" data-akcja="popraw" data-z="${esc(b.zakladka)}">Popraw</button></div>`).join("");
}

function umowa(v, kat, id) {
  const o = opisLokalu(v, id);
  if (!o) return "";
  const w = (a, b) => `<div class="wiersz"><span>${a}</span><span>${b}</span></div>`;
  return `<div class="kafel"><div class="kg">Umowa – ${esc(o.nazwa)}</div><div class="kt">
    ${w("Adres", esc(o.adres))}${w("Strefa", esc(nazwaStrefy(kat, o.strefa)))}
    ${w("Forma", o.forma === "najem" ? "najem" : "własność")}
    ${o.forma === "najem" ? w(`Czynsz${naOkres()}`, zl(naRunde(o.czynsz))) : ""}
    ${w(`Media${naOkres()}`, zl(naRunde(o.utrzymanie)))}
    ${o.wlasciciel ? w("Wynajmujący", esc(o.wlasciciel)) : ""}
    ${o.najem_do ? w("Najem do rundy", licz(o.najem_do)) : ""}
    ${w("Od rundy", licz(o.od_rundy))}${w("Działa od rundy", licz(o.dziala_od))}</div>
    <div class="kd"><a class="podpowiedz" data-zakladka-k="lokale">Najem, kupno i nowe lokale – Inwestycje → Lokale</a></div></div>`;
}

function sanepid(v) {
  const M = v.magazyn, sp = v.wyniki?.magazyn?.sanepid;
  if (!M && !sp) return "";
  const w = (a, b) => `<div class="wiersz"><span>${a}</span><span>${b}</span></div>`;
  const ost = !sp ? "–" : !sp.kontrola ? "nie było kontroli" : sp.mandat ? `<span class="minus">mandat ${zl(sp.mandat)}</span>` : "bez zastrzeżeń";
  return `<div class="kafel"><div class="kg">Sanepid (cała firma)</div><div class="kt">
    ${M ? w("Szansa kontroli w tej rundzie", proc(M.szansa)) : ""}
    ${M ? w("Litry w wynajętej chłodni (plan)", licz(M.litry)) : ""}
    ${M ? w("Przeterminowane w poprzedniej rundzie", zl(M.przeterminowane)) : ""}
    ${w("Ostatnia kontrola", ost)}</div>
    <div class="kd"><a class="podpowiedz" data-zakladka-k="swiezosc">Szczegóły – Dostawy i magazyn</a></div></div>`;
}

export const lokal_przeglad = {
  tytul: "Przegląd", tytulPelny: "Lokale – przegląd", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Wszystko o wybranym lokalu w jednym miejscu: liczby z poprzedniej rundy, braki z listy błędów, umowa i sanepid.
    Przy kilku lokalach na górze jest też porównanie lokali. Decyzje ustawiasz w kolejnych podzakładkach.`,
  decyzje({ v, kat }) {
    const lok = lokalWybrany(v);
    if (!lok) return `<div class="komunikat">Nie masz jeszcze lokalu – wynajmij albo kup go w zakładce <a data-zakladka-k="lokale">Inwestycje → Lokale</a>.</div>`;
    const id = idWybranego(v);
    return kafelkiLokali(v) + porownanie(v, kat)
      + `<div class="tabela-tytul">${esc(nazwaLokalu(v, lok.id))} – liczby</div>` + liczby(v, kat, lok.id)
      + braki(v, id) + `<div class="dwie" style="margin-top:20px">${umowa(v, kat, lok.id)}${sanepid(v)}</div>`;
  },
  akcje: akcjeWyboru,
};
