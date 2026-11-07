"""Wnioski z rundy (gra z lokalami): co poszło dobrze, co nie wyszło i co zrobić w kolejnej rundzie.

Reguły na wynikach firmy z jednej rundy (`wyniki[r][firma]`, silnik/runda.py) – bez losowania i bez nowych
obliczeń. Ton zachęcający: najpierw to, co się udało, potem konkretna rada z zakładką, w której ją wykonać.
Progi: `dane/zalozenia.yaml: wnioski` (oraz `lista_bledow.przeterminowanie_min_zl`).
"""
from __future__ import annotations

from ..dane import Dane
from ..pieniadze.zaleglosci import zl

# przyczyna utraconej sprzedaży (silnik/kuchnia/operacje.py) → (tytuł, rada, zakładka)
_PRZYCZYNY = {
    "pracownicy/sprzęt": ("W kuchni zabrakło rąk albo sprzętu",
                          "Dodajcie stanowisko kuchenne, zatrudnijcie kucharza albo kupcie szybszy sprzęt – kuchnia "
                          "przygotuje więcej porcji i nikt nie odejdzie z kolejki.", "stanowiska"),
    "brak stanowiska z pracownikiem i sprzętem": (
        "Danie bez gotowego stanowiska",
        "Każde danie z menu potrzebuje stanowiska kuchennego z kompletem sprzętu i kucharzem – sprawdźcie zakładki "
        "Stanowiska, Sprzęt i Zatrudnienie.", "stanowiska"),
    "kasa": ("Kolejka przy kasie",
             "Dodajcie kasjera albo stanowisko kasowe – jedna kasa obsłuży tylko część chętnych.", "zatrudnienie"),
    "zasoby": ("Zabrakło składników",
               "Zamówcie więcej u dostawców: zamówienie liczcie z prognozy popytu w Menu, a dostawy rozłóżcie na dni "
               "tygodnia.", "dostawcy"),
}
_KOSZTY = {
    "towary": "Najwięcej kosztowały składniki – zamawiajcie według prognozy i sprawdźcie, czy cena dania pokrywa "
              "koszt jego składników.",
    "wynagrodzenia": "Najwięcej kosztowały pensje – sprawdźcie w HR, czy każdy pracownik ma co robić (wykorzystanie "
                     "czasu).",
    "pozostale": "Najwięcej kosztowały pozostałe wydatki (czynsz, utrzymanie, reklama, amortyzacja) – to koszty "
                 "stałe, więc każdy dodatkowy klient rozkłada je na więcej kebabów.",
}


def _rada(tytul: str, co: str, rada: str, zakladka: str) -> dict:
    return {"tytul": tytul, "co": co, "rada": rada, "zakladka": zakladka}


def _lista(nazwy: list[str]) -> str:
    return ", ".join(nazwy)


