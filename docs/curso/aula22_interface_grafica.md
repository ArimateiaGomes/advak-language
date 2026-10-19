# Aula 22 — Interface gráfica: primeira janela

> **Ao final desta aula você vai saber:** abrir uma janela com a Advak, colocar texto, campos de digitação, botões e uma tabela, e fazer o programa reagir ao clique de um botão.

## De texto para janelas

Até agora, seus programas conversavam pelo terminal: `imprimir` e `entrada`. Programas do dia a dia têm **janelas**, com botões e caixinhas. Isso se chama **interface gráfica** (ou *GUI*). A Advak traz tudo no objeto `gui`.

Ideia importante: um programa com janela é diferente. Em vez de seguir de cima para baixo e terminar, ele **monta** a janela, depois **fica esperando** que a pessoa clique em alguma coisa. Cada botão guarda uma função, chamada quando o botão é clicado.

O roteiro é sempre:

1. criar a janela (`gui.janela`);
2. colocar as peças (`gui.label`, `gui.campo`, `gui.botao`, `gui.tabela`...);
3. ligar os botões às funções;
4. `gui.iniciar()`: abre a janela e espera. O programa só continua depois que a janela é fechada.

> **Sobre os exemplos desta aula.** Um exemplo com janela só mostra algo interessante se alguém clicar. Para que cada exemplo possa ser rodado e conferido sozinho, ele usa `gui.apos(milissegundos, função)` — "daqui a tantos milissegundos, faça isto" — para **clicar no botão por você** (`botao.invoke()`) e fechar a janela (`gui.parar()`). Num programa de verdade você não coloca essas linhas: quem clica e quem fecha é o usuário. Quando você rodar, uma janela aparece por um instante e some.

## A primeira janela

<!--codigo:aula22_exemplo1.dk-->
```advak
seja jan = gui.janela("Minha primeira janela", 420, 220)     // título, largura, altura
jan.centralizar()                                            // põe a janela no meio da tela

gui.label(jan, "Olá, mundo gráfico!", negrito=verdadeiro)
gui.label(jan, "Esta janela fecha sozinha em 1 segundo.")

gui.apos(1000, () => {                                        // (só para o exemplo)
    gui.parar()                                               // fecha a janela
})

imprimir("Abrindo a janela...")
gui.iniciar()                                                 // abre e espera
imprimir("A janela foi fechada, o programa continua.")
```

<!--saida:aula22_exemplo1.dk-->
```text
Abrindo a janela...
A janela foi fechada, o programa continua.
```

Veja a ordem das mensagens: o `imprimir` de baixo só aparece **depois** que a janela fecha, porque `gui.iniciar()` segura o programa enquanto ela estiver aberta.

## Campo e botão: reagindo ao clique

- `gui.campo(janela, "dica", largura=20)` cria uma caixa de digitação. `campo.valor()` devolve o que foi digitado (sempre **texto**, como na aula 4); `campo.definir("texto")` escreve nela; `campo.limpar()` apaga.
- `gui.botao(janela, "Texto", (x) => { ... })` cria um botão. A função no final é executada a cada clique. (O `x` recebe o próprio botão; por enquanto não precisamos dele.)
- `rotulo.texto("novo texto")` troca o texto de um `gui.label`.

<!--codigo:aula22_exemplo2.dk-->
```advak
seja jan = gui.janela("Cumprimento", 380, 240)

gui.label(jan, "Qual é o seu nome?")
seja campo_nome = gui.campo(jan, "Digite aqui", largura=25)
seja resposta = gui.label(jan, "")                      // começa vazio

seja botao = gui.botao(jan, "Cumprimentar", (x) => {
    seja nome = campo_nome.valor()
    resposta.texto(`Olá, ${nome}!`)
    imprimir("Clique recebido. Nome digitado:", nome)
})

// --- Só para o exemplo: a pessoa "digita" e "clica" ---
gui.apos(300, () => {
    campo_nome.definir("Ana")
    botao.invoke()                                      // simula o clique
})
gui.apos(900, () => {
    imprimir("Texto que a janela mostra:", resposta.cget("text"))
    gui.parar()
})

gui.iniciar()
```

<!--saida:aula22_exemplo2.dk-->
```text
Clique recebido. Nome digitado: Ana
Texto que a janela mostra: Olá, Ana!
```

O que aconteceu: ao clicar, a Advak chamou a função do botão, que leu o campo, montou a frase com template string (aula 14) e a colocou no `label`. A linha `resposta.cget("text")` só serve para o exemplo **mostrar no terminal** o texto que está na janela.

