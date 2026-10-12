#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
advak_formatador.py — Formatador automático de código Advak 5.0

Uso:  advak --formatar arquivo.dk          (formata e salva)
      advak --formatar arquivo.dk --ver    (mostra diff sem salvar)
"""
import re, sys
from pathlib import Path

class Formatador:
    """Formata código Advak aplicando estilo consistente."""
    
    INDENT = "    "  # 4 espaços

    def formatar(self, codigo):
        linhas = codigo.split('\n')
        resultado = []
        nivel = 0
        
        for linha in linhas:
            stripped = linha.strip()
            
            # Linha vazia
            if not stripped:
                # Máximo 2 linhas vazias consecutivas
                if resultado and resultado[-1] == '' and (len(resultado) < 2 or resultado[-2] == ''):
                    continue
                resultado.append('')
                continue
            
            # Comentário
            if stripped.startswith('//'):
                resultado.append(self.INDENT * nivel + stripped)
                continue
            
            # Fecha bloco ANTES de indentar
            if stripped.startswith('}'):
                nivel = max(0, nivel - stripped.count('}') + stripped.count('{'))
                nivel = max(0, nivel)
            
            # Linha formatada
            linha_fmt = self.INDENT * nivel + stripped
            
            # Normaliza espaços em operadores
            linha_fmt = self._normalizar_operadores(linha_fmt)
            
            resultado.append(linha_fmt)
            
            # Abre bloco DEPOIS
            aberturas = stripped.count('{') - stripped.count('}')
            if aberturas > 0:
                nivel += aberturas
        
        return '\n'.join(resultado)
    
    def _normalizar_operadores(self, linha):
        # Garante espaço em torno de = (não em == ou !=)
        # (o '.' fica de fora para não separar o intervalo ..= em ".. =")
        linha = re.sub(r'([^=!<>.])=([^=])', r'\1 = \2', linha)
        # Garante espaço após vírgula
        linha = re.sub(r',([^\s])', r', \1', linha)
        # Remove espaço duplo
        linha = re.sub(r'  +', ' ', linha)
        # Remove trailing whitespace
        linha = linha.rstrip()
        return linha
    
    def formatar_arquivo(self, caminho, ver=False):
        caminho = Path(caminho)
        if not caminho.exists():
            print(f"❌ Arquivo não encontrado: {caminho}")
            return False
        
        original = caminho.read_text(encoding='utf-8')
        formatado = self.formatar(original)
        
        if ver:
            # Mostra diff simplificado
            orig_linhas = original.split('\n')
            fmt_linhas  = formatado.split('\n')
            print(f"\n  📋 Diff de {caminho.name}:")
            for i, (o, f) in enumerate(zip(orig_linhas, fmt_linhas), 1):
                if o != f:
                    print(f"  L{i:4} - {o[:70]}")
                    print(f"  L{i:4} + {f[:70]}")
        else:
            caminho.write_text(formatado, encoding='utf-8')
            mudancas = sum(1 for a, b in zip(original.split('\n'), formatado.split('\n')) if a != b)
            print(f"  ✅ {caminho.name} formatado — {mudancas} linhas ajustadas")
        
        return True

def formatar(caminho, ver=False):
    f = Formatador()
    p = Path(caminho)
    if p.is_dir():
        for arq in sorted(p.glob("**/*.dk")):
            f.formatar_arquivo(arq, ver)
    else:
        f.formatar_arquivo(p, ver)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ver = '--ver' in sys.argv
        formatar(sys.argv[1], ver)
    else:
        print("Uso: advak --formatar arquivo.dk")
