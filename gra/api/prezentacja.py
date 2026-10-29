"""Dane dla interfejsu: wszystko, czego potrzebuje strona firmy w danej rundzie (jeden słownik JSON)."""
from __future__ import annotations

from silnik import harmonogram as hm
from silnik.dane import Dane
from silnik.decyzje import (
    cena_sprzedazy_sprzetu,
    gotowe_uslugi,
    kandydaci_firmy,
    lista_bledow,
    zastosuj,
)
from silnik.gra import Gra
from silnik.ksiegowosc import biuro as bo
from silnik.ksiegowosc import rozliczenie as rz
from silnik.ksiegowosc import urzad as urz
from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.ksiegowosc.srodki_trwale import ewidencja
from silnik.kuchnia import magazyn as mag
from silnik.kuchnia import swiezosc
from silnik.kuchnia.dostawcy import ceny_rundy, oferta_rundy
from silnik.kuchnia.dostawcy import info as info_dostawcy
from silnik.ludzie import czas_wlasciciela as cw
from silnik.ludzie import rynek_pracy as rp
from silnik.model import Firma, do_slownika
from silnik.nieruchomosci import przejecia as pr
from silnik.nieruchomosci.lokale import (
    dostepne,
    komunikat_odpoczynku,
    koszt_wejscia,
    runda_nowego_lokalu,
    stan_lokali,
    wybierz,
    zajete,
)
from silnik.pieniadze import banki as bk
from silnik.pieniadze import kasyno as kas
from silnik.pieniadze import lichwiarz as lw
from silnik.pieniadze import wlasciciel as wl
from silnik.rynek import handel as hd
from silnik.rynek import kalendarz as kl
from silnik.rynek import konkurencja as kn
from silnik.rynek import promocje as pm
from silnik.rynek import reklama as rk
from silnik.rynek.popyt import widok_popytu
from silnik.swiat import awarie as aw
from silnik.swiat import zdarzenia as zd
from silnik.wyniki.wnioski import wnioski


def _firma_slownik(f: Firma) -> dict:
    d = do_slownika(f)
    d["pracownicy"] = list(d["pracownicy"].values())
    return d


