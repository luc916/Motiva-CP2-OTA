"""Testa as funcoes retiradas dos proprios .ino, com relogio e GPIO simulados.
Nao simula Wi-Fi, HTTP, flash nem o bootloader do ESP32.
Requisitos: Python 3 e um compilador C++ (c++, g++ ou clang++).
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

RAIZ = Path(__file__).resolve().parents[1]

def extrair(codigo, nome):
    import re
    m = re.search(r'^(?:void|float|bool) ' + nome + r'\([^\n]*\) \{', codigo, re.M)
    if not m:
        raise RuntimeError('Funcao nao encontrada: ' + nome)
    inicio = codigo.index('{', m.start())
    nivel = 1
    fim = inicio + 1
    while nivel:
        if codigo[fim] == '{': nivel += 1
        if codigo[fim] == '}': nivel -= 1
        fim += 1
    return codigo[m.start():fim]

base = r'''
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <algorithm>
#include <vector>
#include <string>
using namespace std;
struct SerialMock {
 void print(const char*) {}
 void println(const char* = "") {}
 template<typename... A> void printf(const char*, A...) {}
} Serial;
const int LED_R=25, LED_G=26, LED_B=27, QUANTIDADE=5;
const uint32_t INTERVALO_LEITURA=2000, INTERVALO_SESSAO=48000;
int leituras[5], indice=0, sessoesConcluidas=0, ultimaSessaoConsultada=0;
uint32_t inicioSessao=0, primeiraSessao=0, relogio=0;
bool alerta=false;
volatile bool otaEmAndamento=false;
int cores[28]={};
vector<uint32_t> tempos;
uint32_t millis() {return relogio;}
void digitalWrite(int pin, bool valor) {cores[pin]=valor;}
long random(int minimo, int maximo) {
 assert(minimo==10 && maximo==21);
 tempos.push_back(relogio);
 return 10 + (tempos.size() % 11);
}
const int pdPASS=1;
int retornoTask=1, chamadasTask=0;
void tarefaOTA(void*) {}
int xTaskCreate(void (*)(void*),const char*,int,void*,int,void*) {
 chamadasTask++; return retornoTask;
}
'''
checks = r'''
int main() {
 int a[]={18,12,15,14,20};
 assert(fabs(calcularMedia(a)-15.8f)<0.0001);
 int extremos[]={10,10,10,10,10};
 assert(calcularMedia(extremos)==10);
 fill(extremos,extremos+5,20);
 assert(calcularMedia(extremos)==20);
 assert(versaoMaisNova("2.0","1.0"));
 assert(!versaoMaisNova("2.0","2.0"));
 assert(!versaoMaisNova("1.0","2.0"));
 assert(versaoMaisNova("1.10","1.9"));
 assert(!versaoMaisNova("2.x","1.0"));
 assert(!versaoMaisNova("-2.0","1.0"));
 assert(!versaoMaisNova("2.0x","1.0"));
 // Exercita o mesmo agendador com cada milissegundo de quatro sessoes.
 for(relogio=0;relogio<=152000;relogio++) atualizarLeituras();
 vector<uint32_t> esperado={0,2000,4000,6000,8000,
  48000,50000,52000,54000,56000,96000,98000,100000,102000,104000,
  144000,146000,148000,150000,152000};
 assert(tempos==esperado && sessoesConcluidas==4);
 // O mesmo intervalo precisa funcionar quando millis() retorna a zero.
 tempos.clear(); indice=0; sessoesConcluidas=0;
 primeiraSessao=inicioSessao=0xffff0000u;
 for(uint32_t d=0;d<=104000;d++) {
  relogio=primeiraSessao+d; atualizarLeituras();
 }
 assert(sessoesConcluidas==3 && tempos.size()==15);
 assert(uint32_t(tempos[5]-tempos[0])==48000);
 assert(uint32_t(tempos[10]-tempos[5])==48000);
 // Nao inicia OTA antes de terminar a terceira sessao, nem em duplicidade.
 sessoesConcluidas=2; verificarOTA(); assert(chamadasTask==0);
 sessoesConcluidas=3; verificarOTA(); assert(chamadasTask==1);
 verificarOTA(); assert(chamadasTask==1);
 otaEmAndamento=false; verificarOTA(); assert(chamadasTask==1);
 sessoesConcluidas=4; retornoTask=0; verificarOTA();
 assert(chamadasTask==2 && !otaEmAndamento);
 @CHECK_V2@
 puts("OK: media, versoes, leituras 0/2/4/6/8 s, sessoes 48 s, rollover e OTA apos 3 sessoes.");
}
'''
v2 = r'''
 int copia[5]; ordenarCopia(a,copia);
 int esperadoOrdenado[]={12,14,15,18,20};
 assert(equal(copia,copia+5,esperadoOrdenado));
 int original[]={18,12,15,14,20}; assert(equal(a,a+5,original));
 assert(copia[2]==15);
 // Duplicatas, ordem inversa e extremos, comparados com a biblioteca C++.
 int casos[][5]={{20,19,18,17,16},{15,15,15,15,15},
  {10,20,10,20,10},{16,16,14,15,20},{14,10,20,12,14}};
 for(auto &caso:casos) {
  int ref[5]; copy(caso,caso+5,ref); sort(ref,ref+5);
  ordenarCopia(caso,copia); assert(equal(ref,ref+5,copia));
 }
 bool estado=false;
 int medianas[]={15,16,15,14,15,20,10};
 bool estados[]={false,true,true,false,false,true,false};
 for(int i=0;i<7;i++) {
  estado=aplicarHisterese(medianas[i],estado); assert(estado==estados[i]);
  fill(leituras,leituras+5,medianas[i]); concluirSessao();
  assert(alerta==estados[i]);
  assert(cores[LED_R]==estados[i] && cores[LED_G]==!estados[i]);
  assert(!cores[LED_B]);
 }
 puts("OK: copia preservada, ordenacao, mediana, limiares 14/16, memoria em 15 e GPIO do LED.");
'''
compiler=shutil.which('c++') or shutil.which('g++') or shutil.which('clang++')
if not compiler: raise SystemExit('Instale um compilador C++ para executar estes testes.')
for versao in (1,2):
    fonte=(RAIZ/f'firmware_v{versao}/firmware_v{versao}.ino').read_text()
    funcoes=['definirLed','calcularMedia']
    if versao==2: funcoes+=['ordenarCopia','aplicarHisterese','mostrarVetor']
    funcoes+=['concluirSessao','anunciarSessao','atualizarLeituras','versaoMaisNova','verificarOTA']
    programa=base+'\n'.join(extrair(fonte,f) for f in funcoes)+checks.replace('@CHECK_V2@',v2 if versao==2 else '')
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/'test.cpp'; exe=Path(tmp)/'test'
        src.write_text(programa)
        subprocess.run([compiler,'-std=c++11','-Wall','-Wextra',str(src),'-o',str(exe)],check=True)
        print(f'Firmware {versao}.0:',flush=True)
        subprocess.run([str(exe)],check=True)
print('Todos os testes locais passaram. OTA pela internet e LEDs no Wokwi: pendentes.')
