"""
Testes SIMULADOS (mock) dos conectores PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB e Redis.

Não existe servidor real aqui: os drivers (psycopg2, pymysql, pymssql, pymongo, redis) são
trocados por versões falsas que só registram o que receberam. Estes testes provam a conversão
de marcadores, a geração do SQL de cada dialeto e o roteamento — NÃO provam que o banco real
aceita o comando. Para isso use testes/bancos_externos.dk com um banco configurado.

Rodar:  python -I testes/test_conectores_mock.py
"""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import advak_conectores as c   # noqa: E402


# ── DB-API falso ─────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self, conn):
        self.conn, self.description, self.rowcount, self.lastrowid = conn, None, 1, 7
        self._rows = []

    def execute(self, sql, params=None):
        self.conn.log.append((sql, params))
        if self.conn.proximo is not None:
            cols, rows = self.conn.proximo
            self.description, self._rows = [(k,) for k in cols], rows
            self.conn.proximo = None
        else:
            self.description, self._rows = None, []

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeConn:
    def __init__(self, **kw):
        self.kw, self.log, self.proximo, self.commits, self.rollbacks = kw, [], None, 0, 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


def instalar_driver_falso(nome_modulo, funcao='connect'):
    mod = types.ModuleType(nome_modulo)
    setattr(mod, funcao, lambda *a, **kw: FakeConn(**kw))
    sys.modules[nome_modulo] = mod
    return mod


def remover_driver(nome_modulo):
    sys.modules.pop(nome_modulo, None)


class TesteUrlEResolucao(unittest.TestCase):
    def test_url_mysql_com_senha_especial(self):
        tipo, p = c.resolver_conexao("mysql://ana:p%40ss%3A1@db.exemplo.com:3307/loja")
        self.assertEqual(tipo, "mysql")
        self.assertEqual((p['host'], p['porta'], p['usuario'], p['senha'], p['banco']),
                         ("db.exemplo.com", 3307, "ana", "p@ss:1", "loja"))

    def test_apelidos_de_esquema(self):
        for url, esperado in [("postgresql://u:s@h/b", "postgres"), ("postgres://u:s@h/b", "postgres"),
                              ("sqlserver://u:s@h/b", "mssql"), ("mssql://u:s@h/b", "mssql"),
                              ("mariadb://u:s@h/b", "mariadb"), ("mongodb://h/b", "mongodb"),
                              ("redis://h:6380/2", "redis")]:
            self.assertEqual(c.resolver_conexao(url)[0], esperado, url)

    def test_porta_padrao(self):
        self.assertEqual(c.resolver_conexao("mssql://u:s@h/b")[1]['porta'], 1433)
        self.assertEqual(c.resolver_conexao("postgresql://u:s@h/b")[1]['porta'], 5432)

    def test_dados_separados(self):
        tipo, p = c.resolver_conexao("mysql", host="srv", usuario="root", senha="x", banco="loja")
        self.assertEqual((tipo, p['host'], p['porta'], p['banco']), ("mysql", "srv", 3306, "loja"))

    def test_url_do_env(self):
        os.environ['ADVAK_MARIADB_URL'] = "mariadb://u:s@h:3310/b"
        try:
            self.assertEqual(c.resolver_conexao("mariadb")[1]['porta'], 3310)
        finally:
            del os.environ['ADVAK_MARIADB_URL']

    def test_banco_desconhecido(self):
        with self.assertRaises(c.ErroBanco) as e:
            c.resolver_conexao("fantasia://x")
        self.assertIn("advak bancos", str(e.exception))

    def test_legado_postgres_sozinho_nao_e_conector_novo(self):
        self.assertFalse(c.eh_conexao_nova(("postgres",), {}))
        self.assertFalse(c.eh_conexao_nova(("meu_banco",), {}))
        self.assertFalse(c.eh_conexao_nova((), {}))
        self.assertTrue(c.eh_conexao_nova(("postgres",), {"host": "x"}))
        self.assertTrue(c.eh_conexao_nova(("mysql",), {}))
        self.assertTrue(c.eh_conexao_nova(("mysql://u:s@h/b",), {}))


class TesteDriverAusente(unittest.TestCase):
    def test_mensagem_com_pip_install(self):
        for modulo, pip in [("pymysql", "pymysql"), ("pymssql", "pymssql"),
                            ("pymongo", "pymongo"), ("redis", "redis")]:
            antes = sys.modules.pop(modulo, None)
            sys.modules[modulo] = None            # força ImportError
            try:
                tipo = {"pymysql": "mysql", "pymssql": "mssql", "pymongo": "mongodb", "redis": "redis"}[modulo]
                with self.assertRaises(c.ErroBanco) as e:
                    c.conectar(f"{tipo}://u:s@h/b")
                self.assertIn(f"pip install {pip}", str(e.exception))
            finally:
                sys.modules.pop(modulo, None)
                if antes is not None:
                    sys.modules[modulo] = antes


