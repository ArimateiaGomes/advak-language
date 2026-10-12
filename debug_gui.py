import sys, os, asyncio, traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from advak_lexer import AdvakLexer
from advak_parser import Parser
from advak_interpreter import AdvakInterpreter, AdvakError

# Carrega .env
for env_file in ['.env', 'env_config.env']:
    if os.path.exists(env_file):
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' in line:
                    k, _, v = line.partition('=')
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break

source_file = os.path.join(BASE_DIR, 'projetos', 'gui_avancada_demo.dk')
with open(source_file, encoding='utf-8') as f:
    source = f.read()

# Monkey-patch o interpreter para mostrar linha atual
import advak_interpreter as ai_mod

orig_exec = ai_mod.AdvakInterpreter.exec_node.__wrapped__ if hasattr(ai_mod.AdvakInterpreter.exec_node, '__wrapped__') else None

# Intercepta erros com traceback completo
async def run():
    tokens = AdvakLexer(source).tokenize()
    ast    = Parser(tokens).parse()
    interp = AdvakInterpreter(ast)
    try:
        await interp.interpret()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\n--- Traceback completo ---")
        traceback.print_exc()

asyncio.run(run())
