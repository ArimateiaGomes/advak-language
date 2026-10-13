"""
Testes do formatador (`advak formatar`): operadores compostos (+=, -=, ...), seta (=>), igualdade e
comparações, intervalos, textos e comentários. Inclui verificação de que formatar NÃO muda o significado
(a árvore sintática antes e depois é a mesma) em todos os .dk do repositório.

Rodar:  python -I testes/test_formatador.py
"""
import glob
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from advak_formatador import Formatador   # noqa: E402
from advak_lexer import AdvakLexer        # noqa: E402
from advak_parser import Parser           # noqa: E402


def fmt(codigo):
    return Formatador().formatar(codigo)


def ast(codigo):
    return Parser(AdvakLexer(codigo).tokenize()).parse()


def sem_linhas(no):
    """Remove números de linha/coluna da árvore, para comparar só o significado."""
    if isinstance(no, dict):
        return {k: sem_linhas(v) for k, v in no.items() if k not in ('line', 'col')}
    if isinstance(no, list):
        return [sem_linhas(x) for x in no]
    return no


class TesteOperadoresCompostos(unittest.TestCase):
    def test_atribuicao_composta_ganha_espacos(self):
        casos = {
            "x+=1": "x += 1", "x-=1": "x -= 1", "x*=2": "x *= 2", "x/=2": "x /= 2", "x%=2": "x %= 2",
            "x**=2": "x **= 2", "x ??=1": "x ??= 1", "x+= 1": "x += 1", "x +=1": "x += 1",
            "x  +=   1": "x += 1", "total+=preco*qtd": "total += preco*qtd",
            "x&=1": "x &= 1", "x|=1": "x |= 1", "x^=1": "x ^= 1", "x<<=1": "x <<= 1", "x>>=1": "x >>= 1",
            "x&&=a": "x &&= a", "x||=a": "x ||= a",
        }
        for entrada, esperado in casos.items():
            self.assertEqual(fmt(entrada), esperado, entrada)

    def test_atribuicao_simples(self):
        for entrada, esperado in {"x=1": "x = 1", "x =1": "x = 1", "x= 1": "x = 1", "x=-1": "x = -1",
                                  "seja y:inteiro=5": "seja y:inteiro = 5", "a=b=c": "a = b = c"}.items():
            self.assertEqual(fmt(entrada), esperado, entrada)

    def test_seta_de_funcao(self):
        for entrada, esperado in {"seja f=(x)=>x+1": "seja f = (x) => x+1", "(a,b)=>a+b": "(a, b) => a+b",
                                  "seja g = x=>x": "seja g = x => x", "f((x)  =>  x)": "f((x) => x)",
                                  "caso 1 =>imprimir(1)": "caso 1 => imprimir(1)"}.items():
            self.assertEqual(fmt(entrada), esperado, entrada)

    def test_comparacoes_e_igualdades_nao_mudam(self):
        for linha in ["a == b", "a != b", "a <= b", "a >= b", "a === b", "a !== b", "se (x==1) { }",
                      "a<=b", "a>=b", "a!=b", "a==b", "x===y", "x!==y", "se (i<=10 && j>=2) { }"]:
            self.assertEqual(fmt(linha), linha, linha)

    def test_intervalos_e_decremento_nao_mudam(self):
        for linha in ["para (i em 1..=10) { }", "seja r = 0..=n", "i-->0", "x--", "x++", "a <- b"]:
            self.assertEqual(fmt(linha), linha, linha)

    def test_textos_e_comentarios_intactos(self):
        for linha in ['seja t = "a+=1 e x=>y e a=b"', "seja t = `${x+=1} => ${y=2}`", "x += 1 // a+=b => c=d",
                      "seja m = 'x+=1'"]:
            self.assertEqual(fmt(linha), linha, linha)

    def test_textos_de_varias_linhas_ficam_intactos(self):
        origem = 'seja t = "linha1,x\n   linha2=3,a\n\tfim"\nseja z=1'
        saida = fmt(origem).split('\n')
        self.assertEqual(saida, ['seja t = "linha1,x', '   linha2=3,a', '\tfim"', 'seja z = 1'])
        origem2 = "seja t = 'a\n  b+=c\n'\nx+=1"
        self.assertEqual(fmt(origem2).split('\n'), ["seja t = 'a", "  b+=c", "'", "x += 1"])
        origem3 = "seja t = `a\n  ${x}=y,z\n`\nx+=1"
        self.assertEqual(fmt(origem3).split('\n'), ["seja t = `a", "  ${x}=y,z", "`", "x += 1"])

    def test_comentarios_de_bloco(self):
        origem = "/* não é string: l'água, a+=b\n   continua, x=1 */\ny=2"
        self.assertEqual(fmt(origem).split('\n'), ["/* não é string: l'água, a+=b", "   continua, x=1 */", "y = 2"])
        self.assertEqual(fmt("/* a=b */ y=2"), "/* a=b */ y = 2")

    def test_aspas_dentro_de_comentario_de_linha_nao_abrem_texto(self):
        self.assertEqual(fmt("x=1 // l'água\ny=2"), "x = 1 // l'água\ny = 2")

    def test_idempotente(self):
        entrada = ("seja t=0\nse (a>=1) {\ntotal+=a\ncontagem-=1\nseja f=(x)=>x*2\n}\n"
                   "para (i em 1..=3) {\nt*=i\n}")
        uma = fmt(entrada)
        self.assertEqual(fmt(uma), uma)

    def test_programa_completo(self):
        origem = ("seja soma=0\npara (i em 1..=5) {\nsoma+=i\nse (soma>=10) {\nsoma-=1\n}\n}\n"
                  "seja dobro=(x)=>x*2\nimprimir(soma,dobro(2))")
        esperado = ("seja soma = 0\npara (i em 1..=5) {\n    soma += i\n    se (soma>=10) {\n        soma -= 1\n    }\n}\n"
                    "seja dobro = (x) => x*2\nimprimir(soma, dobro(2))")
        self.assertEqual(fmt(origem), esperado)


