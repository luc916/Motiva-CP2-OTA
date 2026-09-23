"""Confere os calculos nos logs reais do Wokwi, sem gerar leituras ficticias."""
from pathlib import Path
import re
p=Path(__file__).resolve().parents[1]
main=(p/'evidencias/serial-wokwi.txt').read_text()
hist=(p/'evidencias/serial-histerese.txt').read_text()
erros=(p/'evidencias/serial-erros.txt').read_text()
assert main.index('t=104000 ms') < main.index('Consultando manifesto:')
assert main.index('OTA gravada com sucesso.') < main.index('MONITORAMENTO DE VEGETACAO - FW 2.0')
assert 'SW_CPU_RESET' in main
count=0
for text in (main,hist):
    alerta=False
    for bloco in re.split(r'(?=Sessao \d+ \| inicio relativo:)',text)[1:]:
        nums=[int(x) for x in re.findall(r'Leitura \d+: (\d+) cm',bloco)]
        media=re.search(r'Media da sessao: ([\d.]+)',bloco)
        if not media: continue  # Sessao interrompida pelo reboot ou pela captura.
        assert len(nums)==5 and all(10<=n<=20 for n in nums)
        assert abs(sum(nums)/5-float(media[1]))<0.01
        med=re.search(r'Mediana: (\d+) cm \| Estado: (NORMAL|ALERTA)',bloco)
        if med:
            ordem=re.search(r'Ordem crescente: ([\d ]+)',bloco)
            original=re.search(r'Ordem original: ([\d ]+)',bloco)
            assert list(map(int,ordem[1].split()))==sorted(nums)
            assert list(map(int,original[1].split()))==nums
            assert int(med[1])==sorted(nums)[2]
            if int(med[1])>=16: alerta=True
            elif int(med[1])<=14: alerta=False
            assert med[2]==('ALERTA' if alerta else 'NORMAL')
        count+=1
seq=re.findall(r'Mediana: (\d+) cm \| Estado: (NORMAL|ALERTA)',hist)
assert seq[:4]==[('15','NORMAL'),('16','ALERTA'),('15','ALERTA'),('14','NORMAL')]
for msg in ['Erro: sem conexao Wi-Fi','HTTP/erro: 404','Versao instalada: 1.0 | disponivel: 1.0','-102 - File Not Found (404)','-106 - Verify Bin Header Failed','DIAGNOSTICO CONCLUIDO']:
    assert msg in erros,msg
assert erros.index('DIAGNOSTICO CONCLUIDO')<erros.index('Leitura 5: 16 cm | t=56000 ms')
print(f'OK: {count} sessoes completas conferidas nos logs reais; medias, vetores e medianas corretos.')
print('OK: consulta apos tres sessoes, OTA bem-sucedida e reboot automatico em FW 2.0.')
print('OK: histerese 15 NORMAL -> 16 ALERTA -> 15 ALERTA -> 14 NORMAL.')
print('OK: cinco cenarios de erro e continuidade das leituras apos falha OTA.')
