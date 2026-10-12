// SensorTemperatura
// Gerado pelo Advak 5.0 — Sistema Embarcado
// Frequência: 16 MHz

void setup() {
  Serial.begin(9600);
  pinMode(13, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(2, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);

  Serial.println(\"Advak IoT Iniciado!\");
}

void loop() {
  float temp = analogRead(A0) * 0.48828;\n  advak_enviar(\"TEMP\", temp);\n  delay(2000);
}

// Funções auxiliares Advak
void advak_enviar(String tipo, float valor) {
  Serial.println(tipo + ":" + String(valor, 2));
}

bool advak_receber(String* tipo, float* valor) {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    int sep = cmd.indexOf(':');
    if (sep > 0) {
      *tipo = cmd.substring(0, sep);
      *valor = cmd.substring(sep + 1).toFloat();
      return true;
    }
  }
  return false;
}
