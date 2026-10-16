# Proposta: criação automática ou manual de banco e tabelas

> **Status: implementado em SQLite e PostgreSQL (modos, `db.preparar`, `db.diferencas`, `db.adicionar_coluna`, mensagens do PostgreSQL), conforme as decisões da seção 10. Continua só descrito, sem implementação: instalar servidor (seção 7), a palavra `modelo`, outros bancos e o caminho legado. O ramo "criar o banco PostgreSQL sozinho" foi testado só com driver falso.** A seção 1 descreve o que a
> Advak faz hoje (testado de verdade); o resto é desenho.

## 1. O que a Advak já faz hoje

Testes feitos em 2026-10-15, com o conector novo (`banco.conectar("sqlite:///...")`), salvo indicação.

| Pergunta | Resultado |
|---|---|
| SQLite: o arquivo `.db` é criado sozinho? | **Sim**, inclusive as pastas (`sqlite:///novo/sub/loja.db` criou `novo/sub/`). Quem faz isso é o próprio `sqlite3.connect`, mais um `makedirs`. |
| SQLite: as tabelas são criadas sozinhas? | **Não.** `db.inserir("clientes", ...)` sem tabela dá `Erro no SQLite: no such table: clientes`. O mesmo vale para `db.buscar`. |
| `db.tabela(...)` cria se não existe? | **Sim** (`CREATE TABLE IF NOT EXISTS`). Chamar duas vezes não dá erro. |
| Tabela já existe com colunas diferentes? | **Nada acontece, mas a mensagem mente.** `db.tabela("clientes", {id, nome, email, idade})` sobre uma tabela só com `id, nome` devolve `✅ Tabela 'clientes' criada`; `descrever_tabela` continua mostrando só `id` e `nome`, e `inserir` com `email` falha com `table clientes has no column named email`. |
| Comando manual para criar tabela? | **Sim:** `db.tabela` / `db.criar_tabela`, `db.apagar_tabela`, `db.listar_tabelas`, `db.existe_tabela`, `db.descrever_tabela`. |
| Comando manual para adicionar coluna / migrar / criar banco no conector novo? | **Não existem.** `db.adicionar_coluna`, `db.migrar` e `db.criar_banco` dão `Não é possível acessar '...' em ConectorSQLite`. |
| PostgreSQL: o banco é criado sozinho? | **Não, precisa existir.** `banco.conectar("postgres", ...)` conecta no banco informado (ou em `postgres`). Existe `banco.criar_banco(nome)`, mas só no caminho **legado** (`banco.conectar()` sem URL/tipo), que usa `advak_db.py`. |
| Esse caminho legado tem algo de automático? | **Sim:** `banco.auto_setup(nome, tabelas)` cria o banco e as tabelas que faltam; `banco.migrar(tabela, campos)` cria a tabela ou **só adiciona** colunas novas. Nunca apaga. É o único código parecido com o que esta proposta quer, e só vale para PostgreSQL legado. Não testado nesta sonda para não criar nada no servidor. |
| `servidor.usar_banco("app.db")` (web) | Cria o SQLite sozinho e `servidor.criar_tabela` usa `CREATE TABLE IF NOT EXISTS`, com os mesmos limites: coluna nova não é adicionada. |
| Servidor parado | Hoje a mensagem é a do driver, em **inglês** e duplicada (IPv6 e IPv4): `connection to server at "localhost" (::1), port 59999 failed: Connection refused ... Is the server running...`. |
| Senha/banco inválidos no PostgreSQL | Mensagem em português e útil, mas generalista: "senha, usuário ou banco incorretos?". Não diferencia "banco não existe" de "senha errada". |
| Driver não instalado (ex.: MySQL) | Mensagem clara em português: `O driver do MySQL não está instalado. Instale com: pip install pymysql`. |

Resumo: o que falta é (a) um jeito de declarar o esquema esperado, (b) criar o que falta de forma uniforme em
todos os bancos, (c) acrescentar colunas novas, e (d) mensagens melhores quando o servidor não está lá.

## 2. Modo por projeto

Três modos:

- **`manual`**: a linguagem não cria nada sozinha (exceto o arquivo SQLite, que o SQLite cria por conta própria,
  comportamento de hoje). O desenvolvedor chama `db.criar_banco`, `db.tabela` etc.
