# Aula 7 — Escolha múltipla com `combinar`

> **Ao final desta aula você vai saber:** escolher entre vários valores possíveis usando `combinar`, sem encher o programa de `senão se`.

## Para que serve

Imagine o menu de uma lanchonete: o cliente diz um número e o caixa escolhe o que fazer. Com `senão se` ficaria assim:

```
se (opcao == 1) { ... } senão se (opcao == 2) { ... } senão se (opcao == 3) { ... }
```

O `combinar` faz o mesmo de forma mais limpa. Ele olha **um valor** e procura o `caso` igual a ele:

<!--codigo:aula07_exemplo1.dk-->
```advak
seja dia = numero(entrada("Dia da semana (1 a 7): "))
combinar(dia) {                       // o valor que será comparado
    caso 1: imprimir("Domingo")       // se dia == 1
    caso 2: imprimir("Segunda")
    caso 3: imprimir("Terça")
    padrão: imprimir("Outro dia")     // se nenhum caso combinou
}
```

Com `3`:

<!--entrada:aula07_exemplo1
3
-->
<!--saida:aula07_exemplo1.dk-->
```text
Dia da semana (1 a 7): 3
Terça
```

O `padrão:` é o "senão" do `combinar`: roda quando nenhum `caso` combina. Ele é opcional, mas é boa prática ter.

## Casos com textos

Funciona com texto também:

<!--codigo:aula07_exemplo2.dk-->
```advak
seja op = entrada("Operação (+, -, *): ")
seja a = 8
seja b = 2
combinar(op) {
    caso "+": imprimir(a + b)
    caso "-": imprimir(a - b)
    caso "*": imprimir(a * b)
    padrão: imprimir("Operação desconhecida")
}
```

Digitando `*`:

<!--entrada:aula07_exemplo2
*
-->
<!--saida:aula07_exemplo2.dk-->
```text
Operação (+, -, *): *
16
```

## Vários comandos em um caso

Para rodar mais de um comando, coloque entre chaves `{ }`, ou escreva os comandos nas linhas seguintes:

<!--codigo:aula07_exemplo3.dk-->
```advak
seja opcao = 2
combinar(opcao) {
    caso 1:
        imprimir("Abrindo o cadastro...")
    caso 2:
        imprimir("Abrindo o relatório...")
        imprimir("Aguarde um instante.")
    padrão:
        imprimir("Opção inválida")
}
```

<!--saida:aula07_exemplo3.dk-->
```text
Abrindo o relatório...
Aguarde um instante.
```

Só o caso que combina roda; os outros são ignorados (não é preciso `parar` como em outras linguagens).

## `combinar` com condições

Um truque útil: use `combinar(verdadeiro)` e escreva **condições** nos casos. O primeiro `caso` verdadeiro vence:

<!--codigo:aula07_exemplo4.dk-->
```advak
seja nota = numero(entrada("Nota: "))
combinar(verdadeiro) {
    caso nota >= 9: imprimir("Conceito A")
    caso nota >= 7: imprimir("Conceito B")
    caso nota >= 5: imprimir("Conceito C")
    padrão:         imprimir("Conceito F")
}
```

Com a nota `7.5`:

<!--entrada:aula07_exemplo4
7.5
-->
<!--saida:aula07_exemplo4.dk-->
```text
Nota: 7.5
Conceito B
```

## Erros comuns

**1. Esquecer os dois-pontos depois do caso:**

<!--codigo:aula07_erro1.dk-->
```advak
seja x = 2
combinar(x) {
    caso 1 imprimir("um")
}
```

Mensagem real:

<!--erro:aula07_erro1.dk-->
```text
Localização: linha 3
Problema:    esperado 'COLON', encontrado 'imprimir'
```

**Como corrigir:** escreva `caso 1:` (com `:`) antes do comando.

**2. Tentar dois valores no mesmo caso (`caso 1, 2:`).** A Advak não aceita vírgula no `caso`:

<!--codigo:aula07_erro2.dk-->
```advak
seja x = 2
combinar(x) {
    caso 1, 2: imprimir("pequeno")
}
```

Mensagem real:

<!--erro:aula07_erro2.dk-->
```text
Localização: linha 3
Problema:    esperado 'COLON', encontrado ','
```

**Como corrigir:** use `combinar(verdadeiro)` com `caso x == 1 ou x == 2:`, ou repita o comando em dois casos.

## Exercícios

