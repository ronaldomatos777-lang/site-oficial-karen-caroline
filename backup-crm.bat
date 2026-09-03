@echo off
setlocal
cd /d "%~dp0"

if not exist "data\leads.db" (
  echo Banco de dados ainda nao existe: data\leads.db
  pause
  exit /b 1
)

if not exist "backups" mkdir "backups"

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set "datetime=%%I"
if not defined datetime (
  for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "timestamp=%%I"
) else (
  set "timestamp=%datetime:~0,8%-%datetime:~8,6%"
)

copy /Y "data\leads.db" "backups\leads-%timestamp%.db" >nul
if errorlevel 1 (
  echo Falha ao criar o backup.
  pause
  exit /b 1
)

echo Backup concluido: backups\leads-%timestamp%.db
pause
exit /b 0
