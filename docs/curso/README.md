# Aprenda a programar com Advak

Um curso para quem **nunca programou**: 24 aulas curtas, em português, com exemplos do dia a dia, exercícios do fácil ao desafiador e respostas no final de cada aula. Foi pensado para alunos do ensino médio e da EJA, mas serve para qualquer pessoa curiosa.

Você não precisa saber nada antes. Só precisa de um computador com a Advak instalada (veja [como instalar](../INSTALACAO.md)).

## Como estudar

1. **Siga a ordem.** Cada aula usa o que a anterior ensinou.
2. **Digite os exemplos você mesmo**, em vez de só copiar e colar. Errar ao digitar faz parte de aprender.
3. **Rode e compare.** Debaixo de cada exemplo está a saída real do programa. Se o seu resultado for diferente, volte e confira o código.
4. **Faça os exercícios antes de olhar as respostas.** Travou? Releia a aula, tente de novo, e só então espie a resposta.
5. **Mexa nos exemplos.** Troque um número, apague uma linha, veja o que acontece. É assim que se aprende.
6. **Não tenha medo dos erros.** A Advak mostra mensagens em português dizendo o que deu errado e em qual linha. Toda aula tem uma seção "Erros comuns" com mensagens reais.

Cada aula começa com "Ao final desta aula você vai saber..." e termina com exercícios e respostas. Uma aula leva de 30 a 60 minutos.

## As aulas

**Primeiros passos**

| # | Aula | O que você aprende |
|---|---|---|
| 1 | [O que é programar](aula01_o_que_e_programar.md) | algoritmo, a receita de bolo, o primeiro `imprimir` |
| 2 | [REPL e arquivos](aula02_repl_e_arquivos.md) | testar linha a linha e salvar programas `.dk` |
| 3 | [Variáveis, tipos e constantes](aula03_variaveis_tipos_constantes.md) | `seja`, `fixo`, `tipo` |
| 4 | [Entrada e conversão](aula04_entrada_e_conversao.md) | `entrada`, `numero`, `inteiro`, `texto` |
| 5 | [Operadores](aula05_operadores.md) | contas, comparações, `e`, `ou`, `nao` |

**Tomando decisões e repetindo**

| # | Aula | O que você aprende |
|---|---|---|
| 6 | [Decisões](aula06_decisoes.md) | `se`, `senão se`, `senão` |
| 7 | [Escolha múltipla](aula07_combinar.md) | `combinar` |
| 8 | [Repetição com `enquanto`](aula08_enquanto.md) | laços, `quebrar`, `continuar` |
| 9 | [Repetição com `para`](aula09_para.md) | contador e `para ... em` |

**Guardando e organizando dados**

| # | Aula | O que você aprende |
|---|---|---|
| 10 | [Listas](aula10_listas.md) | várias coisas numa variável só |
| 11 | [Mapas](aula11_mapas.md) | dados com nome (chave e valor) |
| 12 | [Funções](aula12_funcoes.md) | parâmetros e retorno |
| 13 | [Lambdas e pipeline](aula13_lambdas.md) | `filtrar`, `mapear`, `reduzir`, `\|>` |
| 14 | [Textos](aula14_textos.md) | métodos de texto e template strings |

**Programas de verdade**

| # | Aula | O que você aprende |
|---|---|---|
| 15 | [Tratamento de erros](aula15_erros.md) | `tentar`, `capturar`, `finalmente`, `lançar` |
| 16 | [Arquivos e JSON](aula16_arquivos_json.md) | guardar dados no disco |
| 17 | [Classes e objetos](aula17_classes.md) | `classe`, `construtor`, `isso`, `novo` |
| 18 | [Herança](aula18_heranca.md) | `herda`, `super` |
| 19 | [Módulos](aula19_modulos.md) | `exportar`, `importar` |
| 20 | [Testes unitários](aula20_testes.md) | `testar`, `afirmar_igual`, `afirmar_erro` |

**Sistemas completos**

| # | Aula | O que você aprende |
|---|---|---|
| 21 | [Banco de dados](aula21_banco_de_dados.md) | SQLite: criar, inserir, buscar, atualizar, apagar |
| 22 | [Interface gráfica](aula22_interface_grafica.md) | janelas, campos, botões, tabelas |
| 23 | [Servidor web](aula23_servidor_web.md) | rotas, JSON, códigos de status |
| 24 | [Projeto final](aula24_projeto_final.md) | agenda de contatos em camadas: dados, testes, tela e API |

## Depois do curso

- O [Guia prático](../GUIA_PRATICO.md) traz 13 sistemas completos para estudar e adaptar.
- O guia de [bancos de dados](../BANCOS_DE_DADOS.md) mostra como usar outros bancos além do SQLite.
- O [README do projeto](../../README.md) lista todos os recursos da linguagem.

## Sobre os exemplos (para quem mantém o curso)

Todo código mostrado nas aulas está em [`codigos/`](codigos/) e foi **executado de verdade**; a saída que aparece nas aulas é a que o programa produziu. O script `testes/curso.py` confere isso:

```text
python testes/curso.py              # confere se código e saídas das aulas batem com o que roda agora
python testes/curso.py --atualizar  # reescreve as saídas das aulas com o resultado real
AULA=aula16 python testes/curso.py  # confere só uma aula
```

Alguns programas (aulas 22 e 24) abrem uma janela por alguns segundos, e os da aula 23 ligam um servidor temporário numa porta local.