def stan_po_szkicu(gra: Gra, firma: str):
    """Stan firmy po zastosowaniu roboczych decyzji bieżącej rundy (bez sprzedaży) + koszty tych decyzji."""
    r = gra.runda
    stan = gra.stan(r - 1).kopia()
    f = stan.firmy[firma]
    d = gra.szkic(firma)
    ks, rach = Ksiega(vat=rz.reguly_vat(gra.dane)), Rachunek()
    poprzednia_oferta = list(f.oferta)
    # handel: przyjęte oferty od razu na kopii stanu (druga strona – w pustej księdze; jej decyzje – w przeliczeniu)
    handel = hd.przyjmij(gra.dane, stan.firmy, {firma: d}, r, {firma: ks}, {firma: rach},
                         gra.konfiguracja["ziarno"], tylko=firma)[firma]
    # lokal: pula po poprzedniej rundzie (o lokal wybrany w tej rundzie przez kilka drużyn rozstrzyga przeliczenie)
    lokal = wybierz(gra.dane, f, d.get("lokal"), r, zajete(stan.firmy), ks, rach)
    # kupno budynku i wypowiedzenia na kopii stanu (licytacja z innymi drużynami – dopiero w przeliczeniu)
    przejecia = {"przejecie": pr.przejmij(gra.dane, stan.firmy, firma, d.get("przejecie"), r, None, ks, rach),
                 "wypowiedzenia": pr.wypowiedz(gra.dane, stan.firmy, firma, d.get("wypowiedz"), r)}
    # limit nowych i ważność ofert podkupienia (licytacje i odpowiedzi pracowników – dopiero w przeliczeniu)
    dd, _, raport = rp.przed_decyzjami(gra.dane, stan.kopia(), {firma: d}, r, gra.konfiguracja["ziarno"])
    d, uwagi_rp = dd[firma], raport[firma]["uwagi"]
    bank_info = bk.poczatek_rundy(gra.dane, f, d, r, ks, rach)
    harpagon_info = lw.poczatek_rundy(gra.dane, f, d, r, rach)   # wizyty – dopiero w przeliczeniu
    # portfel właściciela i klub: stawki schodzą, wyniki gier – dopiero w przeliczeniu
    portfel_info = wl.poczatek_rundy(gra.dane, f, d, r, rach, gra.konfiguracja["ziarno"], podglad=True)
    info = zastosuj(gra.dane, f, d, r, stan.kandydaci, ceny_rundy(gra.dane, gra.konfiguracja["ziarno"], r,
                                                                  gra.konfiguracja.get("ceny_dostawcow", "dane")), ks, rach)
    info["lokal"] = lokal
    info["bank"], info["leasing"] = bank_info, bk.leasing_wez(gra.dane, f, d, r, ks, rach)
    info["harpagon"], info["przejecia"] = harpagon_info, przejecia
    info["wlasciciel"], info["kasyno"] = portfel_info
    info["urzad"] = urz.ustaw(gra.dane, f, d, r, gra.konfiguracja["ziarno"], ks, rach)
    # nowe oferty – sprawdzone na stanie po zakupach (w przeliczeniu: po tygodniu sprzedaży)
    info["handel"] = hd.raport(handel, hd.wystaw(gra.dane, stan.firmy, firma, d, r,
                                                 hd.odpowiedzi(gra.decyzje.get(r, {}))))
    if gra.dane.zdarzenia:   # eventy w parkach: koszty wybranych opcji (skutki – dopiero w przeliczeniu)
        czas = cw.z_podsumowania(info["czas_wlasciciela"])
        info["zdarzenia"] = zd.rozegraj(gra.dane, f, d, r, gra.konfiguracja["ziarno"], ks, rach, czas, podglad=True)
        info["konkurencja"] = kn.zlec(gra.dane, f, d, r, gra.konfiguracja["ziarno"], sorted(stan.firmy), ks, rach, czas,
                                      podglad=True)   # wpadka – dopiero w przeliczeniu
        info["czas_wlasciciela"] = czas.podsumowanie()
    bledy = lista_bledow(gra.dane, f, d, r, poprzednia_oferta, gra.konfiguracja.get("kredyt_odnawialny", "na_biezaco"),
                         lokal, info)
    bledy += [{"poziom": "czerwony", "zakladka": "rynek_pracy", "tekst": t} for t in uwagi_rp]
    # odrzucone kredyty, lokaty i leasing (zaległości i debet – dopiero w przeliczeniu)
    odrzucone = (bank_info or {}).get("odrzucone", []) + info["leasing"]["odrzucone"]
    bledy += [{"poziom": "czerwony", "zakladka": "finanse_bank", "tekst": f"{o['co']}: {o['powod']}."} for o in odrzucone]
    bledy += lw.bledy(gra.dane, f, harpagon_info, r)
    bledy += wl.bledy(*portfel_info)
    bledy += hd.bledy(info["handel"])
    bledy += pr.bledy(gra.dane, stan.firmy, firma, r, przejecia)
    bledy += (info.get("zdarzenia") or {}).get("bledy", [])
    bledy += kn.bledy(info.get("konkurencja"))
    return stan, f, ks, info, bledy


def kalendarz(dane: Dane, liczba_rund: int) -> dict:
    """Nazwy rund dla strony: okres („tydzień”/„miesiąc” w przypadkach), nazwy i skróty rund 1…liczba_rund."""
    rundy = range(1, liczba_rund + 1)
    return {"okres": dane.okres, "tygodniowe": dane.tygodniowe, "rund_w_roku": dane.rund_w_roku,
            "nazwy": [dane.nazwa_rundy(r) for r in rundy], "skroty": [dane.skrot_rundy(r) for r in rundy],
            "miesiace": [dane.miesiac_rundy(r) for r in rundy]}


