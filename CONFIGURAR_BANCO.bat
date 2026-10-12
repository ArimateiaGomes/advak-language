@echo off
chcp 65001 >nul
cls
echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║   ADVAK 5.0 — Configuração do PostgreSQL      ║
echo  ╚════════════════════════════════════════════════╝
echo.
echo  Cada projeto cria seu próprio banco automaticamente.
echo  Aqui você configura apenas a CONEXÃO com o PostgreSQL.
echo.

if exist .env (
    echo  [!] Arquivo .env já existe:
    type .env
    echo.
    set /p RECONF=  Reconfigurar? (S/N): 
    if /i not "%RECONF%"=="S" goto :fim
    echo.
)

echo  Preencha os dados do PostgreSQL:
echo  (Enter = valor padrão entre colchetes)
echo.

set /p DB_HOST=  Host [localhost]: 
if "%DB_HOST%"=="" set DB_HOST=localhost

set /p DB_PORT=  Porta [5432]: 
if "%DB_PORT%"=="" set DB_PORT=5432

set /p DB_USER=  Usuário [postgres]: 
if "%DB_USER%"=="" set DB_USER=postgres

set /p DB_PASS=  Senha: 

echo.
echo  Salvando .env ...

(
echo # ADVAK 5.0 — Configuração do banco de dados
echo # Cada projeto cria seu proprio banco automaticamente.
echo # Ex: banco_auto("biblioteca") cria o banco "biblioteca"
echo.
echo ADVAK_DB_HOST=%DB_HOST%
echo ADVAK_DB_PORT=%DB_PORT%
echo ADVAK_DB_USER=%DB_USER%
echo ADVAK_DB_PASS=%DB_PASS%
) > .env

echo.
echo  ✅ .env salvo! Agora execute qualquer projeto:
echo.
echo     advak projetos\biblioteca.dk
echo     advak projetos\app_completo.dk
echo.
echo  O banco correto é criado automaticamente na 1ª execução.
echo.

:fim
pause
