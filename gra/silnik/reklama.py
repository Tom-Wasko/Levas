"""Agencje reklamowe w grze z lokalami (F3b.2; notatki „Elementy mapy” i „Ustalenia gry”): kampanie z listy
agencja × kanał × strefa (`dane/mapa/reklama.yaml`), zamiast reklamy tradycyjnej i internetowej z Revasa.

- Zamówienie (`zamow`, w decyzje.zastosuj): koszt netto + VAT płatny z góry, kampania w `Firma.kampanie` trwa
  `rundy` rund od rundy zamówienia. Nasycenie: każda wcześniejsza kampania firmy w tym samym kanale i strefie w ostatnich
  `okno_nasycenia` rundach osłabia nową (`Kampania.sila`). Kampania w tym samym kanale i strefie nie może się nakładać.
- Efekt w rundzie (`efekty_rundy`, w runda.py przed popytem): pula strefy rośnie (mnożnik w popyt.pule – korzystają
  wszystkie lokale, najwięcej reklamujący się) i firma przyciąga mieszkańców strefy (popyt.atrakcyjnosc –
  `reklama_strefy`, odbiera klientów konkurencji). Zagłuszanie: inne firmy z trwającą kampanią tego samego rodzaju
  w tej strefie (kampanie na całe miasto – w każdej strefie). Wygasanie: po końcu efekt × wygasanie co rundę.
"""
from __future__ import annotations

from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Firma, Kampania

OPIS = "Kampania reklamowa"
ZAKLADKA = "agencje"


def zasady(dane: Dane) -> dict | None:
    """mapa/reklama.yaml (model, agencje); None – dane bez agencji reklamowych."""
    return (dane.mapa or {}).get("reklama")


def kanal(dane: Dane, agencja: str, kanal_id: str) -> dict | None:
    return ((zasady(dane) or {}).get("agencje", {}).get(agencja) or {}).get("kanaly", {}).get(kanal_id)


def strefy_kanalu(dane: Dane, kan: dict) -> list[str]:
    """Strefy, w których można zamówić kampanię (zasięg „miasto” – brak wyboru strefy)."""
    return [] if kan["zasieg"] == "miasto" else list(kan["strefy"] or dane.mapa["strefy"])


def koszt(dane: Dane, kan: dict, strefa: str | None) -> float:
    """Koszt netto: przy zasięgu „strefa” × pula strefy (więcej ludzi – drożej), zaokrąglony do 10 zł."""
    k = kan["koszt"] * (dane.mapa["popyt"]["strefy"][strefa]["pula"] if strefa else 1.0)
    return float(round(k / 10) * 10)


def brutto(dane: Dane, netto: float) -> float:
    """Koszt z VAT wg reguł kosztów z podatki_2026.yaml (opis „Kampania reklamowa…”)."""
    vat = (dane.podatki or {}).get("vat")
    return round(netto * (1 + (Ksiega(vat=vat).stawka_vat(OPIS) if vat else 0.0)), 2)


def sila_nowej(dane: Dane, f: Firma, agencja: str, kanal_id: str, strefa: str | None, runda: int) -> float:
    m = zasady(dane)["model"]
    k = sum(1 for x in f.kampanie if (x.agencja, x.kanal, x.strefa) == (agencja, kanal_id, strefa)
            and x.od_rundy > runda - m["okno_nasycenia"] and x.od_rundy < runda)
    return round((1 - m["nasycenie"]) ** k, 4)


def trwa(f: Firma, agencja: str, kanal_id: str, strefa: str | None, runda: int) -> bool:
    return any((x.agencja, x.kanal, x.strefa) == (agencja, kanal_id, strefa) and x.od_rundy <= runda <= x.do_rundy
               for x in f.kampanie)


def nazwa_strefy(dane: Dane, strefa: str | None) -> str:
    return dane.mapa["strefy"][strefa]["nazwa"] if strefa else "całe miasto"


