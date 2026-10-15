# Aula 20 — Testes unitários

> **Ao final desta aula você vai saber:** escrever testes que conferem sozinhos se as suas funções funcionam, usando `testar`, `afirmar_igual`, `afirmar_erro` e companhia, e ler o resultado.

## Por que testar

Você escreve uma função, roda uma vez, parece certa. Duas semanas depois muda uma linha em outro lugar... e a função antiga quebra sem ninguém perceber. Um **teste** é uma conferência automática: você escreve uma vez "para esta entrada, espero esta resposta" e, sempre que quiser, roda tudo e vê se continua valendo. É como o gabarito de uma prova: em segundos você sabe o que acertou e o que errou.

Chamamos de **teste unitário** o teste de uma peça pequena (uma função, um método) de cada vez.

## O primeiro teste

Dois comandos formam a base:

- `testar("descrição", () => { ... })` define um teste, com um nome que explica o que está sendo conferido;
- `afirmar_igual(real, esperado)` diz: "o valor real tem que ser igual ao esperado".

<!--codigo:aula20_exemplo1.dk-->
```advak
função dobro(x) {
    retornar x * 2
}

testar("dobro de 3 é 6", () => {
    afirmar_igual(dobro(3), 6)
})

testar("dobro de zero é zero", () => {
    afirmar_igual(dobro(0), 0)
})

testar("dobro de negativo", () => {
    afirmar_igual(dobro(-5), -10)
})
```

<!--saida:aula20_exemplo1.dk-->
```text
  ✅ dobro de 3 é 6
  ✅ dobro de zero é zero
  ✅ dobro de negativo
```

Cada ✅ é um teste que passou. A parte `() => { ... }` é uma lambda (aula 13) sem parâmetros: o teste é "a receita" que a Advak executa. Os parênteses `()` são obrigatórios.

## Quando um teste falha

Aqui está o valor dos testes: quando o resultado não é o esperado, a Advak mostra ❌ e **explica a diferença**. Vamos escrever uma função com um defeito de propósito e um resumo no fim com `resumo_testes()`:

<!--codigo:aula20_exemplo2.dk-->
```advak
função media(a, b) {
    retornar a + b / 2                  // defeito: faltaram os parênteses
}

testar("média de 4 e 6 é 5", () => {
    afirmar_igual(media(4, 6), 5)
})

testar("média de 10 e 10 é 10", () => {
    afirmar_igual(media(10, 10), 10)
})

resumo_testes()
```

<!--saida:aula20_exemplo2.dk-->
```text
  ❌ média de 4 e 6 é 5
     Esperado 5, obteve 7.0
  ❌ média de 10 e 10 é 10
     Esperado 10, obteve 15.0

  ────────────────────────────────────────────
  Resultado: 0/2 testes passaram  (2 falharam)
```

Os dois testes falharam, e a Advak disse o porquê: `4 + 6 / 2` é `7.0` (a divisão acontece antes da soma) e `10 + 10 / 2` é `15.0`. Sem o teste, esse defeito poderia passar despercebido por muito tempo. Corrija com parênteses, `(a + b) / 2`, e rode de novo:

<!--codigo:aula20_exemplo3.dk-->
```advak
função media(a, b) {
    retornar (a + b) / 2                // corrigido
}

testar("média de 4 e 6 é 5", () => {
    afirmar_igual(media(4, 6), 5)
})

testar("média de 10 e 10 é 10", () => {
    afirmar_igual(media(10, 10), 10)
})

resumo_testes()
```

<!--saida:aula20_exemplo3.dk-->
```text
  ✅ média de 4 e 6 é 5
  ✅ média de 10 e 10 é 10

  ────────────────────────────────────────────
  Resultado: 2/2 testes passaram  🎉
```

`resumo_testes()` mostra quantos testes passaram. Ele também **devolve** um mapa com `total`, `passou` e `falhou`, caso você queira usar esses números.

## Os outros comandos de conferência

