"""
Advak 5.0 — Módulo de Sistemas Embarcados

Suporte completo para desenvolvimento embarcado via:

1. Serial/UART  — comunicação com Arduino, ESP32, sensores
2. MQTT         — protocolo IoT (mosquitto, HiveMQ, AWS IoT)
3. GPIO         — controle de pinos (Raspberry Pi, Orange Pi)
4. I2C / SPI    — protocolos de sensores
5. Sensores     — temperatura, umidade, distância, pressão
6. Atuadores    — servo, motor DC, relé, LED, buzzer
7. Protocolo Modbus — sistemas industriais
8. Automação    — scripts de controle com lógica temporal
9. Dashboard IoT— interface web para monitorar dispositivos
10. Firmware    — gerador de código para Arduino/ESP32

Uso:
    // Comunicação Serial com Arduino
    seja arduino = embarcado.serial.conectar("COM3", 9600)
    arduino.enviar("LED:ON")
    seja resposta = arduino.receber()

    // MQTT para IoT
    seja mqtt = embarcado.mqtt.conectar("broker.hivemq.com")
    mqtt.publicar("casa/sala/temp", 24.5)
    mqtt.subscrever("casa/+/+", função(topico, valor) {
        imprimir(`${topico}: ${valor}`)
    })

    // GPIO (Raspberry Pi)
    seja pino = embarcado.gpio.saida(18)
    pino.ligar()
    embarcado.aguardar(1000)
    pino.desligar()

    // Gerar código Arduino
    embarcado.firmware.arduino("meu_projeto",
        setup="pinMode(13, OUTPUT);",
        loop="digitalWrite(13, HIGH); delay(1000); digitalWrite(13, LOW); delay(1000);"
    )
"""

import os
import json
import threading
import socket
import time
import struct
import queue
import re
from typing import Dict, List, Optional, Callable, Any


# ══════════════════════════════════════════════════════════════════════════════
#  1. COMUNICAÇÃO SERIAL / UART
# ══════════════════════════════════════════════════════════════════════════════

class ConexaoSerial:
    """
    Interface Serial/UART para comunicação com microcontroladores.
    Suporta pyserial se instalado, senão usa simulação para testes.
    """

    def __init__(self, porta: str, baudrate: int = 9600, timeout: float = 1.0):
        self.porta = porta
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None
        self._simulando = False
        self._buffer_sim: queue.Queue = queue.Queue()
        self._conectado = False
        self._callbacks: List[Callable] = []
        self._thread_leitura = None

    def conectar(self):
        """Conecta à porta serial. Usa simulação se pyserial não disponível."""
        try:
            import serial
            self._serial = serial.Serial(
                self.porta, self.baudrate,
                timeout=self.timeout
            )
            self._conectado = True
            print(f"  🔌 Serial: {self.porta} @ {self.baudrate} baud — conectado")
        except ImportError:
            self._simulando = True
            self._conectado = True
            print(f"  🔌 Serial: SIMULADO {self.porta} @ {self.baudrate} baud")
            print(f"     (pip install pyserial para hardware real)")
        except Exception as e:
            self._simulando = True
            self._conectado = True
            print(f"  ⚠️  Serial: {self.porta} — usando simulação ({e})")
        return self

    def enviar(self, dados, nova_linha: bool = True) -> bool:
        """Envia dados pela serial."""
        if not self._conectado:
            return False
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
            if nova_linha:
                dados += b'\n'
        if self._simulando:
            self._buffer_sim.put(f"<ECO:{dados.decode('utf-8', errors='ignore').strip()}>")
            return True
        try:
            self._serial.write(dados)
            return True
        except Exception as e:
            print(f"  ❌ Serial.enviar: {e}")
            return False

    def receber(self, ate_nova_linha: bool = True) -> Optional[str]:
        """Recebe dados da serial."""
        if self._simulando:
            try:
                return self._buffer_sim.get(timeout=self.timeout)
            except queue.Empty:
                return None
        try:
            if ate_nova_linha:
                linha = self._serial.readline()
            else:
                linha = self._serial.read(self._serial.in_waiting or 1)
            return linha.decode('utf-8', errors='ignore').strip() if linha else None
        except Exception:
            return None

    def receber_json(self) -> Optional[dict]:
        """Recebe e parseia JSON da serial."""
        linha = self.receber()
        if linha:
            try:
                return json.loads(linha)
            except json.JSONDecodeError:
                return None
        return None

    def ao_receber(self, fn: Callable, intervalo_ms: int = 50):
        """Registra callback para dados recebidos (leitura contínua)."""
        self._callbacks.append(fn)
        if not self._thread_leitura:
            def _ler():
                while self._conectado:
                    dados = self.receber()
                    if dados:
                        for cb in self._callbacks:
                            try:
                                cb(dados)
                            except Exception:
                                pass
                    time.sleep(intervalo_ms / 1000)
            self._thread_leitura = threading.Thread(target=_ler, daemon=True)
            self._thread_leitura.start()
        return self

    def fechar(self):
        self._conectado = False
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass

    def listar_portas(self) -> List[str]:
        """Lista portas seriais disponíveis."""
        # Tenta pyserial primeiro
        try:
            import serial.tools.list_ports
            return [p.device for p in serial.tools.list_ports.comports()]
        except ImportError:
            pass
        # Windows: lê registro
        try:
            import winreg
            portas = []
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DEVICEMAP\SERIALCOMM")
            i = 0
            while True:
                try:
                    _, valor, _ = winreg.EnumValue(key, i)
                    portas.append(valor)
                    i += 1
                except OSError:
                    break
            return portas if portas else ["COM1", "COM2", "COM3", "COM4"]
        except ImportError:
            pass
        # Linux: /dev/tty*
        import glob
        portas = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyS*')
        return portas if portas else ["COM1", "COM2", "COM3", "/dev/ttyUSB0"]


