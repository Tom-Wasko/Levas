"""Agencja pracy w grze z lokalami (F3a.8): globalna pula, kanały rekrutacji, limit nowych, licytacje, podkupienia.

Dane: dane/kandydaci.yaml – agencja (kanały pracuj.pl / agencja pracy / headhunter, limit, okresy wypowiedzenia).
- Pula jest wspólna: zatrudniony kandydat znika z puli, zwolniony pracownik do niej wraca.
- Kandydata widać w kanale, gdy kanał jest odblokowany i obejmuje jego gwiazdki. Bez wskazanego kanału zatrudnienie
  idzie najtańszym (w złotych) kanałem, na który starcza czasu właściciela.
- Najwyżej `limit_nowych` nowych pracowników na rundę (zatrudnienia + oferty podkupienia).
- Licytacja: kilka firm zatrudnia tę samą osobę w tej samej rundzie → wygrywa wyższa pensja, przy remisie losowanie.
- Podkupienie (tylko przez headhuntera): oferta dla pracownika innej firmy; obecny pracodawca może złożyć kontrofertę
  w tej samej rundzie. Pracownik przyjmuje najlepszą ofertę, jeśli jest wyższa od jego pensji i od kontroferty;
  wygrana kontroferta podnosi mu pensję. Umowa zlecenie – przejście od razu, umowa o pracę – po okresie
  wypowiedzenia. Pracownika w okresie wypowiedzenia nie można zwolnić ani podkupić.
- Okres wypowiedzenia (P6): jedna długość z danych (2 rundy) w obie strony – zwolniony pracownik na umowie o pracę
  pracuje i dostaje pensję jeszcze przez okres wypowiedzenia, potem wraca do puli (`Odejscie` z pustym `do`).

Kolejność w rundzie (silnik/runda.py): `przed_decyzjami` (limit, licytacje, podkupienia) → decyzje firm
(`zastosuj`: kanał, koszt, czas właściciela) → `po_decyzjach` (przejścia pracowników, opłaty headhuntera).
"""
from __future__ import annotations

from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Firma, Odejscie, Pracownik, StanGry

HEADHUNTER = "headhunter"


def ustawienia(dane: Dane) -> dict:
    return dane.rynek_pracy["agencja"]


def kanaly(dane: Dane, runda: int) -> dict[str, dict]:
    """Kanały rekrutacji z flagą `dostepny` w tej rundzie (kolejność jak w danych)."""
    return {n: {**k, "dostepny": k["od_rundy"] <= runda} for n, k in ustawienia(dane)["kanaly"].items()}


def koszt(dane: Dane, kanal: str, kandydat: dict) -> float:
    k = ustawienia(dane)["kanaly"][kanal]
    return k["oplata"] + k["mnoznik_rekrutacji"] * kandydat["koszt_rekrutacji"]


def kanaly_kandydata(dane: Dane, kandydat: dict, runda: int) -> list[str]:
    """Odblokowane kanały, w których widać kandydata – od najtańszego."""
    ok = [n for n, k in kanaly(dane, runda).items() if k["dostepny"] and kandydat["gwiazdki"] in k["gwiazdki"]]
    return sorted(ok, key=lambda n: koszt(dane, n, kandydat))


def widoczni(dane: Dane, pula: list[dict], runda: int) -> list[dict]:
    return [k for k in pula if kanaly_kandydata(dane, k, runda)]


def staz(p: Pracownik, runda: int) -> int:
    return max(0, runda - p.od_rundy)


def okres_wypowiedzenia(dane: Dane, p: Pracownik, runda: int) -> int:
    """Rundy do odejścia: umowa zlecenie 0, umowa o pracę wg danych (jedna długość, wpisy wg stażu – na przyszłość)."""
    if p.umowa != "prace":
        return 0
    s = staz(p, runda)
    return max((w["rund"] for w in ustawienia(dane)["wypowiedzenie"] if s >= w["staz_od"]), default=0)


def headhunter_dostepny(dane: Dane, runda: int) -> bool:
    return kanaly(dane, runda)[HEADHUNTER]["dostepny"]


