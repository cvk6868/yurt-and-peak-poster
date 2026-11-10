@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist geheim.bat (
  echo geheim.bat ontbreekt. Kopieer geheim-voorbeeld.bat naar geheim.bat en vul je sleutels in.
  pause
  exit /b 1
)
call geheim.bat
if "%1"=="echt" (
  python dagelijks.py >> log.txt 2>&1
) else (
  python dagelijks.py --droog >> log.txt 2>&1
)
echo Klaar, zie log.txt
if "%2"=="pauze" pause
