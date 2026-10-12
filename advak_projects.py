"""
Advak 3.0 — Gerenciador de Projetos
Gerencia a pasta /projetos com compilação automática.
"""
import os, sys, shutil, json, subprocess
from datetime import datetime

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJETOS_DIR = os.path.join(BASE_DIR, "projetos")
DIST_DIR     = os.path.join(BASE_DIR, "dist")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")

CORES = {
    'reset':    '\033[0m',  'bold':     '\033[1m',
    'verde':    '\033[32m', 'amarelo':  '\033[33m',
    'azul':     '\033[34m', 'ciano':    '\033[36m',
    'vermelho': '\033[31m', 'cinza':    '\033[90m',
    'magenta':  '\033[35m',
}

def c(cor, txt):
    if sys.platform == 'win32':
        try:
            import ctypes
            h = ctypes.windll.kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(mode))
            if not (mode.value & 0x0004):
                return txt
        except: return txt
    return f"{CORES.get(cor,'')}{txt}{CORES['reset']}"

def garantir_estrutura():
    """Cria estrutura de pastas se não existir."""
    for pasta in [PROJETOS_DIR, DIST_DIR, LOGS_DIR]:
        os.makedirs(pasta, exist_ok=True)
    
    # Cria README na pasta projetos
    readme = os.path.join(PROJETOS_DIR, "LEIA-ME.txt")
    if not os.path.exists(readme):
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("""╔══════════════════════════════════════════════════╗
║         ADVAK — PASTA DE PROJETOS               ║
╚══════════════════════════════════════════════════╝

Como usar:
  1. Coloque seus arquivos .dk aqui nesta pasta
  2. Execute: python advak.py projetos
     (lista todos os projetos disponíveis)
  3. Execute: python advak.py projetos run meu_app.dk
     (executa um projeto)
  4. Execute: python advak.py projetos compilar meu_app.dk
     (compila para executável .exe)
  5. Execute: python advak.py projetos novo meu_app
     (cria novo projeto com estrutura básica)

Exemplos de projetos prontos:
  estoque.dk      — Sistema de estoque com GUI
  gui_escola.dk   — Sistema escolar com GUI
  servidor_exemplo.dk — Servidor HTTP REST
  banco_exemplo.dk    — Exemplos de banco de dados

Os executáveis compilados vão para a pasta: ../dist/
""")

def listar_projetos():
    """Lista todos os projetos na pasta /projetos."""
    garantir_estrutura()
    arquivos = [f for f in os.listdir(PROJETOS_DIR) if f.endswith('.dk')]
    
    if not arquivos:
        print(c('amarelo', "\n  Nenhum projeto encontrado."))
        print(c('cinza', f"  Adicione arquivos .dk em: {PROJETOS_DIR}"))
        print(c('cinza', f"  Ou execute: python advak.py projetos novo <nome>"))
        return []
    
    print(c('bold', f"\n  PROJETOS ADVAK ({len(arquivos)} encontrados)"))
    print(c('cinza', f"  Pasta: {PROJETOS_DIR}"))
    print(c('cinza', "  " + "─" * 60))
    
    for i, arq in enumerate(sorted(arquivos), 1):
        caminho  = os.path.join(PROJETOS_DIR, arq)
        tamanho  = os.path.getsize(caminho)
        mod_time = datetime.fromtimestamp(os.path.getmtime(caminho))
        mod_str  = mod_time.strftime('%d/%m/%Y %H:%M')
        
        # Verifica se já foi compilado
        exe_name = arq.replace('.dk', '.exe')
        exe_path = os.path.join(DIST_DIR, exe_name)
        compilado = c('verde', ' [EXE]') if os.path.exists(exe_path) else ''
        
        print(f"  {c('amarelo', str(i).rjust(3))}  {c('ciano', arq.ljust(30))} "
              f"{c('cinza', f'{tamanho:>6} bytes')}  {c('cinza', mod_str)}{compilado}")
    
    print(c('cinza', "  " + "─" * 60))
    print(c('cinza', f"  Dist (EXE): {DIST_DIR}"))
    print()
    return arquivos

