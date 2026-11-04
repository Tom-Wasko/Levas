// Zdarzenia – eventy w parkach (gra z lokalami, silnik/swiat/zdarzenia.py). Co rundę w parkach zaczynają się 3–4 historie,
// te same dla wszystkich drużyn (P9: opcje po 2–5 h – czasu właściciela nie starczy na wszystko); każda drużyna wybiera reakcję (decyzja `zdarzenia: {historia: opcja}`). Do tego
// historie jednej drużyny: bank żywności i wypadki w lokalu (silnik/swiat/awarie.py – szkody i polisy).
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

// P3: układ „lista spraw + szczegóły” – która sprawa jest pokazana po prawej (stan przeglądarki, nie decyzja)
let pokazana = null;

const nazwaParku = (kat, id) => kat?.mapa?.budynki?.find((b) => b.id === id)?.nazwa || id;
const gdzie = (s, kat) => s.park ? nazwaParku(kat, s.park) : s.wypadek ? "wypadek w lokalu" : "w lokalu";

// stan sprawy: wybrana opcja, czy własny wybór i czy starcza na nią godzin (U8: wolne godziny przed tą sprawą)
function stanSprawy(s, wybor, edycja) {
  const id = wybor ?? s.domyslna, o = s.opcje.find((x) => x.id === id) || s.opcje[0];
  const brakNa = (x) => !!(edycja && x?.koszt?.czas && s.wolne != null && x.koszt.czas > s.wolne + 1e-9);
  return { id, o, wlasny: wybor != null, brak: brakNa(o), brakNa };
}

function pasekCzasu(Z, C, wybory, edycja) {
  if (!C) return "";
  const sprawy = Z.aktywne.reduce((a, s) => a + (stanSprawy(s, wybory[s.historia], edycja).o?.koszt?.czas || 0), 0);
  const zajete = C.pula - C.wolne, inne = Math.max(0, zajete - sprawy);
  const szer = (h) => `${Math.max(0, Math.min(100, h / C.pula * 100)).toFixed(1)}%`;
  return `<div class="zd-czas">
      <div class="zd-czas-tekst"><b>Czas właściciela: ${licz(zajete, 1)} / ${licz(C.pula, 1)} h</b>
        <span>sprawy w parkach ${licz(sprawy, 1)} h · inne zadania ${licz(inne, 1)} h · wolne ${licz(C.wolne, 1)} h</span></div>
      <div class="zd-czas-pasek" title="Sprawy ${licz(sprawy, 1)} h, inne zadania ${licz(inne, 1)} h">
        <i class="inne" style="width:${szer(inne)}"></i><i class="sprawy" style="width:${szer(sprawy)}"></i></div>
      <p class="podpowiedz">Na wszystkie sprawy czasu raczej nie starczy – wybierz, które są warte Twoich godzin. Bez wyboru gra wykona reakcję domyślną.</p>
    </div>`;
}

function listaSpraw(Z, wybory, edycja, kat, akt) {
  const poz = Z.aktywne.map((s) => {
    const st = stanSprawy(s, wybory[s.historia], edycja);
    const [znak, klasa, opis] = st.brak ? ["!", "nie", "brak czasu"] : st.wlasny ? ["✓", "ok", "wybrano"] : ["○", "inf", "domyślna"];
    return `<button class="zd-poz${s.historia === akt ? " aktywna" : ""}" data-akcja="zd-pokaz" data-h="${esc(s.historia)}">
        <span class="zd-znak ${klasa}">${znak}</span>
        <span class="zd-poz-tekst"><b>${esc(s.tytul)}</b><small>${esc(gdzie(s, kat))}${s.nowa ? "" : " · ciąg dalszy"}</small>
          <small>${opis}: ${esc(st.o?.tekst || "")}${st.o?.koszt?.czas ? ` (${licz(st.o.koszt.czas, 1)} h)` : ""}</small></span>
      </button>`;
  }).join("");
  const dalej = Z.oczekujace.length ? `<div class="zd-dalej"><b>Ciąg dalszy</b>${Z.oczekujace.map((o) =>
    `<div>${esc(o.tytul)} <small>– runda ${o.runda}</small></div>`).join("")}</div>` : "";
  return `<div class="zd-lista"><div class="zd-lista-tytul">Sprawy w tym tygodniu</div>${poz}${dalej}</div>`;
}