class TesteSQLDialetos(unittest.TestCase):
    def setUp(self):
        for m, f in [("psycopg2", "connect"), ("pymysql", "connect"), ("pymssql", "connect")]:
            instalar_driver_falso(m, f)

    def tearDown(self):
        for m in ("psycopg2", "pymysql", "pymssql"):
            remover_driver(m)

    def db(self, url):
        return c.conectar(url)

    def ultimo(self, db):
        return db._conn.log[-1]

    def test_senha_nunca_aparece_no_repr(self):
        db = self.db("mysql://ana:segredo123@h:3306/loja")
        self.assertNotIn("segredo123", repr(db))

    def test_postgres_marcadores_e_returning(self):
        db = self.db("postgresql://u:s@h/b")
        db._conn.proximo = (["id", "nome"], [(1, "Ana")])
        r = db.inserir("clientes", {"nome": "Ana"})
        sql, params = self.ultimo(db)
        self.assertEqual(sql, 'INSERT INTO "clientes" ("nome") VALUES (%s) RETURNING *')
        self.assertEqual(params, ("Ana",))
        self.assertEqual(r, {"id": 1, "nome": "Ana"})
        self.assertEqual(db._conn.commits, 1)

    def test_postgres_sql_com_dolar_e_lista(self):
        db = self.db("postgresql://u:s@h/b")
        db.sql("UPDATE t SET a=$2 WHERE id=$1", [5, "x"])
        self.assertEqual(self.ultimo(db), ("UPDATE t SET a=%s WHERE id=%s", ("x", 5)))

    def test_lista_nao_vira_array(self):
        db = self.db("postgresql://u:s@h/b")
        db.buscar("t").onde("id = %s", [3]).executar()
        self.assertEqual(self.ultimo(db)[1], (3,))

    def test_mysql_backticks_e_autonum(self):
        db = self.db("mysql://u:s@h/b")
        db.tabela("produtos", {"id": "autonum", "nome": "texto unico", "ativo": "booleano padrao verdadeiro"})
        sql = self.ultimo(db)[0]
        self.assertIn("`id` INT AUTO_INCREMENT PRIMARY KEY", sql)
        self.assertIn("`nome` VARCHAR(255) UNIQUE", sql)
        self.assertIn("`ativo` TINYINT(1) DEFAULT 1", sql)

    def test_mysql_lastrowid_vira_id(self):
        db = self.db("mysql://u:s@h/b")
        self.assertEqual(db.inserir("t", {"a": 1})['id'], 7)

    def test_mariadb_usa_pymysql(self):
        db = self.db("mariadb://u:s@h/b")
        self.assertEqual(db.tipo, "mariadb")
        self.assertEqual(db._conn.kw['database'], "b")

    def test_mssql_top_e_offset_fetch(self):
        db = self.db("mssql://u:s@h/b")
        db.buscar("itens").onde("preco > %s", 5).limite(10).executar()
        self.assertEqual(self.ultimo(db)[0], 'SELECT TOP 10 * FROM [itens] WHERE (preco > %s)')
        db.buscar("itens").ordenar("id").pagina(3, 10).executar()
        self.assertEqual(self.ultimo(db)[0],
                         'SELECT * FROM [itens] ORDER BY [id] ASC OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY')

    def test_mssql_output_inserted_e_identity(self):
        db = self.db("sqlserver://u:s@h/b")
        db.inserir("t", {"a": 1})
        self.assertEqual(self.ultimo(db)[0], 'INSERT INTO [t] ([a]) OUTPUT INSERTED.* VALUES (%s)')
        db.tabela("t", {"id": "autonum", "nome": "texto"})
        sql = self.ultimo(db)[0]
        self.assertIn("IF OBJECT_ID(N't', N'U') IS NULL", sql)
        self.assertIn("[id] INT IDENTITY(1,1) PRIMARY KEY", sql)
        self.assertIn("[nome] NVARCHAR(MAX)", sql)

    def test_nome_de_tabela_malicioso_e_recusado(self):
        db = self.db("postgresql://u:s@h/b")
        for ruim in ('a;drop table x', 'a"b', "t' OR '1", 'a b', '1abc'):
            with self.assertRaises(c.ErroBanco):
                db.buscar(ruim).executar()

    def test_paginacao_padrao_limit_offset(self):
        db = self.db("mysql://u:s@h/b")
        db.buscar("t").ordenar("id", "desc").pagina(2, 5).executar()
        self.assertEqual(self.ultimo(db)[0], 'SELECT * FROM `t` ORDER BY `id` DESC LIMIT 5 OFFSET 5')

    def test_erro_do_driver_vira_erro_banco_e_reverte(self):
        db = self.db("postgresql://u:s@h/b")

        def quebra(*a, **k):
            raise RuntimeError("falhou")
        db._conn.cursor = lambda: types.SimpleNamespace(execute=quebra, close=lambda: None)
        with self.assertRaises(c.ErroBanco) as e:
            db.sql("DELETE FROM t")
        self.assertIn("Erro no PostgreSQL", str(e.exception))
        self.assertEqual(db._conn.rollbacks, 1)

    def test_transacao_nao_comita_no_meio(self):
        db = self.db("postgresql://u:s@h/b")
        db.iniciar()
        db.sql("DELETE FROM t")
        self.assertEqual(db._conn.commits, 0)
        db.confirmar()
        self.assertEqual(db._conn.commits, 1)
        db.iniciar()
        db.reverter()
        self.assertEqual(db._conn.rollbacks, 1)


# ── MongoDB falso ────────────────────────────────────────────────────────────

class FakeColecao:
    def __init__(self):
        self.docs, self.chamadas = [], []

    def insert_one(self, d):
        d['_id'] = "507f1f77bcf86cd799439011"
        self.docs.append(d)
        return types.SimpleNamespace(inserted_id=d['_id'])

    def find(self, filtro, campos=None):
        self.chamadas.append(("find", filtro))
        return FakeCursorMongo(self.docs)

    def update_many(self, f, u):
        self.chamadas.append(("update_many", f, u))
        return types.SimpleNamespace(modified_count=2)

    def delete_many(self, f):
        self.chamadas.append(("delete_many", f))
        return types.SimpleNamespace(deleted_count=3)

    def count_documents(self, f):
        self.chamadas.append(("count", f))
        return 4


class FakeCursorMongo(list):
    def __init__(self, docs):
        super().__init__(docs)
        self.ops = []

    def sort(self, o): self.ops.append(("sort", o)); return self
    def skip(self, n): self.ops.append(("skip", n)); return self
    def limit(self, n): self.ops.append(("limit", n)); return self


class TesteMongo(unittest.TestCase):
    def setUp(self):
        self.cols = {}
        cols = self.cols

        class Banco:
            def __getitem__(s, nome): return cols.setdefault(nome, FakeColecao())
            def list_collection_names(s): return list(cols)
            def drop_collection(s, n): cols.pop(n, None)
            def create_collection(s, n): cols.setdefault(n, FakeColecao())
            def command(s, d): return {"ok": 1, **d}

        class Cliente:
            def __init__(s, url, **kw): s.url = url
            def __getitem__(s, nome): return Banco()
            def close(s): pass

        mod = types.ModuleType("pymongo")
        mod.MongoClient = Cliente
        sys.modules["pymongo"] = mod
        self.db = c.conectar("mongodb://u:s@h:27017/loja")

    def tearDown(self):
        remover_driver("pymongo")

    def test_inserir_devolve_id_como_texto(self):
        r = self.db.inserir("clientes", {"nome": "Ana"})
        self.assertEqual(r, {"nome": "Ana", "id": "507f1f77bcf86cd799439011"})

    def test_condicoes_viram_filtro(self):
        f = c.cond_para_filtro("preco > %s AND ativo = %s AND qtd <= $3", [10, True, 5])
        self.assertEqual(f, {"preco": {"$gt": 10}, "ativo": True, "qtd": {"$lte": 5}})
        self.assertEqual(c.cond_para_filtro("a != %s", [1]), {"a": {"$ne": 1}})

    def test_condicao_nao_suportada(self):
        with self.assertRaises(c.ErroBanco):
            c.cond_para_filtro("nome LIKE %s", ["x%"])

    def test_buscar_ordenar_paginar(self):
        self.db.inserir("p", {"n": 1})
        self.db.buscar("p").onde("preco > %s", 2).ordenar("n", "DESC").pagina(2, 5).executar()
        self.assertEqual(self.cols["p"].chamadas[-1], ("find", {"preco": {"$gt": 2}}))

    def test_atualizar_deletar_contar(self):
        self.assertEqual(self.db.atualizar("p", {"a": 1}).onde("a = %s", 0).executar(), 2)
        self.assertEqual(self.cols["p"].chamadas[-1], ("update_many", {"a": 0}, {"$set": {"a": 1}}))
        self.assertEqual(self.db.deletar("p").onde({"a": 9}).executar(), 3)
        self.assertEqual(self.db.contar("p"), 4)

    def test_sql_nao_existe(self):
        with self.assertRaises(c.ErroBanco) as e:
            self.db.sql("SELECT 1")
        self.assertIn("não usa SQL", str(e.exception))


# ── Redis falso ──────────────────────────────────────────────────────────────

