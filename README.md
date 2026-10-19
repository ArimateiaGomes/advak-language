# Advak Language

**Uma linguagem de programação em português, feita para ensinar e para criar sistemas de verdade.**

Advak é uma linguagem interpretada, escrita em Python, com palavras-chave em português (`seja`, `se`, `senão`, `para`, `função`, `classe`...). Ela já vem com banco de dados PostgreSQL, servidor web, interface gráfica e testes embutidos, então o aluno sai do "Olá, mundo" e chega num sistema com cadastro e tela sem precisar aprender outra linguagem no meio do caminho.

```advak
seja nome = entrada("Qual é o seu nome? ")
imprimir(`Olá, ${nome}! Bem-vindo ao Advak.`)
```

> Versão atual: **5.2.0** · Autor: **Prof. Arimatéa Gomes** — CETI Silvestre Rocha, Arraial-PI

## 📚 Aprenda a programar com Advak

**Nunca programou? Comece aqui:** [docs/curso/README.md](docs/curso/README.md) — um curso de 24 aulas curtas,
do primeiro `imprimir` até um sistema completo, feito para alunos do ensino médio e da EJA. Todos os
exemplos do curso foram executados com a Advak e a saída mostrada é a real. O curso **não depende de
internet, de chave de API nem de IA**.