- **`automatico`**: ao conectar, a linguagem cria banco, tabelas e colunas novas do modelo (seção 3). Nunca apaga.
- **`perguntar`**: ao conectar, compara o modelo com o banco, mostra o que falta e pergunta `[s/N]` antes de criar.
  Sem terminal interativo (servidor web, tarefa agendada) vira `manual` e diz isso claramente.

**Onde se configura** (a primeira que existir vence): parâmetro na conexão
(`banco.conectar("sqlite:///loja.db", modo="automatico")`), depois `ADVAK_BANCO_MODO=automatico` no `.env`,
depois o padrão.

**Padrão proposto: `manual`.** É o comportamento de hoje, não surpreende quem já tem programas e evita mexer em
banco de produção sem querer. Quem quer conforto liga `automatico` de propósito. *(Decisão sua; ver seção 8.)*

## 3. Modelo declarativo em português

Um bloco que descreve o esquema esperado, usando a mesma linguagem de tipos que `db.tabela` já entende
(`autonum`, `texto obrigatorio`, `inteiro padrao 0`, `ref clientes`...):

```
modelo loja {
    tabela clientes {
        id: autonum
        nome: texto obrigatorio
        email: texto unico
    }
    tabela pedidos {
        id: autonum
        cliente: ref clientes
        total: decimal padrao 0
    }
}

seja db = banco.conectar("sqlite:///loja.db", modelo=loja)
```

Alternativa sem sintaxe nova, mais barata: o modelo é um mapa comum, `seja loja = {"clientes": {"id": "autonum", ...}}`,
passado a `db.preparar(loja)`. Comece por essa e só crie a palavra `modelo` se o mapa se mostrar incômodo
(cada palavra reservada nova, como já aconteceu com `tela`, tem custo).

## 4. Comandos

**`db.preparar()`** (ou `db.preparar(modelo)`): cria o que falta, **nunca apaga nem altera tipos**, devolve um
relatório em português do que foi feito (`banco criado`, `tabela pedidos criada`, `coluna clientes.email adicionada`)
e `nada a fazer` quando está tudo em dia. Em `automatico` é chamado ao conectar; em `perguntar` mostra o relatório
prévio e só roda depois do sim; em `manual` só roda se o desenvolvedor chamar.

**Comandos manuais equivalentes** (valem em todos os bancos SQL, hoje só existem em parte):

| Comando | Situação hoje |
|---|---|
| `db.criar_banco(nome)` | só no PostgreSQL legado |
| `db.tabela(nome, campos)` | existe |
| `db.adicionar_coluna(tabela, campo, definicao)` | só no legado |
| `db.migrar(tabela, campos)` | só no legado |
| `db.existe_tabela`, `db.listar_tabelas`, `db.descrever_tabela` | existem |
| `db.diferencas(modelo)`: lista o que falta, sem criar nada | novo |

**Correção independente da proposta:** `db.tabela` sobre tabela existente com colunas diferentes não deveria dizer
"criada". Sugestão: `ℹ️ Tabela 'clientes' já existe` e, se o modelo difere, um aviso apontando `db.diferencas` /
`db.migrar`.

## 5. Colunas novas (migração simples), por modo

Só **adicionar** coluna. Renomear, mudar tipo e remover ficam fora (seção 9).

- **`manual`**: nada muda sozinho. O erro `no such column`/`no column named email` ganha uma dica:
  "a coluna 'email' não existe em 'clientes'; use `db.adicionar_coluna(...)`".
- **`automatico`**: `preparar` adiciona. Cuidado: coluna nova `obrigatorio` sem `padrao` em tabela com dados não
  pode ser adicionada (o banco recusa); nesse caso a Advak **não adiciona** e explica o que fazer.
- **`perguntar`**: mostra a lista de colunas a adicionar e pergunta antes.

Em todos: colunas que existem no banco e não no modelo são **ignoradas**, nunca removidas.

## 6. Servidor ausente ou que não responde

Mensagem única, em português, no lugar da do driver, diferenciando as causas:

1. **Driver não instalado:** já é bom hoje (`pip install ...`); manter.
2. **Servidor não responde** (conexão recusada / tempo esgotado): "Não consegui falar com o PostgreSQL em
   localhost:5432. Ele está instalado e ligado? No Windows, veja o serviço `postgresql-x64-NN` em Serviços. Para
   instalar, use `advak instalar-banco postgres`." (uma mensagem só, não duas por IPv6/IPv4).
