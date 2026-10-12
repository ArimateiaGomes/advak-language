"""
Advak 5.0 — REPL Interativo
Execute: advak  (sem argumentos)
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advak_lexer import AdvakLexer
from advak_parser import Parser
from advak_interpreter import AdvakInterpreter, AdvakError

try:
    import readline
    import rlcompleter
except ImportError:
    readline = None

BANNER = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    █████╗ ██████╗ ██╗   ██╗ █████╗ ██╗  ██╗            ║
║   ██╔══██╗██╔══██╗██║   ██║██╔══██╗██║ ██╔╝            ║
║   ███████║██║  ██║██║   ██║███████║█████╔╝              ║
║   ██╔══██║██║  ██║╚██╗ ██╔╝██╔══██║██╔═██╗             ║
║   ██║  ██║██████╔╝ ╚████╔╝ ██║  ██║██║  ██╗            ║
║   ╚═╝  ╚═╝╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝  5.0      ║
║                                                          ║
║   Linguagem de Programação em Português                  ║
╚══════════════════════════════════════════════════════════╝
"""

AJUDA = """
  COMANDOS DO REPL:
  ─────────────────────────────────────────────────────
  .ajuda           Mostra esta ajuda
  .sair            Encerra o REPL
  .limpar          Reinicia a sessão (apaga variáveis)
  .vars            Lista variáveis definidas na sessão
  .carregar ARQ    Carrega e executa um arquivo .dk
  .historico       Mostra últimas 20 entradas
  .exemplo         Mostra exemplos de código Advak

  DICAS:
  ─────────────────────────────────────────────────────
  • Expressões são avaliadas e mostradas com  →
  • Blocos multi-linha: termine a linha com  \
  • Ctrl+C cancela a entrada atual
  • Ctrl+D encerra o REPL

  EXEMPLOS RÁPIDOS:
  ─────────────────────────────────────────────────────
  seja x = 10
  x * 2
  seja lista = [1, 2, 3]
  lista.mapear((x) => x * 2)
  moeda(1500)
  data_hoje()
"""

EXEMPLOS = """
  // Variáveis e operações
  seja nome = "Advak"
  seja versao = 5.0
  imprimir("Bem-vindo ao " + nome + " " + texto(versao))

  // Lista e funções
  seja nums = [1, 2, 3, 4, 5]
  nums.filtrar((x) => x % 2 == 0)
  nums.mapear((x) => x ** 2)
  nums.reduzir((a, b) => a + b, 0)

  // Formatação
  moeda(1500.50)
  data_hoje()
  num_abrev(1500000)

  // Estruturas de controle
  seja x = 10
  se (x > 5) { imprimir("maior") } senão { imprimir("menor") }

  // Funções
  função fatorial(n) {
      se (n <= 1) { retornar 1 }
      retornar n * fatorial(n - 1)
  }
  fatorial(10)
"""


