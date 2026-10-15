# Aula 12 — Funções, parâmetros e retorno

> **Ao final desta aula você vai saber:** criar suas próprias funções, passar informações para elas (parâmetros) e receber um resultado de volta (`retornar`).

## Uma receita com nome

Você já usou funções prontas: `imprimir`, `entrada`, `numero`. Uma **função** é um trecho de código com **nome**, que podemos usar quantas vezes quisermos. É como uma receita: escrevemos uma vez e "chamamos" quando precisar.

<!--codigo:aula12_exemplo1.dk-->
```advak
função saudar() {                      // define a função (ainda não executa nada)
    imprimir("Olá! Seja bem-vindo(a).")
}

saudar()                               // chama a função: agora o bloco executa
saudar()                               // pode chamar quantas vezes quiser
```

<!--saida:aula12_exemplo1.dk-->
```text
Olá! Seja bem-vindo(a).
Olá! Seja bem-vindo(a).
```

## Parâmetros: passando informação

Os **parâmetros** ficam entre parênteses e são como variáveis que só existem dentro da função. Quem chama passa os **argumentos** (os valores):

<!--codigo:aula12_exemplo2.dk-->
```advak
função saudar(nome) {                  // "nome" é o parâmetro
    imprimir("Olá,", nome)
}

saudar("Ana")                          // "Ana" é o argumento
saudar("Bia")
```

<!--saida:aula12_exemplo2.dk-->
```text
Olá, Ana
Olá, Bia
```

## Retorno: devolvendo um resultado

`retornar` devolve um valor para quem chamou a função e **encerra** a função. Assim podemos guardar ou usar o resultado:

<!--codigo:aula12_exemplo3.dk-->
```advak
função somar(a, b) {
    retornar a + b                     // devolve o resultado
}

seja total = somar(3, 4)               // o resultado é guardado em "total"
imprimir(total)
imprimir(somar(10, 5) * 2)             // pode ser usado direto em uma conta
```

<!--saida:aula12_exemplo3.dk-->
```text
7
30
```

## Valor padrão

Um parâmetro pode ter um valor que vale quando ninguém o informa:

<!--codigo:aula12_exemplo4.dk-->
```advak
função saudar(nome, saudacao = "Olá") {     // "Olá" é o padrão
    retornar saudacao + ", " + nome + "!"
}

imprimir(saudar("Ana"))                     // usa o padrão
imprimir(saudar("Bia", "Bom dia"))          // troca o padrão
```

<!--saida:aula12_exemplo4.dk-->
```text
Olá, Ana!
Bom dia, Bia!
```

## Funções que decidem

Dentro de uma função cabe tudo o que você já aprendeu:

<!--codigo:aula12_exemplo5.dk-->
```advak
função situacao(nota) {
    se (nota >= 7) {
        retornar "Aprovado"
    } senão se (nota >= 5) {
        retornar "Recuperação"
    }
    retornar "Reprovado"               // só chega aqui se nenhum "se" acima retornou
}

para (n em [9, 6, 3]) {
    imprimir(n, "->", situacao(n))
}
```

<!--saida:aula12_exemplo5.dk-->
```text
9 -> Aprovado
6 -> Recuperação
3 -> Reprovado
```

## Variáveis locais

Uma variável criada **dentro** da função só existe lá dentro:

<!--codigo:aula12_exemplo6.dk-->
```advak
função calcular() {
    seja segredo = 42                  // variável local
    retornar segredo
}

imprimir(calcular())                   // a função devolve o valor: isso funciona
```

<!--saida:aula12_exemplo6.dk-->
```text
42
```

Mas a variável `segredo` não existe fora da função: veja nos erros comuns, logo abaixo.

## Erros comuns

**1. Chamar uma função que não existe (ou escrever o nome errado):**

<!--codigo:aula12_erro1.dk-->
```advak
função dobro(x) {
    retornar x * 2
}
imprimir(dobr(5))
```

Mensagem real:

<!--erro:aula12_erro1.dk-->
```text
Localização: linha 4
Problema:    Variável 'dobr' não definida
```

**Como corrigir:** confira o nome (`dobro`, não `dobr`).

**2. Esquecer o `retornar`.** A função roda, mas devolve `nulo` (nada):

<!--codigo:aula12_erro2.dk-->
```advak
função somar(a, b) {
    seja resultado = a + b
}
imprimir(somar(2, 3))
```

<!--saida:aula12_erro2.dk-->
```text
nulo
```

**Como corrigir:** acrescente `retornar resultado` no fim da função.

**3. Usar fora da função uma variável criada dentro dela:**

<!--codigo:aula12_erro3.dk-->
```advak
função calcular() {
    seja segredo = 42
    retornar segredo
}
calcular()
imprimir(segredo)
```

Mensagem real:

<!--erro:aula12_erro3.dk-->
```text
Localização: linha 6
Problema:    Variável 'segredo' não definida
```

**Como corrigir:** guarde o que a função devolve: `seja resultado = calcular()` e use `resultado`.

**4. Confundir `imprimir` com `retornar`.** `imprimir` só mostra na tela; `retornar` devolve o valor para o programa continuar usando.

## Exercícios

1. Crie a função `apresentar()` que escreve três linhas sobre você e chame-a duas vezes.
2. Crie `dobro(n)` que devolve o dobro de um número e mostre `dobro(21)`.
3. Crie `area_retangulo(base, altura)` e mostre a área de um retângulo de 5 por 3.
4. Crie `e_par(n)` que devolve `verdadeiro` ou `falso`, e teste com 10 e 7.
5. Crie `maior(a, b)` que devolve o maior dos dois números.
6. Crie `media(a, b, c)` e `situacao(media)`; peça três notas e mostre a média e a situação.
7. Crie `fatorial(n)` usando um laço e mostre o fatorial de 6.
8. **Desafio:** crie `e_primo(n)` e use-a para listar os primos até 30.

## Respostas

**Exercício 1**

<!--codigo:aula12_resposta1.dk-->
```advak
função apresentar() {
    imprimir("Meu nome é Ana.")
    imprimir("Eu estudo programação.")
    imprimir("Meu sonho é criar um aplicativo.")
}
apresentar()
apresentar()
```

<!--saida:aula12_resposta1.dk-->
```text
Meu nome é Ana.
Eu estudo programação.
Meu sonho é criar um aplicativo.
Meu nome é Ana.
Eu estudo programação.
Meu sonho é criar um aplicativo.
```

**Exercício 2**

<!--codigo:aula12_resposta2.dk-->
```advak
função dobro(n) {
    retornar n * 2
}
imprimir(dobro(21))
```

<!--saida:aula12_resposta2.dk-->
```text
42
```

**Exercício 3**

<!--codigo:aula12_resposta3.dk-->
```advak
função area_retangulo(base, altura) {
    retornar base * altura
}
imprimir("Área:", area_retangulo(5, 3))
```

<!--saida:aula12_resposta3.dk-->
```text
Área: 15
```

**Exercício 4**

<!--codigo:aula12_resposta4.dk-->
```advak
função e_par(n) {
    retornar n % 2 == 0
}
imprimir(e_par(10))
imprimir(e_par(7))
```

<!--saida:aula12_resposta4.dk-->
```text
verdadeiro
falso
```

**Exercício 5**

<!--codigo:aula12_resposta5.dk-->
```advak
função maior(a, b) {
    se (a > b) {
        retornar a
    }
    retornar b
}
imprimir(maior(8, 12))
```

<!--saida:aula12_resposta5.dk-->
```text
12
```

**Exercício 6**

<!--codigo:aula12_resposta6.dk-->
```advak
função media(a, b, c) {
    retornar (a + b + c) / 3
}
função situacao(m) {
    se (m >= 7) {
        retornar "Aprovado"
    }
    se (m >= 5) {
        retornar "Recuperação"
    }
    retornar "Reprovado"
}
seja n1 = numero(entrada("Nota 1: "))
seja n2 = numero(entrada("Nota 2: "))
seja n3 = numero(entrada("Nota 3: "))
seja m = media(n1, n2, n3)
imprimir("Média:", m, "-", situacao(m))
```

<!--entrada:aula12_resposta6
8
6
7
-->
<!--saida:aula12_resposta6.dk-->
```text
Nota 1: 8
Nota 2: 6
Nota 3: 7
Média: 7.0 - Aprovado
```

**Exercício 7**

<!--codigo:aula12_resposta7.dk-->
```advak
função fatorial(n) {
    seja resultado = 1
    para (i em 2..=n) {
        resultado = resultado * i
    }
    retornar resultado
}
imprimir(fatorial(6))
```

<!--saida:aula12_resposta7.dk-->
```text
720
```

**Exercício 8**

<!--codigo:aula12_resposta8.dk-->
```advak
função e_primo(n) {
    se (n < 2) {
        retornar falso
    }
    para (d em 2..n) {
        se (n % d == 0) {
            retornar falso            // achou um divisor: não é primo
        }
    }
    retornar verdadeiro
}
para (n em 1..=30) {
    se (e_primo(n)) {
        imprimir(n)
    }
}
```

<!--saida:aula12_resposta8.dk-->
```text
2
3
5
7
11
13
17
19
23
29
```

---

**Anterior:** [Aula 11](aula11_mapas.md) · **Próxima aula:** [Aula 13 — Lambdas, `filtrar`, `mapear`, `reduzir` e o pipeline `|>`](aula13_lambdas.md)