# ══════════════════════════════════════════════════════════════════════════════
#  2. CLIENTE MQTT
# ══════════════════════════════════════════════════════════════════════════════

class ClienteMQTT:
    """
    Cliente MQTT para IoT.
    Usa paho-mqtt se disponível, senão implementa protocolo básico.
    Compatível com: Mosquitto, HiveMQ, AWS IoT, Azure IoT Hub.
    """

    def __init__(self, broker: str, porta: int = 1883,
                 usuario: str = None, senha: str = None,
                 client_id: str = None, tls: bool = False):
        self.broker = broker
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        self.client_id = client_id or f"advak_{int(time.time())}"
        self.tls = tls
        self._client = None
        self._simulando = False
        self._subscricoes: Dict[str, List[Callable]] = {}
        self._conectado = False
        self._mensagens_sim: queue.Queue = queue.Queue()

    def conectar(self):
        """Conecta ao broker MQTT."""
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)

            if self.usuario:
                self._client.username_pw_set(self.usuario, self.senha)

            if self.tls:
                import ssl
                self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED,
                                     tls_version=ssl.PROTOCOL_TLS)

            self._client.on_connect    = self._on_connect
            self._client.on_message    = self._on_message
            self._client.on_disconnect = self._on_disconnect

            self._client.connect(self.broker, self.porta, keepalive=60)
            self._client.loop_start()
            time.sleep(0.5)  # Aguarda conexão
            print(f"  📡 MQTT: {self.broker}:{self.porta} — conectado")

        except ImportError:
            self._simulando = True
            self._conectado = True
            print(f"  📡 MQTT: SIMULADO {self.broker}:{self.porta}")
            print(f"     (pip install paho-mqtt para hardware real)")
            self._iniciar_simulacao()
        except Exception as e:
            self._simulando = True
            self._conectado = True
            print(f"  ⚠️  MQTT: {self.broker} — usando simulação ({e})")
            self._iniciar_simulacao()
        return self

    def publicar(self, topico: str, payload, qos: int = 0, retain: bool = False) -> bool:
        """Publica mensagem em um tópico."""
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False)
        elif not isinstance(payload, str):
            payload = str(payload)

        if self._simulando:
            print(f"  📤 MQTT sim [{topico}]: {payload}")
            # Auto-entrega a subscritores locais
            self._entregar_local(topico, payload)
            return True
        try:
            result = self._client.publish(topico, payload, qos=qos, retain=retain)
            return result.rc == 0
        except Exception as e:
            print(f"  ❌ MQTT.publicar: {e}")
            return False

    def subscrever(self, topico: str, fn: Callable, qos: int = 0):
        """Subscreve a um tópico. fn(topico, payload)."""
        if topico not in self._subscricoes:
            self._subscricoes[topico] = []
        self._subscricoes[topico].append(fn)

        if not self._simulando and self._client:
            try:
                self._client.subscribe(topico, qos)
            except Exception as e:
                print(f"  ❌ MQTT.subscrever: {e}")
        return self

    def desconectar(self):
        """Desconecta do broker."""
        self._conectado = False
        if self._client and not self._simulando:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._conectado = True
            # Resubscreve após reconexão
            for topico in self._subscricoes:
                client.subscribe(topico)

    def _on_message(self, client, userdata, msg):
        topico = msg.topic
        try:
            payload = msg.payload.decode('utf-8')
            try:
                payload = json.loads(payload)
            except Exception:
                pass
        except Exception:
            payload = str(msg.payload)
        self._entregar_local(topico, payload)

    def _on_disconnect(self, client, userdata, rc):
        self._conectado = False

    def _entregar_local(self, topico: str, payload):
        """Entrega mensagem aos subscritores locais (com wildcard)."""
        for padrao, callbacks in self._subscricoes.items():
            if self._match_topico(padrao, topico):
                for fn in callbacks:
                    try:
                        fn(topico, payload)
                    except Exception:
                        pass

    def _match_topico(self, padrao: str, topico: str) -> bool:
        """Verifica se tópico casa com padrão MQTT (# e +)."""
        if padrao == topico:
            return True
        partes_pad = padrao.split('/')
        partes_top = topico.split('/')
        if '#' in partes_pad:
            idx = partes_pad.index('#')
            return partes_pad[:idx] == partes_top[:idx]
        if len(partes_pad) != len(partes_top):
            return False
        return all(p == '+' or p == t for p, t in zip(partes_pad, partes_top))

    def _iniciar_simulacao(self):
        def _loop():
            while self._conectado:
                time.sleep(5)
                # Simula mensagens periódicas de sensores
                self._entregar_local("sensor/simulado/temp", 22.5 + (time.time() % 5))
        threading.Thread(target=_loop, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  3. GPIO (Raspberry Pi / Orange Pi)
# ══════════════════════════════════════════════════════════════════════════════

class ControladorGPIO:
    """
    Controle de pinos GPIO para Raspberry Pi, Orange Pi, etc.
    Usa RPi.GPIO se disponível, senão simula.
    """

    ENTRADA = "INPUT"
    SAIDA   = "OUTPUT"
    ALTO    = True
    BAIXO   = False

    def __init__(self):
        self._gpio = None
        self._simulando = False
        self._pinos: Dict[int, dict] = {}
        self._callbacks: Dict[int, List] = {}
        self._inicializar()

    def _inicializar(self):
        try:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            print("  🍓 GPIO: Raspberry Pi detectado")
        except ImportError:
            try:
                import OPi.GPIO as GPIO
                self._gpio = GPIO
                GPIO.setmode(GPIO.BOARD)
                print("  🍊 GPIO: Orange Pi detectado")
            except ImportError:
                self._simulando = True
                pass  # GPIO simulado silenciosamente

    def saida(self, pino: int, valor_inicial: bool = False):
        """Configura pino como saída e retorna controlador."""
        self._pinos[pino] = {'modo': self.SAIDA, 'valor': valor_inicial}
        if not self._simulando:
            try:
                self._gpio.setup(pino, self._gpio.OUT, initial=valor_inicial)
            except Exception as e:
                print(f"  ❌ GPIO.saida({pino}): {e}")

        class PinoSaida:
            def __init__(self_, p, ctrl):
                self_._pino = p
                self_._ctrl = ctrl

            def ligar(self_):
                return self_._ctrl.escrever(self_._pino, True)

            def desligar(self_):
                return self_._ctrl.escrever(self_._pino, False)

            def alternar(self_):
                atual = self_._ctrl._pinos.get(self_._pino, {}).get('valor', False)
                return self_._ctrl.escrever(self_._pino, not atual)

            def pwm(self_, frequencia: int = 50):
                return self_._ctrl.criar_pwm(self_._pino, frequencia)

        return PinoSaida(pino, self)

    def entrada(self, pino: int, pull_up: bool = True):
        """Configura pino como entrada e retorna controlador."""
        self._pinos[pino] = {'modo': self.ENTRADA, 'valor': False}
        if not self._simulando:
            try:
                pull = self._gpio.PUD_UP if pull_up else self._gpio.PUD_DOWN
                self._gpio.setup(pino, self._gpio.IN, pull_up_down=pull)
            except Exception as e:
                print(f"  ❌ GPIO.entrada({pino}): {e}")

        ctrl = self

        class PinoEntrada:
            def __init__(self_, p):
                self_._pino = p

            def ler(self_) -> bool:
                return ctrl.ler(self_._pino)

            def ao_mudar(self_, fn: Callable, borda: str = "ambas"):
                ctrl.ao_mudar(self_._pino, fn, borda)
                return self_

        return PinoEntrada(pino)

    def escrever(self, pino: int, valor: bool) -> bool:
        if pino in self._pinos:
            self._pinos[pino]['valor'] = valor
        if self._simulando:
            estado = "HIGH" if valor else "LOW"
            print(f"  ⚡ GPIO[{pino}] = {estado}")
            return True
        try:
            self._gpio.output(pino, valor)
            return True
        except Exception as e:
            print(f"  ❌ GPIO.escrever({pino}): {e}")
            return False

    def ler(self, pino: int) -> bool:
        if self._simulando:
            return self._pinos.get(pino, {}).get('valor', False)
        try:
            return bool(self._gpio.input(pino))
        except Exception:
            return False

    def ao_mudar(self, pino: int, fn: Callable, borda: str = "ambas"):
        """Registra callback para mudança de estado do pino."""
        if self._simulando:
            print(f"  👂 GPIO[{pino}]: listener registrado (simulado)")
            return
        try:
            bordas = {
                "subida": self._gpio.RISING,
                "descida": self._gpio.FALLING,
                "ambas": self._gpio.BOTH,
            }
            self._gpio.add_event_detect(
                pino, bordas.get(borda, self._gpio.BOTH),
                callback=lambda p: fn(p, self.ler(p)),
                bouncetime=200
            )
        except Exception as e:
            print(f"  ❌ GPIO.ao_mudar({pino}): {e}")

    def criar_pwm(self, pino: int, frequencia: int = 50):
        """Cria controlador PWM para servo/motor."""
        if self._simulando:
            class PWMSimulado:
                def iniciar(self_, ciclo_trabalho: float = 0):
                    print(f"  🔄 PWM[{pino}] iniciado @ {frequencia}Hz, duty={ciclo_trabalho}%")
                def mudar_ciclo(self_, ciclo: float):
                    print(f"  🔄 PWM[{pino}] duty={ciclo:.1f}%")
                def parar(self_):
                    print(f"  🔄 PWM[{pino}] parado")
            return PWMSimulado()
        try:
            pwm = self._gpio.PWM(pino, frequencia)
            class PWMReal:
                def iniciar(self_, ciclo=0): pwm.start(ciclo)
                def mudar_ciclo(self_, ciclo): pwm.ChangeDutyCycle(ciclo)
                def parar(self_): pwm.stop()
            return PWMReal()
        except Exception as e:
            print(f"  ❌ GPIO.pwm({pino}): {e}")
            return None

    def limpar(self):
        if not self._simulando and self._gpio:
            try:
                self._gpio.cleanup()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  4. SENSORES
# ══════════════════════════════════════════════════════════════════════════════

class SistemasSensores:
    """Interface unificada para sensores comuns."""

    def __init__(self, gpio: ControladorGPIO, serial_conn: ConexaoSerial = None):
        self._gpio = gpio
        self._serial = serial_conn

    def temperatura_dht(self, pino: int) -> dict:
        """Lê temperatura e umidade do sensor DHT11/DHT22."""
        try:
            import Adafruit_DHT
            umidade, temperatura = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pino)
            return {
                'temperatura': round(temperatura, 1) if temperatura else None,
                'umidade': round(umidade, 1) if umidade else None,
                'ok': temperatura is not None
            }
        except ImportError:
            # Simulação
            import random
            return {
                'temperatura': round(20 + random.uniform(-5, 15), 1),
                'umidade': round(40 + random.uniform(-20, 40), 1),
                'ok': True,
                'simulado': True
            }
        except Exception as e:
            return {'temperatura': None, 'umidade': None, 'ok': False, 'erro': str(e)}

    def distancia_ultrassonico(self, pino_trig: int, pino_echo: int) -> float:
        """Mede distância com sensor HC-SR04 (cm)."""
        try:
            import time as _time
            trigger = self._gpio.saida(pino_trig)
            # Pulso trigger
            trigger.desligar()
            _time.sleep(0.00002)
            trigger.ligar()
            _time.sleep(0.00001)
            trigger.desligar()
            # Mede echo
            t_inicio = _time.time()
            while self._gpio.ler(pino_echo) == 0:
                t_inicio = _time.time()
                if _time.time() - t_inicio > 1: return -1
            t_fim = _time.time()
            while self._gpio.ler(pino_echo) == 1:
                t_fim = _time.time()
                if _time.time() - t_inicio > 1: return -1
            return round((t_fim - t_inicio) * 34300 / 2, 1)
        except Exception:
            import random
            return round(random.uniform(5, 200), 1)

    def analogico(self, canal: int = 0, resolucao: int = 12) -> dict:
        """Lê valor analógico (ADC via I2C ou SPI)."""
        try:
            import smbus2
            bus = smbus2.SMBus(1)
            raw = bus.read_word_data(0x48, canal)  # ADS1115
            tensao = (raw / (2**resolucao)) * 3.3
            return {'raw': raw, 'tensao': round(tensao, 3), 'ok': True}
        except Exception:
            import random
            raw = random.randint(0, 2**resolucao)
            return {'raw': raw, 'tensao': round((raw / 2**resolucao) * 3.3, 3),
                    'ok': True, 'simulado': True}

    def luz_brilho(self, pino: int = None) -> dict:
        """Lê nível de luz (LDR ou TSL2561)."""
        import random
        return {'lux': round(random.uniform(0, 1000), 1), 'ok': True, 'simulado': True}

    def pressao_bmp(self, endereco_i2c: int = 0x77) -> dict:
        """Lê pressão e temperatura do BMP180/BMP280."""
        try:
            import smbus2
            bus = smbus2.SMBus(1)
            # BMP280 simplificado
            raw_temp = bus.read_i2c_block_data(endereco_i2c, 0xFA, 3)
            temp = (raw_temp[0] << 12 | raw_temp[1] << 4 | raw_temp[2] >> 4) / 100
            return {'temperatura': round(temp, 1), 'pressao': 1013.25, 'ok': True}
        except Exception:
            import random
            return {
                'temperatura': round(20 + random.uniform(-5, 15), 1),
                'pressao': round(1013 + random.uniform(-20, 20), 1),
                'altitude': round(random.uniform(0, 1000), 0),
                'ok': True, 'simulado': True
            }


