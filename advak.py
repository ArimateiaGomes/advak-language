#!/usr/bin/env python3
import sys
import threading as _th_shutdown

# ── Forçar UTF-8 no stdout/stderr (Windows usa CP1252 por padrão) ──────────
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
# Também configura via variável de ambiente para subprocessos filhos
import os as _os_enc
_os_enc.environ.setdefault('PYTHONIOENCODING', 'utf-8')
_os_enc.environ.setdefault('PYTHONUTF8', '1')

# ─────────────────────────────────────────────────────────────────────────────
# SHUTDOWN-SAFE STDOUT/STDERR
# Prevents: "Fatal Python error: _enter_buffered_busy: could not acquire lock"
# This happens when daemon threads try to print() during interpreter shutdown.
# ─────────────────────────────────────────────────────────────────────────────
_io_lock = _th_shutdown.Lock()

class _SafeStream:
    """Thread-safe wrapper for stdout/stderr that silences during shutdown."""
    def __init__(self, stream):
        self._s = stream
    def write(self, s):
        try:
            if sys.is_finalizing():
                return len(s) if s else 0
            with _io_lock:
                return self._s.write(s)
        except Exception:
            return 0
    def flush(self):
        try:
            if not sys.is_finalizing():
                with _io_lock:
                    self._s.flush()
        except Exception:
            pass
    def fileno(self):
        return self._s.fileno()
    def isatty(self):
        return self._s.isatty()
    def readable(self):
        return False
    def writable(self):
        return True
    def __getattr__(self, name):
        return getattr(self._s, name)

sys.stdout = _SafeStream(sys.stdout)
sys.stderr = _SafeStream(sys.stderr)
# ─────────────────────────────────────────────────────────────────────────────


# Suppress NoneType: None noise — must be set before any other imports
def _advak_unraisable_filter(args):
    """Filter out silent NoneType exceptions from asyncio garbage collection."""
    if args.exc_type is type(None) or args.exc_value is None:
        return
    if args.exc_type is None:
        return
    sys.__unraisablehook__(args)
sys.unraisablehook = _advak_unraisable_filter

# Also filter stderr to remove the NoneType: None Windows asyncio noise
class _StderrFilter:
    """Filters out asyncio cleanup noise on Windows."""
    NOISE = {'NoneType: None', 'NoneType: None\n'}
    def write(self, s):
        if s.strip() in ('NoneType: None', 'NoneType:None'):
            return len(s)  # suppress
        sys.__stderr__.write(s)
        return len(s)
    def flush(self):
        sys.__stderr__.flush()
    def __getattr__(self, name):
        return getattr(sys.__stderr__, name)

sys.stderr = _StderrFilter()

import os, asyncio, traceback

# ── Cores ANSI no Windows ────────────────────────────────────────────────────
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
    try:
        import colorama; colorama.init(autoreset=False)
    except ImportErro:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# (NoneType filter is set at the very top of this file)

from advak_lexer       import AdvakLexer
from advak_parser      import Parser
from advak_interpreter import AdvakInterpreter, AdvakError
try:
    from advak_erros import exibir_erro_sintaxe, exibir_erro_advak, exibir_erro_interno
except ImportErro:
    pass

try:
    from advak_verificador import cmd_verificar
except ImportErro:
    def cmd_verificar(p): print("⚠️  Módulo advak_verificador não encontrado")

try:
    from advak_doc import cmd_doc
except ImportErro:
    def cmd_doc(p): print("⚠️  Módulo advak_doc não encontrado")

try:
    from advak_live import cmd_live
except ImportErro:
    def cmd_live(p): print("⚠️  Módulo advak_live não encontrado")

if False:
    def exibir_erro_sintaxe(m, s=None): print(f"\n❌ ERRO DE SINTAXE\n   {m}")
    def exibir_erro_advak(m, s=None):   print(f"\n❌ ERRO ADVAK\n   {m}")
    def exibir_erro_interno(t, m, s=None, debug=False): print(f"\n❌ ERRO INTERNO\n   {t}: {m}")
try:
    from advak_repl import cmd_repl
except ImportErro:
    cmd_repl = None

