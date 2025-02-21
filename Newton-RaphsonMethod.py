# -*- coding: utf-8 -*-

from bibliotecaLerDados import LeitorDados
import numpy as np
from numpy.linalg import inv                 #importa a funcao inversa para matriz
from array import array
import cmath


arqivo = open('G:\\O meu disco\\Biblioteca de Programas em Python\\FluxoNewton\\Fluxo de Carga\\Power-Flow real inputs\\Teste6barras.txt','r')
DadosBarra,DadosLinhas,barra,ramo,Sbase,nb,nl,Y,B,G,ntn,ntd = LeitorDados.ler_dados(arqivo)
#Z = (inv(Y))
print(DadosBarra)
Vbase = 11
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# RESOLUCAO DO SUBSISTEMA 1
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
E = 0.0001
it = 0
maxit = 100
V = np.zeros((nb,1),dtype=float)
teta = np.zeros((nb,1),dtype=float)
Pk = np.zeros((nb,1),dtype=float)
Qk = np.zeros((nb,1),dtype=float)
dP = np.zeros((nb,1),dtype=float)
dQ = np.zeros((nb,1),dtype=float)

for i in range(nb):
    if DadosBarra['tipo'][i] == 2:            # Se for barra slack
        V[i] = DadosBarra['tensao'][i]
        teta[i] = DadosBarra['angulo'][i]
    elif DadosBarra['tipo'][i] == 1:          # Se for barra PV
        V[i] = DadosBarra['tensao'][i]
        teta[i] = 0
    else:                                     # Se for barra PQ
        V[i] = Vbase
        teta[i] = 0

# print(DadosBarra['tipo'])
# Testar a convergencia
# Calculo dis mismatchs de Potencia

for k in range(nb):
    # Calculo das injecoes de potencia ativa (Pk) e reativa (Qk)
    acumuladoP = 0
    acumuladoQ = 0
    for m in range(nb):
        acumuladoP = acumuladoP + V[m] * ((G[k,m]*np.cos(teta[k]-teta[m]) + B[k,m]*np.sin(teta[k]-teta[m])))
        acumuladoQ = acumuladoQ + V[m] * ((G[k,m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m])))
    Pk[k] = (V[k]*acumuladoP)          
    Qk[k] = (V[k]*acumuladoQ)   

    # Calculo dos mismatches de potencia ativa dP e Reativa dQ

    if DadosBarra['tipo'][k] == 2:                                  # Se barra e Vteta, entao nao ha mismatches de P nem de Q
        dP[k] = 0
        dQ[k] = 0
    elif DadosBarra['tipo'][k] == 1:                                # Se barra e PV, entao nao ha mismatches de Q, apenas de P
        dP[k] = barra['P'][k] - (Pk[k]/1000)
        dQ[k] = 0
    else:                                                           # Se barra e PQ, entao ha mismatches de P e de Q
        dP[k] = barra['P'][k] - (Pk[k]/1000)
        dQ[k] = barra['Q'][k] - (Qk[k]/1000)

b = np.append(dP.T,dQ.T,axis=1)                       
x = np.append(teta,V,axis=0)

MAX_MISMATCHE = np.max(np.abs(b))
JAC = np.zeros(((2*nb),(2*nb)),dtype=float)

relatorio_convergencia = {'iteracao':None,'mismatche':None}
iteracao = []
mismatche = []
iteracao.append(it)
mismatche.append(MAX_MISMATCHE)
relatorio_convergencia['iteracao'] = iteracao
relatorio_convergencia['mismatche'] = mismatche

