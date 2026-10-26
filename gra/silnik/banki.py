"""Banki gry z lokalami (F3a.9; dane: dane/mapa/banki.yaml).

Sześć banków, każdy z inną najlepszą ofertą. Konto firmowe (`firma.bank`) niesie opłatę za konto, terminal
(abonament + prowizja od płatności kartą) i limit w koncie (kredyt odnawialny do kwoty limitu; debet ponad limit –
odsetki karne). Lokaty, kredyty i leasing można brać w dowolnym banku – rozliczają się na koncie firmowym.

Kredyty: „na start” bez historii firmy, pozostałe dopiero po `historia_rund` rundach od otwarcia pierwszego lokalu;
inwestycyjny – pod zastaw własnego lokalu albo sprzętu (kwota do części wartości netto zastawu). Raty kapitałowe
równe + odsetki od pozostałej kwoty, od rundy po zaciągnięciu. Gdy gotówki i wolnego limitu nie starcza na ratę,
rata nie wchodzi, a kredyt biegnie dalej na odsetkach karnych (niezapłacone odsetki doliczane do długu, zaległe raty
kapitałowe spłacane razem z najbliższą ratą); po `przejecie_po` rundach z rzędu bank przejmuje zastaw: sprzęt
znika ze stanowiska, lokal przechodzi na bank i firma dalej go wynajmuje. Wycena zastawu pomniejsza dług, nadwyżka
wraca na konto. Leasing: sprzęt od razu na stanowisku, ale nie jest środkiem trwałym firmy – wpłata własna i raty
(annuitetowe) idą w koszty, sprzętu nie można sprzedać, po ostatniej racie wykup; zaległe raty – bank zabiera sprzęt.
"""

from __future__ import annotations

from . import srodki_trwale as st_trwale
from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .model import Firma, Kredyt, Leasing, Lokata

EPS = 1e-6


def ustawienia(dane: Dane) -> dict:
    return dane.mapa["banki"]


def banki(dane: Dane) -> dict[str, dict]:
    return {b["nazwa"]: b for b in ustawienia(dane)["banki"]}


def historia(firma: Firma, runda: int) -> int:
    """Liczba rund działania firmy – od otwarcia pierwszego lokalu (0 – jeszcze żaden nie działa)."""
    otwarte = [lok.dziala_od for lok in firma.lokale if lok.dziala_od <= runda]
    return runda - min(otwarte) if otwarte else 0


def najlepsze(dane: Dane) -> dict[str, str]:
    """Który bank ma najlepszą ofertę w każdej kategorii (porównanie w zakładce Bank)."""
    b = list(banki(dane).values())
    kredyty = [(x["nazwa"], k) for x in b for k in x["kredyty"]]
    return {
        "konto": min(b, key=lambda x: x["konto"] + x["terminal"]["abonament"])["nazwa"],
        "lokata": max(b, key=lambda x: max(x["lokaty"].values()))["nazwa"],
        "kredyt_bez_historii": min(((n, k) for n, k in kredyty if not k["historia"]),
                                   key=lambda p: p[1]["oprocentowanie"])[0],
        "kredyt_inwestycyjny": min(((n, k) for n, k in kredyty if k.get("zastaw")),
                                   key=lambda p: p[1]["oprocentowanie"])[0],
        "leasing": min((x for x in b if x.get("leasing")), key=lambda x: x["leasing"]["oprocentowanie"])["nazwa"],
        "limit": max(b, key=lambda x: x["limit"]["kwota"])["nazwa"],
    }


def rata_annuitetowa(kwota: float, oprocentowanie: float, rund: int, rund_w_roku: int) -> float:
    i = oprocentowanie / rund_w_roku
    return round(kwota * i / (1 - (1 + i) ** -rund), 2)


# --- zastawy -------------------------------------------------------------------------------------

def _srodki_lokalu(dane: Dane, firma: Firma, lokal_id: str) -> list:
    adres = dane.lokale[lokal_id]["adres"]
    return [s for s in firma.srodki_trwale if s.rodzaj in ("lokal", "grunt", "budynek") and s.nazwa.endswith(f": {adres}")]


