# Bancos de dados na Advak

A Advak fala com **23 bancos de dados** usando **os mesmos comandos em português**. Troque o banco
mudando só a linha de conexão.

> **Leia isto primeiro — o que foi testado de verdade.** Só o **SQLite** foi testado contra um banco
> real. Os outros 21 foram testados apenas com um *driver simulado* (mock): isso confere o SQL e os
> comandos que a Advak gera, mas **não prova** que o servidor real aceita tudo. O **DuckDB** está
> **em teste / instável no Windows** (veja a seção própria). Se você usar um desses bancos, rode
> `testes/bancos_externos.dk` (seção "Testar com o seu banco") e nos conte o resultado.

## Resumo dos 23 bancos

| Banco | Tipo | Driver (`pip install ...`) | Esquema da URL | Teste |
|---|---|---|---|---|
| SQLite | Relacional | já vem com o Python | `sqlite:///arquivo.db` | **Real** (`testes/bancos_sqlite.dk`, 6/6) |
| PostgreSQL | Relacional | `psycopg2-binary` | `postgresql://` | Simulado |
| MySQL | Relacional | `pymysql` | `mysql://` | Simulado |
| MariaDB | Relacional | `pymysql` | `mariadb://` | Simulado |
| SQL Server | Relacional | `pymssql` | `mssql://` ou `sqlserver://` | Simulado |
| Oracle | Relacional | `oracledb` | `oracle://` | Simulado |
| Firebird | Relacional | `firebird-driver` | `firebird://` | Simulado |
| IBM Db2 | Relacional | `ibm_db` | `db2://` | Simulado |
| CockroachDB | Relacional | `psycopg2-binary` | `cockroachdb://` | Simulado |
| TimescaleDB | Séries temporais | `psycopg2-binary` | `timescaledb://` | Simulado |
| DuckDB | Analítico | `duckdb` | `duckdb:///arquivo.duckdb` | **Em teste / instável no Windows** |
| ClickHouse | Analítico | `clickhouse-connect` | `clickhouse://` | Simulado |
| Snowflake | Analítico | `snowflake-connector-python` | `snowflake://` | Simulado |
| Google BigQuery | Analítico | `google-cloud-bigquery` | `bigquery://` | Simulado |
| Cassandra | Colunar distribuído | `cassandra-driver` | `cassandra://` | Simulado |
| MongoDB | Documentos | `pymongo` | `mongodb://` | Simulado |
| CouchDB | Documentos | `couchdb` | `couchdb://` | Simulado |
| Google Firestore | Documentos | `google-cloud-firestore` | `firestore://` | Simulado |
| Amazon DynamoDB | Documentos | `boto3` | `dynamodb://` | Simulado |
| Elasticsearch | Busca | `elasticsearch` | `elasticsearch://` | Simulado |
| Redis | Chave-valor e cache | `redis` | `redis://` | Simulado |
| Neo4j | Grafos | `neo4j` | `neo4j://` ou `bolt://` | Simulado |
| InfluxDB | Séries temporais | `influxdb-client` | `influxdb://` | Simulado |

**O que "simulado" quer dizer.** `testes/test_conectores_mock.py` (89 testes) troca cada driver por um
falso e confere o SQL gerado, a troca de marcadores (`%s` e `$1`), as aspas de cada banco, a paginação
(`LIMIT`, `TOP`, `OFFSET ... FETCH`, `FIRST/SKIP`, `ALLOW FILTERING`), a leitura da URL, a proteção contra
nomes perigosos e as mensagens de erro. Nenhum servidor real é contatado.

Veja também a lista no terminal: `advak bancos`.

## Conectar

```
// 1) por URL
seja db = banco.conectar("mysql://usuario:senha@localhost:3306/loja")

// 2) por dados separados
seja db = banco.conectar("mysql", host="localhost", usuario="root", senha="x", banco="loja")

// 3) pelo .env (recomendado: a senha não fica no código)
seja db = banco.conectar("mysql")        // lê ADVAK_MYSQL_URL
```

Se a senha tiver `@ : / #`, troque por `%40 %3A %2F %23`. Copie `.env.exemplo` para `.env` e preencha —
o `.env` nunca vai para o GitHub. A senha nunca aparece quando você imprime a conexão.

> Compatibilidade: `banco.conectar()` e `banco.conectar("nome_do_banco")` continuam usando o
> PostgreSQL de sempre (o `banco.sql`, `banco.inserir` etc. antigos não mudaram). Para o
> PostgreSQL pelo conector novo use a URL (`postgresql://...`) ou dados separados.

Se o driver não estiver instalado, a Advak diz o comando exato, por exemplo:
`O driver do MySQL não está instalado. Instale com:  pip install pymysql`.

## Comandos dos bancos SQL

