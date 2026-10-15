# Aula 10 — Listas

> **Ao final desta aula você vai saber:** guardar vários valores em uma só variável, acessar cada item pela posição, adicionar, remover, ordenar e percorrer listas.

## Uma variável, vários valores

Até agora cada variável guardava **um** valor. Para a lista de compras, a chamada da turma ou as notas de um aluno, usamos uma **lista**: vários valores, em ordem, entre colchetes `[ ]` e separados por vírgula.

<!--codigo:aula10_exemplo1.dk-->
```advak
seja frutas = ["maçã", "banana", "uva"]   // lista com 3 itens
imprimir(frutas)                          // mostra a lista inteira
imprimir(frutas[0])                       // o primeiro item: a contagem começa no ZERO
imprimir(frutas[2])                       // o terceiro item
imprimir(frutas[-1])                      // índice negativo conta do fim: o último
imprimir(frutas.tamanho)                  // quantos itens a lista tem
```

<!--saida:aula10_exemplo1.dk-->
```text
['maçã', 'banana', 'uva']
maçã
uva
uva
3
```

A posição de um item se chama **índice**. Atenção: o primeiro item tem índice **0**, o segundo tem índice 1, e assim por diante.

## Mudando uma lista

<!--codigo:aula10_exemplo2.dk-->
```advak
seja nomes = ["Ana", "Bia"]
nomes.adicionar("Caio")        // coloca no final
nomes.inserir(0, "Zé")         // coloca na posição 0, empurrando os outros
imprimir(nomes)
nomes[1] = "Ana Maria"         // troca o item da posição 1
imprimir(nomes)
nomes.remover(0)               // remove o item da POSIÇÃO 0
imprimir(nomes)
imprimir(nomes.tamanho)
```

<!--saida:aula10_exemplo2.dk-->
```text
['Zé', 'Ana', 'Bia', 'Caio']
['Zé', 'Ana Maria', 'Bia', 'Caio']
['Ana Maria', 'Bia', 'Caio']
3
```

Cuidado: `remover(0)` apaga o item que está na **posição** 0, e não o valor 0.

## Procurando e ordenando

<!--codigo:aula10_exemplo3.dk-->
```advak
seja notas = [7, 3, 9, 5]
imprimir(notas.contem(9))        // verdadeiro: o 9 está na lista
imprimir(notas.contem(10))       // falso
imprimir(notas.indice_de(9))     // em que posição está o 9? posição 2
notas.ordenar()                  // coloca em ordem crescente (muda a própria lista)
imprimir(notas)
imprimir(notas.min(), notas.max(), notas.soma(), notas.media())
```

<!--saida:aula10_exemplo3.dk-->
```text
verdadeiro
falso
2
[3, 5, 7, 9]
3 9 24 6.0
```

## Percorrendo uma lista

Com o `para ... em` da aula 9, cada volta entrega um item. Para conhecer também a posição, use o contador:

<!--codigo:aula10_exemplo4.dk-->
```advak
seja alunos = ["Ana", "Bia", "Caio"]
para (nome em alunos) {
    imprimir("Olá,", nome)
}
para (i em 0..alunos.tamanho) {          // 0, 1, 2: as posições da lista
    imprimir("Aluno", i + 1, "->", alunos[i])
}
```

<!--saida:aula10_exemplo4.dk-->
```text
Olá, Ana
Olá, Bia
Olá, Caio
Aluno 1 -> Ana
Aluno 2 -> Bia
Aluno 3 -> Caio
```

## Lista de listas

Uma lista pode ter listas dentro, como uma tabela:

<!--codigo:aula10_exemplo5.dk-->
```advak
seja tabela = [[1, 2], [3, 4], [5, 6]]   // 3 linhas e 2 colunas
imprimir(tabela[1])                       // a linha de índice 1
imprimir(tabela[1][0])                    // dentro dela, o item de índice 0
```

<!--saida:aula10_exemplo5.dk-->
```text
[3, 4]
3
```

## Erros comuns

**1. Pedir uma posição que não existe:**

<!--codigo:aula10_erro1.dk-->
```advak
seja cores = ["azul", "verde"]
imprimir(cores[2])
```

Mensagem real:

<!--erro:aula10_erro1.dk-->
```text
Problema:    Índice 2 fora do alcance (tamanho: 2)
```

**Como corrigir:** uma lista de 2 itens tem as posições 0 e 1. A última posição é sempre `tamanho - 1` (ou use `[-1]`).

**2. Esquecer que a contagem começa no zero.** `frutas[1]` é o **segundo** item, não o primeiro.