def _nazwa_sprzetu(typ: str, nr: int, nazwa: str) -> str:
    return f"{nazwa} ({typ} {nr})"


def zastawy(dane: Dane, firma: Firma) -> list[dict]:
    """Majątek, który można dać pod zastaw: kupione lokale i sprzęt w ewidencji środków trwałych (bez już
    zastawionych). Wartość – netto (po amortyzacji)."""
    zajete = {k.zastaw for k in firma.kredyty if k.zastaw}
    wynik = []
    for lok in firma.lokale:
        if lok.forma != "kupno" or f"lokal:{lok.id}" in zajete:
            continue
        wartosc = sum(s.wartosc - s.umorzenie for s in _srodki_lokalu(dane, firma, lok.id))
        if wartosc > EPS:
            wynik.append({"id": f"lokal:{lok.id}", "nazwa": f"Lokal: {dane.lokale[lok.id]['adres']}", "wartosc": round(wartosc, 2)})
    for st in firma.stanowiska:
        for n in st.sprzet:
            nazwa = _nazwa_sprzetu(st.typ, st.nr, n)
            sr = next((s for s in firma.srodki_trwale if s.nazwa == nazwa), None)
            zid = f"sprzet:{st.typ}:{st.nr}:{n}"
            if sr and zid not in zajete and sr.wartosc - sr.umorzenie > EPS:
                wynik.append({"id": zid, "nazwa": nazwa, "wartosc": round(sr.wartosc - sr.umorzenie, 2)})
    return wynik


