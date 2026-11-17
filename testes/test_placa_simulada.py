"""
Etapa 2.1a: protocolo de linhas e PlacaSimulada (advak_placa.py). Testes unitários, sem serial, sem pyserial e sem hardware.

O tempo vem de um relógio injetado (RelogioFalso); só um teste (W8) usa tempo real, com tolerância larga.
O esperado de cada caso foi escrito antes da primeira execução.

Rodar:  python -I testes/test_placa_simulada.py
"""
import os
import sys
import tempfile
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from advak_placa import (ErroDeProtocolo, PlacaSimulada, RelogioFalso, analisar_comando, interpretar_resposta,  # noqa: E402
                         linha_ola, linha_ping, linha_servo_add, linha_servo_get, linha_servo_safe,
                         linha_servo_safe_todos, linha_servo_set)


def nova(**opcoes):
    """Uma placa com relógio falso em 0 ms. Devolve (placa, relogio)."""
    relogio = RelogioFalso()
    return PlacaSimulada(relogio=relogio, **opcoes), relogio


def conversar(placa, *linhas):
    """Envia cada linha e devolve todas as respostas disponíveis, na ordem."""
    for linha in linhas:
        placa.enviar_linha(linha)
    saida = []
    while True:
        r = placa.ler_linha()
        if r is None:
            return saida
        saida.append(r)


class TesteAnalisarComando(unittest.TestCase):
    def test_A1_comandos_validos(self):
        casos = {
            "OLA": ("OLA",),
            "PING": ("PING",),
            "SERVO ADD 9 0 180 90": ("ADD", 9, 0, 180, 90),
            "SERVO SET 9 120": ("SET", 9, 120),
            "SERVO SET 9 -5": ("SET", 9, -5),
            "SERVO GET 9": ("GET", 9),
            "SERVO SAFE 9": ("SAFE", 9),
            "SERVO SAFE ALL": ("SAFE", "ALL"),
        }
        for linha, esperado in casos.items():
            with self.subTest(linha=linha):
                self.assertEqual(analisar_comando(linha), esperado)

    def test_A2_formato_invalido(self):
        invalidas = ["", " OLA", "OLA ", "SERVO  SET 9 5", "ola", "SERVO", "SERVO SET", "SERVO ADD 9 0 180",
                     "SERVO ADD 9 0 180 90 1", "SERVO SET 9 abc", "SERVO SET 9 +5", "SERVO SET 9 1.5",
                     "SERVO SET 9 1234567", "SERVO MOVER 9 5", "SERVO SAFE", "SERVO SAFE todos", "SERVO SAFE 9 8",
                     "PING 1", "OLA OLA", "A\nB", "A\rB", "SERVO\tSET 9 5", "x" * 65, "OLÁ", 5, None, b"OLA", ["OLA"]]
        for linha in invalidas:
            with self.subTest(linha=linha):
                with self.assertRaises(ErroDeProtocolo) as ctx:
                    analisar_comando(linha)
                self.assertEqual(ctx.exception.codigo, "FORMATO")

    def test_A3_o_erro_carrega_o_codigo(self):
        try:
            analisar_comando("xyz")
        except ErroDeProtocolo as e:
            self.assertEqual(e.codigo, "FORMATO")
            self.assertEqual(str(e), "FORMATO")
        else:
            self.fail("não levantou ErroDeProtocolo")


