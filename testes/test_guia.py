"""Confere o GUIA_PRATICO: os 12 exemplos existem, estão citados e os que rodam sozinhos dão a saída do guia."""
import csv, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
from rodar_exemplo import executar

GUIA = open(os.path.join(RAIZ, "docs", "GUIA_PRATICO.md"), encoding="utf-8").read()
EXEMPLOS = ["01_medias", "02_gastos", "03_clientes_banco", "04_estoque_gui", "05_api_tarefas", "06_relatorio_csv",
            "07_agenda", "08_regras_testes", "09_trocar_banco", "10_relatorio_vendas_sql", "11_cache_redis",
            "12_catalogo_mongodb", "13_pdv_didatico"]


def moeda(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class TesteGuia(unittest.TestCase):
    def test_tem_13_capitulos_com_exercicio_e_exemplo_real(self):
        self.assertEqual(len(re.findall(r"^## Capítulo \d+", GUIA, re.M)), 13)
        self.assertGreaterEqual(GUIA.count("**Exercício"), 13)
        for e in EXEMPLOS:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "exemplos", e + ".dk")), e)
            self.assertIn(e + ".dk", GUIA)

    def test_palavras_reservadas_cobrem_o_lexer_e_pdv_avisa_que_nao_e_fiscal(self):
        import advak_lexer
        sec = GUIA.split("## Palavras reservadas")[1].split("## Capítulo 1 ")[0]
        self.assertEqual([w for w in advak_lexer.KEYWORDS if "`" + w + "`" not in sec], [])
        for w in ("endereco", "continuar", "acento"):
            self.assertIn(w, sec)
        self.assertIn("NÃO é um PDV fiscal", GUIA.split("## Capítulo 13")[1])
        with open(os.path.join(RAIZ, "exemplos", "13_pdv_didatico.dk"), encoding="utf-8") as f:
            self.assertIn("NÃO é um PDV fiscal", f.read())

    def test_redis_e_mongo_dizem_que_nao_foram_testados_de_verdade(self):
        # protege a honestidade do guia: um aviso para o Redis e outro para o MongoDB
        self.assertGreaterEqual(GUIA.lower().count("não foi testado com um servidor"), 2)
        self.assertIn("Redis real", GUIA)
        self.assertIn("MongoDB real", GUIA)

    def _rodar(self, nome, respostas=()):
        saida, codigo = executar(f"exemplos/{nome}.dk", respostas)
        self.assertIn(codigo, (0, None), saida)
        return saida

    def test_media(self):
        self.assertIn("Média: 7.83", self._rodar("01_medias", ["Ana", "3", "8", "6.5", "9"]))
        self.assertIn("Média: 7.83", GUIA)

    def test_total_do_csv_bate_com_a_soma_das_linhas_o_programa_e_o_guia(self):
        with open(os.path.join(RAIZ, "exemplos", "dados", "vendas.csv"), encoding="utf-8") as f:
            esperado = moeda(sum(int(r["quantidade"]) * float(r["preco"]) for r in csv.DictReader(f)))
        self.assertEqual(esperado, "R$ 507,30")
        self.assertIn("TOTAL GERAL: " + esperado, self._rodar("06_relatorio_csv"))
        self.assertIn("TOTAL GERAL: " + esperado, GUIA)

    def test_pdv_didatico_troco_e_relatorio(self):
        banco = os.path.join(RAIZ, "exemplos", "dados", "pdv_didatico.db")
        if os.path.exists(banco):
            os.remove(banco)
        s = self._rodar("13_pdv_didatico", ["1", "Caderno", "12.5", "20", "1", "Caneta", "2", "100", "3", "1", "2", "2", "10", "",
                                            "50", "4", "0"])
        self.assertIn("TROCO: R$ 5,00", s)
        self.assertIn("Total vendido: R$ 45,00", s)
        self.assertIn("Caneta: 10 unidade(s)", s)
        os.remove(banco)

    def test_agenda_testes_e_sql(self):
        self.assertIn("Carla Souza - (86) 97777-3333 (Teresina)", self._rodar("07_agenda", ["souza", "sair"]))
        self.assertIn("✅ faixas de idade", self._rodar("08_regras_testes"))
        self.assertIn("TOTAL GERAL: R$ 467,30", self._rodar("10_relatorio_vendas_sql"))
        self.assertIn("Total: 3", self._rodar("09_trocar_banco"))
        for t in ("R$ 467,30", "Total: 3"):
            self.assertIn(t, GUIA)


if __name__ == "__main__":
    unittest.main()
