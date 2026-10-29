"""Pliki statyczne bez starych wersji w pamięci przeglądarki.

Strony wczytują pliki z `/static/v<wersja>/…`, gdzie wersja to skrót czasów zmian wszystkich plików
statycznych. Po zmianie zakładki adres jest nowy, więc przeglądarka (i Cloudflare przy `hostuj`) nie
może podać starego modułu – a moduły importowane względnie (`./zakladki/…`) dziedziczą tę wersję.
Odpowiedzi mają dodatkowo `no-cache`. `graj` i `hostuj` uruchamiają serwer bez wbudowanej obsługi
/static/, żeby szła tędy.
"""

import hashlib

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.views import serve
from django.utils.cache import patch_cache_control


def wersja() -> str:
    skrot = hashlib.sha1()
    for finder in finders.get_finders():
        for sciezka, magazyn in finder.list([]):
            skrot.update(f"{sciezka}:{magazyn.get_modified_time(sciezka).timestamp()}".encode())
    return skrot.hexdigest()[:10]


def kontekst(request):
    """`{{ statyczne }}` w szablonach: początek adresu plików statycznych z bieżącą wersją."""
    return {"statyczne": f"/static/v{wersja()}/"}


def widok(request, path):
    odp = serve(request, path, insecure=True)
    patch_cache_control(odp, no_cache=True)
    return odp
