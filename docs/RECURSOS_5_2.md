# Novos recursos da linguagem (Advak 5.2) — notas de trabalho

Este arquivo cresce a cada recurso novo da Etapa 2. O conteúdo alimenta o README, o CHANGELOG e o guia da
Etapa 3. Cada recurso tem testes em `testes/`.

## Intervalos

```
para (i em 1..4) { }            // 1, 2, 3              — o fim fica de FORA
para (i em 1..=4) { }           // 1, 2, 3, 4           — o fim fica DENTRO
para (i em 0..=100 passo 5) { } // 0, 5, 10 ... 100     — passo (sinônimo em inglês: step)
para (i em 5..=1 passo -1) { }  // 5, 4, 3, 2, 1        — para contar para trás use passo negativo
seja pares = 2..=10 passo 2     // [2, 4, 6, 8, 10]     — fora de um laço o intervalo vira uma lista
seja n = 4
para (i em 1..n + 1) { }        // 1..(n + 1): os limites são expressões completas
```

Regras:

- `..` exclui o fim (como `Lista.intervalo(a, b)` e o `range` do Python); `..=` inclui o fim.
- **Não há inversão automática**: `10..1` é um intervalo vazio. Para contar para trás escreva `10..=1 passo -1`.
- Início, fim e passo precisam ser **números inteiros**. Um decimal que é inteiro (`4.0`, resultado de `8 / 2`)
  é aceito; `2.5` dá erro com a dica de usar `piso()`, `teto()` ou `arred()`. Passo `0` dá erro.
- Em `para (i em a..b)` o intervalo é **preguiçoso**: `para (i em 1..=100000000) { ... quebrar }` não cria
  uma lista de 100 milhões de itens. Fora de um laço o intervalo vira lista, com limite de 10 milhões de itens.
- `passo`/`step` só vale logo depois de um intervalo; fora dele continua sendo um nome comum (`seja passo = 3`).
  Atenção: `1..passo` (sem espaço antes de passo e sem outro número) lê `passo` como a variável do fim.

Onde está o código: tokens `..` e `..=` em `advak_lexer.py`; `parse_range` em `advak_parser.py` (acima de
`+`/`-` e abaixo das comparações); `_eval_intervalo` em `advak_interpreter.py`; `advak_nativo.py` (transpilador
Python) e `advak_formatador.py` (não separa mais `..=`).

Testes: `testes/intervalos.dk` (comportamento, 13 casos), `testes/test_intervalos.py` (lexer, parser,
formatador e transpilador).

Observação encontrada no caminho (não é do recurso): o transpilador Python falhava com `KeyError: 'value'` em
qualquer número negativo literal, e o formatador separava `+=`, `-=` e `=>` com espaços indevidos. Os dois
foram corrigidos depois (veja o CHANGELOG).

## Compreensão de listas

```
[x * 2 para x em lista se x > 0]                  // transforma e filtra
[x * x para x em 1..=10]                           // combina com intervalos
[x para x em 0..=20 passo 5 se x != 10]
[[x, y] para x em 1..=3 para y em 1..=3 se x < y]  // laços aninhados: [[1, 2], [1, 3], [2, 3]]
[a + b para (a, b) em [[1, 2], [3, 4]]]            // desmonta cada par: [3, 7]
[c para c em "banana" se c != "a"]                  // percorre texto: ["b", "n", "n"]
[x > 0 ? x : 0 para x em numeros]                  // o elemento pode ser qualquer expressão
[x * 2 for x in lista if x > 0]                    // sinônimos em inglês: for / in (of) / if
```

Regras:

- O resultado é sempre uma **lista nova**. O que vem depois de `em` pode ser lista, texto, mapa (percorre as
  chaves, como o `para-em`), intervalo ou gerador. Outro valor (número, nulo...) dá erro em português.
- Pode haver **vários `para`** (laços aninhados, da esquerda para a direita) e **vários `se`**; cada `se`
  filtra o que vem antes dele.
- `para (a, b) em pares` desmonta cada item em nomes; se o item não tiver a quantidade certa de valores, dá erro.
- A variável do `para` existe **só dentro da compreensão**: não vaza e não altera uma variável de fora com o
  mesmo nome. As cláusulas enxergam as variáveis de fora e as variáveis das cláusulas anteriores.