function scenaHtml(s, wybor, edycja, kat) {
  const st = stanSprawy(s, wybor, edycja);
  const opcje = s.opcje.map((o) => {
    const wybrana = st.id === o.id, brak = st.brakNa(o);
    const koszt = o.koszt?.gotowka || o.koszt?.porcje ? kosztTekst({ ...o.koszt, czas: 0 }) : "–";
    const tresc = `<div class="kg">${o.id === s.domyslna ? `<span class="pigulka inf">domyślna</span>` : "<span></span>"}
        ${wybrana ? `<span class="pigulka ${brak ? "nie" : "ok"}">${brak ? "brak czasu" : "wybrano"}</span>` : ""}</div>
      <div class="kt">${esc(o.tekst)}</div>
      <div class="kd"><div class="wiersz"><span>Czas</span><span>${o.koszt?.czas ? `${licz(o.koszt.czas, 1)} h` : "–"}</span></div>
        <div class="wiersz"><span>Koszt</span><span>${koszt}</span></div>
        ${brak ? `<small class="minus">Wymaga ${licz(o.koszt.czas, 1)} h, masz wolne ${licz(s.wolne, 1)} h${wybrana
          ? " – bez zmiany gra wykona reakcję domyślną" : ""}.</small>` : ""}</div>`;
    const kl = `kafel zd-opcja${wybrana ? " wybrany" : ""}${brak && !wybrana ? " niedostepny" : ""}${wybrana && brak ? " zd-brak" : ""}`;
    return edycja && !(brak && !wybrana)
      ? `<button class="${kl}" data-akcja="zd-wybierz" data-h="${esc(s.historia)}" data-o="${esc(o.id)}">${tresc}</button>`
      : `<div class="${kl}">${tresc}</div>`;
  }).join("");
  return `<div class="zd-scena"><h3>${esc(s.tytul)} <small>· ${esc(gdzie(s, kat))}</small></h3>
    <p class="podpowiedz">${s.nowa ? (s.park ? "Nowe wydarzenie w parku" : s.wypadek ? "Wypadek w lokalu" : "Nowe wydarzenie w lokalu") : "Ciąg dalszy"}</p>
    <p>${esc(s.tekst)}</p><div class="zd-opcje">${opcje}</div>${skutkiHtml(s.skutki)}</div>`;
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
  decyzje({ v, kat, edycja }) {
    const Z = v.zdarzenia;
    if (!Z) return `<p class="podpowiedz">Brak danych.</p>`;
    const wybory = v.decyzje?.zdarzenia || {}, C = v.czas_wlasciciela;
    if (!Z.aktywne.length) {
      return `<p class="podpowiedz">${v.runda < Z.od_rundy ? `Parki budzą się do życia od rundy ${Z.od_rundy}.` : "W tej rundzie w parkach spokojnie."}</p>`
        + (Z.oczekujace.length ? `<p class="podpowiedz">Czekają na ciąg dalszy: ${Z.oczekujace.map((o) => `${esc(o.tytul)} (runda ${o.runda})`).join(", ")}.</p>` : "")
        + efektyHtml(Z.efekty) + `<p class="podpowiedz">Porcja jedzenia kosztuje ${zl2(Z.koszt_porcji)}.</p>`;
    }
    const akt = Z.aktywne.some((s) => s.historia === pokazana) ? pokazana : Z.aktywne[0].historia;
    const s = Z.aktywne.find((x) => x.historia === akt);
    return pasekCzasu(Z, C, wybory, edycja)
      + `<div class="zd-uklad">${listaSpraw(Z, wybory, edycja, kat, akt)}${scenaHtml(s, wybory[s.historia], edycja, kat)}</div>`
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
    "zd-wybierz": (el, c) => { pokazana = el.dataset.h; return c.zmien((d) => { d.zdarzenia = { ...(d.zdarzenia || {}), [el.dataset.h]: el.dataset.o }; }); },
    "zd-pokaz": (el, c) => { pokazana = el.dataset.h; c.rysuj(); },
  },
};