def katalogi(dane: Dane) -> dict:
    return {"mapa": dane.mapa, "uslugi": dane.uslugi, "sprzet": dane.sprzet, "sprzet_kasy": dane.sprzet_kasy, "zawody": dane.zawody, "zasoby": dane.zasoby,
            "oferty": dane.katalog_ofert, "placa_minimalna": dane.z["finanse"]["placa_minimalna"],
            "parametry": {"kapital": dane.z["finanse"]["kapital_startowy"], "godziny": dane.z["operacje"]["godziny_pracownika"],
                          "zus": dane.z["finanse"]["zus_pracodawcy"], "amortyzacja_prog": dane.z["finanse"]["amortyzacja_prog"],
                          "na_runde": 12 / dane.rund_w_roku, "rund_w_roku": dane.rund_w_roku,
                          "sprzedaz_sprzetu": dane.z["finanse"]["sprzedaz_sprzetu"]}}


def karta_skumulowana(gra: Gra, do_rundy: int) -> dict:
    """Średnia kart wyników z rund 2…do_rundy (dla każdej firmy)."""
    if do_rundy < 2:
        return {}
    stan = gra.stan(do_rundy)
    wynik = {}
    for f in stan.firmy:
        karty = [stan.wyniki[r][f]["karta"] for r in range(2, do_rundy + 1)
                 if r in stan.wyniki and f in stan.wyniki[r] and "karta" in stan.wyniki[r][f]]
        if karty:
            wynik[f] = {k: round(sum(c[k] for c in karty) / len(karty), 3) for k in karty[0]}
    return wynik


