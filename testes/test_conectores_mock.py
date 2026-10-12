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


class TesteListagem(unittest.TestCase):
    def test_advak_bancos_lista_e_marca_status(self):
        txt = c.tabela_bancos()
        for nome in ("SQLite", "PostgreSQL", "MySQL", "MariaDB", "SQL Server", "MongoDB", "Redis", "DuckDB"):
            self.assertIn(nome, txt)
        self.assertIn("instável", txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
