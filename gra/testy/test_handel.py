"""Handel między drużynami (F3b.8): oferty towaru i sprzętu, przyjęcie w następnej rundzie, faktury w KPiR obu
stron, partie z terminem u kupującego, odrzucenia (widełki, limit, brak towaru, boty, przed rundą odblokowania),
negocjacje na żywo w rundzie wystawienia (P13)."""

import copy

import pytest
import yaml
from pydantic import ValidationError
from test_lokale import _gra, _lokal, _runda

from silnik import biuro
from silnik import handel as hd
from silnik import rozliczenie as rz
from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.finanse import Ksiega, Rachunek, ksieguj, vat_z_brutto
from silnik.model import Firma
from silnik.schematy import PlikHandlu

DOSTAWCA = "Makro"
HUMMUS = {"dostawca": DOSTAWCA, "zasob": "Hummus", "jakosc": 2, "ilosc": 80, "dzien": 3}


@pytest.fixture
def od_drugiej(monkeypatch):
    """Handel od rundy 2 (w danych – od 5)."""
    oryginal = hd.ustawienia

    def u(d):
        x = copy.deepcopy(oryginal(d))
        if x:
            x["handel"]["od_rundy"] = 2
        return x

    monkeypatch.setattr(hd, "ustawienia", u)


def _towar(cena, ilosc=20, do="B"):
    return {"do": do, "typ": "towar", "zasob": "Hummus", "jakosc": 2, "ilosc": ilosc, "cena": cena}


def _rozen(cena, nr=2, do="B"):
    return {"do": do, "typ": "sprzet", "stanowisko": "kuchnia", "nr": nr, "nazwa": "Rożen", "cena": cena}


def _przygotuj(g, oferty):
    """Runda 1: lokale (A – druga kuchnia); runda 2: A kupuje hummus i rożen, wystawia oferty dla B."""
    _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}}, B=_lokal("centrum_2"))
    return _runda(g, A={"stanowiska": {}, "zamowienia": [HUMMUS],
                        "sprzet_kup": [{"typ": "kuchnia", "nr": 2, "nazwa": "Rożen", "jakosc": 2}],
                        "handel_oferty": oferty}, B={"stanowiska": {"kuchnia": 1}})


def test_dane_handlu():
    u = hd.ustawienia(dane_domyslne())
    assert u["handel"]["od_rundy"] == 5 and u["handel"]["cena_min"] < 1 < u["handel"]["cena_maks"]
    assert all("{" not in t.format(sprzedawca="X", kupujacy="Y", co="Z") for t in u["teksty"])
    w = yaml.safe_load((KATALOG_DANYCH / "zdarzenia" / "handel.yaml").read_text(encoding="utf-8"))
    w["handel"]["cena_min"] = w["handel"]["cena_maks"] + 1
    with pytest.raises(ValidationError):
        PlikHandlu.model_validate(w)
    assert not hd.otwarty(dane_domyslne(), 4) and hd.otwarty(dane_domyslne(), 5)