def widok(gra: Gra, firma: str, runda: int | None = None) -> dict:
    """Widok firmy w rundzie `runda` (domyślnie bieżąca). Decyzje: bieżąca runda – edytowalne, wcześniejsze – podgląd.
    Wyniki w rundzie r: skutki decyzji z rundy r−1 (jak w REVAS)."""
    dane = gra.dane
    biezaca = gra.runda
    runda = min(runda or biezaca, biezaca) if not gra.zakonczona else min(runda or biezaca - 1, biezaca - 1)
    runda = max(runda, gra.runda_startowa)
    edycja = runda == biezaca and not gra.zakonczona
    v = {"gra": {"nazwa": gra.konfiguracja["nazwa"], "runda": biezaca, "liczba_rund": gra.konfiguracja["liczba_rund"],
                 "zakonczona": gra.zakonczona, "firmy": gra.konfiguracja["firmy"], "wyslane": gra.wyslane(),
                 "brakujace": gra.brakujace(), "ziarno": gra.konfiguracja["ziarno"], "runda_startowa": gra.runda_startowa,
                 "konkurenci_stali": gra.konfiguracja.get("konkurenci_stali", []),
                 "kredyt_odnawialny": gra.konfiguracja.get("kredyt_odnawialny", "na_biezaco"),
                 "auto_zamowienia": bool(gra.konfiguracja.get("auto_zamowienia")),
                 "lokale": True,
                 "kalendarz": kalendarz(dane, gra.konfiguracja["liczba_rund"])},
         "firma": firma, "runda": runda, "miesiac": dane.nazwa_rundy(runda), "edycja": edycja,
         "odblokowane": sorted(dane.odblokowane(runda)),
         "harmonogram": {x["klucz"]: x["tydzien"] for x in hm.widok(dane, runda)}}   # z lokalami: tydzień elementu

    if edycja:
        stan, f, ks, info, bledy = stan_po_szkicu(gra, firma)
        v["decyzje"] = gra.szkic(firma)
        v["wyslane"] = firma in gra.wyslane()
        v["warianty"] = sorted(gra.decyzje.get(biezaca, {}).get("_warianty", {}).get(firma, {}))
    else:
        stan = gra.stan(runda)
        f = stan.firmy[firma]
        ks = Ksiega(stan.wyniki[runda][firma]["kpir"]["pozycje"])
        info, bledy = {}, stan.wyniki[runda][firma]["lista_bledow"]
        v["decyzje"] = {k: w for k, w in gra.decyzje.get(runda, {}).get(firma, {}).items()}
        v["wyslane"] = True
    poprzedni = gra.stan(runda - 1)
    v["stan"] = _firma_slownik(f)
    v["stan"]["gotowe_uslugi"] = gotowe_uslugi(dane, f)
    v["stan_przed"] = _firma_slownik(poprzedni.firmy[firma])
    v["koszty_decyzji"] = ks.pozycje
    v["nieudane_zatrudnienia"] = info.get("nieudane_zatrudnienia", [])
    v["lista_bledow"] = bledy
    v["kandydaci"] = (kandydaci_firmy(stan.kandydaci, f) if edycja
                      else kandydaci_firmy(poprzedni.kandydaci, poprzedni.firmy[firma]))
    v["ceny_dostawcow"], v["gazetki"] = oferta_rundy(dane, gra.konfiguracja["ziarno"], runda,
                                                     gra.konfiguracja.get("ceny_dostawcow", "dane"))
    v["dostawcy_info"] = {d: info_dostawcy(dane, d) for d in v["ceny_dostawcow"]}
    v["ceny_sprzedazy_sprzetu"] = {n: {q: cena_sprzedazy_sprzetu(dane, c) for q, c in s["ceny"].items()}
                                   for n, s in dane.sprzet.items()}

    # marki firm (nazwa, slogan, kolor na mapie) – logo dopisuje api/widoki.py (_z_druzyna)
    v["marki"] = {n: {"nazwa": f.nazwa_wyswietlana or n, "slogan": f.misja, "kolor": f.kolor}
                  for n, f in poprzedni.firmy.items()}

    # wyniki poprzedniej rundy (widoczne w tej rundzie)
    if runda - 1 in poprzedni.wyniki:
        w = poprzedni.wyniki.get(runda - 1, {})
        v["wyniki"] = w.get(firma)
        v["wnioski"] = wnioski(dane, v["wyniki"])   # zakładka „Wnioski z rundy”
        v["rynek"] = poprzedni.rynek.get(runda - 1)
        v["karta_skumulowana"] = karta_skumulowana(gra, runda - 1) if runda - 1 >= 2 else {}
        v["dzielnik_karty"] = dane.z["karta_wynikow"]["wynik_ekonomiczny_dzielnik"]
        v["historia"] = [{"runda": r, "miesiac": dane.nazwa_rundy(r), "skrot": dane.skrot_rundy(r), "karta": poprzedni.wyniki[r][firma].get("karta"),
                          "dochod_netto": poprzedni.wyniki[r][firma]["kpir"]["dochod_netto"],
                          "gotowka": poprzedni.wyniki[r][firma]["gotowka"]}
                         for r in range(1, runda) if r in poprzedni.wyniki]
    v["dashboard"] = _dashboard(gra, firma, runda, poprzedni)
    v["lokale"] = _lokale(gra, firma, runda, f, poprzedni, stan, info if edycja else None)
    zk = ((poprzedni.wyniki.get(runda - 1) or {}).get(firma, {}).get("karta") or {}).get("zadowolenie_klientow")
    v["popyt"] = widok_popytu(dane, poprzedni, f, runda, zk)
    v["kalendarz_miasta"] = kl.widok(dane, runda, gra.konfiguracja["liczba_rund"])
    v["swiezosc"] = swiezosc.podsumowanie(dane, f, runda)
    przet = sum(x["wartosc"] for x in ((v.get("wyniki") or {}).get("swiezosc") or {}).get("straty", []) if x["powod"] == "termin")
    v["magazyn"] = mag.ryzyko(dane, f, runda, przet, urz.modyfikatory(dane, f, runda))
    if urz.dane_urzedu(dane):
        v["urzad"] = urz.widok(dane, f, runda, info.get("urzad") if edycja else stan.wyniki[runda][firma].get("urzad"),
                               poprzedni.wyniki, firma, przet)
    v["dostawy_plan"] = (info or {}).get("dostawy") if edycja else stan.wyniki[runda][firma].get("dostawy")
    v["srodki_trwale"] = ewidencja(f)
    v["czas_wlasciciela"] = ((info or {}).get("czas_wlasciciela") if edycja
                             else stan.wyniki[runda][firma].get("czas_wlasciciela")) or cw.nowy(dane).podsumowanie()
    v["wlasciciel_stanowisko"] = ((info or {}).get("wlasciciel_stanowisko") if edycja
                                  else stan.wyniki[runda][firma].get("wlasciciel_stanowisko"))
    v["agencja"] = _agencja(gra, firma, runda, f, stan, edycja)
    zam = ((info.get("kampanie") or {}) if edycja else (stan.wyniki[runda][firma].get("reklama_agencje") or {}))
    v["reklama"] = rk.widok(dane, f, runda, poprzedni.rynek.get(runda - 1), zam.get("zamowione"))
    if pm.zasady(dane):
        v["promocje"] = pm.widok(dane, f, runda, poprzedni.rynek.get(runda - 1),
                                 info.get("promocje") if edycja else stan.wyniki[runda][firma].get("promocje"))
    v["przejecia"] = pr.widok(dane, stan.firmy, firma, runda,
                              info.get("przejecia") if edycja else stan.wyniki[runda][firma].get("przejecia"),
                              (v.get("wyniki") or {}).get("przejecia"))
    if dane.zdarzenia:
        v["zdarzenia"] = zd.widok(dane, poprzedni.firmy[firma], runda, gra.konfiguracja["ziarno"], poprzedni.wyniki, firma)
    if aw.dane_wypadkow(dane):
        v["ubezpieczenia"] = aw.widok(dane, f, runda, info.get("ubezpieczenia") if edycja
                                      else stan.wyniki[runda][firma].get("ubezpieczenia"), poprzedni.wyniki, firma)
    fp = poprzedni.firmy[firma]   # zastawy i limit – stan na początku rundy (przed decyzjami)
    v["banki"] = {"najlepsze": bk.najlepsze(dane), "historia": bk.historia(fp, runda), "zastawy": bk.zastawy(dane, fp),
                  "wolny_limit": bk.wolny_limit(dane, fp), "decyzja": {"bank": info.get("bank"), "leasing": info.get("leasing")}}
    v["kandydaci"] = rp.widoczni(dane, v["kandydaci"], runda)
    if wl.dane_portfela(dane):
        v["wlasciciel"] = wl.widok(dane, fp, f, info.get("wlasciciel") if edycja
                                   else stan.wyniki[runda][firma].get("wlasciciel"))
    v["handel"] = hd.widok(dane, poprzedni.firmy, firma, runda, info.get("handel") if edycja
                           else stan.wyniki[runda][firma].get("handel"),
                           gra.decyzje.get(runda, {}) if edycja else None)
    v["konkurencja"] = kn.widok(dane, firma, runda, gra.konfiguracja["ziarno"], v.get("rynek"),
                                info.get("konkurencja") if edycja
                                else (stan.wyniki[runda][firma].get("konkurencja") or {}).get("zlecenie"))
    klub = kas.widok(dane, fp, runda, info.get("kasyno") if edycja
                     else (stan.wyniki[runda][firma].get("kasyno") or {}).get("gry"), v.get("wyniki"))
    if klub:
        v["kasyno"] = klub
    u = lw.ustawienia(dane)
    v["harpagon"] = {"przed": lw.stan(dane, fp, runda), "po": lw.stan(dane, f, runda),
                     "decyzja": info.get("harpagon"),
                     "warunki": {k: u[k] for k in ("maks_kwota", "min_kwota", "oprocentowanie_rundy", "termin_rund",
                                                   "odsetki_karne_rundy", "karne_od", "wizyty_od")}}
    v["podatki"] = _podatki(dane, fp, runda, rz.rejestr(ks) if edycja else stan.wyniki[runda][firma].get("vat"))
    v["amortyzacja"] = {"prog": dane.z["finanse"]["amortyzacja_prog"], "stawki": dane.z["finanse"]["amortyzacja_roczna"]}
    v["ksiegowosc"] = bo.widok(dane, fp, f, v["decyzje"], v.get("wyniki"))
    if edycja and fp.deklaracja:   # samodzielna księgowość: wynik podatkowy dopiero po deklaracji drużyny
        v["wyniki"] = bo.ukryj(v.get("wyniki"))
        v["ksiegowosc"]["ukryte"] = True
        if v.get("historia"):
            v["historia"][-1]["dochod_netto"] = None
        v["dashboard"]["dochod_netto"] = None
        v["podatki"]["stan"] = fp.deklaracja["stan_przed"]
        v["podatki"]["stan_przed_deklaracja"] = True
    return v


