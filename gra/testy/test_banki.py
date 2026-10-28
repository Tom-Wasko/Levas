"""Banki gry z lokalami (F3a.9): sześć banków z różnymi najlepszymi ofertami, konto i terminal, lokaty w dowolnym
banku, kredyt na start bez historii, inwestycyjny pod zastaw (przejęcie po zaległościach), leasing, limit w koncie."""

from copy import deepcopy

from test_lokale import _gra, _lokal, _netto, _runda

from silnik import banki as bk
from silnik.dane import dane_domyslne
from silnik.finanse import Ksiega, Rachunek


def _kpir(s, r, firma, poczatek):
    return [p for p in s.wyniki[r][firma]["kpir"]["pozycje"] if p["opis"].startswith(poczatek)]


def _bledy(s, r, firma):
    return [b["tekst"] for b in s.wyniki[r][firma]["lista_bledow"] if b["zakladka"] == "finanse_bank"]


def _start():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}, "bank": "mBank"},
               B={**_lokal("zygmuntowskie_1", "kupno"), "bank": "PKO BP"})
    return g, s


def test_kazdy_bank_ma_inna_najlepsza_oferte():
    dane = dane_domyslne()
    naj = bk.najlepsze(dane)
    assert naj == {"konto": "mBank", "lokata": "ING", "kredyt_bez_historii": "Crédit Agricole",
                   "kredyt_inwestycyjny": "PKO BP", "leasing": "Pekao", "limit": "Santander"}
    assert set(naj.values()) == set(bk.banki(dane))


def test_konto_terminal_i_prowizja_od_kart():
    g, s = _start()
    f = deepcopy(s.firmy["A"])
    ks = Ksiega()
    ks.dodaj("Sprzedaż usług", 10000, "przychod")
    info = bk.koniec_rundy(g.dane, f, 2, ks, Rachunek())
    u = bk.ustawienia(g.dane)
    assert info["oplaty"] == {"konto": 0, "terminal": 0, "prowizja": round(10000 * u["udzial_kart"] * 0.0079, 2)}
    s = _runda(g)
    assert _kpir(s, 2, "B", "Opłata za konto firmowe (PKO BP)")[0]["pozostale"] == g.dane.na_runde(20)
    assert _kpir(s, 2, "B", "Abonament terminala")[0]["pozostale"] == _netto(g.dane.na_runde(49))


def test_kredyt_na_start_bez_historii_a_obrotowy_wymaga_historii():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "bank": "mBank",
                     "kredyty_wez": [{"bank": "Crédit Agricole", "produkt": "start", "kwota": 30000, "rund": 26}]},
               B={**_lokal("dworzec_1"), "bank": "mBank",
                  "kredyty_wez": [{"bank": "PKO BP", "produkt": "obrotowy", "kwota": 10000, "rund": 26}]})
    k = s.firmy["A"].kredyty[0]
    assert (k.bank, k.produkt, k.kwota, k.miesiecy) == ("Crédit Agricole", "start", 30000, 26)
    assert _kpir(s, 1, "A", "Prowizja za udzielenie kredytu")[0]["pozostale"] == 900
    assert not s.firmy["B"].kredyty and any("historii" in t for t in _bledy(s, 1, "B"))
    s = _runda(g)   # pierwsza rata od następnej rundy, oprocentowanie Crédit Agricole
    assert s.firmy["A"].kredyty[0].pozostalo == round(30000 - 30000 / 26, 2)
    assert _kpir(s, 2, "A", "Odsetki od kredytu nr")[0]["pozostale"] == round(30000 * 0.119 / 52, 2)


def test_lokata_w_innym_banku_niz_konto():
    g, s = _start()
    s = _runda(g, A={"lokaty_zaloz": [{"bank": "ING", "kwota": 20000, "rund": 4}],
                     "kredyty_wez": [{"bank": "ING", "produkt": "obrotowy", "kwota": 1000, "rund": 4}]})
    lo = s.firmy["A"].lokaty[0]
    assert (lo.bank, lo.oprocentowanie, lo.miesiecy) == ("ING", 0.035, 4)
    assert any("historii" in t for t in _bledy(s, 2, "A"))
    for _ in range(3):
        s = _runda(g)
    assert not s.firmy["A"].lokaty
    odsetki = [p for p in s.wyniki[5]["A"]["kpir"]["pozycje"] if p["opis"].startswith("Odsetki od lokaty")]
    assert odsetki[0]["przychod_pozostaly"] == round(20000 * 0.035 * 4 / 52, 2)