def wnioski(dane: Dane, w: dict | None, wp: dict | None = None) -> dict | None:
    """{"dobre": [tekst], "do_poprawy": [{tytul, co, rada, zakladka}]} z wyników firmy; None – brak wyników.
    `wp` – wyniki poprzedniej rundy (UF23: wzrost sprzedaży i dochodu z liczbami)."""
    if not w:
        return None
    p = dane.z["wnioski"]
    dobre, poprawa = [], []
    sprzedaz = w.get("sprzedaz") or {}
    nazwa = lambda u: dane.uslugi[u]["nazwa"]   # noqa: E731
    klienci = round(sum(v["sprzedaz"] for v in sprzedaz.values()))
    utraceni = round(sum(v["utracona"] for v in sprzedaz.values()))
    netto = w["kpir"]["dochod_netto"]

    # co się udało
    if klienci:
        dobre.append(f"Obsłużyliście {klienci} klientów.")
        if not utraceni:
            dobre.append("Nikt nie odszedł z kolejki – kuchnia, kasa i składniki dały radę.")
    if netto > 0:
        dobre.append(f"Runda na plusie: {zl(netto)} dochodu netto.")
    przed = _liczby(wp)
    if przed.get("klienci") and klienci > przed["klienci"] * (1 + dane.z["wnioski"]["wzrost_klientow"]):   # UF23: wzrost względem poprzedniej rundy
        dobre.append(f"Klientów więcej niż tydzień wcześniej: {round(przed['klienci'])} → {klienci} "
                     f"(+{round(100 * (klienci / przed['klienci'] - 1))}%).")
    if przed.get("dochod_netto") is not None and netto > 0 and netto > przed["dochod_netto"] + 1:
        dobre.append(f"Dochód netto lepszy niż tydzień wcześniej o {zl(netto - przed['dochod_netto'])}.")
    ks = w.get("ksiegowosc") or {}
    if ks.get("tryb") == "deklaracja" and not ks.get("kara"):
        dobre.append("Deklaracje złożone samodzielnie i bez błędów.")
    lokale = w.get("lokale")
    if lokale and not klienci:
        dobre.append("Macie lokal – to pierwszy i najważniejszy krok.")

    # brak sprzedaży – zwykle start gry
    if lokale is not None and not klienci:
        if not lokale:
            poprawa.append(_rada("Firma nie ma jeszcze lokalu", "Bez lokalu nie ma sprzedaży.",
                                 "Wybierzcie lokal na mapie albo w Nowe lokale ▸ Do wynajęcia – wynajem ruszy od razu, "
                                 "a lokal do urządzenia albo działkę możecie wyposażać już w ostatniej rundzie prac.",
                                 "lokale"))
        elif not any(lok["dziala"] for lok in lokale):
            od = min(lok["dziala_od"] for lok in lokale)
            poprawa.append(_rada("Lokal jeszcze się szykuje", f"Sprzedaż ruszy w rundzie {od}.",
                                 "Wykorzystajcie ten czas: ułóżcie menu i ceny, kupcie stanowiska i sprzęt, zatrudnijcie "
                                 "ludzi i zamówcie składniki – lokal otworzy się od razu gotowy.", "oferta"))
        else:
            poprawa.append(_rada("Lokal działał, ale nic nie sprzedano",
                                 "Klienci nie mieli czego kupić.",
                                 "Sprawdźcie po kolei: dania w Menu, ceny w Sprzedaży, stanowiska ze sprzętem i ludźmi "
                                 "oraz składniki w magazynie. Lista błędów pokaże, czego brakuje.", "lista_bledow"))

    # utracona sprzedaż – według przyczyny
    grupy: dict[str, list[str]] = {}
    for u, v in sprzedaz.items():
        if v["popyt"] and v["utracona"] / v["popyt"] >= p["utracona"]:
            przyczyna = v.get("przyczyna") or ""
            klucz = "zasoby" if przyczyna.startswith("zasoby") else przyczyna
            opis = f"{nazwa(u)} ({round(v['utracona'])} z {round(v['popyt'])} chętnych"
            grupy.setdefault(klucz, []).append(opis + (f", brak: {przyczyna.removeprefix('zasoby (').rstrip(')')})" if klucz == "zasoby" else ")"))
    for klucz, dania in grupy.items():
        tytul, rada, zakladka = _PRZYCZYNY.get(klucz, ("Część klientów odeszła bez kebaba",
                                                       "Sprawdźcie, czego zabrakło: stanowisk, ludzi czy składników.",
                                                       "stanowiska"))
        poprawa.append(_rada(tytul, f"Odeszli klienci: {_lista(dania)}.", rada, zakladka))

    # prognoza popytu (Menu) a prawdziwy popyt
    za_nisko, za_wysoko = [], []
    for u, v in sprzedaz.items():
        if v["popyt"] <= 0:
            continue
        odch = (v["prognoza"] - v["popyt"]) / v["popyt"]
        opis = f"{nazwa(u)} (prognoza {round(v['prognoza'])}, popyt {round(v['popyt'])})"
        if odch <= -p["prognoza"]:
            za_nisko.append(opis)
        elif odch >= p["prognoza"]:
            za_wysoko.append(opis)
    if za_nisko:
        poprawa.append(_rada("Chętnych było więcej, niż zakładała prognoza", _lista(za_nisko) + ".",
                             "Podnieście prognozę w Kuchni – według niej zamawiacie składniki i planujecie kuchnię. "
                             "Pomogą pule klientów stref i wydarzenia w Klienci ▸ Strefy i Klienci ▸ Kalendarz.", "oferta"))
    if za_wysoko:
        poprawa.append(_rada("Prognoza była wyższa niż popyt", _lista(za_wysoko) + ".",
                             "Obniżcie prognozę w Menu albo przyciągnijcie klientów ceną, promocją lub reklamą – "
                             "nadmiar składników może się przeterminować.", "oferta"))

    # magazyn i sanepid
    sanepid = (w.get("magazyn") or {}).get("sanepid") or {}
    if sanepid.get("przeterminowane", 0) >= dane.z["lista_bledow"]["przeterminowanie_min_zl"]:
        poprawa.append(_rada("Część składników się przeterminowała",
                             f"Wyrzucony towar był wart {zl(sanepid['przeterminowane'])}.",
                             "Zamawiajcie mniejsze partie, częściej i bliżej prognozy – terminy przydatności widać "
                             "w Zaopatrzenie ▸ Dostawy.", "swiezosc"))
    if sanepid.get("mandat"):
        poprawa.append(_rada("Mandat z sanepidu", f"Kontrola zakończyła się mandatem {zl(sanepid['mandat'])}.",
                             "Ryzyko kontroli rośnie z przeterminowanym towarem i wynajętą chłodnią – trzymajcie "
                             "mniejszy zapas i zadbajcie o higienę (Urzędy ▸ Sanepid).", "urzad"))

    # reklamacje
    reklamacje = round(sum(v["reklamacje"] for v in sprzedaz.values()))
    if reklamacje:
        poprawa.append(_rada("Klienci reklamowali dania", f"Reklamacji: {reklamacje}.",
                             "Reklamacje biorą się z jakości – sprawdźcie gwiazdki składników u dostawców i stan "
                             "sprzętu w kuchni.", "dostawcy"))

    # księgowość
    if ks.get("kara"):
        poprawa.append(_rada("Mandat za deklaracje", f"Urząd naliczył {zl(ks['kara'])} mandatu.",
                             "W Księgowość ▸ Biuro rachunkowe (wyniki) widać, która deklaracja się nie zgadzała. Nad tabelą "
                             "dokumentów jest instrukcja krok po kroku – albo powierzcie księgowość biuru.", "biuro"))
    blad_biura = (w.get("biuro") or {}).get("blad")
    if blad_biura and not blad_biura.get("oc"):
        poprawa.append(_rada("Biuro rachunkowe pomyliło się w deklaracji",
                             f"Mandat {zl(blad_biura['kara'])} zapłaciła firma, bo biuro nie ma OC.",
                             "Rozważcie biuro z ubezpieczeniem OC – wtedy to ono oddaje mandat.", "biuro"))

    # wynik i pieniądze
    kpir = w["kpir"]
    if netto < 0:
        koszty = {k: kpir.get(k, 0) for k in _KOSZTY}
        najwiekszy = max(koszty, key=koszty.get)
        poprawa.append(_rada("Runda na minusie",
                             f"Przychody {zl(kpir['przychody'])}, koszty {zl(kpir['koszty'])}. Strata na starcie "
                             "jest normalna – dopiero inwestujecie.", _KOSZTY[najwiekszy], "kpir"))
    if w.get("kredyt_odnawialny", 0) > 0:
        poprawa.append(_rada("Na koncie zabrakło pieniędzy",
                             f"Firma korzysta z kredytu odnawialnego: {zl(w['kredyt_odnawialny'])}.",
                             "Zostawcie zapas gotówki na pensje i dostawy albo weźcie w banku kredyt z lepszym "
                             "oprocentowaniem, zanim zabraknie.", "bank"))

    # czerwone punkty listy błędów z tej rundy (gdy nie powtarzają rad wyżej)
    zakladki = {r["zakladka"] for r in poprawa}
    czerwone = [b for b in w.get("lista_bledow") or [] if b["poziom"] == "czerwony" and b["zakladka"] not in zakladki]
    for b in czerwone[:p["bledy_max"]]:
        poprawa.append(_rada("Sygnał z listy błędów", b["tekst"],
                             "Ten punkt był na czerwono przed przeliczeniem. Zajrzyjcie do listy błędów przed "
                             "wysłaniem decyzji – podpowiada na bieżąco.", b["zakladka"]))

    if not dobre:
        dobre.append("Każda firma zaczyna od zera – poniżej plan na kolejną rundę.")
    return {"dobre": dobre, "do_poprawy": poprawa}


