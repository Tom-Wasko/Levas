"""Stały link do gry hostowanej na tym komputerze (hostuj.bat).

Tunel Cloudflare ma nowy adres przy każdym uruchomieniu. Jeśli w `lokalne.json` jest sekcja
`staly_link` (zakłada ją `manage.py staly_link`, staly_link.bat), hostuj wgrywa przez FTP z TLS na
zwykły hosting WWW (np. katalog subdomeny) dwa pliki:

- `.htaccess` – przekierowanie 302 na bieżący tunel (z zachowaniem ścieżki),
- `index.html` – to samo przekierowanie zapasowo (gdyby serwer pominął `.htaccess`).

Po zakończeniu gry (Ctrl+C) wgrywa stronę „gra jest wyłączona”. Na hostingu nie trzeba Pythona –
wystarczą pliki statyczne.
"""

import ftplib
import html
import io
import json
import ssl

from django.conf import settings

KLUCZ = "staly_link"


def konfiguracja() -> dict | None:
    """Sekcja `staly_link` z lokalne.json albo None (stały link nie jest ustawiony)."""
    konfig = settings.LOKALNE.get(KLUCZ)
    return konfig if konfig and konfig.get("host") and konfig.get("login") else None


def zapisz_konfiguracje(konfig: dict | None) -> None:
    """Zapisuje (albo z None – usuwa) sekcję `staly_link` w lokalne.json."""
    if konfig is None:
        settings.LOKALNE.pop(KLUCZ, None)
    else:
        settings.LOKALNE[KLUCZ] = konfig
    settings.PLIK_LOKALNY.write_text(json.dumps(settings.LOKALNE, indent=1), encoding="utf-8")


def htaccess(url: str | None) -> str:
    linie = [
        "# Levas - plik nadpisywany przez hostuj.bat (stały link do gry)",
        "DirectoryIndex index.html",
        "<IfModule mod_headers.c>",
        '  Header set Cache-Control "no-store"',
        "</IfModule>",
    ]
    if url:
        linie += [
            "<IfModule mod_rewrite.c>",
            "  RewriteEngine On",
            f"  RewriteRule ^(.*)$ {url}/$1 [R=302,L]",
            "</IfModule>",
        ]
    return "\n".join(linie) + "\n"


def strona(url: str | None) -> str:
    if url:
        u = html.escape(url, quote=True)
        tytul = "Levas – przekierowanie do gry"
        glowa = f'<meta http-equiv="refresh" content="0; url={u}/">'
        tresc = (f'<p>Przechodzę do gry… Jeśli nic się nie dzieje, kliknij: '
                 f'<a href="{u}/">{u}</a></p>'
                 f"<script>location.replace({json.dumps(url + '/')});</script>")
    else:
        tytul, glowa = "Levas – gra wyłączona", ""
        tresc = ("<p>Gra jest teraz wyłączona – gospodarz uruchamia ją na swoim komputerze.</p>"
                 "<p>Spróbuj później albo zapytaj mistrza gry, kiedy wystartuje.</p>")
    return (
        '<!doctype html>\n<html lang="pl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Cache-Control" content="no-store">'
        f"{glowa}<title>{tytul}</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:32rem;margin:3rem auto;"
        "padding:0 1rem;color:#222;background:#fff}h1{font-size:1.5rem}</style>"
        f"</head><body><h1>{tytul}</h1>{tresc}</body></html>\n"
    )


def pliki(url: str | None) -> dict[str, str]:
    """Pliki do wgrania: przekierowanie na `url` albo (None) strona „gra wyłączona”."""
    url = url.rstrip("/") if url else None
    return {".htaccess": htaccess(url), "index.html": strona(url)}


class FTPS(ftplib.FTP_TLS):
    """FTP z TLS, który na kanale danych wznawia sesję TLS kanału poleceń – ProFTPD (np. LH.pl)
    zwykle tego wymaga („522 SSL connection failed: session reuse required”)."""

    def ntransfercmd(self, cmd, rest=None):
        conn, rozmiar = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, rozmiar


def wgraj(konfig: dict, url: str | None) -> None:
    """Wgrywa pliki przekierowania (albo strony „gra wyłączona”) przez FTP z TLS."""
    with FTPS(konfig["host"], timeout=30, context=ssl.create_default_context()) as ftp:
        ftp.login(konfig["login"], konfig["haslo"])
        ftp.prot_p()
        if konfig.get("katalog"):
            ftp.cwd(konfig["katalog"])
        for nazwa, tresc in pliki(url).items():
            ftp.storbinary(f"STOR {nazwa}", io.BytesIO(tresc.encode("utf-8")))


def ustaw(url: str | None) -> str | None:
    """Ustawia stały link na `url` (None – „gra wyłączona”). Zwraca adres stałego linku albo None,
    gdy nie jest skonfigurowany; błędy połączenia wypisuje i nie przerywa gry."""
    if not (konfig := konfiguracja()):
        return None
    try:
        wgraj(konfig, url)
    except (OSError, ftplib.Error) as blad:
        print(f"Nie udało się ustawić stałego linku ({konfig['host']}): {blad}", flush=True)
        return None
    return konfig.get("adres") or konfig["host"]