def _zalegla_runda(dane, f, runda):
    f.gotowka, f.kredyt_odnawialny = -1e6, 1e6      # ani gotówki, ani wolnego limitu
    return bk.koniec_rundy(dane, f, runda, Ksiega(), Rachunek())


def test_kredyt_inwestycyjny_pod_zastaw_lokalu_i_przejecie():
    g, s = _start()
    for _ in range(4):
        s = _runda(g)
    assert bk.historia(s.firmy["B"], 6) == 5
    zastaw = bk.zastawy(g.dane, s.firmy["B"])[0]
    assert zastaw["id"] == "lokal:zygmuntowskie_1"
    za_duzo = {"bank": "PKO BP", "produkt": "inwestycyjny", "kwota": zastaw["wartosc"], "rund": 52, "zastaw": zastaw["id"]}
    s = _runda(g, B={"kredyty_wez": [za_duzo]})
    assert not s.firmy["B"].kredyty and any("pod ten zastaw" in t for t in _bledy(s, 6, "B"))
    kwota = round(0.5 * zastaw["wartosc"], 2)
    s = _runda(g, B={"kredyty_wez": [{**za_duzo, "kwota": kwota}]})
    f = deepcopy(s.firmy["B"])
    k = f.kredyty[0]
    assert (k.produkt, k.oprocentowanie, k.zastaw) == ("inwestycyjny", 0.079, "lokal:zygmuntowskie_1")
    assert not bk.zastawy(g.dane, f)                 # lokal już zastawiony
    for r in (8, 9):
        info = _zalegla_runda(g.dane, f, r)
        assert not info["przejecia"] and info["zaleglosci"]
    assert f.kredyty[0].zalegle == 2 and f.kredyty[0].pozostalo > kwota      # odsetki doliczone do długu
    info = _zalegla_runda(g.dane, f, 10)
    p = info["przejecia"][0]
    assert p["zastaw"].startswith("lokal") and p["wycena"] > p["dlug"] and p["nadwyzka"] > 0
    assert not f.kredyty and f.lokale[0].forma == "najem" and f.lokale[0].czynsz > 0
    assert not [x for x in f.srodki_trwale if x.rodzaj == "lokal"]


def test_spozniona_rata_splacana_razem_z_biezaca():
    g, s = _start()
    s = _runda(g, A={"kredyty_wez": [{"bank": "Crédit Agricole", "produkt": "start", "kwota": 26000, "rund": 26}]})
    f = deepcopy(s.firmy["A"])
    _zalegla_runda(g.dane, f, 3)
    k = f.kredyty[0]
    assert (k.zalegle, k.zaleglosc) == (1, 1000)
    f.gotowka, f.kredyt_odnawialny = 50000, 0
    info = bk.koniec_rundy(g.dane, f, 4, Ksiega(), Rachunek())
    assert info["raty"][0]["zaplacona"] and (k.zalegle, k.zaleglosc) == (0, 0)
    assert k.pozostalo == round(26000 + 26000 * 0.119 / 52 - 2000, 2)


def test_leasing_sprzetu_raty_w_koszty_bez_sprzedazy_i_wykup():
    g, s = _start()
    leasing = {"bank": "Pekao", "typ": "kuchnia", "nr": 2, "nazwa": "Rożen", "jakosc": 3, "rund": 26}
    s = _runda(g, A={"leasing_wez": [leasing]})
    f = s.firmy["A"]
    lea = f.leasingi[0]
    assert f.stanowisko("kuchnia", 2).sprzet["Rożen"] == 3 and not f.srodki_trwale
    assert lea.rata == bk.rata_annuitetowa(7000 * 0.9, 0.075, 26, 52)
    assert _kpir(s, 2, "A", "Opłata wstępna leasingu")[0]["pozostale"] == _netto(700)
    s = _runda(g, A={"sprzet_sprzedaj": [{"typ": "kuchnia", "nr": 2, "nazwa": "Rożen"}]})
    assert "Rożen" in s.firmy["A"].stanowisko("kuchnia", 2).sprzet
    assert _kpir(s, 3, "A", "Rata leasingowa")[0]["pozostale"] == _netto(lea.rata)
    f = deepcopy(s.firmy["A"])
    f.leasingi[0].pozostalo_rat = 1
    info = bk.koniec_rundy(g.dane, f, 4, Ksiega(), Rachunek())
    assert info["wykupy"] and not f.leasingi and "Rożen" not in f.stanowisko("kuchnia", 2).sprzet_wynajmujacego


