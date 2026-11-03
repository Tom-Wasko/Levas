@echo off
rem Levas - ustawienie stalego linku do gry z hostuj.bat (raz). Podwojne klikniecie.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Najpierw uruchom start.bat albo hostuj.bat - przygotuja srodowisko Pythona.
  pause & exit /b 1
)
".venv\Scripts\python.exe" manage.py staly_link %*
pause
