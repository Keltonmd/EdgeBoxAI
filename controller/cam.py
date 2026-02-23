from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from MqttAgent import MqttAgent
from CoppeliaSensorAgent import CoppeliaSensorAgent
import cv2
import time
import numpy as np

topicos = ["/cam/capture", "/colaboracao/fim"]
client = MqttAgent("Cam", topicos)

agent = CoppeliaSensorAgent("/visionSensor")

def preprocessar_imagem(img):
    img = cv2.resize(img, (32, 32))
    img = (img - 128).astype(np.int8)
    return img

while True:
    if client.capture: 
        img, resolution = agent.lerIMG()
        img = agent.desenpacotarIMG(img, resolution)
        
        # Pré-processamento da imagem
        img = preprocessar_imagem(img)

        # gerar timestamp em microssegundos
        timestamp = int(time.time() * 1_000_000)

        # converter timestamp para 8 bytes
        timestamp_bytes = timestamp.to_bytes(8, byteorder="little", signed=True)

        # juntar timestamp + imagem
        payload = timestamp_bytes + img.tobytes()

        # enviar
        client.publicar_bytes("/esp/classificar", payload, 0)
        
        client.capture = False
        
    if client.finalizado:
        client.desconectar()
        break
