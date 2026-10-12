# AdvakMicro — MicroPython
# Gerado pelo Advak 5.0

import machine, time, network, ujson
from umqtt.simple import MQTTClient

# ── Wi-Fi ──
def conectar_wifi(ssid="MinhaRede", senha="senha123"):
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
    client = MQTTClient("advakmicro", "broker.hivemq.com")
    client.set_callback(ao_receber)
    client.connect()
    client.subscribe(b"advak/advakmicro/cmd")
    print("MQTT conectado")

def ao_receber(topico, msg):
    print(f"[{topico.decode()}]: {msg.decode()}")
    dados = ujson.loads(msg)
    # Processe comandos aqui

def publicar(topico, dados):
    if client:
        client.publish(topico.encode(), ujson.dumps(dados).encode())

# ── Sensores ──
led = machine.Pin(2, machine.Pin.OUT)

def ler_sensores():
    return {
        "tempo": time.ticks_ms(),
        "memoria": gc.mem_free() if 'gc' in dir() else 0
    }

# ── Main ──
conectar_wifi()
conectar_mqtt()

while True:
    try:
        client.check_msg()
        dados = ler_sensores()
        publicar("advak/advakmicro/dados", dados)
        led.value(not led.value())
        time.sleep(5)
    except Exception as e:
        print("Erro:", e)
        machine.reset()
