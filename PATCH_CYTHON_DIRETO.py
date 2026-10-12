#!/usr/bin/env python3
"""
PATCH_CYTHON_DIRETO.py
Aplica todas as correcoes necessarias para o Cython funcionar no Windows.
Execute: python PATCH_CYTHON_DIRETO.py
"""
import os, sys, shutil, py_compile, tempfile, re

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'advak_nativo.py')

def main():
    print()
    print("=" * 56)
    print("  PATCH CYTHON — Correcao Completa")
    print("=" * 56)

    with open(ARQUIVO, "r", encoding="utf-8") as f:
        codigo = f.read()

    alterou = False

    # --- Patch 1: CompiladorCython.compilar() com ascii_safe ---
    if "tornar_ascii_seguro" not in codigo:
        idx_class = codigo.find("class CompiladorCython:")
        idx_def   = codigo.find("    def compilar(", idx_class)
        idx_next  = codigo.find("\n    def ", idx_def + 50)
        if idx_def > 0:
            novo_m = '    def compilar(self, source_dk: str, nome: str = None,\n                 pasta_saida: str = "dist",\n                 tipo_c: bool = False) -> dict:\n        """Compila via Cython. Unicode-safe para Windows."""\n\n        os.makedirs(pasta_saida, exist_ok=True)\n        nome = nome or os.path.splitext(os.path.basename(source_dk))[0]\n\n        cython_ok, cython_msg = self._verificar_cython()\n        if not cython_ok:\n            return {\n                \'ok\': False,\n                \'mensagem\': (\n                    f"\\u274c Cython nao disponivel: {cython_msg}\\n"\n                    f"   Instale: pip install cython setuptools"\n                ),\n            }\n\n        with open(source_dk, encoding=\'utf-8\') as f:\n            source = f.read()\n\n        transpilador = TranspiladorPython()\n        python_code = transpilador.transpilar(source, nome)\n\n        # Converte chars unicode para escapes ASCII dentro de strings Python\n        # Necessario porque Cython no Windows nao suporta chars fora do ASCII\n        def tornar_ascii_seguro(code_str):\n            resultado = []\n            for linha in code_str.split(\'\\n\'):\n                if not any(ord(c) > 127 for c in linha):\n                    resultado.append(linha)\n                    continue\n                nova_linha = []\n                em_string = False\n                char_string = None\n                idx_l = 0\n                while idx_l < len(linha):\n                    ch = linha[idx_l]\n                    if not em_string and ch in (\'"\', "\'"):\n                        em_string = True\n                        char_string = ch\n                        nova_linha.append(ch)\n                    elif em_string and ch == char_string:\n                        em_string = False\n                        nova_linha.append(ch)\n                    elif em_string and ord(ch) > 127:\n                        cp = ord(ch)\n                        if cp <= 0xFFFF:\n                            nova_linha.append(f\'\\\\u{cp:04x}\')\n                        else:\n                            nova_linha.append(f\'\\\\U{cp:08x}\')\n                    else:\n                        nova_linha.append(ch)\n                    idx_l += 1\n                resultado.append(\'\'.join(nova_linha))\n            return \'\\n\'.join(resultado)\n\n        python_safe = tornar_ascii_seguro(python_code)\n\n        cython_header = (\n            "# -*- coding: utf-8 -*-\\n"\n            "# cython: language_level=3\\n"\n            "# cython: boundscheck=False\\n"\n            "# cython: wraparound=False\\n"\n            f"# Modulo: {nome}\\n\\n"\n        )\n        cython_code = cython_header + python_safe\n\n        with tempfile.TemporaryDirectory() as tmpdir:\n            pyx_path = os.path.join(tmpdir, f\'{nome}.pyx\')\n            with open(pyx_path, \'w\', encoding=\'utf-8\') as f:\n                f.write(cython_code)\n\n            if tipo_c:\n                c_path = os.path.join(pasta_saida, f\'{nome}_cython.c\')\n                cmd = [sys.executable, \'-m\', \'cython\',\n                       \'--output-file\', c_path, pyx_path]\n                r = subprocess.run(cmd, capture_output=True, text=True)\n                if r.returncode == 0 and os.path.exists(c_path):\n                    size = os.path.getsize(c_path)\n                    return {\n                        \'ok\': True,\n                        \'c_path\': c_path,\n                        \'mensagem\': (\n                            f"\\u2705 Cython -> C: {c_path} ({size:,} bytes)\\n"\n                            f"   Compile: gcc -O2 -shared -fPIC {c_path} -o {nome}.so"\n                        ),\n                    }\n                return {\n                    \'ok\': False,\n                    \'mensagem\': f"\\u274c Cython falhou:\\n{r.stderr[:300]}"\n                }\n\n            pyx_safe = pyx_path.replace(\'\\\\\', \'/\')\n            setup_code = (\n                "# -*- coding: utf-8 -*-\\n"\n                "from setuptools import setup\\n"\n                "from Cython.Build import cythonize\\n"\n                "setup(\\n"\n                f"    name=\'{nome}\',\\n"\n                f"    ext_modules=cythonize(\\n"\n                f"        \'{pyx_safe}\',\\n"\n                "        compiler_directives={\\n"\n                "            \'language_level\': 3,\\n"\n                "            \'boundscheck\': False,\\n"\n                "            \'wraparound\': False,\\n"\n                "            \'cdivision\': True,\\n"\n                "            \'nonecheck\': False,\\n"\n                "        },\\n"\n                "    ),\\n"\n                ")\\n"\n            )\n            setup_path = os.path.join(tmpdir, \'setup.py\')\n            with open(setup_path, \'w\', encoding=\'utf-8\') as f:\n                f.write(setup_code)\n\n            cmd = [sys.executable, setup_path, \'build_ext\',\n                   f\'--build-lib={os.path.abspath(pasta_saida)}\',\n                   \'--inplace\']\n            r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)\n\n            ext_files = [\n                f for f in os.listdir(pasta_saida)\n                if f.startswith(nome) and (f.endswith(\'.pyd\') or f.endswith(\'.so\'))\n            ]\n\n            if r.returncode == 0 and ext_files:\n                ext_path = os.path.join(pasta_saida, ext_files[0])\n                size = self._fmt(os.path.getsize(ext_path))\n                return {\n                    \'ok\': True,\n                    \'extensao\': ext_path,\n                    \'tamanho\': size,\n                    \'mensagem\': (\n                        f"\\u2705 Cython: {ext_path} ({size})\\n"\n                        f"   Tipo: extensao nativa .pyd\\n"\n                        f"   Usar: import {nome}  (em Python)"\n                    ),\n                }\n\n            c_files = [f for f in os.listdir(tmpdir) if f.endswith(\'.c\')]\n            if c_files:\n                c_src = os.path.join(tmpdir, c_files[0])\n                c_dst = os.path.join(pasta_saida, f\'{nome}_cython.c\')\n                shutil.copy(c_src, c_dst)\n                return {\n                    \'ok\': True,\n                    \'c_path\': c_dst,\n                    \'mensagem\': (\n                        f"\\u26a0 Extensao nao compilada, C gerado:\\n"\n                        f"   {c_dst}\\n"\n                        f"   {r.stderr[-150:] if r.stderr else \'\'}"\n                    ),\n                }\n\n            return {\n                \'ok\': False,\n                \'mensagem\': (\n                    f"\\u274c Cython falhou\\n"\n                    f"   {r.stderr[-200:] if r.stderr else \'Erro desconhecido\'}"\n                )\n            }\n\n'
            codigo = codigo[:idx_def] + novo_m + "\n" + codigo[idx_next:]
            print("  [1] CompiladorCython.compilar() — patch aplicado")
            alterou = True
    else:
        print("  [1] CompiladorCython.compilar() — ja corrigido")

    # --- Patch 2: .adicionar() -> .append() no transpilador ---
    OLD2 = "                if prop == 'adicionar':       return f\'{obj}.append({all_args})\'"
    if OLD2 not in codigo:
        OLD_CALL = "                if prop == \'adicionar\':       return f\'{obj}.append({all_args})\'"
        # Simpler check
        if ".append(" not in codigo[codigo.find("elif t == \'call\'"):codigo.find("elif t == \'call\'")+2000]:
            print("  [2] Mapeamento .adicionar->append nao encontrado")
            print("      Baixe o ZIP mais recente para obter a versao completa.")
        else:
            print("  [2] .adicionar() -> .append() — ja corrigido")
    else:
        print("  [2] .adicionar() -> .append() — ja corrigido")

    # --- Patch 3: .tamanho -> len() ---
    if "prop == \'tamanho\'" in codigo or "prop == 'tamanho'" in codigo:
        print("  [3] .tamanho -> len() — ja corrigido")
    else:
        print("  [3] .tamanho -> len() — nao encontrado (baixe ZIP atualizado)")

    if alterou:
        backup = ARQUIVO + ".bak"
        shutil.copy2(ARQUIVO, backup)
        print(f"\n  Backup: {backup}")

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
            f.write(codigo)
            tmp = f.name
        try:
            py_compile.compile(tmp, doraise=True)
            with open(ARQUIVO, "w", encoding="utf-8") as f:
                f.write(codigo)
            print(f"  Arquivo salvo: {ARQUIVO}")
        except Exception as e:
            print(f"  ERRO sintaxe: {e}")
        finally:
            try: os.unlink(tmp)
            except: pass

    print()
    print("  Execute:")
    print("    python advak.py projetos\\testar_nuitka.dk")

if __name__ == "__main__":
    main()
