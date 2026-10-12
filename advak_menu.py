#!/usr/bin/env python3
"""
Advak 3.0 — Sistema de Menu e Ajuda Completa
Menu interativo com documentação completa da linguagem.
"""
import os, sys

CORES = {
    'reset':    '\033[0m',
    'bold':     '\033[1m',
    'dim':      '\033[2m',
    'verde':    '\033[32m',
    'amarelo':  '\033[33m',
    'azul':     '\033[34m',
    'magenta':  '\033[35m',
    'ciano':    '\033[36m',
    'branco':   '\033[97m',
    'vermelho': '\033[31m',
    'cinza':    '\033[90m',
    'bg_azul':  '\033[44m',
    'bg_verde': '\033[42m',
    'bg_preto': '\033[40m',
}

def c(cor, texto):
    return f"{CORES.get(cor,'')}{texto}{CORES['reset']}"

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def linha(char='═', largura=70, cor='azul'):
    return c(cor, char * largura)

def titulo(texto, cor='ciano'):
    pad = (70 - len(texto) - 4) // 2
    return (
        f"\n{linha()}\n"
        f"{c(cor, '║')}  {c('bold', c(cor, texto.center(64)))}  {c(cor, '║')}\n"
        f"{linha()}"
    )

def secao(texto, cor='amarelo'):
    return f"\n{c('bold', c(cor, f'  ▸ {texto}'))}"

def exemplo(codigo, descricao=''):
    linhas = codigo.strip().split('\n')
    resultado = ''
    if descricao:
        resultado += f"  {c('cinza', f'// {descricao}')}\n"
    for ln in linhas:
        resultado += f"  {c('verde', ln)}\n"
    return resultado

def cmd(nome, desc, cor='ciano'):
    return f"  {c(cor, nome.ljust(30))} {c('cinza', desc)}"


# ══════════════════════════════════════════════════════════════════════════════
#  CONTEÚDO DE CADA TÓPICO
# ══════════════════════════════════════════════════════════════════════════════

def tela_menu_principal():
    limpar_tela()
    print(c('ciano', r"""
 █████╗ ██████╗ ██╗   ██╗ █████╗ ██╗  ██╗
██╔══██╗██╔══██╗██║   ██║██╔══██╗██║ ██╔╝
███████║██║  ██║██║   ██║███████║█████╔╝
██╔══██║██║  ██║╚██╗ ██╔╝██╔══██║██╔═██╗
██║  ██║██████╔╝ ╚████╔╝ ██║  ██║██║  ██╗
╚═╝  ╚═╝╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝"""))
    print(c('bold', "  Advak Language v3.0") + c('cinza', "  —  Documentação Completa"))
    print(linha('─', 70, 'cinza'))
    print()
    print(c('bold', '  MENU PRINCIPAL') + c('cinza', ' — digite o número e pressione Enter'))
    print()

    itens = [
        ('1',  '📖', 'Introdução à Linguagem',     'O que é Advak, filosofia, primeiros passos'),
        ('2',  '🔤', 'Variáveis e Tipos',            'seja, fixo, tipos de dados, nulo'),
        ('3',  '⚡', 'Operadores',                   'Aritméticos, lógicos, pipeline |>, null ??'),
        ('4',  '🔁', 'Controle de Fluxo',            'se/senão, enquanto, para, quebrar'),
        ('5',  '⚙️', 'Funções',                      'função, lambda =>, parâmetros, retorno'),
        ('6',  '🏛️', 'Classes e Objetos',            'classe, herda, novo, isso, métodos'),
        ('7',  '📦', 'Listas e Mapas',               'Coleções, propriedades, iteração'),
        ('8',  '🎯', 'Match / Pattern Matching',     'combinar, caso, padrão'),
        ('9',  '🛡️', 'Tratamento de Erros',          'tentar, capturar, finalmente, lançar'),
        ('10', '🗄️', 'Banco de Dados (PostgreSQL)',  'banco.*, CRUD, tabelas, SQL puro'),
        ('11', '🤖', 'IA Nativa',                    'ai_perguntar, ai_classificar, ai_gerar...'),
        ('12', '📚', 'Biblioteca Padrão',            'Mat, Texto, Lista, Arquivo, JSON, OS'),
        ('13', '💻', 'Comandos do REPL',             'Todos os comandos :comando'),
        ('14', '🚀', 'Exemplos Completos',           'Programas prontos para executar'),
        ('15', '⌨️', 'Referência Rápida',            'Cheatsheet — tudo em uma página'),
        ('0',  '🚪', 'Voltar ao REPL',               ''),
    ]

    for num, ico, nome, desc in itens:
        n    = c('bold', c('amarelo', num.rjust(3)))
        i    = ico
        nm   = c('branco', nome)
        ds   = c('cinza', f'  {desc}') if desc else ''
        print(f"  {n}  {i}  {nm}{ds}")

    print()
    print(linha('─', 70, 'cinza'))
    print(c('cinza', "  Dica: dentro de qualquer tela, pressione Enter para voltar ao menu"))
    print()


