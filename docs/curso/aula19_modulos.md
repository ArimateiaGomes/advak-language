# Aula 19 — Módulos

> **Ao final desta aula você vai saber:** dividir um programa grande em vários arquivos, escolher o que cada arquivo mostra aos outros com `exportar`, e usar essas peças com `importar`.

## Por que dividir em arquivos

Um programa de 2.000 linhas num arquivo só é como uma gaveta onde tudo foi jogado junto: ninguém acha nada. Melhor é separar por assunto: um arquivo para as contas, outro para os textos, outro para o banco de dados. Cada arquivo `.dk` que oferece funções, classes ou valores para os outros é chamado de **módulo**.

Dois comandos fazem a ligação:

- `exportar` — no módulo: "estas peças podem ser usadas por quem me importar";
- `importar` — no programa que quer usar: "traga estas peças daquele arquivo".

> **Onde a Advak procura o módulo:** na pasta onde você está rodando o programa (e na subpasta `projetos`). Por isso, nos exemplos, o módulo e o programa ficam na **mesma pasta**.

## Criando o primeiro módulo

Este é o arquivo `aula19_matematica.dk`. Ele não imprime nada: só oferece peças.

<!--codigo:aula19_matematica.dk-->
```advak
fixo PI = 3.14159

função dobro(x) {
    retornar x * 2
}

função area_circulo(raio) {
    retornar PI * raio * raio
}

função segredo() {                       // esta NÃO vai ser exportada
    retornar "uso interno"
}

exportar { PI, dobro, area_circulo }     // só estas três ficam disponíveis
```

E este é o programa que usa o módulo (`aula19_exemplo1.dk`):

<!--codigo:aula19_exemplo1.dk-->
```advak
importar { PI, dobro, area_circulo } de "aula19_matematica.dk"

imprimir("PI vale", PI)
imprimir("O dobro de 4 é", dobro(4))
imprimir("Área de um círculo de raio 2:", area_circulo(2))
```

<!--saida:aula19_exemplo1.dk-->
```text
PI vale 3.14159
O dobro de 4 é 8
Área de um círculo de raio 2: 12.56636
```

Leia `importar { a, b } de "arquivo.dk"` como: "traga `a` e `b` do arquivo". Depois disso, você usa `PI`, `dobro` e `area_circulo` como se tivessem sido escritos no seu programa.

## Só o que foi exportado aparece

A função `segredo` existe dentro do módulo, mas como ficou fora do `exportar`, ninguém de fora a enxerga. É uma boa prática: o módulo mostra só o que é para ser usado e esconde os detalhes.

<!--codigo:aula19_exemplo2.dk-->
```advak
importar { dobro } de "aula19_matematica.dk"

imprimir(dobro(10))

tentar {
    imprimir(segredo())                  // não foi importada
} capturar (e) {
    imprimir("Não deu:", e)
}
```

<!--saida:aula19_exemplo2.dk-->
```text
20
Não deu: Variável 'segredo' não definida
```

## Outro jeito de exportar

Em vez de uma lista no fim do arquivo, você pode escrever `exportar` na frente de cada peça. Também dá para exportar classes. Arquivo `aula19_loja.dk`:

<!--codigo:aula19_loja.dk-->
```advak
exportar fixo MOEDA = "R$"

exportar função com_desconto(preco, percentual) {
    retornar preco * (1 - percentual / 100)
}

exportar classe Produto {
    construtor(nome, preco) {
        isso.nome = nome
        isso.preco = preco
    }
    etiqueta() {
        retornar `${isso.nome}: ${MOEDA} ${isso.preco}`
    }
}
```

Programa que usa (`aula19_exemplo3.dk`):

<!--codigo:aula19_exemplo3.dk-->
```advak
importar { Produto, com_desconto, MOEDA } de "aula19_loja.dk"

seja caderno = novo Produto("Caderno", 20)
imprimir(caderno.etiqueta())
imprimir("Com 25% de desconto:", MOEDA, com_desconto(caderno.preco, 25))
```

<!--saida:aula19_exemplo3.dk-->
```text
Caderno: R$ 20
Com 25% de desconto: R$ 15.0
```

## Trocando o nome com `como`

Se o nome do módulo conflita com algo que você já tem, ou é longo demais, dê outro nome na importação:

<!--codigo:aula19_exemplo4.dk-->
```advak
importar { dobro como duplicar, area_circulo como area } de "aula19_matematica.dk"

imprimir(duplicar(21))
imprimir(area(1))
```