VERSION = "5.2.0"

def cmd_run(path, with_db=False, debug=False, passo=False):
    if not os.path.exists(path):
        print(f"❌ Arquivo '{path}' não encontrado"); return
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    # Inicializa depurador se solicitado
    if debug or passo:
        try:
            import advak_debug
            advak_debug.inicializar(source, path, passo_a_passo=passo)
        except ImportErro:
            print("⚠️  Módulo advak_debug não encontrado")
    # Carrega .env automaticamente
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

    # Sempre carrega config do banco — auto_setup detecta se é necessário
    db_config = {
        'host':     os.environ.get('ADVAK_DB_HOST', 'localhost'),
        'port':     int(os.environ.get('ADVAK_DB_PORT', '5432')),
        'user':     os.environ.get('ADVAK_DB_USER', 'postgres'),
        'password': os.environ.get('ADVAK_DB_PASS', ''),
        'dbname':   os.environ.get('ADVAK_DB_NAME', 'postgres'),
    }
    try:
        tokens = AdvakLexer(source).tokenize()
        ast    = Parser(tokens).parse()
        interp = AdvakInterpreter(ast,
                                  db_config=db_config if with_db else None,
                                  ai_api_key=os.environ.get('GROQ_API_KEY', os.environ.get('ANTHROPIC_API_KEY','')))
        # Run with clean asyncio teardown to suppress NoneType: None on Windows
        if sys.platform == 'win32':
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except AttributeErro:
                pass
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(interp.interpret())
        finally:
            try:
                # Cancel pending tasks cleanly
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            finally:
                loop.close()
    except SyntaxError as e:
        exibir_erro_sintaxe(str(e), source if 'source' in dir() else None)
        if os.environ.get('ADVAK_DEBUG'):
            traceback.print_exc()
    except AdvakError as e:
        exibir_erro_advak(str(e), source if 'source' in dir() else None)
        if os.environ.get('ADVAK_DEBUG'):
            traceback.print_exc()
    except RecursionError:
        exibir_erro_advak(
            "Recursão muito profunda — a função chamou a si mesma vezes demais.\n"
            "   Verifique se há um caso base que interrompe a recursão.",
            source if 'source' in dir() else None
        )
    except MemoryError:
        exibir_erro_advak("Memória insuficiente — o programa usou memória demais.",
                          source if 'source' in dir() else None)
    except KeyboardInterrupt:
        print("\n⚡ Execução interrompida pelo usuário (Ctrl+C)")
    except Exception as e:
        debug = bool(os.environ.get('ADVAK_DEBUG'))
        exibir_erro_interno(type(e).__name__, str(e),
                            source if 'source' in dir() else None, debug)
        if debug:
            traceback.print_exc()

def cmd_check(path):
    try:
        with open(path,'r',encoding='utf-8') as f: src=f.read()
        Parser(AdvakLexer(src).tokenize()).parse()
        print(f"✅ {path}: sintaxe válida")
    except Exception as e: print(f"❌ {e}")

def cmd_compilar(path, args):
    from advak_compiler import AdvakCompiler
    opcoes = {
        'gui':    '--gui'    in args,
        'unico':  '--unico'  in args or True,
        'verbose':'--verbose' in args,
    }
    for i, a in enumerate(args):
        if a == '--nome'   and i+1<len(args): opcoes['nome']  = args[i+1]
        if a == '--icone'  and i+1<len(args): opcoes['icone'] = args[i+1]
        if a == '--saida'  and i+1<len(args): opcoes['saida'] = args[i+1]
    comp = AdvakCompiler()
    comp.verbose = opcoes.pop('verbose', False)
    print(comp.compilar(path, opcoes))

