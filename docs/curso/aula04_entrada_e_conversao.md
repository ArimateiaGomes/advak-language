# Aula 4 — Entrada de dados com `entrada` e conversão com `numero` e `texto`

> **Ao final desta aula você vai saber:** perguntar algo ao usuário com `entrada`, entender por que tudo que se digita chega como **texto** e converter para número com `numero` e `inteiro`.

## Perguntando ao usuário

Até agora os programas sempre faziam a mesma coisa. Com **`entrada("pergunta")`** o programa mostra uma pergunta, **espera a pessoa digitar** e devolve o que ela digitou. Guarde o resultado em uma variável:

<!--codigo:aula04_exemplo1.dk-->
```advak
seja nome = entrada("Qual é o seu nome? ")   // mostra a pergunta e espera você digitar e apertar Enter
imprimir("Olá, " + nome + "!")                // + junta textos
```

Nesta execução, a pessoa digitou `Marina` (a parte depois da pergunta):

<!--entrada:aula04_exemplo1
Marina
-->
<!--saida:aula04_exemplo1.dk-->
```text
Qual é o seu nome? Marina
Olá, Marina!
```

## O que chega é sempre texto

Mesmo que você digite `17`, a Advak recebe o **texto** `"17"`. Por isso, para fazer contas, é preciso **converter**:

| Função | O que faz | Exemplo |
|---|---|---|
| `numero(x)` | vira número (aceita decimais) | `numero("3.5")` → 3.5 |
| `inteiro(x)` | vira número inteiro | `inteiro("7")` → 7 |
| `texto(x)` | vira texto | `texto(42)` → `"42"` |

<!--codigo:aula04_exemplo2.dk-->
```advak
seja a = entrada("Primeiro número: ")        // chega como texto
seja b = entrada("Segundo número: ")          // chega como texto
imprimir("Sem converter:", a + b)             // texto + texto = junta os dois (não soma!)
imprimir("Convertendo:", numero(a) + numero(b))   // número + número = soma de verdade
```

Digitando `4` e `5`:

<!--entrada:aula04_exemplo2
4
5
-->
<!--saida:aula04_exemplo2.dk-->
```text
Primeiro número: 4
Segundo número: 5
Sem converter: 45
Convertendo: 9
```

Veja: `"4" + "5"` virou `45` (dois textos colados), mas `numero("4") + numero("5")` deu `9`.

## Um programa útil: a média de duas notas

<!--codigo:aula04_exemplo3.dk-->
```advak
imprimir("=== Média de duas notas ===")
seja nota1 = numero(entrada("Nota 1: "))     // pergunta e já converte para número
seja nota2 = numero(entrada("Nota 2: "))
seja media = (nota1 + nota2) / 2             // parênteses mandam fazer a soma primeiro
imprimir("Média:", media)
```

Com as notas `7` e `8.5`:

<!--entrada:aula04_exemplo3
7
8.5
-->
<!--saida:aula04_exemplo3.dk-->
```text
=== Média de duas notas ===
Nota 1: 7
Nota 2: 8.5
Média: 7.75
```

## Juntando texto e números

