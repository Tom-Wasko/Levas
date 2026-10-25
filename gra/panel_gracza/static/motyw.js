// Wybór wyglądu gry. Ładowany w <head> (bez defer), żeby motyw był ustawiony przed pierwszym rysowaniem strony.
(function () {
  var MOTYWY = [
    ["klasyczny", "Klasyczny REVAS"],
    ["talerze", "Talerze olimpijskie"],
    ["grafik", "Grafik zajęć"],
    ["noc", "Siłownia nocą"],
  ];
  var KLUCZ = "revas-motyw";
  var znane = function (m) { return MOTYWY.some(function (x) { return x[0] === m; }); };
  var motyw = "klasyczny";
  try { motyw = localStorage.getItem(KLUCZ) || motyw; } catch (e) { /* prywatne okno – zostaje domyślny */ }
  var zAdresu = new URLSearchParams(location.search).get("motyw");   // np. /gra/x/Firma?motyw=noc
  if (znane(zAdresu)) {
    motyw = zAdresu;
    try { localStorage.setItem(KLUCZ, motyw); } catch (e) { /* bez zapisu */ }
  }
  if (!znane(motyw)) motyw = "klasyczny";
  document.documentElement.setAttribute("data-motyw", motyw);

  function ustaw(m) {
    if (!znane(m)) return;
    document.documentElement.setAttribute("data-motyw", m);
    try { localStorage.setItem(KLUCZ, m); } catch (e) { /* bez zapisu */ }
    document.dispatchEvent(new CustomEvent("motyw", { detail: m }));
  }

  document.addEventListener("DOMContentLoaded", function () {
    var konto = document.querySelector(".konto");
    if (!konto) return;
    var pole = document.createElement("label");
    pole.className = "wybor-motywu";
    pole.innerHTML = "<span>Wygląd</span><select aria-label=\"Wygląd gry\">" + MOTYWY.map(function (x) {
      return "<option value=\"" + x[0] + "\"" + (x[0] === motyw ? " selected" : "") + ">" + x[1] + "</option>";
    }).join("") + "</select>";
    pole.querySelector("select").addEventListener("change", function (e) { ustaw(e.target.value); });
    konto.appendChild(pole);
  });

  window.ustawMotyw = ustaw;
})();
