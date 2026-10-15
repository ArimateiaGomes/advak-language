# Aula 17 — Classes e objetos

> **Ao final desta aula você vai saber:** criar um molde (`classe`) com informações e ações, fabricar objetos a partir dele com `novo`, usar `construtor` e `isso`, e guardar vários objetos numa lista.

## O problema: muitos dados que andam juntos

Imagine cadastrar alunos. Cada aluno tem nome e nota, e queremos ações como "mostrar a situação". Com mapas (aula 11) dá para guardar os dados, mas as **ações** ficam soltas em funções. Uma **classe** junta as duas coisas num lugar só.

Pense numa **forma de bolo**: a forma (a classe) define o formato; cada bolo que sai dela (um **objeto**) é um bolo diferente, com seu próprio recheio.

- **classe** = o molde (a forma de bolo);
- **objeto** = uma coisa fabricada a partir do molde (um bolo);
- **atributos** = as informações do objeto (nome, saldo...);
- **métodos** = as ações do objeto (depositar, apresentar...).

## Sua primeira classe

<!--codigo:aula17_exemplo1.dk-->
```advak
classe Pessoa {
    construtor(nome, idade) {            // roda quando o objeto é criado
        isso.nome = nome                 // isso = "este objeto"
        isso.idade = idade
    }

    apresentar() {                       // um método: uma ação
        imprimir(`Oi, sou ${isso.nome} e tenho ${isso.idade} anos`)
    }
}

seja ana = novo Pessoa("Ana", 17)        // novo = fabrica um objeto
seja bia = novo Pessoa("Bia", 20)

ana.apresentar()
bia.apresentar()
imprimir(ana.nome, bia.nome)             // cada objeto tem os seus dados
```

<!--saida:aula17_exemplo1.dk-->
```text
Oi, sou Ana e tenho 17 anos
Oi, sou Bia e tenho 20 anos
Ana Bia
```

Passo a passo:

1. `classe Pessoa { ... }` cria o molde. Por convenção, o nome da classe começa com letra maiúscula.
2. O `construtor` recebe os dados iniciais e os guarda no objeto com `isso.nome = nome`. Dentro da classe, **`isso`** quer dizer "este objeto aqui".
3. `novo Pessoa("Ana", 17)` fabrica um objeto: a Advak chama o construtor com esses valores.
4. `ana.apresentar()` chama o método. Dentro dele, `isso.nome` é o nome **da Ana**; quando chamamos `bia.apresentar()`, `isso.nome` é o nome da Bia.

## Mudando e lendo atributos

Você lê e muda atributos com o ponto, como em um mapa:

<!--codigo:aula17_exemplo2.dk-->
```advak
classe Pessoa {
    construtor(nome, idade) {
        isso.nome = nome
        isso.idade = idade
    }

    fazer_aniversario() {
        isso.idade = isso.idade + 1
    }

    descricao() {
        retornar `${isso.nome} (${isso.idade})`     // métodos também devolvem valores
    }
}

seja p = novo Pessoa("Ana", 17)
imprimir(p.descricao())
p.fazer_aniversario()
imprimir(p.descricao())
p.idade = 30                                          // mudança direta
imprimir(p.idade)
imprimir(tipo(p))
```

<!--saida:aula17_exemplo2.dk-->
```text
Ana (17)
Ana (18)
30
objeto
```

## Uma classe com regras: conta bancária

O grande poder da classe é **proteger regras** junto dos dados. A conta abaixo não deixa sacar mais do que tem (usando `lançar`, da aula 15):