<!--saida:aula19_exemplo4.dk-->
```text
42
3.14159
```

## Módulos que usam módulos

Um módulo também pode importar de outro. Veja `aula19_precos.dk`, que usa o módulo da loja:

<!--codigo:aula19_precos.dk-->
```advak
importar { com_desconto } de "aula19_loja.dk"

exportar função preco_promocional(preco) {
    retornar com_desconto(preco, 10)
}
```

<!--codigo:aula19_exemplo5.dk-->
```advak
importar { preco_promocional } de "aula19_precos.dk"

imprimir(preco_promocional(200))
```

<!--saida:aula19_exemplo5.dk-->
```text
180.0
```

## O que roda quando importa

Quando você importa, o arquivo inteiro do módulo roda **uma vez**, de cima a baixo (por isso é melhor módulo só ter funções e valores, sem `imprimir` solto). Importar o mesmo módulo de novo não roda outra vez. Veja o módulo `aula19_barulhento.dk`:

<!--codigo:aula19_barulhento.dk-->
```advak
imprimir("(carregando o módulo barulhento)")

exportar função oi() {
    retornar "oi!"
}
```

<!--codigo:aula19_exemplo6.dk-->
```advak
imprimir("início")
importar { oi } de "aula19_barulhento.dk"
imprimir(oi())
importar { oi } de "aula19_barulhento.dk"       // segunda vez: não carrega de novo
imprimir(oi())
```

<!--saida:aula19_exemplo6.dk-->
```text
início
(carregando o módulo barulhento)
oi!
oi!
```

## Erros comuns

**1. Importar algo que o módulo não exportou:**

<!--codigo:aula19_erro1.dk-->
```advak
importar { segredo } de "aula19_matematica.dk"
imprimir(segredo())
```

Mensagem real:

<!--erro:aula19_erro1.dk-->
```text
Localização: linha 2
Problema:    'segredo' não exportado por 'aula19_matematica.dk'
```

**Como corrigir:** coloque o nome no `exportar` do módulo (ou use só o que ele exporta).

**2. Arquivo do módulo com o nome errado ou em outra pasta:**

<!--codigo:aula19_erro2.dk-->
```advak
importar { dobro } de "aula19_matematicaa.dk"
imprimir(dobro(2))
```

Mensagem real:

<!--erro:aula19_erro2.dk-->
```text
Problema:    Módulo não encontrado: 'aula19_matematicaa.dk'
```

**Como corrigir:** confira o nome (inclusive o `.dk`) e se o arquivo está na pasta de onde você roda o programa.

**3. Usar a peça sem importar.** Estar no mesmo projeto não basta; cada arquivo precisa dos seus `importar`:

<!--codigo:aula19_erro3.dk-->
```advak
imprimir(dobro(2))
```

Mensagem real:

<!--erro:aula19_erro3.dk-->
```text
Localização: linha 1
Problema:    Variável 'dobro' não definida
```

**Como corrigir:** acrescente `importar { dobro } de "aula19_matematica.dk"` no topo do arquivo.

## Exercícios

1. Crie o módulo `aula19_temperatura.dk` com a função `celsius_para_fahrenheit(c)` (`c * 9 / 5 + 32`), exporte-a e use-a num programa para converter 100 graus.
2. No módulo do exercício 1, acrescente `fahrenheit_para_celsius(f)` e converta 212.
3. Crie `aula19_textos.dk` com uma função `gritar(texto)` que devolve o texto em maiúsculas com `!` no fim. Importe e teste com `"cuidado"`.
4. Crie um módulo com uma constante `DESCONTO_MAXIMO = 30` e uma função `valido(percentual)` que diz se o percentual está entre 0 e 30. Importe só a função.
5. Importe a função `dobro` do módulo de matemática com o nome `duplicar` e mostre o dobro de 7.
6. Crie um módulo com uma classe `Contador` (método `somar`) e use-a em outro arquivo.
7. Crie dois módulos: `aula19_a.dk` com a função `base()` e `aula19_b.dk`, que importa `base` e exporta `derivada()`, usando `base()`. Use `derivada` num programa.
8. **Desafio:** monte um mini-sistema de três arquivos: um módulo `aula19_calculos.dk` (função `media(lista)`), um módulo `aula19_situacao.dk` (função `situacao(media)` que devolve `"aprovado"` com média 7 ou mais), e o programa principal, que pede 3 notas, calcula a média e mostra a situação.

## Respostas

**Exercício 1**

