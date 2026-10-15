# Aula 18 — Herança

> **Ao final desta aula você vai saber:** criar uma classe nova a partir de outra com `herda`, reaproveitar o que já existe, trocar (sobrescrever) comportamentos e chamar a classe de origem com `super`.

## A ideia: não escrever tudo de novo

Uma escola tem alunos e professores. Os dois têm nome e idade, e os dois "se apresentam". Mas o aluno tem uma turma e o professor tem uma matéria. Escrever `nome`, `idade` e `apresentar` duas vezes seria desperdício.

Com **herança**, você escreve o que é comum **uma vez** numa classe geral (a **classe-mãe**, ou *superclasse*) e cria classes mais específicas (as **classes-filhas**) que **herdam** tudo e acrescentam o que for particular. É como a herança de família: o filho recebe características dos pais e ainda tem as suas.

Escrevemos assim: `classe Filha herda Mae { ... }`.

## Primeira herança

<!--codigo:aula18_exemplo1.dk-->
```advak
classe Animal {
    construtor(nome) {
        isso.nome = nome
    }
    falar() {
        imprimir(`${isso.nome} faz um som`)
    }
    apresentar() {
        imprimir(`Sou ${isso.nome}`)
    }
}

classe Cachorro herda Animal {            // Cachorro recebe tudo de Animal
    falar() {                             // e troca o método falar
        imprimir(`${isso.nome} diz: au au`)
    }
}

classe Gato herda Animal {
    falar() {
        imprimir(`${isso.nome} diz: miau`)
    }
}

seja rex = novo Cachorro("Rex")
seja mimi = novo Gato("Mimi")

rex.falar()                               // versão do Cachorro
mimi.falar()                              // versão do Gato
rex.apresentar()                          // herdado: o Cachorro não escreveu esse método
mimi.apresentar()
```

<!--saida:aula18_exemplo1.dk-->
```text
Rex diz: au au
Mimi diz: miau
Sou Rex
Sou Mimi
```

Repare em duas coisas:

- `Cachorro` e `Gato` **não escreveram** `construtor` nem `apresentar`: receberam da classe `Animal`.
- Os dois **trocaram** o método `falar`. Isso se chama **sobrescrever**: a filha escreve um método com o mesmo nome da mãe e o dela passa a valer.

## `super`: chamando a classe-mãe

Quando a filha precisa de dados extras, ela escreve o próprio `construtor`. Mas então precisa avisar a mãe para guardar os dados comuns. Isso é feito com `super(...)`, que chama o construtor da classe-mãe:

<!--codigo:aula18_exemplo2.dk-->
```advak
classe Animal {
    construtor(nome) {
        isso.nome = nome
    }
    falar() {
        imprimir(`${isso.nome} faz um som`)
    }
}

classe Cachorro herda Animal {
    construtor(nome, raca) {
        super(nome)                       // a mãe guarda o nome
        isso.raca = raca                  // a filha guarda o que é só dela
    }
    detalhes() {
        super.falar()                     // chama o falar() da mãe
        imprimir(`Raça: ${isso.raca}`)
    }
}

seja rex = novo Cachorro("Rex", "vira-lata")
rex.detalhes()
imprimir(rex.nome, rex.raca)
```

<!--saida:aula18_exemplo2.dk-->
```text
Rex faz um som
Raça: vira-lata
Rex vira-lata
```

- `super(nome)` dentro do construtor: roda o construtor da `Animal`, que faz `isso.nome = nome`.
- `super.falar()` dentro de um método: chama a versão da mãe, mesmo que a filha tenha trocado o `falar`.

## Cada um do seu jeito (polimorfismo)

Esta é a grande vantagem: você pode tratar objetos diferentes de forma igual e cada um responde do seu jeito.

<!--codigo:aula18_exemplo3.dk-->
```advak
classe Funcionario {
    construtor(nome, salario) {
        isso.nome = nome
        isso.salario = salario
    }
    bonus() {
        retornar isso.salario * 0.1       // regra geral: 10%
    }
}

classe Gerente herda Funcionario {
    bonus() {
        retornar isso.salario * 0.3       // gerente: 30%
    }
}

classe Estagiario herda Funcionario {
    bonus() {
        retornar 0                        // estagiário: sem bônus
    }
}

seja equipe = [
    novo Funcionario("Ana", 3000),
    novo Gerente("Bruno", 8000),
    novo Estagiario("Carla", 1500)
]

para (pessoa em equipe) {
    imprimir(`${pessoa.nome}: bônus de R$ ${pessoa.bonus()}`)     // mesmo comando, resultados diferentes
}
```

<!--saida:aula18_exemplo3.dk-->
```text
Ana: bônus de R$ 300.0
Bruno: bônus de R$ 2400.0
Carla: bônus de R$ 0
```

O laço não precisa saber quem é gerente e quem é estagiário: cada objeto sabe calcular o próprio bônus.

## Quem é quem: `instanceof`

Um objeto da classe-filha **também é** da classe-mãe (um cachorro é um animal), mas não o contrário:

