"""Zgodność rankingu karty z majątkiem netto w mieszanych grach (graj.py) przy wagach-wykładnikach składowych.
python ana.py katalog [a_zp a_zk a_roz a_zad strata]..."""
import glob
import json
import statistics as st
import sys


def ranga(x):
    o = sorted(range(len(x)), key=lambda i: x[i])
    r = [0] * len(x)
    for k, i in enumerate(o):
        r[i] = k
    return r


def spearman(a, b):
    ra, rb = ranga(a), ranga(b)
    n = len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(ra, rb)) / (n * (n * n - 1))


def karta(rundy, w):
    a_zp, a_zk, a_roz, a_zad, strata = w
    s = []
    for x in rundy[1:]:
        k = x["karta"]
        we = k["wynik_ekonomiczny"]
        if we >= 0:
            s.append(we * k["zadowolenie_pracownikow"] ** a_zp * k["zadowolenie_klientow"] ** a_zk
                     * k["rozwoj_firmy"] ** a_roz * k["wskaznik_zadluzenia"] ** a_zad)
        else:
            s.append(we * strata)
    return sum(s) / len(s)


def ocen(gry, w):
    rho, rho_d, zgod1, kar = [], [], 0, []
    for g in gry:
        n = list(g)
        k = [karta(g[f], w) for f in n]
        m = [g[f][-1]["majatek"] for f in n]
        d = [sum(x["karta"]["wynik_ekonomiczny"] for x in g[f][1:]) for f in n]
        rho.append(spearman(k, m))
        rho_d.append(spearman(k, d))
        zgod1 += max(range(6), key=lambda i: k[i]) == max(range(6), key=lambda i: m[i])
        kar += k
    return st.mean(rho), st.mean(rho_d), zgod1 / len(gry), st.mean(kar)


if __name__ == "__main__":
    gry = [json.load(open(p)) for p in sorted(glob.glob(sys.argv[1] + "/g*.json"))]
    wagi = [tuple(map(float, x.split(","))) for x in sys.argv[2:]] or [(1, 1, 1, 1, 1)]
    print(f"{len(gry)} gier")
    for w in wagi:
        r, rd, z1, sk = ocen(gry, w)
        print(w, f"spearman karta~majątek {r:.3f}, karta~dochód {rd:.3f}, ten sam 1. {z1:.0%}, karta śr. {sk:.3f}")