class FakeRedis:
    def __init__(self, **kw):
        self.kw, self.d, self.ttls = kw, {}, {}

    @classmethod
    def from_url(cls, url, **kw): return cls(url=url, **kw)
    def ping(self): return True
    def set(self, k, v, ex=None): self.d[k] = v; self.ttls[k] = ex
    def get(self, k): return self.d.get(k)
    def delete(self, *ks): return sum(1 for k in ks if self.d.pop(k, None) is not None)
    def exists(self, k): return int(k in self.d)
    def keys(self, p): return [k for k in self.d if p == "*" or k.startswith(p.rstrip("*"))]
    def incrby(self, k, n): self.d[k] = str(int(self.d.get(k, 0)) + n); return int(self.d[k])
    def decrby(self, k, n): return self.incrby(k, -n)
    def expire(self, k, s): self.ttls[k] = s; return True
    def ttl(self, k): return self.ttls.get(k, -1)
    def close(self): pass


class TesteRedis(unittest.TestCase):
    def setUp(self):
        mod = types.ModuleType("redis")
        mod.Redis = FakeRedis
        sys.modules["redis"] = mod
        self.db = c.conectar("redis://:senha@h:6379/0")

    def tearDown(self):
        remover_driver("redis")

    def test_definir_obter_e_json(self):
        self.db.definir("a", "oi")
        self.assertEqual(self.db.obter("a"), "oi")
        self.assertEqual(self.db.obter("nada", "padrao"), "padrao")
        self.db.definir("u:1", {"nome": "Ana", "idade": 20}, expira=60)
        self.assertEqual(self.db.obter_json("u:1"), {"nome": "Ana", "idade": 20})
        self.assertEqual(self.db.ttl("u:1"), 60)

    def test_incrementar_existe_excluir_chaves(self):
        self.assertEqual(self.db.incrementar("n"), 1)
        self.assertEqual(self.db.incrementar("n", 4), 5)
        self.assertEqual(self.db.decrementar("n", 2), 3)
        self.assertTrue(self.db.existe("n"))
        self.assertEqual(self.db.chaves("n*"), ["n"])
        self.assertEqual(self.db.excluir("n"), 1)
        self.assertFalse(self.db.existe("n"))

    def test_sql_nao_se_aplica(self):
        with self.assertRaises(c.ErroBanco):
            self.db.sql("SELECT 1")


# ── Grupo 2, lote A: CockroachDB, TimescaleDB, Oracle, Firebird, Db2 ──────────

def instalar_drivers_lote_a():
    ora = instalar_driver_falso("oracledb")
    ora.defaults = types.SimpleNamespace(fetch_lobs=True)
    instalar_driver_falso("psycopg2")
    pai = types.ModuleType("firebird")
    sys.modules["firebird"] = pai
    fb = instalar_driver_falso("firebird.driver")
    pai.driver = fb
    instalar_driver_falso("ibm_db_dbi")


def remover_drivers_lote_a():
    for m in ("oracledb", "psycopg2", "firebird.driver", "firebird", "ibm_db_dbi"):
        remover_driver(m)


class TesteLoteA(unittest.TestCase):
    def setUp(self):
        instalar_drivers_lote_a()

    def tearDown(self):
        remover_drivers_lote_a()

    def ultimo(self, db):
        return db._conn.log[-1]

    def test_esquemas_e_portas(self):
        for url, tipo, porta in [("cockroachdb://root@h/loja?sslmode=require", "cockroachdb", 26257),
                                 ("timescaledb://u:s@h/b", "timescaledb", 5432),
                                 ("oracle://u:s@h/XEPDB1", "oracle", 1521),
                                 ("firebird://SYSDBA:masterkey@h//dados/loja.fdb", "firebird", 3050),
                                 ("db2://u:s@h/SAMPLE", "db2", 50000)]:
            t, p = c.resolver_conexao(url)
            self.assertEqual((t, p['porta']), (tipo, porta), url)

    def test_cockroach_usa_sslmode_da_url(self):
        db = c.conectar("cockroachdb://root@h/loja?sslmode=require")
        self.assertEqual(db._conn.kw['sslmode'], "require")
        self.assertEqual(db._conn.kw['port'], 26257)
        db.inserir("t", {"a": 1})
        self.assertIn("RETURNING *", self.ultimo(db)[0])

    def test_timescale_hipertabela(self):
        db = c.conectar("timescaledb://u:s@h/b")
        db.criar_hipertabela("sensores", "tempo")
        self.assertIn("create_hypertable('sensores', 'tempo'", self.ultimo(db)[0])

    def test_oracle_marcadores_numerados_sem_aspas_e_fetch(self):
        db = c.conectar("oracle://u:s@h/XEPDB1")
        self.assertEqual(db._conn.kw['dsn'], "h:1521/XEPDB1")
        db.sql("UPDATE t SET a=%s WHERE id=%s", [1, 2])
        self.assertEqual(self.ultimo(db), ("UPDATE t SET a=:1 WHERE id=:2", (1, 2)))
        db.buscar("itens").onde("preco > %s", 5).ordenar("nome").pagina(2, 10).executar()
        self.assertEqual(self.ultimo(db)[0], 'SELECT * FROM itens WHERE (preco > :1) ORDER BY nome ASC '
                                             'OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY')

    def test_oracle_cria_tabela_so_se_nao_existe_e_default_antes_de_not_null(self):
        db = c.conectar("oracle://u:s@h/XEPDB1")
        db._conn.proximo = (["NOME"], [("PRODUTOS",)])
        self.assertIn("já existe", db.tabela("produtos", {"id": "autonum"}))
        self.assertEqual([s for s, _ in db._conn.log if s.startswith("CREATE")], [])
        db._conn.proximo = (["NOME"], [])
        db.tabela("itens", {"id": "autonum", "nome": "texto unico", "ativo": "booleano padrao verdadeiro obrigatorio"})
        sql = self.ultimo(db)[0]
        self.assertIn("id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY", sql)
        self.assertIn("nome VARCHAR2(255) UNIQUE", sql)
        self.assertIn("ativo NUMBER(1) DEFAULT 1 NOT NULL", sql)

    def test_resultados_maiusculos_viram_minusculos(self):
        db = c.conectar("oracle://u:s@h/XEPDB1")
        db._conn.proximo = (["ID", "NOME"], [(1, "Ana")])
        self.assertEqual(db.buscar("clientes").executar(), [{"id": 1, "nome": "Ana"}])
        db._conn.proximo = (["NOME"], [("CLIENTES",), ("PEDIDOS",)])
        self.assertEqual(db.listar_tabelas(), ["clientes", "pedidos"])

    def test_oracle_inserir_devolve_dados_enviados(self):
        db = c.conectar("oracle://u:s@h/XEPDB1")
        self.assertEqual(db.inserir("t", {"a": 1}), {"a": 1})
        self.assertEqual(self.ultimo(db), ("INSERT INTO t (a) VALUES (:1)", (1,)))

    def test_firebird_first_skip_e_dsn(self):
        db = c.conectar("firebird://SYSDBA:masterkey@srv:3050/C:/dados/loja.fdb")
        self.assertEqual(db._conn.kw['user'], "SYSDBA")
        db.buscar("itens").ordenar("id").pagina(3, 10).executar()
        self.assertEqual(self.ultimo(db)[0], 'SELECT FIRST 10 SKIP 20 * FROM itens ORDER BY id ASC')
        db.sql("DELETE FROM t WHERE id = %s", 1)
        self.assertEqual(self.ultimo(db), ("DELETE FROM t WHERE id = ?", (1,)))

    def test_firebird_tipos(self):
        db = c.conectar("firebird://SYSDBA:masterkey@srv/loja.fdb")
        db._conn.proximo = (["NOME"], [])
        db.tabela("t", {"id": "autonum", "nome": "texto", "ok": "booleano"})
        sql = self.ultimo(db)[0]
        self.assertIn("id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", sql)
        self.assertIn("nome BLOB SUB_TYPE TEXT", sql)

    def test_db2_fetch_first_e_identity(self):
        db = c.conectar("db2://db2inst1:s@h:50000/SAMPLE")
        db.buscar("itens").limite(5).executar()
        self.assertEqual(self.ultimo(db)[0], 'SELECT * FROM itens FETCH FIRST 5 ROWS ONLY')
        db._conn.proximo = (["NOME"], [])
        db.tabela("t", {"id": "autonum"})
        self.assertIn("id INTEGER NOT NULL GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", self.ultimo(db)[0])

    def test_nomes_perigosos_recusados_tambem_sem_aspas(self):
        db = c.conectar("oracle://u:s@h/XEPDB1")
        for ruim in ("t; DROP TABLE x", "a b", "t--x", "a'b"):
            with self.assertRaises(c.ErroBanco):
                db.buscar(ruim).executar()


