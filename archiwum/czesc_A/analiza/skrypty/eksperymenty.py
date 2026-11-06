"""A2, persona 2 – optymalizator: porównanie strategii na tych samych ziarnach (silnik bez API).

Każdy wariant to pełna gra 18 rund: firma „Optima” + 3 boty (trudny, jak człowiek – dobry, średni).
Decyzje Optimy: kalkulator (planista botów, poziom czlowiek_dobry) + zmiana z wariantu.
Miary: karta skumulowana (średni wynik działalności rund 2–18, jak ranking), miejsce,
majątek netto po 18. rundzie.

Uruchomienie: python -X utf8 eksperymenty.py [ziarno ...]  → archiwum/czesc_A/analiza/eksperymenty.json
"""

from __future__ import annotations

import copy
import json
import sys
import time

from gracz import ANALIZA, _json  # noqa: F401 – najpierw: ustawia Django i ścieżki

from api.prezentacja import _majatek_netto, karta_skumulowana, miejsca
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.limity import naruszenia

F = "Optima"
FIRMY = [(F, None), ("Gigant", "agresywny"), ("Bafra", "zrownowazony"), ("Kopiuj", "nasladowca")]
POZIOMY = {"Gigant": "trudny", "Bafra": "czlowiek_dobry", "Kopiuj": "sredni"}


def plan(g: Gra, strategia="zrownowazony", poziom="czlowiek_dobry", **zmiany_poziomu) -> dict:
    konf = copy.deepcopy(g.konfiguracja)
    for f in konf["firmy"]:
        if f["nazwa"] == F:
            f["poziom"] = poziom
    if zmiany_poziomu:   # g.dane to osobna kopia danych tej gry (rozegraj)
        g.dane.boty["poziomy"][poziom] = {**g.dane.boty["poziomy"][poziom], **zmiany_poziomu}
    return _json(decyzje_bota(g.dane, g.stan(g.runda - 1), F, strategia, g.runda, konf))


def ceny(d: dict, mnoznik: float) -> dict:
    for x in (d.get("sprzedaz") or {}).values():
        x["cena"] = round(x["cena"] * mnoznik, 1)
    return d


def strefa(g: Gra) -> str | None:
    f = g.stan(g.runda - 1).firmy[F]
    return g.dane.lokale[f.lokale[0].id]["strefa"] if f.lokale else None


# --- warianty: funkcja (gra) -> decyzje Optimy ---------------------------------------------------
def baza(g):
    return plan(g)


def planista_trudny(g):
    return plan(g, poziom="trudny")


def drogo(g):
    return ceny(plan(g), 1.3)


def tanio(g):
    return ceny(plan(g), 0.8)


def premium(g):
    return plan(g, strategia="premium")


def tani_kebab(g):
    return plan(g, strategia="tani")


def agresywny(g):
    return plan(g, strategia="agresywny")


def ekspansja(g):
    """Kolejny lokal co 3 rundy, gdy jest gotówka – planista trudny z limitem 4 lokali."""
    return plan(g, poziom="trudny",
                kolejny_lokal={"obsluga": 0.7, "gotowka": 30000, "maks_lokali": 4})


def ekspansja_na_kredyt(g):
    d = plan(g, poziom="trudny", kolejny_lokal={"obsluga": 0.7, "gotowka": 30000, "maks_lokali": 4})
    if g.runda == 1:   # kredyt na start bez historii firmy
        d["kredyty_wez"] = [{"kwota": 50000, "rund": 52, "bank": "Crédit Agricole",
                             "produkt": "start"}]
    return d


def bez_lokalu_lokata(g):
    """Zdegenerowana: nie otwiera lokalu, gotówka na 13-rundowej lokacie w ING (dwa razy)."""
    d = {"bank": "ING", "biuro": "samodzielnie"}
    if g.runda in (1, 14):
        got = g.stan(g.runda - 1).firmy[F].gotowka
        d["lokaty_zaloz"] = [{"kwota": round(got - 2000, -2), "rund": 13, "bank": "ING"}]
    return d


def lokal_i_zamkniecie(g):
    """Do rundy 10 normalnie, potem zwalnia wszystkich i nic nie zamawia (koszty stałe zostają)."""
    if g.runda <= 10:
        return plan(g)
    f = g.stan(g.runda - 1).firmy[F]
    return {"zatrudnij": [], "zamowienia": [], "zwolnij": list(f.pracownicy)} \
        if g.runda == 11 else {"zatrudnij": [], "zamowienia": []}