def test_leasing_zalegly_bank_zabiera_sprzet():
    g, s = _start()
    s = _runda(g, A={"leasing_wez": [{"bank": "PKO BP", "typ": "kuchnia", "nr": 2, "nazwa": "Rożen", "jakosc": 1, "rund": 52}]})
    f = deepcopy(s.firmy["A"])
    for r in (3, 4, 5):
        info = _zalegla_runda(g.dane, f, r)
    assert info["przejecia"] and not f.leasingi and "Rożen" not in f.stanowisko("kuchnia", 2).sprzet


def test_limit_w_koncie_i_debet_ponad_limit():
    g, s = _start()
    f = deepcopy(s.firmy["A"])
    f.bank, f.kredyt_odnawialny, f.gotowka = "Santander", 50000, 0
    ks = Ksiega()
    bk.koniec_rundy(g.dane, f, 2, ks, Rachunek())
    poz = {p["opis"]: p["pozostale"] for p in ks.pozycje}
    assert poz["Odsetki od limitu w koncie"] == round(40000 * 0.169 / 52, 2)
    assert poz["Odsetki karne od debetu ponad limit"] == round(10000 * 0.19 / 52, 2)
    assert bk.debet_ponad_limit(g.dane, f) == 10000
    assert any("ponad limit" in b["tekst"] for b in bk.bledy(g.dane, f, None, None))


def test_kredyt_inwestycyjny_od_wziecia_lokalu_bez_historii():
    inw = {"bank": "PKO BP", "produkt": "inwestycyjny", "kwota": 20000, "rund": 52}
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "bank": "mBank", "kredyty_wez": [{**inw, "zastaw": "lokal:centrum_3"}]},
               B={"bank": "mBank", "kredyty_wez": [{**inw, "zastaw": "lokal:centrum_3"}]})
    assert not s.firmy["B"].kredyty and any("firmie z lokalem" in t for t in _bledy(s, 1, "B"))
    assert not s.firmy["A"].kredyty     # wynajęty lokal nie jest zastawem
    g, s = _start()
    zastaw = bk.zastawy(g.dane, s.firmy["B"])[0]
    s = _runda(g, B={"kredyty_wez": [{**inw, "zastaw": zastaw["id"]}]})   # runda 2 – bez 4 rund historii
    assert [(k.produkt, k.zastaw) for k in s.firmy["B"].kredyty] == [("inwestycyjny", "lokal:zygmuntowskie_1")]


def test_kredyt_inwestycyjny_na_zakup_lokalu_w_tej_samej_rundzie():
    g = _gra(("A", None), ("B", None))
    cena = g.dane.lokale["politechnika_3"]["cena"]       # więcej niż kapitał startowy
    kred = {"bank": "PKO BP", "produkt": "inwestycyjny", "kwota": 60000, "rund": 104, "zastaw": "lokal:politechnika_3"}
    assert cena > 100000
    oferta_a = {"lokal": {"id": "politechnika_3", "forma": "kupno", "oferta": cena + 5000}}
    s = _runda(g, A={**oferta_a, "bank": "mBank", "kredyty_wez": [kred]},
               B={**_lokal("politechnika_3", "kupno"), "bank": "mBank", "kredyty_wez": [kred]})
    a = s.firmy["A"]
    assert [lok.id for lok in a.lokale] == ["politechnika_3"]
    assert [(k.kwota, k.zastaw) for k in a.kredyty] == [(60000, "lokal:politechnika_3")]
    assert not bk.zastawy(g.dane, a)                 # kupiony lokal już zastawiony
    b = s.firmy["B"]   # przegrał licytację – nie ma lokalu pod zastaw, kredyt przepada
    assert not b.lokale and not b.kredyty
    assert any("nie został kupiony" in t for t in _bledy(s, 1, "B"))
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("politechnika_3", "kupno"), "bank": "mBank", "kredyty_wez": [{**kred, "kwota": 30000}]})
    assert not s.firmy["A"].lokale and not s.firmy["A"].kredyty     # za mały kredyt – brak gotówki na zakup
