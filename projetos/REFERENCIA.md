// ═══════════════════════════════════════════════════════════════════════════
//  ADVAK 5.0 — GLOSSÁRIO COMPLETO
//  Toda a sintaxe em Português — sem uma palavra em inglês!
// ═══════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
// PALAVRAS-CHAVE DA LINGUAGEM
// ═══════════════════════════════════════════════════════════════════════════

// Variáveis
seja x = 10                    // var / let
fixo PI = 3.14                 // const
retornar x + y                 // return

// Condicionais
se (x > 0) { }             // if
senão { }                  // else
senão se (x == 0) { }      // else if

// Laços
para (i em lista) { }      // for/* ... */of
para (seja i=0; i<10; i++) { } // for clássico
enquanto (x > 0) { }       // while
quebrar                         // break
continuar                       // continue

// Funções
funcao calcular(a, b) { }  // function
retornar a + b                 // return
assincrona funcao f() { }  // async function
aguarda f()                    // await

// Classes
classe Animal { }           // class
herda Animal                    // extends
inicio(nome) { }            // constructor
isso.nome = nome                // this.name
super(args)                     // super(args)
super.metodo()                  // super.method()

// Tipos e valores
verdadeiro / falso              // true / false
nulo                            // null
tipo(x)                         // typeof(x)

// Módulos
importar { fn } de "arquivo.dk" // import
exportar funcao fn() { }    // export

// Tratamento de erros
tentar { }                  // try
pegar (e) { }               // catch
finalmente { }              // finally
lançar("mensagem")              // throw

// Pattern matching
combinar x {                    // switch/match
    caso 1 => imprimir("um")
    caso 2 => imprimir("dois")
    caso _ => imprimir("outro")
}

// ═══════════════════════════════════════════════════════════════════════════
// FUNÇÕES GLOBAIS
// ═══════════════════════════════════════════════════════════════════════════

imprimir("Olá")                // print / console.log
entrada("Digite: ")            // input
tipo(valor)                    // typeof

// Matemática
arred(3.14, 2)                 // round(3.14, 2)     → 3.14
piso(3.9)                      // floor(3.9)          → 3
teto(3.1)                      // ceil(3.1)           → 4
raiz(16)                       // sqrt(16)            → 4.0
abs(-5)                        // abs(-5)             → 5
aleatorio()                    // random()            → 0.0 a 1.0
inteiro_aleatorio(1, 10)       // randint(1, 10)

// Conversão
numero("42")                   // float("42")         → 42
inteiro("3.9")                 // int("3.9")          → 3
texto(42)                      // str(42)             → "42"
lista("abc")                   // list("abc")         → ["a","b","c"]
booleano(1)                    // bool(1)             → verdadeiro

// Verificação
e_numero("5")                  // isinstance → verdadeiro
e_texto("oi")                  // isinstance → verdadeiro
e_lista([1,2])                 // isinstance → verdadeiro
e_nulo(nulo)                   // isinstance → verdadeiro

// Formatação
moeda(1500.50)                 // "R$ 1.500,50"
num_abrev(1500000)             // "1.5M"
porcentagem(0.75)              // "75%"
formatar_data("2024-12-25")    // "25/12/2024"
data_hoje()                    // "25/04/2026"
data_agora("%H:%M:%S")         // "20:30:00"

// ═══════════════════════════════════════════════════════════════════════════
// STRINGS
// ═══════════════════════════════════════════════════════════════════════════

seja s = "Olá, mundo!"
seja t = `Olá, ${nome}!`       // template string

s.tamanho                      // .length
s.maiusculo()                  // .toUpperCase()
s.minusculo()                  // .toLowerCase()
s.aparar()                     // .trim()
s.trim()                       // .trim() (alias)
s.dividir(",")                 // .split(",")
s.substituir("a", "b")        // .replace("a", "b")
s.contem("ok")                 // .includes("ok")
s.primeiros(3)                 // .slice(0, 3)
s.substr(0, 3)                 // .substring(0, 3)
s.indexOf("x")                 // .indexOf("x")
s.padStart(5, "0")             // .padStart(5, "0")
s.padEnd(5, " ")               // .padEnd(5, " ")
s.repeat(3)                    // .repeat(3)
s.match("[0-9]+")              // .match(regex)

