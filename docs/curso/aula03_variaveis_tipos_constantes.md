# Aula 3 — Variáveis, tipos e constantes (`seja`, `fixo`, `tipo`)

> **Ao final desta aula você vai saber:** guardar valores em variáveis com `seja`, criar valores que não mudam com `fixo`, descobrir o tipo de um valor com `tipo` e escolher bons nomes.

## Variável: uma caixinha com nome

Imagine caixinhas etiquetadas na cozinha: "açúcar", "farinha". A etiqueta é o **nome**; o que está dentro é o **valor**. Uma **variável** é isso: um nome que guarda um valor na memória do computador. Você cria com **`seja`**:

<!--codigo:aula03_exemplo1.dk-->
```advak
seja nome = "Ana"          // cria a variável "nome" e guarda o texto Ana
seja idade = 17            // cria a variável "idade" e guarda o número 17
imprimir(nome)             // escreve o valor guardado: Ana
imprimir(idade)            // escreve 17
idade = idade + 1          // muda o valor guardado (sem "seja", pois a variável já existe)
imprimir("Ano que vem:", idade)
```

Saída:

<!--saida:aula03_exemplo1.dk-->
```text
Ana
17
Ano que vem: 18
```

Regra de ouro: **`seja` cria a variável (só uma vez); depois, para mudar o valor, escreva só `nome = novo valor`.**

## Constante: um valor que não muda

Algumas coisas nunca mudam durante o programa, como o valor de π. Use **`fixo`**; se alguém tentar alterar, a Advak avisa:

<!--codigo:aula03_exemplo2.dk-->
```advak
fixo PI = 3.14159          // constante: por convenção, o nome fica em MAIÚSCULAS
fixo ESCOLA = "Escola Modelo"
seja raio = 2
imprimir("Área do círculo:", PI * raio * raio)
imprimir(ESCOLA)
```

Saída:

<!--saida:aula03_exemplo2.dk-->
```text
Área do círculo: 12.56636
Escola Modelo
```

## Tipos: que espécie de valor é esse?

Cada valor tem um **tipo**. A função `tipo(...)` diz qual é:

<!--codigo:aula03_exemplo3.dk-->
```advak
imprimir(tipo(17))              // número (inteiro ou decimal)
imprimir(tipo(3.5))             // número com vírgula: também é "numero"
imprimir(tipo("Ana"))           // texto, sempre entre aspas
imprimir(tipo(verdadeiro))      // booleano: só pode ser verdadeiro ou falso
imprimir(tipo([1, 2, 3]))       // lista: vários valores em ordem
imprimir(tipo({nome: "Ana"}))   // objeto (mapa): valores com nome
imprimir(tipo(nulo))            // nulo: "nada", "vazio"
```

Saída:

<!--saida:aula03_exemplo3.dk-->
```text
numero
numero
texto
booleano
lista
objeto
nulo
```

| Tipo | Exemplo | Para que serve |
|---|---|---|
| `numero` | `17`, `3.5` | contas |
| `texto` | `"Ana"` | nomes, frases |
| `booleano` | `verdadeiro`, `falso` | respostas de sim/não |
| `lista` | `[1, 2, 3]` | vários valores (aula 10) |
| `objeto` | `{nome: "Ana"}` | dados com nome (aula 11) |
| `nulo` | `nulo` | ausência de valor |

Atenção: `17` é número e `"17"` (com aspas) é **texto**. Parecem iguais, mas o computador os trata de forma diferente (você verá na aula 4).

## Tipo opcional (para quem quer mais segurança)

Você pode **declarar** o tipo que a variável deve guardar. É opcional, mas ajuda a pegar enganos:

<!--codigo:aula03_exemplo4.dk-->
```advak
seja idade: inteiro = 17        // "idade" só aceita números inteiros
imprimir(idade)
```

Saída:

<!--saida:aula03_exemplo4.dk-->
```text
17
```

## Bons nomes

