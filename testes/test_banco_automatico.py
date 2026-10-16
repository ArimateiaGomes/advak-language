"""Banco automático/manual (docs/BANCO_AUTOMATICO_PROPOSTA.md): modo=, preparar, diferencas, adicionar_coluna,
recusas e mensagens do PostgreSQL. Programas .dk reais com python -I; SQLite em pasta temporária.
PostgreSQL: só tentativas que FALHAM (porta fechada) e driver falso; nada é criado em servidor nenhum."""
import os, subprocess, sys, tempfile, types, unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

MAPA = '{"clientes": {"id": "autonum", "nome": "texto obrigatorio"}, "produtos": {"id": "autonum", "nome": "texto", "preco": "decimal"}}'


def rodar(corpo, entrada="", env_extra=None, modo=None, mapa=None):
    """Roda um .dk com a conexão SQLite temporária em `db`. Devolve as linhas de saída."""
    with tempfile.TemporaryDirectory() as pasta:
        banco = os.path.join(pasta, "t.db").replace("\\", "/")
        extra = ""
        if modo:
            extra += f', modo="{modo}"'
        if mapa:
            extra += f", tabelas={mapa}"
        arq = os.path.join(pasta, "prog.dk")
        with open(arq, "w", encoding="utf-8") as f:
            f.write(f'seja db = banco.conectar("sqlite:///{banco}"{extra})\n' + corpo + "\ndb.fechar()\n")
        env = {k: v for k, v in os.environ.items() if k != "ADVAK_BANCO_MODO"}
        env.update(PYTHONUTF8="1", **(env_extra or {}))
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), arq], cwd=pasta, timeout=60,
                           input=entrada, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    return [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip()]


JUNTO = "\n".join
MAPA_SEM_OBRIGATORIO = MAPA.replace("texto obrigatorio", "texto")   # o obrigatorio sem padrao tem testes próprios


class TesteModos(unittest.TestCase):
    def test_padrao_e_manual_e_nao_cria_nada_ao_conectar(self):
        l = rodar("imprimir(db.modo)\nimprimir(db.listar_tabelas())", mapa=MAPA)
        self.assertEqual(l, ["manual", "[]"])

    def test_modo_invalido_explica_os_tres(self):
        l = JUNTO(rodar("imprimir(1)", modo="doido"))
        self.assertIn("manual", l); self.assertIn("automatico", l); self.assertIn("perguntar", l)

    def test_modo_vem_do_env_e_o_parametro_vence(self):
        self.assertEqual(rodar("imprimir(db.modo)", env_extra={"ADVAK_BANCO_MODO": "perguntar"}), ["perguntar"])
        self.assertEqual(rodar("imprimir(db.modo)", modo="manual", env_extra={"ADVAK_BANCO_MODO": "perguntar"}),
                         ["manual"])

    def test_automatico_cria_o_mapa_ao_conectar_e_avisa(self):
        l = rodar("imprimir(db.listar_tabelas())", modo="automatico", mapa=MAPA)
        self.assertIn("['clientes', 'produtos']", l)
        self.assertTrue(any("clientes" in x and "criada" in x for x in l))

    def test_automatico_sem_nada_a_fazer_fica_em_silencio(self):
        l = rodar(f"db.preparar({MAPA})\nimprimir('fim')", modo="automatico")
        self.assertEqual(l[-1], "fim")


