"""Ludzie badanej: python ludzie.py strategia ziarno wariant [wariant2 ...] – zadowolenie, odejścia, karta"""
import statistics, sys
from balans import warianty as W
st, z = sys.argv[1], int(sys.argv[2])
kat = W.katalog_wariantow(W.dane_domyslne())
for wn in (W.BAZA, *sys.argv[3:]):
    k = W.Kontekst(strategia=st, rund=18)
    w = kat[wn] if wn in kat else W.Wariant(wn)
    fs = W.firmy(k, z, list(W.dane_domyslne().boty["strategie"]))
    g = W.Gra.nowa("warianty", fs, k.rund, z, poziomy={n: k.poziom for n, _ in fs}, dane=W.dane_ze_zmianami(k.dane))
    db = W._dane_badanej(g.dane, k.strategia, k.poziom, dict(w.strategia), dict(w.poziom))
    zp, wd, odej, zat, prac, zad_os = [], [], 0, 0, [], []
    for r in range(1, k.rund + 1):
        d = W._wymus(w, W.decyzje_bota(db, g.stan(r - 1), W.BADANA, k.strategia, r, g.konfiguracja))
        g.ustaw_decyzje(W.BADANA, d); s = g.przelicz(wymus=True)
        wy = s.wyniki[r][W.BADANA]
        kt = wy.get("karta") or {}
        zp.append(kt.get("zadowolenie_pracownikow", 0)); wd.append(kt.get("wynik_dzialalnosci", 0))
        odej += len(wy.get("odejscia") or wy.get("wypowiedzenia_pracownikow") or [])
        zat += len(d.get("zatrudnij", []))
        prac.append(len(s.firmy[W.BADANA].pracownicy))
        for x in (wy.get("zadowolenie_osob") or []):
            if isinstance(x, dict) and "zadowolenie" in x: zad_os.append(x["zadowolenie"])
    print(f"{wn:18} karta {statistics.mean(wd):.3f} zp {statistics.mean(zp):.3f} odejscia {odej} zatrudnieni {zat}"
          f" prac {statistics.mean(prac):.1f}" + (f" zad_os min {min(zad_os):.3f} sr {statistics.mean(zad_os):.3f}" if zad_os else "")
          + f" klucze {[a for a in wy if 'odej' in a or 'zadow' in a or 'wypow' in a]}")
