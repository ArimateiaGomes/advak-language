@echo off
REM =======================================================
REM  ADVAK 5.0 - Abrir Guia Interativo de Ensino
REM  Clique duplo para abrir a p?gina de ajuda
REM =======================================================
echo.
echo  Abrindo Advak 5.0 - Guia Interativo...
echo.
python "%~dp0advak.py" run "%~dp0projetos\ajuda.dk"
if errorlevel 1 (
    echo.
    echo  ERRO: Python nao encontrado.
    echo  Instale o Python em: https://python.org/downloads
    echo  Marque "Add Python to PATH" na instalacao.
    pause
)