<!--codigo:aula17_exemplo3.dk-->
```advak
classe Conta {
    construtor(titular, saldo) {
        isso.titular = titular
        isso.saldo = saldo
    }

    depositar(valor) {
        se (valor <= 0) {
            lançar "valor inválido"
        }
        isso.saldo = isso.saldo + valor
    }

    sacar(valor) {
        se (valor > isso.saldo) {
            lançar "saldo insuficiente"
        }
        isso.saldo = isso.saldo - valor
    }
}

seja conta = novo Conta("Ana", 100)
conta.depositar(50)
conta.sacar(30)
imprimir("Saldo:", conta.saldo)

tentar {
    conta.sacar(1000)
} capturar (e) {
    imprimir("Não foi possível:", e)
}
imprimir("Saldo continua:", conta.saldo)

seja outra = novo Conta("Bia", 5)               // outro objeto, outro saldo
imprimir(conta.saldo, outra.saldo)
```

<!--saida:aula17_exemplo3.dk-->
```text
Saldo: 120
Não foi possível: saldo insuficiente
Saldo continua: 120
120 5
```

## Encadeando chamadas com `retornar isso`

Se um método termina com `retornar isso`, ele devolve o próprio objeto, e você pode chamar vários métodos em sequência:

<!--codigo:aula17_exemplo4.dk-->
```advak
classe Contador {
    construtor() {
        isso.valor = 0
    }
    somar(n) {
        isso.valor = isso.valor + n
        retornar isso
    }
}

seja c = novo Contador()
c.somar(1).somar(10).somar(100)
imprimir(c.valor)
```

<!--saida:aula17_exemplo4.dk-->
```text
111
```

## Vários objetos numa lista

Objetos são valores como outros: cabem em listas, e você pode percorrer com `para`:

<!--codigo:aula17_exemplo5.dk-->
```advak
classe Produto {
    construtor(nome, preco) {
        isso.nome = nome
        isso.preco = preco
    }
    com_desconto(percentual) {
        retornar isso.preco * (1 - percentual / 100)
    }
}

seja estoque = [novo Produto("Caderno", 20), novo Produto("Caneta", 3), novo Produto("Mochila", 120)]

seja total = 0
para (p em estoque) {
    imprimir(`${p.nome}: R$ ${p.preco} (com 10% de desconto: R$ ${p.com_desconto(10)})`)
    total = total + p.preco
}
imprimir("Total sem desconto:", total)

seja caros = estoque.filtrar((p) => p.preco > 10)      // aula 13 funciona com objetos
imprimir("Caros:", caros.mapear((p) => p.nome))
```

<!--saida:aula17_exemplo5.dk-->
```text
Caderno: R$ 20 (com 10% de desconto: R$ 18.0)
Caneta: R$ 3 (com 10% de desconto: R$ 2.7)
Mochila: R$ 120 (com 10% de desconto: R$ 108.0)
Total sem desconto: 143
Caros: ['Caderno', 'Mochila']
```

Para saber se um objeto veio de uma classe, use `instanceof`:

<!--codigo:aula17_exemplo6.dk-->
```advak
classe Gato { }
classe Cachorro { }

seja t = novo Gato()
imprimir(t instanceof Gato)
imprimir(t instanceof Cachorro)
```

<!--saida:aula17_exemplo6.dk-->
```text
verdadeiro
falso
```

## Erros comuns

**1. Esquecer o `isso` dentro da classe.** Sem `isso.`, o valor não vai para o objeto:

<!--codigo:aula17_erro1.dk-->
```advak
classe Pessoa {
    construtor(nome) {
        nome = nome                      // errado: não guardou em lugar nenhum do objeto
    }
    mostrar() {
        imprimir(isso.nome)
    }
}
seja p = novo Pessoa("Ana")
p.mostrar()
```

Mensagem real:

<!--erro:aula17_erro1.dk-->
```text
Localização: linha 6
Problema:    'nome' não existe em Pessoa
```

**Como corrigir:** escreva `isso.nome = nome`.

**2. Usar um atributo que ninguém criou:**

<!--codigo:aula17_erro2.dk-->
```advak
classe Pessoa {
    construtor(nome) {
        isso.nome = nome
    }
}
seja p = novo Pessoa("Ana")
imprimir(p.idade)
```

Mensagem real:

<!--erro:aula17_erro2.dk-->
```text
Localização: linha 7
Problema:    'idade' não existe em Pessoa
```

**Como corrigir:** crie o atributo no construtor (`isso.idade = idade`) e passe o valor ao criar o objeto.

**3. Chamar um método que não existe:**

<!--codigo:aula17_erro3.dk-->
```advak
classe Gato {
    miar() {
        imprimir("miau")
    }
}
seja g = novo Gato()
g.latir()
```

Mensagem real:

<!--erro:aula17_erro3.dk-->
```text
Localização: linha 7
Problema:    'latir' não existe em Gato
```

**Como corrigir:** confira se o nome do método está escrito igual ao da classe.

**4. Esquecer de passar os valores ao criar o objeto.** Não dá erro, mas o que faltou vira `nulo`:

<!--codigo:aula17_erro4.dk-->
```advak
classe Pessoa {
    construtor(nome, idade) {
        isso.nome = nome
        isso.idade = idade
    }
}
seja p = novo Pessoa("Ana")
imprimir(p.nome, p.idade)
```

<!--saida:aula17_erro4.dk-->
```text
Ana nulo
```

**Como corrigir:** passe todos os valores que o construtor espera.

## Exercícios

1. Crie a classe `Retangulo` com `largura` e `altura`, e um método `area()`. Crie um retângulo 4 por 5 e mostre a área.
2. Acrescente à classe do exercício 1 o método `perimetro()` e mostre os dois valores para um retângulo 3 por 7.
3. Crie a classe `Aluno` com `nome` e uma lista `notas` (começa vazia). Métodos: `adicionar_nota(n)` e `media()`. Teste com 3 notas.
4. Crie a classe `Lampada` com o atributo `ligada` (começa `falso`) e os métodos `ligar()`, `desligar()` e `estado()`, que devolve `"ligada"` ou `"desligada"`.
5. Crie a classe `Produto` (nome, preço, quantidade) com o método `valor_total()`. Crie 3 produtos numa lista e mostre a soma dos valores totais.
6. Crie a classe `ContaPoupanca` (saldo inicial) com `render(taxa)`, que aumenta o saldo em `taxa` por cento. Renda 10% duas vezes e mostre o saldo.
7. Peça nome e idade e crie um objeto `Pessoa`. Se a idade for 18 ou mais, o método `maior_de_idade()` devolve `verdadeiro`.
8. **Desafio:** crie a classe `Livro` (título e `emprestado`, começando `falso`) com `emprestar()` e `devolver()`. Se tentar emprestar um livro já emprestado, lance o erro `"livro já emprestado"`. Teste capturando o erro.

## Respostas

**Exercício 1**

<!--codigo:aula17_resposta1.dk-->
```advak
classe Retangulo {
    construtor(largura, altura) {
        isso.largura = largura
        isso.altura = altura
    }
    area() {
        retornar isso.largura * isso.altura
    }
}

seja r = novo Retangulo(4, 5)
imprimir("Área:", r.area())
```

<!--saida:aula17_resposta1.dk-->
```text
Área: 20
```

**Exercício 2**

<!--codigo:aula17_resposta2.dk-->
```advak
classe Retangulo {
    construtor(largura, altura) {
        isso.largura = largura
        isso.altura = altura
    }
    area() {
        retornar isso.largura * isso.altura
    }
    perimetro() {
        retornar 2 * (isso.largura + isso.altura)
    }
}

seja r = novo Retangulo(3, 7)
imprimir("Área:", r.area())
imprimir("Perímetro:", r.perimetro())
```

<!--saida:aula17_resposta2.dk-->
```text
Área: 21
Perímetro: 20
```

**Exercício 3**

