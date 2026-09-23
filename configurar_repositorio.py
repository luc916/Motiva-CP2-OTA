"""Uso: python3 configurar_repositorio.py usuario repositorio [branch].
Apos mudar as URLs, recompile os binarios e gere novamente o PDF.
"""
import json
import re
import sys
from pathlib import Path
p=Path(__file__).resolve().parent
if len(sys.argv) not in (3,4):
    raise SystemExit('Uso: python3 configurar_repositorio.py usuario repositorio [branch]')
usuario,repo=sys.argv[1:3]
branch=sys.argv[3] if len(sys.argv)==4 else 'main'
if not all(re.fullmatch(r'[A-Za-z0-9_.-]+',x) for x in (usuario,repo,branch)):
    raise SystemExit('Use nomes simples, sem espacos ou barras.')
base=f'https://raw.githubusercontent.com/{usuario}/{repo}/{branch}/'
for v in (1,2):
    f=p/f'firmware_v{v}/firmware_v{v}.ino'
    s=re.sub(r'(const char\* MANIFESTO_URL =\s*)"[^"]*";',
             lambda m:m[1]+'"'+base+'version.json";',f.read_text())
    f.write_text(s)
(p/'wokwi/sketch.ino').write_text((p/'firmware_v1/firmware_v1.ino').read_text())
(p/'version.json').write_text(json.dumps({'version':'2.0','url':base+'firmware_v2.bin'},indent=2)+'\n')
f=p/'dados-entrega.json'; dados=json.loads(f.read_text())
dados['repositorio_previsto']=f'https://github.com/{usuario}/{repo}'
f.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n')
print('URLs alteradas. Execute bash compilar.sh e python3 gerar_relatorio.py.')