Valem para SQLite, PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, Firebird, Db2, CockroachDB,
TimescaleDB, DuckDB, ClickHouse, Snowflake, BigQuery e Cassandra (com as diferenças da tabela abaixo).

```
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

Tipos de coluna: `autonum`, `inteiro`, `numero`, `decimal`, `flutuante`, `grande`, `texto`, `varchar`,
`char`, `data`, `hora`, `datahora`, `timestamp`, `booleano`, `json`, `bytes`, `ref outra_tabela`.
Modificadores: `obrigatorio`, `unico`, `padrao valor`, `indice`. Cada banco recebe o tipo certo.

Segurança: nomes de tabela e campo só aceitam letras, números e `_`; os **valores** sempre vão como
parâmetros (use `%s` ou `$1`, nunca junte texto de usuário dentro do SQL). Não misture `%s` e `$1` na
mesma consulta. Erros viram mensagens como `Erro no MySQL: ...` e podem ser tratados com
`tentar { } capturar (e) { }`.

### Diferenças entre os bancos SQL

| Banco | O que muda |
|---|---|
| Oracle, Firebird, Db2 | Nomes sem aspas (o banco guarda em MAIÚSCULAS); a Advak devolve os nomes em minúsculas. Não existe `CREATE TABLE IF NOT EXISTS`: a Advak confere antes. `inserir` devolve os dados enviados (sem o `id` gerado — use `buscar` para ler). Oracle precisa do 12c+ para paginar; use `?servico=` ou o nome do serviço na URL (`oracle://u:s@host/XEPDB1`). Firebird: versão 3+ (BOOLEAN e IDENTITY). |
| CockroachDB | Igual ao PostgreSQL. Use `?sslmode=require` quando o cluster exigir. |
| TimescaleDB | Igual ao PostgreSQL, mais `db.criar_hipertabela("sensores", "tempo")`. |
| SQL Server | Paginação com `TOP` e `OFFSET/FETCH`; `texto` vira `NVARCHAR(MAX)`. |
| ClickHouse | Sem transações. `atualizar`/`deletar` são *mutações* assíncronas e retornam 0 (o banco não informa as linhas). `autonum` vira UUID. Sem `unico`/`obrigatorio` (colunas já são não-nulas). |
| Snowflake | URL `snowflake://usuario:senha@CONTA/BANCO/ESQUEMA?warehouse=WH&role=PAPEL`. Restrições `unico` não são impostas pelo Snowflake. |
| BigQuery | URL `bigquery://PROJETO/DATASET?credenciais=chave.json` (ou `GOOGLE_APPLICATION_CREDENTIALS`). Sem transações, sem `unico`; `autonum` vira UUID em texto. Comandos de escrita (DML) exigem faturamento ativo (não funcionam no *sandbox* gratuito). |
| Cassandra | URL `cassandra://usuario:senha@host:9042/KEYSPACE`. Sem transações e sem `OFFSET` (`pagina` > 1 dá erro). Filtros fora da chave usam `ALLOW FILTERING` (lento em tabelas grandes). A primeira coluna `id` vira a chave primária; `autonum` = UUID gerado pela Advak. Sem `unico`/`obrigatorio`/`padrao`. |

## Bancos de documentos: MongoDB, CouchDB, Firestore, DynamoDB, Elasticsearch

Mesmos nomes (`inserir`, `inserir_varios`, `buscar`, `buscar_id`, `atualizar`, `deletar`, `contar`,
`tabela`, `listar_tabelas`, `apagar_tabela`); a "tabela" é uma **coleção** (no CouchDB, um banco; no
Elasticsearch, um índice; no DynamoDB, uma tabela com chave `id` em texto). O `id` volta como texto.
Condições simples como nos bancos SQL: `campo = %s`, `!=`, `>`, `>=`, `<`, `<=`, ligadas por `AND`
(ou passe um dicionário: `.onde({cidade: "Recife"})`). `LIKE`/`OR` não são aceitos. `db.sql(...)` não existe.

| Banco | URL e particularidades |
|---|---|
| MongoDB | `mongodb://usuario:senha@host:27017/banco`. Filtros, ordem e página rodam no servidor. Comando nativo: `db.comando({...})`. |
| CouchDB | `couchdb://usuario:senha@host:5984` (`?https=1`). Nomes de banco em minúsculas. Filtros vão como seletor Mango. |
| Firestore | `firestore://PROJETO?credenciais=chave.json`. **Filtra no cliente**: lê a coleção inteira (custo de leituras). Bom para coleções pequenas. |
| DynamoDB | `dynamodb://CHAVE:SEGREDO@us-east-1` (ou sem credenciais, usando a configuração da AWS); DynamoDB local: `?endpoint=http://localhost:8000`. **Consultas fazem Scan** (leem a tabela inteira = custo). Números decimais são guardados como `Decimal` e voltam como número. |
| Elasticsearch | `elasticsearch://usuario:senha@host:9200` (`?https=1`, `?verificar_certificado=0`). Até 10.000 documentos por consulta; filtros de igualdade e faixa vão ao servidor, o resto é refinado na Advak. |

