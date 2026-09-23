# Executar e entregar

## Links

- Principal, com leituras aleatórias e OTA: https://wokwi.com/projects/475988461020262401
- Histerese com valores fixos: https://wokwi.com/projects/475988911733956609
- Diagnóstico de erros: https://wokwi.com/projects/475989558168554497
- Repositório: https://github.com/luc916/Motiva-CP2-OTA

## Repetir a demonstração principal

1. Abra o projeto principal e inicie a simulação. O LED começa azul e o Serial identifica FW 1.0.
2. Aguarde três sessões completas. Elas começam em 0, 48000 e 96000 ms; a quinta leitura da terceira acontece em 104000 ms.
3. O ESP32 conecta à Wokwi-GUEST, consulta o manifesto e baixa firmware_v2.bin. A transferência pode demorar alguns minutos de relógio real no gateway público.
4. Aguarde a mensagem de sucesso e o reinício automático. Sem trocar o código manualmente, o Serial passa a mostrar FW 2.0, média, vetor original, vetor ordenado e mediana.
5. Confira LED vermelho para ALERTA e verde para NORMAL. O projeto de histerese permite reproduzir também o estado mantido em 15 cm.

O código principal mantém sessões de 48 segundos e leituras pseudoaleatórias. O diagnóstico de histerese usa valores fixos e sessões de 12 segundos apenas para acelerar os testes dos limites. O diagnóstico de erros executa os cenários imediatamente; ele não comprova a espera de três sessões, que foi verificada no projeto principal.

## Resultado da execução

A OTA foi executada com sucesso, inclusive após corrigir a reconexão Wi-Fi. A correção encerra uma tentativa anterior antes de começar outra. Foram verificados os cinco cenários de erro: sem Wi-Fi, manifesto 404, versão igual, arquivo ausente (-102) e arquivo inválido (-106). O firmware permaneceu executando após as falhas.

Os logs originais estão em evidencias/serial-wokwi.txt, evidencias/serial-histerese.txt e evidencias/serial-erros.txt. As capturas estão em evidencias/capturas/. O script tests/verificar_logs.py confere os cálculos e as transições nos registros reais.

Consultas posteriores ao reboot também registraram falhas de rede, tratadas pelo programa sem parar a coleta. O gateway público e a fila de compilação podem variar. Não é necessário comprar um plano para executar esta entrega.

## Entrega

1. Revise output/pdf/Relatorio-Motiva-CP2.pdf, especialmente integrantes e links.
2. Envie somente o PDF no Teams, conforme o enunciado. Os códigos, o manifesto, o binário e os logs estão no repositório; o PDF também contém anexos internos.
3. Mantenha os projetos e o repositório públicos por pelo menos 10 dias após a entrega.

O enunciado informa 21/09/2026 como prazo. A execução foi realizada em 23/09/2026; confirme com o professor a situação da entrega.

## Se precisar alterar o endereço do repositório

Execute python3 configurar_repositorio.py usuario repositorio branch, recompile com bash compilar.sh e atualize o projeto Wokwi. Depois de alterar o código ou binário, repita os testes; os logs desta entrega documentam os arquivos identificados pelos hashes atuais.

Para regenerar o relatório: instale reportlab e pypdf, atualize dados-entrega.json com os dados efetivamente verificados e execute python3 gerar_relatorio.py.
