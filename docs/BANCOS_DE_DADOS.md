# Bancos de dados na Advak

A Advak fala com **23 bancos de dados** usando **os mesmos comandos em português**. Para trocar de banco,
você muda só a linha de conexão.

> ## Leia isto primeiro — o que foi testado de verdade
> * **SQLite**: testado **de verdade** (programa `.dk` real, 6 de 6 testes, e o exemplo deste guia é executado).
> * **PostgreSQL**: o modo antigo da Advak (`advak run programa.dk --db`, com `banco.criar_banco`, `banco.tabela`...)
>   funciona com um PostgreSQL real — foi verificado rodando `primeiros_passos.dk`. O **conector novo por URL**
>   (`banco.conectar("postgresql://...")`) ainda é **simulado**.
> * **Outros 20 bancos**: testados apenas com um *driver simulado* (mock): isso confere o SQL e os comandos
>   que a Advak gera, mas **não prova** que o servidor real aceita tudo.
> * **DuckDB**: **em teste / instável no Windows** (veja [a seção dele](#duckdb)).
>
> Se você usar um desses bancos, rode `testes/bancos_externos.dk` ([como](#testar-com-o-seu-banco)) e nos
> conte o resultado. Os exemplos de cada banco abaixo foram conferidos quanto à **sintaxe** e aos **nomes dos
> comandos** de cada banco, mas só o do SQLite foi **executado**.

## Resumo dos 23 bancos

| Banco | Tipo | Driver (`pip install ...`) | Esquema da URL | Teste |
|---|---|---|---|---|
| [SQLite](#sqlite) | Relacional | já vem com o Python | `sqlite:///arquivo.db` | **Real** |
| [PostgreSQL](#postgresql) | Relacional | `psycopg2-binary` | `postgresql://` | Antigo: real. Conector novo: simulado |
| [MySQL](#mysql) | Relacional | `pymysql` | `mysql://` | Simulado |
| [MariaDB](#mariadb) | Relacional | `pymysql` | `mariadb://` | Simulado |
| [SQL Server](#sql-server) | Relacional | `pymssql` | `mssql://` ou `sqlserver://` | Simulado |
| [Oracle](#oracle) | Relacional | `oracledb` | `oracle://` | Simulado |
| [Firebird](#firebird) | Relacional | `firebird-driver` | `firebird://` | Simulado |
| [IBM Db2](#ibm-db2) | Relacional | `ibm_db` | `db2://` | Simulado |
| [CockroachDB](#cockroachdb) | Relacional (distribuído) | `psycopg2-binary` | `cockroachdb://` | Simulado |
| [TimescaleDB](#timescaledb) | Séries temporais | `psycopg2-binary` | `timescaledb://` | Simulado |
| [DuckDB](#duckdb) | Analítico | `duckdb` | `duckdb:///arquivo.duckdb` | **Em teste / instável no Windows** |
| [ClickHouse](#clickhouse) | Analítico | `clickhouse-connect` | `clickhouse://` | Simulado |
| [Snowflake](#snowflake) | Analítico (nuvem) | `snowflake-connector-python` | `snowflake://` | Simulado |
| [Google BigQuery](#google-bigquery) | Analítico (nuvem) | `google-cloud-bigquery` | `bigquery://` | Simulado |
| [Cassandra](#cassandra) | Colunar distribuído | `cassandra-driver` | `cassandra://` | Simulado |
| [MongoDB](#mongodb) | Documentos | `pymongo` | `mongodb://` | Simulado |
| [CouchDB](#couchdb) | Documentos | `couchdb` | `couchdb://` | Simulado |
| [Google Firestore](#google-firestore) | Documentos (nuvem) | `google-cloud-firestore` | `firestore://` | Simulado |
| [Amazon DynamoDB](#amazon-dynamodb) | Documentos (nuvem) | `boto3` | `dynamodb://` | Simulado |
| [Elasticsearch](#elasticsearch) | Busca | `elasticsearch` | `elasticsearch://` | Simulado |
| [Redis](#redis) | Chave-valor e cache | `redis` | `redis://` | Simulado |
| [Neo4j](#neo4j) | Grafos | `neo4j` | `neo4j://` ou `bolt://` | Simulado |
| [InfluxDB](#influxdb) | Séries temporais | `influxdb-client` | `influxdb://` | Simulado |

**O que "simulado" quer dizer.** `testes/test_conectores_mock.py` (89 testes) troca cada driver por um falso
e confere o SQL gerado, a troca de marcadores (`%s` e `$1`), as aspas de cada banco, a paginação, a leitura da
URL, a proteção contra nomes perigosos e as mensagens de erro. Nenhum servidor real é contatado.

`advak bancos` mostra essa tabela no terminal, e se cada driver já está instalado.

## Qual banco escolher?

| Eu quero... | Use |
|---|---|
| Estudar, ou fazer um app pequeno **sem instalar nada** | **SQLite** (um arquivo só) |
| Um sistema com vários usuários ao mesmo tempo (escola, loja) | **PostgreSQL** (recomendado) ou MySQL/MariaDB |
| Conectar ao banco que a empresa já usa | SQL Server, Oracle, Firebird ou Db2, conforme o caso |
| Sistemas de PDV/frente de caixa antigos | **Firebird** ou SQL Server |
| Guardar dados "soltos", cada registro diferente do outro | **MongoDB** (ou CouchDB / Firestore / DynamoDB na nuvem) |
| Procurar texto em muitos documentos (como uma busca do Google) | **Elasticsearch** |
| Guardar sessões, contadores e resultados que se repetem (cache) | **Redis** |
| Mapear relações (amizades, rotas, quem conhece quem) | **Neo4j** |
| Guardar leituras de sensores ao longo do tempo | **InfluxDB** ou **TimescaleDB** |
| Analisar milhões de linhas | **ClickHouse**, **BigQuery** ou **Snowflake** |
| Um banco que cresce em vários servidores | **CockroachDB** ou **Cassandra** |

Na dúvida, comece pelo **SQLite**. Mudar depois é só trocar a linha de conexão.

---

## Como conectar

```advak
// 1) por URL
seja db = banco.conectar("mysql://usuario:senha@localhost:3306/loja")

// 2) por dados separados
seja db = banco.conectar("mysql", host="localhost", usuario="root", senha="x", banco="loja")

// 3) pelo arquivo .env (recomendado: a senha não fica no código)
seja db = banco.conectar("mysql")        // lê ADVAK_MYSQL_URL do .env
```

No `.env` (copie o `.env.exemplo`), uma linha por banco: `ADVAK_<BANCO>_URL=...`. Se a senha tiver `@ : / #`,
troque por `%40 %3A %2F %23`. O `.env` fica só no seu computador e **nunca vai para o GitHub**. A senha nunca
aparece quando você imprime a conexão.

Se o driver não estiver instalado, a Advak diz o comando exato, por exemplo:
`O driver do MySQL não está instalado. Instale com:  pip install pymysql`.

> **Compatibilidade:** `banco.conectar()` e `banco.conectar("nome_do_banco")` continuam usando o PostgreSQL de
> sempre (o `banco.sql`, `banco.inserir` etc. do modo antigo não mudaram). Para o PostgreSQL pelo conector novo,
> use a URL (`postgresql://...`) ou dados separados.

## Comandos dos bancos SQL

Valem para SQLite, PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, Firebird, Db2, CockroachDB, TimescaleDB,
DuckDB, ClickHouse, Snowflake, BigQuery e Cassandra (com as diferenças da seção seguinte).

```advak
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "decimal"})
db.inserir("produtos", {nome: "Caneta", preco: 2.5})            // devolve o registro
db.inserir_varios("produtos", [{nome: "A", preco: 1}, {nome: "B", preco: 2}])
db.buscar("produtos").onde("preco > %s", 1).ordenar("nome").limite(10).executar()
db.buscar("produtos").pagina(2, 10).executar()                  // página 2, 10 por página
db.buscar_id("produtos", 1)
db.atualizar("produtos", {preco: 3}).onde("id = %s", 1).executar()   // → linhas afetadas
db.deletar("produtos").onde("id = %s", 1).executar()                 // → linhas afetadas
db.sql("SELECT * FROM produtos WHERE id = $1", [1])             // SELECT → lista; outros → linhas afetadas
db.contar("produtos")
db.listar_tabelas()    db.descrever_tabela("produtos")    db.apagar_tabela("produtos")
db.iniciar()  db.confirmar()  db.reverter()                     // transações
db.fechar()
```

Tipos de coluna: `autonum`, `inteiro`, `numero`, `decimal`, `flutuante`, `grande`, `texto`, `varchar`, `char`,
`data`, `hora`, `datahora`, `timestamp`, `booleano`, `json`, `bytes`, `ref outra_tabela`. Modificadores:
`obrigatorio`, `unico`, `padrao valor`, `indice`. Cada banco recebe o tipo certo (`SERIAL` no PostgreSQL,
`AUTO_INCREMENT` no MySQL, `IDENTITY` no SQL Server...).

**Segurança:** nomes de tabela e campo só aceitam letras, números e `_`; os **valores** sempre vão como
parâmetros (`%s` ou `$1`) — nunca junte o texto digitado por um usuário dentro do SQL. Não misture `%s` e
`$1` na mesma consulta. Erros viram mensagens como `Erro no MySQL: ...` e podem ser tratados com
`tentar { } pegar (e) { }`.

### Diferenças entre os bancos SQL

| Banco | O que muda |
|---|---|
| Oracle, Firebird, Db2 | Nomes sem aspas (o banco guarda em MAIÚSCULAS); a Advak devolve os nomes em minúsculas. Não existe `CREATE TABLE IF NOT EXISTS`: a Advak confere antes. `inserir` devolve os dados enviados, sem o `id` gerado (use `buscar` para ler). |
| CockroachDB, TimescaleDB | Iguais ao PostgreSQL. O TimescaleDB ganha `db.criar_hipertabela("sensores", "tempo")`. |
| SQL Server | Paginação com `TOP` e `OFFSET/FETCH`; `texto` vira `NVARCHAR(MAX)`. |
| ClickHouse | Sem transações. `atualizar`/`deletar` são *mutações* assíncronas e retornam 0. `autonum` vira UUID. Sem `unico`/`obrigatorio`. |
| Snowflake | `unico` não é imposto pelo Snowflake. |
| BigQuery | Sem transações, sem `unico`; `autonum` vira UUID em texto. Escrita (DML) exige faturamento ativo. |
| Cassandra | Sem transações e sem `OFFSET`. Filtros fora da chave usam `ALLOW FILTERING` (lento em tabelas grandes). Sem `unico`/`obrigatorio`/`padrao`. |

## Bancos de documentos (MongoDB, CouchDB, Firestore, DynamoDB, Elasticsearch)

Mesmos nomes (`inserir`, `inserir_varios`, `buscar`, `buscar_id`, `atualizar`, `deletar`, `contar`, `tabela`,
`listar_tabelas`, `apagar_tabela`). A "tabela" é uma **coleção** (no CouchDB, um banco; no Elasticsearch, um
índice; no DynamoDB, uma tabela com chave `id` em texto). O `id` volta como texto. Condições simples como nos
bancos SQL: `campo = %s`, `!=`, `>`, `>=`, `<`, `<=`, ligadas por `AND`, ou um dicionário:
`.onde({cidade: "Recife"})`. `LIKE` e `OR` não são aceitos. `db.sql(...)` não existe nesses bancos.

---

# Cada banco

Cada seção segue o mesmo roteiro: o que é, quando usar, onde baixar, driver, conexão, exemplo e se foi testado.

### SQLite

**O que é:** um banco de dados que cabe em **um único arquivo**. Não precisa instalar servidor nem senha.
**Quando usar:** estudar, programas pequenos, apps que levam os dados junto (um arquivo `.db`).
**Instalação:** já vem com o Python. Site oficial: <https://www.sqlite.org/download.html>.
**Driver:** nenhum (`sqlite3` faz parte do Python).
**Conexão (`.env`):** `ADVAK_SQLITE_URL=sqlite:///dados/loja.db` (use `sqlite:///:memory:` para um banco só na memória).
**Exemplo:**
```advak
seja db = banco.conectar("sqlite")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
db.inserir("clientes", {nome: "Bia", cidade: "Teresina"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** **Sim.** `testes/bancos_sqlite.dk` (6 de 6) e este exemplo é executado no teste dos guias.

### PostgreSQL

**O que é:** um banco de dados "grande", gratuito e muito usado em empresas. Funciona como servidor.
**Quando usar:** sistemas com vários usuários ao mesmo tempo, que precisam de segurança e desempenho.
**Instalação:** <https://www.postgresql.org/download/> (Windows: <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>;
Linux: <https://www.postgresql.org/download/linux/>). Programa visual: <https://www.pgadmin.org/download/>.
Passo a passo no [guia de instalação](INSTALACAO.md#5-postgresql-opcional).
**Driver:** `pip install psycopg2-binary`
**Conexão (`.env`):** `ADVAK_POSTGRES_URL=postgresql://postgres:senha@localhost:5432/loja`
**Exemplo:**
```advak
seja db = banco.conectar("postgresql")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").ordenar("nome").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** **Em parte.** O modo antigo (`advak run programa.dk --db`) foi executado contra um
PostgreSQL real. O conector novo por URL usa o mesmo driver, mas só tem teste **simulado**.

### MySQL

**O que é:** outro banco de dados muito popular na web (sites, lojas virtuais). Funciona como servidor.
**Quando usar:** hospedagens de sites e sistemas que já usam MySQL.
**Instalação:** <https://dev.mysql.com/downloads/mysql/> (o site pode recusar acesso automático; abra no navegador).
**Driver:** `pip install pymysql`
**Conexão (`.env`):** `ADVAK_MYSQL_URL=mysql://usuario:senha@localhost:3306/loja`
**Exemplo:**
```advak
seja db = banco.conectar("mysql")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### MariaDB

**O que é:** uma "cópia" livre e compatível do MySQL, criada pelos mesmos autores originais.
**Quando usar:** quando você quer algo parecido com o MySQL, 100% de código aberto (vem em muitas distribuições Linux).
**Instalação:** <https://mariadb.org/download/>
**Driver:** `pip install pymysql`
**Conexão (`.env`):** `ADVAK_MARIADB_URL=mariadb://usuario:senha@localhost:3306/loja`
**Exemplo:**
```advak
seja db = banco.conectar("mariadb")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
seja todos = db.buscar("clientes").executar()
imprimir(todos.tamanho, "cliente(s)")
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### SQL Server

**O que é:** o banco de dados da Microsoft, muito usado em empresas e em sistemas de loja (PDV).
**Quando usar:** quando o sistema da empresa já usa SQL Server.
**Instalação:** <https://www.microsoft.com/sql-server/sql-server-downloads> (a edição *Express* é gratuita).
**Driver:** `pip install pymssql`
**Conexão (`.env`):** `ADVAK_MSSQL_URL=mssql://sa:senha@localhost:1433/loja` (também vale `sqlserver://`)
**Exemplo:**
```advak
seja db = banco.conectar("mssql")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").ordenar("nome").limite(10).executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### Oracle

**O que é:** banco de dados comercial de grande porte, comum em bancos, governo e grandes empresas.
**Quando usar:** quando a empresa já usa Oracle (existe uma edição gratuita, a *Oracle Database Free*).
**Instalação:** <https://www.oracle.com/database/free/> (downloads em <https://www.oracle.com/database/free/get-started/>).
**Driver:** `pip install oracledb`
**Conexão (`.env`):** `ADVAK_ORACLE_URL=oracle://usuario:senha@localhost:1521/FREEPDB1` (o último pedaço é o *nome do serviço*:
`FREEPDB1` na edição Free, `XEPDB1` no Express 21c).
**Exemplo:**
```advak
seja db = banco.conectar("oracle")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").pagina(1, 10).executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Oracle 12c ou mais novo para paginar; `inserir` não devolve o `id`.)

### Firebird

**O que é:** banco de dados livre e leve, muito comum em sistemas de loja e PDV no Brasil.
**Quando usar:** para ler/gravar em sistemas comerciais antigos que usam Firebird.
**Instalação:** <https://firebirdsql.org/en/downloads/> (use a versão 3 ou mais nova).
**Driver:** `pip install firebird-driver`
**Conexão (`.env`):** `ADVAK_FIREBIRD_URL=firebird://SYSDBA:masterkey@localhost:3050/C:/dados/loja.fdb` (o final é o caminho do arquivo do banco no servidor).
**Exemplo:**
```advak
seja db = banco.conectar("firebird")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### IBM Db2

**O que é:** banco de dados da IBM, usado em grandes empresas e bancos.
**Quando usar:** quando a empresa já usa Db2.
**Instalação:** página oficial do produto: <https://www.ibm.com/products/db2> (há uma edição *Community* gratuita).
**Driver:** `pip install ibm_db`
**Conexão (`.env`):** `ADVAK_DB2_URL=db2://db2inst1:senha@localhost:50000/LOJA`
**Exemplo:**
```advak
seja db = banco.conectar("db2")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
seja n = db.contar("clientes")
imprimir(n, "cliente(s)")
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### CockroachDB

**O que é:** um banco de dados que fala "a língua do PostgreSQL", mas espalha os dados por vários servidores e continua funcionando se um cair.
**Quando usar:** sistemas que precisam ficar sempre no ar e crescer.
**Instalação:** <https://www.cockroachlabs.com/docs/stable/install-cockroachdb>
**Driver:** `pip install psycopg2-binary` (o mesmo do PostgreSQL)
**Conexão (`.env`):** `ADVAK_COCKROACHDB_URL=cockroachdb://root@localhost:26257/loja?sslmode=disable` (em produção use `sslmode=require`).
**Exemplo:**
```advak
seja db = banco.conectar("cockroachdb")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
seja todos = db.buscar("clientes").ordenar("nome").executar()
imprimir(todos.tamanho)
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### TimescaleDB

**O que é:** o PostgreSQL com um "turbo" para dados que chegam com data e hora (sensores, medições).
**Quando usar:** guardar muitas leituras ao longo do tempo e consultar por período, sem sair do PostgreSQL.
**Instalação:** <https://docs.timescale.com/self-hosted/latest/install/> (a empresa mudou de nome; a página redireciona).
**Driver:** `pip install psycopg2-binary`
**Conexão (`.env`):** `ADVAK_TIMESCALEDB_URL=timescaledb://postgres:senha@localhost:5432/sensores`
**Exemplo:**
```advak
seja db = banco.conectar("timescaledb")
db.tabela("leituras", {tempo: "datahora obrigatorio", sensor: "texto", valor: "decimal"})
db.criar_hipertabela("leituras", "tempo")
db.inserir("leituras", {tempo: "2024-12-25 10:00:00", sensor: "sala", valor: 22.5})
para (l em db.buscar("leituras").ordenar("tempo", "DESC").limite(5).executar()) {
    imprimir(l.sensor, l.valor)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### DuckDB

**O que é:** um banco "analítico" que roda dentro do programa (como o SQLite), muito rápido para somar e agrupar muitos dados.
**Quando usar:** análises de planilhas/arquivos grandes em um só computador.
**Instalação:** <https://duckdb.org/docs/installation>
**Driver:** `pip install duckdb`
**Conexão (`.env`):** `ADVAK_DUCKDB_URL=duckdb:///dados/analise.duckdb`
**Exemplo:**
```advak
seja db = banco.conectar("duckdb")
db.tabela("vendas", {id: "autonum", produto: "texto", total: "decimal"})
db.inserir("vendas", {produto: "Caneta", total: 12.5})
para (v em db.sql("SELECT produto, SUM(total) AS soma FROM vendas GROUP BY produto")) {
    imprimir(v.produto, v.soma)
}
db.fechar()
```
**Testado de verdade?** **Não — em teste / instável no Windows.** Com `duckdb 1.5.6`, Python 3.13 e Windows 10, um comando
com **parâmetro de texto** (por exemplo `INSERT ... VALUES (?)` com `'a'`) executado **dentro de uma thread** travou para
sempre, e uma vez o `python.exe` fechou com erro de memória. O `testar` e o servidor web da Advak rodam em threads,
então o DuckDB pode travar nesses casos. Em um script simples, na thread principal, o conector funcionou nos testes
manuais, mas **não há teste automático aprovado** (ele foi desativado em `testes/_desativados/`). **Recomendação:** no
Windows, prefira o SQLite por enquanto.

### ClickHouse

**O que é:** banco de dados feito para analisar bilhões de linhas muito rápido (relatórios, estatísticas, logs).
**Quando usar:** análises pesadas em dados que só crescem (e quase nunca mudam).
**Instalação:** <https://clickhouse.com/docs/en/install>
**Driver:** `pip install clickhouse-connect`
**Conexão (`.env`):** `ADVAK_CLICKHOUSE_URL=clickhouse://default:senha@localhost:8123/loja`
**Exemplo:**
```advak
seja db = banco.conectar("clickhouse")
db.tabela("eventos", {id: "autonum", nome: "texto", qtd: "inteiro"})
db.inserir("eventos", {nome: "visita", qtd: 3})
para (e em db.buscar("eventos").onde("qtd > %s", 1).executar()) {
    imprimir(e.nome, e.qtd)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Sem transações; `atualizar`/`deletar` não informam quantas linhas mudaram.)

### Snowflake

**O que é:** banco de dados de análise **na nuvem** (serviço pago, com período de teste).
**Quando usar:** empresas que já têm seus dados no Snowflake.
**Instalação:** não se instala: crie uma conta em <https://www.snowflake.com/> (teste gratuito).
**Driver:** `pip install snowflake-connector-python`
**Conexão (`.env`):** `ADVAK_SNOWFLAKE_URL=snowflake://usuario:senha@MINHA_CONTA/MEU_BANCO/PUBLIC?warehouse=MEU_WH`
**Exemplo:**
```advak
seja db = banco.conectar("snowflake")
db.tabela("vendas", {id: "autonum", produto: "texto", total: "decimal"})
db.inserir("vendas", {produto: "Caneta", total: 12.5})
seja todas = db.buscar("vendas").executar()
imprimir(todas.tamanho)
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### Google BigQuery

**O que é:** banco de dados de análise **na nuvem** do Google (cobra por consulta; existe uso gratuito limitado).
**Quando usar:** análises sobre grandes conjuntos de dados, principalmente se já estão no Google Cloud.
**Instalação:** não se instala: <https://cloud.google.com/bigquery>. Você cria um projeto, um *dataset* e uma chave de acesso (arquivo `.json`).
**Driver:** `pip install google-cloud-bigquery`
**Conexão (`.env`):** `ADVAK_BIGQUERY_URL=bigquery://meu-projeto/meu_dataset?credenciais=chave.json`
**Exemplo:**
```advak
seja db = banco.conectar("bigquery")
db.tabela("vendas", {id: "autonum", produto: "texto", total: "decimal"})
db.inserir("vendas", {produto: "Caneta", total: 12.5})
para (v em db.buscar("vendas").executar()) {
    imprimir(v.produto, v.total)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Escrever dados exige faturamento ativo; não funciona no modo gratuito *sandbox*.)

### Cassandra

**O que é:** banco de dados distribuído (vários servidores) feito para gravar muita coisa muito rápido.
**Quando usar:** sistemas enormes, com muitas gravações (mensagens, históricos).
**Instalação:** <https://cassandra.apache.org/_/download.html>
**Driver:** `pip install cassandra-driver`
**Conexão (`.env`):** `ADVAK_CASSANDRA_URL=cassandra://cassandra:cassandra@localhost:9042/loja` (o último pedaço é o *keyspace*, que você cria antes).
**Exemplo:**
```advak
seja db = banco.conectar("cassandra")
db.tabela("clientes", {id: "autonum", nome: "texto", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
seja todos = db.buscar("clientes").executar()
imprimir(todos.tamanho)
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Sem transações e sem `OFFSET`; o `id` com `autonum` é um UUID.)

### MongoDB

**O que é:** banco de dados de **documentos**: cada registro é como um "cartão" que pode ter campos diferentes dos outros.
**Quando usar:** dados que mudam de formato, catálogos, cadastros flexíveis.
**Instalação:** <https://www.mongodb.com/try/download/community>
**Driver:** `pip install pymongo`
**Conexão (`.env`):** `ADVAK_MONGODB_URL=mongodb://usuario:senha@localhost:27017/loja`
**Exemplo:**
```advak
seja db = banco.conectar("mongodb")
seja ana = db.inserir("clientes", {nome: "Ana", cidade: "Picos", idade: 20})
db.inserir("clientes", {nome: "Bia", cidade: "Teresina"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
imprimir(db.buscar_id("clientes", ana.id).nome)
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (A coleção é criada sozinha; `db.comando({...})` roda comandos nativos.)

### CouchDB

**O que é:** banco de dados de documentos que conversa pela web (HTTP) e é fácil de instalar.
**Quando usar:** apps simples de documentos e sincronização.
**Instalação:** <https://couchdb.apache.org/#download>
**Driver:** `pip install couchdb`
**Conexão (`.env`):** `ADVAK_COUCHDB_URL=couchdb://admin:senha@localhost:5984` (cada "tabela" é um banco do CouchDB, com nome em minúsculas).
**Exemplo:**
```advak
seja db = banco.conectar("couchdb")
db.tabela("clientes")
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado.

### Google Firestore

**O que é:** banco de documentos **na nuvem** do Google/Firebase (tem uso gratuito limitado).
**Quando usar:** apps de celular e web que já usam o Firebase.
**Instalação:** não se instala: <https://firebase.google.com/docs/firestore>. Você cria um projeto e uma chave de acesso (`.json`).
**Driver:** `pip install google-cloud-firestore`
**Conexão (`.env`):** `ADVAK_FIRESTORE_URL=firestore://meu-projeto?credenciais=chave.json`
**Exemplo:**
```advak
seja db = banco.conectar("firestore")
db.inserir("tarefas", {titulo: "Estudar", feita: falso})
para (t em db.buscar("tarefas").onde("feita = %s", falso).executar()) {
    imprimir(t.id, t.titulo)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (A Advak lê a coleção inteira e filtra no seu computador: bom para coleções pequenas; em coleções grandes aumenta o custo de leituras.)

### Amazon DynamoDB

**O que é:** banco de dados de documentos **na nuvem** da Amazon (AWS), pago por uso.
**Quando usar:** apps na AWS que precisam de um banco simples e que não pare.
**Instalação:** não se instala: <https://aws.amazon.com/dynamodb/>. Para estudar no seu computador existe a versão local: <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html>.
**Driver:** `pip install boto3`
**Conexão (`.env`):** `ADVAK_DYNAMODB_URL=dynamodb://CHAVE:SEGREDO@us-east-1` (para a versão local: `...@us-east-1?endpoint=http://localhost:8000`).
**Exemplo:**
```advak
seja db = banco.conectar("dynamodb")
db.tabela("clientes")
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (As consultas fazem *Scan*: leem a tabela inteira, o que custa.)

### Elasticsearch

**O que é:** um "Google" para os seus dados: procura textos muito rápido.
**Quando usar:** campo de busca em site/sistema com muitos textos.
**Instalação:** <https://www.elastic.co/downloads/elasticsearch>
**Driver:** `pip install elasticsearch`
**Conexão (`.env`):** `ADVAK_ELASTICSEARCH_URL=elasticsearch://elastic:senha@localhost:9200` (acrescente `?https=1` se o servidor usa HTTPS).
**Exemplo:**
```advak
seja db = banco.conectar("elasticsearch")
db.inserir("produtos", {nome: "Caneta azul", preco: 2.5})
db.inserir("produtos", {nome: "Caderno", preco: 15})
para (p em db.buscar("produtos").onde("preco > %s", 5).executar()) {
    imprimir(p.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Até 10.000 documentos por consulta.)

### Redis

**O que é:** um banco que guarda **chave e valor** na memória, extremamente rápido.
**Quando usar:** cache (guardar um resultado para não calcular de novo), sessões de login, contadores.
**Instalação:** <https://redis.io/downloads/> (no Windows, o jeito mais simples é usar o WSL ou o Docker).
**Driver:** `pip install redis`
**Conexão (`.env`):** `ADVAK_REDIS_URL=redis://:senha@localhost:6379/0`
**Exemplo:**
```advak
seja cache = banco.conectar("redis")
cache.definir("visitas", 0)
cache.incrementar("visitas")
cache.definir("usuario:1", {nome: "Ana"}, 60)       // some depois de 60 segundos
imprimir(cache.obter("visitas"))
imprimir(cache.obter_json("usuario:1").nome)
cache.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Outros comandos: `existe`, `chaves`, `expirar`, `excluir`, listas, conjuntos, `hash_definir`, `publicar`.)

### Neo4j

**O que é:** banco de dados de **grafos**: guarda coisas (nós) e as ligações entre elas (relações).
**Quando usar:** redes de amizade, rotas, recomendações, "quem conhece quem".
**Instalação:** <https://neo4j.com/download/>
**Driver:** `pip install neo4j`
**Conexão (`.env`):** `ADVAK_NEO4J_URL=neo4j://neo4j:senha@localhost:7687/neo4j` (também vale `bolt://`; Neo4j 5 ou mais novo).
**Exemplo:**
```advak
seja db = banco.conectar("neo4j")
seja ana = db.inserir("Pessoa", {nome: "Ana", idade: 20})
seja bia = db.inserir("Pessoa", {nome: "Bia", idade: 30})
db.relacionar(ana.id, "AMIGA_DE", bia.id, {desde: 2020})
para (p em db.buscar("Pessoa").onde("idade > %s", 25).executar()) {
    imprimir(p.nome)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (`db.consulta("MATCH ...")` roda Cypher puro, sempre com parâmetros.)

### InfluxDB

**O que é:** banco feito para **séries temporais**: valores que chegam com data e hora (temperatura, consumo).
**Quando usar:** painéis de sensores e monitoramento.
**Instalação:** <https://www.influxdata.com/downloads/> (versão 2.x).
**Driver:** `pip install influxdb-client`
**Conexão (`.env`):** `ADVAK_INFLUXDB_URL=influxdb://:MEU_TOKEN@localhost:8086/meu_bucket?org=minha_org`
**Exemplo:**
```advak
seja db = banco.conectar("influxdb")
db.inserir("temperatura", {valor: 21.5}, {sala: "A"})       // campos, depois etiquetas (tags)
para (p em db.buscar("temperatura").desde("-1h").limite(5).executar()) {
    imprimir(p.tempo, p.valor)
}
db.fechar()
```
**Testado de verdade?** Não — apenas simulado. (Pontos de tempo não são atualizáveis: grave outro ponto. `db.consulta('from(bucket: ...)')` roda Flux puro.)

---

## Testar com o seu banco

1. Crie um banco **só para teste**.
2. No `.env`, defina por exemplo `ADVAK_TESTE_MYSQL_URL=mysql://root:senha@localhost:3306/teste_advak`
   (o nome é `ADVAK_TESTE_<BANCO>_URL`; veja a lista no topo de `testes/bancos_externos.dk`).
3. Rode `advak testes/bancos_externos.dk`. O que não estiver configurado aparece como `PULADO`.
4. Conte para nós o resultado (principalmente se algo falhar): é assim que um banco passa de "simulado" para "testado".