# ── 1. Introdução ─────────────────────────────────────────────────────────────
def tela_introducao():
    limpar_tela()
    print(titulo('📖  INTRODUÇÃO À LINGUAGEM ADVAK'))
    print(f"""
{secao('O que é Advak?')}

  Advak é uma linguagem de programação moderna com sintaxe em português
  brasileiro. Foi criada para ser expressiva, legível e poderosa, com
  integração nativa com PostgreSQL e IA (Claude/Anthropic).

  Extensão dos arquivos: {c('verde', '.dk')}
  Versão atual:          {c('verde', '3.0')}
  Paradigma:             {c('verde', 'Multi-paradigma (imperativo, funcional, OO)')}

{secao('Filosofia')}

  ✦ Código em português — mais natural para falantes PT-BR
  ✦ Banco de dados como cidadão de primeira classe
  ✦ IA nativa integrada — sem libs externas
  ✦ Simples de aprender, poderoso para produção

{secao('Instalação e uso')}

{exemplo('''# Instalar dependência do banco
pip install psycopg2-binary

# Executar um arquivo
python advak.py run meu_programa.dk

# Executar com banco de dados
python advak.py run meu_programa.dk --db

# REPL interativo
python advak.py

# Criar novo projeto
python advak.py new meu-projeto

# Verificar sintaxe
python advak.py check arquivo.dk''')}

{secao('Primeiro programa')}

{exemplo('''// meu_primeiro.dk
seja nome = entrada("Qual seu nome? ");
imprimir(`Olá, ${nome}! Bem-vindo ao Advak 3.0 🚀`);

seja resultado = 2 ** 10;
imprimir(`2 elevado a 10 = ${resultado}`);''', 'salve como meu_primeiro.dk e execute')}

{secao('Configuração do banco (variáveis de ambiente)')}

{exemplo('''# Windows
set ADVAK_DB_HOST=localhost
set ADVAK_DB_USER=postgres
set ADVAK_DB_PASS=sua_senha
set ADVAK_DB_NAME=postgres

# Linux/Mac
export ADVAK_DB_HOST=localhost
export ADVAK_DB_USER=postgres
export ADVAK_DB_PASS=sua_senha
export ADVAK_DB_NAME=postgres

# IA nativa
set ANTHROPIC_API_KEY=sk-ant-...''')}
""")


# ── 2. Variáveis e Tipos ──────────────────────────────────────────────────────
def tela_variaveis():
    limpar_tela()
    print(titulo('🔤  VARIÁVEIS E TIPOS DE DADOS'))
    print(f"""
{secao('Declaração de variáveis')}

{exemplo('''seja nome    = "Arimatea";     // variável mutável
fixo  PI     = 3.14159;        // constante (não pode mudar)
seja  ativo  = verdadeiro;     // booleano
seja  pontos = 0;              // número inteiro
seja  preco  = 19.99;          // número decimal
seja  vazio  = nulo;           // valor nulo''')}

{secao('Tipos de dados')}

  {c('amarelo', 'Tipo')}          {c('amarelo', 'Exemplo')}                {c('amarelo', 'Descrição')}
  {c('cinza','─'*65)}
  {c('ciano','inteiro')}       {c('verde', 'seja x = 42')}               Número inteiro
  {c('ciano','decimal')}       {c('verde', 'seja y = 3.14')}             Número com ponto flutuante
  {c('ciano','texto')}         {c('verde', 'seja s = "olá"')}            Cadeia de caracteres
  {c('ciano','booleano')}      {c('verde', 'seja ok = verdadeiro')}      verdadeiro ou falso
  {c('ciano','lista')}         {c('verde', 'seja l = [1, 2, 3]')}        Coleção ordenada
  {c('ciano','mapa')}          {c('verde', 'seja m = {{a: 1}}')}          Chave → valor
  {c('ciano','nulo')}          {c('verde', 'seja n = nulo')}             Ausência de valor
  {c('ciano','função')}        {c('verde', 'seja f = (x) => x * 2')}    Função como valor

{secao('Strings e interpolação')}

{exemplo('''seja cidade = "Arraial";
seja uf     = "PI";

// String normal com aspas duplas
seja msg1 = "Cidade: " + cidade;

// Template string com backtick (interpolação)
seja msg2 = `Cidade: ${cidade} - ${uf}`;

// Expressões dentro de template string
seja preco  = 29.9;
seja qtd    = 3;
seja total  = `Total: R$ ${preco * qtd}`;

imprimir(msg2);   // Cidade: Arraial - PI
imprimir(total);  // Total: R$ 89.7''')}

{secao('Verificação de nulo com ??')}

{exemplo('''seja nome = nulo;
seja exibir = nome ?? "Visitante";
imprimir(exibir);  // Visitante

seja config = nulo;
seja porta  = config ?? 8080;
imprimir(porta);   // 8080''')}

{secao('Conversão de tipos')}

{exemplo('''seja n = numero("42");      // "42" → 42
seja t = texto(100);          // 100  → "100"
seja b = booleano(1);         // 1    → verdadeiro
seja b2= booleano("");        // ""   → falso (vazio = falso)''')}
""")


# ── 3. Operadores ─────────────────────────────────────────────────────────────
def tela_operadores():
    limpar_tela()
    print(titulo('⚡  OPERADORES'))
    print(f"""
{secao('Aritméticos')}

{exemplo('''seja a = 10, b = 3;

imprimir(a + b);    // 13  — soma
imprimir(a - b);    // 7   — subtração
imprimir(a * b);    // 30  — multiplicação
imprimir(a / b);    // 3.33.. — divisão
imprimir(a % b);    // 1   — módulo (resto)
imprimir(a ** b);   // 1000 — potência (10³)''')}

{secao('Comparação')}

{exemplo('''imprimir(5 == 5);    // verdadeiro
imprimir(5 != 3);    // verdadeiro
imprimir(5 > 3);     // verdadeiro
imprimir(5 >= 5);    // verdadeiro
imprimir(3 < 5);     // verdadeiro
imprimir(3 <= 4);    // verdadeiro
imprimir(5 === 5);   // verdadeiro (valor e tipo)
imprimir(5 !== "5"); // verdadeiro (tipos diferentes)''')}

{secao('Lógicos')}

{exemplo('''imprimir(verdadeiro && falso);  // falso  — E lógico
imprimir(verdadeiro || falso);  // verdadeiro — OU lógico
imprimir(!verdadeiro);          // falso  — NÃO lógico

// Curto-circuito
seja nome = "" || "Anônimo";     // "Anônimo"
seja conf = nulo && "ignorado";  // nulo''')}

{secao('Atribuição composta')}

{exemplo('''seja x = 10;
x += 5;   // x = 15
x -= 3;   // x = 12
x *= 2;   // x = 24
x /= 4;   // x = 6
x **= 2;  // x = 36
x %= 10;  // x = 6''')}

{secao('Pipeline |> (encadeamento funcional)')}

{exemplo('''seja dobrar  = (x) => x * 2;
seja somar10 = (x) => x + 10;
seja texto_  = (x) => `Resultado: ${x}`;

// Sem pipeline — difícil de ler
seja r1 = texto_(somar10(dobrar(5)));

// Com pipeline — fluxo da esquerda para direita
seja r2 = 5 |> dobrar |> somar10 |> texto_;

imprimir(r2);  // Resultado: 20''')}

{secao('Null Coalesce ?? e Optional Chaining ?.')}

{exemplo('''seja usuario = nulo;
imprimir(usuario ?? "sem usuário");  // sem usuário

seja obj = {{nome: "Ana", endereco: nulo}};
imprimir(obj?.nome);        // Ana
imprimir(obj?.telefone);    // nulo (não gera erro)
imprimir(obj?.endereco?.rua ?? "sem endereço");''')}
""")


