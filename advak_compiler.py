"""
Advak 3.0 — Compilador para Binário
Gera executáveis independentes a partir de arquivos .dk

Como funciona:
  1. Lê o arquivo .dk
  2. Gera um script Python wrapper
  3. Usa PyInstaller para compilar para .exe / binário

Uso via CLI:
  python advak.py compilar meu_app.dk
  python advak.py compilar meu_app.dk --nome "MeuApp" --icone icon.ico
  python advak.py compilar meu_app.dk --gui        (sem janela de console)
  python advak.py compilar meu_app.dk --unico      (arquivo único .exe)

Uso no código .dk:
  compilador.compilar("meu_app.dk")
  compilador.compilar("meu_app.dk", {{nome: "MeuApp", gui: verdadeiro}})
"""

import os
import sys
import shutil
import tempfile
import subprocess
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WRAPPER_TEMPLATE = '''#!/usr/bin/env python3
"""Gerado por Advak Compiler 3.0"""
import sys, os, asyncio

# Adiciona o diretório do executável ao path
if getattr(sys, 'frozen', False):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from advak_lexer       import AdvakLexer
from advak_parser      import Parser
from advak_interpreter import AdvakInterpreter
from advak_db          import AdvakDB
from advak_http        import AdvakHTTPServer
try:
    from advak_gui import AdvakGUI
    GUI_OK = True
except ImportError:
    GUI_OK = False

SOURCE_CODE = {source_code!r}
DB_CONFIG = {db_config!r}
AI_KEY = os.environ.get('ANTHROPIC_API_KEY', {ai_key!r})

def main():
    try:
        tokens = AdvakLexer(SOURCE_CODE).tokenize()
        ast    = Parser(tokens).parse()
        interp = AdvakInterpreter(ast, db_config=DB_CONFIG, ai_api_key=AI_KEY)
        # Injeta objetos extras
        http = AdvakHTTPServer()
        interp.global_scope.declare('servidor', {{
            'rota': lambda c,m,h: http.rota(c,m,h),
            'get':  lambda c,h: http.get(c,h),
            'post': lambda c,h: http.post(c,h),
            'put':  lambda c,h: http.put(c,h),
            'delete': lambda c,h: http.delete(c,h),
            'iniciar': lambda *a,**k: http.iniciar(*a,**k),
            'parar': http.parar,
            'json': http.json, 'html': http.html,
            'texto': http.texto, 'redirecionar': http.redirecionar,
            'arquivo': http.arquivo, 'renderizar': http.renderizar,
            'middleware': http.middleware,
        }})
        if GUI_OK:
            gui_obj = AdvakGUI()
            interp.global_scope.declare('gui', {{
                'janela': gui_obj.janela,
                'label': gui_obj.label,
                'botao': gui_obj.botao,
                'campo': gui_obj.campo,
                'area_texto': gui_obj.area_texto,
                'tabela': gui_obj.tabela,
                'lista': gui_obj.lista,
                'caixa_selecao': gui_obj.caixa_selecao,
                'checkbox': gui_obj.checkbox,
                'barra_progresso': gui_obj.barra_progresso,
                'separador': gui_obj.separador,
                'frame': gui_obj.frame,
                'frame_horizontal': gui_obj.frame_horizontal,
                'menu_bar': gui_obj.menu_bar,
                'abas': gui_obj.abas,
                'alerta': gui_obj.alerta,
                'erro': gui_obj.erro,
                'aviso': gui_obj.aviso,
                'confirmar': gui_obj.confirmar,
                'pedir': gui_obj.pedir,
                'pedir_numero': gui_obj.pedir_numero,
                'escolher_arquivo': gui_obj.escolher_arquivo,
                'salvar_arquivo': gui_obj.salvar_arquivo,
                'escolher_cor': gui_obj.escolher_cor,
                'escolher_pasta': gui_obj.escolher_pasta,
                'iniciar': gui_obj.iniciar,
                'parar': gui_obj.parar,
                'apos': gui_obj.apos,
                'repetir': gui_obj.repetir,
                'atualizar': gui_obj.atualizar,
                'tema': gui_obj.tema,
            }})
        asyncio.run(interp.interpret())
    except Exception as e:
        import traceback
        print(f"Erro: {{e}}", file=sys.stderr)
        if os.environ.get('ADVAK_DEBUG'):
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
'''


