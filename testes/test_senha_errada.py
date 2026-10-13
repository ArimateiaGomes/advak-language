"""
Senha errada no PostgreSQL em português: o psycopg2 levanta UnicodeDecodeError ("'utf-8' codec can't decode
byte 0xe7...") porque a mensagem do servidor não é UTF-8. A Advak troca isso por uma mensagem clara.
Usa um psycopg2 FALSO (sem servidor e sem senha de verdade).

Rodar:  python -I testes/test_senha_errada.py
"""
import contextlib
import io
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AMIGAVEL = "senha, usuário ou banco incorretos?"


def psycopg2_falso():
    m = types.ModuleType("psycopg2")

    class OperationalError(Exception):
        pass

    def connect(*a, **k):
        raise UnicodeDecodeError("utf-8", b"FATAL: autentica\xe7\xe3o", 16, 17, "invalid continuation byte")
    m.OperationalError, m.connect = OperationalError, connect
    m.__path__ = []                                   # parece um pacote (psycopg2.extras, psycopg2.pool)
    m.extras = types.ModuleType("psycopg2.extras")
    m.pool = types.ModuleType("psycopg2.pool")
    return m


NOMES = ("psycopg2", "psycopg2.extras", "psycopg2.pool")


class Base(unittest.TestCase):
    def setUp(self):
        self._antigos = {n: sys.modules.get(n) for n in NOMES}
        falso = psycopg2_falso()
        sys.modules["psycopg2"], sys.modules["psycopg2.extras"], sys.modules["psycopg2.pool"] = \
            falso, falso.extras, falso.pool

    def tearDown(self):
        for n, antigo in self._antigos.items():
            if antigo is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = antigo


class TesteModoAntigo(Base):
    def test_conectar_levanta_mensagem_clara(self):
        from advak_db import AdvakDB
        with self.assertRaises(sys.modules["psycopg2"].OperationalError) as e:
            AdvakDB(password="errada").conectar()
        msg = str(e.exception)
        self.assertIn(AMIGAVEL, msg)
        self.assertIn("ADVAK_DB_PASS", msg)
        self.assertNotIn("codec", msg)
        self.assertIsNone(e.exception.__cause__)                       # sem o UnicodeDecodeError por trás

    def test_criar_banco_mostra_a_mensagem_clara(self):
        from advak_db import AdvakDB
        r = AdvakDB(password="errada").criar_banco("x")
        self.assertIn(AMIGAVEL, r)
        self.assertNotIn("codec", r)

    def test_auto_setup_mostra_a_mensagem_clara(self):
        from advak_db import AdvakDB
        with self.assertRaises(RuntimeError) as e:
            AdvakDB(password="errada").auto_setup("novo", {"t": {"id": "autonum"}})
        self.assertIn(AMIGAVEL, str(e.exception))
        self.assertNotIn("codec", str(e.exception))


class TesteBancoAuto(Base):
    def test_banco_auto_avisa_com_mensagem_clara_e_cai_no_sqlite(self):
        from advak_bancoweb import BancoWeb
        antes = os.getcwd()
        err = io.StringIO()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            os.chdir(tmp)
            try:
                with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                    db = BancoWeb("teste_senha")
                    self.assertEqual(db._modo, "sq")                      # reserva SQLite
                    with contextlib.suppress(Exception):
                        db._sq.close()
            finally:
                os.chdir(antes)
        self.assertIn(AMIGAVEL, err.getvalue())
        self.assertNotIn("codec", err.getvalue())


class TesteConectorNovo(Base):
    def test_conector_postgresql_levanta_erro_banco_claro(self):
        import advak_conectores as c
        for url in ("postgresql://postgres:Zx9Qk7@localhost/loja", "cockroachdb://root:x@localhost/loja",
                    "timescaledb://postgres:Zx9Qk7@localhost/loja"):
            with self.assertRaises(c.ErroBanco) as e:
                c.conectar(url)
            self.assertIn(AMIGAVEL, str(e.exception), url)
            self.assertNotIn("Zx9Qk7", str(e.exception))                  # a senha nunca aparece
            self.assertNotIn("codec", str(e.exception))

    def test_outros_erros_continuam_com_a_mensagem_original(self):
        import advak_conectores as c
        sys.modules["psycopg2"].connect = lambda *a, **k: (_ for _ in ()).throw(
            sys.modules["psycopg2"].OperationalError("connection refused"))
        with self.assertRaises(sys.modules["psycopg2"].OperationalError):
            c.conectar("postgresql://u:s@localhost/loja")                 # não é UnicodeDecodeError: sem tradução


if __name__ == "__main__":
    unittest.main(verbosity=2)
