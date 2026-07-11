const int PIN_SENSOR_A = 5; // GPIO 5
const int PIN_SENSOR_B = 7; // GPIO 7

// Registradores de ordem
volatile int primeiro_sensor_tocado = 0; // 1 para A, 2 para B
volatile unsigned long ultimo_tempo_A = 0;
volatile unsigned long ultimo_tempo_B = 0;

volatile unsigned long ultimo_tempo_volta = 0;
volatile unsigned long delta_tempo = 0;
volatile bool nova_meia_volta = false;
volatile int direcao_final = 0; // 1 = FRENTE, 2 = TRAS

const unsigned long TEMPO_DEBOUNCE = 200; // Evita repetições do mesmo ímã

// ====== INTERRUPÇÃO SENSOR A ======
void IRAM_ATTR detecta_A() {
  unsigned long tempo_atual = millis();
  if (tempo_atual - ultimo_tempo_A > TEMPO_DEBOUNCE) {
    ultimo_tempo_A = tempo_atual;
    
    // Se ninguém foi tocado ainda nesta passada, o A foi o primeiro! (FRENTE)
    if (primeiro_sensor_tocado == 0) {
      primeiro_sensor_tocado = 1; 
    } 
    // Se o B já tinha sido tocado, o A fecha a passada vindo de trás
    else if (primeiro_sensor_tocado == 2) {
      delta_tempo = tempo_atual - ultimo_tempo_volta;
      ultimo_tempo_volta = tempo_atual;
      direcao_final = 2; // TRÁS
      nova_meia_volta = true;
      primeiro_sensor_tocado = 0; // Reseta para a próxima passada
    }
  }
}

// ====== INTERRUPÇÃO SENSOR B ======
void IRAM_ATTR detecta_B() {
  unsigned long tempo_atual = millis();
  if (tempo_atual - ultimo_tempo_B > TEMPO_DEBOUNCE) {
    ultimo_tempo_B = tempo_atual;
    
    // Se ninguém foi tocado ainda nesta passada, o B foi o primeiro! (TRÁS)
    if (primeiro_sensor_tocado == 0) {
      primeiro_sensor_tocado = 2;
    } 
    // Se o A já tinha sido tocado, o B fecha a passada vindo de frente
    else if (primeiro_sensor_tocado == 1) {
      delta_tempo = tempo_atual - ultimo_tempo_volta;
      ultimo_tempo_volta = tempo_atual;
      direcao_final = 1; // FRENTE
      nova_meia_volta = true;
      primeiro_sensor_tocado = 0; // Reseta para a próxima passada
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  pinMode(PIN_SENSOR_A, INPUT_PULLUP);
  pinMode(PIN_SENSOR_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_A), detecta_A, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_B), detecta_B, FALLING);

  Serial.println("ESP32-C3: Sistema de Ordem Ativo nos GPIOs 5 e 7!");
}

void loop() {
  static float rpm = 0;
  unsigned long tempo_atual = millis();

  if (nova_meia_volta) {
    nova_meia_volta = false;
    
    rpm = (60000.0 / delta_tempo) / 2.0;
    if (rpm > 150) rpm = 150;

    Serial.print("RPM:");
    Serial.print(rpm, 1);
    Serial.print(",");
    if (direcao_final == 1) Serial.println("FRENTE");
    else if (direcao_final == 2) Serial.println("TRAS");
  }

  // SEGURANÇA: Se o pedal parar por 2.5 segundos, zera
  if (tempo_atual - ultimo_tempo_volta > 2500) {
    if (rpm > 0) {
      rpm = 0;
      primeiro_sensor_tocado = 0;
      Serial.println("RPM:0.0,PARADO");
    }
  }

  delay(50);
}