// ═══════════════════════════════════════════════════════════════════════════
// LISTAS
// ═══════════════════════════════════════════════════════════════════════════

seja lista = [1, 2, 3, 4, 5]

lista.tamanho                           // .length
lista.adicionar(6)                      // .push(6)
lista.remover(0)                        // .splice(0, 1)
lista.inclui(3)                         // .includes(3)
lista.ordenar()                         // .sort()
lista.inverter()                        // .reverse()
lista.unir(", ")                        // .join(", ")
lista.fatia(1, 3)                       // .slice(1, 3)
lista.unico()                           // [/* ... */new Set(lista)]
lista.soma()                            // reduce → soma
lista.min()                             // Math.min
lista.max()                             // Math.max

// Funcionais
lista.filtrar((x) => x > 2)            // .filter()
lista.mapear((x) => x * 2)             // .map()
lista.mapear((x, i) => i)              // .map() com índice
lista.reduzir((acc, x) => acc+x, 0)    // .reduce()
lista.encontrar((x) => x > 3)          // .find()
lista.algum((x) => x > 4)              // .some()
lista.todos((x) => x > 0)              // .every()
lista.para_cada((x) => imprimir(x))    // .forEach()
lista.para_cada_com_indice((v,i) => {}) // .forEach with index
lista.flat()                            // .flat()

// ═══════════════════════════════════════════════════════════════════════════
// MAPAS (Objetos)
// ═══════════════════════════════════════════════════════════════════════════

seja obj = {nome: "Ana", idade: 17}

obj.nome                       // obj.name
obj.chaves                     // Object.keys(obj)
obj.valores                    // Object.values(obj)
obj.tamanho                    // Object.keys(obj).length
obj.contem("nome")             // "nome" in obj
obj.mapear((k, v) => v*2)     // map over entries
obj.filtrar((k, v) => v > 5)  // filter entries
obj.para_cada((k, v) => { })  // forEach entries

// ═══════════════════════════════════════════════════════════════════════════
// ARQUIVO
// ═══════════════════════════════════════════════════════════════════════════

Arquivo.escrever("dados.txt", "conteúdo")
Arquivo.ler("dados.txt")
Arquivo.ler_linhas("dados.txt")
Arquivo.escrever_json("dados.json", {a: 1})
Arquivo.ler_json("dados.json")
Arquivo.info("dados.txt")              // {nome, tamanho, /* ... */}
Arquivo.listar("pasta", ".dk")
Arquivo.criar_pasta("nova/pasta")
Arquivo.copiar("origem.txt", "dest.txt")

// ═══════════════════════════════════════════════════════════════════════════
// SERVIDOR WEB
// ═══════════════════════════════════════════════════════════════════════════

servidor.porta(8080)
servidor.obter("/rota",    (req) => { })   // GET
servidor.publicar("/rota", (req) => { })   // POST
servidor.atualizar("/rota",(req) => { })   // PUT
servidor.deletar("/rota",  (req) => { })   // DELETE
servidor.qualquer("/rota", (req) => { })   // TODOS
servidor.estatico("/css",  "./pasta")
servidor.iniciar(8080)
servidor.parar()

// Objeto req (requisição):
req.metodo           // "GET", "POST", etc
req.caminho          // "/api/usuarios"
req.consulta.campo   // ?campo=valor na URL
req.parametros.id    // /rota/:id → valor do :id
req.dados.campo      // corpo JSON (POST)
req.dados            // corpo JSON completo
req.corpo            // corpo bruto (string)
req.cabecalhos       // cabeçalhos HTTP
req.eh_get           // verdadeiro se GET
req.eh_post          // verdadeiro se POST

// Respostas:
retornar html("<h1>Olá!</h1>")
retornar html("<h1>Erro</h1>", 404)
retornar resposta_json({chave: "valor"})
retornar resposta_json({erro: "/* ... */"}, 400)
retornar resposta_texto("texto puro")
retornar redirecionar("/nova-url")

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACE GRÁFICA (GUI)
// ═══════════════════════════════════════════════════════════════════════════

