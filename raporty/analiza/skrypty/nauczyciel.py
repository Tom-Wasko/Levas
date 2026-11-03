"""A2, persona 3 – nauczyciel / mistrz gry: klasa z 4 drużynami i 2 botami, 18 rund.

Drużyny uczniów (decyzje przez API, jak przeglądarka):
- 1A – grają porządnie (kalkulator „jak człowiek – dobry”, biuro, bank);
- 2B – przepalają gotówkę (reklama we wszystkich kanałach, wypłaty właściciela) → alarm debetu
  → mistrz gry daje inwestora ratunkowego;
- 3C – w rundach 5–6 zapominają wysłać (5: zapisany szkic, 6: nic) → mistrz gry zamyka rundę
  „Przelicz mimo braków”;
- 4D – ceny 200% i zamówienia „na zapas” (prognoza ×3).
Mistrz gry: konta uczniów i skład drużyny, pauza (próba przeliczenia w pauzie), zmiana poziomu
bota, cofnięcie rundy i ponowne przeliczenie, eksport JSON i CSV, zrzuty panelu.

Uruchomienie (serwer analizy musi działać): python -X utf8 nauczyciel.py
"""

from __future__ import annotations

from gracz import ANALIZA, Klient, kalkulator, podsumowanie, zapisz_log, zrzut

UCZNIOWIE = ["1A", "2B", "3C", "4D"]
FIRMY = [{"nazwa": n} for n in UCZNIOWIE] + [
    {"nazwa": "Bafra", "bot": "zrownowazony", "poziom": "czlowiek_sredni"},
    {"nazwa": "Sułtan Premium", "bot": "premium", "poziom": "trudny"}]


def teksty(lista):
    return [b["tekst"] for b in lista or []]


def decyzje_1a(gid, v, r):
    return kalkulator(gid, "1A", "zrownowazony", "czlowiek_dobry")


def decyzje_2b(gid, v, r):
    d = kalkulator(gid, "2B", "zrownowazony", "czlowiek_sredni")
    lok = (v["stan"].get("lokale") or [{}])[0].get("id")
    if lok and r >= 3:
        strefa = lok.rsplit("_", 1)[0]
        d["kampanie"] = [{"agencja": a["id"], "kanal": c["id"], "strefa": strefa, "emisje": 10}
                         for a in (v.get("reklama") or {}).get("agencje", [])
                         for c in a.get("kanaly", []) if (c.get("od_rundy") or 1) <= r][:6]
    if r >= 3:
        d["wyplata_wlasna"] = 4000
    return d


def decyzje_4d(gid, v, r):
    d = kalkulator(gid, "4D", "zrownowazony", "czlowiek_sredni")
    for x in (d.get("sprzedaz") or {}).values():
        x["cena"] = round(x["cena"] * 2, 2)
    d["oferta"] = {k: int(p * 3) for k, p in (d.get("oferta") or {}).items()}
    for z in d.get("zamowienia", []):
        if "ilosc" in z:
            z["ilosc"] = round(z["ilosc"] * 3, 2)
    return d


DECYZJE = {"1A": decyzje_1a, "2B": decyzje_2b,
           "3C": lambda gid, v, r: kalkulator(gid, "3C", "zrownowazony", "czlowiek_sredni"),
           "4D": decyzje_4d}


