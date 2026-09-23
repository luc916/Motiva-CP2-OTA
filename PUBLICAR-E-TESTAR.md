# Publicar e finalizar

## 1. GitHub

1. Crie um repositório **público** chamado `Motiva-CP2-OTA` na conta `luc916`, com branch `main`.
2. Envie os arquivos desta pasta, mantendo `version.json` e `firmware_v2.bin` na **raiz** do repositório. Não envie apenas o ZIP ou uma pasta externa contendo tudo.
3. Abra sem login o manifesto: https://raw.githubusercontent.com/luc916/Motiva-CP2-OTA/main/version.json
4. Abra a URL indicada no campo `url`: ela deve baixar o binário, sem página de login. O arquivo deve ter o mesmo SHA-256 registrado em `evidencias/SHA256SUMS.txt`.

Se preferir outro usuário, nome ou branch, rode `python3 configurar_repositorio.py usuario repositorio branch`, recompile com `bash compilar.sh` e publique os arquivos atualizados. Não basta editar apenas o manifesto: o firmware também precisa consultar o endereço correto.

## 2. Wokwi

1. Crie um projeto Arduino ESP32 DevKit v1 em https://wokwi.com/projects/new/esp32.
2. Substitua `sketch.ino` e `diagram.json` pelos arquivos de mesmo nome da pasta `wokwi`.
3. Adicione `libraries.txt` e `partitions.csv`, também da pasta `wokwi`. A tabela deve conter `otadata`, `app0` e `app1`; sem duas partições, a OTA não funciona.
4. Salve o projeto e copie seu link público. Abra esse link sem login para verificar o acesso.
5. Inicie a simulação. O Serial Monitor usa 115200 baud. O primeiro programa deve ser o **1.0**; iniciar diretamente o 2.0 não comprova OTA.
6. Aguarde as três sessões completas. Os inícios esperados são 0, 48000 e 96000 ms em relação à primeira sessão. A quinta leitura da terceira sessão acontece perto de 104000 ms.
7. Confirme a consulta do manifesto, a versão remota 2.0, o download, a mensagem de gravação bem-sucedida e o reinício automático.
8. Após o reinício, confirme `FW 2.0`, média, ordem original, ordem crescente, mediana e LED verde/vermelho. Não troque o código manualmente entre as versões durante a prova de OTA.

O relógio do Wokwi pode correr mais devagar que o tempo da parede. Compare os milissegundos impressos pelo ESP32. Pare e inicie novamente a simulação para repetir a demonstração a partir do sketch 1.0.

## 3. Testes e evidências

Salve a saída real do Serial Monitor em `evidencias/serial-wokwi.txt` e capturas que mostrem as cores e o monitor. Os logs locais entregues não substituem essas evidências.

| Teste do enunciado | Verificação na simulação |
| --- | --- |
| 1 | FW 1.0, cinco leituras entre 10 e 20, média conferida e LED azul. |
| 2 | Inícios em 0/48000/96000 ms, não em 0/56000/112000. |
| 3 | Só consultar a versão 2.0 depois da leitura 5 da sessão 3. |
| 4 | Download do `.bin`, OTA bem-sucedida e reboot automático em FW 2.0. |
| 5 | Vetor original preservado, cópia crescente, média correta e mediana no índice 2. |
| 6 | Mediana >= 16: ALERTA e vermelho. |
| 7 | Mediana 15: conservar NORMAL ou ALERTA de acordo com a sessão anterior. |
| 8 | Mediana <= 14: NORMAL e verde. |

Para testar a histerese sem depender da sorte, use **uma cópia temporária** do projeto com o fonte 2.0. Somente nessa cópia, substitua a linha `leituras[indice] = random(10, 21);` por:

```cpp
const int valoresTeste[4][5] = {
  {15, 14, 15, 16, 15}, // mediana 15: mantem NORMAL inicial
  {18, 16, 15, 16, 20}, // mediana 16: ALERTA
  {15, 14, 15, 16, 15}, // mediana 15: mantem ALERTA
  {14, 10, 20, 12, 14}  // mediana 14: NORMAL
};
leituras[indice] = valoresTeste[sessoesConcluidas % 4][indice];
```

Essa cópia testa os limites e as cores; não comprova OTA. O projeto principal e o binário publicado devem continuar com leituras pseudoaleatórias. Os testes locais já verificam essas transições nas funções originais.

## 4. Situações de erro

Use cópias temporárias e restaure a configuração principal no final.

- **Sem Wi-Fi:** troque `REDE` por um SSID inexistente. Depois da terceira sessão, deve aparecer a mensagem de falha após 15 s, sem impedir as novas sessões.
- **Manifesto indisponível:** coloque uma URL HTTPS inexistente em `MANIFESTO_URL`. Espere o erro HTTP/erro de conexão no Serial.
- **Versão atual:** use um manifesto de teste com `version` igual à versão instalada. Não deve haver download nem reinício.
- **Binário indisponível:** use um manifesto de teste com uma versão superior e uma URL de `.bin` inexistente. Deve aparecer o erro de download/gravação; a versão atual continua executando.
- **Erro na atualização:** aponte para um pequeno arquivo de texto com extensão `.bin`, em vez de uma aplicação ESP32 válida. A biblioteca deve rejeitá-lo e informar erro, sem anunciar sucesso.

Não altere o manifesto principal enquanto outra pessoa estiver validando o projeto.

## 5. PDF final

1. Preencha `repositorio_publicado`, `wokwi_publicado` e `observacoes_demonstracao` em `dados-entrega.json` com os links reais e um resumo dos resultados observados. Não marque testes como concluídos sem executar.
2. Para acrescentar capturas ao PDF, salve imagens `.png` ou `.jpg` em `evidencias/capturas/`. Use nomes explicativos, como `01-fw1-azul.png` e `02-reboot-fw2.png`.
3. Instale as dependências de geração, se necessário: `python3 -m pip install reportlab pypdf`.
4. Execute `python3 gerar_relatorio.py`. O gerador incorpora os códigos atuais, manifesto e binário; também inclui `serial-wokwi.txt` e as capturas, quando presentes.
5. Abra `output/pdf/Relatorio-Motiva-CP2.pdf`, confira os links e as páginas. Entregue **somente esse PDF** no Teams, conforme o enunciado. Os fontes e o binário também ficam acessíveis no repositório.
6. Mantenha repositório e projeto Wokwi públicos por pelo menos 10 dias após a entrega.

O enunciado informa 21/09/2026 como data de entrega. A preparação destes arquivos ocorre em 23/09/2026; verifique com o professor a situação do prazo.