| Comando | Passa quando... |
|---|---|
| `afirmar_igual(a, b)` | `a` é igual a `b` (funciona com textos, listas e mapas também) |
| `afirmar_diferente(a, b)` | `a` é diferente de `b` |
| `afirmar_verdadeiro(v)` | `v` é verdadeiro |
| `afirmar_falso(v)` | `v` é falso |
| `afirmar_nulo(v)` | `v` é `nulo` |
| `afirmar_contem(colecao, item)` | o item está na lista (ou o pedaço está no texto) |
| `afirmar(condicao, "mensagem")` | a condição é verdadeira; senão mostra a mensagem |
| `afirmar_erro(() => ...)` | o código **dá erro** |

<!--codigo:aula20_exemplo4.dk-->
```advak
função eh_par(n) {
    retornar n % 2 == 0
}

função dividir(a, b) {
    se (b == 0) {
        lançar "divisão por zero"
    }
    retornar a / b
}

testar("verdadeiro e falso", () => {
    afirmar_verdadeiro(eh_par(10))
    afirmar_falso(eh_par(7))
})

testar("diferente", () => {
    afirmar_diferente(eh_par(2), eh_par(3))
})

testar("lista e texto", () => {
    afirmar_igual([1, 2, 3], [1, 2, 3])
    afirmar_contem([10, 20, 30], 20)
    afirmar_contem("banana", "nan")
})

testar("nulo", () => {
    seja vazio = nulo
    afirmar_nulo(vazio)
})

testar("dividir por zero tem que dar erro", () => {
    afirmar_erro(() => dividir(1, 0))
})

testar("dividir normal não dá erro", () => {
    afirmar_igual(dividir(9, 3), 3)
})

testar("afirmar com mensagem própria", () => {
    afirmar(eh_par(4), "4 deveria ser par")
})

resumo_testes()
```

<!--saida:aula20_exemplo4.dk-->
```text
  ✅ verdadeiro e falso
  ✅ diferente
  ✅ lista e texto
  ✅ nulo
  ✅ dividir por zero tem que dar erro
  ✅ dividir normal não dá erro
  ✅ afirmar com mensagem própria

  ────────────────────────────────────────────
  Resultado: 7/7 testes passaram  🎉
```

Dentro de um mesmo `testar` você pode ter várias afirmações; o teste passa só se **todas** passarem (a primeira que falhar encerra o teste).

## Testando um módulo

Testes ficam ótimos em um arquivo separado, que importa o que vai testar (aula 19). Usando o módulo `aula19_matematica.dk`:

<!--codigo:aula20_exemplo5.dk-->
```advak
importar { dobro, area_circulo } de "aula19_matematica.dk"

testar("dobro", () => {
    afirmar_igual(dobro(21), 42)
})

testar("área do círculo de raio 1 é PI", () => {
    afirmar_igual(area_circulo(1), 3.14159)
})

testar("área com raio 0", () => {
    afirmar_igual(area_circulo(0), 0)
})

resumo_testes()
```

<!--saida:aula20_exemplo5.dk-->
```text
  ✅ dobro
  ✅ área do círculo de raio 1 é PI
  ✅ área com raio 0

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

## Escrevendo o teste primeiro

Muita gente experiente escreve o teste **antes** da função. Parece estranho, mas ajuda a pensar: "o que eu espero que ela faça?". O roteiro é:

1. escreva o teste (ele vai falhar, porque a função não existe ou está incompleta);
2. escreva o mínimo de código para o teste passar;
3. rode tudo de novo.

Exemplo: queremos uma função `situacao(media)` que diga `"aprovado"` com média 7 ou mais:

<!--codigo:aula20_exemplo6.dk-->
```advak
função situacao(media) {
    se (media >= 7) {
        retornar "aprovado"
    }
    se (media >= 5) {
        retornar "recuperação"
    }
    retornar "reprovado"
}