# U16: „Dlaczego mój wynik się zmienił?” – 1–3 zdania z porównania kart dwóch kolejnych rund
WSKAZNIKI = {"wynik_ekonomiczny": "wynik ekonomiczny", "zadowolenie_pracownikow": "zadowolenie pracowników",
             "zadowolenie_klientow": "zadowolenie klientów", "rozwoj_firmy": "rozwój firmy",
             "wskaznik_zadluzenia": "wskaźnik zadłużenia"}


def _liczba(x: float) -> str:
    return f"{x:.2f}".replace(".", ",").replace("-", "−")


def _wynik(dane: Dane, k: dict) -> float:
    """Wynik działalności z wskaźników karty – jak silnik/wyniki/karta.py: karta (przy stracie bez mnożenia)."""
    we = k["wynik_ekonomiczny"]
    if we < 0:
        return we * dane.z["karta_wynikow"]["strata"]["waga"]
    return we * k["zadowolenie_pracownikow"] * k["zadowolenie_klientow"] * k["rozwoj_firmy"] * k["wskaznik_zadluzenia"]


def _pozycje(kpir: dict) -> dict[str, float]:
    """Saldo pozycji KPiR (przychód − koszt) pogrupowane po opisie przed dwukropkiem („Czynsz najmu: ul. …”)."""
    wynik: dict[str, float] = {}
    for p in kpir.get("pozycje") or []:
        klucz = p["opis"].split(":")[0].strip()
        wynik[klucz] = wynik.get(klucz, 0.0) + p.get("przychod", 0) + p.get("przychod_pozostaly", 0)             - p.get("towary", 0) - p.get("wynagrodzenia", 0) - p.get("pozostale", 0)
    return wynik