# ── Grupo 2, lote B ────────────────────────────────────────────────────────────

_MODULOS_FALSOS = []


def modulo(nome, **attrs):
    """Cria (e registra) um módulo falso, inclusive os pacotes pai (a.b.c)."""
    partes = nome.split(".")
    for i in range(1, len(partes) + 1):
        n = ".".join(partes[:i])
        if n not in sys.modules:
            m = types.ModuleType(n)
            sys.modules[n] = m
            _MODULOS_FALSOS.append(n)
            if i > 1:
                setattr(sys.modules[".".join(partes[:i - 1])], partes[i - 1], m)
    for k, v in attrs.items():
        setattr(sys.modules[nome], k, v)
    return sys.modules[nome]


def limpar_modulos():
    for n in _MODULOS_FALSOS:
        sys.modules.pop(n, None)
    _MODULOS_FALSOS.clear()


class FakeCH:
    def __init__(self, **kw):
        self.kw, self.log, self.proximo = kw, [], None

    def query(self, sql, parameters=None):
        self.log.append(("query", sql, parameters))
        cols, rows = self.proximo or ([], [])
        self.proximo = None
        return types.SimpleNamespace(column_names=cols, result_rows=rows)

    def command(self, sql, parameters=None):
        self.log.append(("command", sql, parameters))

    def insert(self, tabela, dados, column_names=None):
        self.log.append(("insert", tabela, dados, column_names))

    def close(self):
        pass


class TesteClickHouse(unittest.TestCase):
    def setUp(self):
        modulo("clickhouse_connect", get_client=lambda **kw: FakeCH(**kw))
        self.db = c.conectar("clickhouse://u:s@h:8123/analise")

    def tearDown(self):
        limpar_modulos()

    def test_conexao(self):
        self.assertEqual(self.db._conn.kw['database'], "analise")
        self.assertEqual(self.db._conn.kw['port'], 8123)

    def test_create_table_com_engine_e_sem_not_null_nem_unique(self):
        self.db.tabela("eventos", {"id": "autonum", "nome": "texto obrigatorio unico", "qtd": "inteiro"})
        _, sql, _ = self.db._conn.log[-1]
        self.assertIn("ENGINE = MergeTree ORDER BY \"id\"", sql)
        self.assertIn('"id" UUID DEFAULT generateUUIDv4()', sql)
        self.assertNotIn("NOT NULL", sql)
        self.assertNotIn("UNIQUE", sql)
        self.assertIn('"qtd" Int32', sql)

    def test_inserir_usa_api_de_insercao(self):
        self.db.inserir("eventos", {"nome": "x", "qtd": 3})
        self.assertEqual(self.db._conn.log[-1], ("insert", "eventos", [["x", 3]], ["nome", "qtd"]))

    def test_atualizar_e_deletar_viram_mutacoes(self):
        self.db.atualizar("eventos", {"qtd": 5}).onde("nome = %s", "x").executar()
        self.assertEqual(self.db._conn.log[-1][1:], ('ALTER TABLE "eventos" UPDATE "qtd" = %s WHERE (nome = %s)', [5, "x"]))
        self.db.deletar("eventos").onde("qtd > %s", 9).executar()
        self.assertEqual(self.db._conn.log[-1][1:], ('ALTER TABLE "eventos" DELETE WHERE (qtd > %s)', [9]))

    def test_buscar_devolve_dicts(self):
        self.db._conn.proximo = (["nome", "qtd"], [("x", 3)])
        self.assertEqual(self.db.buscar("eventos").onde("qtd > $1", 1).limite(5).executar(),
                         [{"nome": "x", "qtd": 3}])
        self.assertEqual(self.db._conn.log[-1][1], 'SELECT * FROM "eventos" WHERE (qtd > %s) LIMIT 5')

    def test_sem_transacoes(self):
        with self.assertRaises(c.ErroBanco):
            self.db.iniciar()


