"""
Advak: protocolo de linhas entre o programa e a placa, e a PlacaSimulada (etapa 2.1a).

Este módulo só define o protocolo e uma simulação em Python da placa. Não abre porta serial, não usa pyserial e não é
exposto à linguagem Advak (isso é a etapa 2.1b).

AVISO: a PlacaSimulada é o que o protocolo PREVÊ para o firmware. O firmware real ainda não existe, e nada aqui foi
testado em hardware. Em particular, a verificação de limites feita pela placa e o watchdog da placa são o comportamento
previsto para o firmware, e não uma proteção que já exista em uma placa de verdade.

O "OK" da placa confirma que o comando foi ACEITO, não que o servo chegou à posição: um servo comum não informa a
posição real. Por isso a placa guarda e devolve o ÚLTIMO COMANDO aceito (SERVO GET), e não "o ângulo atual".

Protocolo, versão 1. Texto ASCII, uma linha por comando (terminada em \\n no fio; os métodos daqui recebem e devolvem a
linha sem o \\n), no máximo 64 bytes, uma resposta por comando, palavras em maiúsculas separadas por um único espaço:

    programa -> placa                placa -> programa
    OLA                              OK ADVAK 1 servo
    PING                             PONG
    SERVO ADD <pino> <min> <max> <seg>   OK SERVO <pino> <seg>       (registra o servo e vai à posição segura)
    SERVO SET <pino> <angulo>        OK SERVO <pino> <angulo>        (último comando aceito)
    SERVO GET <pino>                 OK SERVO <pino> <ultimo_comando>
    SERVO SAFE <pino>                OK SERVO <pino> <seg>
    SERVO SAFE ALL                   OK SAFE <quantos servos foram para a posição segura>
    (placa, sem comandos aceitos por 3000 ms)  AVISO WATCHDOG       (vai à posição segura de todos os servos)

Erros (a resposta é "ERRO <codigo> <numeros>"): FORMATO, PINO <pino>, LIMITE <pino> <angulo> <min> <max>,
LIMITES <pino> <min> <max> <seg>, REGISTRADO <pino>, WATCHDOG. Depois do aviso de watchdog a placa recusa SERVO SET
(ERRO WATCHDOG) até receber OLA de novo; PING, GET, SAFE e ADD continuam aceitos.

Só um comando ACEITO pela placa (resposta OK ou PONG) reinicia a contagem do watchdog. Uma linha que segue o protocolo
mas é recusada (ERRO LIMITE, LIMITES, PINO, REGISTRADO ou WATCHDOG) e uma linha que não segue o protocolo (ERRO FORMATO)
não adiam o watchdog: um programa preso repetindo comandos recusados cai no estado seguro.
"""
import collections
import re
import time
from typing import Callable, List, Optional, Tuple

VERSAO_PROTOCOLO = 1
MAX_BYTES_LINHA = 64
ANGULO_MINIMO = 0
ANGULO_MAXIMO = 180
PINO_MAXIMO = 53
WATCHDOG_PADRAO_MS = 3000

_INTEIRO = re.compile(r"-?[0-9]{1,6}")
# quantos números vêm depois de "ERRO <codigo>"
_ERROS = {"FORMATO": 0, "PINO": 1, "LIMITE": 4, "LIMITES": 4, "REGISTRADO": 1, "WATCHDOG": 0}


class ErroDeProtocolo(Exception):
    """A linha não segue o protocolo. `codigo` é o texto que vem depois de ERRO (ou RESPOSTA, para uma resposta inválida)."""

    def __init__(self, codigo: str):
        super().__init__(codigo)
        self.codigo = codigo


# ---------------------------------------------------------------- linhas do programa para a placa
def _inteiro(valor, nome: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} precisa ser um inteiro, mas veio {valor!r}")
    return valor


def linha_ola() -> str:
    return "OLA"


def linha_ping() -> str:
    return "PING"


def linha_servo_add(pino: int, minimo: int, maximo: int, seguro: int) -> str:
    return (f"SERVO ADD {_inteiro(pino, 'pino')} {_inteiro(minimo, 'minimo')} {_inteiro(maximo, 'maximo')} "
            f"{_inteiro(seguro, 'seguro')}")


def linha_servo_set(pino: int, angulo: int) -> str:
    return f"SERVO SET {_inteiro(pino, 'pino')} {_inteiro(angulo, 'angulo')}"


def linha_servo_get(pino: int) -> str:
    return f"SERVO GET {_inteiro(pino, 'pino')}"


def linha_servo_safe(pino: int) -> str:
    return f"SERVO SAFE {_inteiro(pino, 'pino')}"


def linha_servo_safe_todos() -> str:
    return "SERVO SAFE ALL"


def _inteiros(tokens: List[str]) -> List[int]:
    for t in tokens:
        if not _INTEIRO.fullmatch(t):
            raise ErroDeProtocolo("FORMATO")
    return [int(t) for t in tokens]