- Sem parênteses em volta do `para` (diferente do laço de instrução `para (i em lista) { }`).
- A origem é percorrida de forma preguiçosa (um intervalo não vira lista antes), mas o **resultado** tem teto de
  10 milhões de itens.
- Não existe tupla em Advak: para devolver dois valores use uma lista (`[x, y]`), não `(x, y)`.
- Fica de fora desta versão: compreensão de **mapa** (`{k: v para ...}`) e de conjunto.

Observação: o parser de listas sempre foi tolerante e aceita itens sem vírgula (`[a b c]` vira lista de três
itens). Isso não mudou; por isso `[para x em l]` (sem o elemento antes do `para`) continua sendo uma lista de
quatro nomes e não um erro de sintaxe.

Onde está o código: `parse_list_literal` e `_parse_compreensao` em `advak_parser.py`; `_comp_rec` em
`advak_interpreter.py`; `advak_nativo.py` gera a compreensão equivalente em Python.

Testes: `testes/compreensao.dk` (16 casos) e `testes/test_compreensao.py` (parser, erros de sintaxe, limite,
transpilador, formatador).

## Interpolação com formatação

Só em textos com **crase** (como sempre); textos com aspas não interpolam. Depois de `:` vem o formato:

```
seja preco = 1500.5
imprimir(`Total: ${preco:moeda}`)                  // Total: R$ 1.500,50
imprimir(`Zero casas: ${preco:moeda.0}`)           // R$ 1.501
imprimir(`Desconto: ${0.075:porcentagem.1}`)       // 7,5%
imprimir(`Habitantes: ${1234567:numero}`)          // 1.234.567
imprimir(`Pi: ${3.14159:.2f}`)                     // 3,14
imprimir(`Pedido ${7:03d}`)                        // Pedido 007
imprimir(`[${nome:>10}] [${nome:<10}] [${nome:^10}] [${nome:*^9}]`)
imprimir(`${nome:maiusculo}`)                      // ANA
imprimir(`Hoje: ${"2024-12-25":dd/mm/aaaa}`)       // Hoje: 25/12/2024
imprimir(`${"2024-12-25 14:30":dd/mm/aaaa hh:mm}`) // 25/12/2024 14:30
imprimir(`${"2024-12-25":dddd, dd [de] mmmm [de] aaaa}`)   // quarta-feira, 25 de dezembro de 2024
```

**Formatos com nome** (sinônimo em inglês entre parênteses):

| Formato | Resultado |
|---|---|
| `moeda` (`currency`), `moeda.N` | `R$ 1.500,50`; `-R$ 9,90`; `.N` = casas decimais |
| `numero` (`number`), `numero.N` | `1.234.567`; `1.234,5` (decimais sem zeros à direita); `.N` fixa as casas |
| `porcentagem` (`pct`, `percent`), `porcentagem.N` | `75%`, `7,5%` |
| `maiusculo` (`upper`), `minusculo` (`lower`), `titulo` (`title`) | transforma o texto |
| `data` (`date`), `hora` (`time`), `datahora` (`datetime`) | `25/12/2024`, `14:30`, `25/12/2024 14:30` |

**Padrão de data** (qualquer formato com `dd`, `mm`, `aaaa`/`yyyy`, `aa`/`yy`, `hh` ou `ss`): `mmmm` = mês por
extenso, `mmm` = jan, `dddd` = dia da semana por extenso, `ddd` = seg. Texto entre colchetes sai como está
(`dd [de] mmmm`). `mm` é o **mês**, exceto quando vem logo depois de `hh` (com um separador curto como `:`, `h`
ou espaço) ou antes de `:ss`: aí são **minutos**. Meses e dias são sempre em português.

**Estilo Python** (alinhamento, zeros, casas): `.2f`, `,.2f`, `05d`, `>10`, `<10`, `^10`, `*^20`, `+.1f`, `x`, `.1%`.

Regras e decisões:

- **Separadores do Brasil em todo formato numérico**, inclusive no estilo Python: `${3.14159:.2f}` dá `3,14` e
  `${1234.5:,.2f}` dá `1.234,50` (diferente do Python puro, que usaria o ponto decimal).
- **Arredondamento escolar** (0,5 sobe): `${2.675:moeda}` dá `R$ 2,68` e `${2.5:.0f}` dá `3`. O Python puro daria
  `2,67` e `2`, por causa da representação binária e do arredondamento para o par.
