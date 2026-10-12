# Inteligência artificial na Advak (opcional)

> ## A IA é opcional
> **A Advak funciona 100% sem IA: sem internet, sem chave de API e sem custo.** Nada neste guia é
> necessário para aprender ou usar a linguagem. O módulo `advak_ia.py` **só é carregado quando o seu
> programa chama `ia.conectar(...)`** (ou `ia.registrar` / `ia.provedores`). Antes disso não existe
> nenhum import do módulo, nenhuma chamada de rede e nenhum gasto — isso é verificado por testes
> automáticos. O curso "Aprenda a programar com Advak" ensina tudo sem IA; ela aparece só em uma aula
> opcional no final.

Se você quiser usar, a Advak conecta com várias IAs usando **os mesmos comandos em português**.

## Provedores

| Provedor | Nome na Advak | Chave no `.env` | Precisa de internet? |
|---|---|---|---|
| Anthropic (Claude) | `anthropic` (ou `claude`) | `ADVAK_ANTHROPIC_API_KEY` | sim |
| OpenAI | `openai` (ou `gpt`) | `ADVAK_OPENAI_API_KEY` | sim |
| Google Gemini | `gemini` (ou `google`) | `ADVAK_GEMINI_API_KEY` | sim |
| Mistral | `mistral` | `ADVAK_MISTRAL_API_KEY` | sim |
| Groq | `groq` | `ADVAK_GROQ_API_KEY` | sim |
| DeepSeek | `deepseek` | `ADVAK_DEEPSEEK_API_KEY` | sim |
| OpenRouter | `openrouter` | `ADVAK_OPENROUTER_API_KEY` | sim |
| Ollama (local) | `ollama` | **não precisa** | **não** (roda no seu computador) |

`advak ia` mostra a lista e se a chave de cada um está configurada (nunca mostra o valor).
Não precisa instalar nada: a Advak usa só a biblioteca padrão do Python.

## Configurar

Copie `.env.exemplo` para `.env` e preencha só os provedores que for usar:

```
ADVAK_ANTHROPIC_API_KEY=sua_chave_aqui
ADVAK_OLLAMA_URL=http://localhost:11434      # opcional
ADVAK_OPENAI_MODELO=gpt-4o-mini              # opcional: troca o modelo padrão
```

**Chaves só no `.env`** — não existe parâmetro de chave nos comandos (se alguém tentar
`ia.conectar("openai", chave="...")`, a Advak recusa e explica). O `.env` nunca vai para o GitHub. As chaves
nunca aparecem em mensagens de erro, logs ou ao imprimir os objetos.

Os nomes dos modelos padrão ficam na tabela `PROVEDORES` do `advak_ia.py` e mudam com o tempo; se um
modelo for descontinuado, use `ADVAK_<PROVEDOR>_MODELO` ou `ia.conectar("openai", modelo="...")`.

## Usar

```
seja assistente = ia.conectar("anthropic")                          // um provedor
seja assistente = ia.conectar(["anthropic", "groq", "ollama"])      // ordem de preferência, com reserva

assistente.perguntar("Explique recursão", {sistema: "Responda em 2 linhas"})   // pergunta única
assistente.conversar("Oi!")                                         // mantém o histórico da conversa
assistente.conversar("E o que é uma lista?")
assistente.conversar([{papel: "usuario", texto: "Oi"}])             // histórico explícito, sem memória
assistente.limpar()   assistente.historico()   assistente.info()   assistente.provedores()
```

Opções (segundo parâmetro): `sistema`, `provedor` (força um deles), `modelo`, `max_tokens`,
`temperatura`, `tempo_limite` e, com o módulo de documentos, `anexos`.

**Reserva automática.** Com vários provedores, se o primeiro falhar (sem chave, sem internet, limite de uso,
erro do servidor) a Advak tenta o próximo e diz qual foi usado em `assistente.info()`. Se todos falharem,
o erro lista o motivo de cada um.

**Provedor próprio** (qualquer servidor compatível com o formato OpenAI, como o LM Studio ou um servidor da escola):

```
ia.registrar("escola", {url: "http://servidor:1234/v1/chat/completions", modelo: "qwen", chave: falso})
seja assistente = ia.conectar("escola")
```

## Gerar código