## Uma calculadora de IMC

O IMC (índice de massa corporal) é o peso dividido pela altura ao quadrado. Juntando campos, botão, conversão e a validação da aula 15:

<!--codigo:aula22_exemplo3.dk-->
```advak
seja jan = gui.janela("Calculadora de IMC", 380, 300)

gui.label(jan, "Calculadora de IMC", negrito=verdadeiro)
gui.label(jan, "Peso (kg):")
seja campo_peso = gui.campo(jan, "ex: 70", largura=15)
gui.label(jan, "Altura (m):")
seja campo_altura = gui.campo(jan, "ex: 1.75", largura=15)
seja resultado = gui.label(jan, "")

função calcular() {
    seja peso_texto = campo_peso.valor()
    seja altura_texto = campo_altura.valor()
    se (!e_numero(peso_texto) ou !e_numero(altura_texto)) {      // valida antes de converter
        resultado.texto("Digite só números.")
        retornar
    }
    seja peso = numero(peso_texto)
    seja altura = numero(altura_texto)
    se (altura <= 0) {
        resultado.texto("A altura deve ser maior que zero.")
        retornar
    }
    seja imc = peso / (altura * altura)
    resultado.texto(`Seu IMC é ${arred(imc, 1)}`)
}

seja botao = gui.botao(jan, "Calcular", (x) => { calcular() }, estilo="sucesso")

// --- Só para o exemplo: três tentativas ---
gui.apos(300, () => {
    campo_peso.definir("abc")
    campo_altura.definir("1.75")
    botao.invoke()
})
gui.apos(700, () => {
    imprimir("1ª tentativa:", resultado.cget("text"))
    campo_peso.definir("70")
    botao.invoke()
})
gui.apos(1100, () => {
    imprimir("2ª tentativa:", resultado.cget("text"))
    campo_altura.definir("0")
    botao.invoke()
})
gui.apos(1500, () => {
    imprimir("3ª tentativa:", resultado.cget("text"))
    gui.parar()
})

gui.iniciar()
```

<!--saida:aula22_exemplo3.dk-->
```text
1ª tentativa: Digite só números.
2ª tentativa: Seu IMC é 22.9
3ª tentativa: A altura deve ser maior que zero.
```

Repare que a função `calcular` é uma função comum (aula 12): o botão só a chama. E que o `estilo="sucesso"` deixa o botão verde (também existem `"perigo"` e `"secundario"`).

## Tabelas

`gui.tabela(janela, ["Coluna 1", "Coluna 2"], altura=5)` cria uma grade. Com ela:

- `tabela.adicionar([valor1, valor2])` acrescenta uma linha;
- `tabela.limpar()` apaga todas as linhas;
- `tabela.preencher(lista_de_linhas)` troca tudo de uma vez;
- `tabela.selecionado()` devolve a linha escolhida pela pessoa (como um mapa, com o nome das colunas) ou `nulo` se nenhuma foi escolhida.

<!--codigo:aula22_exemplo4.dk-->
```advak
seja jan = gui.janela("Lista de compras", 420, 300)

gui.label(jan, "Lista de compras", negrito=verdadeiro)
seja tabela = gui.tabela(jan, ["Item", "Quantidade"], altura=5)

tabela.adicionar(["Arroz", 2])
tabela.adicionar(["Feijão", 1])
tabela.adicionar(["Café", 3])

imprimir("Selecionado no começo:", tabela.selecionado())

// --- Só para o exemplo: a pessoa clica na 2ª linha ---
gui.apos(300, () => {
    seja linhas = lista(tabela.get_children())
    tabela.selection_set(linhas[1])
})
gui.apos(800, () => {
    seja escolhido = tabela.selecionado()
    imprimir("Selecionado depois do clique:", escolhido)
    imprimir("Item:", escolhido["Item"], "| Quantidade:", escolhido["Quantidade"])
    tabela.limpar()
    imprimir("Linhas depois de limpar:", lista(tabela.get_children()).tamanho)
    gui.parar()
})

gui.iniciar()
```

<!--saida:aula22_exemplo4.dk-->
```text
Selecionado no começo: nulo
Selecionado depois do clique: {Item: Feijão, Quantidade: 1}
Item: Feijão | Quantidade: 1
Linhas depois de limpar: 0
```

## Organizando: linha de botões