<!--codigo:aula17_resposta3.dk-->
```advak
classe Aluno {
    construtor(nome) {
        isso.nome = nome
        isso.notas = []
    }
    adicionar_nota(n) {
        isso.notas.adicionar(n)
    }
    media() {
        seja soma = 0
        para (n em isso.notas) {
            soma = soma + n
        }
        retornar soma / isso.notas.tamanho
    }
}

seja a = novo Aluno("Ana")
a.adicionar_nota(7)
a.adicionar_nota(8)
a.adicionar_nota(9)
imprimir(`Média de ${a.nome}:`, a.media())
```

<!--saida:aula17_resposta3.dk-->
```text
Média de Ana: 8.0
```

**Exercício 4**

<!--codigo:aula17_resposta4.dk-->
```advak
classe Lampada {
    construtor() {
        isso.ligada = falso
    }
    ligar() {
        isso.ligada = verdadeiro
    }
    desligar() {
        isso.ligada = falso
    }
    estado() {
        se (isso.ligada) {
            retornar "ligada"
        }
        retornar "desligada"
    }
}

seja l = novo Lampada()
imprimir(l.estado())
l.ligar()
imprimir(l.estado())
l.desligar()
imprimir(l.estado())
```

<!--saida:aula17_resposta4.dk-->
```text
desligada
ligada
desligada
```

**Exercício 5**

<!--codigo:aula17_resposta5.dk-->
```advak
classe Produto {
    construtor(nome, preco, quantidade) {
        isso.nome = nome
        isso.preco = preco
        isso.quantidade = quantidade
    }
    valor_total() {
        retornar isso.preco * isso.quantidade
    }
}

seja itens = [novo Produto("Caderno", 20, 3), novo Produto("Caneta", 3, 10), novo Produto("Mochila", 120, 1)]
seja soma = 0
para (p em itens) {
    soma = soma + p.valor_total()
}
imprimir("Soma dos valores:", soma)
```

<!--saida:aula17_resposta5.dk-->
```text
Soma dos valores: 210
```

**Exercício 6**

<!--codigo:aula17_resposta6.dk-->
```advak
classe ContaPoupanca {
    construtor(saldo) {
        isso.saldo = saldo
    }
    render(taxa) {
        isso.saldo = isso.saldo + isso.saldo * taxa / 100
    }
}

seja c = novo ContaPoupanca(1000)
c.render(10)
c.render(10)
imprimir("Saldo:", c.saldo)
```

<!--saida:aula17_resposta6.dk-->
```text
Saldo: 1210.0
```

**Exercício 7**

<!--codigo:aula17_resposta7.dk-->
```advak
classe Pessoa {
    construtor(nome, idade) {
        isso.nome = nome
        isso.idade = idade
    }
    maior_de_idade() {
        retornar isso.idade >= 18
    }
}

seja nome = entrada("Nome: ")
seja idade = inteiro(entrada("Idade: "))
seja p = novo Pessoa(nome, idade)
imprimir(`${p.nome} é maior de idade?`, p.maior_de_idade())
```

<!--entrada:aula17_resposta7
Ana
17
-->
<!--saida:aula17_resposta7.dk-->
```text
Nome: Ana
Idade: 17
Ana é maior de idade? falso
```

**Exercício 8**

<!--codigo:aula17_resposta8.dk-->
```advak
classe Livro {
    construtor(titulo) {
        isso.titulo = titulo
        isso.emprestado = falso
    }
    emprestar() {
        se (isso.emprestado) {
            lançar "livro já emprestado"
        }
        isso.emprestado = verdadeiro
    }
    devolver() {
        isso.emprestado = falso
    }
}

seja livro = novo Livro("Dom Casmurro")
livro.emprestar()
tentar {
    livro.emprestar()
} capturar (e) {
    imprimir("Erro:", e)
}
livro.devolver()
livro.emprestar()
imprimir("Emprestado agora?", livro.emprestado)
```

<!--saida:aula17_resposta8.dk-->
```text
Erro: livro já emprestado
Emprestado agora? verdadeiro
```

---

**Anterior:** [Aula 16](aula16_arquivos_json.md) · **Próxima aula:** [Aula 18 — Herança](aula18_heranca.md)