def _podatki(dane: Dane, fp: Firma, runda: int, rejestr: dict | None) -> dict:
    """JDG (F3a.11): stawki, stan rozliczeń na początku rundy i VAT z decyzji (szkic) albo z rundy (wyniki)."""
    p, roz = dane.podatki, fp.rozliczenie
    return {"rejestr": rejestr, "ulga_na_start": rz.ulga_na_start(dane, runda),
            "stan": {"vat_nadwyzka": roz.vat_nadwyzka, "dochod": roz.dochod, "zaliczki": roz.zaliczki,
                     "zdrowotna_odliczona": roz.zdrowotna_odliczona, "zaplacone": roz.zaplacone},
            "parametry": {"pit": p["pit_liniowy"], "zdrowotna": p["zdrowotna"]["stawka"],
                          "zdrowotna_minimum": dane.na_runde(p["zdrowotna"]["minimalna_miesieczna"]),
                          "limit_odliczenia": p["zdrowotna"]["limit_odliczenia_roczny"],
                          "spoleczne": dane.na_runde(p["zus_wlasciciela"]["spoleczne_miesieczne"]),
                          "ulga_rund": p["zus_wlasciciela"]["ulga_na_start_rund"], "zus_pracodawcy": p["zus_pracodawcy"],
                          "vat_uslug": {u: rz.stawka_sprzedazy(dane, u) for u in dane.uslugi},
                          "vat_zasobow": {z: rz.stawka_zasobu(dane, z) for z in dane.zasoby},
                          "vat_kosztow": p["vat"]["koszty"], "vat_srodkow_trwalych": p["vat"]["srodki_trwale"]}}


