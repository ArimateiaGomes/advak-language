#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
advak_linter.py — Verificador de código Advak 5.0
Detecta problemas antes de executar.

Uso:  advak --verificar arquivo.dk
      advak --verificar pasta/
"""
import re, sys, os
from pathlib import Path

# Palavras reservadas que não podem ser usadas como variáveis
RESERVADAS = {
    'seja','fixo','se','senão','senao','para','enquanto','retornar',
    'funcao','classe','herda','isso','super','verdadeiro','falso','nulo',
    'e','ou','nao','assincrona','aguarda','produzir','importar','exportar',
    'de','como','tentar','pegar','finalmente','lançar','lancar',
    'quebrar','continuar','combinar','caso','match',
    # NOTE: 'lista', 'entrada', 'onde', 'tipo' removidos das reservadas v5.1
}

# Padrões de problemas comuns
PROBLEMAS = [
    (r'\bseja\s+(seja|fixo|se|senão|para|enquanto|retornar|funcao|classe|combinar|caso)\s*=',
     "Palavra reservada usada como nome de variável"),
    (r'servidor\.get\(', "Use servidor.obter() em vez de servidor.get()"),
    (r'servidor\.post\(', "Use servidor.publicar() em vez de servidor.post()"),
    (r'servidor\.put\(', "Use servidor.atualizar() em vez de servidor.put()"),
    (r'servidor\.delete\(', "Use servidor.deletar() em vez de servidor.delete()"),
    (r'req\.query\.', "Use req.consulta. em vez de req.query."),
    (r'req\.params\.', "Use req.parametros. em vez de req.params."),
    (r'req\.json\.', "Use req.dados. em vez de req.json."),
    (r'json_resp\(', "Use resposta_json() em vez de json_resp()"),
    (r'side="(left|right|top|bottom)"', "Use lado='esquerda/direita/topo/fundo'"),
    (r'padx=', "Use espaco_x= em vez de padx="),
    (r'pady=', "Use espaco_y= em vez de pady="),
    (r'fill="(x|y|both)"', "Use preencher= em vez de fill="),
    (r'state="disabled"', "Use estado='desabilitado' em vez de state="),
    (r'anchor="(w|e|n|s)"', "Use ancora= em vez de anchor="),
    (r'\bprint\(', "Use imprimir() em vez de print()"),
    (r'\binput\(', "Use entrada() em vez de input()"),
]

class Linter:
    def __init__(self):
        self.erros    = []
        self.avisos   = []
        self.infos    = []

    def verificar_arquivo(self, caminho):
        self.erros   = []
        self.avisos  = []
        self.infos   = []
        
        try:
            with open(caminho, encoding='utf-8') as f:
                linhas = f.readlines()
        except Exception as e:
            self.erros.append((0, 0, f"Não foi possível abrir o arquivo: {e}"))
            return

        for num, linha in enumerate(linhas, 1):
            sem_comentario = re.sub(r'//.*$', '', linha)
            
            # Verifica padrões problemáticos
            for padrao, mensagem in PROBLEMAS:
                if re.search(padrao, sem_comentario):
                    self.avisos.append((num, 0, mensagem))
            
            # Backtick com aspas duplas em ${}
            if '`' in linha:
                expr = re.findall(r'\$\{([^}]+)\}', linha)
                for e in expr:
                    if '"' in e and ('?' in e or ':' in e):
                        self.avisos.append((num, 0,
                            'Ternário com aspas duplas em ${} pode causar erro. Use aspas simples.'))
            
            # Funções muito longas (>100 linhas)
            if re.match(r'\s*funcao\s+\w+', linha.strip()):
                self.infos.append((num, 0, "Função iniciada — verifique se não ficará muito longa (>100 linhas)"))
            
            # Variáveis não usadas (simplificado)
            m = re.match(r'\s*seja\s+(\w+)\s*=', sem_comentario)
            if m:
                nome = m.group(1)
                if nome in RESERVADAS:
                    self.erros.append((num, 0, f"Palavra reservada '{nome}' usada como variável"))

        return len(self.erros), len(self.avisos), len(self.infos)

    def relatorio(self, caminho):
        """Imprime relatório colorido."""
        VERM  = "\033[91m"; AMAREL = "\033[93m"; AZUL = "\033[94m"
        VERDE = "\033[92m"; CINZA  = "\033[90m"; R    = "\033[0m"
        NEG   = "\033[1m"
        
        nome = Path(caminho).name
        total = len(self.erros) + len(self.avisos)
        
        print(f"\n  {NEG}📋 {nome}{R}")
        print(f"  {'─'*50}")
        
        for ln, col, msg in self.erros:
            print(f"  {VERM}✖ ERRO{R}    linha {ln:4}: {msg}")
        
        for ln, col, msg in self.avisos:
            print(f"  {AMAREL}⚠ AVISO{R}   linha {ln:4}: {msg}")
        
        if not self.erros and not self.avisos:
            print(f"  {VERDE}✅ Nenhum problema encontrado!{R}")
        else:
            cor = VERM if self.erros else AMAREL
            print(f"\n  {cor}{len(self.erros)} erros, {len(self.avisos)} avisos{R}")
        
        return len(self.erros)

def verificar(caminho):
    """Ponto de entrada principal do linter."""
    caminho = Path(caminho)
    linter = Linter()
    
    if caminho.is_dir():
        arquivos = list(caminho.glob("**/*.dk"))
        print(f"\n  🔍 Verificando {len(arquivos)} arquivos em {caminho}/")
        total_erros = 0
        for arq in sorted(arquivos):
            linter.verificar_arquivo(arq)
            errs = linter.relatorio(arq)
            total_erros += errs
        print(f"\n  {'✅ Tudo OK!' if total_erros == 0 else f'Total: {total_erros} erros encontrados.'}")
        return total_erros
    
    elif caminho.suffix == '.dk':
        linter.verificar_arquivo(caminho)
        return linter.relatorio(caminho)
    
    else:
        print(f"  ❌ Arquivo inválido: {caminho} (precisa ser .dk)")
        return 1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(verificar(sys.argv[1]))
    else:
        print("Uso: advak --verificar arquivo.dk")
        sys.exit(1)
