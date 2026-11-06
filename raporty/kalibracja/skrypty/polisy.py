"""Składki, szkody i odszkodowania wg rodzaju polisy – wszystkie boty z kompletem polis."""
import copy, sys, collections
from silnik.gra import Gra
from silnik.swiat import awarie as aw
import re
S = collections.defaultdict(float)
RODZ = {m[1]: m[0] for m in re.findall(r"typ: szkoda, kwota: \d+, polisa: (\w+), opis: ([^}]+)}",
                                        open("dane/zdarzenia/losowe.yaml", encoding="utf8").read())}
gier = 0
for z in range(1000, 1000 + int(sys.argv[1])):
    g = Gra.nowa("p", [(c, s) for c, s in zip("ABCDEF", ["zrownowazony", "tani", "premium"] * 2)], 18, z)
    d = copy.copy(g.dane); st = d.boty["strategie"]
    pol = list(d.zdarzenia["losowe"]["ubezpieczyciel"]["polisy"])
    d.boty = {**d.boty, "strategie": {k: {**v, "polisy": pol} for k, v in st.items()}}
    g.dane = d
    for _ in range(18):
        g.przelicz(wymus=True)
    for w in g.stan().wyniki.values():
        for f, x in w.items():
            for o in x.get("rachunek", []):
                op = o["opis"]
                for k in ("Składka", "Szkoda", "Odszkodowanie"):
                    if op.startswith(k):
                        rodz = op.split(": ")[-1] if k == "Składka" else RODZ.get(op.split(": ", 1)[-1], "?")
                        S[(k, rodz)] += o["kwota"]
    gier += 6
for k, v in sorted(S.items()):
    print(k, round(v / gier))
