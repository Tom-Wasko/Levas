"""Księgowość JDG (F3a.11): ceny brutto → KPiR netto + rejestr VAT, rozliczenie rundy co do grosza – składki
właściciela (ulga na start, potem preferencyjny ZUS), zdrowotna z minimum, zaliczka PIT narastająco, VAT
z nadwyżką przenoszoną na następną rundę. Gra Revas (bez mapy) nadal liczy CIT."""

from test_lokale import _gra, _lokal, _rachunek, _runda

from silnik import rozliczenie as rz
from silnik import srodki_trwale as st_trwale
from silnik.dane import dane_domyslne
from silnik.finanse import Ksiega, Rachunek, do_zlotego, ksieguj
from silnik.model import Firma

D = dane_domyslne()


def _ksiega():
    return Ksiega(vat=rz.reguly_vat(D))


def _kpir(ks, opis, kolumna="pozostale"):
    return next(p[kolumna] for p in ks.pozycje if p["opis"] == opis)


def test_vat_wydzielany_z_brutto_wg_stawek():
    f, ks, rach = Firma(nazwa="A", gotowka=0), _ksiega(), Rachunek()
    ksieguj(f, ks, rach, "Sprzedaż: Kebab w bułce", 108, "przychod", stawka=rz.stawka_sprzedazy(D, "kebab_w_bulce"))
    ksieguj(f, ks, rach, "Sprzedaż: Napój", 12.3, "przychod", stawka=rz.stawka_sprzedazy(D, "napoj"))
    ksieguj(f, ks, rach, "Czynsz najmu: Rynek 1", 1230)                    # stawka z reguł po opisie
    ksieguj(f, ks, rach, "Wynagrodzenia pracowników", 3000, "wynagrodzenia")   # bez VAT
    ksieguj(f, ks, rach, "Zakup zasobu od dostawcy: Makro", 228, "towary",
            stawki={rz.stawka_zasobu(D, "Mięso kebab"): 105, rz.stawka_zasobu(D, "Opakowanie"): 123})
    ks.dodaj("Amortyzacja: Rożen", 50)                                     # bez ruchu gotówki – bez VAT
    assert _kpir(ks, "Sprzedaż: Kebab w bułce", "przychod") == 100
    assert _kpir(ks, "Sprzedaż: Napój", "przychod") == 10
    assert _kpir(ks, "Czynsz najmu: Rynek 1") == 1000
    assert _kpir(ks, "Wynagrodzenia pracowników", "wynagrodzenia") == 3000
    assert _kpir(ks, "Zakup zasobu od dostawcy: Makro", "towary") == 200
    assert _kpir(ks, "Amortyzacja: Rożen") == 50
    assert (ks.vat_suma("nalezny"), ks.vat_suma("naliczony")) == (10.3, 258)
    assert f.gotowka == round(108 + 12.3 - 1230 - 3000 - 228, 2)           # rachunek – brutto
    r = rz.rejestr(ks)
    assert [(s["rodzaj"], s["stawka"], s["vat"]) for s in r["stawki"]] == [
        ("nalezny", 0.08, 8), ("nalezny", 0.23, 2.3), ("naliczony", 0.05, 5), ("naliczony", 0.23, 253)]
    assert ks.stawka_vat("Opłata za konto firmowe (PKO BP)") == 0                 # usługi finansowe – zw


def test_zaokraglenia_do_grosza_i_zlotego():
    ks = _ksiega()
    assert ks.zarejestruj("x", {0.08: 24.5}, True) == 1.81                 # 24,5 × 8/108 = 1,8148…
    assert ks.zarejestruj("y", {0.23: 7.5}, True) == 1.40                  # 7,5 × 23/123 = 1,4024…
    assert ks.zarejestruj("z", {0.05: 2.1}, False) == 0.10                 # 2,1 × 5/105 = 0,1 (bez błędu floatów)
    assert (do_zlotego(1084.5), do_zlotego(1084.49), do_zlotego(631.14)) == (1085, 1084, 631)


def _rozlicz(f, runda, sprzedaz=0.0, czynsz=0.0, pensje=0.0):
    ks, rach = _ksiega(), Rachunek()
    ksieguj(f, ks, rach, "Sprzedaż: Kebab w bułce", sprzedaz, "przychod", stawka=0.08)
    ksieguj(f, ks, rach, "Czynsz najmu: Rynek 1", czynsz)
    ksieguj(f, ks, rach, "Wynagrodzenia pracowników", pensje, "wynagrodzenia")
    return rz.rozlicz(D, f, runda, ks, rach), ks, rach