class TestePreparar(unittest.TestCase):
    def test_preparar_cria_o_que_falta_e_nunca_apaga(self):
        l = rodar(f'''db.tabela("antiga", {{"id": "autonum", "x": "texto"}})
db.tabela("clientes", {{"id": "autonum", "nome": "texto obrigatorio", "extra": "texto"}})
db.inserir("clientes", {{"nome": "Ana"}})
imprimir(db.preparar({MAPA}))
imprimir(db.listar_tabelas())
imprimir(db.contar("clientes"))
imprimir(db.descrever_tabela("clientes").tamanho)
imprimir(db.preparar({MAPA}))''')
        txt = JUNTO(l)
        self.assertIn("Tabela 'produtos' criada", txt)
        self.assertIn("['antiga', 'clientes', 'produtos']", l)     # a tabela fora do mapa continua
        self.assertEqual(l[-3:-1], ["1", "3"])                     # dado e coluna "extra" continuam
        self.assertIn("Nada a fazer", l[-1])

    def test_preparar_no_modo_manual_executa_porque_foi_pedido(self):
        l = rodar(f"imprimir(db.preparar({MAPA}))\nimprimir(db.listar_tabelas())")
        self.assertIn("['clientes', 'produtos']", l)

    def test_preparar_sem_argumento_usa_o_mapa_do_projeto(self):
        l = rodar("db.preparar()\nimprimir(db.listar_tabelas())", mapa=MAPA)
        self.assertEqual(l[-1], "['clientes', 'produtos']")

    def test_diferencas_lista_sem_alterar(self):
        l = rodar(f'''db.tabela("clientes", {{"id": "autonum"}})
para (d em db.diferencas({MAPA_SEM_OBRIGATORIO})) {{ imprimir(d) }}
imprimir(db.listar_tabelas())
imprimir(db.descrever_tabela("clientes").tamanho)
db.preparar({MAPA_SEM_OBRIGATORIO})
imprimir(db.diferencas({MAPA_SEM_OBRIGATORIO}))''')
        txt = JUNTO(l[:-3])
        self.assertIn("coluna 'clientes.nome'", txt); self.assertIn("tabela 'produtos'", txt)
        self.assertEqual(l[-3:], ["['clientes']", "1", "[]"])


class TesteColunaNova(unittest.TestCase):
    def test_adicionar_coluna_mantem_os_dados(self):
        l = rodar('''db.tabela("c", {"id": "autonum", "nome": "texto"})
db.inserir("c", {"nome": "Ana"})
imprimir(db.adicionar_coluna("c", "email", "texto"))
db.atualizar("c", {"email": "a@x"}).onde("nome = ?", "Ana").executar()
imprimir(db.buscar("c").executar())
imprimir(db.adicionar_coluna("c", "email", "texto"))''')
        self.assertIn("Coluna 'c.email' adicionada", l[0])
        self.assertIn("a@x", l[1]); self.assertIn("Ana", l[1])
        self.assertIn("já existe", l[2])

    def test_obrigatorio_sem_padrao_em_tabela_com_dados_e_recusado_e_explicado(self):
        l = rodar(f'''db.tabela("clientes", {{"id": "autonum", "nome": "texto"}})
db.inserir("clientes", {{"nome": "Ana"}})
imprimir(db.adicionar_coluna("clientes", "cpf", "texto obrigatorio"))
imprimir(db.preparar({{"clientes": {{"id": "autonum", "nome": "texto", "cpf": "texto obrigatorio", "cidade": "texto"}}}}))
imprimir(db.descrever_tabela("clientes").tamanho)''')
        self.assertIn("NÃO adicionada", l[0]); self.assertIn("padrao", l[0])
        txt = JUNTO(l[1:-1])
        self.assertIn("NÃO adicionada", txt); self.assertIn("Coluna 'clientes.cidade' adicionada", txt)
        self.assertEqual(l[-1], "3")                                    # id, nome, cidade (cpf recusada)

    def test_obrigatorio_com_padrao_e_aceito(self):
        l = rodar('''db.tabela("c", {"id": "autonum", "nome": "texto"})
db.inserir("c", {"nome": "Ana"})
imprimir(db.adicionar_coluna("c", "ativo", "inteiro obrigatorio padrao 1"))
imprimir(db.buscar("c").executar())''')
        self.assertIn("adicionada", l[0]); self.assertIn("1", l[1])

    def test_no_sqlite_obrigatorio_sem_padrao_e_recusado_ate_em_tabela_vazia(self):
        l = rodar('''db.tabela("c", {"id": "autonum"})
imprimir(db.adicionar_coluna("c", "cpf", "texto obrigatorio"))''')
        self.assertIn("NÃO adicionada", l[0])