# ── 4. Controle de Fluxo ──────────────────────────────────────────────────────
def tela_controle():
    limpar_tela()
    print(titulo('🔁  CONTROLE DE FLUXO'))
    print(f"""
{secao('Condicional — se / senão')}

{exemplo('''seja nota = 75;

se (nota >= 70) {
    imprimir("Aprovado! ✅");
} senão se (nota >= 50) {
    imprimir("Recuperação ⚠️");
} senão {
    imprimir("Reprovado ❌");
}''')}

{secao('Operador ternário')}

{exemplo('''seja idade = 20;
seja status = (idade >= 18) ? "maior" : "menor";
imprimir(status);  // maior''')}

{secao('Enquanto — laço com condição')}

{exemplo('''seja i = 1;
enquanto (i <= 5) {
    imprimir(`Contagem: ${i}`);
    i += 1;
}''')}

{secao('Para — laço com índice')}

{exemplo('''// Laço clássico
para (seja i = 0; i < 5; i += 1) {
    imprimir(`i = ${i}`);
}

// Laço sobre lista (for-in)
seja frutas = ["maçã", "banana", "uva"];
para (fruta em frutas) {
    imprimir(`Fruta: ${fruta}`);
}

// Laço sobre mapa
seja pessoa = {{nome: "Ana", cidade: "Arraial"}};
para (chave em pessoa) {
    imprimir(`${chave} = ${pessoa[chave]}`);
}''')}

{secao('Quebrar e Continuar')}

{exemplo('''// quebrar — sai do laço
para (seja i = 0; i < 10; i += 1) {
    se (i == 5) { quebrar; }
    imprimir(i);  // imprime 0,1,2,3,4
}

// continuar — pula para próxima iteração
para (seja i = 0; i < 5; i += 1) {
    se (i == 2) { continuar; }
    imprimir(i);  // imprime 0,1,3,4
}''')}
""")


# ── 5. Funções ────────────────────────────────────────────────────────────────
def tela_funcoes():
    limpar_tela()
    print(titulo('⚙️  FUNÇÕES'))
    print(f"""
{secao('Declaração de função')}

{exemplo('''função saudar(nome) {
    retornar `Olá, ${nome}!`;
}

imprimir(saudar("Arimatea"));  // Olá, Arimatea!''')}

{secao('Parâmetros com valor padrão')}

{exemplo('''função potencia(base, expoente = 2) {
    retornar base ** expoente;
}

imprimir(potencia(3));     // 9  (3²)
imprimir(potencia(2, 10)); // 1024''')}

{secao('Parâmetros rest (...)')}

{exemplo('''função somar(...numeros) {
    seja total = 0;
    para (n em numeros) {
        total += n;
    }
    retornar total;
}

imprimir(somar(1, 2, 3, 4, 5));  // 15''')}

{secao('Funções lambda (arrow) =>')}

{exemplo('''// Sintaxe curta — expressão direta
seja dobrar   = (x) => x * 2;
seja somar    = (a, b) => a + b;
seja cumprimentar = (n) => `Oi, ${n}!`;

// Sintaxe com bloco
seja fatorial = (n) => {
    se (n <= 1) { retornar 1; }
    retornar n * fatorial(n - 1);
};

imprimir(dobrar(7));         // 14
imprimir(somar(5, 3));       // 8
imprimir(fatorial(5));       // 120''')}

{secao('Funções de ordem superior')}

{exemplo('''função aplicar(fn, valor) {
    retornar fn(valor);
}

seja triplicar = (x) => x * 3;
imprimir(aplicar(triplicar, 4));  // 12

// Função que retorna função (closure)
função multiplicador(fator) {
    retornar (x) => x * fator;
}

seja vezes5 = multiplicador(5);
seja vezes10 = multiplicador(10);
imprimir(vezes5(6));    // 30
imprimir(vezes10(6));   // 60''')}

{secao('Funções assíncronas')}

{exemplo('''função async buscarDados(id) {
    seja resultado = aguarda banco.buscar_id("usuarios", id);
    retornar resultado;
}

// Com IA
função async analisar(texto) {
    seja analise = aguarda ai_perguntar(`Analise: ${texto}`);
    retornar analise;
}''')}
""")