class TesteSnowflake(unittest.TestCase):
    def setUp(self):
        modulo("snowflake.connector", connect=lambda **kw: FakeConn(**kw))

    def tearDown(self):
        limpar_modulos()

    def test_conexao_conta_banco_esquema_warehouse(self):
        db = c.conectar("snowflake://ana:s@xy12345.sa-east-1/LOJA/PUBLICO?warehouse=WH1&role=ANALISTA")
        kw = db._conn.kw
        self.assertEqual((kw['account'], kw['database'], kw['schema'], kw['warehouse'], kw['role']),
                         ("xy12345.sa-east-1", "LOJA", "PUBLICO", "WH1", "ANALISTA"))

    def test_nomes_sem_aspas_e_resultado_minusculo(self):
        db = c.conectar("snowflake://ana:s@conta/LOJA/PUBLICO")
        db._conn.proximo = (["ID", "NOME"], [(1, "Ana")])
        self.assertEqual(db.buscar("clientes").onde("id = %s", 1).executar(), [{"id": 1, "nome": "Ana"}])
        self.assertEqual(db._conn.log[-1], ("SELECT * FROM clientes WHERE (id = %s)", (1,)))

    def test_ddl_com_if_not_exists_e_autoincrement(self):
        db = c.conectar("snowflake://ana:s@conta/LOJA/PUBLICO")
        db.tabela("t", {"id": "autonum", "criado": "datahora"})
        sql = db._conn.log[-1][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS t", sql)
        self.assertIn("id INTEGER AUTOINCREMENT PRIMARY KEY", sql)
        self.assertIn("criado TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()", sql)

    def test_transacao_usa_begin_commit_rollback(self):
        db = c.conectar("snowflake://ana:s@conta/LOJA/PUBLICO")
        db.iniciar(); db.confirmar(); db.iniciar(); db.reverter()
        self.assertEqual([s for s, _ in db._conn.log], ["BEGIN", "COMMIT", "BEGIN", "ROLLBACK"])


class FakeBQJob:
    def __init__(self, linhas, afetadas):
        self._l, self.num_dml_affected_rows = linhas, afetadas

    def result(self):
        return self._l


class FakeBQLinha:
    def __init__(self, d): self._d = d
    def items(self): return self._d.items()


class FakeBQClient:
    def __init__(self, project=None):
        self.project, self.log, self.linhas, self.afetadas = project, [], [], 2

    @classmethod
    def from_service_account_json(cls, caminho, project=None):
        c_ = cls(project)
        c_.caminho = caminho
        return c_

    def query(self, sql, job_config=None):
        self.log.append((sql, job_config))
        return FakeBQJob(self.linhas, self.afetadas)

    def list_tables(self, dataset):
        return [types.SimpleNamespace(table_id="b"), types.SimpleNamespace(table_id="a")]

    def close(self):
        pass


class FakeBQConfig:
    def __init__(self, **kw): self.kw = kw


class TesteBigQuery(unittest.TestCase):
    def setUp(self):
        modulo("google.cloud.bigquery", Client=FakeBQClient, QueryJobConfig=FakeBQConfig,
               ScalarQueryParameter=lambda nome, tipo, valor: (tipo, valor))
        self.db = c.conectar("bigquery://meu-projeto/vendas?credenciais=chave.json")

    def tearDown(self):
        limpar_modulos()

    def test_credenciais_e_dataset_padrao(self):
        self.assertEqual(self.db._conn.caminho, "chave.json")
        self.db.sql("SELECT 1")
        self.assertEqual(self.db._conn.log[-1][1].kw['default_dataset'], "meu-projeto.vendas")

    def test_marcadores_e_tipos_dos_parametros(self):
        import datetime
        self.db._conn.linhas = [FakeBQLinha({"nome": "Ana", "preco": Decimal_("1.5")})]
        r = self.db.sql("SELECT * FROM t WHERE a = %s AND c = %s", [1, "x"])
        sql, cfg = self.db._conn.log[-1]
        self.assertEqual(sql, "SELECT * FROM t WHERE a = ? AND c = ?")
        self.assertEqual(cfg.kw['query_parameters'], [("INT64", 1), ("STRING", "x")])
        self.assertEqual(r, [{"nome": "Ana", "preco": 1.5}])
        self.db.sql("SELECT * FROM t WHERE c = $2 AND a = $1", [1, "x"])
        self.assertEqual(self.db._conn.log[-1][1].kw['query_parameters'], [("STRING", "x"), ("INT64", 1)])
        self.db.sql("SELECT %s, %s, %s, %s", [True, 2.5, datetime.date(2024, 1, 2), None])
        self.assertEqual([t for t, _ in self.db._conn.log[-1][1].kw['query_parameters']],
                         ["BOOL", "FLOAT64", "DATE", "STRING"])

    def test_dml_devolve_linhas_afetadas_e_sem_unique(self):
        self.assertEqual(self.db.atualizar("t", {"a": 1}).onde("id = %s", "x").executar(), 2)
        self.db.tabela("t", {"id": "autonum", "nome": "texto obrigatorio unico"})
        sql = self.db._conn.log[-1][0]
        self.assertIn("`id` STRING DEFAULT GENERATE_UUID()", sql)
        self.assertIn("`nome` STRING NOT NULL", sql)
        self.assertNotIn("UNIQUE", sql)

    def test_listar_tabelas_e_sem_transacao(self):
        self.assertEqual(self.db.listar_tabelas(), ["a", "b"])
        with self.assertRaises(c.ErroBanco):
            self.db.iniciar()


def Decimal_(txt):
    from decimal import Decimal
    return Decimal(txt)


class FakeCassSessao:
    def __init__(self):
        self.log, self.row_factory, self.linhas = [], None, []

    def execute(self, cql, params=None):
        self.log.append((cql, params))
        return self.linhas


class FakeCluster:
    ultimo = None

    def __init__(self, hosts, port=9042, auth_provider=None):
        self.hosts, self.port, self.auth, self.sessao = hosts, port, auth_provider, FakeCassSessao()
        FakeCluster.ultimo = self

    def connect(self, keyspace=None):
        self.keyspace = keyspace
        return self.sessao

    def shutdown(self):
        pass


class TesteCassandra(unittest.TestCase):
    def setUp(self):
        modulo("cassandra")
        modulo("cassandra.cluster", Cluster=FakeCluster)
        modulo("cassandra.auth", PlainTextAuthProvider=lambda u, s: ("auth", u, s))
        modulo("cassandra.query", dict_factory=lambda *a: None)
        self.db = c.conectar("cassandra://ana:s@h:9042/loja")
        self.sessao = FakeCluster.ultimo.sessao

    def tearDown(self):
        limpar_modulos()

    def test_conexao_keyspace_e_auth(self):
        self.assertEqual(FakeCluster.ultimo.keyspace, "loja")
        self.assertEqual(FakeCluster.ultimo.auth, ("auth", "ana", "s"))

    def test_create_table_tem_primary_key_e_nao_tem_restricoes(self):
        self.db.tabela("produtos", {"id": "autonum", "nome": "texto obrigatorio unico", "preco": "decimal"})
        cql = self.sessao.log[-1][0]
        self.assertIn('"id" uuid', cql)
        self.assertIn('"nome" text', cql)
        self.assertNotIn("NOT NULL", cql)
        self.assertIn('PRIMARY KEY ("id")', cql)

    def test_inserir_gera_uuid_quando_a_tabela_tem_autonum(self):
        self.db.tabela("produtos", {"id": "autonum", "nome": "texto"})
        novo = self.db.inserir("produtos", {"nome": "Caneta"})
        cql, params = self.sessao.log[-1]
        self.assertEqual(cql, 'INSERT INTO "produtos" ("nome", "id") VALUES (%s, %s)')
        self.assertEqual(novo['id'], str(params[1]))

    def test_allow_filtering_e_sem_offset(self):
        self.db.buscar("p").onde("preco > %s", 5).limite(3).executar()
        self.assertEqual(self.sessao.log[-1][0], 'SELECT * FROM "p" WHERE (preco > %s) LIMIT 3 ALLOW FILTERING')
        with self.assertRaises(c.ErroBanco):
            self.db.buscar("p").pagina(2, 10).executar()

    def test_sem_transacoes(self):
        with self.assertRaises(c.ErroBanco):
            self.db.iniciar()


class FakeCouchDb:
    def __init__(self):
        self.docs = {}
        self.n = 0

    def save(self, doc):
        if '_id' not in doc:
            self.n += 1
            doc['_id'] = f"auto{self.n}"
        self.docs[doc['_id']] = dict(doc)
        return doc['_id'], "1-abc"

    def find(self, q):
        self.ultima_consulta = q
        return [dict(d, _rev="1-abc") for d in self.docs.values()]

    def __getitem__(self, id_):
        return dict(self.docs[id_])

    def delete(self, doc):
        del self.docs[doc['_id']]


class FakeCouchServer:
    def __init__(self, url):
        self.url, self.dbs = url, {}

    def version(self): return "3.3"
    def __iter__(self): return iter(list(self.dbs))
    def __contains__(self, n): return n in self.dbs
    def __getitem__(self, n): return self.dbs[n]
    def create(self, n): self.dbs[n] = FakeCouchDb(); return self.dbs[n]
    def delete(self, n): del self.dbs[n]


class TesteCouchDB(unittest.TestCase):
    def setUp(self):
        modulo("couchdb", Server=FakeCouchServer)
        self.db = c.conectar("couchdb://admin:p%40ss@h:5984")
        self.db.tabela("clientes")

    def tearDown(self):
        limpar_modulos()

    def test_url_com_senha_codificada(self):
        self.assertEqual(self.db._srv.url, "http://admin:p%40ss@h:5984/")

    def test_crud_completo_com_mesma_api(self):
        a = self.db.inserir("clientes", {"nome": "Ana", "idade": 20})
        self.db.inserir_varios("clientes", [{"nome": "Bia", "idade": 30}, {"nome": "Caio", "idade": 40}])
        self.assertEqual(self.db.contar("clientes"), 3)
        r = self.db.buscar("clientes").onde("idade >= %s", 30).ordenar("idade", "DESC").executar()
        self.assertEqual([x['nome'] for x in r], ["Caio", "Bia"])
        self.assertNotIn("_rev", r[0])
        self.assertEqual(self.db.buscar_id("clientes", a['id'])['nome'], "Ana")
        self.assertEqual(self.db.atualizar("clientes", {"idade": 21}).onde("nome = %s", "Ana").executar(), 1)
        self.assertEqual(self.db.buscar("clientes").onde("nome = %s", "Ana").primeiro()['idade'], 21)
        self.assertEqual(self.db.deletar("clientes").onde("idade > %s", 25).executar(), 2)
        self.assertEqual(self.db.contar("clientes"), 1)
        self.assertEqual(self.db.buscar("clientes").pagina(1, 1).executar()[0]['nome'], "Ana")

    def test_selector_mango_e_nome_invalido(self):
        self.db.buscar("clientes").onde("idade > %s", 1).executar()
        self.assertEqual(self.db._srv["clientes"].ultima_consulta['selector'], {"idade": {"$gt": 1}})
        with self.assertRaises(c.ErroBanco):
            self.db.tabela("Clientes Novos")

    def test_colecoes(self):
        self.assertEqual(self.db.listar_tabelas(), ["clientes"])
        self.db.apagar_tabela("clientes")
        self.assertEqual(self.db.listar_tabelas(), [])


class FakeDocSnap:
    def __init__(self, id_, dados, ref=None):
        self.id, self._d, self.exists, self.reference = id_, dados, True, ref

    def to_dict(self): return dict(self._d)


class FakeDocRef:
    def __init__(self, col, id_): self.col, self.id = col, id_
    def set(self, d): self.col.docs[self.id] = dict(d)
    def update(self, d): self.col.docs[self.id].update(d)
    def delete(self): self.col.docs.pop(self.id, None)

    def get(self):
        if self.id in self.col.docs:
            return FakeDocSnap(self.id, self.col.docs[self.id], self)
        return types.SimpleNamespace(exists=False, to_dict=lambda: None)


class FakeFsCol:
    def __init__(self): self.docs, self.n = {}, 0

    def add(self, d):
        self.n += 1
        ref = FakeDocRef(self, f"doc{self.n}")
        ref.set(d)
        return (None, ref)

    def document(self, id_): return FakeDocRef(self, id_)
    def stream(self): return [FakeDocSnap(i, d, FakeDocRef(self, i)) for i, d in list(self.docs.items())]


class FakeFsClient:
    def __init__(self, project=None): self.project, self.cols = project, {}
    @classmethod
    def from_service_account_json(cls, caminho, project=None):
        o = cls(project); o.caminho = caminho; return o
    def collection(self, n): return self.cols.setdefault(n, FakeFsCol())
    def collections(self): return [types.SimpleNamespace(id=n) for n in self.cols]
    def close(self): pass


class TesteFirestore(unittest.TestCase):
    def setUp(self):
        modulo("google.cloud.firestore", Client=FakeFsClient)
        self.db = c.conectar("firestore://meu-projeto?credenciais=chave.json")

    def tearDown(self):
        limpar_modulos()

    def test_projeto_e_credenciais(self):
        self.assertEqual((self.db._cli.project, self.db._cli.caminho), ("meu-projeto", "chave.json"))

    def test_crud(self):
        a = self.db.inserir("tarefas", {"titulo": "A", "feita": False, "prio": 2})
        self.db.inserir("tarefas", {"titulo": "B", "feita": True, "prio": 1})
        self.db.inserir("tarefas", {"id": "fixa", "titulo": "C", "feita": False, "prio": 3})
        self.assertEqual(self.db.buscar_id("tarefas", "fixa")['titulo'], "C")
        pend = self.db.buscar("tarefas").onde("feita = %s", False).ordenar("prio", "DESC").executar()
        self.assertEqual([t['titulo'] for t in pend], ["C", "A"])
        self.assertEqual(self.db.atualizar("tarefas", {"feita": True}).onde("titulo = %s", "A").executar(), 1)
        self.assertEqual(self.db.deletar("tarefas").onde("feita = %s", True).executar(), 2)
        self.assertEqual(self.db.contar("tarefas"), 1)
        self.assertEqual(a['id'], "doc1")
        self.assertEqual(self.db.listar_tabelas(), ["tarefas"])


class FakeDynTabela:
    def __init__(self): self.itens, self.scans = {}, 0

    def put_item(self, Item): self.itens[Item['id']] = dict(Item)

    def scan(self, ExclusiveStartKey=None):
        self.scans += 1
        todos = list(self.itens.values())
        if ExclusiveStartKey is None and len(todos) > 1:
            return {'Items': todos[:1], 'LastEvaluatedKey': {'id': todos[0]['id']}}
        return {'Items': todos[1:] if ExclusiveStartKey else todos}

    def get_item(self, Key):
        i = self.itens.get(Key['id'])
        return {'Item': i} if i else {}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues):
        self.ultimo_update = (UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues)
        for ph, nome in ExpressionAttributeNames.items():
            self.itens[Key['id']][nome] = ExpressionAttributeValues[':v' + ph[2:]]

    def delete_item(self, Key): self.itens.pop(Key['id'], None)
    def delete(self): pass
    def wait_until_not_exists(self): pass
    def wait_until_exists(self): pass


