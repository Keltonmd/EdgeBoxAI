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

def guardarBloco():
    espera = agent.getObjeto("/UR10/posEsperaAtras")
    agent.rotacionar_para_posicao_xyz(180, espera)
    
    pos = []

    if client.resultado == 0:  # Azul
        prioridade = posDisponivelAzul
        fallback = posDisponivelVer
    else:  # Vermelho
        prioridade = posDisponivelVer
        fallback = posDisponivelAzul


    for posicao in prioridade:
        if posicao["livre"]:
            posicao["livre"] = False
            pos = posicao["pos"]
            break


    if not pos:
        print("Sem posição na cor correta, usando fallback...")
        
        for posicao in fallback:
            if posicao["livre"]:
                posicao["livre"] = False
                pos = posicao["pos"]
                break


    if not pos:
        print("Sem posições disponíveis em nenhuma estante.")
        return
    
    agent.descerBraco(pos[2] + 0.01)
    # Mover na horinzontal
    agent.mover_para_posicao_xyz([pos[0], None, None])
    # Mover na vertical
    agent.mover_para_posicao_xyz([None, pos[1] + 0.055, None])

    time.sleep(1)
    agent.abrirGarra()
    time.sleep(2)

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

while True:
    if client.espera_bloco and not segurando_bloco:
        pegarBloco()
        print(f"Bloco pego!")
        client.publicar("/entregador/encomendaColetada", {"status": True})
        time.sleep(1)
        client.espera_bloco = False
        segurando_bloco = True
        
    if segurando_bloco and not guardar_caixa:
        client.publicar("/cam/capture", {"status": True})
        guardar_caixa = True
        
    if guardar_caixa and client.resposta:
        guardarBloco()
        print(f"Bloco guardado!")
        segurando_bloco = False
        guardar_caixa = False
        client.resposta = False
    
    if todas_posicoes_ocupadas():
        client.publicar("/colaboracao/fim", {"status": True}, qos=1)
        print("Todos os blocos Guardados")
        client.desconectar()
        break