def test_rozliczenie_kolejnych_rund_co_do_grosza():
    f = Firma(nazwa="A", gotowka=50000)
    # runda 1 (ulga na start): dochód 10 000 − 1 000 − 3 000 = 6 000
    w, ks, rach = _rozlicz(f, 1, sprzedaz=10800, czynsz=1230, pensje=3000)
    assert w["ulga_na_start"] and w["zus_spoleczne"] == 0
    assert w["dochod"] == 6000
    assert (w["zdrowotna"], w["zdrowotna_minimum"]) == (294, 74.86)       # 4,9% × 6 000; minimum 324,41 × 12/52
    assert (w["podstawa"], w["podatek_narastajaco"], w["zaliczka"]) == (5706, 1084, 1084)   # 19% × 5 706 = 1 084,14
    assert (w["vat_nalezny"], w["vat_naliczony"], w["vat_do_zaplaty"], w["vat_nadwyzka"]) == (800, 230, 570, 0)
    assert w["razem"] == 294 + 1084 + 570 and w["dochod_netto"] == 6000 - 294 - 1084
    assert f.gotowka == round(50000 + 10800 - 1230 - 3000 - 294 - 1084 - 570, 2)
    assert [o["opis"] for o in rach.operacje][-3:] == ["Składka zdrowotna właściciela",
                                                       "Zaliczka na podatek dochodowy (PIT liniowy)", "VAT do urzędu skarbowego"]
    # runda 2: strata 5 000 + czynsz bez sprzedaży – zdrowotna minimalna, zaliczki 0, nadwyżka VAT 230
    w, _, _ = _rozlicz(f, 2, czynsz=1230, pensje=4000)
    assert w["dochod"] == -5000 and w["zdrowotna"] == 74.86
    assert (w["dochod_narastajaco"], w["zdrowotna_odliczona"]) == (1000, 368.86)
    assert (w["podstawa"], w["podatek_narastajaco"], w["zaliczka"]) == (631, 120, 0)   # bez zwrotu 964 zł w trakcie gry
    assert (w["vat_saldo"], w["vat_do_zaplaty"], w["vat_nadwyzka"]) == (-230, 0, 230)
    # runda 3: VAT należny 80 pomniejszony o nadwyżkę 230 → dalej 150 do przeniesienia
    w, _, _ = _rozlicz(f, 3, sprzedaz=1080)
    assert (w["vat_nadwyzka_poprzednia"], w["vat_do_zaplaty"], w["vat_nadwyzka"]) == (230, 0, 150)
    assert w["zaliczka"] == 0 and f.rozliczenie.zaliczki == 1084                 # 19% × (2 000 − 443,72) < 1 084
    # runda 4: VAT 800 − 150 = 650; dochód narastająco 12 000, odliczona zdrowotna 443,72 + 490
    w, _, _ = _rozlicz(f, 4, sprzedaz=10800)
    assert (w["vat_do_zaplaty"], w["vat_nadwyzka"], w["zdrowotna"]) == (650, 0, 490)
    assert (w["podstawa"], w["podatek_narastajaco"], w["zaliczka"]) == (11066, 2103, 1019)   # 19% × 11 066 = 2 102,54
    assert f.rozliczenie.zaplacone == round(294 + 1084 + 570 + 74.86 + 74.86 + 490 + 1019 + 650, 2)


def test_skladki_spoleczne_po_uldze_i_limit_odliczenia_zdrowotnej():
    f = Firma(nazwa="A", gotowka=0)
    w, ks, _ = _rozlicz(f, 27, sprzedaz=1080)
    assert not w["ulga_na_start"] and w["zus_spoleczne"] == 97.12            # 420,86 × 12/52
    assert _kpir(ks, rz.ZUS_SPOLECZNE) == 97.12 and not any(x["opis"] == rz.ZUS_SPOLECZNE for x in ks.rejestr_vat)
    assert w["dochod"] == round(1000 - 97.12, 2)
    f.rozliczenie.zdrowotna_odliczona = D.podatki["zdrowotna"]["limit_odliczenia_roczny"] - 10
    w, _, _ = _rozlicz(f, 28, sprzedaz=1080)
    assert w["zdrowotna"] == 74.86 and w["zdrowotna_odliczenie"] == 10      # odliczenie do limitu rocznego


def test_srodek_trwaly_netto_w_ewidencji_i_vat_naliczony():
    f, ks, rach = Firma(nazwa="A", gotowka=20000), _ksiega(), Rachunek()
    st_trwale.zakup(D, f, ks, rach, "Koszt zakupu: Rożen", "Rożen", "sprzet", 12300, 1, True)
    assert f.gotowka == 7700 and f.srodki_trwale[0].wartosc == 10000
    assert ks.vat_suma("naliczony") == 2300 and not ks.pozycje
    st_trwale.zakup(D, f, ks, rach, "Koszt zakupu: Lada", "Lada", "wyposazenie", 615, 1, True)   # poniżej progu – koszt
    assert _kpir(ks, "Koszt zakupu: Lada") == 500 and ks.vat_suma("naliczony") == 2415


def test_gra_z_lokalami_rozlicza_jdg_a_revas_cit():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A=_lokal("centrum_3"), B=_lokal("dworzec_1"))
    w = s.wyniki[1]["A"]
    roz, vat = w["rozliczenie"], w["vat"]
    assert roz["ulga_na_start"] and roz["zus_spoleczne"] == 0
    assert (vat["nalezny"], vat["naliczony"]) == (roz["vat_nalezny"], roz["vat_naliczony"])
    assert _rachunek(s, 1, "A", "Składka zdrowotna właściciela") == [-roz["zdrowotna"]]
    assert not _rachunek(s, 1, "A", "Podatek dochodowy")
    assert w["kpir"]["podatek"] == round(roz["zaliczka"] + roz["zdrowotna"], 2)
    assert w["kpir"]["dochod_netto"] == roz["dochod_netto"]
    sprzedaz = [p for p in w["kpir"]["pozycje"] if p["opis"].startswith("Sprzedaż: ")]
    brutto = sum(r["brutto"] for r in vat["pozycje"] if r["opis"].startswith("Sprzedaż: "))
    assert round(sum(p["przychod"] for p in sprzedaz) + vat["nalezny"], 2) == round(brutto, 2)
    assert s.firmy["A"].rozliczenie.dochod == w["kpir"]["dochod"]
    s = _runda(_gra(("A", None), ("B", None), lokale=False))
    assert "rozliczenie" not in s.wyniki[1]["A"] and "vat" not in s.wyniki[1]["A"]
    assert not any(p.get("vat") for p in s.wyniki[1]["A"]["kpir"]["pozycje"])