testar("7 aprova", () => {
    afirmar_igual(situacao(7), "aprovado")
})
testar("10 aprova", () => {
    afirmar_igual(situacao(10), "aprovado")
})
testar("entre 5 e 7 é recuperação", () => {
    afirmar_igual(situacao(6.9), "recuperação")
    afirmar_igual(situacao(5), "recuperação")
})
testar("abaixo de 5 reprova", () => {
    afirmar_igual(situacao(4.9), "reprovado")
    afirmar_igual(situacao(0), "reprovado")
})

resumo_testes()
```

<!--saida:aula20_exemplo6.dk-->
```text
  ✅ 7 aprova
  ✅ 10 aprova
  ✅ entre 5 e 7 é recuperação
  ✅ abaixo de 5 reprova

  ────────────────────────────────────────────
  Resultado: 4/4 testes passaram  🎉
```

Repare que testamos os **limites** (7, 6.9, 5, 4.9): é nas bordas que os defeitos mais aparecem.

## Erros comuns

**1. Comparar decimais.** Computadores guardam decimais de forma aproximada, e `0.1 + 0.2` não é exatamente `0.3`:

<!--codigo:aula20_erro1.dk-->
```advak
testar("soma de decimais", () => {
    afirmar_igual(0.1 + 0.2, 0.3)
})
```

<!--saida:aula20_erro1.dk-->
```text
  ❌ soma de decimais
     Esperado 0.3, obteve 0.30000000000000004
```

**Como corrigir:** compare a diferença: `afirmar_verdadeiro(abs(0.1 + 0.2 - 0.3) < 0.0001)`.

**2. Chamar a função em vez de passá-la ao `afirmar_erro`.** Sem o `() =>`, o erro acontece *antes* de o `afirmar_erro` poder pegá-lo:

<!--codigo:aula20_erro2.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "divisão por zero"
    }
    retornar a / b
}

testar("dividir por zero dá erro", () => {
    afirmar_erro(dividir(1, 0))
})
```

<!--saida:aula20_erro2.dk-->
```text
  ❌ dividir por zero dá erro
     divisão por zero
```

**Como corrigir:** escreva `afirmar_erro(() => dividir(1, 0))`.

**3. Trocar a ordem esperado/real.** `afirmar_igual(real, esperado)`: a mensagem de falha diz "Esperado X, obteve Y" a partir dessa ordem. Se trocar, a mensagem engana.

<!--codigo:aula20_erro3.dk-->
```advak
testar("ordem trocada", () => {
    afirmar_igual(10, 2 + 2)             // o "real" é o primeiro; aqui está invertido
})
```

<!--saida:aula20_erro3.dk-->
```text
  ❌ ordem trocada
     Esperado 4, obteve 10
```

**Como corrigir:** coloque primeiro o que a função devolveu (`real`) e depois o que você esperava.

**4. Testar uma função que ainda não foi definida.** A Advak lê o arquivo de cima para baixo e roda cada `testar` na hora. Se os testes vêm *antes* da `função`, ela ainda não existe:

<!--codigo:aula20_erro4.dk-->
```advak
// Primeiro os testes...
testar("1 fica 1", () => {
    afirmar_igual(fizzbuzz(1), 1)
})
testar("3 é Fizz", () => {
    afirmar_igual(fizzbuzz(3), "Fizz")
})
testar("5 é Buzz", () => {
    afirmar_igual(fizzbuzz(5), "Buzz")
})
testar("15 é FizzBuzz", () => {
    afirmar_igual(fizzbuzz(15), "FizzBuzz")
})
testar("7 fica 7", () => {
    afirmar_igual(fizzbuzz(7), 7)
})

// ...depois a função
função fizzbuzz(n) {
    se (n % 15 == 0) {
        retornar "FizzBuzz"
    }
    se (n % 3 == 0) {
        retornar "Fizz"
    }
    se (n % 5 == 0) {
        retornar "Buzz"
    }
    retornar n
}

resumo_testes()
```

