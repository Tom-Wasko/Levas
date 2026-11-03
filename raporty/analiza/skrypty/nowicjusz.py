"""A2, persona 1 – nowicjusz (16 lat, pierwszy raz w grze). Gra 4 firm: on + 3 boty, w tym dwa
„jak człowiek”. Typowe błędy: zapomina o banku i biurze, wybiera najtańszy gotowy lokal, chce
sprzedawać wszystko, zaokrągla ceny w górę „żeby zarobić”, sam prowadzi księgowość i nie wpisuje
zapisów, wypłaca sobie pieniądze, bierze pożyczkę u Harpagona, w zdarzeniach klika pierwszą opcję.

Uruchomienie (serwer analizy musi działać): python -X utf8 nowicjusz.py
"""

import math

from gracz import Klient, kalkulator, podsumowanie, zapisz_log, zrzut

FIRMA = "Kebab u Ziomka"
FIRMY = [{"nazwa": FIRMA},
         {"nazwa": "Sułtan", "bot": "tani", "poziom": "czlowiek_slaby"},
         {"nazwa": "Bafra", "bot": "zrownowazony", "poziom": "czlowiek_sredni"},
         {"nazwa": "Döner Max", "bot": "premium", "poziom": "sredni"}]
ZRZUTY = {1: ["dashboard", "lista_bledow", "lokale", "lokal_menu"],
          2: ["lokal_dostawy", "lokal_ludzie", "wnioski/wyniki"],
          3: ["karta_wynikow/wyniki", "raport/wyniki", "zdarzenia"],
          4: ["harpagon", "ksiegowosc", "kpir"],
          6: ["dashboard", "biuro", "urzad"],
          8: ["agencje", "klienci"],
          12: ["mapa", "lokale"],
          19: ["dashboard", "karta_wynikow/wyniki", "wnioski/wyniki", "raport/wyniki"]}


def teksty(lista):
    return [b["tekst"] for b in lista or []]


