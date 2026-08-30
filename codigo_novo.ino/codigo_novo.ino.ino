const int PIN_SENSOR_A = 5; // GPIO 5
const int PIN_SENSOR_B = 7; // GPIO 7

volatile int primeiro_sensor_tocado = 0; // 0=nenhum, 1=A esperando B, 2=B esperando A
volatile unsigned long tempo_inicio_espera = 0;

volatile unsigned long ultimo_tempo_A = 0;
volatile unsigned long ultimo_tempo_B = 0;

volatile unsigned long ultimo_tempo_meia_volta = 0;
volatile unsigned long delta_tempo_meia_volta = 0;
volatile bool nova_meia_volta = false;
volatile int direcao_final = 0;

volatile unsigned long total_meias_voltas = 0;

// Debounce mais realista: bounce mecânico de sensor hall é tipicamente
// < 20-30ms. 150ms estava provavelmente engolindo pulsos reais em
// cadências mais rápidas. Ajuste se precisar.
const unsigned long TEMPO_DEBOUNCE = 40;

// Se ficarmos "esperando o complemento" por mais tempo que isso,
// assumimos que o outro pulso foi perdido e resincronizamos --
// em vez de deixar o estado travado esperando para sempre (ou,
// pior, casar com um pulso de um ciclo seguinte e errar a direção).
// Ajuste conforme a cadência mais lenta esperada (aqui: 400ms
// cobre até ~37 RPM com 2 imãs; diminua se pedalar sempre rápido).
const unsigned long TIMEOUT_RESYNC = 400;

const unsigned long TEMPO_PARADO = 2500;

// =====================================================
// SENSOR A
// =====================================================
void IRAM_ATTR detecta_A() {
  unsigned long agora = millis();
  if (agora - ultimo_tempo_A <= TEMPO_DEBOUNCE) return;
  ultimo_tempo_A = agora;

  // Resincronia: se estávamos esperando um complemento há tempo
  // demais, descarta a espera antiga (pulso perdido) e trata este
  // evento como um novo início, em vez de casar errado.
  if (primeiro_sensor_tocado != 0 &&
      (agora - tempo_inicio_espera) > TIMEOUT_RESYNC) {
    primeiro_sensor_tocado = 0;
  }

  if (primeiro_sensor_tocado == 0) {
    primeiro_sensor_tocado = 1; // A tocou primeiro, espera B
    tempo_inicio_espera = agora;
  }
  else if (primeiro_sensor_tocado == 2) {
    // B->A dentro da janela válida = TRAS
    if (ultimo_tempo_meia_volta > 0) {
      delta_tempo_meia_volta = agora - ultimo_tempo_meia_volta;
    }
    ultimo_tempo_meia_volta = agora;
    direcao_final = 2;
    nova_meia_volta = true;
    total_meias_voltas++;
    primeiro_sensor_tocado = 0;
  }
  // se primeiro_sensor_tocado == 1 (A repetiu antes de B chegar,
  // ainda dentro da janela): ignora, continua esperando B.
}

// =====================================================
// SENSOR B
// =====================================================
void IRAM_ATTR detecta_B() {
  unsigned long agora = millis();
  if (agora - ultimo_tempo_B <= TEMPO_DEBOUNCE) return;
  ultimo_tempo_B = agora;

  if (primeiro_sensor_tocado != 0 &&
      (agora - tempo_inicio_espera) > TIMEOUT_RESYNC) {
    primeiro_sensor_tocado = 0;
  }

  if (primeiro_sensor_tocado == 0) {
    primeiro_sensor_tocado = 2; // B tocou primeiro, espera A
    tempo_inicio_espera = agora;
  }
  else if (primeiro_sensor_tocado == 1) {
    // A->B dentro da janela válida = FRENTE
    if (ultimo_tempo_meia_volta > 0) {
      delta_tempo_meia_volta = agora - ultimo_tempo_meia_volta;
    }
    ultimo_tempo_meia_volta = agora;
    direcao_final = 1;
    nova_meia_volta = true;
    total_meias_voltas++;
    primeiro_sensor_tocado = 0;
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  pinMode(PIN_SENSOR_A, INPUT_PULLUP);
  pinMode(PIN_SENSOR_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_A), detecta_A, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_B), detecta_B, FALLING);

  Serial.println("ESP32-C3: deteccao por ordem com resincronia");
}

void loop() {
  static float rpm = 0;
  unsigned long agora = millis();

  if (nova_meia_volta) {
    noInterrupts();
    nova_meia_volta = false;
    unsigned long delta = delta_tempo_meia_volta;
    int direcao = direcao_final;
    interrupts();

    if (delta > 0) {
      rpm = 30000.0 / delta;
      if (rpm > 150) rpm = 150;
    }

    Serial.print("RPM:");
    Serial.print(rpm, 1);
    Serial.print(",");
    if (direcao == 1) Serial.println("FRENTE");
    else if (direcao == 2) Serial.println("TRAS");
  }

  if (ultimo_tempo_meia_volta > 0 &&
      agora - ultimo_tempo_meia_volta > TEMPO_PARADO) {

    if (rpm > 0) {
      rpm = 0;

      noInterrupts();
      primeiro_sensor_tocado = 0;
      ultimo_tempo_meia_volta = 0;
      direcao_final = 0;
      interrupts();

      Serial.println("RPM:0.0,PARADO");
    }
  }

  delay(10);
}
