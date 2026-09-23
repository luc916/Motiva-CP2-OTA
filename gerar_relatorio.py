"""Gera o PDF da atividade com os fontes atuais e o binario anexado.
Requisitos: pip install reportlab pypdf
"""
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import io
import json
import textwrap
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

P=Path(__file__).resolve().parent
D=json.loads((P/'dados-entrega.json').read_text())
OUT=P/'output/pdf/Relatorio-Motiva-CP2.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
# Fontes locais quando disponiveis; as fontes PDF padrao sao o fallback.
fontes=[('Texto','Arial.ttf','Helvetica'),('Negrito','Arial Bold.ttf','Helvetica-Bold'),('Codigo','Courier New.ttf','Courier')]
for nome,arquivo,padrao in fontes:
    caminho=Path('/System/Library/Fonts/Supplemental')/arquivo
    if caminho.exists(): pdfmetrics.registerFont(TTFont(nome,str(caminho)))
    else: pdfmetrics.registerFont(pdfmetrics.Font(nome,padrao,'WinAnsiEncoding'))
estilos={
 'normal':ParagraphStyle('normal',fontName='Texto',fontSize=10.5,leading=15,spaceAfter=8),
 'h1':ParagraphStyle('h1',fontName='Negrito',fontSize=18,leading=23,spaceAfter=16),
 'h2':ParagraphStyle('h2',fontName='Negrito',fontSize=12,leading=16,spaceBefore=10,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Texto',fontSize=8.8,leading=12,spaceAfter=6),
 'code':ParagraphStyle('code',fontName='Codigo',fontSize=7.6,leading=10),
}
story=[]
def par(s,style='normal'):
    story.append(Paragraph(s,estilos[style]))
def titulo(s): par(s,'h1')
def sub(s): par(s,'h2')
def pagina(): story.append(PageBreak())
def tabela(linhas,larguras):
    cells=[[Paragraph(escape(str(v)),estilos['small']) for v in row] for row in linhas]
    t=Table(cells,colWidths=larguras,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#bbbbbb')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.append(t);story.append(Spacer(1,10))
def link(url):
    return '<link href="'+escape(url)+'" color="#174a7e">'+escape(url)+'</link>'
def code(s): story.append(Preformatted(s,estilos['code']))

titulo('Projeto Motiva - Checkpoint 2')
par('Atualização remota de firmware (OTA) em ESP32','h2')
par('Ciência da Computação - 2º ano, 4º semestre<br/>Professor Marcelo Fernando Morgantini')
tabela([['Integrante','RM']]+D['integrantes'],[367,120])
sub('1. Objetivo')
par('Desenvolvemos duas versões de um programa para simular o monitoramento da altura da vegetação. O ESP32 gera cinco leituras por sessão e pode receber uma nova versão pela internet, sem acesso físico ao equipamento. A versão 2.0 acrescenta mediana e histerese ao cálculo da média.')
sub('2. Projetos publicados')
par('Repositório público: '+(link(D['repositorio_publicado']) if D['repositorio_publicado'] else '<b>pendente de publicação pelo grupo.</b>'))
par('Projeto público Wokwi: '+(link(D['wokwi_publicado']) if D['wokwi_publicado'] else '<b>pendente de criação e publicação pelo grupo.</b>'))
par('Teste controlado de histerese: '+link(D['wokwi_histerese']), 'small')
par('Teste de erros: '+link(D['wokwi_erros']), 'small')
par(escape(D['observacoes_demonstracao']))
par('O projeto principal usa dados pseudoaleatórios e sessões de 48 segundos. O projeto separado de histerese usa dados fixos e sessões de 12 segundos para reproduzir os limites. Os registros de execução estão nos anexos.','small')
sub('3. Arquitetura')
par('ESP32 com FW 1.0 → Wokwi-GUEST → manifesto remoto → download do .bin → partição OTA → reinício → FW 2.0.')
par('O circuito usa apenas ESP32 DevKit v1, LED RGB de cátodo comum e três resistores de 220 ohms. Não há sensor: as alturas são simuladas no programa.')

pagina();titulo('Funcionamento do programa')
sub('4. Leituras e temporização')
par('Cada sessão armazena cinco números inteiros pseudoaleatórios entre 10 e 20 cm. A chamada random(10, 21) inclui o 10 e exclui o 21. O programa mostra cada leitura e calcula a média usando a soma dividida por 5.0.')
tabela([['Evento','Instantes em relação à primeira sessão'],['Sessão 1','0, 2, 4, 6 e 8 segundos'],['Sessão 2','48, 50, 52, 54 e 56 segundos'],['Sessão 3','96, 98, 100, 102 e 104 segundos'],['Primeira consulta OTA','Após concluir a terceira sessão, perto de 104 s']],[142,345])
par('O controle usa millis(). O próximo início é obtido somando 48000 ms ao início anterior. Assim, não se soma uma espera de 48 segundos ao fim das leituras. O laço verifica os prazos continuamente, com uma pequena pausa de 1 ms; pode haver pequena variação de execução, mas o período programado não acumula os 8 segundos de coleta.')
sub('5. Evolução da versão 2.0')
par('A versão 1.0 mantém o LED azul. A versão 2.0 conserva as leituras e a média, copia o vetor e ordena essa cópia pelo método bubble sort. O vetor original permanece intacto. Para cinco valores, a mediana é o terceiro valor ordenado, no índice 2.')
par('Exemplo de cálculo, não log da simulação: para 18, 12, 15, 14 e 20, a ordem crescente é 12, 14, 15, 18 e 20. A média é 15,8 cm e a mediana é 15 cm.')
tabela([['Mediana','Estado e indicação'],['Maior ou igual a 16 cm','ALERTA, LED vermelho'],['Entre 14 e 16 cm','Conserva o estado anterior e sua cor'],['Menor ou igual a 14 cm','NORMAL, LED verde']],[180,307])
par('O estado inicial da versão 2.0 é NORMAL. Como as leituras são inteiras, a faixa intermediária é representada por 15 cm. Na sequência de medianas 15, 16, 15 e 14, os estados são NORMAL, ALERTA, ALERTA e NORMAL. A regra segue a tabela de condições do enunciado.')
sub('6. Ligações')
par('GPIO 25 → resistor → R; GPIO 26 → resistor → G; GPIO 27 → resistor → B. Cada resistor tem 220 ohms. O terminal comum do LED vai ao GND. O arquivo diagram.json contém essas ligações.')

pagina();titulo('Atualização e execução')
sub('7. Processo OTA')
par('Depois de três sessões completas, uma tarefa de rede conecta o ESP32 à Wokwi-GUEST e consulta version.json. A comparação separa os números maior e menor da versão. Uma versão igual ou inferior não gera atualização. Quando existe uma versão superior, HTTPUpdate baixa a aplicação, grava a partição OTA inativa e, em caso de sucesso, o programa reinicia o ESP32.')
par('A tarefa de rede mantém as esperas de Wi-Fi e HTTP fora do loop de medição. Se a tentativa falhar, o firmware atual continua e o programa tenta novamente depois de outra sessão concluída. O reinício de uma OTA bem-sucedida começa uma nova sequência de sessões.')
sub('8. Manifesto version.json')
manifesto=(P/'version.json').read_text()
# URL em linha propria para manter o JSON legivel e valido no PDF.
j=json.loads(manifesto)
code('{\n  "version": "'+j['version']+'",\n  "url":\n    "'+j['url']+'"\n}')
sub('9. Passos para executar')
for txt in [
 '1. Abrir o repositório indicado e conferir version.json e firmware_v2.bin na raiz da branch main. Os endereços diretos são públicos e não exigem login.',
 '2. Abrir o projeto principal pelo link da primeira página. O circuito, a biblioteca e a tabela de partições já estão configurados. O código inicial é o firmware 1.0.',
 '3. Iniciar a simulação em FW 1.0, observar o LED azul e aguardar três sessões completas. Registrar os horários impressos no Serial Monitor a 115200 baud.',
 '4. Registrar consulta, download, sucesso da OTA e reinício automático. Confirmar FW 2.0, ordenação, mediana, histerese e mudança do LED sem substituir manualmente o código.',
 '5. Consultar os logs e as capturas nos anexos deste relatório. Manter o repositório e o projeto públicos por pelo menos 10 dias após a entrega.'
]: par(txt)
sub('10. Compilação e bibliotecas')
par('As duas versões usam o core Arduino ESP32 2.0.17, placa esp32:esp32:esp32 e ArduinoJson 7.4.2. O arquivo compilar.sh refaz os binários. As partições app0 e app1 têm 0x140000 bytes cada. O arquivo usado na OTA contém apenas a aplicação 2.0.')
par('WiFi conecta à rede; WiFiClientSecure fornece HTTPS; HTTPClient consulta o manifesto; ArduinoJson interpreta o JSON; HTTPUpdate baixa e grava o firmware. A tarefa FreeRTOS já está incluída no core. Neste laboratório, setInsecure() não valida o certificado HTTPS; em produção, seriam necessárias validação do servidor e autenticidade do firmware.','small')

pagina();titulo('Testes e tratamento de erros')
sub('11. Verificações realizadas')
par('A lógica foi testada localmente e a aplicação foi executada no Wokwi. A demonstração principal verifica a coleta e a atualização remota. Uma cópia separada recebe valores fixos para verificar os limites da histerese.')
tabela([['Teste','Resultado observado'],
 ['1. Firmware 1.0','Passou no Wokwi: cinco leituras por sessão, valores entre 10 e 20 cm, média e LED azul.'],
 ['2. Sessões de 48 s','Passou no Wokwi: inícios em 0/48000/96000 ms e leituras a cada 2 s. O retorno de millis() a zero foi testado localmente.'],
 ['3. Identificar versão nova','Passou no Wokwi: após a leitura em 104000 ms, consultou o GitHub e identificou a versão 2.0.'],
 ['4. OTA e reinício em 2.0','Gravação OTA e reinício automático em 2.0 observados. Ver log da execução principal no anexo.'],
 ['5. Média e mediana','Passou: média, vetor original, cópia ordenada e mediana exibidos após o reinício. Cálculos conferidos nos logs.'],
 ['6. Mediana >= 16','Passou no Wokwi: mediana 16 ativa ALERTA e LED vermelho.'],
 ['7. Faixa intermediária','Passou no teste controlado: mediana 15 mantém NORMAL e também mantém ALERTA, conforme o estado anterior.'],
 ['8. Mediana <= 14','Passou no teste controlado: mediana 14 retorna a NORMAL; LED verde verificado.']],[142,345])
sub('12. Tratamento de erros verificado')
par('Sem Wi-Fi, a tentativa termina após 15 segundos com mensagem. Falhas de acesso ao manifesto mostram o código HTTP ou erro de conexão. JSON inválido é rejeitado. Versão igual, inferior ou inválida não dispara download. Falhas de download ou de gravação mostram o código e a descrição retornados por HTTPUpdate. O programa não anuncia sucesso quando a atualização falha.')
par('Os cinco cenários foram executados no projeto separado de erros. Foram observados: falha de Wi-Fi, HTTP 404 para o manifesto, versão igual sem download, erro -102 para binário ausente e erro -106 para cabeçalho inválido. O programa continuou medindo após as falhas.','small')

pagina();titulo('Arquivos e evidências locais')
sub('13. Binário entregue')
binario=P/'firmware_v2.bin'
if not binario.exists(): raise SystemExit('Compile os firmwares antes de gerar o relatorio.')
sha=hashlib.sha256(binario.read_bytes()).hexdigest()
par('O arquivo firmware_v2.bin está incluído no pacote do projeto e como anexo interno deste PDF. Ele foi compilado a partir do código 2.0 apresentado no apêndice. O hash abaixo permite conferir se o arquivo publicado corresponde ao binário entregue.')
par(f'Tamanho: {binario.stat().st_size:,} bytes.'.replace(',','.'))
par('SHA-256:','small');code(sha)
par('Para extrair o anexo, use um leitor de PDF com painel de anexos, como Adobe Acrobat Reader. O arquivo no repositório deve ter o mesmo hash. Os fontes completos, version.json e diagram.json também estão anexados.','small')
sub('14. Verificações locais complementares')
par('Os testes locais passaram para média, ordenação, mediana, histerese, temporização, retorno de millis() a zero e início da consulta após três sessões. A conferência automática dos logs reais também passou para 13 sessões completas. Os registros estão na pasta evidencias.','small')
sub('15. Compilação')
for v in (1,2):
    log=(P/f'evidencias/compilacao-v{v}.txt').read_text()
    resumo=[l for l in log.splitlines() if l.startswith(('Sketch uses','Sketch usa'))]
    par(f'<b>Firmware {v}.0:</b> compilado para ESP32.','small')
    for l in resumo: par(escape(l),'small')
par('Em consultas posteriores ao reboot, também ocorreram falhas de conexão e acesso ao manifesto. Elas foram informadas no Serial e a coleta continuou. Isso não impediu a OTA já concluída. Os avisos de core dump na inicialização indicam que não foi reservada uma partição para diagnóstico de falhas; não correspondem a falha na atualização.','small')
sub('16. Conclusão')
par('A versão 1.0 realiza a coleta periódica e calcula a média. A versão 2.0 acrescenta a mediana e usa dois limites para evitar mudanças de estado perto de um único valor. A OTA permite levar essa evolução ao dispositivo instalado em campo. A execução no Wokwi comprovou a atualização remota e os estados do sistema. Os testes de erro também permitiram corrigir a reconexão Wi-Fi: uma tentativa anterior é encerrada antes de iniciar outra.')
sub('Referências')
for nome,url in [
 ('Wokwi: ESP32','https://docs.wokwi.com/guides/esp32'),
 ('Wokwi: Wi-Fi','https://docs.wokwi.com/guides/esp32-wifi'),
 ('Espressif: partições','https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/partition_table.html'),
 ('Espressif: OTA','https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/ota.html')]:
    par('<link href="'+url+'" color="#174a7e">'+nome+'</link>','small')
par('Enunciado: MORGS - CP2, professor Marcelo Fernando Morgantini.','small')

for v in (1,2):
    linhas=(P/f'firmware_v{v}/firmware_v{v}.ino').read_text().splitlines()
    # 56 linhas por pagina, sem ocultar ou omitir trechos do programa.
    for inicio in range(0,len(linhas),56):
        pagina();titulo(f'Apêndice {"A" if v==1 else "B"} - Firmware {v}.0')
        par(f'Código completo: firmware_v{v}/firmware_v{v}.ino | linhas {inicio+1} a {min(inicio+56,len(linhas))}','small')
        code('\n'.join(linhas[inicio:inicio+56]))

pagina();titulo('Apêndice C - Configuração')
sub('partitions.csv');code((P/'wokwi/partitions.csv').read_text())
sub('libraries.txt');code((P/'wokwi/libraries.txt').read_text())
sub('Organização dos arquivos')
code('Motiva-CP2-OTA/\n  version.json\n  firmware_v1.bin\n  firmware_v2.bin\n  firmware_v1/firmware_v1.ino\n  firmware_v2/firmware_v2.ino\n  wokwi/sketch.ino\n  wokwi/diagram.json\n  wokwi/libraries.txt\n  wokwi/partitions.csv\n  README.md\n  PUBLICAR-E-TESTAR.md\n  evidencias/\n  tests/testar.py\n  output/pdf/Relatorio-Motiva-CP2.pdf')
sub('Como repetir a demonstração')
par('Abrir o projeto principal no Wokwi e iniciar a simulação. Aguardar três sessões completas e o download do binário. O tempo de parede pode ser maior que o tempo simulado. Conferir a mensagem de sucesso e o cabeçalho FW 2.0 após o reinício. Usar a cópia de histerese para reproduzir os limites sem depender dos valores aleatórios.')

for nome,titulo_log in [('serial-wokwi.txt','OTA e funcionamento'),('serial-histerese.txt','Histerese'),('serial-erros.txt','Tratamento de erros')]:
    serial=P/'evidencias'/nome
    if serial.exists():
        linhas=[]
        for l in serial.read_text().splitlines():
            if l.startswith(('ets Jul','configsip:','clk_drv:','mode:','load:','ho 0','entry ','E (')): continue
            if l.startswith('rst:') and 'SW_CPU_RESET' not in l: continue
            if nome=='serial-histerese.txt' and l.startswith('Sessao 5 |'): break
            linhas.extend(textwrap.wrap(l,100) or [''])
        while linhas and not linhas[-1].strip(): linhas.pop()
        for inicio in range(0,len(linhas),64):
            pagina();titulo('Anexo - '+titulo_log);par('Saída da aplicação. Log original completo disponível nos anexos internos do PDF.','small');code('\n'.join(linhas[inicio:inicio+64]))
fotos=[f for f in sorted((P/'evidencias/capturas').glob('*')) if f.suffix.lower() in ('.jpg','.jpeg','.png')]
legendas={
 '01-fw1-em-execucao':'Firmware 1.0: LED azul e download remoto da versão 2.0.',
 '02-fw2-apos-ota':'Após OTA: ordenação, mediana e LED vermelho. A consulta posterior registrou falha de rede, tratada sem parar a coleta.',
 '03-histerese-alerta':'Teste controlado: mediana de 15 cm mantém ALERTA e LED vermelho.',
 '04-histerese-normal':'Teste controlado: estado NORMAL e LED verde.'
}
for n,foto in enumerate(fotos):
    if n%2==0: pagina();titulo('Anexo - Demonstração no Wokwi')
    par(escape(legendas.get(foto.stem,foto.stem)),'small')
    im=Image(str(foto));escala=min(487/im.imageWidth,280/im.imageHeight)
    im.drawWidth=im.imageWidth*escala;im.drawHeight=im.imageHeight*escala
    story.append(im);story.append(Spacer(1,18))

def rodape(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#bbbbbb'))
    canvas.line(54,40,A4[0]-54,40)
    canvas.setFont('Texto',8);canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(54,27,'Motiva - CP2 | Atualização remota de firmware')
    canvas.drawRightString(A4[0]-54,27,str(doc.page))
buf=io.BytesIO()
doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=54,leftMargin=54,topMargin=44,bottomMargin=55,title='Motiva - CP2: Atualização remota de firmware',author='Grupo Motiva')
doc.build(story,onFirstPage=rodape,onLaterPages=rodape)
writer=PdfWriter();writer.append(PdfReader(buf))
for nome in ['firmware_v2.bin','version.json','firmware_v1/firmware_v1.ino','firmware_v2/firmware_v2.ino','wokwi/diagram.json','README.md','evidencias/serial-wokwi.txt','evidencias/serial-histerese.txt','evidencias/serial-erros.txt']:
    writer.add_attachment(Path(nome).name,(P/nome).read_bytes())
writer.add_metadata({'/Title':'Motiva - CP2: Atualização remota de firmware','/Author':'Grupo Motiva'})
with OUT.open('wb') as f:writer.write(f)
print(OUT)