# ── 6. Classes ────────────────────────────────────────────────────────────────
def tela_classes():
    limpar_tela()
    print(titulo('🏛️  CLASSES E OBJETOS'))
    print(f"""
{secao('Declaração de classe')}

{exemplo('''classe Pessoa {
    construtor(nome, idade) {
        isso.nome  = nome;
        isso.idade = idade;
    }

    apresentar() {
        retornar `Sou ${isso.nome}, ${isso.idade} anos`;
    }

    ehAdulto() {
        retornar isso.idade >= 18;
    }
}

seja p = novo Pessoa("Ana", 25);
imprimir(p.apresentar());    // Sou Ana, 25 anos
imprimir(p.ehAdulto());      // verdadeiro''')}

{secao('Herança com herda')}

{exemplo('''classe Animal {
    construtor(nome) {
        isso.nome = nome;
    }
    falar() {
        retornar `${isso.nome} faz um som`;
    }
}

classe Cachorro herda Animal {
    construtor(nome, raca) {
        isso.nome = nome;
        isso.raca = raca;
    }
    falar() {
        retornar `${isso.nome} diz: Au Au!`;
    }
    info() {
        retornar `${isso.nome} — Raça: ${isso.raca}`;
    }
}

seja dog = novo Cachorro("Rex", "Labrador");
imprimir(dog.falar());  // Rex diz: Au Au!
imprimir(dog.info());   // Rex — Raça: Labrador''')}

{secao('Classe com banco de dados')}

{exemplo('''classe RepositorioUsuario {
    construtor() {
        isso.tabela = "usuarios";
    }

    buscarTodos() {
        retornar banco.buscar(isso.tabela).ordenar("nome").executar();
    }

    buscarPorEmail(email) {
        retornar banco.buscar(isso.tabela)
            .onde("email = %s", email)
            .primeiro();
    }

    salvar(dados) {
        retornar banco.inserir(isso.tabela, dados);
    }

    atualizar(id, dados) {
        retornar banco.atualizar(isso.tabela, dados)
            .onde("id = %s", id)
            .executar();
    }
}

seja repo = novo RepositorioUsuario();
seja usuarios = repo.buscarTodos();
imprimir(`Total: ${usuarios.tamanho}`);''')}
""")


# ── 7. Listas e Mapas ─────────────────────────────────────────────────────────
def tela_colecoes():
    limpar_tela()
    print(titulo('📦  LISTAS E MAPAS'))
    print(f"""
{secao('Listas')}

{exemplo('''seja nums = [10, 20, 30, 40, 50];

// Acessar
imprimir(nums[0]);           // 10
imprimir(nums.tamanho);      // 5
imprimir(nums.primeiro);     // 10
imprimir(nums.ultimo);       // 50

// Modificar
nums.adicionar(60);          // adiciona no final
nums.remover();              // remove o último
nums.ordenar();              // ordena no lugar
nums.inverter();             // inverte

// Iterar
para (n em nums) {
    imprimir(n);
}

// Métodos funcionais
seja dobrados = nums.map((x) => x * 2);
seja pares    = nums.filtrar((x) => x % 2 == 0);
seja primeiro = nums.find((x) => x > 25);

imprimir(dobrados);   // [20, 40, 60, 80, 100]
imprimir(pares);      // [10, 20, 30, 40, 50]
imprimir(primeiro);   // 30''')}

{secao('Mapas (objetos)')}

{exemplo('''seja produto = {
    nome:     "Notebook",
    preco:    2999.99,
    estoque:  15,
    ativo:    verdadeiro
};

// Acessar
imprimir(produto.nome);          // Notebook
imprimir(produto["preco"]);      // 2999.99

// Modificar
produto.estoque = 14;
produto.desconto = 0.1;

// Iterar chaves
para (chave em produto) {
    imprimir(`${chave}: ${produto[chave]}`);
}''')}

{secao('Lista de mapas — padrão de tabela')}

{exemplo('''seja alunos = [
    {{nome: "Ana",   nota: 9.5}},
    {{nome: "Bob",   nota: 7.2}},
    {{nome: "Carla", nota: 8.8}}
];

// Filtrar aprovados
seja aprovados = alunos.filtrar((a) => a.nota >= 7.0);

// Imprimir
para (a em aprovados) {
    imprimir(`${a.nome}: ${a.nota}`);
}

// Ordenar por nota (usando Lista.ordenar)
seja ranking = Lista.ordenar(alunos);''')}

{secao('Spread e desestruturação')}

{exemplo('''// Spread em lista
seja a = [1, 2, 3];
seja b = [4, 5, 6];
seja c = [...a, ...b];   // [1,2,3,4,5,6]

// Spread em mapa
seja base = {{ativo: verdadeiro, criado: "hoje"}};
seja usuario = {{...base, nome: "Ana", email: "ana@x.com"}};''')}
""")


# ── 8. Match ──────────────────────────────────────────────────────────────────
def tela_match():
    limpar_tela()
    print(titulo('🎯  MATCH / PATTERN MATCHING'))
    print(f"""
{secao('Sintaxe básica')}

{exemplo('''seja dia = 3;

combinar(dia) {
    caso 1: imprimir("Segunda-feira"); quebrar;
    caso 2: imprimir("Terça-feira");   quebrar;
    caso 3: imprimir("Quarta-feira");  quebrar;
    caso 4: imprimir("Quinta-feira");  quebrar;
    caso 5: imprimir("Sexta-feira");   quebrar;
    padrão: imprimir("Fim de semana");
}''')}

{secao('Match com retorno em função')}

{exemplo('''função classificar(nota) {
    combinar(verdadeiro) {
        caso nota >= 90: retornar "🏆 Excelente";
        caso nota >= 70: retornar "✅ Aprovado";
        caso nota >= 50: retornar "⚠️  Recuperação";
        padrão:          retornar "❌ Reprovado";
    }
}

seja notas = [95, 78, 55, 32];
para (n em notas) {
    imprimir(`${n} → ${classificar(n)}`);
}''')}

{secao('Match com strings')}

{exemplo('''seja comando = "criar";

combinar(comando) {
    caso "criar":  imprimir("Criando recurso...");
    caso "listar": imprimir("Listando recursos...");
    caso "apagar": imprimir("Apagando recurso...");
    padrão:        imprimir(`Comando desconhecido: ${comando}`);
}''')}

{secao('Match combinado com banco')}

{exemplo('''função processarAcao(acao, tabela, dados) {
    combinar(acao) {
        caso "inserir":
            retornar banco.inserir(tabela, dados);
        caso "atualizar":
            retornar banco.atualizar(tabela, dados)
                .onde("id = %s", dados.id).executar();
        caso "deletar":
            retornar banco.deletar(tabela)
                .onde("id = %s", dados.id).executar();
        padrão:
            lançar `Ação inválida: ${acao}`;
    }
}''')}
""")