def jako_kandydat(p: Pracownik) -> dict:
    """Pracownik wracający do puli (zwolniony albo bez stanowiska w nowej firmie)."""
    return {"id": p.id, "imie_nazwisko": p.imie_nazwisko, "gwiazdki": p.gwiazdki, "zawod": p.zawod,
            "pensja_preferowana": p.pensja_preferowana, "koszt_rekrutacji": p.koszt_rekrutacji,
            "koszt_odprawy": p.koszt_odprawy, "zadowolenie_klientow": p.zadowolenie_klientow,
            "ryzyko_reklamacji": p.ryzyko_reklamacji}


def _raport() -> dict:
    return {"zatrudnieni": [], "licytacje": [], "ponad_limit": [], "oferty_zlozone": [], "oferty_otrzymane": [],
            "odejscia": [], "przyjscia": [], "uwagi": []}


def przed_decyzjami(dane: Dane, s: StanGry, decyzje: dict[str, dict], runda: int, ziarno) -> tuple[dict, dict, dict]:
    """Limit nowych, licytacje kandydatów i oferty podkupienia. Zwraca (decyzje po filtrze, rezerwacje kandydatów
    {id: firma}, raporty firm). Wygrane kontroferty podnoszą pensje, przyjęte oferty ustawiają `odchodzi`."""
    limit = ustawienia(dane)["limit_nowych"]
    placa_min = dane.z["finanse"]["placa_minimalna"]
    raport = {n: _raport() for n in s.firmy}
    nowe = {}
    for n in s.firmy:
        d = dict(decyzje.get(n, {}))
        zatr = list(d.get("zatrudnij") or [])
        podk = [o for o in (d.get("podkup") or []) if o.get("firma") != n]
        nadmiar = (zatr + podk)[limit:]
        if nadmiar:
            raport[n]["ponad_limit"] = nadmiar
            raport[n]["uwagi"].append(f"Najwyżej {limit} nowych pracowników na rundę (zatrudnienia i oferty podkupienia) "
                                      f"– {len(nadmiar)} odrzucone.")
        d["zatrudnij"] = zatr[:limit]
        d["podkup"] = podk[: max(0, limit - len(zatr))]
        if d.get("zwolnij"):
            f = s.firmy[n]
            w_wypowiedzeniu = [pid for pid in d["zwolnij"] if pid in f.pracownicy and f.pracownicy[pid].odchodzi]
            if w_wypowiedzeniu:
                d["zwolnij"] = [pid for pid in d["zwolnij"] if pid not in w_wypowiedzeniu]
                raport[n]["uwagi"].append("Pracownik w okresie wypowiedzenia odchodzi sam – nie można go zwolnić.")
        nowe[n] = d

    # licytacje: ta sama osoba z puli u kilku firm
    pula = {k["id"]: k for k in s.kandydaci}
    oferty: dict[str, list[tuple[float, str]]] = {}
    for n in sorted(nowe):
        for z in nowe[n]["zatrudnij"]:
            if z.get("kandydat") in pula:
                pensja = float(z.get("pensja") or pula[z["kandydat"]]["pensja_preferowana"])
                oferty.setdefault(z["kandydat"], []).append((pensja, n))
    rezerwacje = {}
    for kid, lista in sorted(oferty.items()):
        najwyzsza = max(p for p, _ in lista)
        najlepsi = sorted({n for p, n in lista if p == najwyzsza})
        wygral = najlepsi[int(strumien(ziarno, runda, "rynek_pracy", "licytacja", kid).integers(len(najlepsi)))] \
            if len(najlepsi) > 1 else najlepsi[0]
        rezerwacje[kid] = wygral
        if len({n for _, n in lista}) < 2:
            continue
        for p, n in lista:
            raport[n]["licytacje"].append({"kandydat": kid, "imie_nazwisko": pula[kid]["imie_nazwisko"], "pensja": p,
                                           "najwyzsza": najwyzsza, "wygrana": n == wygral, "remis": len(najlepsi) > 1})
            if n != wygral:
                # przegrana licytacja: bot (zastepca) zatrudni kogoś podobnego, gracz – nikogo
                nowe[n]["zatrudnij"] = [z for z in nowe[n]["zatrudnij"] if z.get("kandydat") != kid or z.get("zastepca")]
                raport[n]["uwagi"].append(f"{pula[kid]['imie_nazwisko']}: licytację wygrała inna firma "
                                          f"(najwyższa pensja {najwyzsza:.0f} zł).")

    # podkupienia
    hh = headhunter_dostepny(dane, runda)
    do_pracownika: dict[tuple[str, str], list[dict]] = {}
    for n in sorted(nowe):
        for o in nowe[n]["podkup"]:
            cel = s.firmy.get(o.get("firma"))
            p = cel.pracownicy.get(o.get("pracownik")) if cel else None
            pensja = float(o.get("pensja") or 0)
            wpis = {"pracownik": o.get("pracownik"), "firma": o.get("firma"), "pensja": pensja,
                    "umowa": o.get("umowa", "prace"), "imie_nazwisko": p.imie_nazwisko if p else "?"}
            powod = ("headhunter od rundy " + str(kanaly(dane, runda)[HEADHUNTER]["od_rundy"]) if not hh
                     else "pracownika już nie ma" if p is None
                     else "pracownik jest w okresie wypowiedzenia" if p.odchodzi
                     else f"pensja poniżej płacy minimalnej ({placa_min:.0f} zł)" if pensja < placa_min else None)
            if powod:
                raport[n]["oferty_zlozone"].append({**wpis, "wynik": "nieważna", "powod": powod})
                raport[n]["uwagi"].append(f"Oferta dla {wpis['imie_nazwisko']} nieważna: {powod}.")
                continue
            do_pracownika.setdefault((o["firma"], o["pracownik"]), []).append({**wpis, "od": n})
    for (firma, pid), lista in sorted(do_pracownika.items()):
        f = s.firmy[firma]
        p = f.pracownicy[pid]
        kontra = float((nowe[firma].get("kontroferty") or {}).get(pid) or 0)
        najwyzsza = max(o["pensja"] for o in lista)
        najlepsi = [o for o in lista if o["pensja"] == najwyzsza]
        best = najlepsi[int(strumien(ziarno, runda, "rynek_pracy", "podkupienie", pid).integers(len(najlepsi)))] \
            if len(najlepsi) > 1 else najlepsi[0]
        przyjeta = najwyzsza > max(p.pensja, kontra)
        okres = okres_wypowiedzenia(dane, p, runda)
        if przyjeta:
            p.odchodzi = Odejscie(do=best["od"], runda=runda + okres, pensja=best["pensja"], umowa=best["umowa"],
                                  od_rundy=runda)
        elif kontra >= najwyzsza and kontra > p.pensja:
            p.pensja = kontra
        wynik_pr = "odchodzi" if przyjeta else "kontroferta" if kontra >= najwyzsza else "odrzucona"
        raport[firma]["oferty_otrzymane"].append({
            "pracownik": pid, "imie_nazwisko": p.imie_nazwisko, "od": sorted({o["od"] for o in lista}), "najwyzsza": najwyzsza,
            "kontroferta": kontra or None, "wynik": wynik_pr, "do": best["od"] if przyjeta else None,
            "runda_odejscia": runda + okres if przyjeta else None})
        for o in lista:
            wygrana = przyjeta and o is best
            raport[o["od"]]["oferty_zlozone"].append({
                **{k: v for k, v in o.items() if k != "od"},
                "wynik": "przyjeta" if wygrana else "kontroferta" if wynik_pr == "kontroferta"
                else "inna_firma" if przyjeta else "odrzucona",
                "runda_przejscia": runda + okres if wygrana else None})
    return nowe, rezerwacje, raport


