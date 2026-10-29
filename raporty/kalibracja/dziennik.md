# Dziennik kalibracji

Pamięć między sesjami części B. Po każdym kroku: co zmierzono, co zmieniono, co wyszło i co dalej. Najnowszy
wpis na dole.

## B1 – inwentarz decyzji (29.10.2026, Claude Code, Opus 5.5)
- Zrobione:
  - docstring `gra/silnik/decyzje.py` uzupełniony o `przejecie`, `wypowiedz`, `lokal.oferta`,
    `wlasciciel_stanowisko`, pola banku w kredytach i lokatach, `leasing_wez`, `harpagon_wez/splac`,
    `wyplata/wplata_wlasna`, `kasyno`, `detektyw` i `higiena`;
  - `raporty/kalibracja/inwentarz.md`: opcje, parametry, użycie przez boty, zamierzony kompromis i 17 hipotez
    (H1–H17).
- Zmierzone (9 gier botów, 18 rund; dokładny pomiar w B4):
  - pierwszy plus w tygodniu 2–4 prawie u wszystkich;
  - marża netto średniego bota 25–40%, praca 12–20% przychodu;
  - wszystkie boty: mBank i e-Księgi24.
- Pytanie do autora (nie blokuje B2):
  - **P1. Umowa zlecenia nie ma składek ZUS pracodawcy** (`runda.py:211`). W prawie 2026 zlecenie też ma
    składki (bez nich tylko student do 26 lat).
  - Czy uznać to za regułę gry (wtedy balansuję innymi kosztami zlecenia, np. rotacją, w B9), czy dodać
    składki do zlecenia jako część zamrożonego prawa?
  - Domyślnie zostawiam bez zmian do B9 i sprawdzam hipotezę H3.
- Dalej: B2 (zamrożone dane testów, profilowanie, wymuszanie decyzji bota, `balans/warianty.py`).