<!--codigo:aula19_temperatura.dk-->
```advak
função celsius_para_fahrenheit(c) {
    retornar c * 9 / 5 + 32
}

função fahrenheit_para_celsius(f) {
    retornar (f - 32) * 5 / 9
}

exportar { celsius_para_fahrenheit, fahrenheit_para_celsius }
```

<!--codigo:aula19_resposta1.dk-->
```advak
importar { celsius_para_fahrenheit } de "aula19_temperatura.dk"

imprimir("100 °C =", celsius_para_fahrenheit(100), "°F")
```

<!--saida:aula19_resposta1.dk-->
```text
100 °C = 212.0 °F
```

(O módulo `aula19_temperatura.dk` acima já traz a função do exercício 2.)

**Exercício 2**

<!--codigo:aula19_resposta2.dk-->
```advak
importar { fahrenheit_para_celsius } de "aula19_temperatura.dk"

imprimir("212 °F =", fahrenheit_para_celsius(212), "°C")
```

<!--saida:aula19_resposta2.dk-->
```text
212 °F = 100.0 °C
```

**Exercício 3**

<!--codigo:aula19_textos.dk-->
```advak
exportar função gritar(texto) {
    retornar texto.maiusculo() + "!"
}
```

<!--codigo:aula19_resposta3.dk-->
```advak
importar { gritar } de "aula19_textos.dk"

imprimir(gritar("cuidado"))
```

<!--saida:aula19_resposta3.dk-->
```text
CUIDADO!
```

**Exercício 4**

<!--codigo:aula19_regras.dk-->
```advak
fixo DESCONTO_MAXIMO = 30

função valido(percentual) {
    retornar percentual >= 0 e percentual <= DESCONTO_MAXIMO
}

exportar { DESCONTO_MAXIMO, valido }
```

<!--codigo:aula19_resposta4.dk-->
```advak
importar { valido } de "aula19_regras.dk"

imprimir(valido(10))
imprimir(valido(50))
```

<!--saida:aula19_resposta4.dk-->
```text
verdadeiro
falso
```

**Exercício 5**

<!--codigo:aula19_resposta5.dk-->
```advak
importar { dobro como duplicar } de "aula19_matematica.dk"

imprimir(duplicar(7))
```

<!--saida:aula19_resposta5.dk-->
```text
14
```

**Exercício 6**

<!--codigo:aula19_contador.dk-->
```advak
exportar classe Contador {
    construtor() {
        isso.valor = 0
    }
    somar(n) {
        isso.valor = isso.valor + n
    }
}
```

<!--codigo:aula19_resposta6.dk-->
```advak
importar { Contador } de "aula19_contador.dk"

seja c = novo Contador()
c.somar(5)
c.somar(7)
imprimir(c.valor)
```

<!--saida:aula19_resposta6.dk-->
```text
12
```

**Exercício 7**

<!--codigo:aula19_a.dk-->
```advak
exportar função base() {
    retornar 10
}
```

<!--codigo:aula19_b.dk-->
```advak
importar { base } de "aula19_a.dk"

exportar função derivada() {
    retornar base() * 2
}
```

<!--codigo:aula19_resposta7.dk-->
```advak
importar { derivada } de "aula19_b.dk"

imprimir(derivada())
```

<!--saida:aula19_resposta7.dk-->
```text
20
```

**Exercício 8**

<!--codigo:aula19_calculos.dk-->
```advak
exportar função media(lista) {
    seja soma = 0
    para (n em lista) {
        soma = soma + n
    }
    retornar soma / lista.tamanho
}
```

<!--codigo:aula19_situacao.dk-->
```advak
exportar função situacao(media) {
    se (media >= 7) {
        retornar "aprovado"
    }
    retornar "reprovado"
}
```

<!--codigo:aula19_resposta8.dk-->
```advak
importar { media } de "aula19_calculos.dk"
importar { situacao } de "aula19_situacao.dk"

seja notas = []
para (i em 1..4) {
    notas.adicionar(numero(entrada(`Nota ${i}: `)))
}
seja m = media(notas)
imprimir(`Média: ${m}`)
imprimir("Situação:", situacao(m))
```

<!--entrada:aula19_resposta8
8
6
9
-->
<!--saida:aula19_resposta8.dk-->
```text
Nota 1: 8
Nota 2: 6
Nota 3: 9
Média: 7.666666666666667
Situação: aprovado
```

---

**Anterior:** [Aula 18](aula18_heranca.md) · **Próxima aula:** [Aula 20 — Testes unitários](aula20_testes.md)