def test_handel_towarem_i_sprzetem(od_drugiej):
    g = _gra()
    s = _przygotuj(g, [_towar(900), _rozen(4000), _rozen(2000, nr=1)])
    h = s.wyniki[2]["A"]["handel"]
    assert [o["co"] for o in h["wystawione"]] == ["Hummus 2★ × 20 opak.", "Rożen 2★ (kuchnia 2)"]
    assert h["wystawione"][0]["termin"] and h["wystawione"][0]["vat"] == vat_z_brutto(900, 0.05)
    assert "najmu lokalu" in h["odrzucone"][0]["powod"]   # rożen z kuchni 1 jest wynajmującego
    assert any(b["zakladka"] == hd.ZAKLADKA and b["poziom"] == "czerwony" for b in s.wyniki[2]["A"]["lista_bledow"])
    ids = [o.id for o in s.firmy["A"].oferty_handlu]
    gotowka = {n: s.firmy[n].gotowka for n in "AB"}
    s = _runda(g, A={"handel_oferty": []}, B={"handel_przyjmij": [{"id": i} for i in ids]})
    wa, wb = s.wyniki[3]["A"], s.wyniki[3]["B"]
    assert [t["strona"] for t in wa["handel"]["transakcje"]] == ["sprzedaz"] * 2
    assert [t["strona"] for t in wb["handel"]["transakcje"]] == ["zakup"] * 2
    assert all(t["tekst"] and "{" not in t["tekst"] for t in wb["handel"]["transakcje"])
    kpir = {n: {p["opis"]: p for p in s.wyniki[3][n]["kpir"]["pozycje"]} for n in "AB"}
    assert kpir["A"]["Sprzedaż towarów dla drużyny B: Hummus"]["przychod"] == round(900 - vat_z_brutto(900, 0.05), 2)
    assert kpir["B"]["Zakup towarów od drużyny A: Hummus"]["towary"] == round(900 - vat_z_brutto(900, 0.05), 2)
    assert kpir["A"]["Sprzedaż sprzętu: Rożen dla drużyny B"]["przychod_pozostaly"] == round(4000 - vat_z_brutto(4000, 0.23), 2)
    assert "Koszt zakupu: Rożen od drużyny A" in kpir["B"]
    assert all(s.wyniki[3][n]["uzgodnienie"]["roznica"] == 0 for n in "AB")
    assert "Rożen" not in s.firmy["A"].stanowisko("kuchnia", 2).sprzet
    assert s.firmy["B"].stanowisko("kuchnia", 1).sprzet["Rożen"] == 2
    assert s.firmy["A"].oferty_handlu == []
    # pieniądze: kupujący zapłacił 4900, sprzedawca je dostał (reszta zmian – zwykła runda obu)
    rach = {n: [o for o in s.wyniki[3][n]["rachunek"] if "drużyn" in o["opis"]] for n in "AB"}
    assert sum(o["kwota"] for o in rach["A"]) == 4900 and sum(o["kwota"] for o in rach["B"]) == -4900
    assert gotowka["B"] > 4900
    # dokument w biurze rachunkowym: sprzedaż towaru drużynie to faktura sprzedaży, sprzedaż dań – raport kasy
    f, ks, rach = Firma(nazwa="X"), Ksiega(vat=rz.reguly_vat(g.dane)), Rachunek()
    ksieguj(f, ks, rach, f"{hd.SPRZEDAZ_TOWAROW} B: Hummus", 900, "przychod", stawka=0.05)
    ksieguj(f, ks, rach, "Sprzedaż: Kebab", 900, "przychod", stawka=0.08)
    assert [d["typ"] for d in biuro.dokumenty(ks, rach)] == ["Faktura sprzedaży", "Raport kasy fiskalnej"]


def test_partie_u_kupujacego(od_drugiej):
    """Kupujący dostaje partie z terminem sprzedawcy; dostawa w poniedziałek rundy przyjęcia."""
    g = _gra()
    s = _przygotuj(g, [_towar(900)])
    termin = min(p.termin for p in s.firmy["A"].partie if p.zasob == "Hummus")
    oferta = s.firmy["A"].oferty_handlu[0]
    f = copy.deepcopy(s.firmy)
    stan = hd.przyjmij(g.dane, f, {"B": {"handel_przyjmij": [{"id": oferta.id}]}}, 3, {}, {}, 1)
    assert stan["B"]["transakcje"] and not stan["B"]["nieudane"]
    partie = [p for p in f["B"].partie if p.zasob == "Hummus"]
    assert sum(p.ilosc for p in partie) == 20 and {p.termin for p in partie} == {termin}
    assert sum(p.wartosc_gr for p in partie) == 90000 and partie[0].dostawa == g.dane.data_rundy(3).isoformat()
    assert f["B"].magazyn["Hummus|2"] == 20 and f["A"].magazyn["Hummus|2"] == s.firmy["A"].magazyn["Hummus|2"] - 20


