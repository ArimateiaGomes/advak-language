"""db.tabela sobre tabela que já existe: a mensagem não pode dizer "criada" quando as colunas diferem."""
import os, subprocess, sys, tempfile, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rodar(corpo):
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "prog.dk")
        banco = os.path.join(pasta, "t.db").replace("\\", "/")
        with open(arq, "w", encoding="utf-8") as f:
            f.write(f'seja db = banco.conectar("sqlite:///{banco}")\n' + corpo + "\ndb.fechar()\n")
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), arq], cwd=RAIZ, timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
    return [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip()]


BASE = '{id: "autonum", nome: "texto obrigatorio"}'


class TesteTabelaExistente(unittest.TestCase):
    def test_tabela_nova_e_mesmas_colunas_mantem_o_texto_de_sempre(self):
        l = rodar(f'imprimir(db.tabela("clientes", {BASE}))\nimprimir(db.tabela("clientes", {BASE}))')
        self.assertEqual(l, ["✅ Tabela 'clientes' criada", "✅ Tabela 'clientes' criada"])

    def test_colunas_diferentes_nao_diz_criada_e_nao_altera_a_tabela(self):
        l = rodar(f'''db.tabela("clientes", {BASE})
db.inserir("clientes", {{nome: "Ana"}})
imprimir(db.tabela("clientes", {{id: "autonum", nome: "texto", email: "texto", idade: "inteiro"}}))
imprimir(db.tabela("clientes", {{id: "autonum"}}))
imprimir(db.listar_tabelas())
imprimir(db.contar("clientes"))
imprimir(db.descrever_tabela("clientes").tamanho)''')
        self.assertNotIn("criada", l[0])
        self.assertIn("já existe", l[0])
        self.assertIn("Nada foi alterado", l[0])
        self.assertIn("email", l[0]); self.assertIn("idade", l[0])      # faltam na tabela
        self.assertNotIn("criada", l[1])
        self.assertIn("nome", l[1])                                     # sobra na tabela
        self.assertEqual(l[-3:], ["['clientes']", "1", "2"])              # tabela, dado e colunas intactos


if __name__ == "__main__":
    unittest.main(verbosity=2)
