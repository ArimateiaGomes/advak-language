#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVAK 5.1 — Correção de Startup Lento (Timeout de 15s)
Execute: python corrigir_startup.py
"""
import sys, os, re, time, subprocess

VERDE = "\033[92m"; VERM = "\033[91m"; AMAREL = "\033[93m"
RESET = "\033[0m"; AZUL = "\033[94m"

def ok(m):   print(f"  {VERDE}✅{RESET} {m}")
def err(m):  print(f"  {VERM}❌{RESET} {m}")
def info(m): print(f"  {AZUL}→{RESET}  {m}")

print(f"""
{AZUL}╔══════════════════════════════════════════════════════════╗
║  🔧 ADVAK — Correção de Startup Lento                   ║
║  Causa: matplotlib/tkinter carregados desnecessariamente ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

pasta = os.path.dirname(os.path.abspath(__file__))
os.chdir(pasta)
info(f"Pasta: {pasta}")

# ── FIX 1: matplotlib lazy no advak_gui_modern.py ─────────────────────────
print(f"\n{AZUL}━━ Fix 1: matplotlib lazy ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

with open("advak_gui_modern.py", encoding="utf-8") as f:
    gui = f.read()

OLD_MPL = """# Matplotlib para gráficos
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False"""

NEW_MPL = """# Matplotlib — importado sob demanda (lazy) para evitar 1s+ de startup
MATPLOTLIB_OK = None

def _get_matplotlib():
    global MATPLOTLIB_OK
    if MATPLOTLIB_OK is None:
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            MATPLOTLIB_OK = True
        except ImportError:
            MATPLOTLIB_OK = False
    return MATPLOTLIB_OK"""

if OLD_MPL in gui:
    gui = gui.replace(OLD_MPL, NEW_MPL)
    with open("advak_gui_modern.py", "w", encoding="utf-8") as f:
        f.write(gui)
    ok("matplotlib agora é lazy (economiza ~1s no startup)")
elif NEW_MPL in gui or "def _get_matplotlib():" in gui:
    ok("matplotlib já está lazy (fix já aplicado)")
else:
    err("padrão matplotlib não encontrado — versão diferente")

# ── FIX 2: LazyGUI realmente lazy no advak_interpreter.py ─────────────────
print(f"\n{AZUL}━━ Fix 2: LazyGUI realmente lazy ━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

with open("advak_interpreter.py", encoding="utf-8") as f:
    interp = f.read()

# Verificar se LazyGUI já é realmente lazy
if "_wrapper._lazy_nome = nome" in interp:
    ok("LazyGUI já é realmente lazy (fix já aplicado)")
elif "class _LazyGUI:" in interp:
    # Encontrar e substituir
    idx_start = interp.find("        class _LazyGUI:")
    idx_end   = interp.find("\n        _gui = _LazyGUI()")
    if idx_start > 0 and idx_end > 0:
        idx_end += len("\n        _gui = _LazyGUI()")
        old_block = interp[idx_start:idx_end]
        new_block = """        class _LazyGUI:
            \"\"\"Proxy REALMENTE lazy: so importa tkinter quando metodo e CHAMADO.\"\"\"
            _instancia = None

            def _get(self):
                if self._instancia is None:
                    try:
                        from advak_gui_modern import AdvakGUIModern
                        self._instancia = AdvakGUIModern()
                    except Exception:
                        try:
                            from advak_gui import AdvakGUI
                            self._instancia = AdvakGUI()
                        except Exception:
                            self._instancia = None
                return self._instancia

            def __getattr__(self, nome):
                _self = self
                def _wrapper(*args, **kwargs):
                    inst = _self._get()
                    if inst is None:
                        raise RuntimeError("GUI nao disponivel. Instale tkinter.")
                    return getattr(inst, nome)(*args, **kwargs)
                _wrapper._lazy_nome = nome
                _wrapper._lazy_gui  = self
                return _wrapper

        _gui = _LazyGUI()"""
        interp = interp.replace(old_block, new_block)
        with open("advak_interpreter.py", "w", encoding="utf-8") as f:
            f.write(interp)
        ok("LazyGUI reescrita — nao importa tkinter no __getattr__!")
    else:
        err("nao foi possivel localizar _LazyGUI no arquivo")
else:
    err("_LazyGUI nao encontrada — versao diferente do interpretador")

# ── FIX 3: db_config so com --db ──────────────────────────────────────────
print(f"\n{AZUL}━━ Fix 3: PostgreSQL so com --db ━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

with open("advak.py", encoding="utf-8") as f:
    advak = f.read()

OLD_DB = "interp = AdvakInterpreter(ast, db_config=db_config,"
NEW_DB = "interp = AdvakInterpreter(ast, db_config=db_config if with_db else None,"

if NEW_DB in advak:
    ok("db_config ja e condicional (fix ja aplicado)")
elif OLD_DB in advak:
    advak = advak.replace(OLD_DB, NEW_DB)
    with open("advak.py", "w", encoding="utf-8") as f:
        f.write(advak)
    ok("db_config so passado com --db (evita timeout PostgreSQL)")
else:
    err("padrao db_config nao encontrado")

# ── TESTE FINAL ────────────────────────────────────────────────────────────
print(f"\n{AZUL}━━ Teste de Velocidade ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

arq_teste = "_startup_test.dk"
with open(arq_teste, "w", encoding="utf-8") as f:
    f.write('imprimir("STARTUP_OK")\n')

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

try:
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, "advak.py", arq_teste],
        capture_output=True, timeout=10, env=env, cwd=pasta
    )
    t1 = time.time()
    ms = (t1 - t0) * 1000
    saida = r.stdout.decode("utf-8", errors="replace").strip()
    
    if "STARTUP_OK" in saida:
        ok(f"Startup: {ms:.0f}ms — advak.py funciona corretamente!")
        if ms < 3000:
            ok(f"Velocidade adequada ({ms:.0f}ms < 3000ms)")
        else:
            info(f"Startup ainda lento ({ms:.0f}ms) — pode haver outros modulos")
    else:
        err(f"Saida inesperada: {saida[:60]}")
except subprocess.TimeoutExpired:
    err("AINDA com timeout! Veja se ha outros modulos lentos.")
    err("Execute: python -X importtime advak.py _startup_test.dk 2> import_times.txt")
    err("Abra import_times.txt e procure as linhas mais lentas.")
except Exception as e:
    err(f"Erro: {e}")
finally:
    try: os.remove(arq_teste)
    except: pass

print(f"""
{VERDE}╔══════════════════════════════════════════════════════════╗
║  ✅ Correcao concluida!                                 ║
║                                                          ║
║  Agora execute:                                          ║
║  > advak projetos\\advak_studio.dk                       ║
║                                                          ║
║  Pressione F5 — o resultado deve aparecer em < 3s       ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")
