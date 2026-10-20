"""
Testes dos nomes de exceção em advak.py: "except ImportErro" (sem o "r" final) dava NameError em vez de seguir.

(1) sem o colorama, `advak.py versao` precisa terminar com exit 0 (só esse caso foi reproduzido: linha 97);
(2) varredura por AST: nenhum nome usado num "except" de advak.py pode ser inexistente (nem builtin, nem classe
    do arquivo, nem nome importado). É essa varredura que cobre os outros pontos (110, 115, 120, 125, 134, 149, 181).

Rodar:  python -I testes/test_advak_excecoes.py
"""
import ast
import builtins
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVAK = os.path.join(RAIZ, "advak.py")

SEM_COLORAMA = (
    "import runpy, sys\n"
    "sys.modules['colorama'] = None\n"            # 'import colorama' passa a levantar ImportError
    "sys.argv = ['advak.py', 'versao']\n"
    "runpy.run_path(sys.argv_advak, run_name='__main__')\n"
)


class TesteSemColorama(unittest.TestCase):
    def test_versao_roda_sem_colorama(self):
        codigo = SEM_COLORAMA.replace("sys.argv_advak", repr(ADVAK))
        with tempfile.TemporaryDirectory() as pasta:          # cwd fora do repositório
            r = subprocess.run([sys.executable, "-I", "-c", codigo], cwd=pasta, capture_output=True, text=True,
                               encoding="utf-8", timeout=60,
                               env=dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Advak", r.stdout)


def nomes_de_except_inexistentes(caminho):
    """[(linha, nome)] dos nomes simples usados em 'except' que não existem."""
    with open(caminho, encoding="utf-8") as f:
        arvore = ast.parse(f.read(), caminho)
    conhecidos = set(dir(builtins))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ClassDef):
            conhecidos.add(no.name)
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            for a in no.names:
                conhecidos.add((a.asname or a.name).split(".")[0])
    achados = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.ExceptHandler) and no.type is not None:
            tipos = no.type.elts if isinstance(no.type, ast.Tuple) else [no.type]
            achados += [(t.lineno, t.id) for t in tipos if isinstance(t, ast.Name) and t.id not in conhecidos]
    return sorted(achados)


class TesteNomesDeExcecao(unittest.TestCase):
    def test_advak_py_nao_tem_except_com_nome_inexistente(self):
        achados = nomes_de_except_inexistentes(ADVAK)
        mensagem = "\n".join(f"{ADVAK}:{linha}: except {nome} (nome inexistente)" for linha, nome in achados)
        self.assertEqual(achados, [], "\n" + mensagem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
