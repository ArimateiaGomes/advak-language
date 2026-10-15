# Aula 11 — Mapas (objetos)

> **Ao final desta aula você vai saber:** guardar informações com nome (como a ficha de um aluno), ler e mudar cada campo, percorrer um mapa e montar listas de mapas.

## Uma ficha com campos

Uma lista guarda valores em **posições**. Mas uma ficha de aluno tem **campos com nome**: nome, idade, turma. Para isso existe o **mapa** (também chamado de objeto): pares `chave: valor` entre chaves `{ }`.

<!--codigo:aula11_exemplo1.dk-->
```advak
seja aluno = {nome: "Ana", idade: 17, turma: "3A"}   // três campos
imprimir(aluno)                  // o mapa inteiro
imprimir(aluno.nome)             // lê o campo com ponto
imprimir(aluno["idade"])         // ou com colchetes e o nome entre aspas
imprimir(aluno.turma)
```

<!--saida:aula11_exemplo1.dk-->
```text
{nome: Ana, idade: 17, turma: 3A}
Ana
17
3A
```

## Mudando, criando e removendo campos

<!--codigo:aula11_exemplo2.dk-->
```advak
seja aluno = {nome: "Ana", idade: 17}
aluno.idade = 18                 // muda um campo que já existe
aluno.cidade = "Recife"          // cria um campo novo
aluno["nota"] = 9.5              // também funciona com colchetes
imprimir(aluno)
aluno.remover("nota")            // apaga o campo "nota"
imprimir(aluno)
imprimir(aluno.tem("idade"))     // o campo existe?
imprimir(aluno.tem("nota"))
imprimir(aluno.cor)              // campo que não existe: vale nulo (nada)
```

<!--saida:aula11_exemplo2.dk-->
```text
{nome: Ana, idade: 18, cidade: Recife, nota: 9.5}
{nome: Ana, idade: 18, cidade: Recife}
verdadeiro
falso
nulo
```

## Percorrendo um mapa

`aluno.chaves` é a lista dos nomes dos campos e `aluno.valores` é a lista dos valores:

<!--codigo:aula11_exemplo3.dk-->
```advak
seja aluno = {nome: "Ana", idade: 17, turma: "3A"}
imprimir(aluno.chaves)
imprimir(aluno.valores)
para (campo em aluno.chaves) {              // uma volta para cada campo
    imprimir(campo, "=", aluno[campo])      // com colchetes, "campo" é uma variável
}
```

<!--saida:aula11_exemplo3.dk-->
```text
['nome', 'idade', 'turma']
['Ana', 17, '3A']
nome = Ana
idade = 17
turma = 3A
```

Repare: `aluno.nome` lê o campo chamado *nome*. Já `aluno[campo]` lê o campo cujo nome está **guardado na variável** `campo`.

## Lista de mapas: a turma inteira

Juntando as duas ideias, temos uma "planilha": cada linha é um mapa.

<!--codigo:aula11_exemplo4.dk-->
```advak
seja turma = [
    {nome: "Ana", nota: 8},
    {nome: "Bia", nota: 5.5},
    {nome: "Caio", nota: 9}
]
para (aluno em turma) {
    imprimir(aluno.nome, "tirou", aluno.nota)
}
imprimir("Primeiro da lista:", turma[0].nome)
```

<!--saida:aula11_exemplo4.dk-->
```text
Ana tirou 8
Bia tirou 5.5
Caio tirou 9
Primeiro da lista: Ana
```

## Mapa dentro de mapa

<!--codigo:aula11_exemplo5.dk-->
```advak
seja pessoa = {
    nome: "Ana",
    endereco: {rua: "Rua das Flores", numero: 42}
}
imprimir(pessoa.endereco.rua)       // entra no mapa de dentro, campo por campo
imprimir(pessoa.endereco.numero)
```

<!--saida:aula11_exemplo5.dk-->
```text
Rua das Flores
42
```

## Erros comuns

**1. Esquecer as aspas ao usar colchetes com um nome fixo.** Sem aspas, a Advak procura uma **variável**:

<!--codigo:aula11_erro1.dk-->
```advak
seja aluno = {nome: "Ana"}
imprimir(aluno[nome])
```

Mensagem real:

<!--erro:aula11_erro1.dk-->
```text
Localização: linha 2
Problema:    Variável 'nome' não definida
```