def main():
    k = Klient()
    gid = k.nowa_gra("A2 nowicjusz", FIRMY, 101)
    log = []
    druga_proba_lokalu = False
    for r in range(1, 19):
        v = k.widok(gid, FIRMA)
        assert v["runda"] == r, (v["runda"], r)
        wpis = {"runda": r, "miesiac": v["miesiac"], "mysli": [],
                "wnioski": v.get("wnioski"), "bledy_przed": teksty(v["lista_bledow"])}
        m = wpis["mysli"]
        for z in ZRZUTY.get(r, []):
            zrzut(gid, FIRMA, z, f"nowicjusz_r{r:02d}_{z.replace('/', '_')}.png")
        wyn = v.get("wyniki") or {}
        dochod = (wyn.get("kpir") or {}).get("dochod_netto")
        gotowka = v["stan"]["gotowka"]
        wpis["stan_na_start"] = {"gotowka": gotowka, "dochod_poprzedniej": dochod,
                                 "dashboard": v.get("dashboard")}

        d = kalkulator(gid, FIRMA, "zrownowazony", "czlowiek_slaby")
        if r == 1:
            # najpierw sama nazwa i kolor – co mówi gra?
            kod, odp = k.decyzje(gid, FIRMA, {"nazwa": FIRMA, "misja": "Najlepszy kebab na dzielni",
                                              "kolor": "#e11d48"})
            wpis["pierwszy_zapis"] = {"kod": kod, "bledy": teksty(odp.get("lista_bledow"))}
            gotowe = [x for x in v["lokale"]["oferta"] if x["typ"] == "gotowy" and x.get("czynsz")]
            tani = min(gotowe, key=lambda x: x["czynsz"])
            d["lokal"] = {"id": tani["id"], "forma": "najem"}
            m.append(f"Biorę najtańszy gotowy lokal: {tani['nazwa']} ({tani['czynsz']:.0f} zł "
                     "czynszu) – gotowy, więc od razu sprzedaję.")
            d["biuro"] = "samodzielnie"
            m.append("Biuro rachunkowe kosztuje, więc księgowość robię sam.")
            d["oferta"] = {**d.get("oferta", {}), "kebab_w_tortilli": 150, "falafel": 80,
                           "talerz_kebab": 60}
            m.append("Dodaję do menu też rollo, falafela i talerz – "
                     "im więcej dań, tym więcej klientów.")
        if d.get("sprzedaz"):
            narzut = 1.2 if r <= 5 or (dochod or 0) > 0 else 1.0
            for x in d["sprzedaz"].values():
                x["cena"] = float(math.ceil(x["cena"] * narzut))
            if r == 2:
                m.append("Ceny podnoszę o 20% i zaokrąglam w górę – chcę zarabiać.")
            if narzut == 1.0 and r > 5:
                m.append("Jestem na minusie – wracam do cen rynkowych.")
        if r == 3:
            d["wyplata_wlasna"] = 2000
            m.append("Wypłacam sobie 2000 zł na nowe buty – w końcu to moja firma.")
        if r == 4 and gotowka < 30000:
            d["harpagon_wez"] = 5000
            m.append(f"Mam tylko {gotowka:.0f} zł. Bank chce papierów, Harpagon daje od ręki – "
                     "biorę 5000 zł.")
        if r == 9 and (v["harpagon"].get("przed") or {}):
            dlug = (v["harpagon"]["przed"] or {}).get("dlug") or 6000
            d["harpagon_splac"] = dlug
            m.append(f"Harpagon straszy – spłacam {dlug:.0f} zł.")
        if r >= 2:
            wybory = {}
            for h in (v.get("zdarzenia") or {}).get("aktywne", []):
                if h.get("opcje"):
                    wybory[h["historia"]] = h["opcje"][0]["id"]
            if wybory:
                d["zdarzenia"] = wybory
                m.append("Zdarzenia: klikam pierwszą opcję, brzmi najciekawiej.")
        if r == 6:
            biura = (v.get("ksiegowosc") or {}).get("oferty") or []
            if biura:
                tanie = min(biura, key=lambda x: x.get("ryczalt") or 0)
                d["biuro"] = tanie["id"]
                m.append(f"Księgowość mnie przerasta – zmieniam na {tanie['nazwa']}.")
        if r == 8:
            strefa = (v["stan"]["lokale"] or [{}])[0].get("id", "").rsplit("_", 1)[0]
            for a in (v.get("reklama") or {}).get("agencje", []):
                kan = next((c for c in a["kanaly"] if c["id"] == "ulotki"), None)
                if kan:
                    d["kampanie"] = [{"agencja": a["id"], "kanal": "ulotki", "strefa": strefa,
                                      "emisje": 10}]
                    m.append("Kolega mówi, że ulotki działają – zamawiam 10 paczek.")
                    break
        if r == 12 and gotowka > 25000 and not druga_proba_lokalu:
            druga_proba_lokalu = True
            wolne = [x for x in v["lokale"]["oferta"] if x["typ"] == "niewyposazony"]
            if wolne:
                drugi = min(wolne, key=lambda x: x.get("czynsz") or 1e9)
                d["lokal"] = {"id": drugi["id"], "forma": "najem"}
                m.append(f"Idzie mi lepiej – biorę drugi lokal: {drugi['nazwa']} (niewyposażony, "
                         "taniej).")

        kod, odp = k.decyzje(gid, FIRMA, d)
        wpis["zapis"] = {"kod": kod, "blad": odp.get("blad"),
                         "bledy": teksty(odp.get("lista_bledow")) if kod == 200 else None}
        if kod != 200:
            m.append(f"Gra nie przyjęła decyzji: {odp.get('blad')} – poprawiam według kalkulatora.")
            d2 = kalkulator(gid, FIRMA, "zrownowazony", "czlowiek_slaby")
            kod, odp = k.decyzje(gid, FIRMA, d2)
            wpis["zapis_poprawiony"] = {"kod": kod, "blad": odp.get("blad"),
                                        "bledy": teksty(odp.get("lista_bledow"))
                                        if kod == 200 else None}
        wpis["decyzje"] = d
        kod, odp = k.wyslij(gid, FIRMA)
        wpis["wyslij"] = {"kod": kod, "przeliczono": odp.get("przeliczono"),
                          "blad": odp.get("blad")}
        wpis["po_rundzie"] = podsumowanie(k, gid)
        log.append(wpis)
        zapisz_log("nowicjusz", log)
        w = wpis["po_rundzie"][FIRMA]
        print(r, kod, w["dochod_ostatni"], w["gotowka"], w["majatek_netto"], w["miejsce"],
              flush=True)
    # koniec gry: widok po 18. rundzie
    for z in ZRZUTY[19]:
        zrzut(gid, FIRMA, z, f"nowicjusz_koniec_{z.replace('/', '_')}.png")
    zrzut(gid, None, "", "nowicjusz_koniec_mg.png", 1600)
    v = k.widok(gid, FIRMA)
    log.append({"koniec": True, "gid": gid, "wnioski": v.get("wnioski"),
                "karta_skumulowana": v.get("karta_skumulowana"), "dashboard": v.get("dashboard")})
    zapisz_log("nowicjusz", log)


if __name__ == "__main__":
    main()