- **`porcentagem` segue a função `porcentagem()`**: valores de 0 a 1 são tratados como fração (`0.75` → 75%),
  os outros ficam como estão (`75` → 75%). Pegadinha: `1` vira `100%`. (Diferença mínima: no formato, 0,5 sobe;
  a função arredonda para o par.)
- **Nulo** continua saindo como `nulo`, sem aplicar o formato. Formato numérico em texto/booleano, formato
  desconhecido, data inválida, `hora` em um valor sem hora etc. dão **erro em português**
  (`Formato inválido em ${...}: ...`) na hora em que o texto é montado (`advak check` não olha dentro dos templates).
- **Datas** aceitas: texto `aaaa-mm-dd`, `dd/mm/aaaa`, `dd-mm-aaaa`, com hora opcional (`T` ou espaço; segundos;
  fração; fuso é ignorado), texto `hh:mm`, e objetos `date`/`datetime`/`time` do Python (os que vêm do banco).
  Números não são datas.
- **O `:` do formato** é o primeiro que está fora de `()`, `[]`, `{}` e textos e que não é de um ternário.
  `${p > 1 ? a : b}` continua um ternário; com formato: `${p > 1 ? a : b :moeda}`; para o contrário, use
  parênteses. O formato pode ter `:` (`hh:mm`). **Aspas e crases dentro do formato não são aceitas.**
- **Chaves dentro de `${}`** agora funcionam (`` `${ {a: 1}.a }` ``, `` `${"}"}` ``), o que antes dava erro.
  Templates sem formato e sem chaves aninhadas continuam com exatamente o mesmo resultado (testado contra o
  comportamento antigo com milhares de textos aleatórios).
- Fora desta versão: `abrev` (a função `num_abrev()` continua existindo) e moedas estrangeiras.

Efeitos em ferramentas (corrigidos junto, porque o recurso os expôs):

- `advak formatar` mexia **dentro de textos** (`:,.2f` virava `:, .2f`; `"a,b"` virava `"a, b"`; espaços duplos
  eram colapsados) e **colapsava o recuo** das linhas para 1 espaço. Agora textos e comentários ficam intactos,
  textos de crase de várias linhas não são tocados e o recuo é preservado.
- `advak --verificar` sugeria "possível divisão" para o `/` de `dd/mm/aaaa` e de qualquer texto/comentário;
  agora ignora o que está dentro de textos e comentários.
- O texto de instruções do `gerar_codigo` (IA) dizia que `"..."` interpola; corrigido para crases.

Onde está o código: `advak_formatacao.py` (novo; sem dependências), `_interp_template` em `advak_interpreter.py`,
`advak_formatador.py` e `advak_verificador.py`. O transpilador Python não suporta templates (já era assim).

Testes: `testes/formatacao.dk` (14 casos) e `testes/test_formatacao.py` (37 testes: divisor de templates,
separador de formato, números, estilo Python, datas, integração e ferramentas).

## Tipagem opcional

Anotações de tipo são **opcionais**: só o que foi anotado é conferido, em **tempo de execução**. Programas sem
tipos funcionam exatamente como antes.

```
seja idade: inteiro = 17
fixo nome: texto = "Ana"
seja apelido: texto? = nulo                       // ? aceita também nulo
seja valor: inteiro | texto = "10"                // um tipo OU outro
seja notas: lista[numero] = [7, 8.5]              // cada elemento é conferido
seja pessoa: Pessoa = novo Pessoa("Ana")          // classe, estrutura, enum ou tipo algébrico

função somar(a: numero, b: numero = 0) -> numero { retornar a + b }
função saudar(nome: texto) { imprimir(`Oi ${nome}`) }       // sem -> : o retorno é livre
classe Conta { inicio(saldo: numero) { ... }   depositar(v: numero) -> nulo { ... } }
```

