"""B13: mieszane gry 6 firm (strategie × poziomy); per firma i runda – składowe karty i miary kebabowe.
python graj.py katalog ziarno_od ziarno_do procesy"""
import json
import random
import sys
from multiprocessing import Pool
from pathlib import Path

from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.wyniki.majatek import z_portfelem

POZIOMY = ["czlowiek_slaby", "czlowiek_sredni", "czlowiek_dobry", "latwy", "sredni", "trudny"]
KAT = Path(sys.argv[1])


def gra(z: int):
    plik = KAT / f"g{z}.json"
    if plik.exists():
        return
    rng = random.Random(z)
    st = list(dane_domyslne().boty["strategie"])
    st = st + [rng.choice(st)]
    rng.shuffle(st)
    po = POZIOMY[:]
    rng.shuffle(po)
    fs = [(f"F{i}_{s}_{p}", s) for i, (s, p) in enumerate(zip(st, po))]
    g = Gra.nowa("b13", fs, 18, z, poziomy={n: p for (n, _), p in zip(fs, po)})
    for _ in range(18):
        s = g.przelicz(wymus=True)
    out = {}
    for n in s.firmy:
        rundy = []
        for r in range(1, 19):
            w = s.wyniki[r][n]
            rundy.append({"karta": w.get("karta"), "kebab": w.get("karta_kebab"),
                          "netto": w["kpir"]["dochod_netto"], "gotowka": w["gotowka"],
                          "majatek": z_portfelem(w),
                          "mandaty": [o for o in (w.get("urzad") or {}).keys()],
                          "ksiegowosc": (w.get("ksiegowosc") or {}).get("kara")})
        out[n] = rundy
    plik.write_text(json.dumps(out), encoding="utf8")


if __name__ == "__main__":
    KAT.mkdir(exist_ok=True)
    with Pool(int(sys.argv[4])) as p:
        for i, _ in enumerate(p.imap_unordered(gra, range(int(sys.argv[2]), int(sys.argv[3])))):
            print(i, flush=True)