3. **Senha ou usuário errados:** manter a mensagem atual.
4. **Banco não existe:** "O banco 'loja' não existe neste servidor. Em modo `automatico` ele seria criado;
   em `manual`, use `db.criar_banco('loja')` conectado ao banco `postgres`."

Só o item 4 depende do modo; os outros são iguais em todos.

## 7. Instalar o servidor: comando explícito e com confirmação

Proposta: `advak instalar-banco <tipo>` (nunca chamado por `conectar`, `preparar` nem por modo algum).

- Mostra **exatamente** o que vai rodar (ex.: `winget install PostgreSQL.PostgreSQL.17`), de onde vem, o tamanho
  aproximado e que exige permissão de administrador.
- Pede digitar `sim` por extenso; qualquer outra coisa cancela. Não existe `--sim`/`--silencioso` na primeira
  versão. Sem terminal interativo, recusa.
- Antes de tudo, verifica se já está instalado (serviço, porta) e para.
- Não define senha, não cria usuário, não mexe no `.env` sem mostrar e perguntar.
- Se não houver gerenciador de pacotes, **não improvisa**: mostra o link oficial e as instruções.
- Começar por um ou dois bancos (PostgreSQL; MySQL/MariaDB se pedirem). Bancos testados pouco (ver aviso no
  README) não entram.

## 8. Decisões que dependem de você

1. **Padrão do modo:** `manual` (proposto, igual a hoje) ou `perguntar`?
2. **Modelo:** só o mapa + `db.preparar(mapa)`, ou também a palavra nova `modelo { ... }`?
3. **Onde configurar:** parâmetro `modo=` na conexão + `.env`, como proposto, ou também um arquivo de projeto?
4. **SQLite em `manual`:** manter a criação do arquivo (compatível, proposto) ou exigir comando explícito também?
5. **Caminho legado do PostgreSQL** (`banco.conectar()` sem tipo, com `auto_setup`/`migrar`): unificar no conector
   novo e manter o legado só como apelido, ou deixar como está?
6. **Colunas `obrigatorio` sem `padrao`** em tabela com dados: recusar e explicar (proposto) ou preencher com um
   valor neutro?
7. **Instalar servidor:** vale incluir agora? Em quais bancos e com qual gerenciador (winget no Windows)?
8. **Consertar já** a mensagem enganosa "Tabela criada" de `db.tabela`, mesmo antes de qualquer outra coisa?

## 9. Fora do escopo

- Apagar tabelas, colunas ou bancos automaticamente, em qualquer modo.
- Renomear tabelas/colunas, mudar tipo de coluna, migrações com dados (copiar, transformar).
- Histórico/versionamento de migrações (estilo Alembic/Django).
- Bancos NoSQL e de nuvem (MongoDB, Firestore, DynamoDB, BigQuery...): `preparar` valeria só para os bancos SQL.
- Instalação silenciosa de qualquer coisa, configuração de senha/usuário do servidor, backup.
- Garantia de comportamento em MySQL, SQL Server, Firebird etc., que ainda não foram testados em servidor real.

## 10. Decisões do autor (2026-10-15)

Respostas às perguntas da seção 8 (a numeração abaixo é a da seção 8):

1. **Padrão do modo:** `manual`, igual a hoje.
2. **Modelo:** só o mapa comum + `db.preparar(mapa)` por enquanto. A palavra `modelo` fica para depois.
3. **Onde configurar:** como proposto (parâmetro `modo=` na conexão, depois `ADVAK_BANCO_MODO` no `.env`, depois o padrão).
4. **SQLite em `manual`:** manter a criação do arquivo, como proposto.
5. **Caminho legado do PostgreSQL:** deixar como está por enquanto.
6. **Coluna `obrigatorio` sem `padrao` em tabela com dados:** recusar e explicar, como proposto.
7. **Instalar servidor:** fica **apenas descrito** na seção 7; não será implementado agora.
8. **Mensagem enganosa de `db.tabela`:** **corrigir logo**, em um commit pequeno e separado, depois do commit deste documento.

Nada além do item 8 está autorizado a ser implementado.