def test_odrzucone_oferty(od_drugiej):
    g = _gra(("A", None), ("B", None), ("Bot", "tani"))
    s = _przygotuj(g, [_towar(1), _towar(900, ilosc=500), _towar(900, do="Bot"), _towar(900, do="A"),
                       {"do": "B", "typ": "lokal", "cena": 100}, _towar(900), _towar(900), _towar(900), _towar(900)])
    h = s.wyniki[2]["A"]["handel"]
    powody = [o["powod"] for o in h["odrzucone"]]
    assert powody[0].startswith("cena musi być od")
    assert "w magazynie było tylko" in powody[1]
    assert powody[2] == powody[3] == "nie ma takiej drużyny (boty nie handlują)"
    assert powody[4] == "można sprzedać towar albo sprzęt"
    assert len(h["wystawione"]) == 4 and not h["odrzucone"][5:]   # 80 opak.: 4 × 20 – piąta by się nie zmieściła
    # przyjęcie: oferta nie do mnie, wygasła albo bez pieniędzy
    ids = [o.id for o in s.firmy["A"].oferty_handlu]
    f = copy.deepcopy(s.firmy)
    f["B"].gotowka_gr = 0
    w = hd.przyjmij(g.dane, f, {"B": {"handel_przyjmij": [{"id": ids[0]}, {"id": "zly"}]}}, 3, {}, {}, 1)
    assert [o["powod"] for o in w["B"]["nieudane"]] == ["B nie miał(a) na koncie 900,00 zł",
                                                        "nie ma takiej oferty albo już wygasła"]
    assert w["A"]["nieudane"] and not w["A"]["transakcje"]
    w = hd.przyjmij(g.dane, copy.deepcopy(s.firmy), {"B": {"handel_przyjmij": [{"id": ids[0]}]}}, 4, {}, {}, 1)
    assert w["B"]["nieudane"][0]["powod"] == "nie ma takiej oferty albo już wygasła"


def test_przed_odblokowaniem():
    g = _gra()
    s = _przygotuj(g, [_towar(900)])
    h = s.wyniki[2]["A"]["handel"]
    assert not h["wystawione"] and "od rundy 5" in h["odrzucone"][0]["powod"]


def test_negocjacja_ruchy_i_stany():
    dane = dane_domyslne()
    o = {"cena": 900, "klucz": "k"}
    n = hd.negocjacja(dane, o, None)
    assert n["stan"] == "ruch_kupujacego" and n["kontr"] == 0 and n["kontr_zostalo"] == 3 and n["cena"] == 900
    assert hd.negocjacja(dane, o, {"przyjmij": 900})["stan"] == "umowa"
    assert hd.negocjacja(dane, o, {"przyjmij": 850})["stan"] == "ruch_kupujacego"   # przyjęcie starej ceny
    assert hd.negocjacja(dane, o, {"odrzuc": True})["stan"] == "odrzucona"
    n = hd.negocjacja(dane, o, {"kontry": [700]})
    assert n["stan"] == "ruch_sprzedawcy" and n["cena"] == 700 and n["kontr_zostalo"] == 2
    assert hd.negocjacja(dane, {**o, "przyjmij_kontre": 700}, {"kontry": [700]})["stan"] == "umowa"
    o2 = {"cena": 800, "ceny": [900, 800]}
    n = hd.negocjacja(dane, o2, {"kontry": [700, 750, 760]})   # kontra kupującego ponad kolejność – ucięta
    assert [r["cena"] for r in n["ruchy"]] == [900, 700, 800, 750] and n["kontr_zostalo"] == 0
    assert hd.negocjacja(dane, {**o2, "przyjmij_kontre": 750}, {"kontry": [700, 750]})["stan"] == "umowa"
    n = hd.negocjacja(dane, {"ceny": [900, 800, 790]}, {"kontry": [700, 750]})   # czwarta kontra – ponad limit
    assert n["kontr"] == 3 and n["cena"] == 750 and n["stan"] == "ruch_sprzedawcy"


