"""Pary wariant/baza z kolumną `skladowe` (wsk.py): Δ karty przeliczonej z wagami vs Δ majątku.
python pary.py katalog [a_zp,a_zk,a_roz,a_zad,strata ...]  (-v: tabela wariantów)"""
import collections
import csv
import json
import statistics as st
import sys

csv.field_size_limit(10**8)


def karta(sk, w):
    a_zp, a_zk, a_roz, a_zad, strata = w
    return sum(we * zp ** a_zp * zk ** a_zk * roz ** a_roz * zad ** a_zad if we >= 0 else we * strata
               for we, zp, zk, roz, zad in sk) / len(sk)


def przedzial(x):
    return st.mean(x), (1.96 * st.stdev(x) / len(x) ** 0.5 if len(x) > 1 else 0)


def znak(m, e):
    return (m - e > 0) - (m + e < 0)


def main():
    kat = sys.argv[1]
    v = "-v" in sys.argv
    wagi = [tuple(map(float, a.split(","))) for a in sys.argv[2:] if a != "-v"] or [(1, 1, 1, 1, 1)]
    g = list(csv.DictReader(open(f"{kat}/gry.csv", encoding="utf8")))
    for x in g:
        x["sk"] = json.loads(x["skladowe"])
    baza = {(x["kontekst"], x["ziarno"]): x for x in g if x["wariant"] == "baza"}
    for w in wagi:
        d = collections.defaultdict(list)
        for x in g:
            b = baza.get((x["kontekst"], x["ziarno"]))
            if x["wariant"] == "baza" or not b:
                continue
            d[x["wariant"]].append((karta(x["sk"], w) - karta(b["sk"], w), float(x["majatek"]) - float(b["majatek"])))
        konfl, zgodne, wszystkie, rows = [], 0, 0, []
        for nazwa, p in sorted(d.items()):
            dk, ek = przedzial([a for a, _ in p])
            dm, em = przedzial([b for _, b in p])
            ks, ms = znak(dk, ek), znak(dm, em)
            zgodne += sum((a > 0) == (b > 0) for a, b in p if abs(a) > 1e-4 and abs(b) > 1)
            wszystkie += sum(1 for a, b in p if abs(a) > 1e-4 and abs(b) > 1)
            flag = "KONFLIKT" if ks * ms < 0 else ("karta bez majątku" if ks and not ms else "")
            if flag:
                konfl.append(nazwa)
            rows.append(f"  {nazwa:24s} Δkarta {dk:+.3f} ± {ek:.3f}  wygr {sum(a > 0 for a, _ in p) / len(p):4.0%}  "
                        f"Δmaj {dm / 1000:+6.1f} ± {em / 1000:4.1f} tys.  {flag}")
        print(w, f"pary zgodne co do znaku {zgodne}/{wszystkie} = {zgodne / max(1, wszystkie):.0%}; konflikty: {konfl}")
        if v:
            print("\n".join(rows))


main()
