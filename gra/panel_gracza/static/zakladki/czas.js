// Czas właściciela (gra z lokalami, silnik/ludzie/czas_wlasciciela.py): pula godzin na rundę na sprawy poza lokalem.
// Decyzja, na którą nie starcza godzin, jest odrzucona (lista błędów).
import { esc, licz, tabela } from "./wspolne.js";

const ZAKLADKA = { dostawcy: "Dostawcy", zdarzenia: "Zdarzenia", zatrudnienie: "Zatrudnienie" };

function czasHtml(C, tytul) {
  const proc = C.pula ? Math.min(100, Math.round(C.wykorzystane / C.pula * 100)) : 0;
  const odrzucone = C.pozycje.filter((p) => !p.przyjete);
  return `<div class="pasek ciemny"><span>Pula na rundę: <span class="kwota">${licz(C.pula, 1)} h</span></span>
      <span>Wykorzystane: <span class="kwota">${licz(C.wykorzystane, 1)} h</span></span>
      <span>Wolne: <span class="kwota">${licz(C.wolne, 1)} h</span></span></div>
    <div style="height:10px;border-radius:5px;background:var(--tlo-2, #e6e6e6);margin:8px 0;overflow:hidden">
      <div style="height:100%;width:${proc}%;background:${proc >= 100 ? "#e5333f" : "#1e9e5a"}"></div></div>`
    + tabela(tytul, ["Na co", "Zakładka", "Godziny", "Status"],
      C.pozycje.length ? C.pozycje.map((p) => [esc(p.opis), `<a data-zakladka-k="${esc(p.zakladka)}">${esc(ZAKLADKA[p.zakladka] || p.zakladka)}</a>`,
        `${licz(p.godziny, 1)} h`, p.przyjete ? "zaplanowane" : `<span class="minus">odrzucone – brak czasu</span>`])
        : [["Nic nie zużywa czasu właściciela.", "", "", ""]],
      { klasy: ["l", "l"], stopka: ["Razem", "", `${licz(C.wykorzystane, 1)} h`, ""] })
    + (odrzucone.length ? `<div class="komunikat">${odrzucone.length === 1 ? "Jedna decyzja została odrzucona" : `Odrzucone decyzje: ${odrzucone.length}`}
        – zabrakło czasu właściciela. Zmniejsz liczbę dni zakupów w dyskontach albo zamów u dostawcy z dowozem.</div>` : "");
}

export const czas_wlasciciela = {
  tytul: "Czas właściciela", tytulPelny: "Czas właściciela", ikona: "zegar", odblokowanie: (v) => !!v.lokale, ukryta: (v) => !v.lokale,
  info: `Właściciel ma w tygodniu ograniczoną liczbę godzin na sprawy poza lokalem. Każdy dzień zakupów w dyskoncie
    (odbiór osobisty – zakładka <a data-zakladka-k="dostawcy">Dostawcy</a>) zabiera mu kilka kwadransów. Gdy godzin zabraknie,
    kolejne zakupy nie dojdą do skutku – zobaczysz to na liście błędów.`,
  decyzje({ v }) {
    return v.czas_wlasciciela ? czasHtml(v.czas_wlasciciela, "Plan czasu właściciela w tej rundzie") : `<p class="podpowiedz">Brak danych.</p>`;
  },
  wyniki({ v }) {
    const C = v.wyniki?.czas_wlasciciela;
    return C ? czasHtml(C, "Czas właściciela w rundzie") : `<p class="podpowiedz">Wyniki pojawią się po pierwszej rundzie.</p>`;
  },
};
