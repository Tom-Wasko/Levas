"""Agencja pracy i rynek pracy (F3a.8): kanały rekrutacji, licytacja kandydatów, limit nowych, podkupienie
przez headhuntera z kontrofertą i okresem wypowiedzenia, powrót zwolnionych do puli."""

from test_lokale import _gra, _lokal, _runda

from silnik import rynek_pracy as rp
from silnik.dane import dane_domyslne


def _start():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 3}}, B={**_lokal("dworzec_1"), "stanowiska": {"kuchnia": 3}})
    return g, s


def _kandydat(s, gwiazdki, pomin=()):
    return next(k for k in s.kandydaci if k["gwiazdki"] == gwiazdki and k["zawod"] == "Kucharz" and k["id"] not in pomin)


def _z(k, nr, **kw):
    return {"kandydat": k["id"], "typ": "kuchnia", "nr": nr, **kw}


def _bledy(s, r, firma, zakladka):
    return [b["tekst"] for b in s.wyniki[r][firma]["lista_bledow"] if b["zakladka"] == zakladka]


def test_kanaly_i_koszt():
    dane = dane_domyslne()
    k1 = {"gwiazdki": 1, "koszt_rekrutacji": 300}
    k3 = {"gwiazdki": 3, "koszt_rekrutacji": 300}
    assert rp.kanaly_kandydata(dane, k1, 2) == ["pracuj"]
    assert rp.kanaly_kandydata(dane, k3, 2) == ["agencja"]
    assert set(rp.kanaly_kandydata(dane, k3, 4)) == {"agencja", "headhunter"}
    u = rp.ustawienia(dane)["kanaly"]
    assert rp.koszt(dane, "pracuj", k1) == u["pracuj"]["oplata"]
    assert rp.koszt(dane, "headhunter", k3) == u["headhunter"]["oplata"] + u["headhunter"]["mnoznik_rekrutacji"] * 300
    assert all(rp.kanaly_kandydata(dane, k, 2) for k in rp.widoczni(dane, [k1, k3], 2))


def test_zatrudnienie_kanalem_koszt_i_czas_wlasciciela():
    g, s = _start()
    k1, k3 = _kandydat(s, 1), _kandydat(s, 3)
    s = _runda(g, A={"zatrudnij": [_z(k1, 1), _z(k3, 2)]})
    rp_a = s.wyniki[2]["A"]["rynek_pracy"]
    kanaly = {z["pracownik"]: (z["kanal"], z["koszt"]) for z in rp_a["zatrudnieni"]}
    u = rp.ustawienia(g.dane)["kanaly"]
    assert kanaly[k1["id"]] == ("pracuj", u["pracuj"]["oplata"])
    assert kanaly[k3["id"]] == ("agencja", k3["koszt_rekrutacji"])
    assert any(p["godziny"] == u["pracuj"]["czas_wlasciciela"] and p["zakladka"] == "zatrudnienie"
               for p in s.wyniki[2]["A"]["czas_wlasciciela"]["pozycje"])
    assert {k1["id"], k3["id"]}.isdisjoint({k["id"] for k in s.kandydaci})


def test_kanal_niedostepny_odrzuca_zatrudnienie():
    g, s = _start()
    k3 = _kandydat(s, 3)
    s = _runda(g, A={"zatrudnij": [_z(k3, 1, kanal="headhunter")]})
    assert not s.firmy["A"].pracownicy
    assert any("od rundy" in t for t in _bledy(s, 2, "A", "zatrudnienie"))


def test_licytacja_wygrywa_wyzsza_pensja():
    g, s = _start()
    k = _kandydat(s, 3)
    s = _runda(g, A={"zatrudnij": [_z(k, 1, pensja=5000)]}, B={"zatrudnij": [_z(k, 1, pensja=6000)]})
    assert k["id"] in s.firmy["B"].pracownicy and k["id"] not in s.firmy["A"].pracownicy
    assert s.firmy["B"].pracownicy[k["id"]].pensja == 6000
    lic = s.wyniki[2]["A"]["rynek_pracy"]["licytacje"]
    assert lic and not lic[0]["wygrana"] and lic[0]["najwyzsza"] == 6000
    assert any("licytację wygrała inna firma" in t for t in _bledy(s, 2, "A", "rynek_pracy"))


def test_limit_nowych_pracownikow():
    g, s = _start()
    limit = rp.ustawienia(g.dane)["limit_nowych"]
    kucharze = [k for k in s.kandydaci if k["zawod"] == "Kucharz"][: limit + 1]
    s = _runda(g, A={"stanowiska": {"kuchnia": 1}, "zatrudnij": [_z(k, i + 1) for i, k in enumerate(kucharze)]})
    assert len(s.firmy["A"].pracownicy) <= limit
    assert s.wyniki[2]["A"]["rynek_pracy"]["ponad_limit"]