def _agencja(gra: Gra, firma: str, runda: int, f: Firma, stan, edycja: bool) -> dict:
    """Zakładka Rynek pracy: kanały rekrutacji, pracownicy innych firm (headhunter), oferty dla moich pracowników
    (zapisane decyzje innych firm w tej rundzie – do kontroferty), staż i okres wypowiedzenia moich pracowników."""
    dane = gra.dane
    u = rp.ustawienia(dane)
    return {"kanaly": rp.kanaly(dane, runda), "limit": u["limit_nowych"], "wypowiedzenie": u["wypowiedzenie"],
            "kanaly_kandydatow": {k["id"]: rp.kanaly_kandydata(dane, k, runda) for k in stan.kandydaci},
            "headhunter": rp.headhunter_dostepny(dane, runda),
            "cudzy": rp.pracownicy_rynku(dane, stan, firma, runda) if rp.headhunter_dostepny(dane, runda) else [],
            "oferty_dla_mnie": rp.oferty_dla(gra.decyzje.get(runda, {}), f, firma) if edycja else [],
            "moi": [{"id": p.id, "imie_nazwisko": p.imie_nazwisko, "zawod": p.zawod, "gwiazdki": p.gwiazdki, "pensja": p.pensja,
                     "umowa": p.umowa, "staz": rp.staz(p, runda), "okres": rp.okres_wypowiedzenia(dane, p, runda),
                     "odchodzi": do_slownika(p.odchodzi) if p.odchodzi else None}
                    for p in sorted(f.pracownicy.values(), key=lambda p: p.id)]}