def pula_dla(pula: list[dict], rezerwacje: dict[str, str], firma: str) -> list[dict]:
    """Kandydaci dostępni dla firmy w tej rundzie: bez tych, których licytację wygrała inna firma."""
    return [k for k in pula if rezerwacje.get(k["id"], firma) == firma]


def wolne_stanowisko(dane: Dane, f: Firma, zawod: str):
    typ = dane.typ_zawodu(zawod)
    return next((st for st in sorted(f.stanowiska_typu(typ), key=lambda st: st.nr) if not st.pracownik), None)


def po_decyzjach(dane: Dane, s: StanGry, runda: int, raport: dict, ksiegi: dict[str, Ksiega],
                 rachunki: dict[str, Rachunek]) -> None:
    """Przejścia pracowników, których okres wypowiedzenia minął (i zleceniobiorców od razu), oraz opłaty headhuntera
    za oferty przyjęte w tej rundzie. Nowa firma bez wolnego stanowiska – pracownik wraca do puli."""
    czesc = ustawienia(dane)["kanaly"][HEADHUNTER]["podkupienie_czesc_pensji"]
    for n in sorted(s.firmy):
        f = s.firmy[n]
        for pid in sorted(f.pracownicy):
            p = f.pracownicy[pid]
            o = p.odchodzi
            if not o:
                continue
            if o.od_rundy == runda and o.do in s.firmy:   # opłata headhuntera przy przyjęciu oferty
                ksieguj(s.firmy[o.do], ksiegi[o.do], rachunki[o.do], f"Headhunter: podkupienie {p.imie_nazwisko}",
                        o.pensja * czesc)
            if o.runda > runda:
                continue
            del f.pracownicy[pid]
            st = f.stanowisko(dane.typ_zawodu(p.zawod), p.stanowisko)
            if st and st.pracownik == pid:
                st.pracownik = None
            raport[n]["odejscia"].append({"pracownik": pid, "imie_nazwisko": p.imie_nazwisko, "do": o.do})
            nowa = s.firmy.get(o.do)
            st_n = wolne_stanowisko(dane, nowa, p.zawod) if nowa else None
            if st_n is None:
                s.kandydaci.append(jako_kandydat(p))
                if nowa:
                    raport[o.do]["uwagi"].append(f"{p.imie_nazwisko}: brak wolnego stanowiska w dniu przejścia "
                                                 "– osoba wraca do puli kandydatów.")
                continue
            nowy = p.model_copy(update={"pensja_gr": 0, "odchodzi": None, "od_rundy": runda, "stanowisko": st_n.nr,
                                        "premia_gr": 0, "umowa": o.umowa})
            nowy.pensja = o.pensja
            nowa.pracownicy[pid] = nowy
            st_n.pracownik = pid
            raport[o.do]["przyjscia"].append({"pracownik": pid, "imie_nazwisko": p.imie_nazwisko, "od": n,
                                              "stanowisko": st_n.nr})