class FakeDynRecurso:
    def __init__(self, **kw):
        self.kw, self.tabs = kw, {}
        self.tables = types.SimpleNamespace(all=lambda: [types.SimpleNamespace(name=n) for n in self.tabs])

    def Table(self, n): return self.tabs.setdefault(n, FakeDynTabela())

    def create_table(self, **kw):
        self.criada = kw
        return self.Table(kw['TableName'])


class TesteDynamoDB(unittest.TestCase):
    def setUp(self):
        self.res = None

        def resource(servico, **kw):
            self.res = FakeDynRecurso(**kw)
            return self.res
        modulo("boto3", resource=resource)
        self.db = c.conectar("dynamodb://AKIAXXX:segredo@us-east-1?endpoint=http://localhost:8000")

    def tearDown(self):
        limpar_modulos()

    def test_regiao_credenciais_e_endpoint(self):
        self.assertEqual(self.res.kw, {"region_name": "us-east-1", "aws_access_key_id": "AKIAXXX",
                                       "aws_secret_access_key": "segredo", "endpoint_url": "http://localhost:8000"})

    def test_cria_tabela_com_chave_id(self):
        self.db.tabela("pedidos")
        self.assertEqual(self.res.criada['KeySchema'], [{'AttributeName': 'id', 'KeyType': 'HASH'}])
        self.assertEqual(self.res.criada['BillingMode'], 'PAY_PER_REQUEST')

    def test_float_vira_decimal_e_volta_como_numero(self):
        from decimal import Decimal
        self.db.tabela("pedidos")
        novo = self.db.inserir("pedidos", {"total": 12.5, "itens": [1, 2.5], "pago": False})
        guardado = self.res.tabs["pedidos"].itens[novo['id']]
        self.assertEqual(guardado['total'], Decimal("12.5"))
        self.assertEqual(guardado['itens'], [1, Decimal("2.5")])
        lido = self.db.buscar_id("pedidos", novo['id'])
        self.assertEqual((lido['total'], lido['itens']), (12.5, [1, 2.5]))

    def test_scan_com_paginacao_filtro_atualizar_deletar(self):
        self.db.tabela("p")
        for n, v in enumerate([5, 15, 25]):
            self.db.inserir("p", {"nome": f"n{n}", "valor": v})
        r = self.db.buscar("p").onde("valor > %s", 10).ordenar("valor").executar()
        self.assertEqual([x['valor'] for x in r], [15, 25])
        self.assertGreaterEqual(self.res.tabs["p"].scans, 2)
        self.assertEqual(self.db.atualizar("p", {"valor": 99}).onde("nome = %s", "n0").executar(), 1)
        self.assertEqual(self.res.tabs["p"].ultimo_update[0], "SET #c0 = :v0")
        self.assertEqual(self.db.deletar("p").onde("valor >= %s", 25).executar(), 2)


