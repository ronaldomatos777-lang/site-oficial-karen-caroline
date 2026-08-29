@echo off
cd /d "%~dp0"
title Karen Caroline Imoveis - Servidor Local

echo ============================================
echo   KAREN CAROLINE IMOVEIS - SITE + CRM
echo ============================================
echo.
echo Iniciando servidor local...
start "Karen Caroline - Servidor" /min cmd /c "cd /d "%~dp0" && python app.py"

echo Aguardando o CRM ficar disponivel...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/health -TimeoutSec 1; if($r.StatusCode -eq 200){$ok=$true;break} } catch {}; Start-Sleep -Milliseconds 500 }; if($ok){exit 0}else{exit 1}"
if errorlevel 1 (
  echo.
  echo Nao foi possivel iniciar o servidor.
  echo Verifique se o Python e as dependencias estao instalados.
  echo.
  pause
  exit /b 1
)

echo.
echo Site: http://127.0.0.1:5000
echo CRM:  http://127.0.0.1:5000/admin
echo.
echo Abrindo o site no navegador...
start "" http://127.0.0.1:5000
exit
