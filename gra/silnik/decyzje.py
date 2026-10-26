"""Decyzje firmy w rundzie: format, zastosowanie do stanu (zakupy, zatrudnienia, zamówienia) i lista błędów.

Format (słownik; brak klucza = bez zmian względem poprzedniej rundy):
    nazwa, misja
    oferta:            {usługa: prognoza popytu}           – pełna lista usług w ofercie
    sprzedaz:          {usługa: {"cena", "rabat"}}          – usługi włączone do sprzedaży
    lokal:             {"id", "forma": "najem" | "kupno"}   – nowy lokal z mapy (gra z lokalami; silnik/lokale.py)
    stanowiska:        {"kuchnia": 0–5, "kasa": 0–5}        – nowe stanowiska (pakiet; w grze z lokalami najwyżej
                                                              tyle, ile wolnych miejsc w działających lokalach)
    sprzet_kup:        [{"typ", "nr", "nazwa", "jakosc"}]
    sprzet_sprzedaj:   [{"typ", "nr", "nazwa"}]
    zatrudnij:         [{"kandydat", "typ", "nr", "pensja", "umowa"}]   umowa: "prace" | "zlecenie"
                       gra z lokalami: opcjonalnie "kanal": "pracuj" | "agencja" | "headhunter" (silnik/rynek_pracy.py)
    podkup:            [{"pracownik", "firma", "pensja", "umowa"}]   – gra z lokalami: oferta przez headhuntera
    kontroferty:       {id pracownika: pensja}              – odpowiedź na oferty innych firm (ta sama runda)
                       opcjonalnie "zastepca": true + "wzor": {"zawod", "gwiazdki"} – gdy kandydata zatrudni
                       wcześniej inna firma, zatrudniany jest najbardziej podobny
    zmiany:            {id pracownika: {"pensja", "umowa", "premia"}}
    zwolnij:           [id pracownika]
    zamowienia:        [{"dostawca", "zasob", "jakosc", "ilosc", "dzien"}]   ilość w opakowaniach; dzien – dzień
                                                              dostawy w rundzie (0 = poniedziałek; gra z lokalami)
    zwrot_nadmiaru:    {dostawca: true/false}               – zwrot niezużytych zasobów z tej rundy (koszt 10%;
                                                              gra bez lokali – w grze z lokalami zwrotów nie ma)
    udogodnienia_kup / udogodnienia_sprzedaj / wyposazenie_kup / wyposazenie_sprzedaj: [nazwa]
    reklama_tradycyjna:{medium: liczba emisji}
    internet_uruchom / internet_wylacz: [narzędzie]
    kampanie:          [{"agencja", "kanal", "strefa"}]     – gra z lokalami: agencje reklamowe zamiast dwóch
                                                              powyższych (silnik/reklama.py, dane/mapa/reklama.yaml)
    promocje:          [{"typ", "nazwa", "danie"}]          – gra z lokalami: pełna lista włączonych promocji, nazwa
                                                              ozdobna (silnik/promocje.py, dane/mapa/promocje.yaml)
    polisy:            [rodzaj]                             – gra z lokalami: pełna lista polis ubezpieczyciela
                                                              (silnik/awarie.py, dane/zdarzenia/losowe.yaml)
    szkolenia:         [{"firma", "szkolenie"}]
    bank, biuro:       nazwa (z lokalami biuro: id z dane/mapa/biura.yaml albo "samodzielnie")
    ksiegowosc:        {"zapisy": {id dokumentu: {"kolumna", "stawka"}}, "deklaracja": {"vat", "pit", "zdrowotna"}}
                                                              – samodzielna księgowość za poprzednią rundę (biuro.py)
    lokaty_zaloz:      [{"kwota", "miesiecy"}];  lokaty_zerwij: [id]
    kredyty_wez:       [{"kwota", "miesiecy"}];  kredyty_splac: [id]
"""
from __future__ import annotations

import math
from datetime import timedelta