class FakeEs:
    def __init__(self, url, **kw):
        self.url, self.kw, self.docs, self.log = url, kw, {}, []
        self.indices = types.SimpleNamespace(get_alias=lambda index: {"loja": {}, ".kibana": {}},
                                             exists=lambda index: False, create=self._criar,
                                             delete=lambda **k: self.log.append(("delete_index", k)))

    def _criar(self, index): self.log.append(("create_index", index))

    def index(self, index, document, id=None, refresh=None):
        i = id or f"e{len(self.docs) + 1}"
        self.docs[i] = dict(document)
        self.log.append(("index", index, i, refresh))
        return {"_id": i}

    def search(self, index, query, size):
        self.log.append(("search", index, query, size))
        return {"hits": {"hits": [{"_id": i, "_source": d} for i, d in self.docs.items()]}}

    def update(self, index, id, doc, refresh=None):
        self.docs[id].update(doc); self.log.append(("update", id, doc))

    def delete(self, index, id, refresh=None):
        self.docs.pop(id); self.log.append(("delete", id))

    def close(self): pass


class TesteElasticsearch(unittest.TestCase):
    def setUp(self):
        modulo("elasticsearch", Elasticsearch=FakeEs)
        self.db = c.conectar("elasticsearch://elastic:s@h:9200/?https=1&verificar_certificado=0")

    def tearDown(self):
        limpar_modulos()

    def test_conexao(self):
        self.assertEqual(self.db._es.url, "https://h:9200")
        self.assertEqual(self.db._es.kw, {"basic_auth": ("elastic", "s"), "verify_certs": False})

    def test_traducao_de_filtros_seguros(self):
        q = c.ConectorElasticsearch._consulta({"cidade": "Recife", "idade": {"$gte": 18, "$lt": 65},
                                               "ativo": True, "nome": {"$ne": "x"}})
        self.assertEqual(q, {"bool": {"must": [{"match_phrase": {"cidade": "Recife"}},
                                               {"range": {"idade": {"gte": 18, "lt": 65}}},
                                               {"term": {"ativo": True}}]}})
        self.assertEqual(c.ConectorElasticsearch._consulta({}), {"match_all": {}})

    def test_crud_com_refresh_e_refiltro_local(self):
        self.db.inserir("loja", {"nome": "A", "preco": 10})
        self.db.inserir("loja", {"nome": "B", "preco": 30})
        self.assertEqual(self.db._es.log[0][3], "wait_for")
        r = self.db.buscar("loja").onde("nome != %s", "A").executar()
        self.assertEqual([x['nome'] for x in r], ["B"])
        self.assertEqual(self.db.atualizar("loja", {"preco": 11}).onde("nome = %s", "A").executar(), 1)
        self.assertEqual(self.db.deletar("loja").onde("preco > %s", 20).executar(), 1)
        self.assertEqual(self.db.contar("loja"), 1)

    def test_indices_ignoram_internos(self):
        self.assertEqual(self.db.listar_tabelas(), ["loja"])


class FakeNeoSessao:
    def __init__(self, log, respostas): self.log, self.respostas = log, respostas
    def __enter__(self): return self
    def __exit__(self, *a): return False

    def run(self, cypher, params):
        self.log.append((cypher, params))
        r = self.respostas.pop(0) if self.respostas else []
        return [types.SimpleNamespace(data=lambda d=d: d) for d in r]


class FakeNeoDriver:
    def __init__(self, uri, auth): self.uri, self.auth, self.log, self.respostas, self.bancos = uri, auth, [], [], []
    def session(self, database=None):
        self.bancos.append(database)
        return FakeNeoSessao(self.log, self.respostas)
    def close(self): pass


class TesteNeo4j(unittest.TestCase):
    def setUp(self):
        modulo("neo4j", GraphDatabase=types.SimpleNamespace(driver=lambda uri, auth: FakeNeoDriver(uri, auth)))
        self.db = c.conectar("neo4j://neo4j:s@h:7687/grafo")
        self.drv = self.db._drv

    def tearDown(self):
        limpar_modulos()

    def test_uri_auth_e_banco(self):
        self.assertEqual((self.drv.uri, self.drv.auth), ("neo4j://h:7687", ("neo4j", "s")))
        self.db.consulta("RETURN 1")
        self.assertEqual(self.drv.bancos[-1], "grafo")

    def test_inserir_usa_parametros_e_devolve_id(self):
        self.drv.respostas = [[{"id": "4:abc:1"}]]
        r = self.db.inserir("Pessoa", {"nome": "Ana'; DROP", "idade": 20})
        cypher, params = self.drv.log[-1]
        self.assertEqual(cypher, "CREATE (n:Pessoa) SET n = $props RETURN elementId(n) AS id")
        self.assertEqual(params, {"props": {"nome": "Ana'; DROP", "idade": 20}})
        self.assertEqual(r['id'], "4:abc:1")

    def test_buscar_gera_where_parametrizado(self):
        self.drv.respostas = [[{"no": {"nome": "Ana"}, "id": "1"}]]
        r = self.db.buscar("Pessoa").onde("idade >= %s AND nome != %s", 18, "Zé").ordenar("nome", "DESC").pagina(2, 5).executar()
        cypher, params = self.drv.log[-1]
        self.assertEqual(cypher, "MATCH (n:Pessoa) WHERE n.idade >= $p0_0 AND n.nome <> $p1_0 "
                                 "RETURN n AS no, elementId(n) AS id ORDER BY n.nome DESC SKIP 5 LIMIT 5")
        self.assertEqual(params, {"p0_0": 18, "p1_0": "Zé"})
        self.assertEqual(r, [{"nome": "Ana", "id": "1"}])

    def test_atualizar_deletar_contar(self):
        self.drv.respostas = [[{"total": 2}], [{"total": 1}], [{"total": 7}]]
        self.assertEqual(self.db.atualizar("Pessoa", {"idade": 30}).onde("nome = %s", "Ana").executar(), 2)
        self.assertIn("SET n += $dados", self.drv.log[-1][0])
        self.assertEqual(self.db.deletar("Pessoa").onde({"id": "9"}).executar(), 1)
        self.assertIn("elementId(n) = $p0_0", self.drv.log[-1][0])
        self.assertEqual(self.db.contar("Pessoa"), 7)

    def test_relacionar_e_rotulo_invalido(self):
        self.drv.respostas = [[{"id": "r1"}]]
        self.assertEqual(self.db.relacionar("1", "AMIGO_DE", "2", {"desde": 2020}), "r1")
        self.assertIn("CREATE (a)-[r:AMIGO_DE]->(b)", self.drv.log[-1][0])
        for ruim in ("Pessoa) DETACH DELETE (x", "a b", "1x"):
            with self.assertRaises(c.ErroBanco):
                self.db.buscar(ruim)

    def test_sql_nao_existe(self):
        with self.assertRaises(c.ErroBanco) as e:
            self.db.sql("SELECT 1")
        self.assertIn("Cypher", str(e.exception))


