# Instalação da Advak — passo a passo para iniciantes

Este guia leva você do zero até o primeiro programa funcionando. Leva uns 15 minutos. Você **não precisa
saber programar** para seguir.

**O que você precisa de verdade:** só o Python e a pasta da Advak. O PostgreSQL (banco de dados) e as
bibliotecas extras são **opcionais**: dê o passo 5 só quando for usar banco de dados. Sem o PostgreSQL, a
Advak usa o SQLite sozinha.

> Os comandos deste guia foram executados no **Windows 10** com o **Python 3.13**. A parte de Linux foi
> escrita a partir dos comandos padrão dessas distribuições e **não foi testada em um Linux de verdade** —
> se algo não funcionar, avise.

## Índice

1. [Instalar o Python (Windows)](#1-instalar-o-python-windows)
2. [Baixar a Advak](#2-baixar-a-advak)
3. [Instalar as bibliotecas e o comando `advak`](#3-instalar-as-bibliotecas-e-o-comando-advak)
4. [Testar a instalação](#4-testar-a-instalação)
5. [PostgreSQL (opcional)](#5-postgresql-opcional)
6. [Outros bancos de dados (opcional)](#6-outros-bancos-de-dados-opcional)
7. [Instalação no Linux](#7-instalação-no-linux)
8. [Problemas comuns](#8-problemas-comuns)

---

## 1. Instalar o Python (Windows)

1. Abra <https://www.python.org/downloads/> e clique no botão amarelo **Download Python 3.x.x**
   (pegue a versão estável mais recente; a Advak foi testada com o Python 3.13).
2. Abra o arquivo baixado (`python-3.x.x-amd64.exe`).
3. **Atenção — este é o passo mais importante:** na primeira tela, marque a caixa
   **"Add python.exe to PATH"** (em instaladores mais antigos o texto é **"Add Python 3.x to PATH"**).
   Sem isso o Windows não encontra o Python depois.
4. Clique em **Install Now** e espere terminar. Clique em **Close**.
5. Confira: abra o **Prompt de Comando** (tecle `Win`, digite `cmd` e Enter) e digite:

```cmd
python --version
```

Deve aparecer algo como `Python 3.13.8`. Se aparecer *"'python' não é reconhecido..."*, veja
[Problemas comuns](#python-não-é-reconhecido).

## 2. Baixar a Advak

Escolha **uma** das duas formas.

**Forma A — com o Git** (recomendada: depois você atualiza com um comando só). Instale o Git em
<https://git-scm.com/downloads> (pode ir clicando em *Next*) e, no Prompt de Comando:

```cmd
cd C:\
git clone https://github.com/ArimateiaGomes/advak-language.git
cd advak-language
```

**Forma B — sem o Git (ZIP):**

1. Abra <https://github.com/ArimateiaGomes/advak-language>.
2. Clique no botão verde **Code** e depois em **Download ZIP**.
3. Clique com o botão direito no arquivo `.zip` baixado → **Extrair tudo...** e escolha uma pasta simples,
   por exemplo `C:\advak-language`.
4. No Prompt de Comando, entre na pasta:

```cmd
cd C:\advak-language
```

> **Dica:** use uma pasta com nome curto, **sem acentos nem espaços** (evite *Área de Trabalho* ou *Meus
> Documentos*). Isso evita vários problemas.

Dentro da pasta você deve ver arquivos como `advak.py`, `INSTALAR.bat` e `README.md`. Confira com `dir`.

## 3. Instalar as bibliotecas e o comando `advak`

### 3.1 Bibliotecas do Python (`pip`)

Ainda dentro da pasta da Advak:

```cmd
pip install ttkbootstrap psycopg2-binary pyserial paho-mqtt pyinstaller
```

| Biblioteca | Para que serve | Precisa? |
|---|---|---|
| `psycopg2-binary` | Falar com o PostgreSQL | Só se for usar o PostgreSQL |
| `ttkbootstrap` | Deixar as janelas (interface gráfica) mais bonitas | Só para programas com janela |
| `pyinstaller` | Transformar um programa `.dk` em `.exe` | Só para compilar |
| `pyserial` | Conversar com Arduino pela porta USB | Só para eletrônica |
| `paho-mqtt` | Conversar com dispositivos IoT (ESP32) | Só para eletrônica |

Os programas simples (variáveis, contas, listas, arquivos...) **não precisam de nenhuma** delas. Se o
`pip` reclamar de permissão, use `pip install --user ...`.

### 3.2 O comando `advak` (`INSTALAR.bat`)

Na pasta da Advak, dê **dois cliques em `INSTALAR.bat`** (ou rode `INSTALAR.bat` no Prompt de Comando).
Ele adiciona a pasta da Advak ao **PATH do seu usuário** (não precisa ser administrador). Quando terminar,
ele mesmo mostra o resultado de `advak --versao`.

**Feche o Prompt de Comando e abra outro.** O Windows só enxerga o `advak` em janelas abertas **depois**
do `INSTALAR.bat`. A partir daí você digita só `advak programa.dk`, em qualquer pasta, em vez de
`python advak.py programa.dk`.

## 4. Testar a instalação

Em um Prompt de Comando **novo**:

```cmd
advak --versao
```

Resultado esperado:

```text
Advak 5.2.0
```

Teste um programa de verdade — o tour pela sintaxe que vem na pasta (`sintaxe_completa.dk`):

```cmd
cd C:\advak-language
advak sintaxe_completa.dk
```

Ele imprime várias seções e termina com:

```text
═══════════════════════════════
✅ Sintaxe Advak — TUDO OK!
```

Agora seu primeiro programa. Crie (no Bloco de Notas) um arquivo `ola.dk` com:

```advak
seja nome = entrada("Qual é o seu nome? ")
imprimir(`Olá, ${nome}! Bem-vindo à Advak.`)
```

Salve em UTF-8 (o padrão do Bloco de Notas do Windows 10/11 serve) e rode `advak ola.dk`.

> Se o `advak` não for reconhecido, você ainda pode usar `python advak.py ola.dk` dentro da pasta da
> Advak. Veja [PATH não atualizado](#advak-não-é-reconhecido--o-path-não-atualizou).

## 5. PostgreSQL (opcional)

O PostgreSQL é o banco de dados "grande" que a Advak usa nos exemplos de cadastro. **Pule este passo** se
você ainda não vai usar banco de dados.

### 5.1 Baixar

| Sistema | Link |
|---|---|
| **Windows** (instalador EDB — o mais fácil) | <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads> |
| Todos os sistemas (página oficial) | <https://www.postgresql.org/download/> |
| Linux | <https://www.postgresql.org/download/linux/> |
| pgAdmin (programa visual para ver o banco — opcional, já vem no instalador do Windows) | <https://www.pgadmin.org/download/> |

### 5.2 Instalar no Windows, passo a passo

> As telas do instalador mudam um pouco de uma versão para outra (esta descrição segue o instalador oficial
> da EDB; não foi refeita a cada versão). O que importa são **três decisões**: a **senha**, a **porta** e
> **anotar** as duas.

1. Na página da EDB, escolha a **versão** (a mais recente que estiver marcada como estável serve) e
   **Windows x86-64**, e baixe.
2. Abra o instalador (**Executar como administrador**, se o Windows pedir) e clique em **Next**.
3. **Installation Directory** — deixe o padrão. **Next**.
4. **Select Components** — deixe marcados **PostgreSQL Server**, **pgAdmin 4** e **Command Line Tools**.
   (Stack Builder é opcional; pode desmarcar.) **Next**.
5. **Data Directory** — deixe o padrão. **Next**.
6. **Password** — digite a **senha do usuário `postgres`** (o administrador do banco). **Anote essa
   senha em um lugar seguro**: sem ela você não conecta. Se esquecer, é preciso redefinir.
7. **Port** — mantenha **5432** (é a porta padrão que a Advak espera). **Next**.
8. **Locale** — pode deixar *Default locale* (ou *Portuguese, Brazil*). **Next**.
9. Confira o resumo, clique em **Next** e depois **Next** para instalar. Espere terminar e clique em
   **Finish**.

### 5.3 Testar a conexão (antes de usar a Advak)

Pelo **pgAdmin 4** (instalado junto): abra, clique em **Servers → PostgreSQL**, digite a senha do passo 6.
Se aparecerem as pastas *Databases*, *Login/Group Roles*..., o banco está funcionando.

Ou pelo Prompt de Comando (o instalador coloca o *SQL Shell (psql)* no menu Iniciar): abra-o, aperte Enter
nas perguntas de servidor/banco/porta/usuário, digite a senha e, se aparecer `postgres=#`, funcionou.

### 5.4 Contar a senha para a Advak (`.env`)

Na pasta da Advak:

```cmd
copy .env.exemplo .env
notepad .env
```

No Bloco de Notas, troque `sua_senha_aqui` pela senha que você anotou, **sem aspas e sem espaços**, e salve:

```ini
ADVAK_DB_HOST=localhost
ADVAK_DB_PORT=5432
ADVAK_DB_USER=postgres
ADVAK_DB_PASS=a_senha_que_voce_anotou
```

Se preferir, o `CONFIGURAR_BANCO.bat` pergunta esses dados e cria o `.env` para você.

> O arquivo `.env` guarda sua senha e fica **só no seu computador**: ele está no `.gitignore` e nunca vai
> para o GitHub. Nunca coloque a senha dentro de um programa `.dk`.

### 5.5 Testar a Advak com o PostgreSQL

```cmd
advak run primeiros_passos.dk --db
```

Resultado esperado (resumo): ele cria o banco `advak_windows`, uma tabela `contatos` e lista 5 contatos:

```text
Advak funcionando no Windows!
Versao: 3.0  |  Banco: PostgreSQL
Criando banco de dados...
Banco selecionado: advak_windows
Tabela 'contatos' criada!
5 contatos inseridos!
Total de contatos: 5
```

Se você rodar de novo, aparece `❌ Erro: ERRO: o banco de dados "advak_windows" já existe`. **Isso é normal**:
o programa tenta criar o banco, vê que já existe e continua.

### 5.6 Sem PostgreSQL: SQLite automático

Se o PostgreSQL não estiver instalado ou configurado, `banco_auto("minha_app")` cria um arquivo SQLite no
lugar, sem configurar nada. É perfeito para estudar e para levar o programa para outro computador.

## 6. Outros bancos de dados (opcional)

A Advak também fala com MySQL, SQL Server, MongoDB, Redis e outros 15 bancos, sempre com os mesmos
comandos — o guia completo, com links de download, o `pip install` de cada driver e um exemplo para cada
banco, está em [BANCOS_DE_DADOS.md](BANCOS_DE_DADOS.md). Para ver quais drivers já estão instalados:

```cmd
advak bancos
```

## 7. Instalação no Linux

> **Não testado em um Linux real.** Os passos usam os comandos padrão do Ubuntu/Debian; em Fedora use `dnf`
> no lugar de `apt`.

```bash
# 1. Python, pip, Tkinter (janelas) e Git
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk git

# 2. Baixar a Advak
git clone https://github.com/ArimateiaGomes/advak-language.git
cd advak-language

# 3. Ambiente isolado (recomendado; obrigatório em versões novas do Ubuntu/Debian)
python3 -m venv venv
source venv/bin/activate
pip install ttkbootstrap psycopg2-binary pyserial paho-mqtt pyinstaller

# 4. Testar
python3 advak.py --versao
python3 advak.py sintaxe_completa.dk
```

Para digitar só `advak`, crie um apelido (troque o caminho pelo da sua pasta):

```bash
echo "alias advak='$(pwd)/venv/bin/python $(pwd)/advak.py'" >> ~/.bashrc
source ~/.bashrc
advak --versao
```

**PostgreSQL no Linux:** veja <https://www.postgresql.org/download/linux/>. No Ubuntu/Debian:

```bash
sudo apt install postgresql
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'sua_senha';"
cp .env.exemplo .env
nano .env        # coloque a mesma senha em ADVAK_DB_PASS
advak run primeiros_passos.dk --db
```

Os arquivos `.bat` e `.ps1` são só para Windows.

## 8. Problemas comuns

### `python` não é reconhecido

Mensagem do Windows: *"'python' não é reconhecido como um comando interno ou externo, um programa operável
ou um arquivo em lotes."*

Causa: o Python foi instalado sem marcar **Add python.exe to PATH**, ou o Prompt de Comando foi aberto antes
de instalar.

1. Feche o Prompt de Comando e abra outro. Teste `python --version`.
2. Teste `py --version` (o "Python Launcher" do Windows). Se funcionar, use `py` no lugar de `python`
   (`py -m pip install ...`, `py advak.py ...`).
3. Se nenhum funcionar, rode o instalador do Python de novo e escolha **Modify**; clique em **Next** até a
   tela *Advanced Options*, marque **Add Python to environment variables** e clique em **Install**.

### `advak` não é reconhecido / o PATH não atualizou

- Você abriu o Prompt **antes** de rodar o `INSTALAR.bat`: feche e abra de novo.
- Rode o `INSTALAR.bat` outra vez e leia as mensagens. Se aparecer *"Nao foi possivel modificar o PATH"*,
  adicione a mão: tecle `Win + R`, digite `sysdm.cpl`, aba **Avançado** → **Variáveis de Ambiente** →
  em *Variáveis do usuário* edite **Path** → **Novo** → cole a pasta da Advak → OK em tudo.
- Enquanto isso, use o caminho direto: `python C:\advak-language\advak.py programa.dk`.

### Erro do `psycopg2` (`ModuleNotFoundError: No module named 'psycopg2'`)

A biblioteca de PostgreSQL não está instalada **neste** Python:

```cmd
pip install psycopg2-binary
```

Se continuar, você tem mais de um Python. Use o `pip` do mesmo Python que executa a Advak:
`python -m pip install psycopg2-binary`.

### Senha do banco errada (ou ausente)

Dois sintomas reais, que significam a mesma coisa:

```text
❌ Erro: connection to server at "localhost" (::1), port 5432 failed: fe_sendauth: no password supplied
```
→ a senha **não foi lida**: o arquivo `.env` não existe, está em outra pasta ou `ADVAK_DB_PASS` está vazio.

```text
❌ Erro: Não foi possível conectar ao PostgreSQL: senha, usuário ou banco incorretos? (O servidor respondeu com
uma mensagem em português que o Python não conseguiu ler — isso quase sempre significa senha errada.) ...
```
→ **senha (ou usuário) errada**. Com o PostgreSQL em português, o servidor responde "falha na autenticação"
com acentos, e o Python não consegue ler a mensagem. A Advak reconhece essa situação e mostra o aviso acima.
(Em versões anteriores à 5.2 aparecia o erro enigmático `'utf-8' codec can't decode byte 0xe7 ...
UnicodeDecodeError`, que significava a mesma coisa.) Não é problema de acentos nos seus arquivos.

O que fazer:

1. Confira o `.env`: `ADVAK_DB_PASS=senha` — **sem aspas, sem espaço** no começo ou no fim, e o arquivo na
   mesma pasta de onde você roda a Advak (ou numa pasta acima).
2. Teste a mesma senha no **pgAdmin**. Se o pgAdmin também recusar, a senha é outra: redefina no *SQL
   Shell (psql)* (já logado como administrador): `ALTER USER postgres PASSWORD 'nova_senha';`
3. Se aparecer `Connection refused` ("conexão recusada"), o serviço do PostgreSQL não está rodando: tecle
   `Win + R`, digite `services.msc`, ache **postgresql-x64-NN**, clique com o botão direito → **Iniciar**.
   Confira também se a porta no `.env` é a mesma que você escolheu na instalação (5432).

### Acentos estranhos no Prompt de Comando

Sintoma: `OlÃ¡`, `?` ou quadradinhos no lugar de `á`, `ç`. A Advak já manda texto em UTF-8, mas o Prompt
de Comando antigo usa outra tabela de caracteres. Digite antes de rodar o programa:

```cmd
chcp 65001
```

e use uma fonte que mostre acentos (clique com o botão direito na barra da janela → **Propriedades** →
**Fonte** → **Consolas** ou **Lucida Console**). A solução mais simples é usar o **Windows Terminal** (loja
da Microsoft), que já vem bem configurado. Os arquivos `.dk` devem estar salvos em **UTF-8** (o Bloco de
Notas atual já salva assim; o "UTF-8 com BOM" também funciona).

### `ttkbootstrap` ou janelas não abrem

`pip install ttkbootstrap`. No Linux instale também o Tkinter: `sudo apt install python3-tk`.

### O `pip` não funciona

Use `python -m pip install nome-do-pacote`. Se aparecer erro de certificado ou de rede, veja se a internet
da escola/empresa bloqueia o `pypi.org`.

### Ainda com dúvida?

Rode `advak --ajuda`, leia o [README](../README.md) ou abra uma *issue* em
<https://github.com/ArimateiaGomes/advak-language>.