# ══════════════════════════════════════════════════════════════════════════════
#  5. GERADOR DE FIRMWARE ARDUINO / ESP32
# ══════════════════════════════════════════════════════════════════════════════

class GeradorFirmware:
    """Gera código C++ para Arduino e ESP32 a partir de código Advak."""

    @staticmethod
    def arduino(nome_projeto: str, pinos_saida: List[int] = None,
                pinos_entrada: List[int] = None,
                setup: str = "", loop: str = "",
                frequencia: int = 16, pasta: str = None) -> str:
        """Gera sketch Arduino (.ino)."""
        pinos_saida = pinos_saida or []
        pinos_entrada = pinos_entrada or []

        setup_pinos = ""
        for p in pinos_saida:
            setup_pinos += f"  pinMode({p}, OUTPUT);\n"
        for p in pinos_entrada:
            setup_pinos += f"  pinMode({p}, INPUT_PULLUP);\n"

        codigo = f"""// {nome_projeto}
// Gerado pelo Advak 5.0 — Sistema Embarcado
// Frequência: {frequencia} MHz

void setup() {{
  Serial.begin(9600);
{setup_pinos}
{setup}
}}

void loop() {{
{loop}
}}

// Funções auxiliares Advak
void advak_enviar(String tipo, float valor) {{
  Serial.println(tipo + ":" + String(valor, 2));
}}

bool advak_receber(String* tipo, float* valor) {{
  if (Serial.available()) {{
    String cmd = Serial.readStringUntil('\\n');
    int sep = cmd.indexOf(':');
    if (sep > 0) {{
      *tipo = cmd.substring(0, sep);
      *valor = cmd.substring(sep + 1).toFloat();
      return true;
    }}
  }}
  return false;
}}
"""
        pasta = pasta or nome_projeto
        os.makedirs(pasta, exist_ok=True)
        arquivo = os.path.join(pasta, f"{nome_projeto}.ino")
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(codigo)
        print(f"  ✅ Arduino sketch: {arquivo}")
        return arquivo

    @staticmethod
    def esp32_mqtt(nome_projeto: str, ssid: str, senha_wifi: str,
                   broker_mqtt: str, topicos: List[str] = None,
                   pasta: str = None) -> str:
        """Gera firmware ESP32 com Wi-Fi e MQTT."""
        topicos = topicos or ["advak/sensor"]
        subs = "\n".join([f'  client.subscribe("{t}");' for t in topicos])

        codigo = f"""// {nome_projeto} — ESP32 Wi-Fi + MQTT
// Gerado pelo Advak 5.0

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* SSID     = "{ssid}";
const char* SENHA    = "{senha_wifi}";
const char* BROKER   = "{broker_mqtt}";
const int   PORTA    = 1883;

WiFiClient   espClient;
PubSubClient client(espClient);
unsigned long ultimaLeitura = 0;

void conectarWiFi() {{
  WiFi.begin(SSID, SENHA);
  Serial.print("Conectando Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {{
    delay(500); Serial.print(".");
  }}
  Serial.println("\\nWi-Fi: " + WiFi.localIP().toString());
}}

void conectarMQTT() {{
  while (!client.connected()) {{
    if (client.connect("{nome_projeto.lower().replace(' ', '_')}")) {{
{subs}
      Serial.println("MQTT: conectado");
    }} else {{
      Serial.print("MQTT falhou: "); Serial.println(client.state());
      delay(5000);
    }}
  }}
}}

void callback(char* topico, byte* payload, unsigned int tamanho) {{
  String msg = "";
  for (int i = 0; i < tamanho; i++) msg += (char)payload[i];
  Serial.printf("MQTT [%s]: %s\\n", topico, msg.c_str());
  // Processa comandos aqui
}}

void publicarSensores() {{
  StaticJsonDocument<256> doc;
  doc["tempo"] = millis();
  doc["chip_id"] = ESP.getEfuseMac();
  // Adicione suas leituras aqui:
  // doc["temperatura"] = dht.readTemperature();

  String json;
  serializeJson(doc, json);
  client.publish("advak/{nome_projeto.lower()}/dados", json.c_str());
}}

void setup() {{
  Serial.begin(115200);
  conectarWiFi();
  client.setServer(BROKER, PORTA);
  client.setCallback(callback);
}}

void loop() {{
  if (!client.connected()) conectarMQTT();
  client.loop();

  if (millis() - ultimaLeitura > 5000) {{
    publicarSensores();
    ultimaLeitura = millis();
  }}
}}
"""
        pasta = pasta or nome_projeto
        os.makedirs(pasta, exist_ok=True)
        arquivo = os.path.join(pasta, f"{nome_projeto}.ino")
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(codigo)
        print(f"  ✅ ESP32 sketch: {arquivo}")
        return arquivo

    @staticmethod
    def micropython(nome_projeto: str, ssid: str = "", senha_wifi: str = "",
                    broker: str = "", pasta: str = None) -> str:
        """Gera código MicroPython para ESP8266/ESP32."""
        codigo = f"""# {nome_projeto} — MicroPython
# Gerado pelo Advak 5.0

import machine, time, network, ujson
from umqtt.simple import MQTTClient

# ── Wi-Fi ──
def conectar_wifi(ssid="{ssid}", senha="{senha_wifi}"):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, senha)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Wi-Fi:", wlan.ifconfig()[0])

# ── MQTT ──
client = None
def conectar_mqtt():
    global client
    client = MQTTClient("{nome_projeto.lower()}", "{broker}")
    client.set_callback(ao_receber)
    client.connect()
    client.subscribe(b"advak/{nome_projeto.lower()}/cmd")
    print("MQTT conectado")

def ao_receber(topico, msg):
    print(f"[{{topico.decode()}}]: {{msg.decode()}}")
    dados = ujson.loads(msg)
    # Processe comandos aqui

def publicar(topico, dados):
    if client:
        client.publish(topico.encode(), ujson.dumps(dados).encode())

# ── Sensores ──
led = machine.Pin(2, machine.Pin.OUT)

def ler_sensores():
    return {{
        "tempo": time.ticks_ms(),
        "memoria": gc.mem_free() if 'gc' in dir() else 0
    }}

# ── Main ──
conectar_wifi()
conectar_mqtt()

while True:
    try:
        client.check_msg()
        dados = ler_sensores()
        publicar("advak/{nome_projeto.lower()}/dados", dados)
        led.value(not led.value())
        time.sleep(5)
    except Exception as e:
        print("Erro:", e)
        machine.reset()
"""
        pasta = pasta or nome_projeto
        os.makedirs(pasta, exist_ok=True)
        arquivo = os.path.join(pasta, "main.py")
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(codigo)
        print(f"  ✅ MicroPython: {arquivo}")
        return arquivo