def dlaczego(dane: Dane, w: dict | None, wp: dict | None) -> list[str] | None:
    """Zdania o zmianie wyniku działalności między rundą poprzednią (wp) a ostatnią (w); None – brak karty w.
    Pierwsza karta (runda przygotowawcza bez karty) – porównanie z zerem: wynik ekonomiczny 0, KPiR bez pozycji.
    Przyczyna: wskaźnik, którego sama zmiana (przy pozostałych z poprzedniej rundy) najbardziej przesuwa wynik;
    przy wyniku ekonomicznym – pozycja KPiR o największej zmianie w tę samą stronę."""
    k, kp = (w or {}).get("karta"), (wp or {}).get("karta")
    if not k:
        return None
    pierwsza = not kp
    if pierwsza:
        kp, wp = {**k, "wynik_ekonomiczny": 0.0, "wynik_dzialalnosci": 0.0}, {"kpir": {"dochod_netto": 0.0, "pozycje": []}}
    a, b = kp["wynik_dzialalnosci"], k["wynik_dzialalnosci"]
    if abs(b - a) < dane.z["wnioski"]["dlaczego_min"] and not pierwsza:
        return [f"Wynik działalności prawie się nie zmienił ({_liczba(a)} → {_liczba(b)})."]
    zdania = [f"Pierwsza karta wyników: wynik działalności {_liczba(b)}." if pierwsza
              else f"Wynik działalności {'wzrósł' if b > a else 'spadł'} z {_liczba(a)} do {_liczba(b)}."]
    wplyw = {s: _wynik(dane, {**kp, s: k[s]}) - a for s in WSKAZNIKI}
    zgodne = [s for s in WSKAZNIKI if wplyw[s] * (b - a) > 0] or list(WSKAZNIKI)
    glowny = max(zgodne, key=lambda s: abs(wplyw[s]))
    if glowny == "wynik_ekonomiczny":
        dn, dnp = w["kpir"]["dochod_netto"], wp["kpir"]["dochod_netto"]
        zmiana = "zysk zamienił się w stratę" if dnp > 0 > dn else "strata zamieniła się w zysk" if dn > 0 > dnp             else f"dochód netto {'wzrósł' if dn > dnp else 'spadł'}"
        zdanie = f"Dochód netto: {zl(dn)}" if pierwsza             else f"Najwięcej zmienił wynik ekonomiczny: {zmiana} ({zl(dnp)} → {zl(dn)})"
        teraz, przed = _pozycje(w["kpir"]), _pozycje(wp["kpir"])
        roznice = {p: teraz.get(p, 0.0) - przed.get(p, 0.0) for p in set(teraz) | set(przed)}
        kierunek = [p for p in roznice if roznice[p] * (dn - dnp) > 0]
        if kierunek:
            p = max(kierunek, key=lambda x: abs(roznice[x]))
            rodzaj = "przychód" if teraz.get(p, 0.0) + przed.get(p, 0.0) > 0 else "koszt"
            zdanie += f" – najbardziej zaważył {rodzaj} „{p}”: {zl(abs(teraz.get(p, 0.0)))}"                       + ("" if pierwsza else f", rundę wcześniej {zl(abs(przed.get(p, 0.0)))}")
        zdania.append(zdanie + ".")
    else:
        zdania.append(f"Najwięcej zmienił wskaźnik „{WSKAZNIKI[glowny]}”: {_liczba(kp[glowny])} → {_liczba(k[glowny])}.")
    if k["wynik_ekonomiczny"] < 0:
        zdania.append("Przy stracie wynik działalności to sam (ujemny) wynik ekonomiczny – zadowolenie i rozwój "
                      "zaczną się liczyć, gdy firma wyjdzie na plus.")
    return zdania