class TestePerguntar(unittest.TestCase):
    def test_resposta_sim_cria(self):
        l = rodar("imprimir(db.listar_tabelas())", entrada="s\n", modo="perguntar", mapa=MAPA)
        self.assertEqual(l[-1], "['clientes', 'produtos']")
        self.assertTrue(any("[s/N]" in x for x in l))

    def test_resposta_nao_nao_cria(self):
        l = rodar("imprimir(db.listar_tabelas())", entrada="n\n", modo="perguntar", mapa=MAPA)
        self.assertEqual(l[-1], "[]")

    def test_sem_entrada_vira_manual_com_aviso_e_nao_trava(self):
        l = rodar("imprimir(db.listar_tabelas())", entrada="", modo="perguntar", mapa=MAPA)
        self.assertEqual(l[-1], "[]")
        self.assertIn("manual", JUNTO(l[:-1]))


class TesteDicaNoModoManual(unittest.TestCase):
    def test_erro_original_continua_no_comeco_e_ganha_dica(self):
        l = rodar('''db.tabela("produtos", {"id": "autonum", "nome": "texto"})
tentar { db.buscar("produto").executar() } capturar (e) { imprimir("T:", e) }
tentar { db.inserir("produtos", {nome: "X", cor: "azul"}) } capturar (e) { imprimir("C:", e) }''')
        self.assertTrue(l[0].startswith("T: Erro no SQLite: no such table: produto"))
        self.assertIn("db.tabela", JUNTO(l))
        self.assertTrue(any(x.startswith("C: Erro no SQLite: table produtos has no column named cor") for x in l))
        self.assertIn("db.adicionar_coluna", JUNTO(l))


class TesteAvisoSemEmoji(unittest.TestCase):
    def avisar_em(self, codificacao):
        import io
        saida = io.TextIOWrapper(io.BytesIO(), encoding=codificacao, errors="strict")
        with mock.patch.object(sys, "stdout", saida):
            c._avisar("✅ Banco 'x' criado")
            c._avisar("ℹ️  Nada foi criado")
        saida.flush()
        return saida.buffer.getvalue().decode(codificacao)

    def test_cp1252_e_ascii_imprimem_sem_o_emoji_e_sem_erro(self):
        for cod in ("cp1252", "ascii"):
            txt = self.avisar_em(cod)
            self.assertIn("Banco 'x' criado", txt); self.assertIn("Nada foi criado", txt)
            self.assertNotIn("✅", txt)

    def test_aviso_nao_derruba_a_conexao_no_postgres_falso(self):
        import io
        saida = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
        falso = FalsoPg(['FATAL:  database "loja" does not exist'])
        with mock.patch.object(sys, "stdout", saida):
            conectar_pg(falso, modo="automatico")
        self.assertEqual([b for b, _ in falso.chamadas], ["postgres", "loja"])


# ── PostgreSQL: só falhas e driver falso ────────────────────────────────────────────────────────
import advak_conectores as c


class FalsoPg(types.ModuleType):
    """psycopg2 falso: connect() devolve uma conexão que anota os comandos, ou levanta o erro programado."""
    class OperationalError(Exception):
        pass

    def __init__(self, erros=()):
        super().__init__("psycopg2")
        self.erros = list(erros)
        self.chamadas = []                      # (dbname, [comandos])

    def connect(self, **kw):
        if self.erros:
            e = self.erros.pop(0)
            if e:
                raise self.OperationalError(e)
        cmds = []
        self.chamadas.append((kw.get("dbname"), cmds))

        class Cur:
            def execute(s, q, p=None): cmds.append(q)
            def fetchall(s): return []
            def close(s): pass
            description = None
            rowcount = 0

        class Conn:
            autocommit = False
            def cursor(s): return Cur()
            def commit(s): pass
            def rollback(s): pass
            def close(s): pass
        return Conn()