from . import awarie as aw
from . import biuro as bo
from . import czas_wlasciciela as cw
from . import limity as lm
from . import promocje as pm
from . import reklama as rk
from . import rozliczenie as rz
from . import rynek_pracy as rp
from . import srodki_trwale as st_trwale
from . import swiezosc as sw
from . import zdarzenia as zd
from .dane import KASA, KUCHNIA, Dane
from .dostawcy import zasady_dostaw
from .finanse import Ksiega, Rachunek, ksieguj
from .lokale import bledy as bledy_lokali
from .lokale import wolne_miejsca
from .model import Cena, Firma, Pracownik, Stanowisko, grosze
from .operacje import kasjerzy, stanowiska_uslugi


def limit_nowych_uslug(dane: Dane, runda: int, obecnie: int = 0) -> int:
    """O ile może wzrosnąć liczba usług w ofercie. Łącznie w ofercie najwyżej 3 usługi w rundach 1–2, potem
    o 3 więcej w każdej rundzie (runda 3: 6, runda 4: 9 …) – niewykorzystany limit przechodzi dalej.
    Dane: gra A/B/C online – Apex miał w styczniu tylko TBC i dodał w lutym Step, Vela miała Step i Zumbę i dodała
    TBC, w marcu Apex przeszedł z 2 na 6 usług (+4); ATH w marcu 3 → 6 (+5 nowych, −2 usunięte)."""
    r = dane.katalog_ofert["rundy"]
    if runda == 1:
        return r["uslugi_w_rundzie_1"]
    limit_lacznie = r["uslugi_w_rundzie_1"] + r["nowe_uslugi_na_runde"] * max(0, runda - r["nowe_uslugi_od_rundy"] + 1)
    return max(0, limit_lacznie - obecnie)


def cena_sprzedazy_sprzetu(dane: Dane, cena: float) -> float:
    """50% ceny ucięte do 2 cyfr znaczących (okna „Sprzedaj sprzęt” gry A/B/C online: 3500 → 1700, 5500 → 2700,
    2500 → 1200, 350 → 170, 250 → 120, 3600 → 1800)."""
    x = cena * dane.z["finanse"]["sprzedaz_sprzetu"]
    if x < 10:
        return math.floor(x)
    krok = 10 ** (len(str(int(x))) - 2)
    return math.floor(x / krok) * krok


def cena_dostawcy(dane: Dane, ceny_miesiaca: dict, dostawca: str, zasob: str, jakosc: int) -> float | None:
    return ceny_miesiaca.get(dostawca, {}).get(zasob, {}).get(str(jakosc))


def kandydaci_firmy(pula: list[dict], firma: Firma) -> list[dict]:
    """Kandydaci widoczni dla firmy: cała pula bez jej własnych pracowników. Każda firma ma pełną listę – w grze
    A/B/C drużyny A i C zatrudniły w lutym te same osoby (Miś, Tarnowska), a Mroczkowskiego A w lutym, C w marcu."""
    zajeci = {p.imie_nazwisko for p in firma.pracownicy.values()}
    return [k for k in pula if k["id"] not in firma.pracownicy and k["imie_nazwisko"] not in zajeci
            and k.get("tylko_dla", firma.nazwa) == firma.nazwa]   # kandydat z eventu w parku – tylko dla jednej firmy


def _kanal(dane: Dane, kandydat: dict, wybrany: str | None, runda: int, czas: cw.Czas, info: dict) -> str | None:
    """Kanał rekrutacji kandydata (gra z lokalami) i zajęcie czasu właściciela; None – nie da się zatrudnić."""
    mozliwe = rp.kanaly_kandydata(dane, kandydat, runda)
    if not mozliwe:
        return None
    kanaly = rp.kanaly(dane, runda)
    uwagi = info.setdefault("uwagi_rynku_pracy", [])
    if wybrany:
        if wybrany not in mozliwe:
            k = kanaly.get(wybrany)
            uwagi.append(f"{kandydat['imie_nazwisko']}: kanał „{k['nazwa'] if k else wybrany}” "
                         + (f"dostępny od rundy {k['od_rundy']}" if k and not k["dostepny"] else "nie obejmuje tego kandydata")
                         + " – nie zatrudniono.")
            return None
        mozliwe = [wybrany]
    for n in mozliwe:
        h = kanaly[n]["czas_wlasciciela"]
        if not h or czas.wez(h, f"{kanaly[n]['nazwa']}: wybór kandydata {kandydat['imie_nazwisko']}", "zatrudnienie"):
            return n
    uwagi.append(f"{kandydat['imie_nazwisko']}: brak czasu właściciela na rekrutację przez "
                 f"{kanaly[mozliwe[-1]]['nazwa']} – nie zatrudniono.")
    return None