def executar_projeto(nome, with_db=True):
    """Executa um projeto da pasta /projetos."""
    garantir_estrutura()
    
    # Procura o arquivo
    if not nome.endswith('.dk'):
        nome += '.dk'
    
    caminho = os.path.join(PROJETOS_DIR, nome)
    if not os.path.exists(caminho):
        print(c('vermelho', f"❌ Projeto '{nome}' não encontrado em /projetos/"))
        listar_projetos()
        return
    
    print(c('verde', f"\n▶  Executando: {nome}"))
    print(c('cinza', f"   Caminho: {caminho}"))
    print(c('cinza', "─" * 50))
    
    # Muda temporariamente para a pasta do projeto
    os.chdir(PROJETOS_DIR)
    try:
        advak_py = os.path.join(BASE_DIR, 'advak.py')
        args = [sys.executable, advak_py, 'run', caminho]
        if with_db:
            args.append('--db')
        subprocess.run(args)
    finally:
        os.chdir(BASE_DIR)

def compilar_projeto(nome, opcoes=None):
    """Compila um projeto para executável."""
    garantir_estrutura()
    
    if not nome.endswith('.dk'):
        nome += '.dk'
    
    caminho = os.path.join(PROJETOS_DIR, nome)
    if not os.path.exists(caminho):
        print(c('vermelho', f"❌ Projeto '{nome}' não encontrado em /projetos/"))
        listar_projetos()
        return
    
    nome_exe = nome.replace('.dk', '')
    print(c('bold', f"\n🔨 Compilando: {nome} → {nome_exe}.exe"))
    print(c('cinza', f"   Origem: {caminho}"))
    print(c('cinza', f"   Destino: {DIST_DIR}"))
    print()
    
    try:
        sys.path.insert(0, BASE_DIR)
        from advak_compiler import AdvakCompiler
        comp = AdvakCompiler()
        comp.verbose = False
        resultado = comp.compilar(caminho, {
            'nome':  nome_exe,
            'saida': DIST_DIR,
            'unico': True,
            'gui':   opcoes and '--gui' in opcoes,
        })
        print(resultado)
        
        # Salva log
        log_path = os.path.join(LOGS_DIR, f"build_{nome_exe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Projeto: {nome}\nData: {datetime.now()}\n\n{resultado}")
        print(c('cinza', f"\n   Log salvo: {log_path}"))
        
    except Exception as e:
        print(c('vermelho', f"❌ Erro na compilação: {e}"))

def novo_projeto(nome):
    """Cria um novo projeto na pasta /projetos."""
    garantir_estrutura()
    
    if not nome.endswith('.dk'):
        nome_arq = nome + '.dk'
    else:
        nome_arq = nome
        nome = nome.replace('.dk', '')
    
    caminho = os.path.join(PROJETOS_DIR, nome_arq)
    if os.path.exists(caminho):
        print(c('amarelo', f"⚠️  Projeto '{nome_arq}' já existe!"))
        return
    
    # Template básico
    template = f'''// ══════════════════════════════════════════════════
//  Projeto: {nome}
//  Criado:  {datetime.now().strftime('%d/%m/%Y %H:%M')}
//  Advak Language 3.0
// ══════════════════════════════════════════════════

// ── Banco de dados ──────────────────────────────
banco.usar("postgres");
banco.criar_banco("{nome.lower().replace(" ","_").replace("-","_")}");
banco.usar("{nome.lower().replace(" ","_").replace("-","_")}");

// ── Interface gráfica ───────────────────────────
seja jan = gui.janela("{nome}", 800, 600);
jan.centralizar();

gui.label(jan, "{nome} — Advak 3.0", negrito=verdadeiro);
gui.separador(jan);

gui.botao(jan, "Olá Mundo!", (btn) => {{
    gui.alerta("Projeto {nome} funcionando!");
}});

gui.iniciar();
'''
    
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(c('verde', f"\n✅ Projeto criado: {nome_arq}"))
    print(c('cinza', f"   Caminho: {caminho}"))
    print(c('cinza', f"\n   Para executar:"))
    print(c('amarelo', f"   python advak.py projetos run {nome_arq}"))
    print(c('cinza', f"\n   Para compilar:"))
    print(c('amarelo', f"   python advak.py projetos compilar {nome_arq}"))

