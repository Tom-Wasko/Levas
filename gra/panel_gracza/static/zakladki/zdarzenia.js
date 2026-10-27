// Zdarzenia – eventy w parkach (gra z lokalami, silnik/zdarzenia.py). Co rundę w parkach zaczynają się 3–4 historie,
// te same dla wszystkich drużyn (P9: opcje po 2–5 h – czasu właściciela nie starczy na wszystko); każda drużyna wybiera reakcję (decyzja `zdarzenia: {historia: opcja}`). Do tego
// historie jednej drużyny: bank żywności i wypadki w lokalu (silnik/awarie.py – szkody i polisy).
import { esc, licz, proc, tabela, zl2 } from "./wspolne.js";

function kosztTekst(k) {
  if (!k) return "";
  const cz = [];
  if (k.czas) cz.push(`${licz(k.czas, 1)} h właściciela`);
  if (k.gotowka) cz.push(zl2(k.gotowka));
  if (k.porcje) cz.push(`${k.porcje} porcji`);
  return cz.length ? cz.join(" + ") + (k.porcje ? ` (razem ${zl2(k.razem_zl)})` : "") : "bez kosztów";
}

function skutekTekst(s) {
  if (s.typ === "gotowka") return `${esc(s.opis)}: <span class="${s.kwota >= 0 ? "plus" : "minus"}">${zl2(s.kwota)}</span>`;
  if (s.typ === "popyt") return `${esc(s.opis)}: popyt ${s.mnoznik >= 1 ? "+" : ""}${proc(s.mnoznik - 1, 0)} przez ${s.rund} ${s.rund === 1 ? "rundę" : "rundy"}`;
  if (s.typ === "kontrola") return `${esc(s.opis)}: szansa kontroli sanepidu +${proc(s.szansa, 0)} przez ${s.rund} ${s.rund === 1 ? "rundę" : "rundy"}`;
  if (s.typ === "czas") return `${esc(s.opis)}: ${licz(s.godziny, 1)} h właściciela mniej przez ${s.rund} ${s.rund === 1 ? "rundę" : "rundy"}`;
  if (s.typ === "oddaj_zapas") return `${esc(s.opis)}${s.oddane ? `: ${zl2(s.oddane)}` : ""} – znika z zaplecza (bez kosztu w KPiR, był kosztem przy zakupie)`;
  if (s.typ === "szkoda") return `${esc(s.opis)}: szkoda <span class="minus">${zl2(-s.kwota)}</span>${s.odszkodowanie
    ? `, odszkodowanie <span class="plus">${zl2(s.odszkodowanie)}</span>` : s.powod ? ` (${esc(s.powod)})` : ""}`;
  if (s.typ === "kandydat") return `${esc(s.opis)}: ${esc(s.kandydat.imie_nazwisko)} czeka na <a data-zakladka-k="rynek_pracy">rynku pracy</a>`;
  return esc(s.opis);
}

const skutkiHtml = (sk) => sk?.length ? `<ul>${sk.map((s) => `<li>${skutekTekst(s)}</li>`).join("")}</ul>` : "";
const naglowek = (s) => `<h3>${esc(s.tytul)}</h3>`;

function scenaHtml(s, wybor, edycja) {
  const opcje = s.opcje.map((o) => {
    const wybrana = (wybor ?? s.domyslna) === o.id;
    const etykieta = `${esc(o.tekst)}${o.id === s.domyslna ? " <small>(domyślnie)</small>" : ""}<br><small>${kosztTekst(o.koszt)}</small>`;
    return edycja ? `<button class="btn ${wybrana ? "zielony" : "jasny"}" data-akcja="zd-wybierz" data-h="${esc(s.historia)}" data-o="${esc(o.id)}"
        style="text-align:left;margin:4px 0;width:100%">${etykieta}</button>`
      : `<div class="wiersz"><span>${wybrana ? "▶ " : ""}${etykieta}</span></div>`;
  }).join("");
  return `<div class="karta">${naglowek(s)}<p class="podpowiedz">${s.nowa ? (s.park ? "Nowe wydarzenie w parku" : s.wypadek ? "Wypadek w lokalu" : "Nowe wydarzenie w lokalu") : "Ciąg dalszy"}</p>
    <p>${esc(s.tekst)}</p>${opcje}${skutkiHtml(s.skutki)}</div>`;
}

function efektyHtml(E) {
  return E?.length ? tabela("Skutki, które jeszcze trwają", ["Co", "Działanie", "Rundy"], E.map((e) => [esc(e.opis),
    e.typ === "popyt" ? `popyt ${e.wartosc >= 1 ? "+" : ""}${proc(e.wartosc - 1, 0)}` : `${licz(e.wartosc, 1)} h właściciela mniej`,
    e.od_rundy === e.do_rundy ? `${e.od_rundy}` : `${e.od_rundy}–${e.do_rundy}`]), { klasy: ["l", "l"] }) : "";
}