<!--saida:aula20_erro4.dk-->
```text
  ❌ 1 fica 1
     Variável 'fizzbuzz' não definida
  ❌ 3 é Fizz
     Variável 'fizzbuzz' não definida
  ❌ 5 é Buzz
     Variável 'fizzbuzz' não definida
  ❌ 15 é FizzBuzz
     Variável 'fizzbuzz' não definida
  ❌ 7 fica 7
     Variável 'fizzbuzz' não definida

  ────────────────────────────────────────────
  Resultado: 0/5 testes passaram  (5 falharam)
```

**Como corrigir:** coloque a `função` acima dos testes. (O roteiro "teste primeiro" vale para o seu raciocínio: você pensa e escreve os testes antes de preencher a função, mas no arquivo ela fica antes.)

## Exercícios

1. Escreva a função `dobro(x)` e três testes: com número positivo, negativo e zero.
2. Escreva `eh_maior_de_idade(idade)` (18 ou mais) e teste os limites: 17, 18 e 19.
3. Escreva `maior(a, b)` e teste com `a > b`, `a < b` e `a == b`.
4. Escreva `inverter(texto)` (use um laço) e teste com `"abc"`, `""` e `"a"`.
5. Teste uma função `raiz_segura(n)` que lança `"negativo"` se `n < 0`: um teste para `raiz_segura(9)` e outro com `afirmar_erro` para `raiz_segura(-1)`.
6. Escreva `contar_vogais(texto)` e teste com `"banana"`, `"xyz"` e `"AEIOU"`.
7. Use `afirmar_contem` para testar uma função `multiplos_de_3(ate)` que devolve a lista dos múltiplos de 3 até `ate`.
8. **Desafio:** pense primeiro nos testes e depois escreva a função `fizzbuzz(n)`, que devolve `"Fizz"` para múltiplos de 3, `"Buzz"` para múltiplos de 5, `"FizzBuzz"` para os dois e o próprio número nos outros casos. Use os valores 1, 3, 5, 15 e 7.

## Respostas

**Exercício 1**

<!--codigo:aula20_resposta1.dk-->
```advak
função dobro(x) {
    retornar x * 2
}

testar("positivo", () => {
    afirmar_igual(dobro(4), 8)
})
testar("negativo", () => {
    afirmar_igual(dobro(-3), -6)
})
testar("zero", () => {
    afirmar_igual(dobro(0), 0)
})

resumo_testes()
```

<!--saida:aula20_resposta1.dk-->
```text
  ✅ positivo
  ✅ negativo
  ✅ zero

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

**Exercício 2**

<!--codigo:aula20_resposta2.dk-->
```advak
função eh_maior_de_idade(idade) {
    retornar idade >= 18
}

testar("17 anos", () => {
    afirmar_falso(eh_maior_de_idade(17))
})
testar("18 anos", () => {
    afirmar_verdadeiro(eh_maior_de_idade(18))
})
testar("19 anos", () => {
    afirmar_verdadeiro(eh_maior_de_idade(19))
})

resumo_testes()
```

<!--saida:aula20_resposta2.dk-->
```text
  ✅ 17 anos
  ✅ 18 anos
  ✅ 19 anos

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

**Exercício 3**

<!--codigo:aula20_resposta3.dk-->
```advak
função maior(a, b) {
    se (a >= b) {
        retornar a
    }
    retornar b
}

testar("a maior", () => {
    afirmar_igual(maior(5, 2), 5)
})
testar("b maior", () => {
    afirmar_igual(maior(2, 5), 5)
})
testar("iguais", () => {
    afirmar_igual(maior(4, 4), 4)
})

resumo_testes()
```

<!--saida:aula20_resposta3.dk-->
```text
  ✅ a maior
  ✅ b maior
  ✅ iguais

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

**Exercício 4**

<!--codigo:aula20_resposta4.dk-->
```advak
função inverter(texto) {
    seja resultado = ""
    para (letra em texto) {
        resultado = letra + resultado
    }
    retornar resultado
}

