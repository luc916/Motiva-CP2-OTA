#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <ArduinoJson.h>
#include <esp_system.h>

const char* VERSAO = "2.0";
// Configure com a URL RAW do version.json do seu repositorio publico.
const char* MANIFESTO_URL =
  "https://raw.githubusercontent.com/luc916/Motiva-CP2-OTA/main/version.json";
const char* REDE = "Wokwi-GUEST";
const int LED_R = 25, LED_G = 26, LED_B = 27;
const int QUANTIDADE = 5;
const uint32_t INTERVALO_LEITURA = 2000;
const uint32_t INTERVALO_SESSAO = 48000;
int leituras[QUANTIDADE];
int indice = 0;
int sessoesConcluidas = 0;
uint32_t inicioSessao;
uint32_t primeiraSessao;
bool alerta = false;
// A rede roda em uma tarefa para nao atrasar as leituras do loop.
volatile bool otaEmAndamento = false;
int ultimaSessaoConsultada = 0;

void definirLed(bool vermelho, bool verde, bool azul) {
  digitalWrite(LED_R, vermelho);
  digitalWrite(LED_G, verde);
  digitalWrite(LED_B, azul);
}

float calcularMedia(const int valores[]) {
  int soma = 0;
  for (int i = 0; i < QUANTIDADE; i++) soma += valores[i];
  return soma / float(QUANTIDADE);
}

void ordenarCopia(const int original[], int ordenado[]) {
  for (int i = 0; i < QUANTIDADE; i++) ordenado[i] = original[i];
  for (int i = 0; i < QUANTIDADE - 1; i++) {
    for (int j = 0; j < QUANTIDADE - 1 - i; j++) {
      if (ordenado[j] > ordenado[j + 1]) {
        int aux = ordenado[j];
        ordenado[j] = ordenado[j + 1];
        ordenado[j + 1] = aux;
      }
    }
  }
}

bool aplicarHisterese(int mediana, bool estadoAnterior) {
  if (mediana >= 16) return true;
  if (mediana <= 14) return false;
  return estadoAnterior;
}

void mostrarVetor(const char* titulo, const int valores[]) {
  Serial.print(titulo);
  for (int i = 0; i < QUANTIDADE; i++) Serial.printf("%d ", valores[i]);
  Serial.println();
}

void concluirSessao() {
  Serial.printf("Media da sessao: %.1f cm\n", calcularMedia(leituras));
  int ordenado[QUANTIDADE];
  ordenarCopia(leituras, ordenado);
  mostrarVetor("Ordem original: ", leituras);
  mostrarVetor("Ordem crescente: ", ordenado);
  int mediana = ordenado[2];
  alerta = aplicarHisterese(mediana, alerta);
  definirLed(alerta, !alerta, false);
  Serial.printf("Mediana: %d cm | Estado: %s\n", mediana,
                alerta ? "ALERTA" : "NORMAL");
  sessoesConcluidas++;
  Serial.println("Sessao concluida. Proximo inicio: 48 s apos o anterior.");
}

void anunciarSessao() {
  Serial.printf("\nSessao %d | inicio relativo: %lu ms\n",
                sessoesConcluidas + 1,
                (unsigned long)(inicioSessao - primeiraSessao));
}

void atualizarLeituras() {
  uint32_t agora = millis();
  if (indice == QUANTIDADE &&
      uint32_t(agora - inicioSessao) >= INTERVALO_SESSAO) {
    inicioSessao += INTERVALO_SESSAO;
    indice = 0;
    anunciarSessao();
  }
  if (indice < QUANTIDADE &&
      uint32_t(agora - inicioSessao) >= indice * INTERVALO_LEITURA) {
    leituras[indice] = random(10, 21); // 10 a 20, incluindo os extremos.
    Serial.printf("Leitura %d: %d cm | t=%lu ms\n", indice + 1,
                  leituras[indice], (unsigned long)(agora - primeiraSessao));
    indice++;
    if (indice == QUANTIDADE) concluirSessao();
  }
}

bool versaoMaisNova(const char* remota, const char* local) {
  int rMaior, rMenor, lMaior, lMenor;
  char sobra;
  // O projeto usa o formato numerico MAIOR.MENOR.
  if (sscanf(remota, "%d.%d%c", &rMaior, &rMenor, &sobra) != 2 ||
      sscanf(local, "%d.%d%c", &lMaior, &lMenor, &sobra) != 2 ||
      rMaior < 0 || rMenor < 0 || lMaior < 0 || lMenor < 0) {
    Serial.println("Erro: formato de versao invalido.");
    return false;
  }
  return rMaior > lMaior || (rMaior == lMaior && rMenor > lMenor);
}

