"""
Advak 5.0 — Depurador Visual
Execute: advak --debug arquivo.dk
Ou adicione parar() no código para pausar e inspecionar.
"""
import sys, os, asyncio, threading, re

# ── Cores ──────────────────────────────────────────────────────────────────────
def _c(t, cod): 
    try:
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(): 
            return f"\033[{cod}m{t}\033[0m"
    except: pass
    return t

def _vm(t): return _c(t, '95')   # magenta
def _az(t): return _c(t, '94')   # azul
def _vd(t): return _c(t, '92')   # verde
def _am(t): return _c(t, '93')   # amarelo
def _vm2(t): return _c(t, '91')  # vermelho
def _ci(t): return _c(t, '96')   # ciano
def _ng(t): return _c(t, '90')   # cinza
def _nb(t): return _c(t, '1')    # negrito


class AdvakDepurador:
    """
    Depurador interativo para Advak 5.0.
    
    Modos:
    - Passo a passo: executa linha por linha
    - Pontos de parada: para em parar() no código
    - Inspeção: mostra variáveis, pilha de chamadas
    """

    def __init__(self, source: str, path: str = ""):
        self.source      = source
        self.path        = path
        self.linhas      = source.split('\n')
        self.breakpoints = set()        # linhas com ponto de parada
        self.passo_a_passo = False      # modo passo a passo
        self.pausado     = False
        self.linha_atual = 0
        self.pilha       = []           # pilha de chamadas
        self._ultimo_scope = None
        self._continuar  = threading.Event()
        self._continuar.set()

    # ── Interface TUI ─────────────────────────────────────────────────────────

    def banner(self):
        print()
        print(_nb(_vm("╔══════════════════════════════════════════════════╗")))
        print(_nb(_vm("║    🔍  ADVAK DEPURADOR — Modo Interativo         ║")))
        print(_nb(_vm("╚══════════════════════════════════════════════════╝")))
        print(f"  Arquivo: {_ci(self.path or 'código')}")
        print(f"  Linhas:  {_ci(str(len(self.linhas)))}")
        print()
        print(f"  {_am('Comandos disponíveis:')}")
        print(f"    {_vd('c')} ou {_vd('continuar')}   — continua até próxima parada")
        print(f"    {_vd('p')} ou {_vd('proximo')}     — executa próxima linha")
        print(f"    {_vd('v')} ou {_vd('variaveis')}   — mostra variáveis locais")
        print(f"    {_vd('g')} ou {_vd('globais')}     — mostra variáveis globais")
        print(f"    {_vd('i X')}              — inspeciona variável X")
        print(f"    {_vd('b N')}              — adiciona ponto de parada na linha N")
        print(f"    {_vd('rb N')}             — remove ponto de parada da linha N")
        print(f"    {_vd('bp')}              — lista pontos de parada")
        print(f"    {_vd('s')} ou {_vd('pilha')}       — mostra pilha de chamadas")
        print(f"    {_vd('q')} ou {_vd('sair')}        — encerra depuração")
        print()

    def mostrar_codigo(self, linha_atual, contexto=4):
        """Mostra código com destaque na linha atual."""
        inicio = max(0, linha_atual - contexto - 1)
        fim    = min(len(self.linhas), linha_atual + contexto)

        print(f"\n  {_az('── Código ─────────────────────────────────────────')}")
        for i in range(inicio, fim):
            num   = i + 1
            linha = self.linhas[i]
            tem_bp = num in self.breakpoints
            bp_sym = _vm2("●") if tem_bp else " "

            if num == linha_atual:
                print(f"  {bp_sym} {_nb(_am(f'→ {num:4}'))} {_nb(_am('│'))} {_nb(_am(linha))}")
            else:
                print(f"  {bp_sym} {_ng(f'  {num:4}')} {_ng('│')} {_ng(linha)}")
        print(f"  {_az('─' * 50)}")

    def mostrar_variaveis(self, scope, titulo="Variáveis Locais", max_vars=20):
        """Mostra variáveis de um escopo."""
        if scope is None:
            print(f"  {_am('(sem escopo disponível)')}")
            return

        # Filtra variáveis internas
        # Show only user-declared variables: strings, numbers, booleans, lists, dicts
        import types
        vars_scope = getattr(scope, 'vars', {})
        # Known builtin names to skip
        _BUILTINS = {
            'verdadeiro','falso','nulo','gui','banco','Mat','Math','JSON',
            'embarcado','mobile','servidor','IA','Arquivo','OS','Texto','Lista',
            'ws','orm','cache','validar','fila','log','crypto','env','limite',
            'compilador','tipos','sistema','ambiente','advak_executar',
            'parar','inspecionar','rastrear',
        }

        def _e_user_var(k, v):
            if k.startswith('_'): return False
            if k in _BUILTINS: return False
            # Skip Python callables
            if callable(v) and not isinstance(v, (dict, list)): return False
            # For dicts: show only if values are NOT callables (user maps)
            if isinstance(v, dict):
                for vv in list(v.values())[:5]:
                    if callable(vv): return False
                    if isinstance(vv, dict):
                        for vvv in list(vv.values())[:3]:
                            if callable(vvv): return False
                return True
            return isinstance(v, (str, int, float, bool, list, type(None)))

        vars_user = {k: v for k, v in vars_scope.items() if _e_user_var(k, v)}

        print(f"\n  {_ci(f'── {titulo} ({len(vars_user)} variáveis) ──────────────────────')}")

        if not vars_user:
            print(f"  {_ng('  (nenhuma variável definida)')}")
            return

        for nome, val in list(vars_user.items())[:max_vars]:
            tipo_str = self._tipo_str(val)
            val_str  = self._val_str(val)
            print(f"    {_vd(nome):20} {_ng(tipo_str):12} = {_am(val_str)}")

        if len(vars_user) > max_vars:
            print(f"  {_ng(f'  ... e mais {len(vars_user)-max_vars} variáveis')}")

    def inspecionar_variavel(self, nome, scope):
        """Inspeciona uma variável em detalhe."""
        vars_scope = getattr(scope, 'vars', {}) if scope else {}

        # Busca no escopo e pai
        val = None
        encontrado = False
        sc = scope
        while sc:
            if nome in getattr(sc, 'vars', {}):
                val = sc.vars[nome]
                encontrado = True
                break
            sc = getattr(sc, 'parent', None)

        if not encontrado:
            print(f"  {_vm2(f'Variável {nome!r} não encontrada')}")
            return

        print(f"\n  {_ci(f'── Inspecionando: {nome} ─────────────────────────────')}")
        print(f"  {_am('Nome:')}  {_nb(nome)}")
        print(f"  {_am('Tipo:')}  {self._tipo_str(val)}")
        print(f"  {_am('Valor:')} {self._val_str(val, detalhado=True)}")

        # Para listas e mapas, mostra elementos
        if isinstance(val, list) and len(val) <= 20:
            print(f"  {_am('Elementos:')}")
            for i, item in enumerate(val):
                print(f"    [{i}] = {self._val_str(item)}")
        elif isinstance(val, dict) and len(val) <= 20:
            print(f"  {_am('Campos:')}")
            for k, v in val.items():
                print(f"    .{k} = {self._val_str(v)}")

    def mostrar_pilha(self):
        """Mostra pilha de chamadas."""
        print(f"\n  {_ci('── Pilha de Chamadas ─────────────────────────────────')}")
        if not self.pilha:
            print(f"  {_ng('  (no escopo global)')}")
            return
        for i, frame in enumerate(reversed(self.pilha)):
            seta = "→" if i == 0 else " "
            fn   = frame.get('funcao', '?')
            ln   = frame.get('linha', '?')
            arq  = frame.get('arquivo', '')
            linha_info = _ng(f' (linha {ln})')
            print(f"  {_am(seta)} {_vd(fn)}{linha_info}  {_ng(arq)}")

    def _tipo_str(self, val):
        if val is None:       return 'nulo'
        if isinstance(val, bool):  return 'booleano'
        if isinstance(val, int):   return 'numero'
        if isinstance(val, float): return 'numero'
        if isinstance(val, str):   return f'texto({len(val)})'
        if isinstance(val, list):  return f'lista({len(val)})'
        if isinstance(val, dict):  return f'mapa({len(val)})'
        return type(val).__name__

    def _val_str(self, val, detalhado=False):
        if val is None:       return _ng('nulo')
        if val is True:       return _vd('verdadeiro')
        if val is False:      return _vm2('falso')
        if isinstance(val, str):
            s = repr(val) if detalhado else (f'"{val[:40]}..."' if len(val)>40 else f'"{val}"')
            return _ci(s)
        if isinstance(val, (int, float)):
            return _am(str(val))
        if isinstance(val, list):
            if len(val) == 0: return _ng('[]')
            if len(val) <= 5: return f"[{', '.join(self._val_str(x) for x in val)}]"
            return f"[{', '.join(self._val_str(x) for x in val[:3])}, ... +{len(val)-3}]"
        if isinstance(val, dict):
            if len(val) == 0: return _ng('{}')
            items = list(val.items())[:3]
            s = ', '.join(f"{k}: {self._val_str(v)}" for k, v in items)
            return f"{{{s}{', ...' if len(val)>3 else ''}}}"
        return _ng(str(val)[:50])

    # ── Comandos interativos ───────────────────────────────────────────────────

    def prompt(self, scope=None):
        """Mostra prompt interativo e processa comando."""
        self._ultimo_scope = scope
        while True:
            try:
                cmd = input(f"\n  {_nb(_vm('(depurador)'))} {_vd('>')} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return 'sair'

            if not cmd:
                return 'proximo'

            if cmd in ('c', 'continuar', 'r', 'run'):
                self.passo_a_passo = False
                return 'continuar'

            elif cmd in ('p', 'proximo', 'n', 'next', 's', 'step'):
                self.passo_a_passo = True
                return 'proximo'

            elif cmd in ('v', 'variaveis', 'vars', 'l', 'locals'):
                self.mostrar_variaveis(scope, "Variáveis Locais")

            elif cmd in ('g', 'globais', 'globals'):
                sc = scope
                while getattr(sc, 'parent', None):
                    sc = sc.parent
                self.mostrar_variaveis(sc, "Variáveis Globais")

            elif cmd.startswith('i ') or cmd.startswith('inspecionar '):
                nome = cmd.split(' ', 1)[1].strip()
                self.inspecionar_variavel(nome, scope)

            elif cmd.startswith('b ') or cmd.startswith('break '):
                try:
                    n = int(cmd.split()[1])
                    self.breakpoints.add(n)
                    print(f"  {_vd(f'✅ Ponto de parada adicionado na linha {n}')}")
                except: print(f"  {_vm2('Use: b <número da linha>')}")

            elif cmd.startswith('rb ') or cmd.startswith('remove '):
                try:
                    n = int(cmd.split()[1])
                    self.breakpoints.discard(n)
                    print(f"  {_am(f'Ponto de parada removido da linha {n}')}")
                except: print(f"  {_vm2('Use: rb <número da linha>')}")

            elif cmd in ('bp', 'breakpoints', 'pontos'):
                if self.breakpoints:
                    print(f"  {_am('Pontos de parada:')} {sorted(self.breakpoints)}")
                else:
                    print(f"  {_ng('(nenhum ponto de parada definido)')}")

            elif cmd in ('s', 'pilha', 'stack', 'bt'):
                self.mostrar_pilha()

            elif cmd in ('q', 'sair', 'quit', 'exit'):
                print(f"\n  {_am('Depuração encerrada.')}")
                return 'sair'

            elif cmd in ('?', 'ajuda', 'h', 'help'):
                print(f"""
  {_am('Comandos:')}
    c  continuar  — continua execução
    p  proximo    — próxima linha
    v  variaveis  — variáveis locais
    g  globais    — variáveis globais
    i NOME        — inspeciona variável
    b N           — ponto de parada na linha N
    rb N          — remove ponto de parada
    bp            — lista pontos de parada
    s  pilha      — pilha de chamadas
    q  sair       — encerra depuração
                """)
            else:
                # Tenta avaliar como expressão Advak
                print(f"  {_ng(f'Comando desconhecido: {cmd!r} (digite ? para ajuda)')}")


# ── Integração com o interpretador ────────────────────────────────────────────

_depurador_global: AdvakDepurador = None

def inicializar(source: str, path: str = "", passo_a_passo: bool = False) -> AdvakDepurador:
    """Cria e inicializa o depurador."""
    global _depurador_global
    _depurador_global = AdvakDepurador(source, path)
    _depurador_global.passo_a_passo = passo_a_passo
    _depurador_global.banner()
    return _depurador_global

def parar_aqui(linha: int, scope=None, nome_func: str = "global"):
    """Chamado pelo interpretador ao encontrar parar() ou breakpoint."""
    global _depurador_global
    if _depurador_global is None:
        return

    dep = _depurador_global
    dep.linha_atual = linha

    # Verifica se deve parar
    deve_parar = (dep.passo_a_passo or linha in dep.breakpoints)
    if not deve_parar:
        return

    # Mostra contexto e prompt
    print(f"\n  {_nb(_am(f'⏸  Pausado na linha {linha}'))}"
          f"  {_ng(f'[{nome_func}]')}")
    dep.mostrar_codigo(linha)
    dep.mostrar_variaveis(scope)

    cmd = dep.prompt(scope)
    if cmd == 'sair':
        raise SystemExit(0)