## Redis

`db.definir("chave", valor, expira)`, `db.obter("chave")`, `db.obter_json("chave")`, `db.excluir(...)`,
`db.existe`, `db.chaves("padrao*")`, `db.expirar`, `db.ttl`, `db.incrementar`, `db.decrementar`,
`db.lista_adicionar/lista_ler`, `db.conjunto_adicionar/conjunto_ler`, `db.hash_definir/hash_ler`,
`db.publicar`, `db.limpar()` (apaga o banco Redis inteiro — cuidado).

## Neo4j (grafos)

`neo4j://usuario:senha@host:7687/banco` (Neo4j 5+). A "tabela" é o **rótulo** do nó.

```
seja ana = db.inserir("Pessoa", {nome: "Ana", idade: 20})
seja bia = db.inserir("Pessoa", {nome: "Bia", idade: 30})
db.relacionar(ana.id, "AMIGA_DE", bia.id, {desde: 2020})
db.buscar("Pessoa").onde("idade > %s", 25).ordenar("nome").executar()
db.consulta("MATCH (a)-[:AMIGA_DE]->(b) WHERE a.nome = $n RETURN b.nome AS nome", {n: "Ana"})
db.atualizar("Pessoa", {idade: 31}).onde("nome = %s", "Bia").executar()
db.deletar("Pessoa").onde("nome = %s", "Ana").executar()      // apaga também as relações
db.tabela("Pessoa", {email: "texto unico"})                    // cria restrição de unicidade
```

Valores sempre vão como parâmetros (`$n`), nunca dentro do texto Cypher.

## InfluxDB (séries temporais)

`influxdb://:TOKEN@host:8086/BUCKET?org=MINHA_ORG` (`?https=1`). A "tabela" é a **medição**.
Pontos de tempo não são atualizáveis (grave outro ponto com o mesmo tempo e tags).

```
db.inserir("temperatura", {valor: 21.5}, {sala: "A"})            // campos, depois tags
db.buscar("temperatura").desde("-1h").onde("valor > %s", 20).ordenar("tempo", "DESC").limite(10).executar()
db.consulta('from(bucket: "sensores") |> range(start: -1h)')     // Flux puro
db.apagar_dados("temperatura", "2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z")
db.listar_tabelas()
```

## DuckDB — em teste / instável no Windows

**Problema encontrado:** com `duckdb 1.5.6`, Python 3.13 e Windows 10, um comando com **parâmetro de
texto** (por exemplo `INSERT ... VALUES (?)` com `'a'`) executado **dentro de uma thread** trava para
sempre; sem parâmetro ou com parâmetro numérico funciona. Em uma das execuções o `python.exe` chegou a
fechar com erro de memória. O `testar` e o servidor web da Advak rodam em threads, então o DuckDB
pode travar nesses casos. Em um script simples, na thread principal, o conector funcionou nos testes
manuais (tabela, inserir, buscar, atualizar, transação), mas **não** há teste automático aprovado.

O teste automático foi desativado (`testes/_desativados/bancos_duckdb.dk.desativado`) para não travar
ninguém. Recomendação: para análise de dados no Windows, prefira o SQLite por enquanto.

## Testar com o seu banco

1. Crie um banco **só para teste**.
2. No `.env`, defina por exemplo `ADVAK_TESTE_MYSQL_URL=mysql://root:senha@localhost:3306/teste_advak`
   (o nome é `ADVAK_TESTE_<BANCO>_URL`; veja a lista no topo de `testes/bancos_externos.dk`).
3. Rode `advak testes/bancos_externos.dk`. O que não estiver configurado aparece como `PULADO`.

## Qual banco escolher?

- **Estou começando / app pequeno:** SQLite (um arquivo, nada para instalar).
- **App com vários usuários:** PostgreSQL (recomendado) ou MySQL/MariaDB.
- **Empresa que já usa produtos Microsoft ou Oracle:** SQL Server ou Oracle.
- **Sistemas de PDV antigos:** Firebird ou SQL Server.
- **Dados sem formato fixo:** MongoDB (ou CouchDB / Firestore / DynamoDB na nuvem).
- **Busca em texto:** Elasticsearch.
- **Cache, sessões, contadores rápidos:** Redis.
- **Relações entre coisas (redes sociais, rotas):** Neo4j.
- **Leituras de sensores ao longo do tempo:** InfluxDB ou TimescaleDB.
- **Análise de grandes volumes:** ClickHouse, BigQuery ou Snowflake.
