"""Wnioski z rundy (silnik/wnioski.py): co się udało i rady do kolejnej rundy – reguły na wynikach firmy."""

from test_lokale import _gra, _lokal, _runda

from silnik.dane import dane_domyslne
from silnik.wnioski import wnioski

D = dane_domyslne()


def _w(**zmiany):
    w = {"kpir": {"dochod_netto": 500.0, "przychody": 3000.0, "koszty": 2500.0, "towary": 1000.0,
                  "wynagrodzenia": 1200.0, "pozostale": 300.0},
         "sprzedaz": {}, "lokale": [{"dziala": True, "dziala_od": 1}], "lista_bledow": [], "kredyt_odnawialny": 0.0}
    return w | zmiany


def _danie(popyt, sprzedaz, prognoza, przyczyna="", reklamacje=0):
    return {"popyt": popyt, "sprzedaz": sprzedaz, "utracona": popyt - sprzedaz, "prognoza": prognoza,
            "przyczyna": przyczyna, "reklamacje": reklamacje}


def test_brak_wynikow_i_dobra_runda():
    assert wnioski(D, None) is None
    w = wnioski(D, _w(sprzedaz={"kebab_box": _danie(100, 100, 100)}))
    assert w["do_poprawy"] == []
    assert any("100 klientów" in t for t in w["dobre"]) and any("na plusie" in t for t in w["dobre"])


def test_rady_wedlug_przyczyny_i_prognozy():
    w = wnioski(D, _w(sprzedaz={
        "kebab_box": _danie(100, 60, 50, "zasoby (Mięso)"),
        "kebab_w_bulce": _danie(80, 40, 80, "kasa", reklamacje=3),
        "talerz_kebab": _danie(20, 20, 40),
    }))
    tytuly = {r["tytul"]: r for r in w["do_poprawy"]}
    assert "brak: Mięso" in tytuly["Zabrakło składników"]["co"] and tytuly["Zabrakło składników"]["zakladka"] == "dostawcy"
    assert tytuly["Kolejka przy kasie"]["zakladka"] == "zatrudnienie"
    assert "Kebab box" in tytuly["Chętnych było więcej, niż zakładała prognoza"]["co"]
    assert "Talerz" in tytuly["Prognoza była wyższa niż popyt"]["co"]
    assert "Klienci reklamowali dania" in tytuly


def test_strata_i_mandaty_z_rada():
    w = wnioski(D, _w(kpir={"dochod_netto": -800.0, "przychody": 1000.0, "koszty": 1800.0, "towary": 300.0,
                            "wynagrodzenia": 1200.0, "pozostale": 300.0},
                      ksiegowosc={"tryb": "deklaracja", "kara": 500.0},
                      magazyn={"sanepid": {"przeterminowane": 150.0, "mandat": 400.0}}))
    tytuly = {r["tytul"]: r for r in w["do_poprawy"]}
    assert "pensje" in tytuly["Runda na minusie"]["rada"] and "normalna" in tytuly["Runda na minusie"]["co"]
    assert {"Mandat za deklaracje", "Mandat z sanepidu", "Część składników się przeterminowała"} <= set(tytuly)
    assert w["dobre"]   # zawsze coś zachęcającego na początek


def test_czerwone_bledy_bez_powtorzen_i_z_limitem():
    bledy = [{"poziom": "czerwony", "zakladka": f"z{i}", "tekst": f"błąd {i}"} for i in range(5)]
    bledy.append({"poziom": "czerwony", "zakladka": "kpir", "tekst": "powtórka"})
    w = wnioski(D, _w(kpir={**_w()["kpir"], "dochod_netto": -1.0}, lista_bledow=bledy))
    sygnaly = [r for r in w["do_poprawy"] if r["tytul"] == "Sygnał z listy błędów"]
    assert len(sygnaly) == D.z["wnioski"]["bledy_max"] and all(r["co"] != "powtórka" for r in sygnaly)


def test_wnioski_po_rundzie_bez_lokalu_i_z_lokalem():
    g = _gra()
    s = _runda(g, A=_lokal("centrum_2"), B={})
    assert wnioski(D, s.wyniki[1]["B"])["do_poprawy"][0]["tytul"] == "Firma nie ma jeszcze lokalu"
    assert "Macie lokal" in " ".join(wnioski(D, s.wyniki[1]["A"])["dobre"])
