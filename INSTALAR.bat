@echo off
chcp 65001 >nul 2>nul

echo.
echo ======================================================
echo   ADVAK 5.0 - Instalador Windows
echo ======================================================
echo.
echo  Isso vai adicionar o Advak ao PATH do Windows para
echo  que voce possa usar apenas:
echo.
echo     advak projetos\meu_app.dk
echo.
echo  em vez de:
echo.
echo     python advak.py projetos\meu_app.dk
echo.

:: Detecta pasta atual do Advak (sem barra final)
set "ADVAK_DIR=%~dp0"
if "%ADVAK_DIR:~-1%"=="\" set "ADVAK_DIR=%ADVAK_DIR:~0,-1%"

echo  Pasta do Advak: %ADVAK_DIR%
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado!
    echo  Instale em: https://python.org/downloads
    echo  Marque "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Python: %PYVER%
echo.

:: Verifica se ja esta no PATH
echo %PATH% | findstr /i /c:"%ADVAK_DIR%" >nul 2>&1
if not errorlevel 1 (
    echo  Advak ja esta no PATH!
    goto :fim
)

:: Adiciona ao PATH do usuario (sem precisar de admin)
echo  Adicionando ao PATH...

:: Le PATH atual do usuario
for /f "skip=2 tokens=2*" %%a in ('reg query HKCU\Environment /v PATH 2^>nul') do set "OLD_PATH=%%b"

if "%OLD_PATH%"=="" (
    setx PATH "%ADVAK_DIR%" >nul 2>&1
) else (
    setx PATH "%OLD_PATH%;%ADVAK_DIR%" >nul 2>&1
)

if errorlevel 1 (
    echo.
    echo  AVISO: Nao foi possivel modificar o PATH automaticamente.
    echo.
    echo  Adicione manualmente:
    echo    1. Tecla Win + R, digite: sysdm.cpl
    echo    2. Aba "Avancado" - "Variaveis de Ambiente"
    echo    3. Em "Variaveis do usuario", edite "Path"
    echo    4. Clique "Novo" e adicione: %ADVAK_DIR%
    echo    5. OK em tudo
    echo.
    pause
    goto :fim
)

echo  PATH atualizado!
echo.
echo  IMPORTANTE: Feche e reabra o terminal para aplicar.

:fim
echo.
echo ------------------------------------------------------
echo  TESTE (funciona nesta janela com o caminho completo):
echo.
call "%ADVAK_DIR%\advak.bat" --versao
echo.
echo ------------------------------------------------------
echo  INSTALACAO CONCLUIDA!
echo.
echo  Depois de reabrir o terminal, use:
echo.
echo    advak projetos\compilador_demo.dk
echo    advak projetos\guia_gui.dk
echo    advak projetos\estoque.dk
echo    advak
echo.
pause
