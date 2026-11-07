// Urzędy: urząd i sanepid (gra z lokalami, silnik/ksiegowosc/urzad.py): rejestracja firmy, odbiór lokali przez sanepid i higiena.
// Decyzja `higiena: poziom` trwa do zmiany; poziom zmienia szansę i wynik kontroli sanepidu (silnik/kuchnia/magazyn.py).
import { brakWynikow, esc, kafelkiLiczb, naOkres, podsumowanie, proc, tabela, zl, zl2, zwinTabela } from "./wspolne.js";

const rund = (n) => `${n} ${n === 1 ? "rundę" : n < 5 ? "rundy" : "rund"}`;

function skutkiPoziomu(p) {
  const s = [];
  if (p.mnoznik !== 1) s.push(`szansa kontroli z problemów ×${String(p.mnoznik).replace(".", ",")}`);
  if (p.dodatek) s.push(`+${proc(p.dodatek, 0)} szansy kontroli`);
  if (p.mandat) s.push(`+${zl2(p.mandat)} do mandatu`);
  if (!p.odbior) s.push(`<span class="minus">sanepid nie odbierze lokalu</span>`);
  return s.join("<br>") || "–";
}

function odbioryHtml(O) {
  return (O || []).map((o) => `<div class="kafel"><div class="kg">${o.przyjety ? "Odbiór lokalu" : "Odmowa odbioru"}: ${esc(o.nazwa)}</div>
    <div class="kt"><p>${esc(o.tekst)}</p>${o.przyjety ? "" : `<p class="minus">Lokal zacznie działać najwcześniej w rundzie ${o.dziala_od}.</p>`}</div></div>`).join("");
}

function kontrolaHtml(k) {
  if (!k) return "";
  const naglowek = !k.kontrola ? "Sanepid nie przyszedł" : k.mandat ? `Kontrola sanepidu – mandat ${zl2(k.mandat)}` : "Kontrola sanepidu – bez zastrzeżeń";
  return `<div class="kafel"><div class="kg">${naglowek}</div><div class="kt">${k.tekst ? `<p>${esc(k.tekst)}</p>` : ""}
    <div class="wiersz"><span>Szansa kontroli</span><span>${proc(k.szansa)}</span></div>
    ${k.skargi ? `<div class="wiersz"><span>W tym skargi</span><span>${proc(k.skargi)}</span></div>` : ""}</div></div>`;
}