def cmd_new(nome):
    os.makedirs(nome, exist_ok=True)
    os.makedirs(f"{nome}/public", exist_ok=True)
    os.makedirs(f"{nome}/templates", exist_ok=True)
    db = nome.lower().replace('-','_')
    with open(f"{nome}/main.dk",'w',encoding='utf-8') as f:
        f.write(f'// Projeto {nome} — Advak 3.0\n// Execute: advak run {nome}/main.dk\nimprimir("✅ Projeto {nome} iniciado!");\n')
    with open(f"{nome}/servidor.dk",'w',encoding='utf-8') as f:
        f.write(f'''// Servidor HTTP — {nome}
// Execute: advak run {nome}/servidor.dk

servidor.rota("/", "GET", (req) => {{
    retornar servidor.html("<h1>Olá do Advak!</h1><p>Servidor rodando.</p>");
}});

servidor.rota("/api/status", "GET", (req) => {{
    retornar servidor.json({{status: "ok", app: "{nome}", versao: "1.0"}});
}});

servidor.iniciar(8080);
''')
    with open(f"{nome}/app_gui.dk",'w',encoding='utf-8') as f:
        f.write(f'''// App Desktop GUI — {nome}
// Execute: advak run {nome}/app_gui.dk

seja jan = gui.janela("{nome}", 600, 400);
jan.centralizar();

gui.label(jan, "{nome} — Advak 3.0");
gui.separador(jan);

seja campo_nome = gui.campo(jan, "Digite seu nome...");
gui.botao(jan, "Dizer Olá", (btn) => {{
    seja nome = campo_nome.valor();
    se (nome) {{
        gui.alerta(`Olá, ${{nome}}! 👋`);
    }} senão {{
        gui.aviso("Digite seu nome primeiro!");
    }}
}});

gui.iniciar();
''')
    with open(f"{nome}/.env",'w') as f:
        f.write(f"ADVAK_DB_HOST=localhost\nADVAK_DB_PORT=5432\nADVAK_DB_USER=postgres\nADVAK_DB_PASS=\nADVAK_DB_NAME={db}\nANTHROPIC_API_KEY=\n")
    print(f"✅ Projeto '{nome}' criado!")
    print(f"   📄 {nome}/main.dk        — script básico")
    print(f"   🌐 {nome}/servidor.dk    — servidor HTTP")
    print(f"   🖥️  {nome}/app_gui.dk    — app desktop GUI")
    print(f"   📁 {nome}/public/        — arquivos estáticos")
    print(f"   📁 {nome}/templates/     — templates HTML")
    print(f"\n   Executar servidor: advak run {nome}/servidor.dk")
    print(f"   Executar GUI:      advak run {nome}/app_gui.dk")
    print(f"   Compilar binário:  advak compilar {nome}/main.dk")

def show_help():
    print("""
  Advak Language v""" + VERSION + """  —  PostgreSQL + IA + HTTP + GUI

  Comandos:
    advak                          REPL interativo
    advak --db                     REPL + banco automático
    advak run <arquivo.dk>         Executa arquivo
    advak run <arquivo.dk> --db    Executa com banco
    advak compilar <arquivo.dk>    Compila para executável
      --gui     Sem janela de console (para apps GUI)
      --unico   Arquivo único .exe (padrão)
      --nome    Nome do executável
      --icone   Caminho do ícone (.ico)
      --saida   Pasta de saída (padrão: dist/)
      --verbose Mostra log completo
    advak bancos                   Lista os bancos de dados suportados e os drivers instalados
    advak ia                       Lista os provedores de IA e se a chave está configurada
    advak documentos               Lista os formatos de documento (PDF, DOCX, XLSX...) e os drivers
    advak new <nome>               Cria novo projeto completo
    advak check <arquivo.dk>       Verifica sintaxe
    advak --verificar <arquivo.dk> Verifica tipos e padrões
    advak --doc <arquivo.dk>       Gera documentação HTML
    advak --live <arquivo.dk>      Hot reload (reexecuta ao salvar)
    advak --debug <arquivo.dk>     Depurador interativo
    advak --passo <arquivo.dk>     Execução passo a passo
    advak --versao                Versão

  Variáveis de ambiente:
    ADVAK_DB_HOST / ADVAK_DB_PORT / ADVAK_DB_USER / ADVAK_DB_PASS / ADVAK_DB_NAME
    GEMINI_API_KEY (ou ANTHROPIC_API_KEY)
""")