def zamow(dane: Dane, f: Firma, d: dict, runda: int, ks: Ksiega, rach: Rachunek) -> dict:
    """Kampanie z decyzji `kampanie: [{"agencja", "kanal", "strefa"}]`. Zwraca {"zamowione": [...], "uwagi": [...]}."""
    info = {"zamowione": [], "uwagi": []}
    R = zasady(dane)
    if not R:
        return info
    for z in d.get("kampanie") or []:
        a, k = z.get("agencja"), z.get("kanal")
        kan = kanal(dane, a, k)
        if kan is None:
            info["uwagi"].append(f"Nieznana kampania reklamowa: {a} / {k}.")
            continue
        nazwa = f"{kan['nazwa']} ({R['agencje'][a]['nazwa']})"
        strefa = None if kan["zasieg"] == "miasto" else z.get("strefa")
        if not f.lokale:
            info["uwagi"].append(f"{nazwa}: agencja przyjmuje zlecenia dopiero od firm z lokalem.")
        elif kan["od_rundy"] > runda:
            info["uwagi"].append(f"{nazwa}: dostępne od rundy {kan['od_rundy']}.")
        elif kan["zasieg"] == "strefa" and strefa not in strefy_kanalu(dane, kan):
            info["uwagi"].append(f"{nazwa}: " + ("wybierz strefę." if not strefa else
                                                 f"agencja nie robi tej kampanii w strefie {nazwa_strefy(dane, strefa)}."
                                                 if strefa in dane.mapa["strefy"] else f"nieznana strefa {strefa}."))
        elif trwa(f, a, k, strefa, runda):
            info["uwagi"].append(f"{nazwa} – {nazwa_strefy(dane, strefa)}: kampania jeszcze trwa, nową zamówisz po jej końcu.")
        else:
            netto = koszt(dane, kan, strefa)
            kamp = Kampania(agencja=a, kanal=k, strefa=strefa, od_rundy=runda, do_rundy=runda + kan["rundy"] - 1,
                            koszt=netto, sila=sila_nowej(dane, f, a, k, strefa, runda))
            f.kampanie.append(kamp)
            opis = f"{OPIS}: {kan['nazwa']} – {nazwa_strefy(dane, strefa)}"
            stawka = ks.stawka_vat(opis) if ks.vat is not None else 0.0
            ksieguj(f, ks, rach, opis, round(netto * (1 + stawka), 2), "pozostale")
            info["zamowione"].append({**kamp.model_dump(), "nazwa": kan["nazwa"], "agencja_nazwa": R["agencje"][a]["nazwa"],
                                      "brutto": round(netto * (1 + stawka), 2)})
    return info


def _waga(m: dict, k: Kampania, runda: int) -> tuple[float, str] | None:
    if runda < k.od_rundy:
        return None
    if runda <= k.do_rundy:
        return 1.0, "trwa"
    w = m["wygasanie"] ** (runda - k.do_rundy)
    return (w, "wygasa") if w >= m["prog_wygasania"] else None


def efekty_rundy(dane: Dane, firmy: dict[str, Firma], runda: int, ziarno=None) -> dict:
    """Efekty kampanii wszystkich firm w rundzie: {"pula": {strefa: ułamek}, "firmy": {firma: {strefa: ułamek}},
    "kampanie": {firma: [szczegóły do wyników]}}. Z ziarnem – komiczny raport agencji w pierwszej rundzie kampanii."""
    R = zasady(dane)
    m = R["model"]
    strefy = list(dane.mapa["strefy"])
    aktywne: dict[tuple[str, str | None], set[str]] = {}
    for n, f in firmy.items():
        for k in f.kampanie:
            if k.od_rundy <= runda <= k.do_rundy and kanal(dane, k.agencja, k.kanal):
                aktywne.setdefault((R["agencje"][k.agencja]["rodzaj"], k.strefa), set()).add(n)
    wynik = {"pula": {z: 0.0 for z in strefy}, "firmy": {}, "kampanie": {}}
    for n, f in firmy.items():
        przyc = {}
        for k in f.kampanie:
            kan, w = kanal(dane, k.agencja, k.kanal), _waga(m, k, runda)
            if kan is None or w is None:
                continue
            waga, faza = w
            rodzaj = R["agencje"][k.agencja]["rodzaj"]
            zag, inni_max, pula_k, przyc_k = [], 0, 0.0, 0.0
            for z in ([k.strefa] if k.strefa else strefy):
                inni = len((aktywne.get((rodzaj, z), set()) | aktywne.get((rodzaj, None), set())) - {n})
                mn = 1 / (1 + m["zagluszanie"] * inni)
                e = waga * k.sila * mn
                wynik["pula"][z] += e * kan["pula"]
                przyc[z] = przyc.get(z, 0.0) + e * kan["przyciaganie"]
                zag.append(mn)
                inni_max = max(inni_max, inni)
                pula_k, przyc_k = pula_k + e * kan["pula"], przyc_k + e * kan["przyciaganie"]
            nz = len(zag)
            wpis = {"agencja": k.agencja, "kanal": k.kanal, "strefa": k.strefa, "nazwa": kan["nazwa"],
                    "agencja_nazwa": R["agencje"][k.agencja]["nazwa"], "strefa_nazwa": nazwa_strefy(dane, k.strefa),
                    "od_rundy": k.od_rundy, "do_rundy": k.do_rundy, "faza": faza, "waga": round(waga, 4),
                    "sila": k.sila, "zagluszanie": round(sum(zag) / nz, 4), "konkurenci": inni_max,
                    "pula": round(pula_k / nz, 4), "przyciaganie": round(przyc_k / nz, 4),
                    "koszt": k.koszt if k.od_rundy == runda else 0.0, "tekst": None}
            if ziarno is not None and k.od_rundy == runda:
                teksty = kan["teksty"]
                t = teksty[int(strumien(ziarno, runda, "reklama", n, k.agencja, k.kanal).integers(len(teksty)))]
                wpis["tekst"] = " ".join(t.replace("{strefa}", wpis["strefa_nazwa"]).split())
            wynik["kampanie"].setdefault(n, []).append(wpis)
        if przyc:
            wynik["firmy"][n] = {z: round(x, 4) for z, x in przyc.items()}
    wynik["pula"] = {z: round(x, 4) for z, x in wynik["pula"].items()}
    return wynik