def _lokale(gra: Gra, firma: str, runda: int, f: Firma, poprzedni, stan, info: dict | None) -> dict:
    """Zakładka Lokale i mapa: wolne lokale na początku rundy (z kosztem wejścia), kto zajmuje które lokale,
    lokale firmy po decyzjach i wynik decyzji o lokalu."""
    dane = gra.dane
    zaj = zajete(poprzedni.firmy)
    decyzja = info.get("lokal") if info is not None else stan.wyniki.get(runda, {}).get(firma, {}).get("lokal_decyzja")
    return {"oferta": [{**lok, "wejscie": {fm: koszt_wejscia(dane, lok, fm) for fm in ("najem", "kupno")
                                          if lok.get("czynsz" if fm == "najem" else "cena")}}
                       for lok in dostepne(dane, runda, zaj)],
            "zajete": zajete(stan.firmy) if info is None else zaj,
            "moje": stan_lokali(dane, f, runda),
            "nowy_od": runda_nowego_lokalu(dane, poprzedni.firmy[firma]),
            "odpoczynek": komunikat_odpoczynku(dane, poprzedni.firmy[firma], runda)
            if runda < runda_nowego_lokalu(dane, poprzedni.firmy[firma]) else None,
            "decyzja": decyzja}


def _dashboard(gra: Gra, firma: str, runda: int, poprzedni) -> dict:
    f = poprzedni.firmy[firma]
    d = {"nazwa": f.nazwa_wyswietlana or firma, "saldo": f.gotowka, "dochod_netto": 0.0, "miejsce": None,
         "liczba_firm": len(poprzedni.firmy), "lokaty": sum(l.kwota for l in f.lokaty),
         "zadluzenie": sum(k.pozostalo for k in f.kredyty) + f.kredyt_odnawialny}
    if runda - 1 in poprzedni.wyniki:
        d["dochod_netto"] = poprzedni.wyniki[runda - 1][firma]["kpir"]["dochod_netto"]
    if runda >= 3 and runda - 1 in poprzedni.rynek:
        karty = poprzedni.rynek[runda - 1]["karta"]
        ranking = sorted(karty, key=lambda n: -karty[n]["wynik_dzialalnosci"])
        d["miejsce"] = ranking.index(firma) + 1 if firma in ranking else None
    return d


def tabela_wynikow(gra: Gra, co: str = "wyniki") -> tuple[list[str], list[list]]:
    """Wyniki do arkusza (eksport CSV mistrza gry). `wyniki` – wiersz na firmę w każdej przeliczonej rundzie,
    `ranking` – ranking po ostatniej przeliczonej rundzie (jak w panelu mistrza gry)."""
    if co == "ranking":
        p = przeglad_mg(gra)
        firmy = sorted(p["firmy"], key=lambda f: (f.get("miejsce") is None, f.get("miejsce") or 0, f["nazwa"]))
        return (["miejsce", "firma", "bot", "wynik działalności (średnia)", "dochód netto razem", "gotówka",
                 "zadłużenie", "lokaty", "pracownicy"],
                [[f.get("miejsce", ""), f["nazwa"], f["strategia"] or "", f["wynik_skumulowany"] if f["wynik_skumulowany"] is not None else "",
                  f["dochod_suma"], f["gotowka"], f["zadluzenie"], f["lokaty"], f["pracownicy"]] for f in firmy])
    ostatnia = gra.runda - 1
    stan = gra.stan(ostatnia)
    strategie = gra.dane.boty["strategie"]
    boty = {f["nazwa"]: strategie.get(f["bot"], {}).get("nazwa", f["bot"]) for f in gra.konfiguracja["firmy"] if f["bot"]}
    wiersze = []
    for r in range(gra.runda_startowa, ostatnia + 1):
        karta = stan.rynek.get(r, {}).get("karta", {})
        for n, w in stan.wyniki.get(r, {}).items():
            k = w["kpir"]
            wynik = karta.get(n, {}).get("wynik_dzialalnosci")
            wiersze.append([r, gra.dane.skrot_rundy(r), n, boty.get(n, ""), k["przychody"], k["koszty"], k["dochod_netto"],
                            w["gotowka"], w["zadluzenie"], float(wynik) if wynik is not None else ""])
    return (["runda", "tydzień", "firma", "bot", "przychody", "koszty", "dochód netto", "gotówka", "zadłużenie",
             "wynik działalności"], wiersze)