def main():
    args = sys.argv[1:]
    if not args: __import__('advak_repl').AdvakREPL().run(); return
    # Extract debug/passo flags
    _debug = '--debug' in args or '-d' in args
    _passo = '--passo' in args or '--step' in args
    args = [a for a in args if a not in ('--debug','-d','--passo','--step')]
    if not args: __import__('advak_repl').AdvakREPL().run(); return
    cmd = args[0].lower()
    with_db = '--db' in args
    if cmd in ('--ajuda','-h','help','ajuda'): show_help()
    elif cmd in ('--versao','-v','version','--versao','-V','versao'): print(f"Advak {VERSION}")
    elif cmd in ('documentos', 'documents'):
        import advak_documentos
        print(advak_documentos.tabela_formatos())
    elif cmd in ('ia', 'ai'):
        import advak_ia
        print(advak_ia.tabela_provedores())
    elif cmd in ('bancos', 'databases', 'dbs'):
        import advak_conectores
        print(advak_conectores.tabela_bancos())
    elif cmd == 'run':
        if len(args)<2: print("Uso: advak run <arquivo.dk> [--db]")
        else: cmd_run(args[1], with_db, debug=_debug, passo=_passo)
    elif cmd in ('repl','--db'): __import__('advak_repl').AdvakREPL().run()
    elif cmd in ('repl', 'interativo'):
        from advak_repl import AdvakREPL
        AdvakREPL().run()
    elif cmd == 'check':
        if len(args)<2: print("Uso: advak check <arquivo.dk>")
        else: cmd_check(args[1])
    elif cmd in ('compilar', 'build', 'compile', 'nativo'):
        if len(args)<2: print("Uso: advak compilar <arquivo.dk> [--gui] [--nome Nome]")
        else: cmd_compilar(args[1], args[2:])
    elif cmd == 'new':
        if len(args)<2: print("Uso: advak new <nome>")
        else: cmd_new(args[1])
    elif cmd in ('projetos', 'projects', 'proj'):
        from advak_projects import cmd_projetos
        cmd_projetos(args[1:])
    elif cmd in ('verificar', '--verificar', 'check-tipos', 'tipos', 'linter', '--linter'):
        if len(args) < 2: print("Uso: advak --verificar <arquivo.dk>")
        else: cmd_verificar(args[1])
    elif cmd in ('formatar', '--formatar', 'format', '--format'):
        alvo = args[1] if len(args) > 1 else '.'
        ver  = '--ver' in args
        try:
            import advak_formatador
            advak_formatador.formatar(alvo, ver)
        except ImportError:
            print("❌ advak_formatador.py não encontrado")
    elif cmd in ('perfil', '--perfil', 'profile', '--profile'):
        if len(args) < 2: print("Uso: advak --perfil <arquivo.dk>")
        else:
            print(f"  📊 Perfil de execução para {args[1]}")
            try:
                import advak_profiler
                cmd_run(args[1], with_db, debug=_debug, passo=_passo)
            except ImportError:
                cmd_run(args[1], with_db, debug=_debug, passo=_passo)
    elif cmd in ('doc', '--doc', 'documentar', 'docs'):
        if len(args) < 2: print("Uso: advak --doc <arquivo.dk>")
        else: cmd_doc(args[1])
    elif cmd in ('live', '--live', 'hot', '--hot-reload'):
        if len(args) < 2: print("Uso: advak --live <arquivo.dk>")
        else: cmd_live(args[1])
    elif cmd in ('testar', '--testar', 'test', '--test'):
        if len(args) < 2: print("Uso: advak --testar <arquivo.dk>")
        else: cmd_run(args[1], with_db, debug=False, passo=False)
    elif cmd.endswith('.dk'): cmd_run(cmd, with_db, debug=_debug, passo=_passo)
    else:
        print(f"  ❌ Comando não reconhecido: '{cmd}'")
        print("  Use: advak --ajuda para ver os comandos disponíveis")

import atexit as _atexit

@_atexit.register
def _safe_shutdown():
    import sys
    try:
        sys.stdout.flush()
    except Exception:
        pass
    try:
        sys.stderr.flush()
    except Exception:
        pass

if __name__ == '__main__':
    main()