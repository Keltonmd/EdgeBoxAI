from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import numpy as np


class CoppeliaSensorAgent:
    def __init__(self, caminho):
        self.caminho = caminho
    
        # variaveis padrão
        self.client = None
        self.sim = None
        
        self.baseSensor = None
        
        self.inicializador()
    
    def inicializador(self):    
        self.conectar()
        self.obterBase()
    
    def conectar(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.require('sim')
        
    def obterBase(self):
        self.baseSensor = self.sim.getObject(self.caminho)
        
    def leitura(self):
        result, _, _, _, _ = self.sim.readProximitySensor(self.baseSensor)
        return bool(result)
    
    def handleObjeto(self, caminho):
        return self.sim.getObject(caminho)
    
    def lerIMG(self):
        img, resolution = self.sim.getVisionSensorImg(self.baseSensor)
        return img, resolution

    def desenpacotarIMG(self, img, resolution):
        img = self.sim.unpackUInt8Table(img)
        img = np.array(img, dtype=np.uint8)
        img = np.reshape(img, (resolution[1], resolution[0], 3))
        img = np.flip(img, 0)
        
        return img