while MAX_MISMATCHE > E and it < 100:
    # Montar a matriz Jacobiana
    for J in range(nl):
        k = (int(DadosLinhas['De'][J]))
        m = (int(DadosLinhas['Para'][J]))
        # Submatriz H
        JAC[k][m] = V[k]*V[m]*(G[k, m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
        JAC[m][k] = V[m]*V[k]*(-G[k, m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
        if DadosBarra['tipo'][k] == 2:       # Se barra for Vteta
            JAC[k][k] = 10**99
        else:
            JAC[k][k] = -Qk[k] - (np.power(V[k],2) * B[k][k])
        if DadosBarra['tipo'][k] == 2:       # Se barra for Vteta
            JAC[m][m] = 10**99
        else:
            JAC[m][m] = -Qk[m] - (np.power(V[m],2) * B[m][m])
        # Submatriz N
        JAC[k][nb+k] = np.power(V[k],-1) * (Pk[k]+G[k][k]*np.power(V[k],2))
        JAC[m][nb+m] = np.power(V[m],-1) * (Pk[m]+G[m][m]*np.power(V[m],2))
        JAC[k][nb+m] = V[k]*(G[k,m]*np.cos(teta[k]-teta[m]) + B[k,m]*np.sin(teta[k]-teta[m]))
        JAC[m][nb+k] = V[m]*(G[k,m]*np.cos(teta[k]-teta[m]) - B[k,m]*np.sin(teta[k]-teta[m]))
        # Submatriz M
        JAC[nb+k][k] = -G[k,k]*np.power(V[k],2) + Pk[k]
        JAC[nb+m][m] = -G[m,m]*np.power(V[m],2) + Pk[m]
        JAC[nb+k][m] = -V[k]*V[m]*(G[k,m]*np.cos(teta[k]-teta[m]) + B[k,m]*np.sin(teta[k]-teta[m]))
        JAC[nb+m][k] = -V[k]*V[m]*(G[k,m]*np.cos(teta[k]-teta[m]) - B[k,m]*np.sin(teta[k]-teta[m]))
        # Submatriz L
        if DadosBarra['tipo'][k] == 0:           # Se k for PQ
            JAC[nb+k][nb+k] = np.power(V[k],-1)*(Qk[k]-B[k,k]*np.power(V[k],2))
        else:                                    # Se k for Vteta ou PV
            JAC[nb+k][nb+k] = 10**99
        if DadosBarra['tipo'][m] == 0:           # Se m for PQ
            JAC[nb+m][nb+m] = np.power(V[m],-1)*(Qk[m]-B[m,m]*np.power(V[m],2))
        else:                                    # Se m for Vteta ou PV
            JAC[nb+m][nb+m] = 10*99
        JAC[nb+k][nb+m] = V[k]*(G[k,m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
        JAC[nb+m][nb+k] = -V[m]*(G[k,m]*np.sin(teta[k]-teta[m]) + B[k,m]*np.cos(teta[k]-teta[m]))

    # Obter as correcoes das variaveis de estado (deltaTeta e deltaV)

    dx = (np.linalg.solve(JAC,b.T))
    x = x + dx
    teta = np.copy(x[0:nb])
    V = np.copy(x[nb:(2*nb)]) 

    # Incrementar a iteracao
    it += 1

    # Verificacao da possibilidade da barra PQ voltar a ser PV
    '''for k in range (nb):
            if DadosBarra['Qmax_ger'][k] > 0 and DadosBarra['Qmin_ger'][k] < 0:
                if V[k] >= DadosBarra['tensao'][k]:
                    V[k] = DadosBarra['tensao'][k]
                    DadosBarra['tipo'][k] = 1 # Barra volta a ser do tipo PV'''

    # Atualizacao dos valores de Pk e Qk e Calculo dos Mismatches de Ptencia
    for k in range(nb):
        # Calculo das injecoes de potencia ativa (Pk) e reativa (Qk)
        acumuladoP = 0
        acumuladoQ = 0
        for m in range(nb):
            acumuladoP = acumuladoP + V[m] * (G[k,m]*np.cos(teta[k]-teta[m]) + B[k,m]*np.sin(teta[k]-teta[m]))
            acumuladoQ = acumuladoQ + V[m] * (G[k,m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
        Pk[k] = V[k]*acumuladoP          
        Qk[k] = V[k]*acumuladoQ   
    
        # Calculo dos mismatches de potencia ativa dP e reativa dQ   

        if DadosBarra['tipo'][k] == 2:                                  # Se barra e Vteta, entao nao ha mismatches de P nem de Q
            dP[k] = 0
            dQ[k] = 0
        elif DadosBarra['tipo'][k] == 1:                                # Se barra e PV, entao nao ha mismatches de Q, apenas de P
            dP[k] = barra['P'][k] - (Pk[k])
            dQ[k] = 0
        else:                                                           # Se barra e PQ, entao ha mismatches de P e de Q
            dP[k] = barra['P'][k] - (Pk[k])
            dQ[k] = barra['Q'][k] - (Qk[k])

    
     # Verificacao do limite de reativos e possivel transformacao de barra PV para PQ

    '''for k in range(nb):
        if DadosBarra['tipo'][k] == 1:
            if Qk[k] > DadosBarra['Qmax_ger'][k]:
                    barra['Q'][k] = DadosBarra['Qmax_ger'][k]
                    DadosBarra['tipo'][k] = 0 # Vira barra PQ
            elif Qk[k] < DadosBarra['Qmin_ger'][k]:
                    barra['Q'][k] = DadosBarra['Qmin_ger'][k]
                    DadosBarra['tipo'][k] = 0 # Vira barra PQ'''

    b = np.zeros((2*nb,1),dtype=float)
    b = np.append(dP.T,dQ.T,axis=1)
    MAX_MISMATCHE = np.max(np.abs(b))
    iteracao.append(it)
    mismatche.append(MAX_MISMATCHE)
    relatorio_convergencia['iteracao'] = iteracao
    relatorio_convergencia['mismatche'] = mismatche

   
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# RESOLUCAO DO SUBSISTEMA 2
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# Calculo de Pk nas barras Vteta e de Qk nas barras Vteta e PV
#print(V*400)
#print('*='*30)
#print((teta/np.pi)*180)
#print(teta)
#print('*='*30)
#print(DadosBarra)


for k in range(nb):
    # Calculo das injecoes de Potencia Ativa (Pk) e Reativa (Qk)
    acumuladoP = 0
    acumuladoQ = 0
    for m in range(nb):
        if DadosBarra['tipo'][k] == 2:
            acumuladoP = acumuladoP + V[m] * (G[k,m]*np.cos(teta[k]-teta[m]) + B[k,m]*np.sin(teta[k]-teta[m]))
            acumuladoQ = acumuladoQ + V[m] * (G[k,m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
        elif DadosBarra['tipo'][k] == 1:
            acumuladoQ = acumuladoQ + V[m] * (G[k,m]*np.sin(teta[k]-teta[m]) - B[k,m]*np.cos(teta[k]-teta[m]))
    if DadosBarra['tipo'][k] == 2:
        Pk[k] = V[k]*(acumuladoP)           
        Qk[k] = V[k]*(acumuladoQ) 
    elif DadosBarra['tipo'][k] == 1:
        Pk[k] = DadosBarra['Pger'][k]
        Qk[k] = V[k]*(acumuladoQ) 

for k in range(len(Pk)):
    Pk[k] = Pk[k]/100
    Qk[k] = Qk[k]/100

# Calculo dos Fluxos de Potencia Ativa (Pkm, Pmk) e Reativa (Qkm, Qmk) nos ramos
Fluxo = {'Pkm':None,'Pmk':None,'Qkm':None,'Qmk':None,'PerdaAtiva_km':None,'PerdaReativa_km':None}
temp = [] 
temp1 = []
temp2 = []
temp3 = []
temp4 = []
temp5 = []
#PeradaAtivakm = []
#PerdaReativakm = []

for J in range(nl):
    k = int(DadosLinhas['De'][J])
    m = int(DadosLinhas['Para'][J])
    gkm = ramo['g'][J]
    bkm = ramo['b'][J]
    bkmsh = ramo['bsh'][J]
    akm = DadosLinhas['tap'][J]
    fikm = DadosLinhas['fi'][J]

    temp.append(((((1/akm)*V[k])**2)*gkm - ((1/akm)*V[k]*V[m]*(gkm*np.cos(teta[k]-teta[m]+fikm) + bkm*np.sin(teta[k]-teta[m]+fikm))))/100)
    temp1.append((((V[m]**2))*gkm - (1/akm)*V[k]*V[m]*(gkm*np.cos(teta[k]-teta[m]+fikm) - bkm*np.sin(teta[k]-teta[m]+fikm)))/100)
    temp2.append((-(((1/akm)*V[k])**2)*(bkm+bkmsh) - (1/akm)*V[k]*V[m]*(gkm*np.sin(teta[k]-teta[m]+fikm) - bkm*np.cos(teta[k]-teta[m]+fikm)))/100)
    temp3.append((-(V[m]**2)*(bkm+bkmsh) + (1/akm)*V[k]*V[m]*(gkm*np.sin(teta[k]-teta[m]+fikm) + bkm*np.cos(teta[k]-teta[m]+fikm)))/100)
    temp4.append(np.abs((np.abs(temp[J])) - np.abs(temp1[J])))
    temp5.append(np.abs((np.abs(temp2[J])) - np.abs(temp3[J])))
    Fluxo['Pkm'] = temp[:]
    Fluxo['Pmk'] = temp1[:]
    Fluxo['Qkm'] = temp2[:]
    Fluxo['Qmk'] = temp3[:]
    Fluxo['PerdaAtiva_km'] = temp4[:]
    Fluxo['PerdaReativa_km'] = temp5[:]
    #PeradaAtivakm.append(gkm*((V[k]**2)+(V[m]**2) - 2*V[k]*V[m]*np.cos(teta[k]-teta[m])))
    #PerdaReativakm.append((-bkmsh*((V[k]**2)*(V[m]**2)) - (bkm*((V[k]**2)*(V[m]**2)-2*V[k]*V[m]*np.cos(teta[k]-teta[m])))))

del(temp,temp1,temp2,temp3,temp4,temp5)

#print(type(Vteta))

# Transformando os fluxos, as perdas, as injecoes de potencia e os mismatches de potencia em MVA

'''for J in Fluxo.keys():
    for i in range(len(Fluxo[J])):
        Fluxo[J][i] = Fluxo[J][i]*Sbase'''


'''Pk = Pk*Sbase
Qk = Qk*Sbase
dP = dP*Sbase
dQ = dQ*Sbase'''


# Transformando o teta em graus

teta_graus = (teta/np.pi)*180

'''# Colocando os valores calculados dentro de um dicionario para uma melhor impressao
cal = {'V':None,'teta_graus':None,'teta':None,'Pk':None,'Qk':None,'dP':None,'dQ':None}
a = [] 
b = []
c = []
d = []
e = []
f = [] 
g = []
for i in range(nb):
    a.append(float(V[i]))
    b.append(float(teta_graus[i]))
    c.append(float(teta[i]))
    d.append(float(Pk[i]))
    e.append(float(Qk[i]))
    f.append(float(dP[i]))
    g.append(float(dQ[i]))
    cal['V'] = a[:]
    cal['teta_graus'] = b[:]
    cal['teta'] = c[:]
    cal['Pk'] = d[:]
    cal['Qk'] = e[:]
    cal['dP'] = f[:]
    cal['dP'] = g[:]
del(a,b,c,d,e,f,g)'''

#print(float(sum(Fluxo['PerdaAtiva_km']*100)))
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# IMPRIMINDO RELATORIO DE SAIDA
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# print(DadosBarra['tipo'])
arq = open('G:\\O meu disco\\Biblioteca de Programas em Python\\FluxoNewton\\Fluxo de Carga\\Power-Flow real inputs\\relatorioTeste6barras.txt','w')
arq.write('=='*60)
arq.write('\n')
arq.write('                                               RELATÓRIO DE SAÍDA                    \n')
arq.write('=='*60)
arq.write('\n')
arq.write('                                           Informações Gerais do Sistema                 \n')
arq.write('--'*60)
arq.write('\n')
arq.write('  Arquivo de Entrada: {}\n'.format(arqivo))    
arq.write('  Numero de Barras: {}\n'.format(nb))
arq.write('  Numero de Linhas: {}\n'.format(nl))
arq.write('  Numero de trafos convencionais: {}\n'.format(ntn))
arq.write('  Numero de trafos defasadores: {}\n'.format(ntd))
arq.write('=='*60)
arq.write('\n')
arq.write('                                                 DADOS DAS BARRAS                               \n')
arq.write('=='*60)
arq.write('\n')
arq.write('  Barra   ')
arq.write('  Tipo    ')
arq.write('    Tensão  ')
arq.write('    Ângulo (º)  ')
arq.write('    Ângulo (rad) ')
arq.write('    Pk (kW)  ')
arq.write('    Qk (kVAr ')
arq.write('    dP (kW)  ')
arq.write('    dQ (kVAr) ')
arq.write('\n')
arq.write('--'*60) 
arq.write('\n')
for i in range(nb):
    arq.write('{:^10.4f}{:^10.4f}  {:^10.4f}   {:^10.4f}        {:^10.4f}      {:^10.4f}   {:^10.4f}   {:^10.4f}   {:^10.4f}\n'.format(float(DadosBarra['num'][i]),float(DadosBarra['tipo'][i]),float(V[i]),float(teta_graus[i]),float(teta[i]),float(Pk[i]*100),float(Qk[i]*100),float(dP[i]*100),float(dQ[i]*100)))
arq.write('\n')
arq.write('=='*60)
arq.write('\n')
arq.write('                                                 DADOS DOS RAMOS                               \n')
arq.write('=='*60)
arq.write('\n')
arq.write(' '*69)
arq.write('                         PERDAS\n')    
arq.write('   k    ')
arq.write('      m    ')
arq.write('      Pkm (kW)   ')
arq.write('   Pmk (kW)   ')
arq.write('   Qkm (kVAr)   ')
arq.write('   Qmk (kVAr)   ')
arq.write('   Ativa (kW)   ')
arq.write('   Reativa (kVAr)   ')
arq.write('\n')
arq.write('--'*60)
arq.write('\n') 
for i in range(nl):
    arq.write('{:^10.4f}{:^10.4f}    {:^10.4f}   {:^10.4f}      {:^10.4f}      {:^10.4f}     {:^10.4f}        {:^10.4f}\n'.format(float((DadosLinhas['De'][i])+1),float((DadosLinhas['Para'][i])+1),float(Fluxo['Pkm'][i]*100),float(Fluxo['Pmk'][i]*100),float(Fluxo['Qkm'][i]*100),float(Fluxo['Qmk'][i]*100),float(Fluxo['PerdaAtiva_km'][i]*100),float(Fluxo['PerdaReativa_km'][i]*100)))
arq.write('                                                                                      ------            ------')
arq.write('\n')
arq.write('                                                                             Total')
arq.write('  {:^10.4f}        {:^10.4f}'.format(float(sum(Fluxo['PerdaAtiva_km'])*100),float(sum(Fluxo['PerdaReativa_km'])*100)))
arq.write('\n')
arq.write('--'*60) 
arq.write('\n')
arq.write('=='*60)
arq.write('\n')
arq.write('                                               RELATÓRIO DE CONVERGÊNCIA                    \n')
arq.write('=='*60)
arq.write('\n')
arq.write('  Método de Newton-Raphson\n')
arq.write('  Tolerância de Convergência: {:0.4f}\n'.format(float(E)))
arq.write('--'*60) 
arq.write('\n')
arq.write('  Iteração   ')
arq.write('  Mismatche  ')
arq.write('\n')
arq.write('--'*60) 
arq.write('\n')
for i in range(len(relatorio_convergencia['iteracao'])):
    arq.write('    {:^5.4f}      {:^5.4f} \n'.format(float(relatorio_convergencia['iteracao'][i]),float(relatorio_convergencia['mismatche'][i])))
arq.write('\n')
arq.write('=='*60)
arq.write('\n')
arq.write('  FIM')
arq.close()