bool conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  Serial.println("Conectando a rede Wokwi-GUEST...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(REDE, "", 6);
  uint32_t inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
    delay(100); // Somente a tarefa de rede espera; o loop segue medindo.
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Erro: sem conexao Wi-Fi. Tentaremos na proxima sessao.");
    return false;
  }
  Serial.print("Wi-Fi conectado. IP: ");
  Serial.println(WiFi.localIP());
  return true;
}

void consultarAtualizacao() {
  if (String(MANIFESTO_URL).indexOf("SEU_USUARIO") >= 0) {
    Serial.println("OTA pendente: configure MANIFESTO_URL antes de publicar.");
    return;
  }
  if (!conectarWiFi()) return;
  WiFiClientSecure cliente;
  // Simplificacao para este laboratorio, sem dados privados.
  // Em producao, validar o certificado do servidor com setCACert().
  cliente.setInsecure();
  HTTPClient http;
  http.setConnectTimeout(10000);
  http.setTimeout(15000);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  Serial.print("Consultando manifesto: ");
  Serial.println(MANIFESTO_URL);
  if (!http.begin(cliente, MANIFESTO_URL)) {
    Serial.println("Erro: nao foi possivel iniciar a consulta do manifesto.");
    return;
  }
  int codigo = http.GET();
  if (codigo != HTTP_CODE_OK) {
    Serial.printf("Erro: manifesto inacessivel. HTTP/erro: %d\n", codigo);
    http.end();
    return;
  }
  JsonDocument documento;
  DeserializationError erro = deserializeJson(documento, http.getString());
  http.end();
  if (erro || !documento["version"].is<const char*>() ||
      !documento["url"].is<const char*>()) {
    Serial.println("Erro: manifesto invalido (version e url obrigatorios).");
    return;
  }
  String versaoRemota = documento["version"].as<String>();
  String url = documento["url"].as<String>();
  Serial.printf("Versao instalada: %s | disponivel: %s\n",
                VERSAO, versaoRemota.c_str());
  if (!versaoMaisNova(versaoRemota.c_str(), VERSAO)) {
    Serial.println("Sem atualizacao: versao atual ou remota nao superior/valida.");
    return;
  }
  if (!url.startsWith("https://")) {
    Serial.println("Erro: use uma URL HTTPS direta para o firmware.");
    return;
  }
  Serial.print("Atualizacao disponivel. Baixando: ");
  Serial.println(url);
  WiFiClientSecure download;
  download.setInsecure();
  HTTPUpdate atualizador;
  atualizador.rebootOnUpdate(false);
  atualizador.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  t_httpUpdate_return resultado = atualizador.update(download, url);
  if (resultado == HTTP_UPDATE_OK) {
    Serial.println("OTA gravada com sucesso. Reiniciando o ESP32...");
    Serial.flush();
    ESP.restart();
  } else if (resultado == HTTP_UPDATE_NO_UPDATES) {
    Serial.println("Servidor nao enviou um novo firmware.");
  } else {
    Serial.printf("Erro no download/gravação OTA: %d - %s\n",
                  atualizador.getLastError(),
                  atualizador.getLastErrorString().c_str());
    Serial.println("Firmware atual mantido. Nova tentativa na proxima sessao.");
  }
}

void tarefaOTA(void*) {
  consultarAtualizacao();
  otaEmAndamento = false;
  vTaskDelete(nullptr);
}

void verificarOTA() {
  // A primeira tentativa so ocorre depois de tres sessoes completas.
  if (sessoesConcluidas >= 3 && !otaEmAndamento &&
      ultimaSessaoConsultada != sessoesConcluidas) {
    ultimaSessaoConsultada = sessoesConcluidas;
    otaEmAndamento = true;
    if (xTaskCreate(tarefaOTA, "OTA", 12288, nullptr, 1, nullptr) != pdPASS) {
      otaEmAndamento = false;
      Serial.println("Erro: nao foi possivel iniciar a tarefa OTA.");
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  definirLed(false, true, false);
  randomSeed(esp_random());
  Serial.println("========================================");
  Serial.printf("MONITORAMENTO DE VEGETACAO - FW %s\n", VERSAO);
  Serial.println("========================================");
  primeiraSessao = inicioSessao = millis();
  anunciarSessao();
}

void loop() {
  atualizarLeituras();
  verificarOTA();
  delay(1); // Cede tempo ao sistema, sem uma espera longa entre leituras.
}
