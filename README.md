# Levas

Symulacja biznesowa: drużyny prowadzą kebaby w Lublinie. Levas powstaje na bazie lokalnej kopii gry REVAS.

- `notatki/` – notatki projektowe (Obsidian): [Główny obraz](notatki/Główny%20obraz.md), [Plan implementacji](notatki/Plan%20implementacji.md), [Technologia](notatki/Technologia.md).
- `gra/` – kod gry (silnik, serwer, testy).
- `POSTEP.md` – postęp prac.

## Uruchomienie
Windows: `gra/start.bat` (za pierwszym razem tworzy `.venv` i instaluje pakiety). Testy: `gra/.venv/Scripts/python -m pytest` w folderze `gra`.
