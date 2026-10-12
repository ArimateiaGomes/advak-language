# Advak Language

**Uma linguagem de programação em português, feita para ensinar e para criar sistemas de verdade.**

Advak é uma linguagem interpretada, escrita em Python, com palavras-chave em português (`seja`, `se`, `senão`, `para`, `função`, `classe`...). Ela já vem com banco de dados PostgreSQL, servidor web, interface gráfica e testes embutidos, então o aluno sai do "Olá, mundo" e chega num sistema com cadastro e tela sem precisar aprender outra linguagem no meio do caminho.

```advak
seja nome = entrada("Qual é o seu nome? ")
imprimir(`Olá, ${nome}! Bem-vindo ao Advak.`)
```

> Versão atual: **5.1.0** · Autor: **Prof. Arimatéa Gomes** — CETI Silvestre Rocha, Arraial-PI

---

## Influências

A linguagem de programação Advak foi influenciada por **Python**, **C**, **Prolog**, **Haskell** e **Java**:

| Linguagem | O que o Advak herdou |
|---|---|
| **Python** | Simplicidade e leitura fácil; é a linguagem em que o interpretador do Advak foi escrito |
| **C** | Sintaxe com chaves `{ }`, laço `para` com contador, operadores (`++`, `+=`, `&&`, `\|\|`) e recursos como estruturas e enumerações |
| **Prolog** | Programação lógica com fatos, regras e consultas |
| **Haskell** | Estilo funcional: lambdas, funções puras, imutabilidade, composição de funções e o operador pipeline `\|>` |
| **Java** | Orientação a objetos com `classe`, `construtor`, `herda`, `isso` e `novo` |

---

## Sumário

