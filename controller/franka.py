from CoppeliaBracoAgent import CoppeliaBracoAgent
from MqttAgent import MqttAgent
import time

agent = CoppeliaBracoAgent("/Franka")
topicos = [("/bloco/disponivel", 1), "/entregador/pontoRecebimento", "/colaboracao/fim"]
segurando_bloco = False
client = MqttAgent("Franka", topicos)
bloco = None

def pegarBloco():
    global bloco
    agent.abrirGarra()
    time.sleep(1)
    
    bloco = client.cubo
    altura = 0.02
    
    # Alinha o target horizontalmente com o bloco
    agent.alinharComObjeto(bloco)
    
    # z Final
    z_bloco = agent.getPos(bloco)[2] + altura
    agent.descerBraco(z_bloco)
    
    agent.fecharGarra()
    time.sleep(2)
    
    # Sobe de volta à altura anterior (posição de início do movimento)
    altura_inicial = agent.getPos("/pontoEspera")[2]
    agent.subirBraco(altura_inicial)
    
def entregarBloco():
    global bloco
    pos_Entrega = agent.getPos("/youBot/cuboPos")
    
    agent.mover_para_posicao_xyz([pos_Entrega[0], pos_Entrega[1], None])
    agent.alinharComObjeto("/youBot/cuboPos")
    agent.descerBraco(pos_Entrega[2] + 0.02, velocidade=0.001)
    time.sleep(2)
    agent.abrirGarra()
    time.sleep(1)

    agent.corrigirCaixa(bloco, [pos_Entrega[0], pos_Entrega[1], pos_Entrega[2]])
    
    posEspera = agent.getPos("/pontoEspera")
    agent.subirBraco(posEspera[2])
    agent.mover_para_posicao_xyz([posEspera[0], posEspera[1], None])

agent.abrirGarra()
while True:
    if client.espera_bloco and not segurando_bloco:
        pegarBloco()
        print(f"Bloco pego!")
        client.espera_bloco = False
        segurando_bloco = True
        
    if client.destino_livre and segurando_bloco:
        entregarBloco()
        print(f"Bloco entregue!")
        client.publicar("/entregador/encomendaDisponibilizada", {'status': True})
        client.destino_livre = False
        segurando_bloco = False
    
    if client.finalizado:
        client.desconectar()
        break