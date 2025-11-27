from CoppeliaBracoAgent import CoppeliaBracoAgent
from MqttAgent import MqttAgent
import time

agent = CoppeliaBracoAgent("/UR10")
agent.obterScriptHandle()
posDisponivelVer = agent.getPosicoesRack("/rack1/pos", 10)
posDisponivelAzul = agent.getPosicoesRack("/rack2/pos", 10)

topicos = ["/entregador/coletaDisponivel", "/edison/resultado"]
client = MqttAgent("UR10", topicos)

segurando_bloco = False
guardar_caixa = False

def pegarBloco():
    espera = agent.getObjeto("/UR10/posEspera")
    agent.rotacionar_para_posicao_xyz(0,espera)
    time.sleep(1.5)
    agent.abrirGarra()
    
    pos_cubo = agent.getPos("/youBot/cuboPos")
    
    if pos_cubo[1] > 0:
        pos_cubo[1] += 0.025
    else:
        pos_cubo[1] -= 0.025
        
    agent.mover_para_posicao_xyz([pos_cubo[0], pos_cubo[1], pos_cubo[2] - 0.008] )
    time.sleep(1)
    agent.fecharGarra()
    time.sleep(2)
    
    posEspera = agent.getPos("/UR10/posEspera")
    agent.subirBraco(posEspera[2] - posEspera[2]/2)
    
    agent.mover_para_posicao_xyz([posEspera[0], posEspera[1], posEspera[2]])

def guardarBloco():
        
    time.sleep(3)
    espera = agent.getPos("/UR10/posEsperaAtras")
    agent.mover(espera[0], espera[1], espera[2], 0, 0, 180)
    
    time.sleep(5)
    
    pos = []
    resultado = 1
    #client.
    if resultado == 0: # Azul
        for posicao in posDisponivelAzul:
            if posicao["livre"]:
                posicao["livre"] = False
                pos = posicao["pos"]
                break
    else: # Vermelho
        for posicao in posDisponivelVer:
            if posicao["livre"]:
                posicao["livre"] = False
                pos = posicao["pos"]
                break
                
    if not pos:
        return
    
    agent.mover(pos[0], espera[1], pos[2] + 0.02, 0, 0, 180)
    time.sleep(2)
    agent.mover(pos[0], pos[1], pos[2] + 0.02, 0, 0, 180)
    
    time.sleep(2)
    agent.abrirGarra()
    time.sleep(2)
    
    agent.mover(pos[0], espera[1], pos[2] + 0.02, 0, 0, 180)
    time.sleep(3)
    agent.mover(espera[0], espera[1], espera[2], 0, 0, 180)
    
    time.sleep(3)
    
    espera = agent.getPos("/UR10/posEspera")
    
    agent.mover(espera[0], espera[1], espera[2], 0, 0, 0)

def todas_posicoes_ocupadas():
    if not any(pos["livre"] for pos in posDisponivelVer) and not any(pos["livre"] for pos in posDisponivelAzul):
        return True
    return False

agent.abrirGarra()


guardarBloco()