"""Agencje reklamowe w grze z lokalami (F3b.2, Z5; notatki „Elementy mapy” i „Ustalenia gry”): kampanie z listy
agencja × kanał × strefa (`dane/mapa/reklama.yaml`) z liczbą emisji w rundzie, zamiast reklamy z Revasa.

- Zamówienie (`zamow`, w decyzje.zastosuj): emisje × cena emisji (przy zasięgu „strefa” × pula strefy) z rabatem
  z progów kanału (`znizki`, na wszystkie emisje), + VAT, płatne z góry. Kampania w `Firma.kampanie` działa w rundzie
  zamówienia (od_rundy = do_rundy); jedna na kanał i strefę w rundzie, najwyżej `maks_emisji` emisji.
- Nasycenie (Z5, mechanizm reklamy tradycyjnej z gry ATH): efekt kampanii × (1 − e^(−tempo_emisji · emisje)) –
  pierwsze emisje działają najmocniej, ok. 10 to ponad 90% efektu kanału.
- Efekt w rundzie (`efekty_rundy`, w runda.py przed popytem): pula strefy rośnie (mnożnik w popyt.pule – korzystają
  wszystkie lokale, najwięcej reklamujący się) i firma przyciąga mieszkańców strefy (popyt.atrakcyjnosc –
  `reklama_strefy`, odbiera klientów konkurencji). Zagłuszanie: inne firmy z kampanią tego samego rodzaju w tej
  strefie w tej rundzie (kampanie na całe miasto – w każdej strefie). Wygasanie: po rundzie emisji efekt × wygasanie
  co rundę.
- Sufit (P10): suma kampanii firmy w strefie nasyca się do `maks_przyciagania` (x → maks · (1 − e^(−x/maks))),
  poszerzenie puli strefy – do `maks_puli`; kilka kampanii razem daje kebabowi ok. +10% … +30% popytu, nie więcej.
- Marketing internetowy (UF19, sekcja `internet` – zakładka Marketing → Internet): kampanie zamawia się tak samo,
  ale efekt w rundzie emisji to dopiero część pełnego (`narastanie` – posty się udostępnia, opinie przybywają), pełny
  przychodzi po kilku rundach, a potem gaśnie co rundę × `trwalosc` (wolniej niż reklama tradycyjna). Efekt liczy
  się z historii kampanii firmy (`Firma.kampanie` – pamięć efektu), więc nie trzeba osobnego stanu.
"""
from __future__ import annotations

import math

from ..dane import Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..losowosc import strumien
from ..model import Firma, Kampania

OPIS = "Kampania reklamowa"
ZAKLADKA = "agencje"
ZAKLADKA_INTERNET = "internet"   # UF19


def zasady(dane: Dane) -> dict | None:
    """mapa/reklama.yaml (model, agencje, internet); None – dane bez agencji reklamowych."""
    return (dane.mapa or {}).get("reklama")


def internet(dane: Dane) -> dict | None:
    """UF19: sekcja `internet` (model, agencje); None – dane bez marketingu internetowego."""
    return (zasady(dane) or {}).get("internet")


def agencje(dane: Dane) -> dict:
    """Wszystkie agencje: tradycyjne i internetowe (id się nie powtarzają – pilnuje schemat)."""
    return {**((zasady(dane) or {}).get("agencje") or {}), **((internet(dane) or {}).get("agencje") or {})}


def internetowa(dane: Dane, agencja: str) -> bool:
    return agencja in ((internet(dane) or {}).get("agencje") or {})


def kanal(dane: Dane, agencja: str, kanal_id: str) -> dict | None:
    return (agencje(dane).get(agencja) or {}).get("kanaly", {}).get(kanal_id)


def strefy_kanalu(dane: Dane, kan: dict) -> list[str]:
    """Strefy, w których można zamówić kampanię (zasięg „miasto” – brak wyboru strefy)."""
    return [] if kan["zasieg"] == "miasto" else list(kan["strefy"] or dane.mapa["strefy"])


def cena_emisji(dane: Dane, kan: dict, strefa: str | None) -> float:
    """Cena jednej emisji netto: przy zasięgu „strefa” × pula strefy (więcej ludzi – drożej), do złotówki."""
    return float(round(kan["cena_emisji"] * (dane.mapa["popyt"]["strefy"][strefa]["pula"] if strefa else 1.0)))


def rabat(kan: dict, emisje: int) -> float:
    """Rabat z najwyższego osiągniętego progu kanału (na wszystkie emisje zamówienia)."""
    return max([r for od, r in kan.get("znizki") or [] if emisje >= od], default=0.0)