function rozegranaHtml(w) {
  return `<div class="karta">${naglowek(w)}<p>${esc(w.tekst)}</p>
    ${w.opcja ? `<p><b>${w.domyslna ? "Reakcja (domyślna)" : "Twoja reakcja"}:</b> ${esc(w.opcja_tekst)} <small>– ${kosztTekst(w.koszt)}</small></p>
      <p>${esc(w.wynik)}</p>` : ""}${skutkiHtml(w.skutki?.map((s) => s.typ === "oddaj_zapas" ? { ...s, oddane: w.oddane } : s))}
    ${w.ciag_dalszy ? `<p class="podpowiedz">Ciąg dalszy nastąpi (runda ${w.ciag_dalszy}).</p>` : ""}</div>`;
}

export const zdarzenia = {
  tytul: "Parki i zdarzenia", tytulPelny: "Parki – eventy, zdarzenia i wypadki", ikona: "zdarzenia", odblokowanie: (v) => !!v.zdarzenia, ukryta: (v) => !v.zdarzenia,
  info: `Co tydzień w parkach na <a data-zakladka-k="mapa">mapie miasta</a> dzieją się 3–4 rzeczy, które widzą wszystkie drużyny.
    Na wszystko nie starczy czasu – reakcja zajmuje zwykle 2–5 h z 20 h właściciela, więc trzeba wybierać.
    Jak zareagujesz, zależy od Ciebie: reakcja może kosztować czas właściciela, gotówkę albo porcje jedzenia, a jej skutki
    – pieniądze, klienci, nowy pracownik – bywają odłożone w czasie. Bez wyboru gra wybiera reakcję domyślną.
    Czasem coś przytrafia się tylko Tobie – w lokalu. Wypadki kosztują, a część kosztów zwraca
    <a data-zakladka-k="ubezpieczenia">polisa</a>, jeśli kupiłeś ją zawczasu.`,
  decyzje({ v, edycja }) {
    const Z = v.zdarzenia;
    if (!Z) return `<p class="podpowiedz">Brak danych.</p>`;
    const wybory = v.decyzje?.zdarzenia || {}, C = v.czas_wlasciciela;
    const czas = C && Z.aktywne.length ? `<div class="komunikat">Wolny czas właściciela: <b>${licz(C.wolne, 1)} h</b> z ${licz(C.pula, 1)} h.
      W tym tygodniu ${Z.aktywne.length === 1 ? "jedna sprawa czeka" : Z.aktywne.length < 5 ? `${Z.aktywne.length} sprawy czekają` : `${Z.aktywne.length} spraw czeka`} – na wszystkie czasu raczej nie starczy.</div>` : "";
    return czas + (Z.aktywne.length ? Z.aktywne.map((s) => scenaHtml(s, wybory[s.historia], edycja)).join("")
      : `<p class="podpowiedz">${v.runda < Z.od_rundy ? `Parki budzą się do życia od rundy ${Z.od_rundy}.` : "W tej rundzie w parkach spokojnie."}</p>`)
      + (Z.oczekujace.length ? `<p class="podpowiedz">Czekają na ciąg dalszy: ${Z.oczekujace.map((o) => `${esc(o.tytul)} (runda ${o.runda})`).join(", ")}.</p>` : "")
      + efektyHtml(Z.efekty)
      + `<p class="podpowiedz">Porcja jedzenia kosztuje ${zl2(Z.koszt_porcji)}.</p>`;
  },
  wyniki({ v }) {
    const W = v.wyniki?.zdarzenia, Z = v.zdarzenia;
    const teraz = W?.sceny?.length ? W.sceny.map(rozegranaHtml).join("") : `<p class="podpowiedz">W poprzedniej rundzie nic się nie wydarzyło.</p>`;
    const dawne = (Z?.dziennik || []).filter((w) => w.runda < v.runda - 1);
    return teraz + efektyHtml(Z?.efekty)
      + (dawne.length ? tabela("Dziennik historii", ["Runda", "Historia", "Reakcja"], dawne.slice().reverse().map((w) =>
        [w.runda, esc(w.tytul), esc(w.opcja_tekst || "–")]), { klasy: ["", "l", "l"] }) : "");
  },
  akcje: {
    "zd-wybierz": (el, c) => c.zmien((d) => { d.zdarzenia = { ...(d.zdarzenia || {}), [el.dataset.h]: el.dataset.o }; }),
  },
};