## Exercícios

1. Crie uma lista com cinco nomes de colegas e mostre o primeiro e o último.
2. Crie uma lista de números e mostre quantos itens ela tem.
3. Comece com uma lista vazia `[]`. Peça três nomes, adicione cada um à lista e mostre a lista no final.
4. Dada `[4, 8, 15, 16, 23, 42]`, mostre a soma e a média dos números.
5. Dada `[5, 2, 9, 1]`, ordene a lista e mostre o menor e o maior.
6. Peça um nome e diga se ele **está** na lista `["Ana", "Bia", "Caio"]`.
7. Peça cinco números, guarde em uma lista e mostre apenas os que são maiores que a média.
8. **Desafio:** dada `[3, 7, 3, 9, 7, 3]`, monte uma nova lista **sem repetidos**, mantendo a ordem em que aparecem.

## Respostas

**Exercício 1**

<!--codigo:aula10_resposta1.dk-->
```advak
seja colegas = ["Ana", "Bia", "Caio", "Davi", "Eva"]
imprimir("Primeiro:", colegas[0])
imprimir("Último:", colegas[-1])
```

<!--saida:aula10_resposta1.dk-->
```text
Primeiro: Ana
Último: Eva
```

**Exercício 2**

<!--codigo:aula10_resposta2.dk-->
```advak
seja numeros = [10, 20, 30, 40]
imprimir("A lista tem", numeros.tamanho, "itens")
```

<!--saida:aula10_resposta2.dk-->
```text
A lista tem 4 itens
```

**Exercício 3**

<!--codigo:aula10_resposta3.dk-->
```advak
seja nomes = []
para (i em 1..=3) {
    nomes.adicionar(entrada("Nome: "))
}
imprimir(nomes)
```

<!--entrada:aula10_resposta3
Ana
Bia
Caio
-->
<!--saida:aula10_resposta3.dk-->
```text
Nome: Ana
Nome: Bia
Nome: Caio
['Ana', 'Bia', 'Caio']
```

**Exercício 4**

<!--codigo:aula10_resposta4.dk-->
```advak
seja numeros = [4, 8, 15, 16, 23, 42]
imprimir("Soma:", numeros.soma())
imprimir("Média:", numeros.media())
```

<!--saida:aula10_resposta4.dk-->
```text
Soma: 108
Média: 18.0
```

**Exercício 5**

<!--codigo:aula10_resposta5.dk-->
```advak
seja numeros = [5, 2, 9, 1]
numeros.ordenar()
imprimir(numeros)
imprimir("Menor:", numeros[0], "Maior:", numeros[-1])
```

<!--saida:aula10_resposta5.dk-->
```text
[1, 2, 5, 9]
Menor: 1 Maior: 9
```

**Exercício 6**

<!--codigo:aula10_resposta6.dk-->
```advak
seja turma = ["Ana", "Bia", "Caio"]
seja nome = entrada("Nome: ")
se (turma.contem(nome)) {
    imprimir(nome, "está na lista.")
} senão {
    imprimir(nome, "não está na lista.")
}
```

<!--entrada:aula10_resposta6
Bia
-->
<!--saida:aula10_resposta6.dk-->
```text
Nome: Bia
Bia está na lista.
```

**Exercício 7**

<!--codigo:aula10_resposta7.dk-->
```advak
seja numeros = []
para (i em 1..=5) {
    numeros.adicionar(numero(entrada("Número: ")))
}
seja media = numeros.media()
imprimir("Média:", media)
para (n em numeros) {
    se (n > media) {
        imprimir(n, "é maior que a média")
    }
}
```

<!--entrada:aula10_resposta7
2
4
6
8
10
-->
<!--saida:aula10_resposta7.dk-->
```text
Número: 2
Número: 4
Número: 6
Número: 8
Número: 10
Média: 6.0
8 é maior que a média
10 é maior que a média
```

**Exercício 8**

<!--codigo:aula10_resposta8.dk-->
```advak
seja original = [3, 7, 3, 9, 7, 3]
seja sem_repetidos = []
para (n em original) {
    se (nao sem_repetidos.contem(n)) {   // só adiciona se ainda não está lá
        sem_repetidos.adicionar(n)
    }
}
imprimir(sem_repetidos)
```

<!--saida:aula10_resposta8.dk-->
```text
[3, 7, 9]
```

---

**Anterior:** [Aula 9](aula09_para.md) · **Próxima aula:** [Aula 11 — Mapas (objetos)](aula11_mapas.md)