class AdvakREPL:
    def __init__(self):
        self.historico = []
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.interp = AdvakInterpreter([])
        self.loop.run_until_complete(self.interp.interpret())
        self.scope = self.interp.global_scope
        self._buffer = []

    def _is_complete(self, code):
        opens  = code.count('{') + code.count('(') + code.count('[')
        closes = code.count('}') + code.count(')') + code.count(']')
        return opens <= closes

    def _fmt_value(self, v):
        """Formata valor para exibição no REPL."""
        if v is None:          return None  # Não exibe nulo
        if v is True:          return "verdadeiro"
        if v is False:         return "falso"
        if isinstance(v, str): return f'"{v}"'
        if isinstance(v, float):
            if v == int(v):    return str(int(v))
            return str(round(v, 10))
        if isinstance(v, list):
            if len(v) > 10:
                items = ", ".join(str(x) for x in v[:10])
                return f"[{items}, ... +{len(v)-10}]"
            return str(v)
        if isinstance(v, dict):
            if len(v) > 5:
                items = ", ".join(f"{k}: {v2}" for k, v2 in list(v.items())[:5])
                return f"{{{items}, ...}}"
            return str(v)
        return str(v)

    def _eval(self, code):
        try:
            tokens = AdvakLexer(code).tokenize()
            ast    = Parser(tokens).parse()
            if not ast: return

            last = ast[-1]
            if last.get('type') == 'expr_stmt':
                async def _run():
                    for node in ast[:-1]:
                        await self.interp.exec_node(node, self.scope)
                    result = await self.interp.eval(last['expr'], self.scope)
                    fmt = self._fmt_value(result)
                    if fmt is not None:
                        print(f"  \033[32m→ {fmt}\033[0m")
                self.loop.run_until_complete(_run())
            else:
                async def _run_all():
                    for node in ast:
                        await self.interp.exec_node(node, self.scope)
                self.loop.run_until_complete(_run_all())

        except SyntaxError as e:
            print(f"  \033[31m❌ Sintaxe: {e}\033[0m")
        except AdvakError as e:
            print(f"  \033[31m❌ {e}\033[0m")
        except Exception as e:
            print(f"  \033[31m❌ {type(e).__name__}: {e}\033[0m")

    def _carregar(self, path):
        if not path.endswith('.dk'): path += '.dk'
        for base in ['.', 'projetos']:
            full = os.path.join(base, path)
            if os.path.exists(full):
                print(f"  📂 Carregando {full}...")
                with open(full, encoding='utf-8') as f:
                    self._eval(f.read())
                return
        print(f"  \033[31m❌ Arquivo não encontrado: {path}\033[0m")

    def _listar_vars(self):
        skip = {'verdadeiro','falso','nulo','imprimir','texto','numero',
                'booleano','tipo','lista','mapa','tamanho','gui',
                'intervalo','range','moeda','porcentagem','num_fmt',
                'num_abrev','formatar_data','data_agora','data_hoje',
                'advak_executar'}
        vars_user = {k: v for k, v in self.scope.vars.items()
                     if k not in skip and not k.startswith('_')}
        if not vars_user:
            print("  (nenhuma variável definida)")
            return
        for k, v in sorted(vars_user.items()):
            fmt = self._fmt_value(v)
            tipo = type(v).__name__
            print(f"  \033[36m{k}\033[0m = {fmt}  \033[90m({tipo})\033[0m")

    def run(self):
        print(BANNER)
        print(f"  Python {sys.version.split()[0]} | Advak 5.0")
        print(f"  Digite \033[36m.ajuda\033[0m para ver os comandos\n")

        if readline:
            readline.set_history_length(500)
            hist_file = os.path.expanduser('~/.advak_history')
            try:
                if os.path.exists(hist_file):
                    readline.read_history_file(hist_file)
            except Exception: pass

        while True:
            try:
                prompt = "\033[34madvak>>\033[0m " if not self._buffer else "\033[90m     ..\033[0m "
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\n  Até logo! 👋")
                break

            # Commands
            if not self._buffer and line.strip().startswith('.'):
                cmd = line.strip()
                if cmd in ('.sair', '.exit', '.quit'):
                    print("  Até logo! 👋"); break
                elif cmd == '.limpar':
                    self.interp = AdvakInterpreter([])
                    self.loop.run_until_complete(self.interp.interpret())
                    self.scope = self.interp.global_scope
                    self._buffer = []
                    print("  ✅ Sessão reiniciada")
                elif cmd == '.ajuda':
                    print(AJUDA)
                elif cmd == '.vars':
                    self._listar_vars()
                elif cmd == '.exemplo':
                    print(EXEMPLOS)
                elif cmd == '.historico':
                    for i, h in enumerate(self.historico[-20:], 1):
                        print(f"  {i:3}. {h}")
                elif cmd.startswith('.carregar '):
                    self._carregar(cmd[10:].strip())
                else:
                    print(f"  ❓ Comando desconhecido: {cmd}  (tente .ajuda)")
                continue

            # Multi-line buffer
            if line.endswith('\\'):
                self._buffer.append(line[:-1])
                continue

            # Auto-detect incomplete blocks
            full = '\n'.join(self._buffer + [line])
            if not self._is_complete(full):
                self._buffer.append(line)
                continue

            # Execute
            if full.strip():
                self.historico.append(full.strip()[:80])
                self._eval(full)

            self._buffer = []

        if readline:
            try: readline.write_history_file(hist_file)
            except Exception: pass


def cmd_repl():
    AdvakREPL().run()


if __name__ == '__main__':
    cmd_repl()