| Tipo (sinônimos) | Aceita |
|---|---|
| `inteiro` (`int`, `integer`) | só inteiros. `5.0` **não** é inteiro; booleano também não |
| `numero` (`número`, `decimal`, `flutuante`, `float`, `number`) | inteiro ou decimal (nunca booleano) |
| `texto` (`string`, `str`) | texto |
| `booleano` (`bool`, `boolean`) | `verdadeiro` / `falso` |
| `lista` (`list`, `array`), `lista[T]` | lista; com `[T]`, cada elemento é conferido |
| `mapa` (`objeto`, `dict`, `map`), `mapa[T]` | mapa; com `[T]`, cada valor é conferido |
| `funcao` (`função`, `function`) | função, lambda ou método |
| `nulo` (`null`) | só nulo |
| `qualquer` (`any`) | qualquer valor |
| nome de classe / `estrutura` / `enum` / `tipo` | instância daquele tipo (classes: inclui as subclasses) |

Modificadores: `T?` também aceita `nulo`; `A | B` aceita qualquer um dos dois; `lista[lista[inteiro]]` aninha.

Quando a conferência acontece:

- **Declaração**: `seja x: T = valor` confere o valor. `seja x: T` sem valor é permitido (começa como `nulo`); o
  primeiro valor atribuído é conferido. `= nulo` explícito só passa em `T?`, `nulo` ou `qualquer`.
- **Reatribuição**: toda atribuição (`=`, `+=`, `++`...) é conferida, inclusive por uma função interna que altera
  a variável de fora. Um novo `seja x = ...` sem tipo, no mesmo escopo, remove a anotação.
- **Parâmetros**: conferidos a cada chamada, também o valor padrão quando é usado. Argumento que faltou chega como
  `nulo` e a mensagem sugere isso. Parâmetro `...resto` (spread) não é conferido.
- **Retorno** (`-> T`): conferido quando a função retorna. Se terminar sem `retornar`, o valor é `nulo` e só passa em
  `nulo`, `T?` ou `qualquer`. Em função assíncrona vale o valor final; em geradores só os parâmetros são conferidos.
- **Tipo desconhecido** (`Int`, `strng`, `lista[Foo]`) dá erro listando os tipos válidos, na declaração da variável
  ou na primeira chamada da função.

Mensagens (português, com a linha do erro):

```
Tipo incorreto: 'idade' é inteiro, mas recebeu texto ("abc").
Tipo incorreto no parâmetro 'a' de somar(): esperava numero, mas recebeu texto ("x").
Tipo incorreto no retorno de somar(): esperava numero, mas retornou texto ("x").
Tipo inválido em variável 'z': tipo desconhecido 'Int'. Tipos disponíveis: ...
```

Decisões e limites desta versão:

- **`inteiro` é estrito e não há conversão automática**: `seja x: inteiro = 10 / 2` dá erro, porque `/` devolve
  decimal (use `10 // 2` ou `inteiro(10 / 2)`). `seja nota: numero = 7` funciona.
- **Fora desta versão**: parâmetros tipados em **lambdas com seta** (`(a: numero) => ...` é erro de sintaxe; a
  função anônima `função(a: numero) { }` aceita), tipos em desestruturação e em `para (x: T em ...)`, conferência
  dos **campos** de `estrutura` (continuam só anotados) e checagem **estática** no `advak --verificar`
  (os erros aparecem ao executar).
- `->` virou um símbolo da linguagem (tipo de retorno); em `i-->0` o `--` continua sendo o decremento.
- Interfaces aceitam `-> T` nos métodos, mas não conferem tipos.
- Custo: só o código anotado paga. Medido em 30.000 repetições: variável tipada ≈ +9% de tempo em um laço que só
  atribui; função com 2 parâmetros e retorno tipados ≈ +28% por chamada (≈ 40 µs).

Efeito colateral corrigido: usar um tipo algébrico (`tipo Arvore { Folha, ... }`) como valor, por exemplo
`seja a = Arvore.Folha`, dava "Variante 'get' não existe" (o mesmo defeito que o `enum` tinha); agora funciona.

Onde está o código: `advak_tipos.py` (novo, sem dependências), `parse_tipo` / `parse_retorno` / `parse_params` em
`advak_parser.py`, o token `->` em `advak_lexer.py`, e em `advak_interpreter.py`: `Scope.tipos`, `_CtxTipos`,
`_conferir_parametro` / `_conferir_retorno` e `var_decl`.

Testes: `testes/tipagem.dk` (26 casos) e `testes/test_tipagem.py` (21 testes: lexer, parser, tabela de conferência,
mensagens, e verificação de que nenhum `.dk` do repositório usa anotações).