# ── 9. Erros ──────────────────────────────────────────────────────────────────
def tela_erros():
    limpar_tela()
    print(titulo('🛡️  TRATAMENTO DE ERROS'))
    print(f"""
{secao('tentar / capturar / finalmente')}

{exemplo('''tentar {
    seja resultado = 10 / 0;
    imprimir(resultado);
} capturar (erro) {
    imprimir(`❌ Erro: ${erro}`);
} finalmente {
    imprimir("Isso sempre executa");
}''')}

{secao('Lançar erros')}

{exemplo('''função dividir(a, b) {
    se (b == 0) {
        lançar "Divisão por zero não é permitida!";
    }
    retornar a / b;
}

tentar {
    imprimir(dividir(10, 2));   // 5
    imprimir(dividir(10, 0));   // lança erro
} capturar (e) {
    imprimir(`Capturado: ${e}`);
}''')}

{secao('Erros com banco de dados')}

{exemplo('''função salvarUsuario(dados) {
    tentar {
        seja novo = banco.inserir("usuarios", dados);
        imprimir(`✅ Usuário criado: ID ${novo.id}`);
        retornar novo;
    } capturar (erro) {
        se (Texto.contem(erro, "unique")) {
            imprimir("❌ Email já cadastrado!");
        } senão {
            imprimir(`❌ Erro ao salvar: ${erro}`);
        }
        retornar nulo;
    }
}

salvarUsuario({{nome: "Ana", email: "ana@email.com"}});''')}

{secao('Transação com rollback automático')}

{exemplo('''função transferirSaldo(de_id, para_id, valor) {
    tentar {
        banco.iniciar();

        seja de = banco.buscar_id("contas", de_id);
        se (de.saldo < valor) {
            lançar "Saldo insuficiente";
        }

        banco.atualizar("contas", {{saldo: de.saldo - valor}})
            .onde("id = %s", de_id).executar();

        banco.atualizar("contas", {{saldo: de.saldo + valor}})
            .onde("id = %s", para_id).executar();

        banco.confirmar();
        imprimir("✅ Transferência realizada");

    } capturar (erro) {
        banco.reverter();
        imprimir(`❌ Falha — revertido: ${erro}`);
    }
}''')}
""")


# ── 10. Banco de Dados ────────────────────────────────────────────────────────
def tela_banco():
    limpar_tela()
    print(titulo('🗄️  BANCO DE DADOS — POSTGRESQL'))
    print(f"""
{secao('Conexão e seleção de banco')}

{exemplo('''// Conectar ao banco
banco.usar("postgres");          // usa banco existente
banco.criar_banco("minha_app");  // cria novo banco
banco.usar("minha_app");         // muda para ele

// Listar bancos disponíveis
seja dbs = banco.listar_bancos();
para (db em dbs) { imprimir(db); }''')}

{secao('Tipos de campo para criar tabelas')}

    {c('amarelo', 'Tipo Advak')}     {c('amarelo', 'PostgreSQL')}          {c('amarelo', 'Uso')}
    {c('cinza','─'*62)}
    {c('verde','autonum')}      SERIAL PRIMARY KEY   Chave primária auto-incremento
    {c('verde','inteiro')}      INTEGER              Números inteiros
    {c('verde','decimal')}      NUMERIC(15,2)        Valores monetários
    {c('verde','flutuante')}    FLOAT                Ponto flutuante
    {c('verde','grande')}       BIGINT               Inteiros muito grandes
    {c('verde','texto')}        TEXT                 Texto sem limite
    {c('verde','varchar')}      VARCHAR(255)         Texto com limite
    {c('verde','booleano')}     BOOLEAN              verdadeiro/falso
    {c('verde','data')}         DATE                 Apenas data
    {c('verde','datahora')}     TIMESTAMP DEFAULT NOW() Data e hora
    {c('verde','json')}         JSONB                Dados JSON indexados
    {c('verde','ref')}          INTEGER + FK         Chave estrangeira

{secao('Modificadores de campo')}

    {c('verde','obrigatorio')}  — NOT NULL
    {c('verde','unico')}        — UNIQUE
    {c('verde','padrao X')}     — DEFAULT X
    {c('verde','indice')}       — cria índice na coluna

{secao('Criar tabela completa')}

{exemplo('''banco.tabela("produtos", {
    "id":        "autonum",
    "nome":      "texto obrigatorio",
    "codigo":    "varchar unico obrigatorio",
    "preco":     "decimal obrigatorio",
    "estoque":   "inteiro padrao 0",
    "categoria": "texto",
    "ativo":     "booleano padrao verdadeiro",
    "imagem":    "texto",
    "criado":    "datahora",
    "fornecedor_id": "ref fornecedores"
});''')}

{secao('CRUD completo')}

{exemplo('''// CREATE — Inserir
seja prod = banco.inserir("produtos", {
    "nome": "Notebook", "preco": 2999.99, "codigo": "NB001"
});
imprimir(`Inserido ID: ${prod.id}`);

// READ — Buscar
seja todos    = banco.buscar("produtos").executar();
seja caros    = banco.buscar("produtos")
    .onde("preco > %s", 1000)
    .ordenar("preco", "DESC")
    .limite(10)
    .executar();
seja um = banco.buscar_id("produtos", 1);

// UPDATE — Atualizar
banco.atualizar("produtos", {{"preco": 2799.99}})
    .onde("id = %s", 1)
    .executar();

// DELETE — Deletar
banco.deletar("produtos")
    .onde("id = %s", 1)
    .executar();''')}

{secao('Consultas avançadas')}

{exemplo('''// Paginação
seja pagina1 = banco.buscar("produtos").pagina(1, 10).executar();
seja pagina2 = banco.buscar("produtos").pagina(2, 10).executar();

// Contar
seja total = banco.buscar("produtos").contar();
seja ativos = banco.buscar("produtos").onde("ativo = %s", verdadeiro).contar();

// SQL puro para consultas complexas
seja relatorio = banco.sql("""
    SELECT c.nome, COUNT(p.id) as total, SUM(p.valor) as receita
    FROM clientes c
    LEFT JOIN pedidos p ON c.id = p.cliente_id
    GROUP BY c.nome
    ORDER BY receita DESC
    LIMIT 10
""");

// Migração (adiciona colunas novas sem apagar dados)
banco.migrar("produtos", {{"peso": "decimal", "dimensoes": "texto"}});''')}
""")