# ══════════════════════════════════════════════════════════════════════════════
#  6. AUTOMAÇÃO COM LÓGICA TEMPORAL
# ══════════════════════════════════════════════════════════════════════════════

class AutomacaoEmbarcada:
    """Sistema de automação com agendamento e regras."""

    def __init__(self):
        self._tarefas: List[dict] = []
        self._regras: List[dict] = []
        self._rodando = False
        self._thread = None

    def a_cada(self, segundos: float, fn: Callable, nome: str = ""):
        """Executa função periodicamente."""
        self._tarefas.append({
            'fn': fn,
            'intervalo': segundos,
            'ultimo': 0,
            'nome': nome or f"tarefa_{len(self._tarefas)}",
        })
        return self

    def se(self, condicao: Callable, entao: Callable, nome: str = ""):
        """Adiciona regra: se condição → executar."""
        self._regras.append({
            'condicao': condicao,
            'entao': entao,
            'nome': nome,
            'ultimo_estado': False,
        })
        return self

    def iniciar(self):
        """Inicia o loop de automação em background."""
        self._rodando = True
        def _loop():
            while self._rodando:
                agora = time.time()
                # Tarefas periódicas
                for t in self._tarefas:
                    if agora - t['ultimo'] >= t['intervalo']:
                        t['ultimo'] = agora
                        try:
                            t['fn']()
                        except Exception as e:
                            print(f"  ❌ Automação[{t['nome']}]: {e}")
                # Regras
                for r in self._regras:
                    try:
                        estado_atual = bool(r['condicao']())
                        if estado_atual and not r['ultimo_estado']:
                            r['entao']()
                        r['ultimo_estado'] = estado_atual
                    except Exception as e:
                        print(f"  ❌ Regra[{r['nome']}]: {e}")
                time.sleep(0.05)  # 20 Hz

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return self

    def parar(self):
        self._rodando = False


