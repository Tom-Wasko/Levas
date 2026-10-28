@echo off
rem Levas - gra z kolegami przez internet (tunel Cloudflare). Podwojne klikniecie.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Pierwsze uruchomienie: tworze srodowisko Pythona i instaluje pakiety...
  python -m venv .venv || (echo Nie znaleziono Pythona 3.12+. Zainstaluj go z python.org & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
)
if not exist ".venv\Lib\site-packages\django" ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
".venv\Scripts\python.exe" manage.py hostuj
pause
