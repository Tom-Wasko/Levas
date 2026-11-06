"""Przebieg gry badanej: gotówka, debet, dochód i największe wydatki – python alarm2.py strategia poziom ziarno [rund]"""
import sys
from balans import warianty as wa
from silnik.boty import decyzje_bota
st, po, z = sys.argv[1], sys.argv[2], int(sys.argv[3])
R = int(sys.argv[4]) if len(sys.argv) > 4 else 8
k = wa.Kontekst(strategia=st, poziom=po, rywale="sredni")
fs = wa.firmy(k, z, list(wa.dane_domyslne().boty["strategie"]))
g = wa.Gra.nowa("w", fs, 18, z, poziomy={n: po if n == wa.BADANA else "sredni" for n, _ in fs},
                dane=wa.dane_ze_zmianami(""))
db = wa._dane_badanej(g.dane, st, po, {}, {})
for r in range(1, R + 1):
    d = decyzje_bota(db, g.stan(r - 1), wa.BADANA, st, r, g.konfiguracja)
    g.ustaw_decyzje(wa.BADANA, d)
    s = g.przelicz(wymus=True)
    x = s.wyniki[r][wa.BADANA]
    poz = sorted(x["kpir"].get("pozycje", []), key=lambda p: -abs(p.get("kwota", 0)))[:6]
    print(r, "gotówka", round(x["gotowka"]), "ponad limit", x["bank"]["debet_ponad_limit"], "netto", round(x["kpir"]["dochod_netto"]),
          "| klucze decyzji:", sorted(k for k, v in d.items() if v))
    print("    ", [(p.get("opis") or p.get("nazwa"), round(p.get("kwota", 0))) for p in poz])
