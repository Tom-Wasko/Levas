"""Przebieg gry badanej (gotówka, debet, wypadki) – python alarm.py strategia poziom ziarno [polisy,...|-]"""
import sys
from balans import warianty as wa
from silnik.boty import decyzje_bota
st, po, z = sys.argv[1], sys.argv[2], int(sys.argv[3])
k = wa.Kontekst(strategia=st, poziom=po, rywale="sredni")
w = wa.Wariant("x", "x", strategia=(("polisy", [] if sys.argv[4] == "-" else sys.argv[4].split(",")),)) \
    if len(sys.argv) > 4 else wa.Wariant("baza", "baza")
fs = wa.firmy(k, z, list(wa.dane_domyslne().boty["strategie"]))
g = wa.Gra.nowa("w", fs, 18, z, poziomy={n: po if n == wa.BADANA else "sredni" for n, _ in fs},
                dane=wa.dane_ze_zmianami(""), kasyno_botow=True)
db = wa._dane_badanej(g.dane, st, po, dict(w.strategia), {})
for r in range(1, 19):
    g.ustaw_decyzje(wa.BADANA, wa._wymus(w, decyzje_bota(db, g.stan(r - 1), wa.BADANA, st, r, g.konfiguracja)))
    s = g.przelicz(wymus=True)
    x = s.wyniki[r][wa.BADANA]
    print(r, round(x["gotowka"]), x["bank"]["debet_ponad_limit"], x.get("alarm"),
          [o for o in x.get("wypadki", [])] if isinstance(x.get("wypadki"), list) else "")