class TesteInterpretarResposta(unittest.TestCase):
    def test_R1_respostas_validas(self):
        casos = {
            "OK ADVAK 1 servo": ("OK_ADVAK", 1),
            "PONG": ("PONG",),
            "OK SERVO 9 120": ("OK_SERVO", 9, 120),
            "OK SAFE 2": ("OK_SAFE", 2),
            "ERRO LIMITE 9 200 0 180": ("ERRO", "LIMITE", (9, 200, 0, 180)),
            "ERRO LIMITES 9 0 181 90": ("ERRO", "LIMITES", (9, 0, 181, 90)),
            "ERRO PINO 10": ("ERRO", "PINO", (10,)),
            "ERRO REGISTRADO 9": ("ERRO", "REGISTRADO", (9,)),
            "ERRO FORMATO": ("ERRO", "FORMATO", ()),
            "ERRO WATCHDOG": ("ERRO", "WATCHDOG", ()),
            "AVISO WATCHDOG": ("AVISO", "WATCHDOG"),
        }
        for linha, esperado in casos.items():
            with self.subTest(linha=linha):
                self.assertEqual(interpretar_resposta(linha), esperado)

    def test_R2_respostas_invalidas(self):
        invalidas = ["", "OK", "OK SERVO 9", "OK SERVO a b", "OK ADVAK 1", "OK ADVAK 1 motor", "ERRO", "ERRO XYZ",
                     "ERRO LIMITE 9 200 0", "ERRO FORMATO 1", "AVISO", "AVISO OUTRO", "pong", " PONG", "OK SAFE",
                     "OK SAFE x", None, 7]
        for linha in invalidas:
            with self.subTest(linha=linha):
                with self.assertRaises(ErroDeProtocolo) as ctx:
                    interpretar_resposta(linha)
                self.assertEqual(ctx.exception.codigo, "RESPOSTA")

    def test_R3_o_que_se_monta_se_le_de_volta(self):
        self.assertEqual(analisar_comando(linha_ola()), ("OLA",))
        self.assertEqual(analisar_comando(linha_ping()), ("PING",))
        self.assertEqual(linha_servo_add(9, 0, 180, 90), "SERVO ADD 9 0 180 90")
        self.assertEqual(analisar_comando(linha_servo_add(9, 0, 180, 90)), ("ADD", 9, 0, 180, 90))
        self.assertEqual(linha_servo_set(9, 120), "SERVO SET 9 120")
        self.assertEqual(analisar_comando(linha_servo_set(9, -5)), ("SET", 9, -5))
        self.assertEqual(analisar_comando(linha_servo_get(9)), ("GET", 9))
        self.assertEqual(analisar_comando(linha_servo_safe(9)), ("SAFE", 9))
        self.assertEqual(linha_servo_safe_todos(), "SERVO SAFE ALL")
        self.assertEqual(analisar_comando(linha_servo_safe_todos()), ("SAFE", "ALL"))

    def test_R4_montar_exige_inteiros(self):
        for chamada in (lambda: linha_servo_set(9, 90.5), lambda: linha_servo_set(9, "90"),
                        lambda: linha_servo_set(9, True), lambda: linha_servo_add(9, 0, 180, None),
                        lambda: linha_servo_get("9"), lambda: linha_servo_safe(1.0)):
            with self.subTest():
                with self.assertRaises(TypeError):
                    chamada()