# ── 11. IA Nativa ─────────────────────────────────────────────────────────────
def tela_ia():
    limpar_tela()
    print(titulo('🤖  IA NATIVA INTEGRADA'))
    print(f"""
{secao('Configuração')}

{exemplo('''# Defina a variável de ambiente antes de executar
# Windows:
set ANTHROPIC_API_KEY=sk-ant-api03-...

# Linux/Mac:
export ANTHROPIC_API_KEY=sk-ant-api03-...''')}

{secao('Funções de IA disponíveis')}

    {c('verde', 'ai_perguntar(prompt)')}
    Faz uma pergunta livre para a IA e retorna a resposta.

    {c('verde', 'ai_classificar(texto, categorias)')}
    Classifica texto em uma das categorias fornecidas.

    {c('verde', 'ai_transformar(dados, instrucao)')}
    Transforma/reescreve dados conforme a instrução.

    {c('verde', 'ai_resumir(texto)')}
    Resume um texto de forma concisa em português.

    {c('verde', 'ai_gerar(instrucao)')}
    Gera conteúdo criativo conforme instrução.

{secao('Exemplos práticos')}

{exemplo('''// 1. Pergunta livre
seja resposta = ai_perguntar("O que é recursão em programação?");
imprimir(resposta);

// 2. Classificação de sentimento
seja texto = "Adorei o produto, chegou rápido!";
seja sentimento = ai_classificar(texto, ["positivo", "negativo", "neutro"]);
imprimir(`Sentimento: ${sentimento}`);

// 3. Transformação de texto
seja informal = "oi tudo bem cara, queria saber se vcs entregam";
seja formal   = ai_transformar(informal, "Reescreva de forma profissional");
imprimir(formal);

// 4. Resumo
seja artigo = entrada("Cole o texto para resumir: ");
seja resumo = ai_resumir(artigo);
imprimir(`Resumo: ${resumo}`);

// 5. Geração de conteúdo
seja descricao = ai_gerar("Escreva uma descrição de produto para um notebook gamer");
imprimir(descricao);''')}

{secao('IA + Banco de dados')}

{exemplo('''// Classifica e salva feedbacks automaticamente
seja feedbacks = banco.buscar("feedbacks")
    .onde("categoria IS NULL")
    .executar();

para (f em feedbacks) {
    seja cat = ai_classificar(f.texto,
        ["elogio", "reclamacao", "sugestao", "duvida"]);

    banco.atualizar("feedbacks", {{"categoria": cat}})
        .onde("id = %s", f.id)
        .executar();

    imprimir(`#${f.id} → ${cat}`);
}
imprimir("✅ Feedbacks classificados com IA!");''')}
""")


# ── 12. Biblioteca Padrão ─────────────────────────────────────────────────────
def tela_stdlib():
    limpar_tela()
    print(titulo('📚  BIBLIOTECA PADRÃO'))
    print(f"""
{secao('Mat — Matemática')}

{exemplo('''imprimir(Mat.pi);              // 3.14159...
imprimir(Mat.raiz(16));        // 4.0
imprimir(Mat.abs(-5));         // 5
imprimir(Mat.piso(3.7));       // 3
imprimir(Mat.teto(3.2));       // 4
imprimir(Mat.arred(3.567, 2)); // 3.57
imprimir(Mat.max(5, 10, 3));   // 10
imprimir(Mat.min(5, 10, 3));   // 3
imprimir(Mat.pot(2, 8));       // 256
imprimir(Mat.log(Mat.e));      // 1.0
imprimir(Mat.aleatorio());     // 0.0 a 1.0
imprimir(Mat.inteiro_aleatorio(1, 100)); // 1 a 100''')}

{secao('Texto — Manipulação de strings')}

{exemplo('''seja s = "  Olá, Mundo!  ";
imprimir(Texto.tamanho(s));            // 15
imprimir(Texto.maiusculo(s));          // "  OLÁ, MUNDO!  "
imprimir(Texto.minusculo(s));          // "  olá, mundo!  "
imprimir(Texto.aparar(s));             // "Olá, Mundo!"
imprimir(Texto.substituir(s,"Mundo","Advak")); // "Olá, Advak!"
imprimir(Texto.dividir("a,b,c", ",")); // ["a","b","c"]
imprimir(Texto.contem(s, "Mundo"));    // verdadeiro
imprimir(Texto.começa(s, "  Olá"));    // verdadeiro''')}

{secao('Lista — Operações em coleções')}

{exemplo('''seja nums = Lista.intervalo(1, 6);   // [1,2,3,4,5]
seja pares = Lista.filtrar(nums, (x) => x % 2 == 0); // [2,4]
seja dobros= Lista.map(nums, (x) => x * 2);  // [2,4,6,8,10]
seja texto = Lista.unir(nums, ", ");  // "1, 2, 3, 4, 5"
seja ord   = Lista.ordenar(nums, verdadeiro); // [5,4,3,2,1]
seja unico = Lista.unico([1,2,2,3,3,3]);      // [1,2,3]''')}

{secao('Arquivo — Sistema de arquivos')}

{exemplo('''// Ler arquivo
seja conteudo = Arquivo.ler("dados.txt");
imprimir(conteudo);

// Escrever arquivo
Arquivo.escrever("saida.txt", "Conteúdo do arquivo");

// Verificar se existe
se (Arquivo.existe("config.json")) {
    seja config = JSON.parse(Arquivo.ler("config.json"));
}

// Listar diretório
seja arquivos = Arquivo.listar(".");
para (a em arquivos) { imprimir(a); }

// Criar diretório
Arquivo.criar_dir("minha_pasta");''')}

{secao('JSON — Serialização')}

{exemplo('''seja dados = {{nome: "Ana", idade: 25, ativo: verdadeiro}};

// Objeto → string JSON
seja json_str = JSON.stringify(dados);
imprimir(json_str);  // {"nome":"Ana","idade":25,"ativo":true}

// String JSON → objeto
seja obj = JSON.parse(json_str);
imprimir(obj.nome);  // Ana

// Formatado (indentado)
imprimir(JSON.formatar(dados));''')}

{secao('OS — Sistema operacional')}

{exemplo('''// Variável de ambiente
seja api_key = OS.env("ANTHROPIC_API_KEY", "não definida");

// Executar comando do sistema
OS.executar("echo Olá do sistema");

// Diretório atual
imprimir(OS.pwd());

// Argumentos da linha de comando
seja args = OS.args;
para (a em args) { imprimir(a); }''')}
""")


