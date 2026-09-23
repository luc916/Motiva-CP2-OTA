# Motiva - CP2: atualização remota de firmware

ESP32 no Wokwi, sem sensor físico. O programa simula a altura da vegetação e recebe uma nova versão pela internet.

## Integrantes

| Nome | RM |
| --- | --- |
| Lucas Kenzo Nishiwaki | 561325 |
| Felipe Hui Hattori | 565169 |
| Kauã Peres de Macedo | 563977 |
| Rafael Vaz de Lima | 566429 |
| André Eduardo Martins | 563297 |
| Kauany Ribeiro de Moura | 564576 |

## Situação da entrega

Os arquivos foram preparados para publicação posterior pelo grupo. O endereço configurado é `https://github.com/luc916/Motiva-CP2-OTA`, branch `main`. Esse é o endereço previsto, não uma confirmação de que o repositório já foi publicado. O link público do Wokwi ainda precisa ser criado.

O PDF inclui os códigos completos, o manifesto, a explicação e o resultado dos testes locais. O binário 2.0 também está anexado dentro do PDF. A comprovação da atualização pela internet deve ser acrescentada depois da demonstração. Não entregar a versão com links pendentes.

## Arquitetura

ESP32 executando FW 1.0 -> Wi-Fi Wokwi-GUEST -> version.json público -> firmware_v2.bin -> gravação na partição OTA inativa -> reinício -> FW 2.0.

O circuito usa ESP32 DevKit v1 e LED RGB de cátodo comum. Vermelho no GPIO 25, verde no GPIO 26 e azul no GPIO 27, cada canal com resistor de 220 ohms; terminal comum no GND. Não há sensor.

- **1.0:** cinco leituras inteiras de 10 a 20 cm, vetor, média e LED azul.
- **2.0:** mantém as leituras e a média, ordena uma cópia com bubble sort, calcula a mediana pelo índice 2 e aplica histerese. LED verde em NORMAL e vermelho em ALERTA.
- **Histerese:** mediana >= 16 ativa alerta; mediana <= 14 desativa; entre os limites mantém o estado anterior. O estado inicial é NORMAL. Com valores inteiros, o valor intermediário possível é 15.
- **Temporização:** leituras nos instantes 0, 2, 4, 6 e 8 segundos; sessões começam em 0, 48, 96, 144 segundos. O próximo início é calculado a partir do início anterior. `millis()` mede o tempo simulado; o laço tem resolução aproximada de 1 ms, não garantia de tempo real rígido.
- **OTA:** primeira consulta após a terceira sessão completa, aproximadamente no segundo 104. Uma tarefa FreeRTOS cuida da rede enquanto o `loop()` continua medindo. Em falha, há outra tentativa depois da próxima sessão completa. Reiniciar após uma atualização bem-sucedida começa uma nova contagem.

## Arquivos

- `firmware_v1/firmware_v1.ino`: código completo 1.0.
- `firmware_v2/firmware_v2.ino`: código completo 2.0.
- `firmware_v1.bin` e `firmware_v2.bin`: aplicações compiladas para ESP32 clássico.
- `version.json`: versão e URL direta do firmware 2.0.
- `wokwi/`: sketch inicial 1.0, circuito, bibliotecas e tabela de partições.
- `output/pdf/Relatorio-Motiva-CP2.pdf`: relatório com fontes completas e anexos.
- `evidencias/`: registros de compilação, testes locais e hashes.
- `tests/testar.py`: testes locais das funções extraídas dos próprios códigos.
- `PUBLICAR-E-TESTAR.md`: passos para publicar, demonstrar e concluir o relatório.

## Compilação reproduzível

Use Arduino CLI, core `esp32:esp32@2.0.17`, placa `esp32:esp32:esp32` e ArduinoJson `7.4.2`. O arquivo `partitions.csv` de cada sketch reserva duas partições de aplicação de 0x140000 bytes para OTA.

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@2.0.17 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli lib install ArduinoJson@7.4.2
bash compilar.sh
python3 tests/testar.py
```

O binário para OTA é `firmware_v2.bin`, somente a aplicação. Não use bootloader, tabela de partições ou um binário mesclado como arquivo de atualização.

## Bibliotecas

`WiFi` conecta à rede, `WiFiClientSecure` transporta HTTPS, `HTTPClient` consulta o manifesto, `ArduinoJson` lê seus campos e `HTTPUpdate` baixa e grava a aplicação usando o mecanismo OTA do ESP32. Apenas ArduinoJson é instalada separadamente. A tarefa FreeRTOS já faz parte do core ESP32.

Neste laboratório, `setInsecure()` simplifica o uso do HTTPS: há criptografia, mas o certificado do servidor não é autenticado. Uma implantação real deve validar o certificado e a autenticidade do firmware.

## Conceitos para explicar

A média soma os valores e divide pela quantidade. A mediana é o valor central do vetor ordenado e sofre menos influência de uma leitura isolada muito alta ou baixa. Histerese usa dois limites e conserva o estado entre eles, evitando ficar ligando e desligando o alerta perto de um único limite. OTA permite corrigir e melhorar equipamentos em campo sem ir até cada dispositivo.

## Referências

- Enunciado MORGS - CP2, professor Marcelo Fernando Morgantini.
- [ESP32 no Wokwi](https://docs.wokwi.com/guides/esp32).
- [Rede virtual do Wokwi](https://docs.wokwi.com/guides/esp32-wifi).
- [Partições no Arduino ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/partition_table.html).
- [Atualização OTA no ESP32](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/ota.html).