def koszt(dane: Dane, kan: dict, strefa: str | None, emisje: int) -> float:
    """Koszt netto zamówienia: emisje × cena emisji × (1 − rabat)."""
    return round(emisje * cena_emisji(dane, kan, strefa) * (1 - rabat(kan, emisje)), 2)


def brutto(dane: Dane, netto: float) -> float:
    """Koszt z VAT wg reguł kosztów z podatki_2026.yaml (opis „Kampania reklamowa…”)."""
    vat = (dane.podatki or {}).get("vat")
    return round(netto * (1 + (Ksiega(vat=vat).stawka_vat(OPIS) if vat else 0.0)), 2)


def efekt_emisji(dane: Dane, emisje: int | None) -> float:
    """Część pełnego efektu kanału po tylu emisjach: 1 − e^(−tempo · emisje); None (zapis sprzed Z5) – 1."""
    if emisje is None:
        return 1.0
    return 1 - math.exp(-zasady(dane)["model"]["tempo_emisji"] * emisje) if emisje > 0 else 0.0


def zamowiona(f: Firma, agencja: str, kanal_id: str, strefa: str | None, runda: int) -> bool:
    """Kampania w tym kanale i strefie już zamówiona w tej rundzie (albo – w zapisie sprzed Z5 – jeszcze trwa)."""
    return any((x.agencja, x.kanal, x.strefa) == (agencja, kanal_id, strefa) and x.od_rundy <= runda <= x.do_rundy
               for x in f.kampanie)


def nazwa_strefy(dane: Dane, strefa: str | None) -> str:
    return dane.mapa["strefy"][strefa]["nazwa"] if strefa else "całe miasto"


def zamow(dane: Dane, f: Firma, d: dict, runda: int, ks: Ksiega, rach: Rachunek) -> dict:
    """Kampanie z decyzji `kampanie: [{"agencja", "kanal", "strefa", "emisje"}]`.
    Zwraca {"zamowione": [...], "uwagi": [...], "uwagi_internet": [...]}."""
    info = {"zamowione": [], "uwagi": [], "uwagi_internet": []}   # UF19: uwagi kampanii internetowych osobno (zakładka)
    R = zasady(dane)
    if not R:
        return info
    A = agencje(dane)
    for z in d.get("kampanie") or []:
        a, k = z.get("agencja"), z.get("kanal")
        kan = kanal(dane, a, k)
        uwagi = info["uwagi_internet" if internetowa(dane, a) else "uwagi"]
        if kan is None:
            uwagi.append(f"Nieznana kampania reklamowa: {a} / {k}.")
            continue
        nazwa = f"{kan['nazwa']} ({A[a]['nazwa']})"
        strefa = None if kan["zasieg"] == "miasto" else z.get("strefa")
        try:
            emisje = int(z.get("emisje") or 0)
        except (TypeError, ValueError):
            emisje = 0
        if not f.lokale:
            uwagi.append(f"{nazwa}: agencja przyjmuje zlecenia dopiero od firm z lokalem.")
        elif kan["od_rundy"] > runda:
            uwagi.append(f"{nazwa}: dostępne od rundy {kan['od_rundy']}.")
        elif kan["zasieg"] == "strefa" and strefa not in strefy_kanalu(dane, kan):
            uwagi.append(f"{nazwa}: " + ("wybierz strefę." if not strefa else
                                                 f"agencja nie robi tej kampanii w strefie {nazwa_strefy(dane, strefa)}."
                                                 if strefa in dane.mapa["strefy"] else f"nieznana strefa {strefa}."))
        elif emisje < 1:
            uwagi.append(f"{nazwa} – {nazwa_strefy(dane, strefa)}: podaj liczbę emisji ({kan['emisja']}).")
        elif emisje > kan["maks_emisji"]:
            uwagi.append(f"{nazwa} – {nazwa_strefy(dane, strefa)}: najwyżej {kan['maks_emisji']} emisji w rundzie.")
        elif zamowiona(f, a, k, strefa, runda):
            uwagi.append(f"{nazwa} – {nazwa_strefy(dane, strefa)}: już zamówiona w tej rundzie – zmień liczbę emisji.")
        else:
            netto = koszt(dane, kan, strefa, emisje)
            kamp = Kampania(agencja=a, kanal=k, strefa=strefa, od_rundy=runda, do_rundy=runda, koszt=netto, emisje=emisje)
            f.kampanie.append(kamp)
            opis = f"{OPIS}: {kan['nazwa']} – {nazwa_strefy(dane, strefa)} ({emisje} × {kan['emisja']})"
            stawka = ks.stawka_vat(opis) if ks.vat is not None else 0.0
            ksieguj(f, ks, rach, opis, round(netto * (1 + stawka), 2), "pozostale")
            info["zamowione"].append({**kamp.model_dump(), "nazwa": kan["nazwa"], "agencja_nazwa": A[a]["nazwa"],
                                      "cena_emisji": cena_emisji(dane, kan, strefa), "rabat": rabat(kan, emisje),
                                      "brutto": round(netto * (1 + stawka), 2)})
    return info