def zastosuj(dane: Dane, firma: Firma, d: dict, runda: int, pula: list[dict], ceny_dostawcow: dict,
             ksiega: Ksiega, rachunek: Rachunek, lokale: bool = False) -> dict:
    """Wykonuje decyzje zakupowe i kadrowe (przed sprzedażą). Zwraca informacje do wyników (np. zakupy zasobów).
    `lokale` – gra z lokalami: nowe stanowiska tylko na wolnych miejscach działających lokali (lokal wybrany
    wcześniej, w silnik/lokale.py: wybierz)."""
    info = {"zakupy_zasobow": {}, "zatrudnieni": [], "zwolnieni": [], "inwestycje": 0.0, "sprzedany_majatek": 0.0,
            "szkolenia_procent": 0.0, "majatek_przed": firma.majatek}
    odbl = dane.odblokowane(runda)
    if d.get("nazwa"):
        firma.nazwa_wyswietlana = d["nazwa"]
    if "misja" in d:
        firma.misja = d["misja"]
    if "oferta" in d:
        nowa = {u: int(p or 0) for u, p in d["oferta"].items() if u in dane.uslugi}
        rundy = dane.katalog_ofert["rundy"]
        limit = limit_nowych_uslug(dane, runda, len(firma.oferta))
        dozwolone = rundy["uslugi_startowe"] if runda < rundy["nowe_uslugi_od_rundy"] else list(dane.uslugi)
        nowe = [u for u in nowa if u not in firma.oferta]
        wolne = max(0, len(firma.oferta) + limit - sum(u in firma.oferta for u in nowa))
        odrzucone = [u for u in nowe if u not in dozwolone] + [u for u in nowe if u in dozwolone][wolne:]
        firma.oferta = {u: p for u, p in nowa.items() if u not in odrzucone}
        if odrzucone:
            info["odrzucone_uslugi"] = odrzucone
        for u in firma.oferta:
            if u not in firma.uslugi_kiedykolwiek:
                firma.uslugi_kiedykolwiek.append(u)
    if "sprzedaz" in d and "sprzedaz" in odbl:
        firma.ceny = {u: Cena(cena=float(c["cena"]), rabat=float(c.get("rabat", 0) or 0))
                      for u, c in d["sprzedaz"].items() if c and c.get("cena")}
    if d.get("bank") and d["bank"] in dane.dostepne("banki", runda):
        firma.bank = d["bank"]
    if d.get("biuro") and (not lokale or bo.poprawny_wybor(dane, d["biuro"])):   # z lokalami: biura z mapy
        firma.biuro = d["biuro"]

    # stanowiska (działają od razu)
    pakiety = dane.katalog_ofert["stanowiska"]["pakiety"]
    miejsca = wolne_miejsca(dane, firma, runda) if lokale else None
    for typ, n in (d.get("stanowiska") or {}).items():
        n = int(n or 0)
        if n <= 0 or typ not in dane.typy_stanowisk:
            continue
        n = min(n, dane.maks_nowych_stanowisk)
        if miejsca is not None and n > len(miejsca[typ]):
            info.setdefault("odrzucone_stanowiska", {})[typ] = n - len(miejsca[typ])
            n = len(miejsca[typ])
            if n == 0:
                continue
        start = firma.nowy_nr(typ)
        for i in range(n):
            firma.stanowiska.append(Stanowisko(nr=start + i, typ=typ, od_rundy=runda,
                                               lokal=miejsca[typ][i] if miejsca is not None else None))
        st_trwale.zakup(dane, firma, ksiega, rachunek, f"Uruchomienie stanowiska: {dane.typy_stanowisk[typ]['kto']}",
                        f"Stanowiska: {dane.typy_stanowisk[typ]['kto']} (runda {runda})", "sprzet", pakiety[str(n)],
                        runda, lokale)
        firma.majatek += pakiety[str(n)]
        info["inwestycje"] += pakiety[str(n)]
        for lok_id in miejsca[typ][:n] if miejsca is not None else []:   # nakłady najemcy – rozliczenie ulepszeń
            lok = next(x for x in firma.lokale if x.id == lok_id)
            if lok.forma == "najem":
                lok.naklady += pakiety[str(n)] / n

    # sprzedaż i zakup sprzętu
    sprzet_ok, kadry_ok = "inwestycje_sprzet" in odbl, "hr_zatrudnienie" in odbl
    czas = cw.nowy(dane) if lokale else None   # czas właściciela: pracuj.pl, potem odbiór osobisty w dyskontach
    for e in zd.efekty_czasu(firma, runda) if lokale else []:   # skutki eventów w parkach (np. przeziębienie)
        czas.wez(e.wartosc, e.opis, zd.ZAKLADKA)
    for s in d.get("sprzet_sprzedaj", []) if sprzet_ok else []:
        st = firma.stanowisko(s["typ"], int(s["nr"]))
        if st and s["nazwa"] in st.sprzet and s["nazwa"] not in st.sprzet_wynajmujacego:
            q = st.sprzet.pop(s["nazwa"])
            st_trwale.sprzedaj(firma, f"{s['nazwa']} ({s['typ']} {s['nr']})", ksiega)
            ksieguj(firma, ksiega, rachunek, f"Sprzedaż sprzętu: {s['nazwa']}",
                    cena_sprzedazy_sprzetu(dane, dane.sprzet[s["nazwa"]]["ceny"][str(q)]), "przychod_pozostaly")
            wartosc = dane.sprzet[s["nazwa"]]["ceny"][str(q)]      # majątek po cenie zakupu (rozwój firmy)
            firma.majatek -= wartosc
            info["sprzedany_majatek"] += wartosc
    for s in d.get("sprzet_kup", []) if sprzet_ok else []:
        st = firma.stanowisko(s["typ"], int(s["nr"]))
        info_s = dane.sprzet.get(s["nazwa"])
        if not st or not info_s or s["nazwa"] in st.sprzet:
            continue
        if info_s["dla"] != st.typ:
            continue
        q = int(s.get("jakosc", 3))
        cena = info_s["ceny"][str(q)]
        st.sprzet[s["nazwa"]] = q
        st_trwale.zakup(dane, firma, ksiega, rachunek, f"Koszt zakupu: {s['nazwa']}", f"{s['nazwa']} ({s['typ']} {s['nr']})",
                        "sprzet", cena, runda, lokale)
        firma.majatek += cena
        info["inwestycje"] += cena

    # kadry
    for pid in d.get("zwolnij", []) if kadry_ok else []:
        p = firma.pracownicy.pop(pid, None)
        if p:
            st = firma.stanowisko(dane.typ_zawodu(p.zawod), p.stanowisko)
            if st:
                st.pracownik = None
            ksieguj(firma, ksiega, rachunek, f"Koszt zwolnienia {p.imie_nazwisko}", p.koszt_odprawy)   # opis jak w KPiR gry
            info["zwolnieni"].append(pid)
    for pid, zm in (d.get("zmiany") or {}).items():
        p = firma.pracownicy.get(pid)
        if not p:
            continue
        if zm.get("pensja"):
            p.pensja = float(zm["pensja"])
        if zm.get("umowa") in ("prace", "zlecenie"):
            p.umowa = zm["umowa"]
        p.premia = float(zm.get("premia", 0) or 0)
    for z in d.get("zatrudnij", []) if kadry_ok else []:
        dostepni = kandydaci_firmy(rp.widoczni(dane, pula, runda) if lokale else pula, firma)
        kandydat = next((k for k in dostepni if k["id"] == z["kandydat"]), None)
        if kandydat is None and z.get("zastepca"):
            # kandydata nie ma na liście: najbardziej podobny (gwiazdki, potem pensja)
            wzor = z.get("wzor") or {}
            podobni = [k for k in dostepni if k["zawod"] == wzor.get("zawod")]
            kandydat = min(podobni, key=lambda k: (abs(k["gwiazdki"] - wzor.get("gwiazdki", 2)), k["pensja_preferowana"]),
                           default=None)
        st = firma.stanowisko(z["typ"], int(z["nr"]))
        if not kandydat or not st or st.pracownik:
            info.setdefault("nieudane_zatrudnienia", []).append(z)
            continue
        if dane.typ_zawodu(kandydat["zawod"]) != st.typ:
            continue
        koszt = kandydat["koszt_rekrutacji"]
        if lokale:  # kanał rekrutacji: wskazany albo najtańszy, na który starcza czasu właściciela
            kanal = _kanal(dane, kandydat, z.get("kanal"), runda, czas, info)
            if kanal is None:
                info.setdefault("nieudane_zatrudnienia", []).append(z)
                continue
            koszt = rp.koszt(dane, kanal, kandydat)
        p = Pracownik(id=kandydat["id"], imie_nazwisko=kandydat["imie_nazwisko"], zawod=kandydat["zawod"],
                      gwiazdki=kandydat["gwiazdki"], pensja_preferowana=kandydat["pensja_preferowana"],
                      koszt_rekrutacji=kandydat["koszt_rekrutacji"], koszt_odprawy=kandydat["koszt_odprawy"],
                      zadowolenie_klientow=kandydat["zadowolenie_klientow"], ryzyko_reklamacji=kandydat["ryzyko_reklamacji"],
                      pensja=float(z.get("pensja") or kandydat["pensja_preferowana"]), umowa=z.get("umowa", "prace"),
                      od_rundy=runda, stanowisko=st.nr)
        firma.pracownicy[p.id] = p
        st.pracownik = p.id
        ksieguj(firma, ksiega, rachunek, f"Koszt zatrudnienia: {p.imie_nazwisko}", koszt)
        info["zatrudnieni"].append(p.id)
        if lokale:
            info.setdefault("kanaly_zatrudnienia", []).append({"pracownik": p.id, "imie_nazwisko": p.imie_nazwisko,
                                                               "kanal": kanal, "koszt": koszt, "pensja": p.pensja})

    # zasoby od dostawców
    zakupy, zamowienia, stawki = {}, [], {}
    for z in d.get("zamowienia", []) if "dostawcy" in odbl else []:
        ilosc = float(z.get("ilosc") or 0)
        cena = cena_dostawcy(dane, ceny_dostawcow, z["dostawca"], z["zasob"], int(z["jakosc"]))
        if ilosc > 0 and cena is not None:
            zamowienia.append({**z, "ilosc": ilosc, "cena": cena})
    if lokale:  # dni dostaw, limity dyskontów, minimalne zamówienie, opłaty za dowóz, czas właściciela (silnik/dostawcy.py)
        zamowienia, info["dostawy"] = zasady_dostaw(dane, zamowienia, dane.data_rundy(runda),
                                                    (dane.data_rundy(runda + 1) - dane.data_rundy(runda)).days, czas)
        info["czas_wlasciciela"] = czas.podsumowanie()
    for z in zamowienia:
        ilosc, cena = z["ilosc"], z.pop("cena")
        k = f"{z['zasob']}|{int(z['jakosc'])}"
        firma.magazyn[k] = firma.magazyn.get(k, 0.0) + ilosc
        firma.wartosc_magazynu_gr[k] = firma.wartosc_magazynu_gr.get(k, 0) + grosze(ilosc * cena)
        if lokale:  # partia z dniem dostawy (świeżość); magazyn do końca decyzji = stan + zamówione
            dni = (dane.data_rundy(runda + 1) - dane.data_rundy(runda)).days
            dzien = min(max(0, int(z.get("dzien") or 0)), dni - 1)
            firma.partie.append(sw.nowa_partia(dane, z["zasob"], int(z["jakosc"]), ilosc, cena,
                                               dane.data_rundy(runda) + timedelta(days=dzien), z["dostawca"], runda))
        zakupy[z["dostawca"]] = zakupy.get(z["dostawca"], 0.0) + ilosc * cena
        s, sv = stawki.setdefault(z["dostawca"], {}), rz.stawka_zasobu(dane, z["zasob"]) or 0.0   # VAT wg składnika
        s[sv] = s.get(sv, 0.0) + ilosc * cena
        info["zakupy_zasobow"].setdefault(z["dostawca"], []).append({**z, "cena": cena, "wartosc": round(ilosc * cena, 2)})
    for dostawca, kwota in zakupy.items():
        ksieguj(firma, ksiega, rachunek, f"Zakup zasobu od dostawcy: {dostawca}", kwota, "towary", stawki=stawki[dostawca])
    for dostawca, kwota in info.get("dostawy", {}).get("oplaty", {}).items():
        ksieguj(firma, ksiega, rachunek, f"Koszt dostawy: {dostawca}", kwota)

    # udogodnienia i wyposażenie
    for rodzaj, nazwa_pozycji in (("udogodnienia", "udogodnień"), ("wyposazenie", "wyposażenia")):
        if f"hr_{rodzaj}" not in odbl and f"inwestycje_{rodzaj}" not in odbl:
            continue
        pozycje = dane.pozycje(rodzaj)
        posiadane = getattr(firma, rodzaj)
        for n in d.get(f"{rodzaj}_sprzedaj", []):
            if n in posiadane:
                posiadane.remove(n)
                st_trwale.sprzedaj(firma, n, ksiega)
                ksieguj(firma, ksiega, rachunek, f"Sprzedaż {nazwa_pozycji}: {n}",
                        pozycje[n]["cena"] * dane.z["finanse"]["sprzedaz_udogodnien"], "przychod_pozostaly")
                firma.majatek -= pozycje[n]["cena"]
                info["sprzedany_majatek"] += pozycje[n]["cena"]
        for n in d.get(f"{rodzaj}_kup", []):
            if n in pozycje and n not in posiadane and pozycje[n]["od_rundy"] <= runda:
                posiadane.append(n)
                st_trwale.zakup(dane, firma, ksiega, rachunek, f"Koszt zakupu: {n}", n,   # opis jak w KPiR gry
                                "sprzet" if rodzaj == "udogodnienia" else "wyposazenie", pozycje[n]["cena"], runda, lokale)
                firma.majatek += pozycje[n]["cena"]
                info["inwestycje"] += pozycje[n]["cena"]

    # marketing (gra z lokalami: kampanie agencji reklamowych zamiast reklamy z Revasa)
    agencje = lokale and rk.zasady(dane) is not None
    if agencje:
        info["kampanie"] = rk.zamow(dane, firma, d, runda, ksiega, rachunek)
    if lokale and pm.zasady(dane):
        info["promocje"] = pm.ustaw(dane, firma, d, runda, ksiega, rachunek)
    if "marketing_tradycyjny" in odbl and not agencje:
        from .rynek import koszt_emisji
        media = dane.dostepne("media_tradycyjne", runda)
        for medium, emisje in (d.get("reklama_tradycyjna") or {}).items():
            if medium in media and int(emisje or 0) > 0:
                ksieguj(firma, ksiega, rachunek, f"Reklama tradycyjna: {medium}", koszt_emisji(media[medium], int(emisje)))
    if "marketing_internetowy" in odbl and not agencje:
        narzedzia = dane.dostepne("narzedzia_internetowe", runda)
        for n in d.get("internet_wylacz", []):
            firma.internet.pop(n, None)
        for n in d.get("internet_uruchom", []):
            if n in narzedzia and n not in firma.internet:
                firma.internet[n] = runda
                ksieguj(firma, ksiega, rachunek, f"Uruchomienie reklamy internetowej: {n}", narzedzia[n]["uruchomienie"])

    # szkolenia (koszt łączny w firmie szkoleniowej, efekt w tym miesiącu)
    if "hr_szkolenia" in odbl:
        szk = dane.katalog_ofert["szkolenia"]
        firmy = [f["nazwa"] for f in szk["firmy"]]
        pozycje = {p["nazwa"]: p for p in szk["pozycje"]}
        koszty = {}
        for s in d.get("szkolenia", []):
            if s.get("szkolenie") in pozycje and s.get("firma") in firmy:
                p = pozycje[s["szkolenie"]]
                koszty[s["firma"]] = koszty.get(s["firma"], 0) + p["ceny"][firmy.index(s["firma"])]
                info["szkolenia_procent"] += p["procent"] / 100
        for f, kwota in koszty.items():
            ksieguj(firma, ksiega, rachunek, f"Szkolenie w firmie: {f}", kwota)
    if lokale and aw.dane_wypadkow(dane):   # polisy i składki – po inwestycjach (składka od majątku)
        info["ubezpieczenia"] = aw.ustaw(dane, firma, d, runda, ksiega, rachunek)
    return info