# ── 13. Comandos do REPL ──────────────────────────────────────────────────────
def tela_repl_cmds():
    limpar_tela()
    print(titulo('💻  COMANDOS DO REPL'))
    print(f"""
{secao('Iniciar o REPL')}

{exemplo('''# REPL simples
python advak.py

# REPL com banco conectado automaticamente
python advak.py --db

# REPL direto
python advak_repl.py''')}

{secao('Comandos de banco de dados')}

  {cmd(':conectar [host] [user] [senha] [banco]', 'Conecta ao PostgreSQL')}
  {cmd(':banco <nome>',     'Muda para outro banco')}
  {cmd(':bancos',          'Lista todos os bancos disponíveis')}
  {cmd(':tabelas',         'Lista tabelas do banco atual')}
  {cmd(':descrever <tab>', 'Exibe estrutura de uma tabela')}
  {cmd(':sql <query>',     'Executa SQL puro diretamente')}

{secao('Comandos do REPL')}

  {cmd(':vars',               'Lista variáveis definidas na sessão')}
  {cmd(':limpar',             'Limpa todas as variáveis do escopo')}
  {cmd(':historico',          'Mostra os últimos 20 comandos')}
  {cmd(':executar <arq.dk>', 'Executa um arquivo .dk')}
  {cmd(':salvar <arq.dk>',   'Salva os comandos da sessão em arquivo')}

{secao('Comandos de informação')}

  {cmd(':ajuda',   'Exibe ajuda rápida do REPL')}
  {cmd(':menu',    'Abre este menu de documentação')}
  {cmd(':versao',  'Exibe versão do Advak')}
  {cmd(':sair',    'Encerra o REPL')}

{secao('Atalhos de teclado')}

  {c('verde', 'Ctrl+C')}   Cancela a linha atual / interrompe execução
  {c('verde', 'Ctrl+D')}   Sai do REPL (equivale a :sair)
  {c('verde', 'Tab')}      Indentação automática (2 espaços)
  {c('verde', 'Enter')}    Linha vazia com bloco aberto executa o bloco

{secao('Bloco multi-linha')}

{exemplo('''// No REPL, blocos são detectados automaticamente.
// Comece a digitar uma função e pressione Enter:

advak> função calcular(x) {
...      retornar x * 2;
...    }
...
// ← linha vazia executa o bloco

advak> imprimir(calcular(5));
10''', 'exemplo de sessão no REPL')}

{secao('Comandos da linha de comando (fora do REPL)')}

  {cmd('python advak.py run arq.dk',       'Executa arquivo')}
  {cmd('python advak.py run arq.dk --db',  'Executa com banco conectado')}
  {cmd('python advak.py check arq.dk',     'Verifica sintaxe')}
  {cmd('python advak.py new <nome>',       'Cria novo projeto')}
  {cmd('python advak.py --version',        'Exibe versão')}
  {cmd('python advak.py --help',           'Exibe ajuda')}
""")


# ── 14. Exemplos Completos ────────────────────────────────────────────────────
def tela_exemplos():
    limpar_tela()
    print(titulo('🚀  EXEMPLOS COMPLETOS'))

    print(f"""
{secao('1 — Sistema de cadastro de alunos')}

{exemplo('''// cadastro_alunos.dk
banco.usar("escola");
banco.tabela("alunos", {
    "id":      "autonum",
    "nome":    "texto obrigatorio",
    "email":   "texto unico",
    "turma":   "varchar",
    "nota":    "decimal padrao 0"
});

// Menu simples
função menu() {
    imprimir("\\n=== CADASTRO DE ALUNOS ===");
    imprimir("1 - Cadastrar aluno");
    imprimir("2 - Listar alunos");
    imprimir("3 - Buscar por turma");
    imprimir("0 - Sair");
    retornar entrada("Opção: ");
}

seja op = menu();
enquanto (op != "0") {
    combinar(op) {
        caso "1":
            seja nome  = entrada("Nome: ");
            seja email = entrada("Email: ");
            seja turma = entrada("Turma: ");
            seja nota  = numero(entrada("Nota: "));
            seja r = banco.inserir("alunos",
                {{nome: nome, email: email, turma: turma, nota: nota}});
            imprimir(`✅ Aluno #${r.id} cadastrado!`);

        caso "2":
            seja lista = banco.buscar("alunos").ordenar("nome").executar();
            para (a em lista) {
                imprimir(`${a.id} | ${a.nome} | ${a.turma} | ${a.nota}`);
            }

        caso "3":
            seja turma = entrada("Turma: ");
            seja alunos = banco.buscar("alunos")
                .onde("turma = %s", turma)
                .ordenar("nota","DESC")
                .executar();
            imprimir(`${alunos.tamanho} aluno(s) na turma ${turma}:`);
            para (a em alunos) {
                imprimir(`  ${a.nome} — Nota: ${a.nota}`);
            }
    }
    op = menu();
}
imprimir("Até logo!");''', 'salve como cadastro_alunos.dk')}

{secao('2 — Análise de dados com IA')}

{exemplo('''// analise_ia.dk — Analisa feedbacks com IA
banco.usar("loja");

// Busca feedbacks sem classificação
seja feedbacks = banco.buscar("feedbacks")
    .onde("categoria IS NULL")
    .limite(20)
    .executar();

imprimir(`Analisando ${feedbacks.tamanho} feedbacks...`);

para (f em feedbacks) {
    // Classifica com IA
    seja cat = ai_classificar(f.texto,
        ["elogio", "reclamacao", "sugestao", "duvida"]);

    // Salva classificação
    banco.atualizar("feedbacks", {{categoria: cat}})
        .onde("id = %s", f.id).executar();

    imprimir(`#${f.id}: ${cat}`);
}

// Relatório final
seja relatorio = banco.sql(
    "SELECT categoria, COUNT(*) as total " +
    "FROM feedbacks GROUP BY categoria"
);
imprimir("\\n=== RELATÓRIO ===");
para (r em relatorio) {
    imprimir(`${r.categoria}: ${r.total}`);
}''', 'requer ANTHROPIC_API_KEY configurado')}
""")