Para escrever frases com valores, o jeito mais prático é o **texto com crases** (`` ` ``) e `${...}`, que você verá em detalhes na aula 14:

<!--codigo:aula04_exemplo4.dk-->
```advak
seja nome = entrada("Nome: ")
seja idade = inteiro(entrada("Idade: "))
imprimir(`${nome} tem ${idade} anos e terá ${idade + 1} no ano que vem.`)
```

<!--entrada:aula04_exemplo4
Joana
15
-->
<!--saida:aula04_exemplo4.dk-->
```text
Nome: Joana
Idade: 15
Joana tem 15 anos e terá 16 no ano que vem.
```

## Erros comuns

**1. Digitar letras onde se espera um número.** Se a pessoa digita `abc` e o programa faz `numero("abc")`:

<!--codigo:aula04_erro1.dk-->
```advak
seja n = numero(entrada("Digite um número: "))
imprimir(n * 2)
```

<!--entrada:aula04_erro1
abc
-->

Mensagem real (digitando `abc`):

<!--erro:aula04_erro1.dk-->
```text
0
```

**Como corrigir:** repare que a Advak **não deu erro**: `numero("abc")` virou `0` e a conta saiu errada sem avisar. Na aula 15 você aprende a conferir o que foi digitado (`e_numero`) e a tratar problemas com `tentar`/`capturar`. Por enquanto, digite apenas números.

**2. Esquecer de converter e somar textos:** `"4" + "5"` dá `45`, não `9` (veja o Exemplo 2). Converta com `numero(...)`.

## Exercícios

1. Pergunte o nome da pessoa e responda `Bem-vindo, <nome>!`.
2. Peça dois números e mostre a **soma**.
3. Peça o preço de um produto e a quantidade comprada; mostre o total.
4. Peça um valor em reais e mostre o dobro dele.
5. Peça o ano de nascimento e mostre a idade aproximada (use 2026 como ano atual).
6. **Desafio:** peça o nome, o ano de nascimento e escreva uma frase só: `Ana tem cerca de 17 anos.` usando crases.

## Respostas

**Exercício 1**

<!--codigo:aula04_resposta1.dk-->
```advak
seja nome = entrada("Seu nome: ")
imprimir("Bem-vindo, " + nome + "!")
```

<!--entrada:aula04_resposta1
Carlos
-->
<!--saida:aula04_resposta1.dk-->
```text
Seu nome: Carlos
Bem-vindo, Carlos!
```

**Exercício 2**

<!--codigo:aula04_resposta2.dk-->
```advak
seja a = numero(entrada("Primeiro número: "))
seja b = numero(entrada("Segundo número: "))
imprimir("Soma:", a + b)
```

<!--entrada:aula04_resposta2
12
30.5
-->
<!--saida:aula04_resposta2.dk-->
```text
Primeiro número: 12
Segundo número: 30.5
Soma: 42.5
```

**Exercício 3**

<!--codigo:aula04_resposta3.dk-->
```advak
seja preco = numero(entrada("Preço do produto: "))
seja quantidade = inteiro(entrada("Quantidade: "))
imprimir("Total:", preco * quantidade)
```

<!--entrada:aula04_resposta3
12.5
4
-->
<!--saida:aula04_resposta3.dk-->
```text
Preço do produto: 12.5
Quantidade: 4
Total: 50.0
```

**Exercício 4**

<!--codigo:aula04_resposta4.dk-->
```advak
seja valor = numero(entrada("Valor em reais: "))
imprimir("O dobro é:", valor * 2)
```

<!--entrada:aula04_resposta4
45.75
-->
<!--saida:aula04_resposta4.dk-->
```text
Valor em reais: 45.75
O dobro é: 91.5
```

**Exercício 5**

<!--codigo:aula04_resposta5.dk-->
```advak
seja nascimento = inteiro(entrada("Ano de nascimento: "))
imprimir("Idade aproximada:", 2026 - nascimento)
```

<!--entrada:aula04_resposta5
2009
-->
<!--saida:aula04_resposta5.dk-->
```text
Ano de nascimento: 2009
Idade aproximada: 17
```

**Exercício 6**

<!--codigo:aula04_resposta6.dk-->
```advak
seja nome = entrada("Nome: ")
seja nascimento = inteiro(entrada("Ano de nascimento: "))
imprimir(`${nome} tem cerca de ${2026 - nascimento} anos.`)
```

<!--entrada:aula04_resposta6
Ana
2009
-->
<!--saida:aula04_resposta6.dk-->
```text
Nome: Ana
Ano de nascimento: 2009
Ana tem cerca de 17 anos.
```

---

**Anterior:** [Aula 3](aula03_variaveis_tipos_constantes.md) · **Próxima aula:** [Aula 5 — Operadores](aula05_operadores.md)
