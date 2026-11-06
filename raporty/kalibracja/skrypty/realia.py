"""Realia (B15): 6 botów (domyślnie średnich, argument: poziom, np. czlowiek_sredni), 18 rund, ziarna 7 i 11, rundy 3–18, wszystkie firmy (jak B4, tabela 6).
Uruchamiać z katalogu gra/ (bieżącego albo wypakowanego z tagu kalibracja-start)."""
import collections
import re
import sys

POZ = sys.argv[1] if len(sys.argv) > 1 else None

from silnik.gra import Gra

STRAT = ["zrownowazony", "tani", "premium", "agresywny", "nasladowca", "zrownowazony"]
GLOWNE = ("kebab_w_bulce", "kebab_w_tortilli", "talerz_kebab", "kebab_box", "falafel", "rollo")
s = collections.Counter()
opisy = collections.Counter()
lokale = []
for z in (7, 11):
    g = Gra.nowa("t", [(c, x) for c, x in zip("ABCDEF", STRAT)], 18, z, **({"poziomy": dict.fromkeys("ABCDEF", POZ)} if POZ else {}))
    for _ in range(18):
        g.przelicz(wymus=True)
    st = g.stan()
    for f in st.firmy.values():
        lokale.append(len(getattr(f, "lokale", []) or []))
    for r in range(3, 19):
        for f, w in st.wyniki[r].items():
            k = w["kpir"]
            s["przychody"] += k["przychody"]
            s["towary"] += k["towary"]
            s["wynagrodzenia"] += k["wynagrodzenia"]
            s["pozostale"] += k["pozostale"]
            s["netto"] += k["dochod_netto"]
            s["fr"] += 1
            for p in k["pozycje"]:
                klucz = re.sub(r"[:(–-].*", "", p["opis"]).strip()[:40]
                opisy[klucz] += p.get("pozostale", 0) + p.get("wynagrodzenia", 0)
            for d, x in w["sprzedaz"].items():
                if d in GLOWNE and isinstance(x, dict):
                    s["glowne"] += x["sprzedaz"]
                    s["glowne_zl"] += x["sprzedaz"] * x["cena_po_rabacie"]
P = s["przychody"]
print(f"marża netto {s['netto'] / P:.1%}, towary {s['towary'] / P:.1%}, wynagrodzenia {s['wynagrodzenia'] / P:.1%}, "
      f"pozostałe {s['pozostale'] / P:.1%}")
print(f"przychód firmy na tydzień {P / s['fr']:.0f} zł, lokale na koniec {lokale}")
print(f"cena dania głównego po rabacie {s['glowne_zl'] / s['glowne']:.2f} zł, dań głównych na firmę dziennie "
      f"{s['glowne'] / s['fr'] / 7:.0f}")
for o, v in opisy.most_common(25):
    print(f"  {o:40s} {v / P:6.1%}")