def przeglad_mg(gra: Gra) -> dict:
    """Widok mistrza gry: bieżąca runda, kto wysłał decyzje, wyniki i ranking wszystkich firm, historia rund."""
    dane, konf = gra.dane, gra.konfiguracja
    r = gra.runda
    ostatnia = r - 1  # ostatnia przeliczona runda
    stan = gra.stan(ostatnia)
    wyslane = set(gra.wyslane())
    strategie = dane.boty["strategie"]
    skum = karta_skumulowana(gra, ostatnia)
    karta_ost = stan.rynek.get(ostatnia, {}).get("karta", {}) if ostatnia >= 2 else {}
    rundy = [x for x in range(gra.runda_startowa, ostatnia + 1) if x in stan.wyniki]
    firmy = []
    for f in konf["firmy"]:
        n = f["nazwa"]
        fs = stan.firmy[n]
        wyn = [stan.wyniki[x][n]["kpir"]["dochod_netto"] for x in rundy if n in stan.wyniki[x]]
        firmy.append({
            "nazwa": n, "bot": f["bot"], "strategia": strategie.get(f["bot"], {}).get("nazwa") if f["bot"] else None,
            "poziom": f.get("poziom") if f["bot"] else None,
            "wyslane": None if f["bot"] else n in wyslane,
            "gotowka": fs.gotowka,
            "zadluzenie": sum(k.pozostalo for k in fs.kredyty) + fs.kredyt_odnawialny,
            "lokaty": sum(lk.kwota for lk in fs.lokaty),
            "pracownicy": len(fs.pracownicy), "stanowiska": len(fs.stanowiska),
            "dochod_ostatni": wyn[-1] if wyn else None, "dochod_suma": round(sum(wyn), 2),
            "wynik_ostatni": karta_ost.get(n, {}).get("wynik_dzialalnosci"),
            "wynik_skumulowany": skum.get(n, {}).get("wynik_dzialalnosci"),
        })
    ranking = sorted((f for f in firmy if f["wynik_skumulowany"] is not None), key=lambda f: -f["wynik_skumulowany"])
    for i, f in enumerate(ranking):
        f["miejsce"] = i + 1
    return {
        "gra": {"nazwa": konf["nazwa"], "runda": r, "liczba_rund": konf["liczba_rund"], "zakonczona": gra.zakonczona,
                "ziarno": konf["ziarno"], "kapital": gra.kapital_startowy,
                "kredyt_odnawialny": konf.get("kredyt_odnawialny", "na_biezaco"),
                "auto_zamowienia": bool(konf.get("auto_zamowienia")),
                "ceny_dostawcow": konf.get("ceny_dostawcow", "dane"),
                "lokale": True,
                "brakujace": [] if gra.zakonczona else gra.brakujace(),
                "kalendarz": kalendarz(dane, konf["liczba_rund"])},
        "firmy": firmy,
        "historia": [{"runda": x, "skrot": dane.skrot_rundy(x),
                      "dochod": {n: w["kpir"]["dochod_netto"] for n, w in stan.wyniki[x].items()},
                      "gotowka": {n: w["gotowka"] for n, w in stan.wyniki[x].items()}} for x in rundy],
    }