def analisar_comando(linha) -> tuple:
    """Lê uma linha do programa. Devolve ('OLA',), ('PING',), ('ADD', pino, min, max, seg), ('SET', pino, angulo),
    ('GET', pino), ('SAFE', pino) ou ('SAFE', 'ALL'). Qualquer outra coisa levanta ErroDeProtocolo('FORMATO')."""
    if (not isinstance(linha, str) or not linha or len(linha.encode("utf-8")) > MAX_BYTES_LINHA
            or "\n" in linha or "\r" in linha or linha != linha.strip() or "  " in linha):
        raise ErroDeProtocolo("FORMATO")
    t = linha.split(" ")
    if t == ["OLA"]:
        return ("OLA",)
    if t == ["PING"]:
        return ("PING",)
    if t[0] == "SERVO" and len(t) >= 3:
        verbo, args = t[1], t[2:]
        if verbo == "ADD" and len(args) == 4:
            return ("ADD", *_inteiros(args))
        if verbo == "SET" and len(args) == 2:
            return ("SET", *_inteiros(args))
        if verbo == "GET" and len(args) == 1:
            return ("GET", *_inteiros(args))
        if verbo == "SAFE" and len(args) == 1:
            return ("SAFE", "ALL" if args[0] == "ALL" else _inteiros(args)[0])
    raise ErroDeProtocolo("FORMATO")


def interpretar_resposta(linha) -> tuple:
    """Lê uma linha da placa. Devolve ('OK_ADVAK', versao), ('PONG',), ('OK_SERVO', pino, comando), ('OK_SAFE', n),
    ('ERRO', codigo, (numeros,)) ou ('AVISO', 'WATCHDOG'). Resposta inválida levanta ErroDeProtocolo('RESPOSTA')."""
    if not isinstance(linha, str) or not linha or linha != linha.strip() or "  " in linha:
        raise ErroDeProtocolo("RESPOSTA")
    t = linha.split(" ")
    try:
        if t[0] == "OK" and len(t) == 4 and t[1] == "ADVAK" and t[3] == "servo":
            return ("OK_ADVAK", *_inteiros([t[2]]))
        if t == ["PONG"]:
            return ("PONG",)
        if t[0] == "OK" and len(t) == 4 and t[1] == "SERVO":
            return ("OK_SERVO", *_inteiros(t[2:]))
        if t[0] == "OK" and len(t) == 3 and t[1] == "SAFE":
            return ("OK_SAFE", *_inteiros(t[2:]))
        if t == ["AVISO", "WATCHDOG"]:
            return ("AVISO", "WATCHDOG")
        if t[0] == "ERRO" and len(t) >= 2 and t[1] in _ERROS and len(t) - 2 == _ERROS[t[1]]:
            return ("ERRO", t[1], tuple(_inteiros(t[2:])))
    except ErroDeProtocolo:
        pass
    raise ErroDeProtocolo("RESPOSTA")


# ---------------------------------------------------------------- relógio e placa simulada
class RelogioFalso:
    """Relógio injetável para os testes: milissegundos que só andam quando `avancar` é chamado."""

    def __init__(self, inicio_ms: float = 0.0):
        self._ms = float(inicio_ms)

    def __call__(self) -> float:
        return self._ms

    def avancar(self, ms: float) -> None:
        if ms < 0:
            raise ValueError("o relógio falso não anda para trás")
        self._ms += ms