1. [Influências](#influências)
1. [Instalação](#instalação)
2. [Como executar](#como-executar)
3. [Primeiro programa](#primeiro-programa)
4. [Guia da linguagem](#guia-da-linguagem)
   - [Variáveis e tipos](#variáveis-e-tipos)
   - [Operadores](#operadores)
   - [Textos e template strings](#textos-e-template-strings)
   - [Condicionais](#condicionais)
   - [Laços de repetição](#laços-de-repetição)
   - [Funções e lambdas](#funções-e-lambdas)
   - [Listas](#listas)
   - [Mapas (objetos)](#mapas-objetos)
   - [Classes e herança](#classes-e-herança)
   - [Combinar (match)](#combinar-match)
   - [Tratamento de erros](#tratamento-de-erros)
   - [Módulos](#módulos)
5. [Biblioteca padrão](#biblioteca-padrão)
6. [Banco de dados](#banco-de-dados)
7. [Servidor web](#servidor-web)
8. [Interface gráfica](#interface-gráfica)
9. [Testes unitários](#testes-unitários)
10. [Sintaxe em inglês](#sintaxe-em-inglês)
11. [Ferramentas de linha de comando](#ferramentas-de-linha-de-comando)
12. [Exemplos prontos](#exemplos-prontos)
13. [Estrutura do projeto](#estrutura-do-projeto)
14. [Tabela de palavras-chave](#tabela-de-palavras-chave)

---

## Instalação

### Requisitos

- **Python 3** — baixe em [python.org](https://python.org/downloads) e marque **"Add Python to PATH"** na instalação.
- **PostgreSQL** (opcional) — só é necessário para os recursos de banco de dados. Sem ele, o Advak usa SQLite automaticamente.

### Passo a passo (Windows)

```cmd
git clone https://github.com/SEU_USUARIO/advak-language.git
cd advak-language
pip install ttkbootstrap psycopg2-binary pyserial paho-mqtt pyinstaller
INSTALAR.bat
```

O `INSTALAR.bat` coloca a pasta do Advak no PATH do Windows. **Feche e abra o terminal de novo** e o comando `advak` passa a funcionar em qualquer pasta.

### Dependências opcionais

| Pacote | Para que serve |
|---|---|
| `psycopg2-binary` | Conexão com o PostgreSQL |
| `ttkbootstrap` | Visual moderno na interface gráfica |
| `pyinstaller` | Compilar programas `.dk` para `.exe` |
| `pyserial` | Comunicação com Arduino pela porta serial |
| `paho-mqtt` | Comunicação com dispositivos IoT (ESP32) |

### Configurando o PostgreSQL

Copie o arquivo de exemplo e coloque sua senha:

```cmd
copy .env.exemplo .env
notepad .env
```

```ini
ADVAK_DB_HOST=localhost
ADVAK_DB_PORT=5432
ADVAK_DB_USER=postgres
ADVAK_DB_PASS=sua_senha_aqui
```

Também dá para configurar pelo assistente: `CONFIGURAR_BANCO.bat`.

> O arquivo `.env` fica só no seu computador. Ele está no `.gitignore` e nunca vai para o GitHub.

---

## Como executar

Os arquivos da linguagem usam a extensão **`.dk`**.

| Comando | O que faz |
|---|---|
| `advak programa.dk` | Executa um programa |
| `advak run programa.dk --db` | Executa já conectado ao PostgreSQL |
| `advak` | Abre o modo interativo (REPL) |
| `advak check programa.dk` | Verifica a sintaxe sem executar |

Sem o `INSTALAR.bat`, use o Python diretamente:

```cmd
python advak.py run programa.dk
```

Outra opção é arrastar um arquivo `.dk` para cima do `rodar.bat`.

---

## Primeiro programa

Crie um arquivo `ola.dk`:

```advak
// Meu primeiro programa em Advak
seja nome = entrada("Digite seu nome: ")
seja idade = numero(entrada("Digite sua idade: "))

imprimir(`Olá, ${nome}!`)

se (idade >= 18) {
    imprimir("Você é maior de idade.")
} senão {
    imprimir(`Faltam ${18 - idade} anos para a maioridade.`)
}
```

Execute:

```cmd
advak ola.dk
```

> O ponto e vírgula no fim da linha é **opcional**. Os dois estilos funcionam.

---

## Guia da linguagem

### Variáveis e tipos

```advak
seja nome    = "Arimatea"     // texto
seja idade   = 42             // número inteiro
seja preco   = 9.99           // número decimal
seja ativo   = verdadeiro     // booleano (verdadeiro / falso)
seja vazio   = nulo           // ausência de valor
fixo PI      = 3.14159        // constante: não pode ser alterada

imprimir(tipo(nome))          // texto
imprimir(tipo(idade))         // numero
imprimir(tipo([1, 2]))        // lista
```

### Operadores

```advak
imprimir(10 + 3)      // 13   soma
imprimir(10 - 3)      // 7    subtração
imprimir(10 * 3)      // 30   multiplicação
imprimir(10 / 3)      // 3.33 divisão
imprimir(10 % 3)      // 1    resto da divisão
imprimir(2 ** 10)     // 1024 potência

imprimir(5 == 5)      // verdadeiro   igual
imprimir(5 != 3)      // verdadeiro   diferente
imprimir(10 > 5 && 3 < 7)       // verdadeiro   E lógico
imprimir(falso || verdadeiro)   // verdadeiro   OU lógico
imprimir(!verdadeiro)           // falso        NÃO lógico

seja x = 5
x += 1       // também: -=  *=  /=  %=
x++          // incrementa 1

// Ternário
imprimir(x > 3 ? "grande" : "pequeno")

// Valor padrão quando for nulo
seja apelido = nulo ?? "sem apelido"

// Acesso seguro (não dá erro se for nulo)
seja pessoa = {endereco: {cidade: "Arraial"}}
imprimir(pessoa?.endereco?.cidade)
```

### Textos e template strings

Use crases (`` ` ``) para colocar variáveis e contas dentro do texto:

```advak
seja a = 8
seja b = 4
imprimir(`${a} + ${b} = ${a + b}`)        // 8 + 4 = 12

seja s = "  Olá, mundo!  "
s.tamanho                 // quantidade de caracteres
s.maiusculo()             // "  OLÁ, MUNDO!  "
s.minusculo()
s.aparar()                // remove espaços das pontas
"a,b,c".dividir(",")      // ["a", "b", "c"]
"abc".substituir("a", "X")// "Xbc"
"abc".contem("b")         // verdadeiro
"abcdef".primeiros(3)     // "abc"
```

### Condicionais

```advak
seja nota = 75

se (nota >= 90) {
    imprimir("Excelente")
} senão se (nota >= 70) {
    imprimir("Aprovado")
} senão {
    imprimir("Recuperação")
}
```

### Laços de repetição

```advak
// Percorrer uma lista
seja frutas = ["maçã", "banana", "uva"]
para (f em frutas) {
    imprimir(`- ${f}`)
}

// Laço com contador
para (seja i = 1; i <= 3; i += 1) {
    imprimir(`linha ${i}`)
}

// Enquanto
seja n = 3
enquanto (n > 0) {
    imprimir(n)
    n -= 1
}

// Pular e parar
para (i em Lista.intervalo(10)) {
    se (i == 2) { continuar }   // pula para a próxima volta
    se (i == 5) { quebrar }     // sai do laço
    imprimir(i)
}
```

### Funções e lambdas

```advak
função somar(a, b) {
    retornar a + b
}

// Parâmetro com valor padrão
função saudar(nome, saudacao = "Olá") {
    retornar `${saudacao}, ${nome}!`
}

// Recursão
função fatorial(n) {
    se (n <= 1) { retornar 1 }
    retornar n * fatorial(n - 1)
}

imprimir(somar(15, 27))        // 42
imprimir(saudar("Ana"))        // Olá, Ana!
imprimir(saudar("Ana", "Oi"))  // Oi, Ana!
imprimir(fatorial(6))          // 720
```

`funcao` (sem acento) também é aceito.

**Lambdas** (funções curtas) e o **operador pipeline** `|>`, que passa o resultado de uma função para a próxima:

```advak
seja dobrar   = (x) => x * 2
seja quadrado = (x) => x ** 2
seja somar10  = (x) => x + 10

imprimir(dobrar(7))                              // 14
imprimir(3 |> dobrar |> quadrado |> somar10)     // ((3*2)²)+10 = 46
```

### Listas

```advak
seja nums = [5, 2, 8, 1, 9]

nums.adicionar(3)          // coloca no final
nums.remover(0)            // remove pela posição
nums.ordenar()             // ordena
nums.inverter()            // inverte a ordem
nums.tamanho               // quantidade de itens
nums.primeiro()            // primeiro item
nums.ultimo()              // último item
nums[0]                    // item na posição 0
nums.inclui(8)             // verdadeiro se existir
nums.unir(", ")            // "1, 2, 3, ..."
nums.fatia(1, 3)           // pedaço da lista
nums.unico()               // remove repetidos
nums.soma()   nums.min()   nums.max()

// Funções de alta ordem
seja l = [1, 2, 3, 4, 5]
l.filtrar((x) => x > 2)              // [3, 4, 5]
l.mapear((x) => x * 2)               // [2, 4, 6, 8, 10]
l.reduzir((acc, x) => acc + x, 0)    // 15
l.encontrar((x) => x > 3)            // 4
l.algum((x) => x > 4)                // verdadeiro
l.todos((x) => x > 0)                // verdadeiro

// Espalhar e desestruturar
seja a = [1, 2]
seja b = [...a, 3]           // [1, 2, 3]
seja [x, y] = [10, 20]       // x = 10, y = 20
```

### Mapas (objetos)

```advak
seja pessoa = {nome: "Ana", cidade: "Arraial", nota: 9.5}

imprimir(pessoa.nome)          // Ana
imprimir(pessoa["cidade"])     // Arraial
pessoa.ativo = verdadeiro      // cria um novo campo

pessoa.chaves                  // ["nome", "cidade", "nota", "ativo"]
pessoa.valores                 // ["Ana", "Arraial", 9.5, verdadeiro]
pessoa.tamanho                 // 4
pessoa.contem("nome")          // verdadeiro

seja {nome, cidade} = pessoa   // desestruturação
```

### Classes e herança

```advak
classe Veiculo {
    construtor(marca, modelo) {
        isso.marca  = marca
        isso.modelo = modelo
    }
    descricao() {
        retornar `${isso.marca} ${isso.modelo}`
    }
}

classe Carro herda Veiculo {
    construtor(marca, modelo, portas) {
        super(marca, modelo)
        isso.portas = portas
    }
    descricao() {
        retornar `${super.descricao()} (${isso.portas} portas)`
    }
}

seja c = novo Carro("Toyota", "Corolla", 4)
imprimir(c.descricao())     // Toyota Corolla (4 portas)
```

| Advak | Significado |
|---|---|
| `classe` | declara uma classe |
| `construtor(...)` | método executado ao criar o objeto |
| `isso` | o próprio objeto (como `this`) |
| `herda` | herança (como `extends`) |
| `super(...)` / `super.metodo()` | chama a classe mãe |
| `novo` | cria um objeto |

### Combinar (match)

Escolhe um caminho de acordo com o valor:

```advak
seja dia = 3

combinar(dia) {
    caso 1: imprimir("Segunda")
    caso 2: imprimir("Terça")
    caso 3: imprimir("Quarta")
    padrão: imprimir("Outro dia")
}
```

Forma alternativa, com seta e `_` para "qualquer outro":

```advak
combinar dia {
    caso 1 => imprimir("um")
    caso 2 => imprimir("dois")
    caso _ => imprimir("outro")
}
```

### Tratamento de erros

```advak
tentar {
    lançar "Algo deu errado!"
} capturar (e) {
    imprimir(`Erro: ${e}`)
} finalmente {
    imprimir("Isso sempre executa")
}
```

`pegar` funciona como sinônimo de `capturar`, e `lancar` (sem cedilha) como sinônimo de `lançar`.

Quando um programa tem erro, o Advak mostra a linha exata e dicas em português:

```
╔══════════════════════════════════════════╗
║        ❌  ERRO DE SINTAXE               ║
╚══════════════════════════════════════════╝
  📍 Localização: linha 12
  💬 Problema:    token inesperado ';'
```

### Módulos

Divida o programa em vários arquivos. No arquivo `matematica.dk`:

```advak
exportar função dobro(x) {
    retornar x * 2
}
```

Em outro arquivo, na mesma pasta:

```advak
importar { dobro } de "matematica.dk"
imprimir(dobro(21))   // 42
```

> Atenção: a linha `importar` **não pode** terminar com ponto e vírgula.

Também existem módulos da biblioteca padrão:

```advak
importar Mat de "std:math"
importar { hoje, agora } de "std:data"
```

---

## Biblioteca padrão

### Matemática

```advak
arred(3.14159, 2)          // 3.14
piso(3.9)                  // 3
teto(3.1)                  // 4
raiz(16)                   // 4.0
abs(-5)                    // 5
aleatorio()                // número entre 0 e 1
inteiro_aleatorio(1, 10)   // inteiro entre 1 e 10

Mat.raiz(144)   Mat.abs(-42)   Mat.pi
```

### Conversão

```advak
numero("42")       // 42
inteiro("3.9")     // 3
texto(42)          // "42"
booleano(1)        // verdadeiro
```

### Formatação brasileira

```advak
moeda(1500.50)                // R$ 1.500,50
num_abrev(1500000)            // 1.5M
porcentagem(0.75)             // 75%
formatar_data("2024-12-25")   // 25/12/2024
data_hoje()                   // data de hoje, ex.: 11/10/2026
```

### Entrada e saída

```advak
imprimir("Olá")
seja resposta = entrada("Digite algo: ")
```

### Arquivos

```advak
Arquivo.escrever("dados.txt", "conteúdo")
seja conteudo = Arquivo.ler("dados.txt")
Arquivo.ler_linhas("dados.txt")
Arquivo.escrever_json("dados.json", {a: 1})
Arquivo.ler_json("dados.json")
Arquivo.listar("pasta", ".dk")
Arquivo.criar_pasta("nova/pasta")
Arquivo.copiar("origem.txt", "destino.txt")
```

### JSON

```advak
seja obj = {nome: "Advak", versao: 5}
seja texto_json = JSON.stringify(obj)    // {"nome": "Advak", "versao": 5}
seja de_volta   = JSON.parse(texto_json)
```

### Expressões regulares

```advak
Regex.testar("[0-9]+", "abc123")            // verdadeiro
Regex.extrair_todos("[a-z]+", "abc def")    // ["abc", "def"]
Regex.substituir("[0-9]", "X", "a1b2")      // "aXbX"
```

### HTTP (consumir APIs)

```advak
seja dados = HTTP.json("https://api.exemplo.com/dados")
HTTP.post("https://api.exemplo.com", {a: 1})
HTTP.baixar("https://site.com/arquivo.pdf", "local.pdf")
```

---

## Banco de dados

O Advak conversa com o **PostgreSQL** sem precisar escrever SQL. Execute os programas com `--db`:

```cmd
advak run meu_app.dk --db
```

### Criar banco e tabela

```advak
banco.criar_banco("escola")
banco.usar("escola")

banco.tabela("alunos", {
    "id":     "autonum",
    "nome":   "texto obrigatorio",
    "email":  "texto unico",
    "turma":  "varchar",
    "nota":   "decimal",
    "faltas": "inteiro padrao 0",
    "ativo":  "booleano padrao verdadeiro",
    "criado": "datahora"
})
```

**Tipos de campo:** `autonum`, `texto`, `varchar`, `inteiro`, `decimal`, `booleano`, `data`, `datahora`, `ref outra_tabela` (chave estrangeira).

**Modificadores:** `obrigatorio` (NOT NULL), `unico` (UNIQUE), `padrao valor` (DEFAULT).

### Inserir

```advak
seja aluno = banco.inserir("alunos", {"nome": "Ana", "turma": "1A", "nota": 8.5})
imprimir(aluno.id)   // id gerado

banco.inserir_varios("alunos", [
    {"nome": "Bob",   "turma": "1A", "nota": 7.2},
    {"nome": "Carla", "turma": "1B", "nota": 9.1}
])
```

### Buscar

```advak
seja todos = banco.buscar("alunos").ordenar("nome").executar()

seja aprovados = banco.buscar("alunos")
    .onde("nota >= %s", 7.0)
    .ordenar("nota", "DESC")
    .executar()

para (a em aprovados) {
    imprimir(`${a.nome} — ${a.nota}`)
}

seja total   = banco.buscar("alunos").contar()
seja melhor  = banco.buscar("alunos").ordenar("nota", "DESC").primeiro()
seja um      = banco.buscar_id("alunos", 1)
seja pagina1 = banco.buscar("alunos").ordenar("nome").pagina(1, 10).executar()
```

Use `%s` no filtro e passe o valor separado. Assim o Advak protege o banco contra SQL injection.

### Atualizar e excluir

```advak
banco.atualizar("alunos", {"turma": "2A"})
    .onde("nome = %s", "Bob")
    .executar()

banco.deletar("alunos")
    .onde("id = %s", 3)
    .executar()
```

### SQL direto

```advak
seja stats = banco.sql("SELECT turma, COUNT(*) AS total FROM alunos GROUP BY turma")
para (s em stats) {
    imprimir(`${s.turma}: ${s.total}`)
}

// Com parâmetros: um valor para cada %s
seja r = banco.sql("SELECT nome FROM alunos WHERE nota > %s", 8)
```

### Banco automático (SQLite como reserva)

`banco_auto` tenta o PostgreSQL e, se ele não estiver disponível, cria um arquivo SQLite. É útil para levar o programa para outro computador:

```advak
seja db = banco_auto("minha_app")

seja alunos = db.criar_tabela("alunos", {nome: "texto", turma: "texto", nota: "decimal"})
alunos.inserir({nome: "Ana", turma: "1A", nota: 8.5})

imprimir(alunos.contar())
seja ap = alunos.buscar("nota >= ?", [7])
seja todos = alunos.todos()
```

### Comandos do REPL para banco

Dentro do `advak` interativo:

| Comando | O que faz |
|---|---|
| `:bancos` | Lista os bancos |
| `:tabelas` | Lista as tabelas do banco atual |
| `:descrever alunos` | Mostra a estrutura da tabela |
| `:sql SELECT * FROM alunos` | Executa SQL direto |
| `:menu` | Documentação completa |
| `:sair` | Sai do REPL |

---

## Servidor web

Crie uma API ou um site em poucas linhas:

```advak
servidor.obter("/", (req) => {
    retornar html("<h1>Olá do Advak!</h1>")
})

servidor.obter("/api/alunos/:id", (req) => {
    retornar resposta_json({
        id:    req.parametros.id,    // valor do :id na URL
        busca: req.consulta.q        // ?q=... na URL
    })
})

servidor.publicar("/api/alunos", (req) => {
    seja novo_aluno = req.dados      // corpo JSON enviado
    retornar resposta_json({ok: verdadeiro}, 201)
})

servidor.iniciar(8080)
```

Acesse `http://localhost:8080`.

| Rota | Método HTTP |
|---|---|
| `servidor.obter(caminho, fn)` | GET |
| `servidor.publicar(caminho, fn)` | POST |
| `servidor.atualizar(caminho, fn)` | PUT |
| `servidor.deletar(caminho, fn)` | DELETE |
| `servidor.estatico("/css", "./pasta")` | Arquivos estáticos |

**Respostas:** `html(texto, status)`, `resposta_json(objeto, status)`, `resposta_texto(texto)`, `redirecionar(url)`.

**Requisição (`req`):** `req.metodo`, `req.caminho`, `req.parametros`, `req.consulta`, `req.dados`, `req.corpo`, `req.cabecalhos`.

---

## Interface gráfica

Aplicativos de desktop com janelas, botões e tabelas (usa Tkinter, que já vem com o Python no Windows):

```advak
gui.tema("escuro")
seja jan = gui.janela("Cadastro de Alunos", 600, 400)

gui.label(jan, "Nome do aluno:", negrito=verdadeiro)
seja campo_nome = gui.campo(jan, "Digite o nome...", largura=30)

gui.botao(jan, "Salvar", (x) => {
    seja nome = campo_nome.valor()
    se (nome) {
        gui.alerta(`Aluno ${nome} salvo!`)
        campo_nome.limpar()
    } senão {
        gui.aviso("Digite um nome primeiro.")
    }
}, estilo="sucesso")

gui.iniciar()
```

**Componentes:** `gui.label`, `gui.botao`, `gui.campo`, `gui.area_texto`, `gui.checkbox`, `gui.caixa_selecao`, `gui.slider`, `gui.switch`, `gui.tabela`, `gui.abas`, `gui.card`, `gui.menu_bar`, `gui.frame`, `gui.frame_horizontal`, `gui.barra_progresso`, `gui.barra_status`.

**Diálogos:** `gui.alerta`, `gui.aviso`, `gui.confirmar` (retorna verdadeiro/falso), `gui.pedir` (retorna o texto digitado), `gui.toast`, `gui.escolher_arquivo`.

**Temporizadores:** `gui.apos(1000, fn)` executa uma vez depois de 1 segundo; `gui.repetir(500, fn)` repete a cada meio segundo.

Para ver todos os componentes funcionando:

```cmd
advak projetos\guia_gui.dk
```

---

## Testes unitários

```advak
função somar(a, b) { retornar a + b }

testar("soma de dois números", () => {
    afirmar_igual(somar(2, 2), 4)
    afirmar_verdadeiro(somar(1, 1) > 0)
    afirmar_falso(somar(1, 1) > 10)
    afirmar_contem([1, 2, 3], 2)
})

resumo_testes()
```

Saída:

```
  ✅ soma de dois números
  Resultado: 1/1 testes passaram  🎉
```

---

## Sintaxe em inglês

As palavras-chave em inglês também funcionam, e dá para misturar os dois idiomas no mesmo arquivo:

```advak
let a = 1
const b = 2
function sum(x, y) { return x + y }

if (a < b) {
    print(sum(a, b))
} else {
    print("no")
}
```

Veja `syntax_english.dk` e `english_full.dk`.

---

## Ferramentas de linha de comando

| Comando | O que faz |
|---|---|
| `advak` | REPL interativo |
| `advak --db` | REPL já conectado ao banco |
| `advak run arquivo.dk` | Executa um arquivo |
| `advak run arquivo.dk --db` | Executa com banco de dados |
| `advak check arquivo.dk` | Verifica a sintaxe |
| `advak --verificar arquivo.dk` | Verifica tipos e padrões (linter) |
| `advak formatar arquivo.dk` | Formata o código automaticamente |
| `advak --doc arquivo.dk` | Gera documentação HTML do arquivo |
| `advak --live arquivo.dk` | Reexecuta sempre que o arquivo é salvo |
| `advak --debug arquivo.dk` | Depurador interativo |
| `advak --passo arquivo.dk` | Executa linha por linha |
| `advak --perfil arquivo.dk` | Mede o desempenho |
| `advak compilar arquivo.dk` | Gera um `.exe` na pasta `dist/` |
| `advak new meu_projeto` | Cria um projeto novo com exemplos |
| `advak projetos` | Lista os projetos da pasta `projetos/` |
| `advak --versao` | Mostra a versão |
| `advak --ajuda` | Mostra a ajuda |

### Compilar para executável

```cmd
advak compilar meu_app.dk --gui --nome MeuApp --icone icone.ico
```

| Opção | Significado |
|---|---|
| `--gui` | Não abre a janela preta do console (para apps com interface) |
| `--nome` | Nome do executável |
| `--icone` | Ícone `.ico` |
| `--saida` | Pasta de saída (padrão: `dist/`) |

Requer `pip install pyinstaller`.

---

## Exemplos prontos

Na raiz do projeto:

| Arquivo | Conteúdo |
|---|---|
| `sintaxe_completa.dk` | Tour por toda a sintaxe |
| `primeiros_passos.dk` | Primeiros passos com PostgreSQL |
| `banco_exemplo.dk` | Banco de dados escolar completo |
| `servidor_exemplo.dk` | Loja com API REST + PostgreSQL |
| `gui_exemplo.dk` | Gestão de alunos com interface gráfica |

Na pasta `projetos/`:

| Arquivo | Conteúdo |
|---|---|
| `calculadora.dk`, `fatorial.dk`, `fibonacci.dk` | Exercícios de lógica |
| `classes_demo.dk` | Orientação a objetos |
| `modulos_demo.dk` | Importar e exportar módulos |
| `testes_demo.dk` | Testes unitários |
| `estoque.dk`, `tarefas.dk`, `cadastro.dk` | Sistemas com interface gráfica |
| `gui_escola.dk`, `biblioteca.dk` | Sistemas escolares |
| `supermercado_pdv.dk` | Frente de caixa (PDV) |
| `api_escola.dk`, `ola_web.dk` | APIs e sites |
| `guia_gui.dk`, `gui_moderno_demo.dk` | Todos os componentes de tela |
| `mobile_embarcado_demo.dk` | Mobile, QR Code e IoT |
| `firmware_arduino/`, `firmware_esp32/`, `firmware_micropython/` | Código gerado para placas |
| `REFERENCIA.md` | Glossário com todas as funções |

---

## Estrutura do projeto

```
advak-language/
├── advak.py                 # Ponto de entrada (comando advak)
├── advak_lexer.py           # Análise léxica: transforma o texto em tokens
├── advak_parser.py          # Análise sintática: monta a árvore do programa
├── advak_interpreter.py     # Interpretador: executa a árvore
├── advak_repl.py            # Modo interativo
├── advak_erros.py           # Mensagens de erro em português
│
├── advak_db.py              # Motor de banco PostgreSQL
├── advak_bancoweb.py        # Banco automático (PostgreSQL ou SQLite)
├── advak_http.py            # Servidor HTTP nativo
├── advak_web.py             # Servidor web completo, autenticação
├── advak_gui_modern.py      # Componentes de interface gráfica
├── advak_mobile.py          # Recursos mobile e QR Code
├── advak_embarcado.py       # Arduino, ESP32, MQTT
├── advak_modern.py          # Módulos modernos (validação, criptografia)
├── advak_advanced.py        # Recursos avançados
│
├── advak_compiler.py        # Compilação para executável
├── advak_nativo.py          # Compilador nativo
├── advak_debug.py           # Depurador
├── advak_linter.py          # Verificador de código
├── advak_verificador.py     # Verificador de tipos
├── advak_formatador.py      # Formatador de código
├── advak_profiler.py        # Medição de desempenho
├── advak_doc.py             # Gerador de documentação
├── advak_live.py            # Hot reload
├── advak_menu.py            # Menu de ajuda
├── advak_projects.py        # Gerenciador de projetos
├── advak_playground.html    # Playground no navegador
│
├── INSTALAR.bat             # Instala o comando advak no Windows
├── CONFIGURAR_BANCO.bat     # Assistente de configuração do banco
├── rodar.bat                # Executa um .dk arrastado
├── .env.exemplo             # Modelo de configuração
│
├── *.dk                     # Exemplos principais
└── projetos/                # Mais exemplos e projetos
```

### Como funciona por dentro

```
código .dk  →  Lexer  →  tokens  →  Parser  →  árvore (AST)  →  Interpretador  →  resultado
```

Um bom roteiro para quem quer estudar como uma linguagem de programação é construída.

---

## Tabela de palavras-chave

| Advak | Inglês | Para que serve |
|---|---|---|
| `seja` | `let` / `var` | Declarar variável |
| `fixo` | `const` | Declarar constante |
| `se` / `senão` | `if` / `else` | Condição |
| `para ... em` | `for ... in` | Percorrer lista |
| `enquanto` | `while` | Repetir enquanto for verdade |
| `quebrar` / `continuar` | `break` / `continue` | Controlar laços |
| `função` / `funcao` | `function` | Declarar função |
| `retornar` | `return` | Devolver valor |
| `classe` | `class` | Declarar classe |
| `construtor` | `constructor` | Inicializar objeto |
| `isso` | `this` | O próprio objeto |
| `herda` | `extends` | Herança |
| `novo` | `new` | Criar objeto |
| `combinar` / `caso` / `padrão` | `match` / `case` / `default` | Escolha por valor |
| `tentar` / `capturar` / `finalmente` | `try` / `catch` / `finally` | Tratar erros |
| `lançar` | `throw` | Gerar erro |
| `importar` / `exportar` / `de` | `import` / `export` / `from` | Módulos |
| `verdadeiro` / `falso` | `true` / `false` | Booleanos |
| `nulo` | `null` | Sem valor |
| `imprimir` | `print` | Mostrar na tela |
| `entrada` | `input` | Ler do teclado |

---

## Licença

Este projeto está sob a licença **MIT**. Você pode usar, estudar, modificar e distribuir a Advak Language livremente, inclusive em projetos comerciais, desde que mantenha o aviso de direitos autorais e a licença. Veja o arquivo [LICENSE](LICENSE).

© 2026 Prof. Arimatéa Gomes

## Autor

**Prof. Arimatéa Gomes**
CETI Silvestre Rocha — Arraial, Piauí, Brasil