def publiczne(dane: Dane, efekty: dict) -> dict:
    """Do danych rynku (widoczne dla wszystkich – reklamy widać na mieście): {firma: {"wydatki", "kampanie"}}."""
    return {n: {"wydatki": round(sum(x["koszt"] for x in lista), 2),
                "kampanie": [{k: x[k] for k in ("agencja", "kanal", "strefa", "faza")} for x in lista]}
            for n, lista in efekty["kampanie"].items()}


def widok(dane: Dane, f: Firma, runda: int, rynek_poprzedni: dict | None, zamowione: list | None = None) -> dict | None:
    """Zakładka „Agencje reklamowe” (decyzje): agencje z kanałami (koszt i siła w każdej strefie), kampanie firmy
    trwające w tej rundzie (f – stan po decyzjach), kto reklamował się w poprzedniej rundzie."""
    R = zasady(dane)
    if not R:
        return None
    agencje = []
    for a, ag in R["agencje"].items():
        kanaly = []
        for k, kan in ag["kanaly"].items():
            st = strefy_kanalu(dane, kan) or [None]
            kanaly.append({"id": k, **{x: kan[x] for x in ("nazwa", "od_rundy", "zasieg", "rundy", "pula", "przyciaganie")},
                           "dostepny": kan["od_rundy"] <= runda, "strefy": [s for s in st if s],
                           "koszty": {s or "miasto": koszt(dane, kan, s) for s in st},
                           "sila": {s or "miasto": sila_nowej(dane, f, a, k, s, runda) for s in st},
                           "trwa": [s or "miasto" for s in st if trwa(f, a, k, s, runda)
                                    and not any(z["agencja"] == a and z["kanal"] == k and z["strefa"] == s
                                                for z in zamowione or [])]})
        agencje.append({"id": a, "nazwa": ag["nazwa"], "opis": ag["opis"], "rodzaj": ag["rodzaj"], "budynek": ag["budynek"],
                        "kanaly": kanaly})
    ef = efekty_rundy(dane, {f.nazwa: f}, runda)
    konkurencja: dict = {}
    for n, x in ((rynek_poprzedni or {}).get("kampanie") or {}).items():
        if n == f.nazwa:
            continue
        for k in x["kampanie"]:
            rodzaj = R["agencje"].get(k["agencja"], {}).get("rodzaj")
            if rodzaj:
                konkurencja.setdefault(rodzaj, {}).setdefault(k["strefa"] or "miasto", []).append(n)
    return {"model": R["model"], "agencje": agencje,
            "strefy": {z: s["nazwa"] for z, s in dane.mapa["strefy"].items()},
            "moje_strefy": sorted({dane.lokale[lok.id]["strefa"] for lok in f.lokale}),
            "trwajace": ef["kampanie"].get(f.nazwa, []), "zamowione": zamowione or [], "konkurencja": konkurencja}


__all__ = ["OPIS", "ZAKLADKA", "brutto", "efekty_rundy", "kanal", "koszt", "nazwa_strefy", "publiczne", "sila_nowej",
           "strefy_kanalu", "trwa", "widok", "zamow", "zasady"]