def wyplaty(g):
    """Co rundę wypłaca do portfela właściciela gotówkę ponad 25 000 zł."""
    d = plan(g)
    got = g.stan(g.runda - 1).firmy[F].gotowka
    if g.runda >= 3 and got > 25000:
        d["wyplata_wlasna"] = round(got - 25000, 2)
    return d


def harpagon_dzwignia(g):
    """Bierze maksimum od Harpagona w rundzie 1 i spłaca w terminie (pożyczka poza KPiR)."""
    d = plan(g)
    if g.runda == 1:
        d["harpagon_wez"] = 20000
    if g.runda == 5:
        d["harpagon_splac"] = 25000
    return d


def niskie_pensje(g):
    d = plan(g)
    for z in d.get("zatrudnij", []):
        z["pensja"] = 4806   # płaca minimalna
    return d


def max_reklama(g):
    d = plan(g)
    s = strefa(g)
    if s and g.runda >= 3:
        d["kampanie"] = [{"agencja": a, "kanal": k, "strefa": s, "emisje": 10} for a, k in
                         (("papier_przyjmie", "ulotki"), ("papier_przyjmie", "plakaty"))]
    return d


def nic_z_biurem(g):
    """Jak bez_lokalu_lokata, ale z najtańszym biurem (bez mandatów za brak deklaracji)."""
    d = bez_lokalu_lokata(g)
    d["biuro"] = min(g.dane.mapa["biura"]["biura"], key=lambda b: b.get("ryczalt") or 0)["id"]
    return d


def premium_ekspansja(g):
    return plan(g, strategia="premium", poziom="trudny",
                kolejny_lokal={"obsluga": 0.7, "gotowka": 30000, "maks_lokali": 4})


def premium_drogo(g):
    return ceny(plan(g, strategia="premium"), 1.2)


WARIANTY = [baza, planista_trudny, drogo, tanio, premium, tani_kebab, agresywny, ekspansja,
            ekspansja_na_kredyt, bez_lokalu_lokata, lokal_i_zamkniecie, wyplaty, harpagon_dzwignia,
            niskie_pensje, max_reklama, nic_z_biurem, premium_ekspansja, premium_drogo]


def rozegraj(wariant, ziarno: int) -> dict:
    g = Gra.nowa(f"eksp-{wariant.__name__}", FIRMY, 18, ziarno, dane=copy.deepcopy(dane_domyslne()),
                 poziomy=POZIOMY)
    odrzucone = []
    for _ in range(18):
        d = wariant(g)
        bledy = naruszenia(g.dane, g.stan().firmy[F], d, g.runda)
        if bledy:
            odrzucone.append({"runda": g.runda, "bledy": bledy})
            d = plan(g)
        g.ustaw_decyzje(F, d)
        g.wyslij(F)
        g.przelicz()
    skum = karta_skumulowana(g, 18)
    m = miejsca(skum)
    st = g.stan(18)
    wyn = {n: {"wynik": skum.get(n, {}).get("wynik_dzialalnosci"), "miejsce": m.get(n),
               "majatek_netto": _majatek_netto(st.wyniki[18].get(n)),
               "dochod_suma": round(sum(st.wyniki[r][n]["kpir"]["dochod_netto"]
                                        for r in range(1, 19) if n in st.wyniki.get(r, {})), 2),
               "lokale": len(st.firmy[n].lokale)} for n, _ in FIRMY}
    return {"wariant": wariant.__name__, "ziarno": ziarno, "firmy": wyn, "karta": skum.get(F),
            "odrzucone": odrzucone}


def main():
    wybrane = [a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--warianty=")]
    ziarna = [int(x) for x in sys.argv[1:] if x.isdigit()] or [202, 203, 204]
    plik = ANALIZA / ("eksperymenty_dodatkowe.json" if wybrane else "eksperymenty.json")
    wyniki = []
    for z in ziarna:
        for w in [w for w in WARIANTY if not wybrane or w.__name__ in wybrane[0]]:
            t = time.time()
            try:
                x = rozegraj(w, z)
            except Exception as e:  # noqa: BLE001 – wariant, który wywraca grę, też jest wynikiem
                x = {"wariant": w.__name__, "ziarno": z, "wyjatek": repr(e)}
            wyniki.append(x)
            o = x.get("firmy", {}).get(F, {})
            print(f"{z} {w.__name__:22s} wynik={o.get('wynik')} miejsce={o.get('miejsce')} "
                  f"majatek={o.get('majatek_netto')} odrzucone={len(x.get('odrzucone', []))} "
                  f"{x.get('wyjatek', '')} {time.time() - t:.0f}s", flush=True)
            plik.write_text(
                json.dumps(wyniki, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