| Quero... | Vá para |
|---|---|
| Instalar a Advak (Windows ou Linux), com PostgreSQL | [docs/INSTALACAO.md](docs/INSTALACAO.md) |
| Aprender do zero | [docs/curso/README.md](docs/curso/README.md) |
| Ver aplicativos completos do dia a dia, explicados | [docs/GUIA_PRATICO.md](docs/GUIA_PRATICO.md) |
| Conectar a um dos 23 bancos de dados | [docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md) |
| Usar IA (opcional) | [docs/IA.md](docs/IA.md) e [docs/DOCUMENTOS.md](docs/DOCUMENTOS.md) |
| Ver o que mudou | [CHANGELOG.md](CHANGELOG.md) |

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
1. [Novidades da versão 5.2](#novidades-da-versão-52)
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
   - [Inteligência artificial (opcional)](#inteligência-artificial-opcional)
6. [Banco de dados](#banco-de-dados) (PostgreSQL e [23 bancos suportados](#bancos-de-dados-suportados))
7. [Servidor web](#servidor-web)
8. [Interface gráfica](#interface-gráfica)
9. [Testes unitários](#testes-unitários)
10. [Sintaxe em inglês](#sintaxe-em-inglês)
11. [Ferramentas de linha de comando](#ferramentas-de-linha-de-comando)
12. [Exemplos prontos](#exemplos-prontos)
13. [Estrutura do projeto](#estrutura-do-projeto)
14. [Tabela de palavras-chave](#tabela-de-palavras-chave)

---

## Novidades da versão 5.2

| Novidade | Exemplo |
|---|---|
| **Intervalos** | `para (i em 1..=10 passo 2) { }` — `1..10` não inclui o fim, `1..=10` inclui |
| **Compreensão de listas** | `[x * 2 para x em lista se x > 0]` |
| **Interpolação com formatação** | `` `Total: ${preco:moeda}` `` → `R$ 1.500,50`; `` `${d:dd/mm/aaaa}` `` |
| **Tipagem opcional** | `seja idade: inteiro = 17`, `função somar(a: numero, b: numero) -> numero { ... }` |
| **23 bancos de dados** | `banco.conectar("mysql://usuario:senha@localhost/loja")` — mesma API para todos |
| **IA (opcional)** | `seja assistente = ia.conectar("ollama")` — 8 provedores, só carregada se você usar |
| **Documentos** | `documento.ler("relatorio.pdf")` e `assistente.perguntar("Resuma", {anexos: ["a.pdf"]})` |
| **Ferramentas corrigidas** | `advak formatar` (`+=`, `=>`, textos de várias linhas), `--verificar` e o transpilador Python (números negativos) |
| **Correções** | `caso` com condição, `importar` com `;`, `servidor.rota`, `enum`, geradores, `inicio(...)` como construtor, `lista.primeiro`, arquivos `.dk` com BOM do Bloco de Notas |

Veja o detalhe de cada uma nas seções abaixo, no [CHANGELOG](CHANGELOG.md) e em
[docs/RECURSOS_5_2.md](docs/RECURSOS_5_2.md).

> **A IA é opcional.** A Advak funciona 100% sem ela: sem internet, sem chave de API e sem custo.

---

## Instalação

> Guia completo, passo a passo para iniciantes (Windows e Linux, PostgreSQL, problemas comuns):
> **[docs/INSTALACAO.md](docs/INSTALACAO.md)**.

### Requisitos

- **Python 3** — baixe em [python.org](https://python.org/downloads) e marque **"Add Python to PATH"** na instalação.
- **PostgreSQL** (opcional) — só é necessário para os recursos de banco de dados. Sem ele, o Advak usa SQLite automaticamente.
  - Windows: [instalador do PostgreSQL (EDB)](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
  - Página oficial com todos os sistemas: [postgresql.org/download](https://www.postgresql.org/download/)
  - Linux: [postgresql.org/download/linux](https://www.postgresql.org/download/linux/)
  - Programa visual para ver o banco (opcional): [pgAdmin](https://www.pgadmin.org/download/)

  > Durante a instalação do PostgreSQL, anote a **senha** que você criar para o usuário `postgres` e mantenha a porta **5432**. Essa senha vai no arquivo `.env`.

### Passo a passo (Windows)

```cmd
git clone https://github.com/ArimateiaGomes/advak-language.git
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

Os drivers dos outros bancos (MySQL, SQL Server, MongoDB, Redis...) e de leitura de documentos (PDF, Word...)
também são opcionais e instalados só quando você usar: veja [docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md)
e [docs/DOCUMENTOS.md](docs/DOCUMENTOS.md).

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

**Tipos opcionais** (novo na 5.2): você pode dizer o tipo e a Advak confere para você. Sem o tipo, tudo
continua livre:

```advak
seja idade: inteiro = 17
seja apelido: texto? = nulo                       // o ? aceita também nulo
função somar(a: numero, b: numero = 0) -> numero { retornar a + b }

idade = "dezoito"   // Tipo incorreto: 'idade' é inteiro, mas recebeu texto ("dezoito").
```

Tipos: `inteiro`, `numero`, `texto`, `booleano`, `lista` (`lista[numero]`), `mapa`, `funcao`, `nulo`, `qualquer`,
o nome de uma classe, e `A | B` para "um ou outro".

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

**Formatando valores dentro do texto** (novo na 5.2): depois de `:` vem o formato — dinheiro, porcentagem,
casas decimais, zeros à esquerda, alinhamento e datas, sempre com vírgula decimal e ponto de milhar:

```advak
seja preco = 1500.5
imprimir(`Total: ${preco:moeda}`)                         // Total: R$ 1.500,50
imprimir(`Desconto: ${0.075:porcentagem.1}`)              // Desconto: 7,5%
imprimir(`Pedido ${7:03d} | Pi ${3.14159:.2f}`)           // Pedido 007 | Pi 3,14
imprimir(`Hoje: ${"2024-12-25":dd/mm/aaaa} (${"2024-12-25":dddd})`)   // Hoje: 25/12/2024 (quarta-feira)
```

Formatos: `moeda`, `numero`, `porcentagem`, `maiusculo`, `minusculo`, `titulo`, `data`, `hora`, `datahora`,
padrões de data (`dd/mm/aaaa hh:mm`) e estilo Python (`.2f`, `05d`, `>10`). Só vale em textos com crase.

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

**Intervalos** (novo na 5.2): `1..4` vai de 1 até 3 (o fim **não** entra); `1..=4` vai de 1 até 4 (o fim entra).
O `passo` (ou `step`) é opcional e, para contar para trás, use passo negativo:

```advak
para (i em 1..4) { imprimir(i) }              // 1 2 3
para (i em 1..=4) { imprimir(i) }             // 1 2 3 4
para (i em 10..=0 passo -5) { imprimir(i) }   // 10 5 0
seja pares = 2..=10 passo 2                   // fora de um laço vira lista: [2, 4, 6, 8, 10]
```

Intervalos só aceitam números inteiros e `10..1` é um intervalo vazio (não conta para trás sozinho).

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

**Compreensão de listas** (novo na 5.2): monta uma lista nova a partir de outra, em uma linha:

```advak
seja nums = [1, -2, 3, -4, 5]
imprimir([x * 2 para x em nums se x > 0])                 // [2, 6, 10]
imprimir([x * x para x em 1..=5])                         // [1, 4, 9, 16, 25]
imprimir([[a, b] para a em 1..=3 para b em 1..=3 se a < b])   // [[1, 2], [1, 3], [2, 3]]
```

Em inglês: `[x * 2 for x in nums if x > 0]`.

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

## Inteligência artificial (opcional)

> **A IA é totalmente opcional.** A Advak funciona 100% sem ela: sem internet, sem chave e sem custo.
> O módulo de IA (`advak_ia.py`) só é carregado quando o seu programa chama `ia.conectar(...)`. Antes
> disso não há nenhum import, chamada de rede ou gasto. Todo o resto da linguagem, os exemplos e o
> curso funcionam sem ela.

Se quiser usar, é a mesma API para Anthropic (Claude), OpenAI, Gemini, Mistral, Groq, DeepSeek,
OpenRouter e Ollama (local, sem chave):

```advak
seja assistente = ia.conectar(["anthropic", "ollama"])   // reserva automática se o primeiro falhar
imprimir(assistente.perguntar("Explique o que é uma variável em uma frase"))
```

As chaves ficam só no `.env` (`ADVAK_<PROVEDOR>_API_KEY`), nunca no código. O que você envia a uma API
externa sai do computador; para dados sensíveis use o Ollama. Veja [docs/IA.md](docs/IA.md) e o comando
`advak ia`.

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

### Bancos de dados suportados

Além do PostgreSQL de cima, a versão 5.2 conecta com **23 bancos**, todos com os **mesmos comandos**. Para
trocar de banco, você muda só a linha de conexão (a senha fica no `.env`, nunca no programa):

```advak
seja db = banco.conectar("sqlite:///loja.db")      // ou "mysql://usuario:senha@localhost/loja", "mongodb://..."
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Picos"})
para (c em db.buscar("clientes").onde("cidade = %s", "Picos").executar()) {
    imprimir(c.id, c.nome)
}
db.fechar()
```

| Tipo | Bancos |
|---|---|
| Relacionais | **SQLite**, **PostgreSQL**, MySQL, MariaDB, SQL Server, Oracle, Firebird, IBM Db2, CockroachDB |
| Séries temporais | TimescaleDB, InfluxDB |
| Analíticos | DuckDB (em teste / instável no Windows), ClickHouse, Snowflake, Google BigQuery |
| Documentos | MongoDB, CouchDB, Google Firestore, Amazon DynamoDB |
| Busca, cache e grafos | Elasticsearch, Redis, Neo4j |
| Colunar distribuído | Cassandra |

Os drivers são opcionais e só são carregados quando o banco é usado; se faltar um, a Advak mostra o
`pip install` exato. `advak bancos` lista tudo e mostra o que está instalado.

> **Seja honesto com os testes:** só o **SQLite** e o **PostgreSQL** foram testados contra um banco de verdade
> (o PostgreSQL pelo modo antigo `--db` e pelo conector novo). Os outros 21 foram testados com drivers simulados
> (o DuckDB está em teste / instável no Windows). Os capítulos 9 a 12 do guia foram testados só com SQLite ou com bancos simulados. Conectar a um servidor real de MySQL, SQL Server, Firebird, Redis ou MongoDB **ainda não foi testado**. A tabela completa, links de download,
> strings de conexão e um exemplo de cada banco estão em **[docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md)**.

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

### Teclado e mouse

`gui.ao_tecla(tratador)` chama o tratador a cada tecla pressionada na janela principal. Numa tela de desenho (`gui.canvas`), `area.ao_clicar(tratador)` e `area.ao_soltar(tratador)` chamam o tratador quando o botão esquerdo do mouse é pressionado ou solto sobre ela. A variável da tela não pode se chamar `tela` (palavra reservada); aqui ela é `area`.

```advak
seja jan = gui.janela("Teclado e mouse", 320, 200)
seja area = gui.canvas(jan, 300, 140, "branco")
seja bola = area.circulo(150, 70, 10, "azul")

gui.ao_tecla((e) => {
    imprimir("tecla:", e.tecla, "| caractere:", e.caractere)
    se (e.tecla == "esquerda") {
        area.mover(bola, -10, 0)
    }
})
area.ao_clicar((e) => { imprimir("clicou em", e.x, e.y) })
area.ao_soltar((e) => { imprimir("soltou em", e.x, e.y) })

// Daqui até gui.iniciar(): simula a pessoa usando a janela. Num programa de verdade, apague estas linhas.
gui.apos(200, () => {
    jan.focus_force()
    jan.event_generate("<KeyPress>", keysym="a")
    jan.event_generate("<KeyPress>", keysym="Left")
    area.widget.event_generate("<ButtonPress-1>", x=40, y=30)
    area.widget.event_generate("<ButtonRelease-1>", x=40, y=30)
})
gui.apos(1200, () => {
    imprimir("bola em", area.widget.coords(bola))
    gui.parar()
})
gui.iniciar()
imprimir("fechou")
```

Saída deste programa, rodado de verdade (3 vezes, igual nas 3). A janela fecha sozinha por causa do `gui.apos(1200, ...)`:

```text
tecla: a | caractere: a
tecla: esquerda | caractere: 
clicou em 40 30
soltou em 40 30
bola em [130.0, 60.0, 150.0, 80.0]
fechou
```

As linhas de simulação usam `jan.event_generate` e `area.widget`, atalhos para o Tkinter; `area.widget` é provisório e será trocado por eventos em português num passo futuro.

**O que o tratador recebe:**

| Chamada | O tratador recebe |
|---|---|
| `gui.ao_tecla` | `e.tecla` e `e.caractere` |
| `area.ao_clicar`, `area.ao_soltar` | `e.x` e `e.y`: as coordenadas do desenho, números inteiros |

- `tecla` vem em português para sete teclas: `esquerda`, `direita`, `cima`, `baixo`, `espaco`, `enter` e `esc`. As outras seguem o nome do Tk (`a`, `A`, `F1`...). `caractere` é o texto digitado: vazio para setas, Esc e F1, e `"\r"` para enter. O `ç` chega como `ccedilla` em `tecla` e como `ç` em `caractere`.
- Chamar `gui.ao_tecla`, `area.ao_clicar` ou `area.ao_soltar` de novo troca o tratador.
- Uma tecla digitada num campo com foco também chega ao `gui.ao_tecla`; o campo recebe o texto normalmente.
- Só o botão esquerdo do mouse. Não existem `ao_mover` nem tratador de tecla solta.
- Os tratadores rodam um por vez, na ordem em que chegam. Um erro dentro de um tratador aparece no terminal, com a mensagem e a linha.
- `ao_soltar` tem outro sentido em `habilitar_drop` e `kanban`: lá é o tratador de um item arrastado e solto numa área; em `area.ao_soltar` é soltar o botão do mouse sobre a tela.

**O que não foi medido:**

- Se o Windows repete a tecla segurada. O tratador é chamado uma vez por tecla que o Tk entregar, um de cada vez, sem juntar eventos.
- Janela secundária: `gui.ao_tecla` só foi testado na janela principal.
- Programas compilados (`advak_compiler.py`): `gui.ao_tecla` não existe neles. O compilador também não lista `gui.canvas`.

Detalhes e testes: `CHANGELOG.md` e `testes/test_gui_teclado.py`.

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
| `advak bancos` | Lista os 23 bancos suportados e quais drivers estão instalados |
| `advak ia` | Lista os provedores de IA e se a chave está configurada (opcional) |
| `advak documentos` | Lista os formatos de documento que a Advak sabe ler (PDF, DOCX, XLSX...) |
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

Na pasta `testes/` há um `.dk` de teste para cada recurso novo (`intervalos.dk`, `compreensao.dk`,
`formatacao.dk`, `tipagem.dk`, `bancos_sqlite.dk`...), que também servem de exemplo de uso.

### Documentação

| Documento | Conteúdo |
|---|---|
| [docs/curso/README.md](docs/curso/README.md) | **Aprenda a programar com Advak** — curso de 24 aulas para quem nunca programou |
| [docs/INSTALACAO.md](docs/INSTALACAO.md) | Instalação passo a passo (Windows e Linux), PostgreSQL e problemas comuns |
| [docs/GUIA_PRATICO.md](docs/GUIA_PRATICO.md) | Aplicativos completos do dia a dia, explicados linha a linha |
| [docs/BANCOS_DE_DADOS.md](docs/BANCOS_DE_DADOS.md) | Os 23 bancos suportados: quando usar, download, driver, conexão e exemplo |
| [docs/IA.md](docs/IA.md), [docs/DOCUMENTOS.md](docs/DOCUMENTOS.md) | IA e leitura de documentos (opcionais) |
| [docs/RECURSOS_5_2.md](docs/RECURSOS_5_2.md) | Detalhes dos recursos novos da linguagem |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |

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
├── advak_conectores.py      # Conectores dos 23 bancos (API única)
├── advak_ia.py              # IA com 8 provedores (opcional, carregada sob demanda)
├── advak_documentos.py      # Leitura de PDF, DOCX, XLSX, PPTX, imagens (opcional)
├── advak_formatacao.py      # Formatos de ${valor:moeda}, datas e números
├── advak_tipos.py           # Tipagem opcional (seja x: inteiro)
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
├── projetos/                # Mais exemplos e projetos
├── docs/                    # Documentação, guia prático e o curso (docs/curso/)
├── exemplos/                # Aplicativos do guia prático (docs/GUIA_PRATICO.md)
└── testes/                  # Testes de cada recurso (.dk e Python)
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
| `1..10` / `1..=10` / `passo` | `step` | Intervalo sem / com o fim, e o salto |
| `[x para x em l se c]` | `[x for x in l if c]` | Compreensão de listas |
| `: tipo` / `-> tipo` | | Tipo opcional de variável / parâmetro / retorno |

---

## Roadmap

### Recursos para sistemas de varejo, fiscais e não fiscais

A meta é que a linguagem tenha os recursos para quem programa nela criar qualquer sistema, fiscal ou não. **A Advak não é um sistema fiscal:** ela fornece as peças, e a conformidade com a legislação (homologação, certificado, regras da SEFAZ) continua sendo responsabilidade de quem desenvolve o sistema. **Hoje, nenhum destes recursos está pronto ou verificado para uso fiscal:**

- Números decimais exatos para dinheiro e impostos, sem erro de centavos.
- XML: ler, montar e validar (XSD).
- Assinatura digital e certificado (arquivo .pfx), com hash e criptografia.
- Cliente HTTP/SOAP com certificado de cliente (TLS).
- QR Code e código de barras; geração de PDF; impressão em impressora térmica.
- Hardware: porta serial/USB, leitor, balança e gaveta.
- Concorrência real (async/await) e sockets de rede.

O PDV do [guia prático](docs/GUIA_PRATICO.md#capítulo-13--pdv-didático) é didático e **não é PDV fiscal**.

### Ideia para uma versão futura (sem data)

Uma palavra própria para a divisão inteira (por exemplo `div`), deixando o `//` sempre como comentário. Acabaria com a regra de espaços e de parênteses descrita abaixo, mas quebraria os programas que hoje usam `//` como divisão, então exigiria uma versão nova, com aviso de transição. Está só registrada como possibilidade: **não está implementada e não há versão prevista.**

### Limitações conhecidas da linguagem

- **Divisão inteira ou comentário?** O `//` divide quando vem colado ou com um espaço antes (`7//2`, `7 // 2`) e é comentário quando tem 2 ou mais espaços (ou um tab) antes dele, fora de parênteses abertos. Por isso `seja y = 7 // 2   // metade` funciona: a divisão vale 3 e `// metade` é comentário. Com um espaço só (`7 // 2 // metade`), o segundo `//` ainda é lido como outra divisão.
- **Dentro de parênteses abertos o comentário continua sendo lido como divisão.** Vale também para o corpo de uma função escrita como argumento, como `testar(...)`: ali `seja z = (10 // 3)   // 3` tem duas divisões, e um comentário `//` que pareça uma conta, como `// 201 = criado`, é lido como divisão inteira. Comentários com frases normais (`// isto é um comentário`) não são afetados.
- **`advak formatar`** mantém os 2 ou mais espaços antes de um comentário `//` no fim da linha, porque com um espaço só o `//` passaria a ser lido como divisão.

---

## Licença

Este projeto está sob a licença **MIT**. Você pode usar, estudar, modificar e distribuir a Advak Language livremente, inclusive em projetos comerciais, desde que mantenha o aviso de direitos autorais e a licença. Veja o arquivo [LICENSE](LICENSE).

© 2026 Prof. Arimatéa Gomes

## Autor

**Prof. Arimatéa Gomes**
CETI Silvestre Rocha — Arraial, Piauí, Brasil