**Como corrigir:** use `aluno["nome"]` (com aspas) ou `aluno.nome` (com ponto).

**2. Achar que um campo que não existe dá erro.** A Advak devolve `nulo`. Se o resultado aparecer vazio ou `nulo`, confira se escreveu o nome do campo certo (maiúsculas e acentos contam!).

## Exercícios

1. Crie um mapa `livro` com `titulo`, `autor` e `paginas`, e mostre cada campo.
2. Crie um mapa `carro` e depois mude o campo `ano` e adicione o campo `cor`.
3. Crie um mapa com sua ficha (nome, idade, cidade) e mostre `chave = valor` para cada campo.
4. Peça nome e idade, monte um mapa com as respostas e mostre o mapa.
5. Crie uma lista com três produtos (`nome` e `preco`) e mostre o **total** dos preços.
6. Na mesma lista de produtos, mostre o nome do produto mais caro.
7. **Desafio:** conte quantas vezes cada palavra aparece em `["sol", "lua", "sol", "mar", "sol", "lua"]`, guardando as contagens em um mapa.

## Respostas

**Exercício 1**

<!--codigo:aula11_resposta1.dk-->
```advak
seja livro = {titulo: "Dom Casmurro", autor: "Machado de Assis", paginas: 256}
imprimir("Título:", livro.titulo)
imprimir("Autor:", livro.autor)
imprimir("Páginas:", livro.paginas)
```

<!--saida:aula11_resposta1.dk-->
```text
Título: Dom Casmurro
Autor: Machado de Assis
Páginas: 256
```

**Exercício 2**

<!--codigo:aula11_resposta2.dk-->
```advak
seja carro = {modelo: "Fusca", ano: 1970}
carro.ano = 1972
carro.cor = "azul"
imprimir(carro)
```

<!--saida:aula11_resposta2.dk-->
```text
{modelo: Fusca, ano: 1972, cor: azul}
```

**Exercício 3**

<!--codigo:aula11_resposta3.dk-->
```advak
seja ficha = {nome: "Ana", idade: 17, cidade: "Recife"}
para (campo em ficha.chaves) {
    imprimir(campo, "=", ficha[campo])
}
```

<!--saida:aula11_resposta3.dk-->
```text
nome = Ana
idade = 17
cidade = Recife
```

**Exercício 4**

<!--codigo:aula11_resposta4.dk-->
```advak
seja nome = entrada("Nome: ")
seja idade = numero(entrada("Idade: "))
seja pessoa = {nome: nome, idade: idade}
imprimir(pessoa)
```

<!--entrada:aula11_resposta4
Bia
16
-->
<!--saida:aula11_resposta4.dk-->
```text
Nome: Bia
Idade: 16
{nome: Bia, idade: 16}
```

**Exercício 5**

<!--codigo:aula11_resposta5.dk-->
```advak
seja produtos = [
    {nome: "Caderno", preco: 12.5},
    {nome: "Caneta", preco: 3},
    {nome: "Mochila", preco: 80}
]
seja total = 0
para (p em produtos) {
    total = total + p.preco
}
imprimir("Total:", total)
```

<!--saida:aula11_resposta5.dk-->
```text
Total: 95.5
```

**Exercício 6**

<!--codigo:aula11_resposta6.dk-->
```advak
seja produtos = [
    {nome: "Caderno", preco: 12.5},
    {nome: "Caneta", preco: 3},
    {nome: "Mochila", preco: 80}
]
seja mais_caro = produtos[0]
para (p em produtos) {
    se (p.preco > mais_caro.preco) {
        mais_caro = p
    }
}
imprimir("Mais caro:", mais_caro.nome)
```

<!--saida:aula11_resposta6.dk-->
```text
Mais caro: Mochila
```

**Exercício 7**

<!--codigo:aula11_resposta7.dk-->
```advak
seja palavras = ["sol", "lua", "sol", "mar", "sol", "lua"]
seja contagem = {}
para (p em palavras) {
    se (contagem.tem(p)) {
        contagem[p] = contagem[p] + 1     // já apareceu: soma 1
    } senão {
        contagem[p] = 1                   // primeira vez
    }
}
imprimir(contagem)
```

<!--saida:aula11_resposta7.dk-->
```text
{sol: 3, lua: 2, mar: 1}
```

---

**Anterior:** [Aula 10](aula10_listas.md) · **Próxima aula:** [Aula 12 — Funções](aula12_funcoes.md)