def main():
    k = Klient()
    log = []
    gid = k.nowa_gra("A2 nauczyciel", FIRMY, 303)

    # konta uczniów i skład drużyny 1A
    kod, odp = k.zapytaj("POST", "/api/konta", json={"osoby": ["Ala Analizowa", "Jan Testowy"]})
    konta = odp.get("konta", [])
    loginy = [x["login"] for x in konta]
    sklad = [k.zapytaj("POST", f"/api/gry/{gid}/druzyny/1A", json={"dodaj": x}) for x in loginy]
    log.append({"krok": "konta", "kod": kod, "loginy": loginy,
                "sklad": [(c, o.get("blad") or "ok") for c, o in sklad],
                "druzyny": k.zapytaj("GET", f"/api/gry/{gid}/druzyny")[1]})
    zrzut(gid, None, "", "nauczyciel_r01_mg.png", 1600)
    # 1A gra z konta ucznia (mistrz gry widzi decyzje drużyny z uczniami tylko do odczytu)
    uczen = Klient(konta[0]["login"], konta[0]["haslo"])
    log.append({"krok": "logowanie ucznia", "zalogowany": uczen.zalogowany,
                "mg_zapis_1a": k.decyzje(gid, "1A", {"misja": "test MG"}),
                "obca_druzyna": uczen.decyzje(gid, "2B", {"misja": "test ucznia"}),
                "uczen_mg": uczen.mg(gid)})

    inwestor_dany = False
    for r in range(1, 19):
        wpis = {"runda": r, "mg": []}
        for f in UCZNIOWIE:
            kl = uczen if f == "1A" else k
            v = kl.widok(gid, f)
            if f == "3C" and r == 6:
                wpis["mg"].append("3C nic nie zapisali ani nie wysłali")
                continue
            d = DECYZJE[f](gid, v, r)
            kod, odp = kl.decyzje(gid, f, d)
            if kod != 200:
                wpis.setdefault("odrzucone", {})[f] = odp.get("blad")
                kod, odp = kl.decyzje(gid, f, kalkulator(gid, f, "zrownowazony", "czlowiek_sredni"))
            wpis.setdefault("bledy", {})[f] = teksty(odp.get("lista_bledow"))[:8]
            if f == "3C" and r == 5:
                wpis["mg"].append("3C zapisali szkic, ale nie kliknęli Wyślij")
                continue
            kl.wyslij(gid, f)
        p = k.mg(gid)
        if p["gra"]["runda"] == r:   # runda nie przeliczyła się sama – ktoś nie wysłał
            wpis["czeka_na"] = [f["nazwa"] for f in p["firmy"] if not f.get("wyslane")
                                and not f.get("bot")]
            if r == 5:
                zrzut(gid, None, "", "nauczyciel_r05_mg_czeka.png", 1600)
                k.prowadzenie(gid, {"pauza": True})
                wpis["przelicz_w_pauzie"] = k.przelicz(gid)
                k.prowadzenie(gid, {"pauza": False})
                zrzut(gid, "3C", "dashboard", "nauczyciel_r05_3c_dashboard.png")
            wpis["przelicz_wymus"] = k.przelicz(gid)
            wpis["mg"].append(f"Przelicz mimo braków: {wpis['czeka_na']}")
        wpis["po_rundzie"] = podsumowanie(k, gid)
        alarmy = [n for n, x in wpis["po_rundzie"].items() if x.get("alarm")]
        wpis["alarmy"] = alarmy
        w_alarmie = [n for n in alarmy if n in UCZNIOWIE]
        if w_alarmie and not inwestor_dany:   # pierwsza drużyna w alarmie dostaje inwestora
            inwestor_dany, f = True, w_alarmie[0]
            zrzut(gid, None, "", f"nauczyciel_r{r:02d}_mg_alarm.png", 1600)
            zrzut(gid, f, "dashboard", f"nauczyciel_r{r:02d}_{f}_alarm.png")
            zrzut(gid, f, "wlasciciel", f"nauczyciel_r{r:02d}_{f}_wlasciciel.png")
            wpis["inwestor"] = k.prowadzenie(gid, {"inwestor": {"firma": f, "kwota": 20000}})
            wpis["mg"].append(f"{f} w alarmie – inwestor ratunkowy 20 000 zł")
        if r == 8:
            wpis["zmiana_poziomu"] = k.prowadzenie(
                gid, {"poziom": {"firma": "Bafra", "poziom": "trudny"}})
            wpis["mg"].append("Bafra: poziom bota czlowiek_sredni → trudny")
        if r == 10:   # cofnięcie i ponowne przeliczenie tych samych decyzji
            przed = {n: x["majatek_netto"] for n, x in wpis["po_rundzie"].items()}
            wpis["cofnij"] = k.zapytaj("POST", f"/api/gry/{gid}/cofnij", json={})
            for f in UCZNIOWIE:
                (uczen if f == "1A" else k).wyslij(gid, f)
            if k.mg(gid)["gra"]["runda"] == 10:
                k.przelicz(gid)
            po = {n: x["majatek_netto"] for n, x in podsumowanie(k, gid).items()}
            wpis["cofnij_porownanie"] = {"przed": przed, "po": po}
            wpis["mg"].append("Cofnięcie rundy 10 i ponowne przeliczenie")
        if inwestor_dany and "inwestor_po" not in wpis and r == 12:
            f = next(x["mg"][-1].split()[0] for x in log if x.get("inwestor"))
            zrzut(gid, f, "dashboard", f"nauczyciel_r12_{f}_po_inwestorze.png")
        if r in (6, 12):
            zrzut(gid, None, "", f"nauczyciel_r{r:02d}_mg.png", 1600)
        log.append(wpis)
        zapisz_log("nauczyciel", log)
        print(r, {n: (x["miejsce"], round(x["majatek_netto"] or 0), x["alarm"])
                  for n, x in wpis["po_rundzie"].items()}, wpis["mg"], flush=True)

    # koniec: eksporty i zrzuty
    s = k.s
    for co in ("wyniki", "ranking"):
        x = s.get(f"http://127.0.0.1:8766/api/gry/{gid}/{co}.csv", timeout=120)
        (ANALIZA / f"nauczyciel_{co}.csv").write_bytes(x.content)
    e = s.get(f"http://127.0.0.1:8766/api/gry/{gid}/eksport", timeout=120)
    log.append({"koniec": True, "gid": gid, "eksport_kb": round(len(e.content) / 1024),
                "csv": [(ANALIZA / f"nauczyciel_{c}.csv").stat().st_size
                        for c in ("wyniki", "ranking")],
                "po_grze": podsumowanie(k, gid)})
    zrzut(gid, None, "", "nauczyciel_koniec_mg.png", 1800)
    for f in ("1A", "4D"):
        zrzut(gid, f, "karta_wynikow/wyniki", f"nauczyciel_koniec_{f}_karta.png")
    zapisz_log("nauczyciel", log)


if __name__ == "__main__":
    main()