- Use nomes que expliquem o conteúdo: `nota_final` é melhor que `x`.
- Sem espaços: use `_` (`nome_completo`).
- Não comece com número (`1nota` não vale).
- A Advak diferencia maiúsculas de minúsculas e letras com acento: `Nome`, `nome` e `nomé` são três variáveis diferentes.
- **Não use palavras reservadas** (como `se`, `para`, `endereco`): veja a lista em [GUIA_PRATICO.md](../GUIA_PRATICO.md#palavras-reservadas).

## Erros comuns

**1. Mudar uma constante:**

<!--codigo:aula03_erro1.dk-->
```advak
fixo PI = 3.14
PI = 3
```

Mensagem real:

<!--erro:aula03_erro1.dk-->
```text
Tipo:    ImmutableError
Detalhe: [Advak] Erro de imutabilidade: 'PI' é imutável e não pode ser reatribuído
```

**Como corrigir:** se o valor precisa mudar, use `seja` em vez de `fixo`.

**2. Usar uma variável antes de criá-la (ou errar o nome):**

<!--codigo:aula03_erro2.dk-->
```advak
seja nota = 8
imprimir(note)
```

Mensagem real:

<!--erro:aula03_erro2.dk-->
```text
Localização: linha 2
Problema:    Variável 'note' não definida
```

**Como corrigir:** confira a escrita: `nota`, não `note`.

**3. Usar uma palavra reservada como nome:**

<!--codigo:aula03_erro3.dk-->
```advak
seja endereco = "Rua A"
```

Mensagem real:

<!--erro:aula03_erro3.dk-->
```text
Localização: linha 1
Problema:    esperado 'IDENT', encontrado 'endereco'
```

**Como corrigir:** troque o nome: `seja rua = "Rua A"`.

## Exercícios

1. Crie as variáveis `produto` (texto) e `preco` (número) e imprima as duas.
2. Crie `saldo` com 100, depois some 50 a ele e imprima o novo saldo.
3. Crie a constante `PI` e calcule a área de um círculo de raio 5 (`PI * raio * raio`).
4. Use `tipo(...)` para descobrir o tipo de `42`, `"42"` e `verdadeiro`.
5. Troque o valor de duas variáveis: `a = 1` e `b = 2`; no final, `a` deve valer 2 e `b` valer 1 (dica: use uma terceira variável).
6. **Desafio:** declare `seja nome: texto = "Ana"` e imprima. Depois tente guardar um número nessa variável e observe o que acontece.

## Respostas

**Exercício 1**

<!--codigo:aula03_resposta1.dk-->
```advak
seja produto = "Caderno"
seja preco = 12.5
imprimir(produto)
imprimir(preco)
```

<!--saida:aula03_resposta1.dk-->
```text
Caderno
12.5
```

**Exercício 2**

<!--codigo:aula03_resposta2.dk-->
```advak
seja saldo = 100
saldo = saldo + 50
imprimir("Novo saldo:", saldo)
```

<!--saida:aula03_resposta2.dk-->
```text
Novo saldo: 150
```

**Exercício 3**

<!--codigo:aula03_resposta3.dk-->
```advak
fixo PI = 3.14159
seja raio = 5
imprimir("Área:", PI * raio * raio)
```

<!--saida:aula03_resposta3.dk-->
```text
Área: 78.53975
```

**Exercício 4**

<!--codigo:aula03_resposta4.dk-->
```advak
imprimir(tipo(42))
imprimir(tipo("42"))
imprimir(tipo(verdadeiro))
```

<!--saida:aula03_resposta4.dk-->
```text
numero
texto
booleano
```

**Exercício 5**

<!--codigo:aula03_resposta5.dk-->
```advak
seja a = 1
seja b = 2
seja auxiliar = a      // guarda o valor de a antes de perdê-lo
a = b
b = auxiliar
imprimir("a =", a, " b =", b)
```

<!--saida:aula03_resposta5.dk-->
```text
a = 2  b = 1
```

**Exercício 6**

<!--codigo:aula03_erro_resposta6.dk-->
```advak
seja nome: texto = "Ana"
imprimir(nome)
nome = 123
imprimir(nome)
```

<!--erro:aula03_erro_resposta6.dk-->
```text
Problema:    Tipo incorreto: 'nome' é texto, mas recebeu inteiro (123).
```

A Advak mostra o `Ana` e depois recusa o número: é ela protegendo você, porque a variável foi declarada como `texto`.

---

**Anterior:** [Aula 2](aula02_repl_e_arquivos.md) · **Próxima aula:** [Aula 4 — Entrada de dados e conversão](aula04_entrada_e_conversao.md)