def nasycenie(x: float, maks: float) -> float:
    """Suma efektów kampanii z sufitem: dla małych x prawie x, przy wielu kampaniach dochodzi do `maks`."""
    return maks * (1 - math.exp(-x / maks)) if x > 0 else 0.0


def waga_internetu(mi: dict, wiek: int) -> tuple[float, str] | None:
    """UF19: część efektu kampanii internetowej `wiek` rund po emisji: z listy narastanie, potem × trwalosc co rundę;
    faza – „trwa” (runda emisji), „narasta”, „wygasa”; None – efekt poniżej progu."""
    nar = mi["narastanie"]
    if wiek < 0:
        return None
    if wiek < len(nar):
        return nar[wiek], "trwa" if wiek == 0 else "narasta"
    w = nar[-1] * mi["trwalosc"] ** (wiek - len(nar) + 1)
    return (w, "wygasa") if w >= mi["prog_wygasania"] else None


def _waga(m: dict, k: Kampania, runda: int, mi: dict | None = None) -> tuple[float, str] | None:
    if mi is not None:   # kampania internetowa
        return waga_internetu(mi, runda - k.od_rundy)
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
    m, A, mi = R["model"], agencje(dane), (internet(dane) or {}).get("model")
    strefy = list(dane.mapa["strefy"])
    aktywne: dict[tuple[str, str | None], set[str]] = {}
    for n, f in firmy.items():
        for k in f.kampanie:
            if k.od_rundy <= runda <= k.do_rundy and kanal(dane, k.agencja, k.kanal):
                aktywne.setdefault((A[k.agencja]["rodzaj"], k.strefa), set()).add(n)
    wynik = {"pula": {z: 0.0 for z in strefy}, "firmy": {}, "suma": {}, "kampanie": {}}
    for n, f in firmy.items():
        przyc = {}
        for k in f.kampanie:
            kan = kanal(dane, k.agencja, k.kanal)
            w = None if kan is None else _waga(m, k, runda, mi if internetowa(dane, k.agencja) else None)
            if w is None:
                continue
            waga, faza = w
            rodzaj = A[k.agencja]["rodzaj"]
            zag, inni_max, pula_k, przyc_k = [], 0, 0.0, 0.0
            for z in ([k.strefa] if k.strefa else strefy):
                inni = len((aktywne.get((rodzaj, z), set()) | aktywne.get((rodzaj, None), set())) - {n})
                mn = 1 / (1 + m["zagluszanie"] * inni)
                e = waga * k.sila * efekt_emisji(dane, k.emisje) * mn
                wynik["pula"][z] += e * kan["pula"]
                przyc[z] = przyc.get(z, 0.0) + e * kan["przyciaganie"]
                zag.append(mn)
                inni_max = max(inni_max, inni)
                pula_k, przyc_k = pula_k + e * kan["pula"], przyc_k + e * kan["przyciaganie"]
            nz = len(zag)
            wpis = {"agencja": k.agencja, "kanal": k.kanal, "strefa": k.strefa, "nazwa": kan["nazwa"],
                    "agencja_nazwa": A[k.agencja]["nazwa"], "strefa_nazwa": nazwa_strefy(dane, k.strefa),
                    "internet": internetowa(dane, k.agencja),
                    "od_rundy": k.od_rundy, "do_rundy": k.do_rundy, "faza": faza, "waga": round(waga, 4),
                    "sila": k.sila, "emisje": k.emisje, "nasycenie": round(efekt_emisji(dane, k.emisje), 4),
                    "zagluszanie": round(sum(zag) / nz, 4), "konkurenci": inni_max,
                    "pula": round(pula_k / nz, 4), "przyciaganie": round(przyc_k / nz, 4),
                    "koszt": k.koszt if k.od_rundy == runda else 0.0, "tekst": None}
            if ziarno is not None and k.od_rundy == runda:
                teksty = kan["teksty"]
                t = teksty[int(strumien(ziarno, runda, "reklama", n, k.agencja, k.kanal).integers(len(teksty)))]
                wpis["tekst"] = " ".join(t.replace("{strefa}", wpis["strefa_nazwa"]).split())
            wynik["kampanie"].setdefault(n, []).append(wpis)
        if przyc:
            wynik["firmy"][n] = {z: round(nasycenie(x, m["maks_przyciagania"]), 4) for z, x in przyc.items()}
            wynik["suma"][n] = {z: round(x, 4) for z, x in przyc.items()}   # przed sufitem (do wyników)
    wynik["pula"] = {z: round(nasycenie(x, m["maks_puli"]), 4) for z, x in wynik["pula"].items()}
    return wynik