<!--codigo:aula18_exemplo4.dk-->
```advak
classe Animal {
    construtor(nome) {
        isso.nome = nome
    }
}
classe Cachorro herda Animal { }
classe Gato herda Animal { }

seja rex = novo Cachorro("Rex")
imprimir("É Cachorro?", rex instanceof Cachorro)
imprimir("É Animal?", rex instanceof Animal)
imprimir("É Gato?", rex instanceof Gato)

seja bicho = novo Animal("Bicho")
imprimir("Um Animal qualquer é Cachorro?", bicho instanceof Cachorro)
```

<!--saida:aula18_exemplo4.dk-->
```text
É Cachorro? verdadeiro
É Animal? verdadeiro
É Gato? falso
Um Animal qualquer é Cachorro? falso
```

## Heranças em cadeia

Uma filha pode ter filhas. Tudo vai sendo herdado, de geração em geração:

<!--codigo:aula18_exemplo5.dk-->
```advak
classe Animal {
    construtor(nome) {
        isso.nome = nome
    }
    apresentar() {
        imprimir(`Sou ${isso.nome}`)
    }
}

classe Cachorro herda Animal {
    construtor(nome, raca) {
        super(nome)
        isso.raca = raca
    }
    falar() {
        imprimir(`${isso.nome} diz: au au`)
    }
}

classe Filhote herda Cachorro { }         // não escreve nada: herda tudo

seja bolt = novo Filhote("Bolt", "pug")
bolt.falar()                              // vem de Cachorro
bolt.apresentar()                         // vem de Animal
imprimir(bolt.raca)
imprimir(bolt instanceof Animal)
```

<!--saida:aula18_exemplo5.dk-->
```text
Bolt diz: au au
Sou Bolt
pug
verdadeiro
```

## Erros comuns

**1. Escrever um construtor na filha e esquecer o `super`.** Os dados da mãe não são guardados:

<!--codigo:aula18_erro1.dk-->
```advak
classe Animal {
    construtor(nome) {
        isso.nome = nome
    }
}
classe Cachorro herda Animal {
    construtor(nome, raca) {
        isso.raca = raca                  // faltou super(nome)
    }
}
seja rex = novo Cachorro("Rex", "pug")
imprimir(rex.nome)
```

Mensagem real:

<!--erro:aula18_erro1.dk-->
```text
Localização: linha 12
Problema:    'nome' não existe em Cachorro
```

**Como corrigir:** na primeira linha do construtor da filha, escreva `super(nome)`.

**2. Esperar que a mãe conheça métodos da filha.** A herança vai só em uma direção:

<!--codigo:aula18_erro2.dk-->
```advak
classe Animal { }
classe Cachorro herda Animal {
    latir() {
        imprimir("au au")
    }
}
seja a = novo Animal()
a.latir()
```

Mensagem real:

<!--erro:aula18_erro2.dk-->
```text
Localização: linha 8
Problema:    'latir' não existe em Animal
```

**Como corrigir:** se todos os animais precisam do método, coloque-o na classe-mãe.

**3. Usar herança onde não faz sentido.** Só use `herda` quando a frase "*a filha é um(a) tipo de mãe*" fizer sentido: Cachorro **é um** Animal. Já "Carro **é um** Motor" não faz sentido: o carro **tem** um motor, e isso se resolve guardando um objeto dentro de outro (`isso.motor = novo Motor()`).

## Exercícios

1. Crie a classe `Veiculo` com `modelo` e um método `descricao()` que mostra `Veículo: <modelo>`. Crie `Carro` herdando de `Veiculo` sem escrever nada nela, e teste.
2. Na classe `Carro` do exercício 1, sobrescreva `descricao()` para mostrar `Carro: <modelo>`.
3. Crie `Pessoa` (nome) e `Aluno` herdando de `Pessoa`, com o construtor `(nome, turma)` usando `super`. Mostre nome e turma.
4. Crie `Forma` com o método `area()` que devolve 0, e as filhas `Quadrado` (lado) e `Circulo` (raio, use 3.14) que sobrescrevem `area()`. Mostre a área de cada uma numa lista.
5. Crie `Conta` com `saldo` e `sacar(v)`. Crie `ContaEspecial`, que pode ficar até 100 negativo: sobrescreva `sacar(v)` para permitir até `saldo + 100`, e lance `"limite excedido"` além disso.
6. Crie `Funcionario` (nome, salário) e `Vendedor`, que também recebe `comissao` (porcentagem) e tem o método `ganho_total(vendas)`.
7. Use `instanceof` para contar, numa lista com 2 cachorros e 3 gatos, quantos são `Gato`.
8. **Desafio:** crie `Animal`, `Mamifero` (herda de Animal) e `Cachorro` (herda de Mamifero). Cada classe tem um método `tipo_do_bicho()` que usa `super` para somar a frase da mãe: `animal`, depois `animal > mamífero`, depois `animal > mamífero > cachorro`.

## Respostas

**Exercício 1**

<!--codigo:aula18_resposta1.dk-->
```advak
classe Veiculo {
    construtor(modelo) {
        isso.modelo = modelo
    }
    descricao() {
        imprimir(`Veículo: ${isso.modelo}`)
    }
}
classe Carro herda Veiculo { }

seja c = novo Carro("Fusca")
c.descricao()
```