```
seja assistente = ia.conectar("anthropic")
assistente.gerar_codigo("calculadora de médias", "medias.dk")
```

O que acontece, nesta ordem:

1. a IA escreve o programa `.dk`;
2. a Advak **valida a sintaxe** (a mesma verificação do `advak check`); se houver erro, devolve o erro à IA
   e tenta de novo (até 3 tentativas);
3. o código é **mostrado na tela**;
4. a Advak **pergunta** `Salvar em 'medias.dk'? [s/N]` (e uma segunda vez se o arquivo já existir);
5. só com `s` o arquivo é gravado.

**A Advak nunca executa o código gerado.** Você lê, entende e, se quiser, roda com `advak medias.dk`.
Código com erro de sintaxe nunca é salvo. Sem terminal para responder, nada é salvo. Importante: a validação
confere a *sintaxe*, não se o programa faz o que você pediu — **leia antes de executar**.

## Erros comuns (todos em português)

| Situação | O que a Advak diz |
|---|---|
| Chave ausente | Qual variável colocar no `.env` e que o `.env` não vai para o GitHub |
| Chave inválida (401/403) | Confira a variável no `.env`, sem espaços nem aspas |
| Limite de uso (429) | Espere, confira o plano ou use outro provedor na reserva |
| Sem internet | Verifique a conexão ou use o Ollama (funciona offline) |
| Ollama desligado | Rode `ollama serve` e `ollama pull <modelo>` |
| Modelo não encontrado (404) | Confira o nome do modelo (`ADVAK_<PROVEDOR>_MODELO`) |

## Privacidade e dados sensíveis

**Tudo que você envia a uma API externa (perguntas, textos, documentos, imagens) sai do seu computador**
e é processado pelo provedor, sob as regras dele. Não envie senhas, dados pessoais de alunos, notas,
laudos ou outros dados sensíveis a provedores externos. Para esses casos use o **modo local**: o **Ollama**
roda no seu computador e nada sai dele (e, para imagens e PDFs digitalizados, o OCR local do módulo de
documentos). Chaves de API também não devem ser compartilhadas nem enviadas por e-mail.

Texto vindo de fora (documentos, páginas, respostas de pessoas) deve ser tratado como **dado**, não como
instrução: a Advak coloca esse conteúdo separado da sua pergunta e avisa a IA para não obedecer comandos
escritos dentro dele. Isso reduz, mas não elimina, o risco de uma IA ser enganada por um texto malicioso.

## O que foi testado de verdade e o que foi simulado

| O quê | Como | Resultado |
|---|---|---|
| Formato das requisições e respostas dos 8 provedores | **Simulado** (`testes/test_ia_mock.py`, 45 testes, sem rede) | passam |
| Erros (401, 404, 429, 5xx, sem rede, tempo esgotado, Ollama desligado, resposta inválida) | **Simulado** | passam |
| Reserva entre provedores, escolha por nome, histórico, provedor próprio | **Simulado** | passam |
| Chaves nunca em erros, `repr`, `info` e tabelas | **Simulado** (inclui servidor que ecoa a chave) | passam |
| `gerar_codigo`: valida, mostra, pede confirmação, não salva sem `s`, nunca executa | **Simulado** | passam |
| A IA não é carregada nem usa rede antes de `ia.conectar` | **Real** (roda o interpretador e bloqueia conexões externas) | passa |
| Programa `.dk` conversando com um servidor HTTP falso em `localhost` imitando o Ollama | **Real, local** (`testes/test_ia_local.py`) | passa |
| Chamadas às APIs reais (Anthropic, OpenAI, Gemini, Mistral, Groq, DeepSeek, OpenRouter) | **Não testado**: não há chaves neste repositório. `testes/ia_real.dk` roda só os provedores cujas chaves estiverem no `.env` (cada teste faz uma chamada pequena e pode gastar centavos) | pendente |
| Ollama real | **Não testado**. Rode `testes/ia_real.dk` com `ADVAK_TESTE_OLLAMA=1` | pendente |

Ou seja: a Advak foi verificada contra respostas simuladas e contra um servidor local falso, **mas nenhuma
API real de IA foi chamada**. Se um provedor mudar o formato da API ou o nome de um modelo, o ajuste é
feito em `advak_ia.py`. Se você testar com uma chave, conte o resultado.
