@echo off
REM =======================================================
REM  ADVAK 5.0 - Executar arquivo .dk no Windows
REM  Uso: arraste um arquivo .dk para este .bat
REM       ou execute: rodar.bat projetos\ajuda.dk
REM =======================================================

if "%~1"=="" (
    echo.
    echo  Advak 5.0 - Iniciando guia interativo...
    echo.
    python "%~dp0advak.py" run "%~dp0projetos\ajuda.dk"
) else (
    python "%~dp0advak.py" run "%~1"
)

if errorlevel 1 (
    echo.
    echo  Erro ao executar. Verifique se o Python esta instalado.
    echo  Instale em: https://python.org/downloads
    pause
)
