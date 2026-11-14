> This is a translation of [README.md](README.md). The Portuguese version is the reference and may be newer. The documents linked from `docs/` are in Portuguese. This translation currently covers only up to the 'First program' section; for the rest, see the Portuguese README.md.

# Advak Language

**A programming language in Portuguese, made to teach and to build real systems.**

Advak is an interpreted language, written in Python, with keywords in Portuguese (`seja`, `se`, `senão`, `para`, `função`, `classe`...). It already comes with PostgreSQL database, web server, graphical interface and built-in tests, so the student goes from "Hello, world" to a system with registration and a screen without having to learn another language along the way.

```advak
seja nome = entrada("Qual é o seu nome? ")
imprimir(`Olá, ${nome}! Bem-vindo ao Advak.`)
```

> Current version: **5.2.0** · Author: **Prof. Arimatéa Gomes** — CETI Silvestre Rocha (Ensino Médio de Tempo Integral, a full-time high school in Brazil), Arraial-PI

## 📚 Learn to program with Advak

**Never programmed? Start here:** [docs/curso/README.md](docs/curso/README.md) — a course of 24 short lessons,
from the first `imprimir` to a complete system, made for high-school and EJA students. All the
course examples were run with Advak and the output shown is the real one. The course **does not depend on the
internet, on an API key or on AI**.

| I want to... | Go to |
|---|---|
| Install Advak (Windows or Linux), with PostgreSQL | [docs/INSTALACAO.md](docs/INSTALACAO.md) |
| Learn from scratch | [docs/curso/README.md](docs/curso/README.md) |
| See complete everyday applications, explained | [docs/GUIA_PRATICO.md](docs/GUIA_PRATICO.md) |
| Connect to one of the 23 databases | [docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md) |
| Use AI (optional) | [docs/IA.md](docs/IA.md) and [docs/DOCUMENTOS.md](docs/DOCUMENTOS.md) |
| See what changed | [CHANGELOG.md](CHANGELOG.md) |

---

## Influences

The Advak programming language was influenced by **Python**, **C**, **Prolog**, **Haskell** and **Java**:

| Language | What Advak inherited |
|---|---|
| **Python** | Simplicity and easy reading; it is the language in which the Advak interpreter was written |
| **C** | Syntax with braces `{ }`, `para` loop with a counter, operators (`++`, `+=`, `&&`, `\|\|`) and features such as structures and enumerations |
| **Prolog** | Logic programming with facts, rules and queries |
| **Haskell** | Functional style: lambdas, pure functions, immutability, function composition and the pipeline operator `\|>` |
| **Java** | Object orientation with `classe`, `construtor`, `herda`, `isso` and `novo` |

---

## Table of contents

