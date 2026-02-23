from CoppeliaSensorAgent import CoppeliaSensorAgent
from MqttAgent import MqttAgent
import time

ultimoEstado = False
agent = CoppeliaSensorAgent("/proximitySensor")

client = MqttAgent("sensor", ["/colaboracao/fim"])
cont = 1
while True:
    detectado = agent.leitura()
    
    if detectado and not ultimoEstado:
        time.sleep(3)
        print("[SENSOR] Bloco detectado. Publicando...")
        client.publicar("/bloco/disponivel", msg={"cubo": f"/cubo_{cont}"}, qos=1)
        ultimoEstado = True
        cont += 1
    elif not detectado:
        ultimoEstado = False
        
    if client.finalizado:
        client.desconectar()
        break
    
    time.sleep(0.1)