def copiar_para_projetos(arquivo):
    """Copia um arquivo .dk para a pasta /projetos."""
    garantir_estrutura()
    if not os.path.exists(arquivo):
        print(c('vermelho', f"❌ Arquivo '{arquivo}' não encontrado!"))
        return
    destino = os.path.join(PROJETOS_DIR, os.path.basename(arquivo))
    shutil.copy2(arquivo, destino)
    print(c('verde', f"✅ Copiado para projetos: {os.path.basename(arquivo)}"))

def status_projetos():
    """Mostra status completo da estrutura de projetos."""
    garantir_estrutura()
    print(c('bold', "\n  ADVAK — STATUS DOS PROJETOS"))
    print(c('cinza', "  " + "─" * 50))
    
    # Conta projetos
    dks  = [f for f in os.listdir(PROJETOS_DIR) if f.endswith('.dk')]
    exes = [f for f in os.listdir(DIST_DIR)     if f.endswith('.exe')] if os.path.exists(DIST_DIR) else []
    
    print(f"  {c('ciano', 'Pasta projetos:')} {PROJETOS_DIR}")
    print(f"  {c('ciano', 'Pasta dist:')}     {DIST_DIR}")
    print(f"  {c('ciano', 'Pasta logs:')}     {LOGS_DIR}")
    print(c('cinza', "  " + "─" * 50))
    print(f"  {c('verde', str(len(dks)).rjust(4))} projetos .dk")
    print(f"  {c('verde', str(len(exes)).rjust(4))} executáveis compilados")
    print()

def cmd_projetos(args):
    """Ponto de entrada para os comandos de projetos."""
    garantir_estrutura()
    
    if not args:
        listar_projetos()
        print(c('cinza', "  Comandos disponíveis:"))
        print(c('cinza', "    python advak.py projetos                     lista projetos"))
        print(c('cinza', "    python advak.py projetos run <nome.dk>        executa"))
        print(c('cinza', "    python advak.py projetos compilar <nome.dk>   compila para .exe"))
        print(c('cinza', "    python advak.py projetos novo <nome>           cria novo projeto"))
        print(c('cinza', "    python advak.py projetos adicionar <arq.dk>   copia para /projetos"))
        print(c('cinza', "    python advak.py projetos status               mostra estrutura"))
        return
    
    sub = args[0].lower()
    
    if sub in ('run', 'executar'):
        if len(args) < 2:
            print("Uso: python advak.py projetos run <nome.dk>")
        else:
            executar_projeto(args[1])
    
    elif sub in ('compilar', 'build', 'compile'):
        if len(args) < 2:
            print("Uso: python advak.py projetos compilar <nome.dk>")
        else:
            compilar_projeto(args[1], args[2:])
    
    elif sub in ('novo', 'new', 'criar'):
        if len(args) < 2:
            print("Uso: python advak.py projetos novo <nome>")
        else:
            novo_projeto(' '.join(args[1:]))
    
    elif sub in ('adicionar', 'add', 'copiar'):
        if len(args) < 2:
            print("Uso: python advak.py projetos adicionar <arquivo.dk>")
        else:
            copiar_para_projetos(args[1])
    
    elif sub in ('status', 'info'):
        status_projetos()
        listar_projetos()
    
    elif sub in ('lista', 'list', 'ls'):
        listar_projetos()
    
    else:
        # Tenta executar diretamente pelo nome
        executar_projeto(sub)

if __name__ == '__main__':
    cmd_projetos(sys.argv[1:])
