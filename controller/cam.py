from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from MqttAgent import MqttAgent
from CoppeliaSensorAgent import CoppeliaSensorAgent
import cv2
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
        client.publicar_bytes("/esp/classificar", img.tobytes(), 0)
        client.capture = False
        
    if client.finalizado:
        client.desconectar()
        break