1. [Influences](#influences)
1. [What's new in version 5.2](#whats-new-in-version-52)
1. [Installation](#installation)
2. [How to run](#how-to-run)
3. [First program](#first-program)
4. [Language guide](#language-guide)
   - [Variables and types](#variables-and-types)
   - [Operators](#operators)
   - [Strings and template strings](#strings-and-template-strings)
   - [Conditionals](#conditionals)
   - [Loops](#loops)
   - [Functions and lambdas](#functions-and-lambdas)
   - [Lists](#lists)
   - [Maps (objects)](#maps-objects)
   - [Classes and inheritance](#classes-and-inheritance)
   - [Combinar (match)](#combinar-match)
   - [Error handling](#error-handling)
   - [Modules](#modules)
5. [Standard library](#standard-library)
   - [Artificial intelligence (optional)](#artificial-intelligence-optional)
6. [Database](#database) (PostgreSQL and [23 supported databases](#supported-databases))
7. [Web server](#web-server)
8. [Graphical interface](#graphical-interface)
9. [Unit tests](#unit-tests)
10. [English syntax](#english-syntax)
11. [Command-line tools](#command-line-tools)
12. [Ready-made examples](#ready-made-examples)
13. [Project structure](#project-structure)
14. [Keyword table](#keyword-table)

---

## What's new in version 5.2

| New feature | Example |
|---|---|
| **Ranges** | `para (i em 1..=10 passo 2) { }` — `1..10` does not include the end, `1..=10` does |
| **List comprehensions** | `[x * 2 para x em lista se x > 0]` |
| **Interpolation with formatting** | `` `Total: ${preco:moeda}` `` → `R$ 1.500,50`; `` `${d:dd/mm/aaaa}` `` |
| **Optional typing** | `seja idade: inteiro = 17`, `função somar(a: numero, b: numero) -> numero { ... }` |
| **23 databases** | `banco.conectar("mysql://usuario:senha@localhost/loja")` — same API for all |
| **AI (optional)** | `seja assistente = ia.conectar("ollama")` — 8 providers, loaded only if you use it |
| **Documents** | `documento.ler("relatorio.pdf")` and `assistente.perguntar("Resuma", {anexos: ["a.pdf"]})` |
| **Fixed tools** | `advak formatar` (`+=`, `=>`, multi-line strings), `--verificar` and the Python transpiler (negative numbers) |
| **Fixes** | `caso` with a condition, `importar` with `;`, `servidor.rota`, `enum`, generators, `inicio(...)` as a constructor, `lista.primeiro`, `.dk` files with the Notepad BOM |

See the details of each one in the sections below, in the [CHANGELOG](CHANGELOG.md) and in
[docs/RECURSOS_5_2.md](docs/RECURSOS_5_2.md).

> **AI is optional.** Advak works 100% without it: no internet, no API key and no cost.

---

## Installation

> Complete step-by-step guide for beginners (Windows and Linux, PostgreSQL, common problems):
> **[docs/INSTALACAO.md](docs/INSTALACAO.md)**.

### Requirements

- **Python 3** — download it at [python.org](https://python.org/downloads) and check **"Add Python to PATH"** during installation.
- **PostgreSQL** (optional) — only needed for the database features. Without it, Advak uses SQLite automatically.
  - Windows: [PostgreSQL installer (EDB)](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
  - Official page with all systems: [postgresql.org/download](https://www.postgresql.org/download/)
  - Linux: [postgresql.org/download/linux](https://www.postgresql.org/download/linux/)
  - Visual program to browse the database (optional): [pgAdmin](https://www.pgadmin.org/download/)

  > During the PostgreSQL installation, write down the **password** you create for the `postgres` user and keep port **5432**. That password goes in the `.env` file.

### Step by step (Windows)

```cmd
git clone https://github.com/ArimateiaGomes/advak-language.git
cd advak-language
pip install ttkbootstrap psycopg2-binary pyserial paho-mqtt pyinstaller
INSTALAR.bat
```

`INSTALAR.bat` adds the Advak folder to the Windows PATH. **Close and reopen the terminal** and the `advak` command will work from any folder.

### Optional dependencies

| Package | What it is for |
|---|---|
| `psycopg2-binary` | Connection to PostgreSQL |
| `ttkbootstrap` | Modern look for the graphical interface |
| `pyinstaller` | Compile `.dk` programs into `.exe` |
| `pyserial` | Communication with Arduino over the serial port |
| `paho-mqtt` | Communication with IoT devices (ESP32) |

The drivers for the other databases (MySQL, SQL Server, MongoDB, Redis...) and for reading documents (PDF, Word...)
are also optional and installed only when you use them: see [docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md)
and [docs/DOCUMENTOS.md](docs/DOCUMENTOS.md).

### Configuring PostgreSQL

Copy the example file and put your password in it:

```cmd
copy .env.exemplo .env
notepad .env
```

```ini
ADVAK_DB_HOST=localhost
ADVAK_DB_PORT=5432
ADVAK_DB_USER=postgres
ADVAK_DB_PASS=sua_senha_aqui
```

You can also configure it with the wizard: `CONFIGURAR_BANCO.bat`.

> The `.env` file stays only on your computer. It is in `.gitignore` and never goes to GitHub.

---

## How to run

Language files use the **`.dk`** extension.

| Command | What it does |
|---|---|
| `advak programa.dk` | Runs a program |
| `advak run programa.dk --db` | Runs already connected to PostgreSQL |
| `advak` | Opens interactive mode (REPL) |
| `advak check programa.dk` | Checks the syntax without running |

Without `INSTALAR.bat`, use Python directly:

```cmd
python advak.py run programa.dk
```

Another option is to drag a `.dk` file onto `rodar.bat`.

---

## First program

Create a file `ola.dk`:

```advak
// Meu primeiro programa em Advak
seja nome = entrada("Digite seu nome: ")
seja idade = numero(entrada("Digite sua idade: "))

imprimir(`Olá, ${nome}!`)

se (idade >= 18) {
    imprimir("Você é maior de idade.")
} senão {
    imprimir(`Faltam ${18 - idade} anos para a maioridade.`)
}
```

Run:

```cmd
advak ola.dk
```

> The semicolon at the end of a line is **optional**. Both styles work.

---
