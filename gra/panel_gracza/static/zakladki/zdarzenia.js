// Zdarzenia – eventy w parkach (gra z lokalami, silnik/swiat/zdarzenia.py). Co rundę w parkach zaczynają się 3–4 historie,
// UF13: bez własnej zakładki – park na mapie otwiera okno parku (`oknoParku`, nad mapą pasek `parkiNaMapie`),
// sprawy tylko tej drużyny (bank żywności, wypadki) są częścią „sprawy” zakładki Mój lokal.
// te same dla wszystkich drużyn (P9: opcje po 2–5 h – czasu właściciela nie starczy na wszystko); każda drużyna wybiera reakcję (decyzja `zdarzenia: {historia: opcja}`). Do tego
// historie jednej drużyny: bank żywności i wypadki w lokalu (silnik/swiat/awarie.py – szkody i polisy).
import { esc, licz, okno, podsumowanie, proc, tabela, toast, zl2 } from "./wspolne.js";

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
  const opcje = s.opcje.map((o, i) => {
    const wybrana = st.id === o.id, brak = st.brakNa(o);
    const koszt = o.koszt?.gotowka || o.koszt?.porcje ? kosztTekst({ ...o.koszt, czas: 0 }) : "–";
    const tresc = `<div class="kg"><span class="zd-litera">${"ABCDEFG"[i] || i + 1}</span>${o.id === s.domyslna ? `<span class="pigulka inf">domyślna</span>` : ""}
        ${wybrana ? `<span class="pigulka ${brak ? "nie" : "ok"}">${brak ? "brak czasu" : "wybrano"}</span>` : ""}</div>
      <div class="kt">${esc(o.tekst)}</div>
      <div class="kd"><div class="wiersz"><span>Czas</span><span>${o.koszt?.czas ? `${licz(o.koszt.czas, 1)} h` : "–"}</span></div>
        <div class="wiersz"><span>Koszt</span><span>${koszt}</span></div>
        ${brak ? `<small class="minus">Wymaga ${licz(o.koszt.czas, 1)} h, masz wolne ${licz(s.wolne, 1)} h${wybrana
          ? " – bez zmiany gra wykona reakcję domyślną" : ""}.</small>` : ""}</div>`;
    const kl = `kafel zd-opcja${wybrana ? " wybrany" : ""}${brak && !wybrana ? " niedostepny" : ""}${wybrana && brak ? " zd-brak" : ""}`;
    return edycja && !(brak && !wybrana)
      ? `<button class="${kl}" data-akcja="zd-wybierz" data-h="${esc(s.historia)}" data-o="${esc(o.id)}" data-park="${esc(s.park || "")}">${tresc}</button>`
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

const wParku = (s) => !!s.park;
const lokalne = (lista) => (lista || []).filter((s) => !wParku(s));

// UF13: okno parku z mapy – sprawy tego parku w tej rundzie (kafelki opcji), skutki poprzedniej rundy i historia parku
export function oknoParku(c, id) {
  const { v, kat } = c, b = kat.mapa?.budynki?.find((x) => x.id === id), nazwa = b?.nazwa || id, Z = v.zdarzenia;
  if (!Z) return toast(`${nazwa}: ${b?.opis || ""}`);
  const wybory = v.decyzje?.zdarzenia || {}, edycja = c.edycja;
  const teraz = Z.aktywne.filter((s) => s.park === id);
  const dalej = Z.oczekujace.filter((o) => o.park === id);
  const ostatnie = (v.wyniki?.zdarzenia?.sceny || []).filter((w) => w.park === id);
  const dawne = (Z.dziennik || []).filter((w) => w.park === id && w.runda < v.runda - 1);
  let html = b?.opis ? `<p class="podpowiedz">${esc(b.opis)}</p>` : "";
  if (v.runda < Z.od_rundy) html += `<p class="podpowiedz">Parki budzą się do życia od rundy ${Z.od_rundy}.</p>`;
  else if (teraz.length) html += pasekCzasu(Z, v.czas_wlasciciela, wybory, edycja) + teraz.map((s) => scenaHtml(s, wybory[s.historia], edycja, kat)).join("");
  else html += `<p class="podpowiedz">W tym tygodniu w tym parku spokojnie.${Z.aktywne.some(wParku) ? " Coś dzieje się w innym parku – parki ze znakiem „!” na mapie." : ""}</p>`;
  if (dalej.length) html += `<p class="podpowiedz">Ciąg dalszy nastąpi: ${dalej.map((o) => `${esc(o.tytul)} (runda ${o.runda})`).join(", ")}.</p>`;
  if (ostatnie.length) html += `<div class="sekcja-tytul" style="margin-top:18px">Co wydarzyło się w poprzedniej rundzie</div>` + ostatnie.map(rozegranaHtml).join("");
  if (dawne.length) html += tabela("Historia parku", ["Runda", "Historia", "Reakcja"], dawne.slice().reverse().map((w) =>
    [w.runda, esc(w.tytul), esc(w.opcja_tekst || "–")]), { klasy: ["", "l", "l"] });
  html += `<p class="podpowiedz">Porcja jedzenia kosztuje ${zl2(Z.koszt_porcji)}.</p>`;
  okno(esc(nazwa), html, { przyciski: `<button class="btn pom" data-akcja="zamknij-okno">OK</button>` });
}

// pasek nad mapą: sprawy w parkach w tej rundzie (klik → okno parku) i skutki, które jeszcze trwają
export function parkiNaMapie(v, kat, edycja) {
  const Z = v.zdarzenia;
  if (!Z || v.runda < Z.od_rundy) return "";
  const wybory = v.decyzje?.zdarzenia || {};
  const sprawy = Z.aktywne.filter(wParku).map((s) => {
    const st = stanSprawy(s, wybory[s.historia], edycja);
    const [znak, klasa] = st.brak ? ["!", "nie"] : st.wlasny ? ["✓", "ok"] : ["○", "inf"];
    return `<button class="zd-park" data-akcja="zd-park" data-id="${esc(s.park)}"><span class="zd-znak ${klasa}">${znak}</span>
      <span><b>${esc(nazwaParku(kat, s.park))}</b><small>${esc(s.tytul)}</small></span></button>`;
  }).join("");
  const trwa = (Z.efekty || []).map((e) => `${esc(e.opis)} (do rundy ${e.do_rundy})`).join(" · ");
  return `<div class="zd-parki"><div class="zd-parki-tytul">${sprawy ? "W parkach w tym tygodniu – kliknij, żeby zareagować" : "W parkach w tym tygodniu spokojnie"}</div>
    ${sprawy ? `<div class="zd-parki-lista">${sprawy}</div>` : ""}${trwa ? `<p class="podpowiedz">Jeszcze trwa: ${trwa}.</p>` : ""}</div>`;
}

const parkiZeSprawa = (v) => new Set((v.zdarzenia?.aktywne || []).filter(wParku).map((s) => s.park));
export { parkiZeSprawa };

export const AKCJE_ZDARZEN = {
  "zd-wybierz": async (el, c) => {
    pokazana = el.dataset.h;
    await c.zmien((d) => { d.zdarzenia = { ...(d.zdarzenia || {}), [el.dataset.h]: el.dataset.o }; });
    if (el.dataset.park && el.closest(".zaslona")) oknoParku(c, el.dataset.park);
  },
  "zd-pokaz": (el, c) => { pokazana = el.dataset.h; c.rysuj(); },
  "zd-park": (el, c) => oknoParku(c, el.dataset.id),
};

// część „sprawy” zakładki Mój lokal: bank żywności i wypadki – tylko tej drużyny
export const sprawy = {
  tytul: "Sprawy w lokalu", tytulPelny: "Sprawy w lokalu – bank żywności, wypadki", ikona: "zdarzenia",
  odblokowanie: (v) => !!v.zdarzenia,
  ukryta: (v) => !v.zdarzenia || !(lokalne(v.zdarzenia.aktywne).length || lokalne(v.wyniki?.zdarzenia?.sceny).length),
  info: `Czasem coś przytrafia się tylko Tobie – w lokalu. Reakcja może kosztować czas właściciela, gotówkę albo porcje
    jedzenia, a jej skutki bywają odłożone w czasie. Bez wyboru gra wybiera reakcję domyślną. Wypadki kosztują, a część kosztów
    zwraca <a data-zakladka-k="ubezpieczenia">polisa</a>, jeśli kupiłeś ją zawczasu. Wydarzenia w parkach – kliknij park na
    <a data-zakladka-k="mapa">mapie miasta</a>.`,
  decyzje({ v, kat, edycja }) {
    const Z = v.zdarzenia, L = lokalne(Z.aktywne), wybory = v.decyzje?.zdarzenia || {};
    if (!L.length) return `<p class="podpowiedz">W tym tygodniu w lokalu spokojnie.</p>` + efektyHtml(Z.efekty);
    const akt = L.some((s) => s.historia === pokazana) ? pokazana : L[0].historia;
    const s = L.find((x) => x.historia === akt);
    return pasekCzasu(Z, v.czas_wlasciciela, wybory, edycja)
      + (L.length > 1 ? `<div class="zd-uklad">${listaSpraw({ ...Z, aktywne: L, oczekujace: [] }, wybory, edycja, kat, akt)}${scenaHtml(s, wybory[s.historia], edycja, kat)}</div>`
        : scenaHtml(s, wybory[s.historia], edycja, kat))
      + efektyHtml(Z.efekty) + `<p class="podpowiedz">Porcja jedzenia kosztuje ${zl2(Z.koszt_porcji)}.</p>`;
  },
  wynikiGdy: (v) => lokalne(v.wyniki?.zdarzenia?.sceny).length > 0,
  wyniki({ v }) {
    const L = lokalne(v.wyniki?.zdarzenia?.sceny), tr = v.zdarzenia?.efekty?.length || 0;
    return podsumowanie([`W lokalu ${L.length === 1 ? "zdarzyła się" : "zdarzyło się"} <b>${licz(L.length)}</b> ${L.length === 1 ? "sprawa" : "spraw"}: ${L.map((w) => esc(w.tytul)).join(", ")}.`,
      tr ? `Skutki ${tr === 1 ? "jednego zdarzenia trwają" : "zdarzeń trwają"} jeszcze w kolejnych rundach.` : ""])
      + L.map(rozegranaHtml).join("") + efektyHtml(v.zdarzenia?.efekty);
  },
  akcje: AKCJE_ZDARZEN,
};