class AdvakCompiler:
    """Compilador de código Advak para executável binário."""

    def __init__(self):
        self.verbose = False

    def compilar(self, arquivo_dk, opcoes=None):
        """
        Compila um arquivo .dk para executável.

        opcoes: dict com:
          nome       — nome do executável (padrão: nome do arquivo)
          icone      — caminho para ícone .ico (Windows) ou .icns (Mac)
          gui        — True = sem janela de console (para apps GUI)
          unico      — True = arquivo único (padrão: pasta)
          saida      — pasta de saída (padrão: dist/)
          db_config  — configuração do banco
          ai_key     — chave da API
          incluir    — lista de arquivos/pastas extras a incluir
        """
        opcoes = opcoes or {}

        if not os.path.exists(arquivo_dk):
            return f"❌ Arquivo '{arquivo_dk}' não encontrado"

        # Lê o código fonte
        with open(arquivo_dk, encoding='utf-8') as f:
            source_code = f.read()

        # Valida sintaxe
        try:
            from advak_lexer  import AdvakLexer
            from advak_parser import Parser
            tokens = AdvakLexer(source_code).tokenize()
            Parser(tokens).parse()
        except SyntaxError as e:
            return f"❌ Erro de sintaxe: {e}"

        nome_base = opcoes.get('nome') or os.path.splitext(os.path.basename(arquivo_dk))[0]
        pasta_saida = opcoes.get('saida', 'dist')
        gui_mode = opcoes.get('gui', False)
        unico = opcoes.get('unico', True)
        icone = opcoes.get('icone', None)
        db_config = opcoes.get('db_config', {})
        ai_key = opcoes.get('ai_key', os.environ.get('GROQ_API_KEY', os.environ.get('ANTHROPIC_API_KEY', '')))

        print(f"\n🔨 Advak Compiler 3.0")
        print(f"   Arquivo:    {arquivo_dk}")
        print(f"   Executável: {nome_base}")
        print(f"   Modo GUI:   {'sim' if gui_mode else 'não'}")
        print(f"   Arquivo único: {'sim' if unico else 'não'}")
        print()

        # Cria diretório temporário
        with tempfile.TemporaryDirectory() as tmpdir:
            # Gera o wrapper Python
            wrapper_path = os.path.join(tmpdir, f'{nome_base}_main.py')
            wrapper_code = WRAPPER_TEMPLATE.format(
                source_code=source_code,
                db_config=db_config,
                ai_key=ai_key,
            )
            with open(wrapper_path, 'w', encoding='utf-8') as f:
                f.write(wrapper_code)

            # Copia os módulos do Advak para o tmpdir
            modulos = [
                'advak_lexer.py', 'advak_parser.py',
                'advak_interpreter.py', 'advak_db.py',
                'advak_http.py', 'advak_gui.py', 'advak_gui_modern.py',
            ]
            for mod in modulos:
                src = os.path.join(BASE_DIR, mod)
                if os.path.exists(src):
                    shutil.copy(src, tmpdir)

            # Copia arquivos extras
            for extra in opcoes.get('incluir', []):
                if os.path.exists(extra):
                    dest = os.path.join(tmpdir, os.path.basename(extra))
                    if os.path.isdir(extra):
                        shutil.copytree(extra, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy(extra, dest)

            # Monta comando PyInstaller
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--noconfirm',
                '--name', nome_base,
                '--distpath', os.path.abspath(pasta_saida),
                '--workpath', os.path.join(tmpdir, 'build'),
                '--specpath', tmpdir,
            ]

            if unico:
                cmd.append('--onefile')
            else:
                cmd.append('--onedir')

            if gui_mode:
                cmd.append('--windowed')

            if icone and os.path.exists(icone):
                cmd += ['--icon', icone]

            # Adiciona módulos do Advak como dados
            for mod in modulos:
                mod_path = os.path.join(tmpdir, mod)
                if os.path.exists(mod_path):
                    cmd += ['--add-data', f'{mod_path}{os.pathsep}.']

            # Imports ocultos necessários
            hidden = ['psycopg2', 'json', 'asyncio', 'threading',
                      'http.server', 'urllib.parse', 'urllib.request',
                      'groq', 'matplotlib', 'tkinter']
            for h in hidden:
                cmd += ['--hidden-import', h]

            cmd.append(wrapper_path)

            print(f"⚙️  Compilando com PyInstaller...")
            if self.verbose:
                print(f"   Comando: {' '.join(cmd)}\n")

            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                cwd=tmpdir
            )

            if result.returncode != 0:
                error_msg = result.stderr[-2000:] if result.stderr else 'Erro desconhecido'
                return f"❌ Falha na compilação:\n{error_msg}"

        # Verifica o resultado
        sistema = sys.platform
        if sistema == 'win32':
            ext = '.exe'
        elif sistema == 'darwin':
            ext = '.app' if not unico else ''
        else:
            ext = ''

        if unico:
            executavel = os.path.join(pasta_saida, nome_base + ext)
        else:
            executavel = os.path.join(pasta_saida, nome_base)

        if os.path.exists(executavel):
            tamanho = self._tamanho_fmt(executavel)
            return (
                f"✅ Compilação concluída!\n"
                f"   Executável: {executavel}\n"
                f"   Tamanho:    {tamanho}\n"
                f"   Sistema:    {sistema}\n"
                f"\n   Para executar: {executavel}"
            )
        else:
            return f"⚠️  Processo concluiu mas executável não encontrado em {executavel}"

    def _tamanho_fmt(self, path):
        if os.path.isdir(path):
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, files in os.walk(path)
                for f in files
            )
        else:
            total = os.path.getsize(path)

        for unit in ['B', 'KB', 'MB', 'GB']:
            if total < 1024:
                return f"{total:.1f} {unit}"
            total /= 1024
        return f"{total:.1f} TB"

    def limpar(self, nome=None):
        """Remove arquivos temporários de compilação."""
        removidos = []
        for pasta in ['build', '__pycache__']:
            if os.path.exists(pasta):
                shutil.rmtree(pasta, ignore_errors=True)
                removidos.append(pasta)
        if nome:
            spec = f'{nome}.spec'
            if os.path.exists(spec):
                os.remove(spec)
                removidos.append(spec)
        return f"✅ Limpeza concluída: {removidos}" if removidos else "ℹ️  Nada para limpar"

    def info(self):
        """Informações sobre o ambiente de compilação."""
        try:
            import PyInstaller
            pi_ver = PyInstaller.__version__
        except ImportError:
            pi_ver = 'Não instalado'

        return {
            'pyinstaller':  pi_ver,
            'python':       sys.version.split()[0],
            'groq':         groq_ok,
            'plataforma':   sys.platform,
            'plataforma':   sys.platform,
            'arquitetura':  __import__('platform').machine(),
            'tkinter_ok':   'sim' if self._check_tkinter() else 'não (instale python3-tk)',
            'psycopg2_ok':  'sim' if self._check_psycopg2() else 'não (instale psycopg2-binary)',
        }

    def _check_tkinter(self):
        try:
            import tkinter
            return True
        except ImportError:
            return False

    def _check_psycopg2(self):
        try:
            import psycopg2
            return True
        except ImportError:
            return False


# ── Função de conveniência para o CLI ─────────────────────────────────────────

def cmd_compilar(arquivo_dk, opcoes=None):
    comp = AdvakCompiler()
    result = comp.compilar(arquivo_dk, opcoes)
    print(result)