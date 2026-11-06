"""balans.warianty z dodatkową kolumną `skladowe` (JSON: per runda 2..N [we, zp, zk, roz, zad]) – do przeliczania
karty z innymi wagami bez nowych gier. Użycie jak `python -m balans.warianty pelny ...`."""
import json
import sys

from balans import warianty as wa

_miary = wa.miary


def miary(s, rund):
    m = _miary(s, rund)
    k = [s.wyniki[r][wa.BADANA]["karta"] for r in range(2, rund + 1)]
    m["skladowe"] = json.dumps([[x["wynik_ekonomiczny"], x["zadowolenie_pracownikow"], x["zadowolenie_klientow"],
                                 x["rozwoj_firmy"], x["wskaznik_zadluzenia"]] for x in k], separators=(",", ":"))
    return m


wa.miary = miary
if "skladowe" not in wa.POLA_GRY:
    wa.POLA_GRY.append("skladowe")

if __name__ == "__main__":
    sys.exit(wa.main(sys.argv[1:]))
