// AdvakSensor — ESP32 Wi-Fi + MQTT
// Gerado pelo Advak 5.0

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* SSID     = "MinhaRede";
const char* SENHA    = "senha123";
const char* BROKER   = "broker.hivemq.com";
const int   PORTA    = 1883;

WiFiClient   espClient;
PubSubClient client(espClient);
unsigned long ultimaLeitura = 0;

void conectarWiFi() {
  WiFi.begin(SSID, SENHA);
  Serial.print("Conectando Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWi-Fi: " + WiFi.localIP().toString());
}

void conectarMQTT() {
  while (!client.connected()) {
    if (client.connect("advaksensor")) {
  client.subscribe("advak/sensor/temp");
  client.subscribe("advak/sensor/umidade");
      Serial.println("MQTT: conectado");
    } else {
      Serial.print("MQTT falhou: "); Serial.println(client.state());
      delay(5000);
    }
  }
}

void callback(char* topico, byte* payload, unsigned int tamanho) {
  String msg = "";
  for (int i = 0; i < tamanho; i++) msg += (char)payload[i];
  Serial.printf("MQTT [%s]: %s\n", topico, msg.c_str());
  // Processa comandos aqui
}

void publicarSensores() {
  StaticJsonDocument<256> doc;
  doc["tempo"] = millis();
  doc["chip_id"] = ESP.getEfuseMac();
  // Adicione suas leituras aqui:
  // doc["temperatura"] = dht.readTemperature();

  String json;
  serializeJson(doc, json);
  client.publish("advak/advaksensor/dados", json.c_str());
}

void setup() {
  Serial.begin(115200);
  conectarWiFi();
  client.setServer(BROKER, PORTA);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) conectarMQTT();
  client.loop();

  if (millis() - ultimaLeitura > 5000) {
    publicarSensores();
    ultimaLeitura = millis();
  }
}