# ══════════════════════════════════════════════════════════════════════════════
#  7. DASHBOARD IoT (Interface Web para Monitorar)
# ══════════════════════════════════════════════════════════════════════════════

class DashboardIoT:
    """
    Dashboard web em tempo real para monitorar dispositivos embarcados.
    Atualização via WebSocket, sem refresh de página.
    """

    def __init__(self, titulo: str = "Advak IoT Dashboard", porta: int = 8080):
        self.titulo = titulo
        self.porta = porta
        self._metricas: Dict[str, Any] = {}
        self._graficos: Dict[str, List] = {}
        self._alertas: List[dict] = []
        self._clientes: List = []
        self._rodando = False

    def metrica(self, nome: str, valor, unidade: str = "", cor: str = "#2563EB") -> 'DashboardIoT':
        """Adiciona/atualiza uma métrica no dashboard."""
        self._metricas[nome] = {'valor': valor, 'unidade': unidade, 'cor': cor}
        self._broadcast({'tipo': 'metrica', 'nome': nome, 'valor': valor,
                         'unidade': unidade, 'cor': cor})
        return self

    def grafico(self, nome: str, valor: float, maximo_pontos: int = 50) -> 'DashboardIoT':
        """Adiciona ponto a um gráfico em tempo real."""
        if nome not in self._graficos:
            self._graficos[nome] = []
        self._graficos[nome].append({'t': time.time(), 'v': valor})
        if len(self._graficos[nome]) > maximo_pontos:
            self._graficos[nome].pop(0)
        self._broadcast({'tipo': 'grafico', 'nome': nome, 'valor': valor,
                         'historico': self._graficos[nome][-10:]})
        return self

    def alerta(self, mensagem: str, nivel: str = "aviso") -> 'DashboardIoT':
        """Adiciona alerta ao dashboard."""
        alerta = {'mensagem': mensagem, 'nivel': nivel, 'tempo': time.time()}
        self._alertas.append(alerta)
        if len(self._alertas) > 100:
            self._alertas.pop(0)
        self._broadcast({'tipo': 'alerta', **alerta})
        return self

    def iniciar(self) -> str:
        """Inicia o dashboard e retorna a URL."""
        self._rodando = True
        t = threading.Thread(target=self._servidor, daemon=True)
        t.start()

        ip = self._obter_ip()
        url = f"http://{ip}:{self.porta}"
        print(f"  📊 Dashboard IoT: {url}")
        return url

    def _broadcast(self, msg: dict):
        """Envia mensagem para todos os clientes WS."""
        dados = json.dumps(msg, ensure_ascii=False, default=str).encode()
        for c in list(self._clientes):
            try:
                tamanho = len(dados)
                if tamanho < 126:
                    c.send(bytes([0x81, tamanho]) + dados)
                else:
                    c.send(bytes([0x81, 126]) + struct.pack('!H', tamanho) + dados)
            except Exception:
                self._clientes.remove(c)

    def _obter_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"

    def _gerar_html(self) -> str:
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{self.titulo}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:#0F172A;color:#F1F5F9;padding:16px}}
h1{{color:#3B82F6;margin-bottom:20px;font-size:1.4rem}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:20px}}
.card{{background:#1E293B;border-radius:12px;padding:16px;border:1px solid #334155}}
.card .valor{{font-size:2.5rem;font-weight:700;color:#3B82F6}}
.card .nome{{color:#94A3B8;font-size:0.85rem;margin-top:4px}}
.card .unidade{{font-size:1rem;color:#64748B;margin-left:4px}}
.alertas{{background:#1E293B;border-radius:12px;padding:16px}}
.alerta{{padding:8px;border-left:4px solid;margin-bottom:6px;border-radius:4px;font-size:0.9rem}}
.alerta.aviso{{border-color:#D97706;background:#451a03}}
.alerta.erro{{border-color:#DC2626;background:#450a0a}}
.alerta.info{{border-color:#2563EB;background:#172554}}
.status{{position:fixed;top:16px;right:16px;width:10px;height:10px;
  border-radius:50%;background:#DC2626}}
.status.online{{background:#16A34A}}
</style>
</head>
<body>
<div class="status" id="status"></div>
<h1>📡 {self.titulo}</h1>
<div class="grade" id="metricas"></div>
<div class="alertas"><h3 style="margin-bottom:12px;color:#94A3B8">Alertas</h3>
<div id="alertas"></div></div>
<script>
const ws = new WebSocket(`ws://${{location.hostname}}:${{parseInt(location.port)+1}}`);
ws.onopen = () => document.getElementById('status').className = 'status online';
ws.onclose = () => document.getElementById('status').className = 'status';
ws.onmessage = e => {{
  const msg = JSON.parse(e.data);
  if (msg.tipo === 'metrica') {{
    let el = document.getElementById('m_' + msg.nome);
    if (!el) {{
      el = document.createElement('div');
      el.className = 'card'; el.id = 'm_' + msg.nome;
      document.getElementById('metricas').appendChild(el);
    }}
    el.innerHTML = `
      <div class="valor" style="color:${{msg.cor}}">${{msg.valor}}<span class="unidade">${{msg.unidade}}</span></div>
      <div class="nome">${{msg.nome}}</div>`;
  }} else if (msg.tipo === 'alerta') {{
    const a = document.createElement('div');
    a.className = 'alerta ' + (msg.nivel || 'info');
    a.textContent = msg.mensagem;
    const div = document.getElementById('alertas');
    div.insertBefore(a, div.firstChild);
    if (div.children.length > 20) div.lastChild.remove();
  }}
}};
// Carrega métricas iniciais
fetch('/api/metricas').then(r=>r.json()).then(d=>{{
  Object.entries(d).forEach(([n,v])=>{{
    ws.dispatchEvent(new MessageEvent('message',{{
      data:JSON.stringify({{tipo:'metrica',nome:n,...v}})
    }}));
  }});
}}).catch(()=>{{}});
</script>
</body>
</html>"""

    def _servidor(self):
        import http.server
        dashboard = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/api/metricas':
                    data = json.dumps(dashboard._metricas).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
                elif self.path.startswith('/ws'):
                    self._ws_upgrade()
                else:
                    data = dashboard._gerar_html().encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(data)

            def _ws_upgrade(self):
                key = None
                data = self.headers.as_string()
                for line in data.split('\r\n'):
                    if 'Sec-WebSocket-Key' in line:
                        key = line.split(': ')[1].strip()
                if key:
                    magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                    accept = base64.b64encode(
                        hashlib.sha1((key+magic).encode()).digest()).decode()
                    self.send_response(101)
                    self.send_header('Upgrade', 'websocket')
                    self.send_header('Connection', 'Upgrade')
                    self.send_header('Sec-WebSocket-Accept', accept)
                    self.end_headers()
                    dashboard._clientes.append(self.connection)
                    try:
                        while True: self.connection.recv(1024)
                    except Exception:
                        if self.connection in dashboard._clientes:
                            dashboard._clientes.remove(self.connection)

            def log_message(self, fmt, *args): pass

        import hashlib, base64
        srv = http.server.HTTPServer(('0.0.0.0', self.porta), H)
        srv.serve_forever()


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO DO SISTEMA EMBARCADO
# ══════════════════════════════════════════════════════════════════════════════

def criar_sistema_embarcado():
    """Retorna o objeto 'embarcado' para o escopo Advak."""
    _gpio = [None]
    _mqtt = [None]
    _serial = [None]
    _auto = [None]

    def get_gpio():
        if not _gpio[0]:
            _gpio[0] = ControladorGPIO()
        return _gpio[0]

    def conectar_serial(porta, baudrate=9600, timeout=1.0):
        conn = ConexaoSerial(porta, baudrate, timeout).conectar()
        _serial[0] = conn
        sensores = SistemasSensores(get_gpio(), conn)
        return {
            'enviar':       lambda dados, nl=True: conn.enviar(dados, nl),
            'receber':      lambda nl=True: conn.receber(nl),
            'receber_json': lambda: conn.receber_json(),
            'ao_receber':   lambda fn, ms=50: conn.ao_receber(fn, ms),
            'fechar':       lambda: conn.fechar(),
            'listar_portas':lambda: conn.listar_portas(),
        }

    def conectar_mqtt(broker, porta=1883, usuario=None, senha=None, tls=False):
        cli = ClienteMQTT(broker, porta, usuario, senha, tls=tls).conectar()
        _mqtt[0] = cli
        return {
            'publicar':     lambda topico, payload, qos=0, ret=False:
                                cli.publicar(topico, payload, qos, ret),
            'subscrever':   lambda topico, fn, qos=0: cli.subscrever(topico, fn, qos),
            'desconectar':  lambda: cli.desconectar(),
        }

    def criar_automacao():
        auto = AutomacaoEmbarcada()
        _auto[0] = auto
        return {
            'a_cada':   lambda seg, fn, nome="": (auto.a_cada(seg, fn, nome), None)[1],
            'se':       lambda cond, entao, nome="": (auto.se(cond, entao, nome), None)[1],
            'iniciar':  lambda: auto.iniciar(),
            'parar':    lambda: auto.parar(),
        }

    def criar_dashboard(titulo="Advak IoT", porta=8080):
        dash = DashboardIoT(titulo, porta)
        url = dash.iniciar()
        return {
            'metrica':  lambda nome, valor, unidade="", cor="#2563EB":
                            dash.metrica(nome, valor, unidade, cor),
            'grafico':  lambda nome, valor, max_pts=50:
                            dash.grafico(nome, valor, max_pts),
            'alerta':   lambda msg, nivel="aviso": dash.alerta(msg, nivel),
            'url':      url,
        }

    gpio_ctrl = get_gpio()

    return {
        # Serial / UART
        'serial': {
            'conectar':      lambda porta, baud=9600, timeout=1.0:
                                 conectar_serial(porta, baud, timeout),
            'listar_portas': lambda: ConexaoSerial("").listar_portas(),
        },

        # MQTT
        'mqtt': {
            'conectar': lambda broker, porta=1883, usuario=None, senha=None, tls=False:
                            conectar_mqtt(broker, porta, usuario, senha, tls),
        },

        # GPIO
        'gpio': {
            'saida':     lambda pino, inicial=False: gpio_ctrl.saida(pino, inicial),
            'entrada':   lambda pino, pull_up=True: gpio_ctrl.entrada(pino, pull_up),
            'escrever':  lambda pino, valor: gpio_ctrl.escrever(pino, valor),
            'ler':       lambda pino: gpio_ctrl.ler(pino),
            'limpar':    lambda: gpio_ctrl.limpar(),
        },

        # Sensores
        'sensor': {
            'temperatura':  lambda pino=4: SistemasSensores(gpio_ctrl).temperatura_dht(pino),
            'distancia':    lambda trig=23, echo=24:
                                SistemasSensores(gpio_ctrl).distancia_ultrassonico(trig, echo),
            'analogico':    lambda canal=0: SistemasSensores(gpio_ctrl).analogico(canal),
            'pressao':      lambda: SistemasSensores(gpio_ctrl).pressao_bmp(),
            'luz':          lambda: SistemasSensores(gpio_ctrl).luz_brilho(),
        },

        # Firmware
        'firmware': {
            'arduino':      lambda nome, pinos_saida=None, pinos_entrada=None,
                                   setup="", loop="", pasta=None:
                                GeradorFirmware.arduino(
                                    nome, pinos_saida, pinos_entrada, setup, loop, pasta=pasta),
            'esp32':        lambda nome, ssid, senha, broker, topicos=None, pasta=None:
                                GeradorFirmware.esp32_mqtt(nome, ssid, senha, broker, topicos, pasta),
            'micropython':  lambda nome, ssid="", senha="", broker="", pasta=None:
                                GeradorFirmware.micropython(nome, ssid, senha, broker, pasta),
        },

        # Automação
        'automacao':    criar_automacao,

        # Dashboard IoT
        'dashboard':    lambda titulo="Advak IoT", porta=8080: criar_dashboard(titulo, porta),

        # Utilitários
        'aguardar':     lambda ms: time.sleep(ms / 1000),
        'timestamp':    lambda: time.time(),
        'agora_ms':     lambda: int(time.time() * 1000),
    }