def publiczne(dane: Dane, efekty: dict) -> dict:
    """Do danych rynku (widoczne dla wszystkich – reklamy widać na mieście): {firma: {"wydatki", "kampanie"}}."""
    return {n: {"wydatki": round(sum(x["koszt"] for x in lista), 2),
                "kampanie": [{k: x[k] for k in ("agencja", "kanal", "strefa", "faza", "emisje")} for x in lista]}
            for n, lista in efekty["kampanie"].items()}


def widok(dane: Dane, f: Firma, runda: int, rynek_poprzedni: dict | None, zamowione: list | None = None) -> dict | None:
    """Zakładka „Agencje reklamowe” (decyzje): agencje z kanałami (cena emisji w każdej strefie, progi rabatów),
    kampanie firmy działające w tej rundzie (f – stan po decyzjach), kto reklamował się w poprzedniej rundzie."""
    R = zasady(dane)
    if not R:
        return None
    lista, mi = [], (internet(dane) or {}).get("model")
    for a, ag in agencje(dane).items():
        kanaly = []
        for k, kan in ag["kanaly"].items():
            st = strefy_kanalu(dane, kan) or [None]
            kanaly.append({"id": k, **{x: kan[x] for x in ("nazwa", "od_rundy", "zasieg", "emisja", "maks_emisji", "pula",
                                                            "przyciaganie")},
                           "znizki": [list(x) for x in kan.get("znizki") or []],
                           "dostepny": kan["od_rundy"] <= runda, "strefy": [s for s in st if s],
                           "ceny": {s or "miasto": cena_emisji(dane, kan, s) for s in st}})
        lista.append({"id": a, "nazwa": ag["nazwa"], "opis": ag["opis"], "rodzaj": ag["rodzaj"], "budynek": ag["budynek"],
                      "kanaly": kanaly, "internet": internetowa(dane, a)})
    ef = efekty_rundy(dane, {f.nazwa: f}, runda)
    konkurencja: dict = {}
    for n, x in ((rynek_poprzedni or {}).get("kampanie") or {}).items():
        if n == f.nazwa:
            continue
        for k in x["kampanie"]:
            rodzaj = agencje(dane).get(k["agencja"], {}).get("rodzaj")
            if rodzaj and k.get("faza", "trwa") == "trwa":
                konkurencja.setdefault(rodzaj, {}).setdefault(k["strefa"] or "miasto", []).append(n)
    return {"model": R["model"], "agencje": lista,
            "strefy": {z: s["nazwa"] for z, s in dane.mapa["strefy"].items()},
            "moje_strefy": sorted({dane.lokale[lok.id]["strefa"] for lok in f.lokale}),
            "trwajace": ef["kampanie"].get(f.nazwa, []), "zamowione": zamowione or [], "konkurencja": konkurencja,
            "internet": None if mi is None else {"model": mi, "prognoza": prognoza_internetu(dane, f, runda)}}


def prognoza_internetu(dane: Dane, f: Firma, runda: int, rund: int = 4) -> dict:
    """UF19: obecność firmy w sieci – przyciąganie z kampanii internetowych (już zamówionych, bez zagłuszania
    i sufitu) w tej i kolejnych rundach, gdyby nie zamawiać nowych: {strefa lub „miasto”: [ułamek na rundę]}."""
    mi = internet(dane)["model"]
    wynik: dict[str, list[float]] = {}
    for k in f.kampanie:
        kan = kanal(dane, k.agencja, k.kanal)
        if kan is None or not internetowa(dane, k.agencja):
            continue
        baza = k.sila * efekt_emisji(dane, k.emisje) * kan["przyciaganie"]
        rz = wynik.setdefault(k.strefa or "miasto", [0.0] * rund)
        for j in range(rund):
            w = waga_internetu(mi, runda + j - k.od_rundy)
            rz[j] += baza * w[0] if w else 0.0
    return {z: [round(x, 4) for x in rz] for z, rz in wynik.items() if any(rz)}


__all__ = ["OPIS", "ZAKLADKA", "ZAKLADKA_INTERNET", "agencje", "brutto", "cena_emisji", "efekt_emisji", "efekty_rundy", "internet", "internetowa",
           "kanal", "koszt", "nazwa_strefy", "prognoza_internetu", "publiczne", "rabat", "strefy_kanalu", "waga_internetu",
           "widok", "zamow", "zamowiona", "zasady"]
