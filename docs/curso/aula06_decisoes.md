# Aula 6 — Decisões: `se`, `senão se`, `senão`

> **Ao final desta aula você vai saber:** fazer o programa tomar decisões, escolhendo caminhos diferentes conforme uma condição.

## Tomando decisões

No dia a dia decidimos o tempo todo: **se** está chovendo, levo guarda-chuva; **senão**, vou sem. Na Advak:

```
se (condição) {
    ... roda se a condição for verdadeira
} senão {
    ... roda se for falsa
}
```

A **condição** é uma comparação (aula 5) que dá `verdadeiro` ou `falso`. O que está entre as chaves `{ }` é o **bloco**.

<!--codigo:aula06_exemplo1.dk-->
```advak
seja idade = numero(entrada("Qual é a sua idade? "))
se (idade >= 18) {                       // a condição vai entre parênteses
    imprimir("Você é maior de idade.")   // só roda se a condição for verdadeira
} senão {
    imprimir("Você é menor de idade.")   // só roda se for falsa
}
imprimir("Fim do programa.")              // fora das chaves: roda sempre
```

Com a idade `20` e depois, em outra execução, com `15`:

<!--entrada:aula06_exemplo1
20
-->
<!--saida:aula06_exemplo1.dk-->
```text
Qual é a sua idade? 20
Você é maior de idade.
Fim do programa.
```

Rodando de novo, agora digitando 15:

<!--codigo:aula06_exemplo1b.dk-->
```advak
seja idade = numero(entrada("Qual é a sua idade? "))
se (idade >= 18) {
    imprimir("Você é maior de idade.")
} senão {
    imprimir("Você é menor de idade.")
}
imprimir("Fim do programa.")
```

<!--entrada:aula06_exemplo1b
15
-->
<!--saida:aula06_exemplo1b.dk-->
```text
Qual é a sua idade? 15
Você é menor de idade.
Fim do programa.
```

## Mais de dois caminhos: `senão se`

Quando há várias possibilidades, encadeie com `senão se`. A Advak testa de cima para baixo e **para no primeiro que for verdadeiro**:

<!--codigo:aula06_exemplo2.dk-->
```advak
seja nota = numero(entrada("Digite a nota: "))
se (nota >= 7) {
    imprimir("Aprovado")
} senão se (nota >= 5) {          // só chega aqui se nota < 7
    imprimir("Recuperação")
} senão {                         // só chega aqui se nota < 5
    imprimir("Reprovado")
}
```

Com a nota `6`:

<!--entrada:aula06_exemplo2
6
-->
<!--saida:aula06_exemplo2.dk-->
```text
Digite a nota: 6
Recuperação
```

## Combinando condições

Use `e`, `ou` e `nao` (aula 5) dentro da condição:

<!--codigo:aula06_exemplo3.dk-->
```advak
seja idade = numero(entrada("Idade: "))
seja tem_ingresso = verdadeiro
se (idade >= 14 e tem_ingresso) {
    imprimir("Pode entrar no show.")
} senão {
    imprimir("Não pode entrar.")
}
```

Com a idade `12`:

<!--entrada:aula06_exemplo3
12
-->
<!--saida:aula06_exemplo3.dk-->
```text
Idade: 12
Não pode entrar.
```

## Erros comuns

**1. Esquecer de fechar a chave `}`:**

<!--codigo:aula06_erro1.dk-->
```advak
seja x = 10
se (x > 5) {
    imprimir("maior")
```

Mensagem real:

<!--erro:aula06_erro1.dk-->
```text
Problema:    [Advak] Linha ?: esperado 'RCURLY', encontrado 'fim do arquivo'
```

**Como corrigir:** cada `{` precisa de um `}` correspondente. Olhe o recuo (as linhas com espaço no começo) para achar o bloco que ficou aberto.

**2. Usar `senão` sem `se` antes.** A Advak **não reclama** (o bloco simplesmente roda), então o erro é silencioso e perigoso:

<!--codigo:aula06_erro2.dk-->
```advak
senão {
    imprimir("sozinho")
}
```