def _podkupienie(kontroferta=None, umowa="prace"):
    g, s = _start()
    k = _kandydat(s, 1)
    _runda(g, A={"zatrudnij": [_z(k, 1, umowa=umowa)]})
    _runda(g)
    oferta = {"pracownik": k["id"], "firma": "A", "pensja": 5200, "umowa": "prace"}
    s = _runda(g, B={"podkup": [oferta]}, A={"kontroferty": {k["id"]: kontroferta}} if kontroferta else {})
    return g, s, k["id"]


def test_podkupiony_odchodzi_po_okresie_wypowiedzenia():
    g, s, pid = _podkupienie()
    p = s.firmy["A"].pracownicy[pid]
    assert p.odchodzi and p.odchodzi.do == "B" and p.odchodzi.runda == 4 + rp.okres_wypowiedzenia(g.dane, p, 4)
    hh = [x for x in s.wyniki[4]["B"]["rachunek"] if x["opis"].startswith("Headhunter")]
    assert hh and -hh[0]["kwota"] == 5200 * rp.ustawienia(g.dane)["kanaly"]["headhunter"]["podkupienie_czesc_pensji"]
    s = _runda(g, A={"zwolnij": [pid]})
    assert pid in s.firmy["A"].pracownicy and _bledy(s, 5, "A", "rynek_pracy")
    s = _runda(g)
    assert pid not in s.firmy["A"].pracownicy
    nowy = s.firmy["B"].pracownicy[pid]
    assert (nowy.pensja, nowy.od_rundy, nowy.odchodzi) == (5200, 6, None)
    assert s.firmy["B"].stanowisko("kuchnia", nowy.stanowisko).pracownik == pid
    assert all(st.pracownik != pid for st in s.firmy["A"].stanowiska)
    assert s.wyniki[6]["A"]["rynek_pracy"]["odejscia"] and s.wyniki[6]["B"]["rynek_pracy"]["przyjscia"]


def test_wygrana_kontroferta_podnosi_pensje():
    g, s, pid = _podkupienie(kontroferta=5300)
    p = s.firmy["A"].pracownicy[pid]
    assert p.odchodzi is None and p.pensja == 5300
    assert s.wyniki[4]["B"]["rynek_pracy"]["oferty_zlozone"][0]["wynik"] == "kontroferta"
    assert not [x for x in s.wyniki[4]["B"]["rachunek"] if x["opis"].startswith("Headhunter")]


def test_zleceniobiorca_przechodzi_od_razu():
    g, s, pid = _podkupienie(umowa="zlecenie")
    assert pid not in s.firmy["A"].pracownicy and pid in s.firmy["B"].pracownicy


def test_zwolniony_wraca_do_puli():
    g, s = _start()
    k = _kandydat(s, 1)
    _runda(g, A={"zatrudnij": [_z(k, 1)]})
    s = _runda(g, A={"zwolnij": [k["id"]]})
    assert k["id"] in {x["id"] for x in s.kandydaci}


def test_wlasciciel_na_stanowisku_jako_pracownik_1_gwiazdka():
    from silnik.model import WLASCICIEL, WlascicielNaStanowisku
    from silnik.operacje import kasjerzy
    g, s = _start()
    f = s.firmy["A"].model_copy(deep=True)
    kasa = f.stanowisko("kasa", 1)
    assert f.pracownik_stanowiska(kasa) is None and not kasjerzy(g.dane, f)
    f.wlasciciel_na = WlascicielNaStanowisku(typ="kasa", nr=1, godziny=12, zawod="Kasjer", zadowolenie_klientow=0.5,
                                             ryzyko_reklamacji=0.1)
    p = f.pracownik_stanowiska(kasa)
    assert (p.id, p.gwiazdki, p.pensja) == (WLASCICIEL, 1, 0) and kasjerzy(g.dane, f) == [kasa]
    assert f.godziny_stanowiska(kasa, 40) == 12 and f.godziny_stanowiska(f.stanowisko("kuchnia", 1), 40) == 0
    # w grze: godziny z puli czasu właściciela, bez pensji, tylko w tej rundzie; za dużo godzin – odrzucone
    k1 = _kandydat(s, 1)
    s2 = _runda(g, A={"zatrudnij": [_z(k1, 1)], "wlasciciel_stanowisko": {"typ": "kasa", "nr": 1, "godziny": 10}},
                B={"wlasciciel_stanowisko": {"typ": "kasa", "nr": 1, "godziny": 25}})
    a, b = s2.wyniki[2]["A"], s2.wyniki[2]["B"]
    assert a["wlasciciel_stanowisko"]["przyjete"] and 0 <= a["wlasciciel_stanowisko"]["wykorzystanie"] <= 1
    assert any(p["opis"] == "Praca na stanowisku: Kasa nr 1" and p["godziny"] == 10 and p["przyjete"]
               for p in a["czas_wlasciciela"]["pozycje"])
    assert list(s2.firmy["A"].pracownicy) == [k1["id"]] and s2.firmy["A"].wlasciciel_na is None
    assert not b["wlasciciel_stanowisko"]["przyjete"]
    assert any("Właściciel nie stanie" in t for t in _bledy(s2, 2, "B", "zatrudnienie"))
