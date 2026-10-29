# Levas

Symulacja biznesowa: drużyny prowadzą kebaby w Lublinie. Levas powstaje na bazie lokalnej kopii gry REVAS.

- `notatki/` – notatki projektowe (Obsidian): [Główny obraz](notatki/Główny%20obraz.md), [Plan optymalizacji](notatki/Plan%20optymalizacji.md) (bieżący), [Plan implementacji](archiwum/Plan%20implementacji.md) (archiwum), [Technologia](notatki/Technologia.md).
- `gra/` – kod gry (silnik, serwer, testy).
- `POSTEP.md` – postęp prac.
- `AGENTS.md` – przewodnik po projekcie dla agentów AI (OpenCode, Claude Code); `zadania/` – instrukcje dla ich sesji; `raporty/` – wyniki analiz i kalibracji.
- `dokumentacja/` – tło: `WIEDZA_O_GRZE.md` (mechaniki oryginalnego REVAS) i `ROZNICE_LEVAS_STARY.md` (co było w starej
  wersji Levasa); `archiwum/` – zakończone plany i dzienniki prac.

## Uruchomienie
Windows: `gra/start.bat` (za pierwszym razem tworzy `.venv` i instaluje pakiety). Testy: `gra/.venv/Scripts/python -m pytest` w folderze `gra`.
