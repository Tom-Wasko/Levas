// Z6 (przebudowa zakładek 2.11.2026): proste infografiki SVG w dymkach kółek „i” dla najtrudniejszych mechanik.
// Liczby na rysunkach to przykłady – prawdziwe wartości są w tabelach zakładek.

const KOL = { pom: "#1e9e5a", pomJ: "#eaf7ef", tekst: "#2b2b30", szary: "#70707a", szaryJ: "#f4f4f6", linia: "#cfd8d2",
  czer: "#d93445", czerJ: "#fdeaec", nieb: "#2f6fb0", niebJ: "#e6eff8", zolty: "#c98a0b", zoltyJ: "#fbf3df" };

const svg = (w, h, opis, tresc) => `<svg viewBox="0 0 ${w} ${h}" width="${w}" role="img" aria-label="${opis}"
  font-family="inherit" font-size="11" fill="${KOL.tekst}" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="strz" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0L10 5L0 10z" fill="${KOL.szary}"/></marker></defs>${tresc}</svg>`;
const prost = (x, y, w, h, tlo, ramka = KOL.linia, r = 6) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${tlo}" stroke="${ramka}"/>`;
const napis = (x, y, t, opc = "") => `<text x="${x}" y="${y}" ${opc}>${t}</text>`;
const srodek = (x, y, t, opc = "") => napis(x, y, t, `text-anchor="middle" ${opc}`);
const strzalka = (x1, y1, x2, y2, kol = KOL.szary) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${kol}" stroke-width="1.5" marker-end="url(#strz)"/>`;
const pol = (x) => String(x).replace(".", ",");

// 1. Świeżość: partie w magazynie zużywane od najkrótszego terminu (FIFO), po terminie – kosz, nadmiar – chłodnia
export const IG_SWIEZOSC = svg(400, 190, "Partie zużywane od najkrótszego terminu", `
  ${napis(0, 12, "Magazyn lokalu – partie mięsa", 'font-weight="700"')}
  ${prost(0, 22, 86, 46, KOL.czerJ, KOL.czer)}${srodek(43, 40, "dostawa Pn")}${srodek(43, 56, "termin: Czw", `fill="${KOL.czer}" font-weight="700"`)}
  ${prost(94, 22, 86, 46, KOL.zoltyJ, KOL.zolty)}${srodek(137, 40, "dostawa Śr")}${srodek(137, 56, "termin: So")}
  ${prost(188, 22, 86, 46, KOL.pomJ, KOL.pom)}${srodek(231, 40, "dostawa Pt")}${srodek(231, 56, "termin: Wt")}
  ${strzalka(43, 72, 43, 98)}${srodek(46, 112, "do dań – najpierw", 'font-weight="700"')}${srodek(46, 125, "najkrótszy termin")}
  ${prost(294, 22, 106, 46, KOL.szaryJ)}${srodek(347, 40, "wieczorem")}${srodek(347, 56, "po terminie → kosz")}
  ${strzalka(276, 45, 292, 45)}
  ${prost(150, 98, 250, 52, KOL.niebJ, KOL.nieb)}${napis(160, 116, "Szafa / zamrażarka pełna?", 'font-weight="700"')}
  ${napis(160, 131, "nadmiar → wynajęta chłodnia: płacisz za litr,")}${napis(160, 144, "a termin partii się skraca")}
  ${napis(0, 172, "Kosz i dużo towaru w chłodni przyciągają sanepid.", `fill="${KOL.czer}"`)}
  ${napis(0, 186, "Mrożonka zastępuje świeży składnik, gdy go zabraknie (−1★).", `fill="${KOL.szary}"`)}`);

// 2. Wybór lokalu: klienci strefy dzielą się według atrakcyjności A (model logitowy z opcją zewnętrzną)
const UDZIALY = [["Twój lokal", 1.5, KOL.pom], ["Rywal w strefie", 1.0, KOL.nieb], ["Bary spoza gry, obiad w domu", 1.0, KOL.szary]];
export const IG_KLIENCI = (() => {
  const suma = UDZIALY.reduce((s, x) => s + x[1], 0);
  let x = 0, pasy = "", opisy = "";
  UDZIALY.forEach(([n, a, k], i) => {
    const w = (380 * a) / suma;
    pasy += `<rect x="${10 + x}" y="58" width="${w - 2}" height="30" rx="4" fill="${k}"/>`
      + srodek(10 + x + w / 2, 77, `${Math.round((100 * a) / suma)} os.`, 'fill="#fff" font-weight="700"');
    opisy += `<rect x="10" y="${104 + i * 16}" width="10" height="10" rx="2" fill="${k}"/>` + napis(26, 113 + i * 16, `${n}: A = ${pol(a)}`);
    x += w;
  });
  return svg(400, 200, "Podział klientów strefy między lokale", `
    ${napis(10, 14, "100 głodnych w strefie wybiera, gdzie zjeść", 'font-weight="700"')}
    ${napis(10, 32, "udział lokalu = A lokalu / (A spoza gry + Σ A lokali)", `fill="${KOL.szary}"`)}
    ${napis(10, 48, "Przykład:")}${pasy}${opisy}
    ${prost(10, 156, 380, 40, KOL.pomJ, KOL.pom)}
    ${napis(20, 172, "A rośnie z: jakością, niższą ceną (wobec cen strefy), zadowoleniem,")}
    ${napis(20, 187, "wyposażeniem i reklamą; maleje z odległością od strefy klienta.")}`);
})();

// 3. Reklama: efekt nasyca się 1 − e^(−tempo · emisje), a cena emisji spada na progach rabatów (przykład: ulotki)
export function igReklama(tempo = 0.265, znizki = [[4, 0.15], [11, 0.3]], maks = 20) {
  const X = (n) => 40 + (n / maks) * 340, Y = (e) => 100 - e * 80;
  const pkt = Array.from({ length: maks + 1 }, (_, n) => `${X(n).toFixed(1)},${Y(1 - Math.exp(-tempo * n)).toFixed(1)}`).join(" ");
  const znaczniki = [1, 4, 10].map((n) => {
    const e = 1 - Math.exp(-tempo * n);
    return `<circle cx="${X(n)}" cy="${Y(e)}" r="3.5" fill="${KOL.pom}"/>` + napis(X(n) + 6, Y(e) + 12, `${n} → ${Math.round(e * 100)}%`, 'font-weight="700"');
  }).join("");
  const progi = [[1, 0], ...znizki];
  const slupki = progi.map(([od, r], i) => {
    const doN = i + 1 < progi.length ? progi[i + 1][0] - 1 : maks, h = 34 * (1 - r);
    return `<rect x="${X(od - 1) + 1}" y="${184 - h}" width="${X(doN) - X(od - 1) - 2}" height="${h}" fill="${i ? KOL.pomJ : KOL.szaryJ}" stroke="${KOL.pom}"/>`
      + srodek((X(od - 1) + X(doN)) / 2, 180 - h, r ? `−${Math.round(r * 100)}%` : "100%", 'font-weight="700"');
  }).join("");
  return svg(400, 210, "Nasycenie efektu reklamy i progi rabatów", `
    ${napis(0, 12, "Siła kampanii w rundzie (% pełnego efektu kanału)", 'font-weight="700"')}
    <line x1="40" y1="100" x2="384" y2="100" stroke="${KOL.linia}"/><line x1="40" y1="20" x2="40" y2="100" stroke="${KOL.linia}"/>
    <line x1="40" y1="20" x2="384" y2="20" stroke="${KOL.linia}" stroke-dasharray="3 3"/>${napis(4, 24, "100%", `fill="${KOL.szary}"`)}
    <polyline points="${pkt}" fill="none" stroke="${KOL.pom}" stroke-width="2.5"/>${znaczniki}
    ${napis(0, 132, "Cena jednej emisji – progi rabatów (na wszystkie emisje)", 'font-weight="700"')}
    ${slupki}<line x1="40" y1="184" x2="384" y2="184" stroke="${KOL.linia}"/>
    ${[1, 5, 10, 15, 20].filter((n) => n <= maks).map((n) => srodek(X(n), 198, n, `fill="${KOL.szary}"`)).join("")}
    ${napis(384, 208, "emisje w rundzie", `text-anchor="end" fill="${KOL.szary}"`)}`);
}

// 4. VAT: brutto = netto + VAT; należny ze sprzedaży − naliczony z zakupów = do zapłaty albo nadwyżka
export const IG_VAT = svg(400, 200, "Rozliczenie VAT w rundzie", `
  ${napis(0, 12, "Przykład: ceny w grze są brutto", 'font-weight="700"')}
  ${prost(0, 22, 120, 40, KOL.pomJ, KOL.pom)}${srodek(60, 38, "Sprzedaż kebaba")}${srodek(60, 54, "108 zł brutto", 'font-weight="700"')}
  ${prost(0, 92, 120, 40, KOL.niebJ, KOL.nieb)}${srodek(60, 108, "Zakup mięsa")}${srodek(60, 124, "52,50 zł brutto", 'font-weight="700"')}
  ${strzalka(122, 34, 168, 34)}${strzalka(122, 52, 168, 64)}${strzalka(122, 104, 168, 104)}${strzalka(122, 122, 168, 134)}
  ${napis(172, 38, "100 zł netto → KPiR (przychód)")}${napis(172, 68, "8 zł VAT należny (8%)", `fill="${KOL.czer}" font-weight="700"`)}
  ${napis(172, 108, "50 zł netto → KPiR (koszt)")}${napis(172, 138, "2,50 zł VAT naliczony (5%)", `fill="${KOL.pom}" font-weight="700"`)}
  ${prost(0, 152, 400, 46, KOL.szaryJ)}
  ${napis(10, 170, "Deklaracja: należny 8 − naliczony 2,50 = 5,50 zł do urzędu", 'font-weight="700"')}
  ${napis(10, 188, "Gdy naliczony jest większy – nadwyżka przechodzi na następną rundę.", `fill="${KOL.szary}"`)}`);

// 5. PIT i ZUS: z KPiR dochód narastająco → zaliczka PIT 19% minus to, co już wpłacone; zdrowotna i ZUS osobno
export const IG_PIT = svg(400, 186, "Rozliczenie PIT i ZUS w rundzie", `
  ${prost(0, 0, 120, 44, KOL.pomJ, KOL.pom)}${srodek(60, 18, "KPiR")}${srodek(60, 34, "przychody − koszty", 'font-weight="700"')}
  ${strzalka(122, 22, 150, 22)}
  ${prost(152, 0, 248, 44, KOL.szaryJ)}${srodek(276, 18, "dochód narastająco od początku gry")}${srodek(276, 34, "(straty z wcześniejszych rund się liczą)", `fill="${KOL.szary}"`)}
  ${strzalka(276, 46, 276, 66)}
  ${prost(0, 68, 400, 44, KOL.czerJ, KOL.czer)}${srodek(200, 86, "zaliczka PIT = 19% × (dochód narastająco − odliczona zdrowotna)", 'font-weight="700"')}
  ${srodek(200, 102, "− zaliczki wpłacone wcześniej (gdy wynik ujemny – nic nie płacisz)", `fill="${KOL.szary}"`)}
  ${prost(0, 124, 194, 60, KOL.niebJ, KOL.nieb)}${napis(10, 142, "Składka zdrowotna", 'font-weight="700"')}
  ${napis(10, 158, "4,9% dochodu, nie mniej")}${napis(10, 172, "niż minimum")}
  ${prost(206, 124, 194, 60, KOL.zoltyJ, KOL.zolty)}${napis(216, 142, "ZUS społeczny", 'font-weight="700"')}
  ${napis(216, 158, "ulga na start: pierwsze 26 rund bez")}${napis(216, 172, "składek, potem preferencyjny ZUS")}`);

// 6. Auto-dostawca: cena Auchan + prowizja + abonament; nadwyżka czeka u dostawcy i kosztuje przechowanie
export const IG_AUTO = svg(400, 176, "Jak działa auto-dostawca", `
  ${prost(0, 0, 112, 52, KOL.niebJ, KOL.nieb)}${srodek(56, 20, "Auchan", 'font-weight="700"')}${srodek(56, 38, "średnia cen +12%")}
  ${strzalka(114, 26, 142, 26)}
  ${prost(144, 0, 116, 52, KOL.zoltyJ, KOL.zolty)}${srodek(202, 20, "Auto-dostawca", 'font-weight="700"')}${srodek(202, 38, "+10% prowizji")}
  ${strzalka(262, 26, 290, 26)}
  ${prost(292, 0, 108, 52, KOL.pomJ, KOL.pom)}${srodek(346, 20, "Twój lokal", 'font-weight="700"')}${srodek(346, 38, "dowozi codziennie")}
  ${strzalka(202, 54, 202, 80)}
  ${prost(100, 82, 204, 46, KOL.szaryJ)}${srodek(202, 100, "Co nie zejdzie – czeka u dostawcy")}${srodek(202, 116, "0,15 zł za litr dziennie", 'font-weight="700"')}
  ${napis(0, 150, "+ abonament 120 zł tygodniowo. Wygodne, ale drożej niż samemu.")}
  ${napis(0, 168, "Po terminie towar u dostawcy przepada (bez sanepidu).", `fill="${KOL.szary}"`)}`);