`gui.frame_horizontal(janela)` cria uma "faixa" onde as peças ficam lado a lado. Ideal para uma fileira de botões. Veja um contador com três botões:

<!--codigo:aula22_exemplo5.dk-->
```advak
seja jan = gui.janela("Contador", 360, 200)

seja total = 0
seja mostrador = gui.label(jan, "Valor: 0", negrito=verdadeiro, tamanho=16)

função mostrar() {
    mostrador.texto(`Valor: ${total}`)
}

seja faixa = gui.frame_horizontal(jan)
seja mais = gui.botao(faixa, "+1", (x) => {
    total = total + 1
    mostrar()
})
seja menos = gui.botao(faixa, "-1", (x) => {
    total = total - 1
    mostrar()
}, estilo="perigo")
seja zerar = gui.botao(faixa, "Zerar", (x) => {
    total = 0
    mostrar()
}, estilo="secundario")

// --- Só para o exemplo: seis cliques ---
gui.apos(300, () => { mais.invoke() })
gui.apos(500, () => { mais.invoke() })
gui.apos(700, () => { mais.invoke() })
gui.apos(900, () => { menos.invoke() })
gui.apos(1100, () => {
    imprimir("Depois de +1 +1 +1 -1:", mostrador.cget("text"))
    zerar.invoke()
})
gui.apos(1400, () => {
    imprimir("Depois de Zerar:", mostrador.cget("text"))
    gui.parar()
})

gui.iniciar()
```

<!--saida:aula22_exemplo5.dk-->
```text
Depois de +1 +1 +1 -1: Valor: 2
Depois de Zerar: Valor: 0
```

## Erros comuns

**1. Esquecer o `gui.iniciar()`.** A janela é montada e o programa termina na hora, sem ninguém ter tempo de vê-la:

<!--codigo:aula22_erro1.dk-->
```advak
seja jan = gui.janela("Esqueci", 300, 150)
gui.label(jan, "Você não vai me ver")
imprimir("O programa chegou ao fim.")
```

<!--saida:aula22_erro1.dk-->
```text
O programa chegou ao fim.
```

**Como corrigir:** a última linha de um programa com janela é `gui.iniciar()`.

**2. Chamar a função em vez de entregá-la ao botão.** Com `cumprimentar()` (com parênteses), a função roda **uma vez, na hora de criar o botão**, e não a cada clique:

<!--codigo:aula22_erro2.dk-->
```advak
função cumprimentar() {
    imprimir("Função executada!")
}

seja jan = gui.janela("Teste", 300, 150)
imprimir("Antes de criar o botão")
gui.botao(jan, "Clique", cumprimentar())          // errado: já executou
imprimir("Depois de criar o botão (ninguém clicou!)")

gui.apos(500, () => { gui.parar() })
gui.iniciar()
```

<!--saida:aula22_erro2.dk-->
```text
Antes de criar o botão
Função executada!
Depois de criar o botão (ninguém clicou!)
```

**Como corrigir:** entregue uma lambda: `gui.botao(jan, "Clique", (x) => { cumprimentar() })`.

**3. Esquecer que o campo devolve texto.** `campo.valor()` é sempre texto, e um campo vazio devolve `""`. Somar sem converter junta os textos, e `numero("")` dá 0 sem avisar:

<!--codigo:aula22_erro3.dk-->
```advak
seja jan = gui.janela("Teste", 300, 150)
seja campo = gui.campo(jan, "Digite um número", largura=20)

gui.apos(300, () => {
    imprimir("Campo vazio devolve:", "[" + campo.valor() + "]")
    campo.definir("5")
    imprimir("5 + 5 sem converter:", campo.valor() + campo.valor())
    imprimir("5 + 5 convertendo:", numero(campo.valor()) + numero(campo.valor()))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_erro3.dk-->
```text
Campo vazio devolve: []
5 + 5 sem converter: 55
5 + 5 convertendo: 10
```

**Como corrigir:** converta com `numero(...)` e valide com `e_numero(...)` antes (aula 15).

**4. Um erro dentro do botão aparece só no terminal.** Se a função do botão tem um defeito, a Advak mostra o erro **no terminal**, com a mensagem e a linha, mas a janela segue sem reação: o botão simplesmente "não faz nada" nela. Aqui, `arredondar` não existe para números (o certo é `arred`):

<!--codigo:aula22_erro4.dk-->
```advak
seja jan = gui.janela("Teste", 300, 150)
seja saida = gui.label(jan, "ainda não calculou")
seja botao = gui.botao(jan, "Calcular", (x) => {
    imprimir("1) o botão começou a rodar")
    seja valor = 22.857.arredondar(1)              // defeito: esse comando não existe
    imprimir("2) esta linha nunca aparece")
    saida.texto(`IMC ${valor}`)
})