def _przejmij_zastaw(dane: Dane, firma: Firma, k: Kredyt, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Bank przejmuje zastaw zaległego kredytu: wycena pomniejsza dług, nadwyżka wraca na konto."""
    u = ustawienia(dane)
    rodzaj, _, reszta = k.zastaw.partition(":")
    if rodzaj == "lokal":
        lok = next(x for x in firma.lokale if x.id == reszta)
        srodki = _srodki_lokalu(dane, firma, lok.id)
        wartosc = sum(s.wartosc - s.umorzenie for s in srodki)
        for s in srodki:
            st_trwale.sprzedaj(firma, s.nazwa, ksiega)
        d = dane.lokale[lok.id]
        lok.forma, lok.czynsz = "najem", d.get("czynsz") or round(u["czynsz_po_przejeciu"] * (lok.cena or wartosc), 2)
        opis = f"lokal {d['adres']} (dalej w najmie od banku)"
    else:
        typ, nr, nazwa = reszta.split(":", 2)
        st = firma.stanowisko(typ, int(nr))
        sr_nazwa = _nazwa_sprzetu(typ, int(nr), nazwa)
        sr = next((s for s in firma.srodki_trwale if s.nazwa == sr_nazwa), None)
        wartosc = sr.wartosc - sr.umorzenie if sr else 0.0
        if st and nazwa in st.sprzet:
            q = st.sprzet.pop(nazwa)
            firma.majatek -= dane.sprzet[nazwa]["ceny"][str(q)]
        st_trwale.sprzedaj(firma, sr_nazwa, ksiega)
        opis = sr_nazwa
    wycena = round(wartosc * u["wycena_zastawu"], 2)
    dlug = k.pozostalo
    nadwyzka = max(0.0, round(wycena - dlug, 2))
    k.zastaw = ""
    if wycena >= dlug:
        firma.kredyty.remove(k)
    else:   # reszta długu zostaje jako kredyt bez zastawu (zaległość – rozłożona na pozostałe raty)
        k.pozostalo, k.zaleglosc, k.zalegle = round(dlug - wycena, 2), 0.0, 0
    if nadwyzka > 0:
        rachunek.zapisz(firma, f"Nadwyżka z wyceny przejętego zastawu kredytu nr {k.id}", nadwyzka, "kredyty")
    return {"kredyt": k.id, "bank": k.bank, "zastaw": opis, "wycena": wycena, "dlug": dlug, "nadwyzka": nadwyzka}


# --- decyzje (początek rundy) ----------------------------------------------------------------------

def powod_kredytu(dane: Dane, firma: Firma, d: dict, runda: int) -> str | None:
    """Dlaczego bank odmówi kredytu (None – udzieli)."""
    u = ustawienia(dane)
    bank = banki(dane).get(d.get("bank"))
    if not bank:
        return "nieznany bank"
    produkt = next((p for p in bank["kredyty"] if p["produkt"] == d.get("produkt")), None)
    if not produkt:
        return f"{bank['nazwa']} nie ma takiego kredytu"
    kwota, rund = float(d.get("kwota") or 0), int(d.get("rund") or d.get("miesiecy") or 0)
    if kwota <= 0 or rund <= 0:
        return "podaj kwotę i okres"
    if rund > produkt["maks_rund"]:
        return f"okres najwyżej {produkt['maks_rund']} rund"
    if kwota > produkt["maks_kwota"] + EPS:
        return f"kwota najwyżej {produkt['maks_kwota']:,.0f} PLN".replace(",", " ")
    if produkt["historia"] and historia(firma, runda) < u["historia_rund"]:
        return f"bank wymaga {u['historia_rund']} rund historii firmy (od otwarcia pierwszego lokalu)"
    if any(k.bank == bank["nazwa"] and k.produkt == produkt["produkt"] for k in firma.kredyty):
        return "ten kredyt jest już w spłacie – najpierw spłać poprzedni"
    if produkt.get("zastaw"):
        z = next((x for x in zastawy(dane, firma) if x["id"] == d.get("zastaw")), None)
        if not z:
            return "wybierz zastaw (kupiony lokal albo sprzęt, niezastawiony)"
        if kwota > produkt["zastaw"] * z["wartosc"] + EPS:
            return f"pod ten zastaw najwyżej {produkt['zastaw'] * z['wartosc']:,.0f} PLN".replace(",", " ")
    return None


def poczatek_rundy(dane: Dane, firma: Firma, decyzje: dict, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Zmiana konta, zerwane lokaty, spłaty kredytów, nowe kredyty i lokaty (przed zakupami rundy)."""
    info = {"nowe_lokaty": [], "nowe_kredyty": [], "zerwane_lokaty": [], "splacone_kredyty": [], "odrzucone": []}
    if decyzje.get("bank") in banki(dane):
        firma.bank = decyzje["bank"]
    for lid in decyzje.get("lokaty_zerwij", []):
        lokata = next((x for x in firma.lokaty if x.id == lid), None)
        if lokata:
            firma.lokaty.remove(lokata)
            rachunek.zapisz(firma, f"Zerwanie lokaty nr {lokata.id} (bez odsetek)", lokata.kwota, "lokaty")
            info["zerwane_lokaty"].append(lokata.id)
    for kid in decyzje.get("kredyty_splac", []):
        k = next((x for x in firma.kredyty if x.id == kid), None)
        if k and firma.gotowka >= k.pozostalo:
            firma.kredyty.remove(k)
            rachunek.zapisz(firma, f"Spłata kredytu nr {k.id} ({k.bank})", -k.pozostalo, "kredyty")
            info["splacone_kredyty"].append(k.id)
        elif k:
            info["odrzucone"].append({"co": f"Spłata kredytu nr {k.id}", "powod": "za mało gotówki na koncie"})
    for d in decyzje.get("kredyty_wez", []):
        powod = powod_kredytu(dane, firma, d, runda)
        if powod:
            info["odrzucone"].append({"co": f"Kredyt {d.get('produkt', '')} – {d.get('bank', '')}", "powod": powod})
            continue
        produkt = next(p for p in banki(dane)[d["bank"]]["kredyty"] if p["produkt"] == d["produkt"])
        firma.licznik += 1
        kwota = float(d["kwota"])
        k = Kredyt(id=firma.licznik, kwota=kwota, oprocentowanie=produkt["oprocentowanie"], od_rundy=runda,
                   miesiecy=int(d.get("rund") or d["miesiecy"]), pozostalo=kwota, bank=d["bank"],
                   produkt=produkt["produkt"], zastaw=d.get("zastaw", "") if produkt.get("zastaw") else "")
        firma.kredyty.append(k)
        rachunek.zapisz(firma, f"{produkt['nazwa']} nr {k.id} ({k.bank})", kwota, "kredyty")
        ksieguj(firma, ksiega, rachunek, f"Prowizja za udzielenie kredytu nr {k.id} ({k.bank})",
                round(kwota * produkt["prowizja"], 2))
        info["nowe_kredyty"].append(k.id)
    for d in decyzje.get("lokaty_zaloz", []):
        bank = banki(dane).get(d.get("bank") or firma.bank)
        rund = int(d.get("rund") or d.get("miesiecy") or 0)
        if not bank or rund not in bank["lokaty"]:
            info["odrzucone"].append({"co": f"Lokata na {rund} rund", "powod": "bank nie ma lokaty na taki okres"})
            continue
        kwota = min(float(d["kwota"]), max(0.0, firma.gotowka))
        if kwota <= 0:
            info["odrzucone"].append({"co": f"Lokata w {bank['nazwa']}", "powod": "brak gotówki na koncie"})
            continue
        firma.licznik += 1
        lokata = Lokata(id=firma.licznik, kwota=kwota, oprocentowanie=bank["lokaty"][rund], od_rundy=runda,
                        miesiecy=rund, bank=bank["nazwa"])
        firma.lokaty.append(lokata)
        rachunek.zapisz(firma, f"Założenie lokaty nr {lokata.id} ({lokata.bank})", -kwota, "lokaty")
        info["nowe_lokaty"].append(lokata.id)
    return info


def leasing_wez(dane: Dane, firma: Firma, decyzje: dict, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Sprzęt w leasingu (po zakupach rundy – stanowiska z tej rundy już są):
    leasing_wez: [{"bank", "typ", "nr", "nazwa", "jakosc", "rund"}]."""
    info = {"nowe": [], "odrzucone": []}
    for d in decyzje.get("leasing_wez", []) if "inwestycje_sprzet" in dane.odblokowane(runda) else []:
        bank = banki(dane).get(d.get("bank"))
        st = firma.stanowisko(d.get("typ"), int(d.get("nr") or 0))
        sprzet = dane.sprzet.get(d.get("nazwa"))
        rund = int(d.get("rund") or 0)
        powod = ("bank nie prowadzi leasingu" if not bank or not bank.get("leasing")
                 else "nie ma takiego stanowiska" if not st
                 else "nieznany sprzęt" if not sprzet or sprzet["dla"] != st.typ
                 else "ten sprzęt już jest na stanowisku" if d["nazwa"] in st.sprzet
                 else f"okres leasingu: {', '.join(map(str, bank['leasing']['rund']))} rund"
                 if rund not in bank["leasing"]["rund"] else None)
        if powod:
            info["odrzucone"].append({"co": f"Leasing: {d.get('nazwa', '')}", "powod": powod})
            continue
        lz = bank["leasing"]
        q = int(d.get("jakosc", 3))
        cena = sprzet["ceny"][str(q)]
        firma.licznik += 1
        lea = Leasing(id=firma.licznik, bank=bank["nazwa"], typ=st.typ, nr=st.nr, nazwa=d["nazwa"], jakosc=q,
                      cena=cena, od_rundy=runda, rund=rund, pozostalo_rat=rund, wykup=round(cena * lz["wykup"], 2),
                      rata=rata_annuitetowa(cena * (1 - lz["wplata"]), lz["oprocentowanie"], rund, dane.rund_w_roku))
        firma.leasingi.append(lea)
        st.sprzet[lea.nazwa] = q
        st.sprzet_wynajmujacego.append(lea.nazwa)   # własność banku – nie do sprzedania do wykupu
        ksieguj(firma, ksiega, rachunek, f"Opłata wstępna leasingu nr {lea.id}: {lea.nazwa} ({lea.bank})",
                round(cena * lz["wplata"], 2))
        info["nowe"].append(lea.id)
    return info


# --- koniec rundy --------------------------------------------------------------------------------

def wolny_limit(dane: Dane, firma: Firma) -> float:
    bank = banki(dane).get(firma.bank)
    return max(0.0, (bank["limit"]["kwota"] if bank else 0.0) - firma.kredyt_odnawialny)


def _stac(dane: Dane, firma: Firma, kwota: float) -> bool:
    return firma.gotowka + wolny_limit(dane, firma) >= kwota - EPS


def koniec_rundy(dane: Dane, firma: Firma, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Opłaty konta i terminala, raty kredytów i leasingu (zaległości, przejęcia), odsetki limitu, lokaty."""
    u, rwr = ustawienia(dane), dane.rund_w_roku
    bank = banki(dane).get(firma.bank)
    info = {"oplaty": {}, "raty": [], "leasing": [], "przejecia": [], "wykupy": [], "zaleglosci": [], "lokaty": []}
    if bank:
        sprzedaz = ksiega.suma("przychod")
        info["oplaty"] = {"konto": dane.na_runde(bank["konto"]), "terminal": dane.na_runde(bank["terminal"]["abonament"]),
                          "prowizja": round(sprzedaz * u["udzial_kart"] * bank["terminal"]["prowizja"], 2)}
        ksieguj(firma, ksiega, rachunek, f"Opłata za konto firmowe ({bank['nazwa']})", info["oplaty"]["konto"])
        ksieguj(firma, ksiega, rachunek, "Abonament terminala płatniczego", info["oplaty"]["terminal"])
        ksieguj(firma, ksiega, rachunek, "Prowizja od płatności kartą", info["oplaty"]["prowizja"])

    for k in list(firma.kredyty):
        if k.od_rundy == runda:
            continue
        stopa = u["stopa_karna"] if k.zalegle else k.oprocentowanie
        odsetki = round(k.pozostalo * stopa / rwr, 2)
        rata = round(max(0.0, min(k.pozostalo - k.zaleglosc, k.kwota / k.miesiecy)), 2)   # dług zawiera zaległość
        wiersz = {"kredyt": k.id, "bank": k.bank, "odsetki": odsetki, "rata": rata, "zaleglosc": k.zaleglosc}
        if _stac(dane, firma, odsetki + rata + k.zaleglosc):   # zaległe raty kapitałowe spłacane razem z bieżącą
            ksieguj(firma, ksiega, rachunek, f"Odsetki od kredytu nr {k.id} ({k.bank})", odsetki)
            rachunek.zapisz(firma, f"Rata kapitałowa kredytu nr {k.id}", -(rata + k.zaleglosc), "kredyty")
            k.pozostalo = round(k.pozostalo - rata - k.zaleglosc, 2)
            k.zaleglosc, k.zalegle = 0.0, 0
            wiersz["zaplacona"] = True
            if k.pozostalo <= EPS:
                firma.kredyty.remove(k)
        else:   # rata nie weszła: odsetki doliczone do długu, rata kapitałowa – do zaległości
            k.pozostalo = round(k.pozostalo + odsetki, 2)
            k.zaleglosc = round(k.zaleglosc + rata, 2)
            k.zalegle += 1
            wiersz["zaplacona"] = False
            info["zaleglosci"].append(f"Kredyt nr {k.id} ({k.bank}): rata nie została zapłacona – brak środków "
                                      f"({k.zalegle} z {u['przejecie_po']} rund"
                                      + (" do przejęcia zastawu)." if k.zastaw else "; odsetki karne)."))
            if k.zastaw and k.zalegle >= u["przejecie_po"]:
                info["przejecia"].append(_przejmij_zastaw(dane, firma, k, runda, ksiega, rachunek))
        info["raty"].append(wiersz)

    for lea in list(firma.leasingi):
        if lea.od_rundy == runda:
            continue
        ile = 1 + lea.zalegle
        wiersz = {"leasing": lea.id, "bank": lea.bank, "sprzet": lea.nazwa, "rata": lea.rata, "rat": ile}
        if _stac(dane, firma, lea.rata * ile):
            ksieguj(firma, ksiega, rachunek, f"Rata leasingowa nr {lea.id}: {lea.nazwa} ({lea.bank})", round(lea.rata * ile, 2))
            lea.pozostalo_rat, lea.zalegle = max(0, lea.pozostalo_rat - ile), 0
            wiersz["zaplacona"] = True
        else:
            lea.zalegle += 1
            wiersz["zaplacona"] = False
            info["zaleglosci"].append(f"Leasing nr {lea.id} ({lea.nazwa}): rata nie została zapłacona "
                                      f"({lea.zalegle} z {u['przejecie_po']} rund do odebrania sprzętu).")
        st = firma.stanowisko(lea.typ, lea.nr)
        if lea.pozostalo_rat == 0:      # wykup – sprzęt firmy
            ksieguj(firma, ksiega, rachunek, f"Wykup sprzętu z leasingu nr {lea.id}: {lea.nazwa}", lea.wykup)
            if st and lea.nazwa in st.sprzet_wynajmujacego:
                st.sprzet_wynajmujacego.remove(lea.nazwa)
            firma.majatek += lea.cena
            firma.leasingi.remove(lea)
            info["wykupy"].append({"leasing": lea.id, "sprzet": lea.nazwa})
        elif lea.zalegle >= u["przejecie_po"]:   # bank zabiera sprzęt
            if st:
                st.sprzet.pop(lea.nazwa, None)
                if lea.nazwa in st.sprzet_wynajmujacego:
                    st.sprzet_wynajmujacego.remove(lea.nazwa)
            firma.leasingi.remove(lea)
            info["przejecia"].append({"leasing": lea.id, "bank": lea.bank, "zastaw": f"{lea.nazwa} ({lea.typ} {lea.nr})",
                                      "wycena": 0.0, "dlug": round(lea.rata * lea.pozostalo_rat, 2), "nadwyzka": 0.0})
        info["leasing"].append(wiersz)

    if firma.kredyt_odnawialny > 0 and bank:
        w_limicie = min(firma.kredyt_odnawialny, bank["limit"]["kwota"])
        ksieguj(firma, ksiega, rachunek, "Odsetki od limitu w koncie", round(w_limicie * bank["limit"]["oprocentowanie"] / rwr, 2))
        if firma.kredyt_odnawialny > w_limicie + EPS:
            ksieguj(firma, ksiega, rachunek, "Odsetki karne od debetu ponad limit",
                    round((firma.kredyt_odnawialny - w_limicie) * u["stopa_karna"] / rwr, 2))

    for lo in list(firma.lokaty):
        if runda >= lo.od_rundy + lo.miesiecy - 1:
            odsetki = round(lo.kwota * lo.oprocentowanie * lo.miesiecy / rwr, 2)
            firma.lokaty.remove(lo)
            rachunek.zapisz(firma, f"Zakończenie lokaty nr {lo.id} ({lo.bank})", lo.kwota, "lokaty")
            ksieguj(firma, ksiega, rachunek, f"Odsetki od lokaty nr {lo.id} ({lo.bank})", odsetki, "przychod_pozostaly")
            info["lokaty"].append({"lokata": lo.id, "bank": lo.bank, "kwota": lo.kwota, "odsetki": odsetki})
    return info


def debet_ponad_limit(dane: Dane, firma: Firma) -> float:
    """Kredyt odnawialny ponad limit konta (po wyrównaniu gotówki na koniec rundy)."""
    bank = banki(dane).get(firma.bank)
    return max(0.0, round(firma.kredyt_odnawialny - (bank["limit"]["kwota"] if bank else 0.0), 2))


def bledy(dane: Dane, firma: Firma, info_poczatek: dict | None, info_koniec: dict | None) -> list[dict]:
    """Czerwone błędy zakładki Bank: odrzucone decyzje, zaległe raty, przejęcia, debet ponad limit."""
    wynik = [f"{o['co']}: {o['powod']}." for o in (info_poczatek or {}).get("odrzucone", [])]
    if info_koniec:
        wynik += info_koniec["zaleglosci"]
        wynik += [f"Bank {p['bank']} przejął zastaw: {p['zastaw']}." for p in info_koniec["przejecia"]]
    debet = debet_ponad_limit(dane, firma)
    if debet > 0:
        wynik.append(f"Debet ponad limit w koncie: {debet:,.2f} PLN – odsetki karne.".replace(",", " "))
    return [{"poziom": "czerwony", "zakladka": "finanse_bank", "tekst": t} for t in wynik]