testar("abc", () => {
    afirmar_igual(inverter("abc"), "cba")
})
testar("vazio", () => {
    afirmar_igual(inverter(""), "")
})
testar("uma letra", () => {
    afirmar_igual(inverter("a"), "a")
})

resumo_testes()
```

<!--saida:aula20_resposta4.dk-->
```text
  ✅ abc
  ✅ vazio
  ✅ uma letra

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

**Exercício 5**

<!--codigo:aula20_resposta5.dk-->
```advak
função raiz_segura(n) {
    se (n < 0) {
        lançar "negativo"
    }
    retornar n ** 0.5
}

testar("raiz de 9", () => {
    afirmar_igual(raiz_segura(9), 3)
})
testar("raiz de negativo dá erro", () => {
    afirmar_erro(() => raiz_segura(-1))
})

resumo_testes()
```

<!--saida:aula20_resposta5.dk-->
```text
  ✅ raiz de 9
  ✅ raiz de negativo dá erro

  ────────────────────────────────────────────
  Resultado: 2/2 testes passaram  🎉
```

**Exercício 6**

<!--codigo:aula20_resposta6.dk-->
```advak
função contar_vogais(texto) {
    seja total = 0
    para (letra em texto.minusculo()) {
        se ("aeiou".contem(letra)) {
            total = total + 1
        }
    }
    retornar total
}

testar("banana", () => {
    afirmar_igual(contar_vogais("banana"), 3)
})
testar("xyz", () => {
    afirmar_igual(contar_vogais("xyz"), 0)
})
testar("maiúsculas", () => {
    afirmar_igual(contar_vogais("AEIOU"), 5)
})

resumo_testes()
```

<!--saida:aula20_resposta6.dk-->
```text
  ✅ banana
  ✅ xyz
  ✅ maiúsculas

  ────────────────────────────────────────────
  Resultado: 3/3 testes passaram  🎉
```

**Exercício 7**

<!--codigo:aula20_resposta7.dk-->
```advak
função multiplos_de_3(ate) {
    seja lista = []
    para (n em 1..ate + 1) {
        se (n % 3 == 0) {
            lista.adicionar(n)
        }
    }
    retornar lista
}

testar("até 10", () => {
    seja m = multiplos_de_3(10)
    afirmar_contem(m, 3)
    afirmar_contem(m, 9)
    afirmar_igual(m.tamanho, 3)
})

resumo_testes()
```

<!--saida:aula20_resposta7.dk-->
```text
  ✅ até 10

  ────────────────────────────────────────────
  Resultado: 1/1 testes passaram  🎉
```

**Exercício 8**

<!--codigo:aula20_resposta8.dk-->
```advak
função fizzbuzz(n) {
    se (n % 15 == 0) {
        retornar "FizzBuzz"
    }
    se (n % 3 == 0) {
        retornar "Fizz"
    }
    se (n % 5 == 0) {
        retornar "Buzz"
    }
    retornar n
}

testar("1 fica 1", () => {
    afirmar_igual(fizzbuzz(1), 1)
})
testar("3 é Fizz", () => {
    afirmar_igual(fizzbuzz(3), "Fizz")
})
testar("5 é Buzz", () => {
    afirmar_igual(fizzbuzz(5), "Buzz")
})
testar("15 é FizzBuzz", () => {
    afirmar_igual(fizzbuzz(15), "FizzBuzz")
})
testar("7 fica 7", () => {
    afirmar_igual(fizzbuzz(7), 7)
})

resumo_testes()
```

<!--saida:aula20_resposta8.dk-->
```text
  ✅ 1 fica 1
  ✅ 3 é Fizz
  ✅ 5 é Buzz
  ✅ 15 é FizzBuzz
  ✅ 7 fica 7

  ────────────────────────────────────────────
  Resultado: 5/5 testes passaram  🎉
```

---

**Anterior:** [Aula 19](aula19_modulos.md) · **Próxima aula:** [Aula 21 — Banco de dados: primeiro contato](aula21_banco_de_dados.md)
