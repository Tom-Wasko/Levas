// Kółka „i” z dymkiem (przebudowa zakładek 2.11.2026, archiwum/plany/przebudowa_zakladek.md): na stronie zostają nagłówki,
// tabele, pola i krótkie etykiety, a opisy i objaśnienia pokazują się w dymku po najechaniu (albo dotknięciu) kółka.

// kółko z treścią dymka (HTML: tekst i/lub infografika SVG)
export const kolko = (html, klasa = "") => html
  ? `<span class="kolko-i ${klasa}" tabindex="0" role="button" aria-label="Wyjaśnienie">i<span class="dymek-tresc">${html}</span></span>`
  : "";

const DLUGA = 60;   // znaków – krótsza podpowiedź zostaje na stronie jako etykieta
const NAGLOWEK = ".pasek, .tabela-tytul, h3, h4, .kg";

// gdzie postawić kółko podpowiedzi-akapitu: nagłówek przed nim, tytuł tabeli przed nim albo nagłówek kafelka
function kotwica(el) {
  const p = el.previousElementSibling;
  if (p?.matches(NAGLOWEK)) return p;
  if (p?.matches(".tab-wrap") && p.previousElementSibling?.matches(".tabela-tytul")) return p.previousElementSibling;
  return el.closest(".kafel")?.querySelector(":scope > .kg") || null;
}

// długie podpowiedzi (.podpowiedz) → kółka „i”; ostrzeżenia (.minus) i podpowiedzi z polami zostają na wierzchu
export function zwinPodpowiedzi(korzen) {
  korzen.querySelectorAll(".podpowiedz").forEach((el) => {
    if (el.closest(".dymek-tresc") || el.matches(".minus, .zostaw")) return;
    if (el.querySelector("input, select, textarea, button, [data-akcja], .minus")) return;
    if (el.textContent.trim().length < DLUGA) return;
    const k = document.createElement("span");
    k.innerHTML = kolko(el.innerHTML);
    const kolkoEl = k.firstElementChild;
    const cel = el.matches("span") ? null : kotwica(el);
    if (cel) { cel.appendChild(kolkoEl); el.remove(); } else el.replaceWith(kolkoEl);
  });
}

// wyzwalacz dymka: kółko „i” albo dowolny element .ma-dymek z ukrytą .dymek-tresc w środku (np. wydarzenie w kalendarzu)
const WYZWALACZ = ".kolko-i, .ma-dymek";

// jeden wspólny dymek (position: fixed) – nie ucina go przewijana tabela ani okno
let dymek = null, przypiety = null;
function pokaz(k) {
  if (!dymek) { dymek = document.createElement("div"); dymek.className = "dymek"; document.body.appendChild(dymek); }
  dymek.innerHTML = k.querySelector(".dymek-tresc")?.innerHTML || "";
  dymek.style.display = "block";
  const r = k.getBoundingClientRect(), d = dymek.getBoundingClientRect();
  const x = Math.min(Math.max(8, r.left + r.width / 2 - d.width / 2), window.innerWidth - d.width - 8);
  const y = r.bottom + 8 + d.height < window.innerHeight ? r.bottom + 8 : Math.max(8, r.top - d.height - 8);
  dymek.style.left = `${x}px`; dymek.style.top = `${y}px`;
}
function schowaj() { if (dymek) dymek.style.display = "none"; przypiety = null; }

document.addEventListener("mouseover", (e) => { const k = e.target.closest?.(WYZWALACZ); if (k && !przypiety) pokaz(k); });
document.addEventListener("mouseout", (e) => {
  const k = e.target.closest?.(WYZWALACZ);
  if (k && !przypiety && !k.contains(e.relatedTarget)) schowaj();
});
document.addEventListener("focusin", (e) => { if (e.target.matches?.(WYZWALACZ)) pokaz(e.target); });
document.addEventListener("focusout", (e) => { if (e.target.matches?.(WYZWALACZ) && !przypiety) schowaj(); });
// klik / dotknięcie przypina dymek (ekrany dotykowe); drugi klik albo klik obok – zamyka
document.addEventListener("click", (e) => {
  const k = e.target.closest?.(WYZWALACZ);
  if (k) { e.preventDefault(); e.stopPropagation(); if (przypiety === k) schowaj(); else { pokaz(k); przypiety = k; } return; }
  if (przypiety && !e.target.closest?.(".dymek")) schowaj();
}, true);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") schowaj(); });
window.addEventListener("scroll", () => { if (!przypiety) schowaj(); }, { passive: true });