gui.apos(300, () => { botao.invoke() })
gui.apos(900, () => {
    imprimir("Texto da janela depois do clique:", saida.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_erro4.dk-->
```text
1) o botão começou a rodar
❌ Erro em tratador: Não é possível acessar 'arredondar' em número decimal (linha 5)
Texto da janela depois do clique: ainda não calculou
⚠ 1 erro em tratadores (1 diferente).
```

**Como corrigir:** leia a mensagem no terminal: ela diz o que falhou e em que linha (aqui, a 5). Se o botão faz a coisa errada sem mensagem nenhuma, espalhe `imprimir("passou aqui")` pela função: a última mensagem que aparecer mostra onde parou. Também ajuda testar a função fora do botão primeiro, chamando-a direto.

## Exercícios

1. Abra uma janela com o título `Boas-vindas` e um label com seu nome. (Feche-a sozinha após 1 segundo com `gui.apos` e `gui.parar`.)
2. Faça uma janela com um campo e um botão `Repetir`: ao clicar, um label mostra o texto digitado em letras maiúsculas.
3. Faça um conversor de Celsius para Fahrenheit: um campo, um botão e um label com o resultado. Valide com `e_numero`.
4. Faça uma janela com dois campos (a e b) e um botão `Somar` que mostra a soma.
5. Faça um botão que a cada clique aumenta um contador mostrado num label (comece em 0). Simule 3 cliques.
6. Faça uma tabela `Nome | Idade` com 3 pessoas e mostre, no terminal, a pessoa que estiver selecionada (simule a seleção da 3ª linha).
7. Faça uma lista de tarefas simples: um campo, um botão `Adicionar` que acrescenta o texto do campo a uma tabela de uma coluna, e limpa o campo. Simule adicionar duas tarefas e mostre quantas linhas a tabela tem.
8. **Desafio:** faça uma janela de login com campos usuário e senha (`senha=verdadeiro` esconde o que se digita) e um botão `Entrar`. Se o usuário for `admin` e a senha `1234`, o label mostra `Bem-vindo!`; senão, `Dados incorretos.` Simule uma tentativa errada e uma certa.

## Respostas

**Exercício 1**

<!--codigo:aula22_resposta1.dk-->
```advak
seja jan = gui.janela("Boas-vindas", 320, 160)
gui.label(jan, "Ana Souza", negrito=verdadeiro, tamanho=16)
gui.apos(1000, () => { gui.parar() })
gui.iniciar()
imprimir("Janela fechada.")
```

<!--saida:aula22_resposta1.dk-->
```text
Janela fechada.
```

**Exercício 2**

<!--codigo:aula22_resposta2.dk-->
```advak
seja jan = gui.janela("Repetir", 340, 200)
seja campo = gui.campo(jan, "Escreva algo", largura=25)
seja saida = gui.label(jan, "")
seja botao = gui.botao(jan, "Repetir", (x) => {
    saida.texto(campo.valor().maiusculo())
})

gui.apos(300, () => {
    campo.definir("gosto de programar")
    botao.invoke()
})
gui.apos(800, () => {
    imprimir("Janela mostra:", saida.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta2.dk-->
```text
Janela mostra: GOSTO DE PROGRAMAR
```

**Exercício 3**

<!--codigo:aula22_resposta3.dk-->
```advak
seja jan = gui.janela("Conversor", 340, 220)
gui.label(jan, "Graus Celsius:")
seja campo = gui.campo(jan, "ex: 100", largura=15)
seja saida = gui.label(jan, "")
seja botao = gui.botao(jan, "Converter", (x) => {
    seja texto_digitado = campo.valor()
    se (!e_numero(texto_digitado)) {
        saida.texto("Digite um número.")
        retornar
    }
    seja c = numero(texto_digitado)
    saida.texto(`${c} °C = ${c * 9 / 5 + 32} °F`)
})

gui.apos(300, () => {
    campo.definir("abc")
    botao.invoke()
})
gui.apos(700, () => {
    imprimir("Com texto:", saida.cget("text"))
    campo.definir("100")
    botao.invoke()
})
gui.apos(1100, () => {
    imprimir("Com número:", saida.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta3.dk-->
```text
Com texto: Digite um número.
Com número: 100 °C = 212.0 °F
```

**Exercício 4**

<!--codigo:aula22_resposta4.dk-->
```advak
seja jan = gui.janela("Somar", 340, 240)
seja campo_a = gui.campo(jan, "a", largura=10)
seja campo_b = gui.campo(jan, "b", largura=10)
seja saida = gui.label(jan, "")
seja botao = gui.botao(jan, "Somar", (x) => {
    saida.texto(`Soma: ${numero(campo_a.valor()) + numero(campo_b.valor())}`)
})

gui.apos(300, () => {
    campo_a.definir("12")
    campo_b.definir("30")
    botao.invoke()
})
gui.apos(800, () => {
    imprimir(saida.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta4.dk-->
```text
Soma: 42
```

**Exercício 5**

<!--codigo:aula22_resposta5.dk-->
```advak
seja jan = gui.janela("Cliques", 300, 180)
seja total = 0
seja mostrador = gui.label(jan, "Cliques: 0")
seja botao = gui.botao(jan, "Clique aqui", (x) => {
    total = total + 1
    mostrador.texto(`Cliques: ${total}`)
})

gui.apos(300, () => { botao.invoke() })
gui.apos(500, () => { botao.invoke() })
gui.apos(700, () => { botao.invoke() })
gui.apos(1000, () => {
    imprimir(mostrador.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta5.dk-->
```text
Cliques: 3
```

**Exercício 6**

<!--codigo:aula22_resposta6.dk-->
```advak
seja jan = gui.janela("Pessoas", 340, 240)
seja tabela = gui.tabela(jan, ["Nome", "Idade"], altura=4)
tabela.adicionar(["Ana", 17])
tabela.adicionar(["Bruno", 22])
tabela.adicionar(["Carla", 30])

gui.apos(300, () => {
    seja linhas = lista(tabela.get_children())
    tabela.selection_set(linhas[2])
})
gui.apos(800, () => {
    seja p = tabela.selecionado()
    imprimir(`Selecionada: ${p["Nome"]}, ${p["Idade"]} anos`)
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta6.dk-->
```text
Selecionada: Carla, 30 anos
```

**Exercício 7**

<!--codigo:aula22_resposta7.dk-->
```advak
seja jan = gui.janela("Tarefas", 360, 320)
seja campo = gui.campo(jan, "Nova tarefa", largura=30)
seja tabela = gui.tabela(jan, ["Tarefa"], altura=6)
seja botao = gui.botao(jan, "Adicionar", (x) => {
    se (campo.valor() != "") {
        tabela.adicionar([campo.valor()])
        campo.limpar()
    }
})

gui.apos(300, () => {
    campo.definir("Estudar Advak")
    botao.invoke()
})
gui.apos(600, () => {
    campo.definir("Fazer exercícios")
    botao.invoke()
})
gui.apos(900, () => {
    imprimir("Tarefas na tabela:", lista(tabela.get_children()).tamanho)
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta7.dk-->
```text
Tarefas na tabela: 2
```

**Exercício 8**

<!--codigo:aula22_resposta8.dk-->
```advak
seja jan = gui.janela("Login", 320, 260)
gui.label(jan, "Usuário:")
seja campo_usuario = gui.campo(jan, "", largura=20)
gui.label(jan, "Senha:")
seja campo_senha = gui.campo(jan, "", largura=20, senha=verdadeiro)
seja aviso = gui.label(jan, "")

seja botao = gui.botao(jan, "Entrar", (x) => {
    se (campo_usuario.valor() == "admin" e campo_senha.valor() == "1234") {
        aviso.texto("Bem-vindo!")
    } senão {
        aviso.texto("Dados incorretos.")
    }
})

gui.apos(300, () => {
    campo_usuario.definir("admin")
    campo_senha.definir("0000")
    botao.invoke()
})
gui.apos(700, () => {
    imprimir("Tentativa errada:", aviso.cget("text"))
    campo_senha.definir("1234")
    botao.invoke()
})
gui.apos(1100, () => {
    imprimir("Tentativa certa:", aviso.cget("text"))
    gui.parar()
})
gui.iniciar()
```

<!--saida:aula22_resposta8.dk-->
```text
Tentativa errada: Dados incorretos.
Tentativa certa: Bem-vindo!
```

---

**Anterior:** [Aula 21](aula21_banco_de_dados.md) · **Próxima aula:** [Aula 23 — Servidor web: primeira API](aula23_servidor_web.md)