<!--saida:aula18_resposta1.dk-->
```text
Veículo: Fusca
```

**Exercício 2**

<!--codigo:aula18_resposta2.dk-->
```advak
classe Veiculo {
    construtor(modelo) {
        isso.modelo = modelo
    }
    descricao() {
        imprimir(`Veículo: ${isso.modelo}`)
    }
}
classe Carro herda Veiculo {
    descricao() {
        imprimir(`Carro: ${isso.modelo}`)
    }
}

seja v = novo Veiculo("Bicicleta")
seja c = novo Carro("Fusca")
v.descricao()
c.descricao()
```

<!--saida:aula18_resposta2.dk-->
```text
Veículo: Bicicleta
Carro: Fusca
```

**Exercício 3**

<!--codigo:aula18_resposta3.dk-->
```advak
classe Pessoa {
    construtor(nome) {
        isso.nome = nome
    }
}
classe Aluno herda Pessoa {
    construtor(nome, turma) {
        super(nome)
        isso.turma = turma
    }
}

seja a = novo Aluno("Ana", "3º A")
imprimir(a.nome, a.turma)
```

<!--saida:aula18_resposta3.dk-->
```text
Ana 3º A
```

**Exercício 4**

<!--codigo:aula18_resposta4.dk-->
```advak
classe Forma {
    area() {
        retornar 0
    }
}
classe Quadrado herda Forma {
    construtor(lado) {
        isso.lado = lado
    }
    area() {
        retornar isso.lado * isso.lado
    }
}
classe Circulo herda Forma {
    construtor(raio) {
        isso.raio = raio
    }
    area() {
        retornar 3.14 * isso.raio * isso.raio
    }
}

seja formas = [novo Quadrado(4), novo Circulo(2), novo Forma()]
para (f em formas) {
    imprimir("Área:", f.area())
}
```

<!--saida:aula18_resposta4.dk-->
```text
Área: 16
Área: 12.56
Área: 0
```

**Exercício 5**

<!--codigo:aula18_resposta5.dk-->
```advak
classe Conta {
    construtor(saldo) {
        isso.saldo = saldo
    }
    sacar(v) {
        se (v > isso.saldo) {
            lançar "saldo insuficiente"
        }
        isso.saldo = isso.saldo - v
    }
}
classe ContaEspecial herda Conta {
    sacar(v) {
        se (v > isso.saldo + 100) {
            lançar "limite excedido"
        }
        isso.saldo = isso.saldo - v
    }
}

seja c = novo ContaEspecial(50)
c.sacar(120)
imprimir("Saldo:", c.saldo)
tentar {
    c.sacar(100)
} capturar (e) {
    imprimir("Erro:", e)
}
```

<!--saida:aula18_resposta5.dk-->
```text
Saldo: -70
Erro: limite excedido
```

**Exercício 6**

<!--codigo:aula18_resposta6.dk-->
```advak
classe Funcionario {
    construtor(nome, salario) {
        isso.nome = nome
        isso.salario = salario
    }
}
classe Vendedor herda Funcionario {
    construtor(nome, salario, comissao) {
        super(nome, salario)
        isso.comissao = comissao
    }
    ganho_total(vendas) {
        retornar isso.salario + vendas * isso.comissao / 100
    }
}

seja v = novo Vendedor("Davi", 2000, 5)
imprimir(`${v.nome} ganhou R$ ${v.ganho_total(10000)}`)
```

<!--saida:aula18_resposta6.dk-->
```text
Davi ganhou R$ 2500.0
```

**Exercício 7**

<!--codigo:aula18_resposta7.dk-->
```advak
classe Animal { }
classe Cachorro herda Animal { }
classe Gato herda Animal { }

seja bichos = [novo Cachorro(), novo Gato(), novo Cachorro(), novo Gato(), novo Gato()]
seja gatos = 0
para (b em bichos) {
    se (b instanceof Gato) {
        gatos = gatos + 1
    }
}
imprimir("Gatos:", gatos)
```

<!--saida:aula18_resposta7.dk-->
```text
Gatos: 3
```

**Exercício 8**

<!--codigo:aula18_resposta8.dk-->
```advak
classe Animal {
    tipo_do_bicho() {
        retornar "animal"
    }
}
classe Mamifero herda Animal {
    tipo_do_bicho() {
        retornar super.tipo_do_bicho() + " > mamífero"
    }
}
classe Cachorro herda Mamifero {
    tipo_do_bicho() {
        retornar super.tipo_do_bicho() + " > cachorro"
    }
}

imprimir(novo Animal().tipo_do_bicho())
imprimir(novo Mamifero().tipo_do_bicho())
imprimir(novo Cachorro().tipo_do_bicho())
```

<!--saida:aula18_resposta8.dk-->
```text
animal
animal > mamífero
animal > mamífero > cachorro
```

---

**Anterior:** [Aula 17](aula17_classes.md) · **Próxima aula:** [Aula 19 — Módulos](aula19_modulos.md)