def conectar_pg(falso, modo=None, **kw):
    with mock.patch.dict(sys.modules, {"psycopg2": falso}):
        extra = {"modo": modo} if modo else {}
        return c.conectar("postgres", host="localhost", usuario="u", senha="s", banco="loja", **kw, **extra)


class TesteMensagensPostgres(unittest.TestCase):
    def msg(self, falso, **kw):
        with self.assertRaises(c.ErroBanco) as e:
            conectar_pg(falso, **kw)
        return str(e.exception)

    def test_driver_ausente(self):
        real = c.importlib.import_module
        def sem_pg(nome, *a, **k):
            if nome == "psycopg2":
                raise ImportError(nome)
            return real(nome, *a, **k)
        with mock.patch.object(c.importlib, "import_module", sem_pg):
            with self.assertRaises(c.ErroBanco) as e:
                c.conectar("postgres", host="localhost", usuario="u", senha="s", banco="loja")
        self.assertIn("driver", str(e.exception)); self.assertIn("pip install", str(e.exception))

    def test_servidor_nao_responde_na_porta_padrao(self):
        m = self.msg(FalsoPg(['connection to server at "localhost" (::1), port 5432 failed: Connection refused']))
        self.assertIn("Não consegui falar com o PostgreSQL em localhost:5432", m)
        self.assertIn("instalado e ligado", m)
        self.assertNotIn("instalar-banco", m)
        self.assertEqual(m.count("localhost:5432"), 1)           # uma mensagem só, não uma por IPv6/IPv4

    def test_porta_errada(self):
        m = self.msg(FalsoPg(['connection to server at "localhost" (127.0.0.1), port 5999 failed: Connection refused']),
                     porta=5999)
        self.assertIn("porta", m.lower())

    def test_senha_ou_usuario_errados(self):
        m = self.msg(FalsoPg(['connection to server at "localhost", port 5432 failed: FATAL:  password authentication '
                              'failed for user "u"']))
        self.assertIn("senha", m.lower()); self.assertIn("usuário", m.lower())

    def test_banco_inexistente_no_modo_manual_ensina_criar_banco(self):
        m = self.msg(FalsoPg(['connection to server failed: FATAL:  database "loja" does not exist']))
        self.assertIn("O banco 'loja' não existe", m); self.assertIn("criar_banco", m)

    def test_banco_inexistente_no_automatico_cria_e_reconecta(self):
        falso = FalsoPg(['FATAL:  database "loja" does not exist'])
        conectar_pg(falso, modo="automatico")
        bancos = [b for b, _ in falso.chamadas]
        self.assertEqual(bancos, ["postgres", "loja"])
        self.assertTrue(any('CREATE DATABASE "loja"' in q for q in falso.chamadas[0][1]))

    def test_banco_inexistente_no_perguntar_sem_entrada_nao_cria(self):
        falso = FalsoPg(['FATAL:  database "loja" does not exist'])
        with mock.patch("builtins.input", side_effect=EOFError):
            with self.assertRaises(c.ErroBanco):
                conectar_pg(falso, modo="perguntar")
        self.assertEqual(falso.chamadas, [])

    def test_porta_fechada_de_verdade_com_o_driver_real(self):
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            self.skipTest("psycopg2 não instalado")
        with self.assertRaises(c.ErroBanco) as e:
            c.conectar("postgres", host="localhost", porta=59999, usuario="u", senha="s", banco="x")
        m = str(e.exception)
        self.assertIn("59999", m); self.assertIn("Detalhe do driver:", m)
        self.assertIn("connection to server", m.split("Detalhe do driver:")[1])    # o texto do driver fica só no final
        self.assertEqual(m.count("Detalhe do driver:"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
