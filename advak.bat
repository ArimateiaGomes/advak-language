@echo off
setlocal
rem Guarda a pagina de codigo do Prompt para devolve-la no fim (setlocal nao restaura isso).
set "CP="
for /f "tokens=2 delims=:." %%a in ('chcp') do set "CP=%%a"
if defined CP set "CP=%CP: =%"
chcp 65001 >nul
set PYTHONUTF8=1
python "%~dp0advak.py" %*
set "RC=%ERRORLEVEL%"
if defined CP chcp %CP% >nul
endlocal & exit /b %RC%