class PlacaSimulada:
    """Máquina de estados do protocolo, do lado da placa. Não usa thread nem dorme: o tempo vem de `relogio` (uma função
    que devolve milissegundos) e o watchdog é avaliado quando chega uma linha, em `ler_linha` e em `atualizar`. Só
    comandos aceitos (resposta OK ou PONG) reiniciam a contagem do watchdog; linhas recusadas ou inválidas não.

    muda=True faz a placa ignorar tudo (nenhuma resposta, nenhum estado), para testar tempo limite.
    arquivo_log: caminho; cada linha trocada é anexada como "<ms>\\t>\\t<linha>" (programa -> placa) ou
    "<ms>\\t<\\t<resposta>" (placa -> programa). Em memória, o mesmo fica em `registro`."""

    def __init__(self, relogio: Optional[Callable[[], float]] = None, watchdog_ms: float = WATCHDOG_PADRAO_MS,
                 muda: bool = False, arquivo_log: Optional[str] = None):
        if isinstance(watchdog_ms, bool) or not isinstance(watchdog_ms, (int, float)) or watchdog_ms <= 0:
            raise ValueError(f"watchdog_ms precisa ser um número maior que zero, mas veio {watchdog_ms!r}")
        self._relogio = relogio or (lambda: time.monotonic() * 1000.0)
        self.watchdog_ms = watchdog_ms
        self.muda = bool(muda)
        self.arquivo_log = arquivo_log
        self.registro: List[Tuple[float, str, str]] = []
        self._respostas: collections.deque = collections.deque()
        self._servos: dict = {}
        self._ultimo_aceito_ms = self._relogio()
        self._em_watchdog = False

    # ---- o que o programa usa
    def enviar_linha(self, linha) -> None:
        """Programa -> placa. A resposta (se houver) fica na fila de `ler_linha`."""
        self.atualizar()
        agora = self._relogio()
        self._registrar(">", linha if isinstance(linha, str) else repr(linha))
        if self.muda:
            return
        try:
            resposta = self._executar(analisar_comando(linha))
            self._ultimo_aceito_ms = agora   # só um comando aceito (OK ou PONG) reinicia o watchdog
        except ErroDeProtocolo as e:
            resposta = f"ERRO {e.codigo}"
        self._responder(resposta)

    def ler_linha(self) -> Optional[str]:
        """Placa -> programa. Devolve a próxima resposta, ou None se não há nenhuma."""
        self.atualizar()
        return self._respostas.popleft() if self._respostas else None

    def atualizar(self) -> None:
        """Avalia o watchdog com o relógio atual: sem comandos aceitos por `watchdog_ms`, todos os servos vão à posição
        segura e a placa avisa uma vez (AVISO WATCHDOG)."""
        if self.muda or self._em_watchdog or not self._servos:
            return
        if self._relogio() - self._ultimo_aceito_ms >= self.watchdog_ms:
            for s in self._servos.values():
                s["comando"] = s["seguro"]
            self._em_watchdog = True
            self._responder("AVISO WATCHDOG")

    # ---- consultas (para os testes)
    def ultimo_comando(self, pino: int) -> Optional[int]:
        """Último comando ACEITO para o servo (não é a posição real). None se o pino não está registrado."""
        s = self._servos.get(pino)
        return None if s is None else s["comando"]

    def pinos_registrados(self) -> List[int]:
        return sorted(self._servos)

    @property
    def em_watchdog(self) -> bool:
        return self._em_watchdog

    @property
    def ultimo_aceito_ms(self) -> float:
        """Instante (em ms do relógio) do último comando aceito, ou o da criação da placa se nenhum foi aceito."""
        return self._ultimo_aceito_ms

    # ---- por dentro
    def _servo(self, pino: int) -> dict:
        if pino not in self._servos:
            raise ErroDeProtocolo(f"PINO {pino}")
        return self._servos[pino]

    def _executar(self, cmd: tuple) -> str:
        tipo = cmd[0]
        if tipo == "OLA":
            self._em_watchdog = False
            return f"OK ADVAK {VERSAO_PROTOCOLO} servo"
        if tipo == "PING":
            return "PONG"
        if tipo == "ADD":
            _, pino, minimo, maximo, seguro = cmd
            if not 0 <= pino <= PINO_MAXIMO:
                raise ErroDeProtocolo(f"PINO {pino}")
            if pino in self._servos:
                raise ErroDeProtocolo(f"REGISTRADO {pino}")
            if not (ANGULO_MINIMO <= minimo < maximo <= ANGULO_MAXIMO and minimo <= seguro <= maximo):
                raise ErroDeProtocolo(f"LIMITES {pino} {minimo} {maximo} {seguro}")
            self._servos[pino] = {"minimo": minimo, "maximo": maximo, "seguro": seguro, "comando": seguro}
            return f"OK SERVO {pino} {seguro}"
        if tipo == "SET":
            _, pino, angulo = cmd
            s = self._servo(pino)
            if self._em_watchdog:
                raise ErroDeProtocolo("WATCHDOG")
            if not s["minimo"] <= angulo <= s["maximo"]:
                raise ErroDeProtocolo(f"LIMITE {pino} {angulo} {s['minimo']} {s['maximo']}")
            s["comando"] = angulo
            return f"OK SERVO {pino} {angulo}"
        if tipo == "GET":
            s = self._servo(cmd[1])
            return f"OK SERVO {cmd[1]} {s['comando']}"
        if tipo == "SAFE":
            if cmd[1] == "ALL":
                for s in self._servos.values():
                    s["comando"] = s["seguro"]
                return f"OK SAFE {len(self._servos)}"
            s = self._servo(cmd[1])
            s["comando"] = s["seguro"]
            return f"OK SERVO {cmd[1]} {s['seguro']}"
        raise ErroDeProtocolo("FORMATO")   # não acontece: analisar_comando só devolve os tipos acima

    def _responder(self, texto: str) -> None:
        self._respostas.append(texto)
        self._registrar("<", texto)

    def _registrar(self, direcao: str, texto: str) -> None:
        agora = self._relogio()
        self.registro.append((agora, direcao, texto))
        if self.arquivo_log:
            with open(self.arquivo_log, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"{agora:.1f}\t{direcao}\t{texto}\n")