class TestePlacaBasico(unittest.TestCase):
    def test_B1_cumprimento(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "OLA"), ["OK ADVAK 1 servo"])
        self.assertIsNone(placa.ler_linha())

    def test_B2_ping(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "PING"), ["PONG"])

    def test_B3_registrar_um_servo(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "SERVO ADD 9 0 180 90"), ["OK SERVO 9 90"])
        self.assertEqual(placa.ultimo_comando(9), 90)
        self.assertEqual(placa.pinos_registrados(), [9])
        self.assertIsNone(placa.ultimo_comando(10))

    def test_B4_mover_e_perguntar(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120", "SERVO GET 9"),
                         ["OK SERVO 9 90", "OK SERVO 9 120", "OK SERVO 9 120"])
        self.assertEqual(placa.ultimo_comando(9), 120)

    def test_B5_fora_dos_limites_e_recusado(self):
        placa, _ = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        self.assertEqual(conversar(placa, "SERVO SET 9 200", "SERVO SET 9 -1", "SERVO SET 9 181"),
                         ["ERRO LIMITE 9 200 0 180", "ERRO LIMITE 9 -1 0 180", "ERRO LIMITE 9 181 0 180"])
        self.assertEqual(placa.ultimo_comando(9), 90)

    def test_B6_os_limites_valem_para_cada_servo_e_as_bordas_passam(self):
        placa, _ = nova()
        conversar(placa, "SERVO ADD 9 30 150 90")
        self.assertEqual(conversar(placa, "SERVO SET 9 29", "SERVO SET 9 151"),
                         ["ERRO LIMITE 9 29 30 150", "ERRO LIMITE 9 151 30 150"])
        self.assertEqual(conversar(placa, "SERVO SET 9 30", "SERVO SET 9 150"), ["OK SERVO 9 30", "OK SERVO 9 150"])

    def test_B7_pino_nao_registrado(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "SERVO SET 10 50", "SERVO GET 10", "SERVO SAFE 10"), ["ERRO PINO 10"] * 3)

    def test_B8_registro_recusado(self):
        placa, _ = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        pedidos = {
            "SERVO ADD 9 0 180 90": "ERRO REGISTRADO 9",
            "SERVO ADD 54 0 180 90": "ERRO PINO 54",
            "SERVO ADD -1 0 180 90": "ERRO PINO -1",
            "SERVO ADD 10 100 100 100": "ERRO LIMITES 10 100 100 100",
            "SERVO ADD 10 0 181 90": "ERRO LIMITES 10 0 181 90",
            "SERVO ADD 10 -1 180 90": "ERRO LIMITES 10 -1 180 90",
            "SERVO ADD 10 0 180 200": "ERRO LIMITES 10 0 180 200",
            "SERVO ADD 10 50 100 40": "ERRO LIMITES 10 50 100 40",
        }
        for linha, esperado in pedidos.items():
            with self.subTest(linha=linha):
                self.assertEqual(conversar(placa, linha), [esperado])
        self.assertEqual(conversar(placa, "SERVO GET 10"), ["ERRO PINO 10"])
        self.assertEqual(placa.pinos_registrados(), [9])

    def test_B9_posicao_segura_de_um_e_de_todos(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "SERVO SAFE ALL"), ["OK SAFE 0"])
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO ADD 10 30 150 100", "SERVO SET 9 10", "SERVO SET 10 140")
        self.assertEqual(conversar(placa, "SERVO SAFE 9"), ["OK SERVO 9 90"])
        self.assertEqual((placa.ultimo_comando(9), placa.ultimo_comando(10)), (90, 140))
        conversar(placa, "SERVO SET 9 10")
        self.assertEqual(conversar(placa, "SERVO SAFE ALL"), ["OK SAFE 2"])
        self.assertEqual((placa.ultimo_comando(9), placa.ultimo_comando(10)), (90, 100))

    def test_B10_formato_invalido_nao_muda_o_estado(self):
        placa, _ = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120")
        self.assertEqual(conversar(placa, "SERVO SET 9 abc", "SERVO", "", "xyz"), ["ERRO FORMATO"] * 4)
        self.assertEqual(placa.ultimo_comando(9), 120)

    def test_B11_dois_servos_sao_independentes(self):
        placa, _ = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO ADD 10 45 135 90")
        self.assertEqual(conversar(placa, "SERVO SET 10 150", "SERVO SET 9 150"),
                         ["ERRO LIMITE 10 150 45 135", "OK SERVO 9 150"])
        self.assertEqual((placa.ultimo_comando(9), placa.ultimo_comando(10)), (150, 90))

    def test_B12_uma_resposta_por_comando_e_em_ordem(self):
        placa, _ = nova()
        self.assertEqual(conversar(placa, "OLA", "PING", "SERVO ADD 9 0 180 90", "SERVO GET 9"),
                         ["OK ADVAK 1 servo", "PONG", "OK SERVO 9 90", "OK SERVO 9 90"])

    def test_B13_sem_resposta_devolve_none(self):
        placa, _ = nova()
        self.assertIsNone(placa.ler_linha())
        self.assertIsNone(placa.ler_linha())

    def test_B14_linha_que_nao_e_texto(self):
        placa, _ = nova()
        placa.enviar_linha(5)
        self.assertEqual(placa.ler_linha(), "ERRO FORMATO")
        self.assertEqual(placa.registro[0], (0.0, ">", "5"))

    def test_B15_watchdog_invalido(self):
        for valor in (0, -1, "x", None, True):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    PlacaSimulada(watchdog_ms=valor)