def gotowe_uslugi(dane: Dane, firma: Firma) -> dict[str, list[str]]:
    """Dla dań z oferty: lista braków (pusta = danie może być sprzedawane)."""
    braki = {}
    rec = kasjerzy(dane, firma)
    kuchnia, kasa = dane.typy_stanowisk[KUCHNIA]["kto"], dane.typy_stanowisk[KASA]["kto"]
    for u in firma.oferta:
        b = []
        if not stanowiska_uslugi(dane, firma, u):
            b.append(f"brak stanowiska z pracownikiem ({kuchnia.lower()}: {dane.uslugi[u]['prowadzacy'].lower()}) "
                     "i całym sprzętem dania")
        if not rec:
            b.append(f"brak obsadzonego stanowiska ({kasa.lower()}) z kompletem sprzętu")
        if u not in firma.ceny:
            b.append("nie jest włączone do sprzedaży (brak ceny)")
        for z in dane.uslugi[u]["zasoby"]:
            if sw.dostepne(dane, firma.magazyn, z) <= 1e-9:
                b.append(f"brak składnika: {z}")
        braki[u] = b
    return braki


def lista_bledow(dane: Dane, firma: Firma, d: dict, runda: int, poprzednia_oferta: list[str],
                 tryb_kredytu: str = "jednoczesnie", lokal: dict | None = None, info: dict | None = None) -> list[dict]:
    """Ostrzeżenia jak w zakładce „Lista błędów”: czerwone (poważne), pomarańczowe, niebieskie (informacyjne).
    `lokal` – w grze z lokalami wynik decyzji o lokalu (silnik/lokale.py: wybierz; None – gra bez lokali),
    `info` – wynik `zastosuj` (odrzucone stanowiska)."""
    wynik = []

    def dodaj(poziom, zakladka, tekst):
        wynik.append({"poziom": poziom, "zakladka": zakladka, "tekst": tekst})

    if lokal is not None:
        bledy_lokali(dane, firma, runda, lokal, dodaj)
        for poziom, tekst in sw.ostrzezenia(dane, firma, runda):
            dodaj(poziom, "swiezosc", tekst)
        for tekst in (info or {}).get("dostawy", {}).get("uwagi", []):
            dodaj("czerwony", "dostawcy", tekst)
        for tekst in (info or {}).get("uwagi_rynku_pracy", []):
            dodaj("czerwony", "zatrudnienie", tekst)
        for tekst in ((info or {}).get("kampanie") or {}).get("uwagi", []):
            dodaj("czerwony", rk.ZAKLADKA, tekst)
        for tekst in ((info or {}).get("promocje") or {}).get("uwagi", []):
            dodaj("czerwony", pm.ZAKLADKA, tekst)
        for b in aw.bledy((info or {}).get("ubezpieczenia")):
            dodaj(b["poziom"], b["zakladka"], b["tekst"])
        for b in bo.bledy(dane, firma, d):
            dodaj(b["poziom"], b["zakladka"], b["tekst"])
        # przekroczenia odrzuca zapis decyzji (API), a przeliczenie przycina – tu czerwone są w uwagach rynku pracy i lokali
        lim = lm.stan_limitow(dane, firma, d, runda)
        if lim["pracownicy"]["nowi"] == lim["pracownicy"]["limit"]:
            dodaj("niebieski", "zatrudnienie", f"Wykorzystany limit nowych pracowników w tej rundzie "
                  f"({lim['pracownicy']['limit']}) – kolejnych przyjmiesz w następnej rundzie.")
        if firma.lokale and runda < lim["lokal"]["od_rundy"]:
            dodaj("niebieski", "lokale", f"Kolejny lokal możesz wziąć od rundy {lim['lokal']['od_rundy']}.")
        for typ, n in (info or {}).get("odrzucone_stanowiska", {}).items():
            dodaj("czerwony", "stanowiska", f"Brak miejsca w lokalach na {n} {dane.typy_stanowisk[typ]['nazwa'].lower()} "
                  "– nie zostały uruchomione. Weź większy lub kolejny lokal.")

    rundy = dane.katalog_ofert["rundy"]
    oferta = d.get("oferta") or firma.oferta
    przyrost = len(oferta) - len(poprzednia_oferta)
    limit = limit_nowych_uslug(dane, runda, len(poprzednia_oferta))
    if runda == 1:
        spoza = [u for u in (d.get("oferta") or {}) if u not in rundy["uslugi_startowe"]]
        if spoza:
            dodaj("czerwony", "oferta", "W rundzie 1 można wybrać tylko dania: "
                  + ", ".join(dane.uslugi[u]["nazwa"] for u in rundy["uslugi_startowe"]) + ".")
    if przyrost > limit or (d.get("oferta") and set(d["oferta"]) - set(firma.oferta)):
        dodaj("czerwony", "oferta", f"W tej rundzie liczba dań może wzrosnąć najwyżej o {limit} – nadmiarowe nie zostały dodane.")
    if not firma.bank and not d.get("bank"):
        dodaj("czerwony", "finanse_bank", "Nie wybrano banku.")
    if not firma.biuro and not d.get("biuro"):
        dodaj("czerwony", "finanse_biuro", "Nie wybrano biura rachunkowego.")
    placa_min = dane.z["finanse"]["placa_minimalna"]
    for z in d.get("zatrudnij", []):
        if float(z.get("pensja") or placa_min) < placa_min:
            dodaj("czerwony", "hr_zatrudnienie", f"Pensja poniżej płacy minimalnej ({placa_min} PLN).")
    if runda >= 2:
        for u, braki in gotowe_uslugi(dane, firma).items():
            for b in braki:
                dodaj("czerwony", "oferta", f"{dane.uslugi[u]['nazwa']}: {b}.")
        for u in firma.oferta:
            if not firma.oferta.get(u):
                dodaj("niebieski", "oferta", f"{dane.uslugi[u]['nazwa']}: nie podano prognozy popytu.")
    puste = [s for s in firma.stanowiska if not s.pracownik]
    if puste and runda >= 2:
        dodaj("niebieski", "hr_zatrudnienie", f"Puste stanowiska: {len(puste)} (nie generują kosztów).")
    if firma.gotowka < 0:
        if tryb_kredytu == "na_biezaco":
            dodaj("pomaranczowy", "finanse_bank", "Wydatki przekraczają saldo konta – zostanie uruchomiony kredyt odnawialny "
                  f"(ok. {-firma.gotowka:,.0f} PLN).".replace(",", " "))
        else:
            dodaj("niebieski", "finanse_bank", "Wydatki przekraczają saldo konta. Jeśli przychody z tej rundy ich nie pokryją, "
                  "uruchomi się kredyt odnawialny na brakującą kwotę.")
    return wynik