O resultado:

<!--saida:aula06_erro2.dk-->
```text
sozinho
```

**Como corrigir:** o `senão` sempre acompanha um `se`. Escreva primeiro o `se (condição) { ... }`; sem ele, esse bloco roda sempre, o que quase nunca é o que você quer.

## Exercícios

1. Peça um número e diga se ele é **positivo** ou **não positivo** (zero ou negativo).
2. Peça um número e diga se é **par** ou **ímpar** (dica: `% 2`).
3. Peça a nota e mostre `Aprovado` (>= 7), `Recuperação` (>= 5) ou `Reprovado`.
4. Um cinema cobra R$ 10 de quem tem menos de 12 anos, R$ 20 de quem tem de 12 a 59 e R$ 10 de quem tem 60 ou mais. Peça a idade e mostre o preço.
5. Peça dois números e diga qual é o **maior** (ou se são iguais).
6. **Desafio:** peça o ano e diga se é **bissexto**: divisível por 4 e não por 100, ou divisível por 400.

## Respostas

**Exercício 1**

<!--codigo:aula06_resposta1.dk-->
```advak
seja n = numero(entrada("Digite um número: "))
se (n > 0) {
    imprimir("Positivo")
} senão {
    imprimir("Não positivo")
}
```

<!--entrada:aula06_resposta1
-3
-->
<!--saida:aula06_resposta1.dk-->
```text
Digite um número: -3
Não positivo
```

**Exercício 2**

<!--codigo:aula06_resposta2.dk-->
```advak
seja n = inteiro(entrada("Digite um número: "))
se (n % 2 == 0) {
    imprimir("Par")
} senão {
    imprimir("Ímpar")
}
```

<!--entrada:aula06_resposta2
7
-->
<!--saida:aula06_resposta2.dk-->
```text
Digite um número: 7
Ímpar
```

**Exercício 3**

<!--codigo:aula06_resposta3.dk-->
```advak
seja nota = numero(entrada("Nota: "))
se (nota >= 7) {
    imprimir("Aprovado")
} senão se (nota >= 5) {
    imprimir("Recuperação")
} senão {
    imprimir("Reprovado")
}
```

<!--entrada:aula06_resposta3
4.5
-->
<!--saida:aula06_resposta3.dk-->
```text
Nota: 4.5
Reprovado
```

**Exercício 4**

<!--codigo:aula06_resposta4.dk-->
```advak
seja idade = inteiro(entrada("Idade: "))
se (idade < 12 ou idade >= 60) {
    imprimir("Ingresso: R$ 10")
} senão {
    imprimir("Ingresso: R$ 20")
}
```

<!--entrada:aula06_resposta4
65
-->
<!--saida:aula06_resposta4.dk-->
```text
Idade: 65
Ingresso: R$ 10
```

**Exercício 5**

<!--codigo:aula06_resposta5.dk-->
```advak
seja a = numero(entrada("Primeiro número: "))
seja b = numero(entrada("Segundo número: "))
se (a > b) {
    imprimir("O maior é", a)
} senão se (b > a) {
    imprimir("O maior é", b)
} senão {
    imprimir("São iguais")
}
```

<!--entrada:aula06_resposta5
8
12
-->
<!--saida:aula06_resposta5.dk-->
```text
Primeiro número: 8
Segundo número: 12
O maior é 12
```

**Exercício 6**

<!--codigo:aula06_resposta6.dk-->
```advak
seja ano = inteiro(entrada("Ano: "))
se ((ano % 4 == 0 e ano % 100 != 0) ou ano % 400 == 0) {
    imprimir("Bissexto")
} senão {
    imprimir("Não é bissexto")
}
```

<!--entrada:aula06_resposta6
2024
-->
<!--saida:aula06_resposta6.dk-->
```text
Ano: 2024
Bissexto
```

---

**Anterior:** [Aula 5](aula05_operadores.md) · **Próxima aula:** [Aula 7 — Escolha múltipla com `combinar`](aula07_combinar.md)
