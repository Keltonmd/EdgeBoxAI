from CoppeliaBracoAgent import CoppeliaBracoAgent
from MqttAgent import MqttAgent
import time

agent = CoppeliaBracoAgent("/UR10")
agent.obterScriptHandle()
posDisponivelVer = agent.getPosicoesRack("/rack/posVer", 10)
posDisponivelAzul = agent.getPosicoesRack("/rack/posAzu", 10)

topicos = ["/entregador/coletaDisponivel", "/esp/resultado"]
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

def guardarBloco(resultado):

    espera = agent.getObjeto("/UR10/posEsperaAtras")
    agent.rotacionar_para_posicao_xyz(180, espera)
    
    pos = []
    
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
    
    agent.descerBraco(pos[2] + 0.01)
    # Mover na horinzontal
    agent.mover_para_posicao_xyz([pos[0], None, None])
    # Mover na vertical
    agent.mover_para_posicao_xyz([None, pos[1] + 0.04, None])

    time.sleep(1)
    agent.abrirGarra()
    time.sleep(3)

    posEspera = agent.getPos("/UR10/posEsperaAtras")
    
    # Mover na vertical
    agent.mover_para_posicao_xyz([None, posEspera[1], None])
    
    # Mover na horinzontal
    agent.mover_para_posicao_xyz([posEspera[0], None, None])

    agent.subirBraco(posEspera[2] + 0.01)
        
    espera = agent.getObjeto("/UR10/posEspera")
    agent.rotacionar_para_posicao_xyz(0, espera)
    
    
def todas_posicoes_ocupadas():
    if not any(pos["livre"] for pos in posDisponivelVer) and not any(pos["livre"] for pos in posDisponivelAzul):
        return True
    return False

agent.abrirGarra()

pegarBloco()
guardarBloco(1)

'''
for _ in range(10):
    pegarBloco()
    guardarBloco(0)
'''