class TesteWatchdog(unittest.TestCase):
    def test_W1_sem_servo_registrado_nao_ha_aviso(self):
        placa, relogio = nova()
        conversar(placa, "OLA")
        relogio.avancar(10000)
        self.assertIsNone(placa.ler_linha())
        self.assertFalse(placa.em_watchdog)

    def test_W2_dispara_exatamente_em_3000_ms(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120")
        relogio.avancar(2999)
        self.assertIsNone(placa.ler_linha())
        self.assertEqual(placa.ultimo_comando(9), 120)
        relogio.avancar(1)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")
        self.assertEqual(placa.ultimo_comando(9), 90)
        self.assertTrue(placa.em_watchdog)

    def test_W3_ping_reinicia_a_contagem(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120")
        relogio.avancar(2000)
        self.assertEqual(conversar(placa, "PING"), ["PONG"])
        relogio.avancar(2000)
        self.assertIsNone(placa.ler_linha())
        self.assertEqual(placa.ultimo_comando(9), 120)
        relogio.avancar(1000)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")

    def test_W4_o_aviso_vem_uma_vez_so(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(3000)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")
        relogio.avancar(10000)
        self.assertIsNone(placa.ler_linha())

    def test_W5_depois_do_aviso_so_o_cumprimento_libera_o_movimento(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120")
        relogio.avancar(3000)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")
        self.assertEqual(conversar(placa, "SERVO SET 9 100"), ["ERRO WATCHDOG"])
        self.assertEqual(conversar(placa, "PING"), ["PONG"])
        self.assertEqual(conversar(placa, "SERVO GET 9"), ["OK SERVO 9 90"])
        self.assertEqual(conversar(placa, "SERVO SAFE 9"), ["OK SERVO 9 90"])
        self.assertEqual(conversar(placa, "SERVO ADD 10 0 90 45"), ["OK SERVO 10 45"])
        self.assertTrue(placa.em_watchdog)
        self.assertEqual(conversar(placa, "OLA"), ["OK ADVAK 1 servo"])
        self.assertFalse(placa.em_watchdog)
        self.assertEqual(conversar(placa, "SERVO SET 9 130"), ["OK SERVO 9 130"])

    def test_W6_o_aviso_vem_antes_da_resposta_ao_comando_atrasado(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(5000)
        self.assertEqual(conversar(placa, "SERVO SET 9 100"), ["AVISO WATCHDOG", "ERRO WATCHDOG"])
        self.assertEqual(placa.ultimo_comando(9), 90)

    def test_W7_watchdog_configuravel(self):
        placa, relogio = nova(watchdog_ms=500)
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(499)
        self.assertIsNone(placa.ler_linha())
        relogio.avancar(1)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")

    def test_W8_tempo_real_com_tolerancia_larga(self):
        placa = PlacaSimulada(watchdog_ms=200)
        placa.enviar_linha("SERVO ADD 9 0 180 90")
        time.sleep(1.0)
        self.assertEqual([placa.ler_linha(), placa.ler_linha(), placa.ler_linha()],
                         ["OK SERVO 9 90", "AVISO WATCHDOG", None])
        self.assertEqual(placa.ultimo_comando(9), 90)

    def test_W9_uma_linha_invalida_nao_adia_o_watchdog(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(2000)
        self.assertEqual(conversar(placa, "xyz"), ["ERRO FORMATO"])
        relogio.avancar(999)
        self.assertIsNone(placa.ler_linha())
        relogio.avancar(1)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")

    def test_W10_um_ping_valido_adia_o_watchdog(self):
        """Mesma linha do tempo do W9, com PING no lugar da linha inválida: o aviso só vem 3000 ms depois do PING."""
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(2000)
        self.assertEqual(conversar(placa, "PING"), ["PONG"])
        relogio.avancar(2999)
        self.assertIsNone(placa.ler_linha())
        relogio.avancar(1)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")

    def test_W11_linha_recusada_pela_placa_nao_adia_o_watchdog(self):
        """Decisão: só comando ACEITO (OK ou PONG) reinicia a contagem. Uma linha que segue o protocolo mas é recusada
        não adia: o aviso vem 3000 ms depois do último comando aceito (o ADD, em 0 ms)."""
        recusas = [("SERVO SET 9 200", "ERRO LIMITE 9 200 0 180"), ("SERVO SET 10 50", "ERRO PINO 10"),
                   ("SERVO ADD 9 0 180 90", "ERRO REGISTRADO 9"), ("SERVO ADD 10 100 100 100", "ERRO LIMITES 10 100 100 100")]
        for linha, esperado in recusas:
            with self.subTest(linha=linha):
                placa, relogio = nova()
                conversar(placa, "SERVO ADD 9 0 180 90")
                relogio.avancar(2000)
                self.assertEqual(conversar(placa, linha), [esperado])
                self.assertEqual(placa.ultimo_aceito_ms, 0.0)
                relogio.avancar(999)
                self.assertIsNone(placa.ler_linha())
                relogio.avancar(1)
                self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")

    def test_W12_programa_preso_repetindo_comandos_recusados_cai_no_estado_seguro(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90", "SERVO SET 9 120")
        respostas = []
        for _ in range(7):          # um comando recusado a cada 500 ms, de 500 a 3500 ms
            relogio.avancar(500)
            respostas += conversar(placa, "SERVO SET 9 200")
        self.assertEqual(respostas, ["ERRO LIMITE 9 200 0 180"] * 5 + ["AVISO WATCHDOG", "ERRO WATCHDOG", "ERRO WATCHDOG"])
        self.assertEqual(placa.ultimo_comando(9), 90)
        self.assertTrue(placa.em_watchdog)

    def test_W13_comando_recusado_por_watchdog_tambem_nao_reinicia_a_contagem(self):
        placa, relogio = nova()
        conversar(placa, "SERVO ADD 9 0 180 90")
        relogio.avancar(3000)
        self.assertEqual(placa.ler_linha(), "AVISO WATCHDOG")
        relogio.avancar(1000)
        self.assertEqual(conversar(placa, "SERVO SET 9 100"), ["ERRO WATCHDOG"])
        self.assertEqual(placa.ultimo_aceito_ms, 0.0)
        relogio.avancar(500)
        self.assertEqual(conversar(placa, "PING"), ["PONG"])
        self.assertEqual(placa.ultimo_aceito_ms, 4500.0)


class TesteMuda(unittest.TestCase):
    def test_M1_placa_muda_ignora_tudo(self):
        placa, relogio = nova(muda=True)
        self.assertEqual(conversar(placa, "OLA", "SERVO ADD 9 0 180 90"), [])
        self.assertEqual(placa.pinos_registrados(), [])
        relogio.avancar(10000)
        self.assertIsNone(placa.ler_linha())
        self.assertEqual(placa.registro, [(0.0, ">", "OLA"), (0.0, ">", "SERVO ADD 9 0 180 90")])


class TesteLog(unittest.TestCase):
    def test_L1_registro_em_memoria_com_o_tempo_do_relogio(self):
        placa, relogio = nova()
        conversar(placa, "OLA")
        relogio.avancar(12.5)
        conversar(placa, "PING")
        self.assertEqual(placa.registro, [(0.0, ">", "OLA"), (0.0, "<", "OK ADVAK 1 servo"),
                                          (12.5, ">", "PING"), (12.5, "<", "PONG")])

    def test_L2_arquivo_de_log_em_utf8_so_com_lf(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "placa.log")
            placa, _ = nova(arquivo_log=caminho)
            conversar(placa, "OLA", "ângulo:90")
            with open(caminho, "rb") as f:
                conteudo = f.read()
        esperado = ("0.0\t>\tOLA\n0.0\t<\tOK ADVAK 1 servo\n0.0\t>\tângulo:90\n0.0\t<\tERRO FORMATO\n").encode("utf-8")
        self.assertEqual(conteudo, esperado)
        self.assertNotIn(b"\r", conteudo)


class TesteRelogioFalso(unittest.TestCase):
    def test_C1_anda_so_quando_mandam_e_nao_volta(self):
        relogio = RelogioFalso(5)
        self.assertEqual(relogio(), 5.0)
        relogio.avancar(2.5)
        self.assertEqual(relogio(), 7.5)
        with self.assertRaises(ValueError):
            relogio.avancar(-1)
        self.assertEqual(relogio(), 7.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
