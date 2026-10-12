# Bancos de dados na Advak

A Advak fala com vários bancos de dados usando **os mesmos comandos em português**. Troque o banco
mudando só a linha de conexão.

> **Estado desta versão (Grupo 1):** SQLite, PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB e
> Redis estão prontos; DuckDB está **em teste / instável no Windows**. Os demais bancos
> (Oracle, Firebird, Db2, CockroachDB, TimescaleDB, ClickHouse, Snowflake, BigQuery, CouchDB,
> Firestore, DynamoDB, Elasticsearch, Neo4j, InfluxDB e Cassandra) entram nos próximos grupos.

## Resumo e o que foi testado de verdade

| Banco | Tipo | Driver (`pip install ...`) | Teste |
|---|---|---|---|
| SQLite | Relacional | já vem com o Python | **Real**: `testes/bancos_sqlite.dk` (6/6) |
| PostgreSQL | Relacional | `psycopg2-binary` | Simulado (mock) — ainda não rodado contra um servidor |
| MySQL | Relacional | `pymysql` | Simulado (mock) |
| MariaDB | Relacional | `pymysql` | Simulado (mock) |
| SQL Server | Relacional | `pymssql` | Simulado (mock) |
| MongoDB | Documentos (NoSQL) | `pymongo` | Simulado (mock) |
| Redis | Chave-valor e cache | `redis` | Simulado (mock) |
| DuckDB | Analítico | `duckdb` | **Em teste / instável no Windows** (veja abaixo) |

**O que "simulado" quer dizer.** `testes/test_conectores_mock.py` (31 testes) troca o driver por um
falso e confere o SQL gerado, a troca de marcadores (`%s` e `$1`), as aspas de cada banco, a paginação
(`LIMIT`, `TOP`, `OFFSET ... FETCH`), a leitura da URL e as mensagens de erro. Isso **não prova** que
o servidor real aceita o comando. Se você tiver um desses bancos instalado, rode
`testes/bancos_externos.dk` (veja "Testar com o seu banco") e nos conte o resultado.

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

Esquemas aceitos: `sqlite:///arquivo.db`, `postgresql://`, `mysql://`, `mariadb://`,
`mssql://` (ou `sqlserver://`), `mongodb://`, `redis://`, `duckdb:///arquivo.duckdb`.
Se a senha tiver `@ : / #`, troque por `%40 %3A %2F %23`. Copie `.env.exemplo` para `.env`
e preencha — o `.env` nunca vai para o GitHub.

> Compatibilidade: `banco.conectar()` e `banco.conectar("nome_do_banco")` continuam usando o
> PostgreSQL de sempre (o `banco.sql`, `banco.inserir` etc. antigos não mudaram). Para o
> PostgreSQL pelo conector novo use a URL (`postgresql://...`) ou dados separados.

Se o driver não estiver instalado, a Advak diz o comando exato, por exemplo:
`O driver do MySQL não está instalado. Instale com:  pip install pymysql`.

## Comandos (bancos SQL)

```
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "decimal"})
db.inserir("produtos", {nome: "Caneta", preco: 2.5})            // devolve o registro (com id)
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
Modificadores: `obrigatorio`, `unico`, `padrao valor`, `indice`. Cada banco recebe o tipo certo
(`SERIAL` no PostgreSQL, `AUTO_INCREMENT` no MySQL, `IDENTITY` no SQL Server...).

Segurança: nomes de tabela e campo só aceitam letras, números e `_`; os **valores** sempre vão como
parâmetros (use `%s` ou `$1`, nunca junte texto de usuário dentro do SQL).

Erros viram mensagens como `Erro no MySQL: ...` e podem ser tratados com `tentar { } capturar (e) { }`.

## MongoDB

Mesmos nomes (`inserir`, `buscar`, `atualizar`, `deletar`, `contar`); a "tabela" é uma **coleção**,
criada sozinha. O `id` volta como texto. Condições simples funcionam como nos bancos SQL
(`campo = %s`, `!=`, `>`, `>=`, `<`, `<=`, ligadas por `AND`) ou você passa um dicionário:
`db.buscar("clientes").onde({cidade: "Recife"}).executar()`. Comando nativo: `db.comando({...})`.
`db.sql(...)` não existe no MongoDB.

## Redis

`db.definir("chave", valor, expira)`, `db.obter("chave")`, `db.obter_json("chave")`, `db.excluir(...)`,
`db.existe`, `db.chaves("padrao*")`, `db.expirar`, `db.ttl`, `db.incrementar`, `db.decrementar`,
`db.lista_adicionar/lista_ler`, `db.conjunto_adicionar/conjunto_ler`, `db.hash_definir/hash_ler`,
`db.publicar`, `db.limpar()` (apaga o banco Redis inteiro — cuidado).

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
   (também `..._POSTGRES_URL`, `..._MARIADB_URL`, `..._MSSQL_URL`, `..._MONGODB_URL`, `..._REDIS_URL`).
3. Rode `advak testes/bancos_externos.dk`. O que não estiver configurado aparece como `PULADO`.

## Qual banco escolher?

- **Estou começando / app pequeno:** SQLite (um arquivo, nada para instalar).
- **App com vários usuários:** PostgreSQL (recomendado) ou MySQL/MariaDB.
- **Empresa que já usa produtos Microsoft:** SQL Server.
- **Dados sem formato fixo:** MongoDB.
- **Cache, sessões, contadores rápidos:** Redis.