# UF23: „Tydzień w liczbach” – nagłówek karty wyników i wniosków: najważniejsze liczby rundy z poprzednią rundą
# (strzałki w panelu) i 1–3 zdania-historie tygodnia (najlepszy dzień, najchętniej brane danie, co zjadło zysk)
DNI = {"pn": "poniedziałek", "wt": "wtorek", "śr": "środa", "czw": "czwartek", "pt": "piątek", "sob": "sobota",
       "nd": "niedziela"}
KOSZTY = {"towary": "składniki", "wynagrodzenia": "pensje", "pozostale": "pozostałe koszty (czynsz, utrzymanie, reklama)"}


def _liczby(w: dict | None) -> dict[str, float | None]:
    if not w:
        return {}
    sp = (w.get("sprzedaz") or {}).values()
    kpir = w.get("kpir") or {}
    return {"klienci": sum(v["sprzedaz"] for v in sp), "utracona": sum(v["utracona"] for v in sp),
            "przychody": kpir.get("przychody"), "koszty": kpir.get("koszty"),
            "dochod_netto": kpir.get("dochod_netto"), "gotowka": w.get("gotowka")}


def tydzien(dane: Dane, w: dict | None, wp: dict | None) -> dict | None:
    """{"liczby": [{klucz, etykieta, wartosc, poprzednia, format, lepiej}], "zdania": [tekst]}; None – brak wyników.
    `lepiej` 1 – więcej znaczy lepiej, −1 – mniej (utracona sprzedaż, koszty); `poprzednia` None w pierwszej rundzie."""
    if not w:
        return None
    teraz, przed = _liczby(w), _liczby(wp)
    opis = [("klienci", "Obsłużeni klienci", "liczba", 1), ("utracona", "Odeszli bez kebaba", "liczba", -1),
            ("przychody", "Przychody", "zl", 1), ("koszty", "Koszty", "zl", -1),
            ("dochod_netto", "Dochód netto", "zl", 1), ("gotowka", "Saldo konta", "zl", 1)]
    liczby = [{"klucz": k, "etykieta": e, "wartosc": teraz[k], "poprzednia": przed.get(k), "format": f, "lepiej": lp}
              for k, e, f, lp in opis if teraz.get(k) is not None]
    zdania = []
    dni = [d for d in ((w.get("klienci") or {}).get("dni") or []) if d.get("sprzedaz")]
    if dni:
        naj = max(dni, key=lambda d: d["sprzedaz"])
        zdania.append(f"Najlepszy dzień: {DNI.get(naj['dzien'], naj['dzien'])} – {round(naj['sprzedaz'])} klientów"
                      + (f", {round(naj['utracona'])} odeszło bez kebaba." if naj.get("utracona", 0) >= 1 else "."))
    sprzedaz = {u: v for u, v in (w.get("sprzedaz") or {}).items() if v["sprzedaz"] > 0}
    if sprzedaz:
        u = max(sprzedaz, key=lambda x: sprzedaz[x]["sprzedaz"])
        razem = sum(v["sprzedaz"] for v in sprzedaz.values())
        zdania.append(f"Najchętniej brane: {dane.uslugi[u]['nazwa']} – {round(sprzedaz[u]['sprzedaz'])} porcji "
                      f"({round(100 * sprzedaz[u]['sprzedaz'] / razem)}% sprzedaży).")
    kpir = w.get("kpir") or {}
    koszty = {k: kpir.get(k, 0) for k in KOSZTY}
    if any(koszty.values()):
        k = max(koszty, key=koszty.get)
        przych = kpir.get("przychody") or 0
        # największa pozycja KPiR – tylko gdy mówi coś więcej niż grupa („Zakup zasobu” przy składnikach nie mówi)
        pozycje = {p: -x for p, x in _pozycje(kpir).items() if x < 0} if k != "towary" else {}
        poz = max(pozycje, key=pozycje.get) if pozycje else None
        zdania.append((f"Zysk najbardziej zjadły {KOSZTY[k]}: " if przych > 0 else f"Najwięcej kosztowały {KOSZTY[k]}: ")
                      + zl(koszty[k])
                      + (f" ({round(100 * koszty[k] / przych)} gr z każdej złotówki przychodu)" if przych > 0 else "")
                      + (f"; największa pozycja – „{poz}”: {zl(pozycje[poz])}." if poz else "."))
    return {"liczby": liczby, "zdania": zdania}