gui.tema("escuro")
seja jan = gui.janela("Meu App", 900, 600)

// Widgets:
gui.label(jan, "Texto", tamanho=12, negrito=verdadeiro, cor="#3B82F6")
gui.botao(jan, "Clique!", ao_clicar=() => fn(), estilo="sucesso")
gui.campo(jan, placeholder="Digite/* ... */", largura=30)
gui.area_texto(jan, largura=40, altura=5)
gui.checkbox(jan, texto="Ativo")
gui.slider(jan, minimo=0, maximo=100)
gui.switch(jan, "Modo escuro")
gui.caixa_selecao(jan, opcoes=["A","B","C"])
gui.tabela(jan, colunas=["Nome","Nota"], ao_selecionar=(l) => fn(l))
gui.abas(jan)
gui.card(jan, "Título", "Descrição")
gui.badge(jan, "Novo", "verde")
gui.separador(jan)
gui.barra_status(jan, "Pronto")
gui.barra_progresso(jan, 0, 100)
gui.frame(jan, cor="#1E293B")
gui.frame_horizontal(jan)

// pack() em PORTUGUÊS:
widget.pack(lado="esquerda", preencher="x", expandir=verdadeiro)
widget.pack(lado="direita",  espaco_x=8, espaco_y=4)
widget.pack(lado="topo",     espaco_ix=6)
widget.pack(ancora="oeste")  // w=oeste, e=leste, n=norte, s=sul

// configure() em PORTUGUÊS:
widget.configure(text="novo texto")
widget.configure(estado="desabilitado")   // disabled
widget.configure(estado="habilitado")     // normal
widget.configure(estado="somente_leitura")// readonly

// Diálogos:
gui.alerta("Mensagem!")
gui.aviso("Atenção!")
gui.confirmar("Tem certeza?")         // retorna verdadeiro/falso
gui.pedir("Digite um valor:")         // retorna texto ou nulo
gui.toast("Salvo!", "sucesso", 3000)
gui.escolher_arquivo()

// Eventos:
jan.bind("<F12>", (e) => fn())
jan.bind("<Return>", (e) => fn())

// Timer:
gui.apos(1000, () => fn())           // após 1 segundo
gui.repetir(500, () => fn())         // a cada 500ms

// Animações:
gui.animar(widget, "x", 300, duracao=500)
gui.iniciar()

// ═══════════════════════════════════════════════════════════════════════════
// BANCO DE DADOS (PostgreSQL)
// ═══════════════════════════════════════════════════════════════════════════

banco.sql("SELECT * FROM tabela")
banco.sql("SELECT * FROM t WHERE id=$1", [id])
banco.sql("BEGIN")
banco.sql("COMMIT")
banco.sql("ROLLBACK")

// ═══════════════════════════════════════════════════════════════════════════
// REGEX
// ═══════════════════════════════════════════════════════════════════════════

Regex.testar("[0-9]+", "abc123")           // → verdadeiro
Regex.extrair("[0-9]+", "nota: 9")         // → [9]
Regex.extrair_todos("[a-z]+", "abc def")   // → [abc, def]
Regex.substituir("[0-9]", "X", "a1b2")    // → aXbX
Regex.dividir(",", "a,b,c")               // → [a, b, c]

// ═══════════════════════════════════════════════════════════════════════════
// TESTES UNITÁRIOS
// ═══════════════════════════════════════════════════════════════════════════

testar("Nome do teste", () => {
    afirmar_igual(2 + 2, 4)
    afirmar_verdadeiro(5 > 3)
    afirmar_falso(5 > 10)
    afirmar_nulo(nulo)
    afirmar_contem([1,2,3], 2)
    afirmar_erro(() => { lançar("erro esperado") })
})
resumo_testes()

// ═══════════════════════════════════════════════════════════════════════════
// HTTP (Consumir APIs)
// ═══════════════════════════════════════════════════════════════════════════

HTTP.get("https://api.exemplo.com/dados")
HTTP.json("https://api.exemplo.com/dados")     // GET + parse JSON
HTTP.post("https://api.exemplo.com", {a: 1})
HTTP.baixar("https://site.com/file.pdf", "local.pdf")