class TesteSignificadoPreservado(unittest.TestCase):
    """Formatar não pode mudar o que o programa significa."""

    def test_arvore_igual_em_trechos(self):
        trechos = [
            "seja s=0\npara (i em 1..=5) {\ns+=i\ns-=1\ns*=2\n}\nseja f=(x)=>x+1\nseja g=f(2)==3",
            "seja a=1\nse (a<=2&&a>=0) { a=a+1 }\nseja b=a!=2",
            "função f(a:numero,b:numero=0)->numero{\nretornar a+b\n}",
            "seja l=[1,2,3]\nseja m={a:1,b:2}\nseja c=[x*2 para x em l se x>1]",
            "combinar x {\ncaso 1 => imprimir(1)\ncaso _ => imprimir(2)\n}",
        ]
        for t in trechos:
            self.assertEqual(sem_linhas(ast(fmt(t))), sem_linhas(ast(t)), t)

    def test_arvore_igual_em_todos_os_dk_do_repositorio(self):
        arquivos = (glob.glob(os.path.join(RAIZ, '*.dk')) + glob.glob(os.path.join(RAIZ, 'projetos', '*.dk'))
                    + glob.glob(os.path.join(RAIZ, 'testes', '*.dk')))
        comparados = 0
        problemas = []
        for caminho in arquivos:
            with open(caminho, encoding='utf-8') as f:
                origem = f.read()
            try:
                a = sem_linhas(ast(origem))
            except SyntaxError:
                continue                                         # exemplo antigo que já não analisa
            try:
                b = sem_linhas(ast(fmt(origem)))
            except SyntaxError as e:
                problemas.append(f"{os.path.basename(caminho)}: o formatado não analisa ({str(e)[:80]})")
                continue
            if a != b:
                problemas.append(f"{os.path.basename(caminho)}: a árvore mudou")
            comparados += 1
        self.assertGreater(comparados, 40)
        self.assertEqual(problemas, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