def oferty_dla(gra_decyzje: dict[str, dict], firma: Firma, nazwa: str) -> list[dict]:
    """Bieżące (zapisane) oferty innych firm dla pracowników `firma` – do kontroferty w zakładce Rynek pracy."""
    wynik = []
    for od, d in sorted(gra_decyzje.items()):
        if od == nazwa or od.startswith("_"):
            continue
        for o in d.get("podkup") or []:
            p = firma.pracownicy.get(o.get("pracownik")) if o.get("firma") == nazwa else None
            if p and not p.odchodzi:
                wynik.append({"pracownik": p.id, "imie_nazwisko": p.imie_nazwisko, "od": od, "pensja": float(o.get("pensja") or 0),
                              "umowa": o.get("umowa", "prace"), "obecna_pensja": p.pensja})
    return wynik


def pracownicy_rynku(dane: Dane, s: StanGry, nazwa: str, runda: int) -> list[dict]:
    """Pracownicy innych firm (dla headhuntera): pensja, staż i okres wypowiedzenia."""
    return [{"id": p.id, "imie_nazwisko": p.imie_nazwisko, "firma": n, "zawod": p.zawod, "gwiazdki": p.gwiazdki,
             "pensja": p.pensja, "umowa": p.umowa, "staz": staz(p, runda), "okres": okres_wypowiedzenia(dane, p, runda),
             "odchodzi": bool(p.odchodzi)}
            for n, f in sorted(s.firmy.items()) if n != nazwa for p in f.pracownicy.values()]