def test_negocjacje_na_zywo_i_umowa(od_drugiej):
    """Szkic oferty A widzi B jeszcze w tej rundzie; kontra, kontra, przyjęcie – transakcja w następnej rundzie
    po uzgodnionej cenie, bez handel_przyjmij."""
    from api.prezentacja import widok
    g = _gra()
    _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}}, B=_lokal("centrum_2"))
    a = {"stanowiska": {}, "zamowienia": [HUMMUS], "handel_oferty": [{**_towar(900), "klucz": "k1"}]}
    g.ustaw_decyzje("A", a)
    na = widok(g, "B")["handel"]["na_zywo"]
    (o,) = na["przychodzace"]
    assert o["klucz"] == "A/k1" and o["negocjacja"]["stan"] == "ruch_kupujacego" and o["od_nazwa"] == "A"
    z1 = na["znacznik"]
    g.ustaw_decyzje("B", {"handel_odpowiedzi": {"A/k1": {"kontry": [700]}}})
    assert widok(g, "A")["handel"]["na_zywo"]["moje"]["k1"]["stan"] == "ruch_sprzedawcy"
    a["handel_oferty"][0].update(ceny=[900, 800], cena=800)
    g.ustaw_decyzje("A", a)
    na = widok(g, "B")["handel"]["na_zywo"]
    assert na["znacznik"] != z1 and na["przychodzace"][0]["negocjacja"]["cena"] == 800
    s = _runda(g, B={"handel_odpowiedzi": {"A/k1": {"kontry": [700], "przyjmij": 800}}})
    (w,) = s.wyniki[2]["A"]["handel"]["wystawione"]
    assert w["uzgodniona"] and w["cena"] == 800 and w["negocjacja"]["stan"] == "umowa"
    s = _runda(g, A={"handel_oferty": []}, B={})
    (t,) = s.wyniki[3]["B"]["handel"]["transakcje"]
    assert t["strona"] == "zakup" and t["cena"] == 800 and t["uzgodniona"]
    assert any(p["opis"] == "Zakup towarów od drużyny A: Hummus" for p in s.wyniki[3]["B"]["kpir"]["pozycje"])
    assert all(s.wyniki[3][n]["uzgodnienie"]["roznica"] == 0 for n in "AB")


def test_odrzucona_oferta_przepada(od_drugiej):
    g = _gra()
    _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}}, B=_lokal("centrum_2"))
    s = _runda(g, A={"stanowiska": {}, "zamowienia": [HUMMUS], "handel_oferty": [_towar(900)]},
               B={"handel_odpowiedzi": {"A/i1": {"odrzuc": True}}})
    h = s.wyniki[2]["A"]["handel"]
    assert not h["wystawione"] and h["odrzucone_przez_adresata"] and not s.firmy["A"].oferty_handlu
    assert not any(b["zakladka"] == hd.ZAKLADKA for b in s.wyniki[2]["A"]["lista_bledow"])


def test_widok_i_podglad(od_drugiej):
    from api.prezentacja import stan_po_szkicu, widok
    g = _gra()
    s = _przygotuj(g, [_towar(900), _rozen(4000)])
    v = widok(g, "B")["handel"]
    assert v["otwarty"] and [o["co"] for o in v["przychodzace"]] == ["Hummus 2★ × 20 opak.", "Rożen 2★ (kuchnia 2)"]
    assert [d["nazwa"] for d in v["druzyny"]] == ["A"] and v["stanowiska"][0]["typ"] == "kuchnia"
    va = widok(g, "A")["handel"]
    assert len(va["wystawione"]) == 2 and va["towary"][0]["zasob"] == "Hummus"
    assert all(x["stanowisko"] == "kuchnia" and x["nr"] == 2 for x in va["sprzet"])
    ids = [o.id for o in s.firmy["A"].oferty_handlu]
    g.ustaw_decyzje("B", {"handel_przyjmij": [{"id": ids[0]}]})
    _, f, _, info, _ = stan_po_szkicu(g, "B")
    assert f.magazyn["Hummus|2"] == 20 and info["handel"]["transakcje"][0]["strona"] == "zakup"
    assert g.stan(2).firmy["B"].magazyn.get("Hummus|2", 0) == 0   # podgląd na kopii stanu
    assert widok(g, "B")["handel"]["decyzja"]["transakcje"]