# ── 15. Referência Rápida ─────────────────────────────────────────────────────
def tela_cheatsheet():
    limpar_tela()
    print(titulo('⌨️  REFERÊNCIA RÁPIDA — CHEATSHEET'))
    print(f"""
{c('bold', c('amarelo', '  VARIÁVEIS'))}
  seja x = 10;           fixo PI = 3.14;        seja s = "texto";
  seja ok = verdadeiro;  seja n = nulo;          seja l = [1,2,3];
  seja m = {{a: 1}};

{c('bold', c('amarelo', '  OPERADORES'))}
  + - * / % **    == != < > <= >=    && ||  !
  |>  ??  ?.      ===  !==            += -= *=

{c('bold', c('amarelo', '  CONTROLE DE FLUXO'))}
  se (cond) {{ }} senão {{ }}
  enquanto (cond) {{ }}
  para (seja i=0; i<n; i+=1) {{ }}
  para (item em lista) {{ }}
  quebrar;   continuar;

{c('bold', c('amarelo', '  FUNÇÕES'))}
  função nome(a, b=0) {{ retornar a+b; }}
  seja fn = (x) => x * 2;
  função async nome() {{ aguarda expr; }}

{c('bold', c('amarelo', '  CLASSES'))}
  classe Nome herda Base {{ construtor(x) {{ isso.x=x; }} método() {{}} }}
  seja obj = novo Nome(valor);

{c('bold', c('amarelo', '  MATCH'))}
  combinar(v) {{ caso 1: ...; caso 2: ...; padrão: ...; }}

{c('bold', c('amarelo', '  ERROS'))}
  tentar {{ }} capturar (e) {{ }} finalmente {{ }}
  lançar "mensagem";

{c('bold', c('amarelo', '  BANCO DE DADOS'))}
  banco.usar("db");          banco.criar_banco("db");
  banco.tabela("t", {{...}});  banco.inserir("t", {{...}});
  banco.buscar("t").onde("campo=%s",val).ordenar("c").limite(n).executar();
  banco.buscar_id("t", id);
  banco.atualizar("t",{{...}}).onde("id=%s",id).executar();
  banco.deletar("t").onde("id=%s",id).executar();
  banco.sql("SELECT ...");
  banco.iniciar();  banco.confirmar();  banco.reverter();

{c('bold', c('amarelo', '  TIPOS DE CAMPO'))}
  autonum  inteiro  decimal  flutuante  grande
  texto    varchar  booleano  data  datahora  json  ref

{c('bold', c('amarelo', '  IA NATIVA'))}
  ai_perguntar("prompt")
  ai_classificar("texto", ["cat1","cat2"])
  ai_transformar("dados", "instrução")
  ai_resumir("texto longo")
  ai_gerar("instrução criativa")

{c('bold', c('amarelo', '  BIBLIOTECA PADRÃO'))}
  Mat.raiz(x)  Mat.abs(x)  Mat.aleatorio()  Mat.pi
  Texto.aparar(s)  Texto.dividir(s,sep)  Texto.substituir(s,a,b)
  Lista.intervalo(n)  Lista.map(l,fn)  Lista.filtrar(l,fn)
  Arquivo.ler(p)  Arquivo.escrever(p,c)  Arquivo.existe(p)
  JSON.stringify(o)  JSON.parse(s)
  OS.env("VAR")  OS.pwd()

{c('bold', c('amarelo', '  TEMPLATE STRINGS'))}
  `Olá ${{nome}}!`   `${{a}} + ${{b}} = ${{a+b}}`

{c('bold', c('amarelo', '  COMANDOS DO REPL'))}
  :conectar  :banco  :bancos  :tabelas  :descrever  :sql
  :vars  :limpar  :historico  :executar  :salvar  :menu  :sair
""")


# ══════════════════════════════════════════════════════════════════════════════
#  ROTEADOR DO MENU
# ══════════════════════════════════════════════════════════════════════════════

TELAS = {
    '1':  tela_introducao,
    '2':  tela_variaveis,
    '3':  tela_operadores,
    '4':  tela_controle,
    '5':  tela_funcoes,
    '6':  tela_classes,
    '7':  tela_colecoes,
    '8':  tela_match,
    '9':  tela_erros,
    '10': tela_banco,
    '11': tela_ia,
    '12': tela_stdlib,
    '13': tela_repl_cmds,
    '14': tela_exemplos,
    '15': tela_cheatsheet,
}


def executar_menu():
    """Loop principal do menu — pode ser chamado de qualquer lugar."""
    while True:
        tela_menu_principal()
        try:
            op = input(c('bold', '  Escolha: ')).strip()
        except (EOFError, KeyboardInterrupt):
            break

        if op == '0' or op == '':
            break

        if op in TELAS:
            TELAS[op]()
            try:
                input(c('cinza', '\n  Pressione Enter para voltar ao menu...'))
            except (EOFError, KeyboardInterrupt):
                break
        else:
            print(c('vermelho', f"\n  Opção '{op}' inválida."))
            import time; time.sleep(1)


if __name__ == '__main__':
    executar_menu()