// UF15: Urzędy → Urząd (rejestracja, odbiory lokali) i Urzędy → Sanepid (higiena, kontrole, skargi)
export const urzad = {
  tytul: "Urząd", tytulPelny: "Urzędy – ratusz", ikona: "urzad", odblokowanie: (v) => !!v.urzad, ukryta: (v) => !v.urzad,
  info: `Firma jest zarejestrowana, ale każdy lokal przed pierwszą sprzedażą musi odebrać sanepid – bez porządnego sprzątania
    (poziom higieny w zakładce <a data-zakladka-k="sanepid">Sanepid</a>) odbioru nie będzie. Braki w decyzjach widać
    na <a data-zakladka-k="lista_bledow">liście błędów</a>.`,
  decyzje({ v }) {
    const U = v.urzad;
    if (!U) return `<p class="podpowiedz">Brak danych.</p>`;
    const R = U.rejestracja, D = U.decyzja;
    const lokale = U.lokale.map((l) => [esc(l.nazwa), l.dziala_od,
      l.odbior ? `<span class="plus">odebrany w rundzie ${l.odbior}</span>` : `odbiór w rundzie ${l.dziala_od}`]);
    return `<div class="karta"><p>W ratuszu pachnie pastą do podłóg i kawą z automatu. Okienko sanepidu jest na końcu korytarza,
        za tablicą „Myj ręce” w czterech językach i plakatem z gołębiem przekreślonym na czerwono.</p></div>
      <div class="kafel"><div class="kg">Rejestracja firmy – CEIDG</div><div class="kt"><p>${esc(R.tekst)}</p>
        <div class="wiersz"><span>PKD</span><span>${esc(R.pkd)} – ${esc(R.opis_pkd)}</span></div></div></div>`
      + (lokale.length ? tabela("Lokale i odbiory sanepidu", ["Lokal", "Działa od rundy", "Odbiór"], lokale, { klasy: ["l", "", "l"] })
        : `<p class="podpowiedz">Nie masz jeszcze lokalu – sanepid odbierze go w rundzie, w której lokal ma zacząć działać.</p>`)
      + odbioryHtml(D?.odbiory)
      + `<p class="podpowiedz">Po odmowie odbioru lokal czeka ${rund(U.odroczenie_rund)}.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.urzad;
    if (!W) return brakWynikow();
    const odb = W.odbiory || [], ok = odb.filter((o) => o.przyjety).length;
    if (!odb.length) return `<p class="podpowiedz">W tej rundzie nie było odbiorów lokali.</p>`;
    return podsumowanie(ok === odb.length ? `Sanepid odebrał ${ok === 1 ? "lokal" : "wszystkie lokale"} – można zaczynać sprzedaż.`
      : `Sanepid odmówił odbioru ${odb.length - ok} z ${odb.length} lokali – te lokale ruszą później.`, ok === odb.length ? "ok" : "uwaga") + odbioryHtml(odb);
  },
};

export const sanepid = {
  tytul: "Sanepid", tytulPelny: "Urzędy – sanepid", ikona: "swiezosc", odblokowanie: (v) => !!v.urzad, ukryta: (v) => !v.urzad,
  info: `Higiena kosztuje co rundę za każdy działający lokal i zmienia kontrole: lepsza zmniejsza szansę, że kontrola
    przyczepi się do wynajętej chłodni albo przeterminowanego towaru. Skargi z historii ściągają sanepid częściej.
    Ryzyko kontroli widać też w zakładce <a data-zakladka-k="swiezosc">Magazyn i świeżość</a>.`,
  decyzje({ v, edycja }) {
    const U = v.urzad;
    if (!U) return `<p class="podpowiedz">Brak danych.</p>`;
    const D = U.decyzja, Z = U.ryzyko;
    const wybrany = D?.higiena ?? U.higiena;
    const poziomy = U.poziomy.map((p) => [`<b>${esc(p.nazwa)}</b><br><small>${esc(p.opis)}</small>`, zl2(p.koszt_rundy), skutkiPoziomu(p),
      p.id === wybrany ? `<span class="plus">wybrany</span>`
        : edycja ? `<button class="btn jasny" data-akcja="urz-higiena" data-p="${esc(p.id)}">Wybierz</button>` : ""]);
    return tabela("Higiena lokali", ["Poziom", `Koszt za lokal${naOkres()}`, "Wpływ na kontrole", ""], poziomy, { klasy: ["l", "", "l"], sortuj: false })
      + (Z ? `<div class="pasek ciemny"><span>Szansa kontroli w tej rundzie: <span class="kwota">${proc(Z.szansa)}</span></span>
          <span>W tym z problemów: <span class="kwota">${proc(Z.problem)}</span></span>
          <span>Możliwy mandat: <span class="kwota">${Z.problem > 0 ? zl2(Z.mandat) : "–"}</span></span>
          ${D ? `<span>Higiena w tej rundzie: <span class="kwota">${zl2(D.koszt)}</span></span>` : ""}</div>`
        : U.kontrole_od > v.runda ? `<p class="podpowiedz">Pierwsze kontrole sanepidu – od rundy ${U.kontrole_od}. Do tego czasu
          higiena decyduje tylko o odbiorze lokalu (i kosztuje).</p>` : "")
      + (U.skargi.length ? tabela("Skargi do sanepidu", ["Skarga", "Szansa kontroli", "Do rundy"],
        U.skargi.map((s) => [esc(s.opis), `+${proc(s.szansa, 0)}`, s.do_rundy]), { klasy: ["l"] }) : "")
      + `<p class="podpowiedz">Szansa kontroli: stała część ${proc(U.szansa_bazowa)} plus problemy – litry w wynajętej chłodni (z planu dostaw),
        przeterminowany towar (jak w poprzedniej rundzie), higiena i skargi. Kontrola kończy się mandatem tym częściej, im większa część z problemów.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.urzad, U = v.urzad;
    if (!W) return brakWynikow();
    const poziom = U?.poziomy.find((p) => p.id === W.higiena);
    const razem = [["Higiena", poziom ? esc(poziom.nazwa) : "–"], ["Działające lokale", W.lokale],
      ["Koszt utrzymania czystości", `<span class="minus">${zl2(-W.koszt)}</span>`],
      ["Mandat sanepidu", W.kontrola?.mandat ? `<span class="minus">${zl2(-W.kontrola.mandat)}</span>` : "–"]];
    const kontr = W.kontrola, mandat = kontr?.mandat || 0;
    const lead = podsumowanie([!W.lokale ? "Żaden lokal jeszcze nie działa, więc sanepid nie miał czego kontrolować."
      : !kontr?.kontrola ? "Sanepid w tej rundzie nie przyszedł z kontrolą." : mandat ? `Kontrola sanepidu skończyła się mandatem <b>${zl(mandat)}</b>.` : "Sanepid skontrolował lokal i nie miał zastrzeżeń.",
      W.koszt > 0 ? `Utrzymanie czystości kosztowało ${zl2(W.koszt)}.` : ""], mandat ? "zly" : "ok");
    const kafle = kafelkiLiczb([{ etykieta: "Higiena", wartosc: poziom ? esc(poziom.nazwa) : "–" }, { etykieta: "Koszt czystości", wartosc: zl2(W.koszt) },
      kontr && { etykieta: "Szansa kontroli", wartosc: proc(kontr.szansa) }, { etykieta: "Mandat", wartosc: mandat ? zl(mandat) : "brak", ton: mandat ? "minus" : "plus" }]);
    return lead + kafle
      + zwinTabela("Sanepid w rundzie", ["Co", ""], razem, { klasy: ["l"], sortuj: false })
      + kontrolaHtml(W.kontrola)
      + (U?.kontrole.length ? zwinTabela("Kontrole sanepidu", ["Runda", "Wynik", "Szansa", "Mandat"], U.kontrole.map((k) => [k.runda,
        k.mandat ? "z zastrzeżeniami" : "bez zastrzeżeń", proc(k.szansa), k.mandat ? `<span class="minus">${zl2(-k.mandat)}</span>` : "–"]), { klasy: ["", "l"] }) : "")
      + (U ? `<p class="podpowiedz">Od początku gry: higiena ${zl2(U.koszt_razem)}, mandaty sanepidu ${zl2(U.mandaty_razem)} (poza KPiR).</p>` : "");
  },
  akcje: {
    "urz-higiena": (el, c) => c.zmien((d) => { d.higiena = el.dataset.p; }),
  },
};