class FakeInfluxCliente:
    def __init__(self, url, token, org):
        self.url, self.token, self.org, self.escritas, self.fluxos, self.apagados = url, token, org, [], [], []
        self.tabelas = []
        cli = self
        self.write_api = lambda write_options=None: types.SimpleNamespace(
            write=lambda bucket, org, record: cli.escritas.append((bucket, org, record)))
        self.query_api = lambda: types.SimpleNamespace(query=cli._query)
        self.delete_api = lambda: types.SimpleNamespace(delete=lambda *a, **k: cli.apagados.append((a, k)))

    def _query(self, flux, org=None):
        self.fluxos.append(flux)
        return [types.SimpleNamespace(records=[types.SimpleNamespace(values=v) for v in self.tabelas])]

    def close(self): pass


class FakePonto:
    def __init__(self, medicao): self.m, self.tags, self.campos, self.t = medicao, {}, {}, None
    def tag(self, k, v): self.tags[k] = v; return self
    def field(self, k, v): self.campos[k] = v; return self
    def time(self, t): self.t = t; return self


class TesteInfluxDB(unittest.TestCase):
    def setUp(self):
        modulo("influxdb_client", InfluxDBClient=FakeInfluxCliente, Point=FakePonto)
        modulo("influxdb_client.client.write_api", SYNCHRONOUS="sync")
        self.db = c.conectar("influxdb://:meu-token@h:8086/sensores?org=escola")
        self.cli = self.db._cli

    def tearDown(self):
        limpar_modulos()

    def test_conexao(self):
        self.assertEqual((self.cli.url, self.cli.token, self.cli.org), ("http://h:8086", "meu-token", "escola"))

    def test_inserir_ponto_com_tags(self):
        self.db.inserir("temperatura", {"valor": 21.5}, tags={"sala": "A"})
        bucket, org, ponto = self.cli.escritas[-1]
        self.assertEqual((bucket, org, ponto.m, ponto.tags, ponto.campos), ("sensores", "escola", "temperatura", {"sala": "A"}, {"valor": 21.5}))

    def test_buscar_gera_flux(self):
        self.cli.tabelas = [{"_time": "2024-01-01", "valor": 21.5, "sala": "A", "result": "_result", "table": 0,
                             "_start": 1, "_stop": 2, "_measurement": "temperatura"}]
        r = self.db.buscar("temperatura").desde("-1h").onde("valor > %s AND sala = %s", 20, "A").limite(10).executar()
        flux = self.cli.fluxos[-1]
        self.assertIn('from(bucket: "sensores")', flux)
        self.assertIn('range(start: -1h)', flux)
        self.assertIn('r._measurement == "temperatura"', flux)
        self.assertIn('filter(fn: (r) => r.valor > 20)', flux)
        self.assertIn('filter(fn: (r) => r.sala == "A")', flux)
        self.assertIn('sort(columns: ["_time"], desc: true)', flux)
        self.assertTrue(flux.endswith('limit(n: 10)'))
        self.assertEqual(r, [{"tempo": "2024-01-01", "valor": 21.5, "sala": "A"}])

    def test_entradas_perigosas_recusadas(self):
        for fn in (lambda: self.db.buscar('x") |> drop('), lambda: self.db.buscar("t").desde("-1h) |> yield("),
                   lambda: self.db.buscar("t").onde("a; b = %s", 1)):
            with self.assertRaises(c.ErroBanco):
                fn()
        self.db.buscar("t").onde("nome = %s", 'a"b${x}').executar()
        self.assertIn('r.nome == "a\\"b\\${x}"', self.cli.fluxos[-1])

    def test_atualizar_deletar_nao_existem_e_apagar_dados(self):
        for fn in (lambda: self.db.atualizar("t", {}), lambda: self.db.deletar("t")):
            with self.assertRaises(c.ErroBanco):
                fn()
        self.db.apagar_dados("temperatura", "2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z")
        self.assertEqual(self.cli.apagados[-1][0][2], '_measurement="temperatura"')
        with self.assertRaises(c.ErroBanco):
            self.db.apagar_dados("temperatura", "ontem", "hoje")


class TesteTodosOsBancos(unittest.TestCase):
    def test_mais_de_vinte_bancos_registrados(self):
        self.assertGreaterEqual(len(c.BANCOS), 23)
        for nome in ("sqlite", "postgres", "mysql", "mariadb", "mssql", "oracle", "firebird", "db2",
                     "cockroachdb", "timescaledb", "duckdb", "clickhouse", "snowflake", "bigquery",
                     "mongodb", "couchdb", "firestore", "dynamodb", "redis", "elasticsearch", "neo4j",
                     "influxdb", "cassandra"):
            self.assertIn(nome, c.BANCOS)
            self.assertTrue(hasattr(c, c.BANCOS[nome]['classe']), nome)

    def test_todo_banco_tem_apelido_de_url_resolvivel(self):
        for tipo, info in c.BANCOS.items():
            for esquema in info['esquemas']:
                if tipo in ('sqlite', 'duckdb'):
                    continue
                self.assertEqual(c.resolver_conexao(f"{esquema}://u:s@h/b")[0], tipo, esquema)

    def test_msg_de_driver_ausente_para_todos(self):
        for tipo, info in c.BANCOS.items():
            if tipo in ('sqlite', 'duckdb'):
                continue
            topo = info['modulo'].split('.')[0]
            guardados = {k: v for k, v in sys.modules.items() if k == info['modulo'] or k.startswith(topo + '.') or k == topo}
            for k in guardados:
                sys.modules.pop(k)
            sys.modules[info['modulo']] = None
            try:
                with self.assertRaises(c.ErroBanco) as e:
                    c.conectar(f"{info['esquemas'][0]}://u:s@h/b")
                self.assertIn(f"pip install {info['pip']}", str(e.exception), tipo)
            finally:
                sys.modules.pop(info['modulo'], None)
                sys.modules.update(guardados)


class TesteListagem(unittest.TestCase):
    def test_advak_bancos_lista_e_marca_status(self):
        txt = c.tabela_bancos()
        for nome in ("SQLite", "PostgreSQL", "MySQL", "MariaDB", "SQL Server", "MongoDB", "Redis", "DuckDB"):
            self.assertIn(nome, txt)
        self.assertIn("instável", txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