1. Peça um número de 1 a 3 e escreva `um`, `dois` ou `três` por extenso (`padrão`: `fora do intervalo`).
2. Peça o número do mês (1 a 12) e escreva quantos dias ele tem em um ano comum (fevereiro: 28; abril, junho, setembro, novembro: 30; os outros: 31). Dica: use `combinar(verdadeiro)`.
3. Faça uma calculadora: peça dois números e a operação (`+`, `-`, `*`, `/`) e mostre o resultado.
4. Peça uma letra de nota (`A`, `B`, `C`) e escreva `Ótimo`, `Bom` ou `Regular`; qualquer outra: `Letra inválida`.
5. Peça a idade e classifique: criança (até 11), adolescente (12 a 17), adulto (18 a 59) ou idoso (60 ou mais).
6. **Desafio:** menu de lanchonete. Mostre `1-Pão`, `2-Suco`, `3-Bolo`, peça a opção e a quantidade, e escreva o total (pão R$ 5, suco R$ 7, bolo R$ 9).

## Respostas

**Exercício 1**

<!--codigo:aula07_resposta1.dk-->
```advak
seja n = numero(entrada("Número de 1 a 3: "))
combinar(n) {
    caso 1: imprimir("um")
    caso 2: imprimir("dois")
    caso 3: imprimir("três")
    padrão: imprimir("fora do intervalo")
}
```

<!--entrada:aula07_resposta1
2
-->
<!--saida:aula07_resposta1.dk-->
```text
Número de 1 a 3: 2
dois
```

**Exercício 2**

<!--codigo:aula07_resposta2.dk-->
```advak
seja mes = numero(entrada("Mês (1 a 12): "))
combinar(verdadeiro) {
    caso mes == 2: imprimir("28 dias")
    caso mes == 4 ou mes == 6 ou mes == 9 ou mes == 11: imprimir("30 dias")
    padrão: imprimir("31 dias")
}
```

<!--entrada:aula07_resposta2
9
-->
<!--saida:aula07_resposta2.dk-->
```text
Mês (1 a 12): 9
30 dias
```

**Exercício 3**

<!--codigo:aula07_resposta3.dk-->
```advak
seja a = numero(entrada("Primeiro número: "))
seja b = numero(entrada("Segundo número: "))
seja op = entrada("Operação (+, -, *, /): ")
combinar(op) {
    caso "+": imprimir(a + b)
    caso "-": imprimir(a - b)
    caso "*": imprimir(a * b)
    caso "/": imprimir(a / b)
    padrão: imprimir("Operação inválida")
}
```

<!--entrada:aula07_resposta3
10
4
/
-->
<!--saida:aula07_resposta3.dk-->
```text
Primeiro número: 10
Segundo número: 4
Operação (+, -, *, /): /
2.5
```

**Exercício 4**

<!--codigo:aula07_resposta4.dk-->
```advak
seja letra = entrada("Nota (A, B ou C): ")
combinar(letra) {
    caso "A": imprimir("Ótimo")
    caso "B": imprimir("Bom")
    caso "C": imprimir("Regular")
    padrão: imprimir("Letra inválida")
}
```

<!--entrada:aula07_resposta4
B
-->
<!--saida:aula07_resposta4.dk-->
```text
Nota (A, B ou C): B
Bom
```

**Exercício 5**

<!--codigo:aula07_resposta5.dk-->
```advak
seja idade = numero(entrada("Idade: "))
combinar(verdadeiro) {
    caso idade <= 11: imprimir("Criança")
    caso idade <= 17: imprimir("Adolescente")
    caso idade <= 59: imprimir("Adulto")
    padrão: imprimir("Idoso")
}
```

<!--entrada:aula07_resposta5
65
-->
<!--saida:aula07_resposta5.dk-->
```text
Idade: 65
Idoso
```

**Exercício 6**

<!--codigo:aula07_resposta6.dk-->
```advak
imprimir("1-Pão  2-Suco  3-Bolo")
seja opcao = numero(entrada("Opção: "))
seja qtd = numero(entrada("Quantidade: "))
seja preco = 0
combinar(opcao) {
    caso 1: preco = 5
    caso 2: preco = 7
    caso 3: preco = 9
    padrão: imprimir("Opção inválida")
}
imprimir("Total: R$", preco * qtd)
```

<!--entrada:aula07_resposta6
2
3
-->
<!--saida:aula07_resposta6.dk-->
```text
1-Pão  2-Suco  3-Bolo
Opção: 2
Quantidade: 3
Total: R$ 21
```

---

**Anterior:** [Aula 6](aula06_decisoes.md) · **Próxima aula:** [Aula 8 — Repetição com `enquanto`](aula08_enquanto.md)
