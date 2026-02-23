from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import time
import numpy as np

class CoppeliaMobileAgent:
    def __init__(self, caminho, nomes):
        self.caminho = caminho
        self.nomeJuntas = nomes
        
        # variaveis padrão
        self.client = None
        self.sim = None
        
        # Variaveis para o handle
        self.baseRobo = None
        self.juntas = []
        
        self.inicializar()
        
    def inicializar(self):
        self.conectar()
        self.obterBase()
        self.obterJuntas()
    
    # Metodo padrão para realizar a conexão com o CoppeliaSim
    def conectar(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.require('sim')
        
    # Metodos para obter os handles do robo
    def obterBase(self):
        self.baseRobo = self.sim.getObject(self.caminho)
    
    def obterJuntas(self):
        for nome in self.nomeJuntas:
            junta = self.sim.getObject(self.caminho + nome)
            self.juntas.append(junta)
    
    def setVelocidade(self, vel):
        for i in range(len(self.juntas)):
            self.sim.setJointTargetVelocity(self.juntas[i], vel)
            
    def virarRobo(self, vel1, vel2):
        """
        Args:
            vel1 (positivo) e vel2 (negativo): vira dirita
            vel1 (negativo) e vel2 (positivo): vira esquerda
        """
        for i in range(len(self.juntas)):
            vel = vel1 if i % 2 == 0 else vel2
            self.sim.setJointTargetVelocity(self.juntas[i], vel)
            
    def calcularRotacao(self, alpha, beta, gamma):        
        # Casos fixos
        if (alpha, beta, gamma) == (0, 90, 180):
            return 0, (0 * (np.pi / 180))
        elif (alpha, beta, gamma) == (-90, 0, -90):
            return 90, (90 * (np.pi / 180))
        elif (alpha, beta, gamma) == (0, -90, 0):
            return 180, (180 * (np.pi / 180))
        elif (alpha, beta, gamma) == (90, 0, 90):
            return 270, (270 * (np.pi / 180))
        
        # Casos restantes:
        if alpha == -90 and gamma == -90 and beta > 0:
            return 90 - beta, ((90 - beta) * (np.pi / 180))
        elif alpha == -90 and gamma == -90 and beta < 0:
            return 90 + (beta * -1), ((90 + (beta * -1)) * (np.pi / 180))
        elif alpha == 90 and gamma == 90 and beta < 0:
            return 180 + (90 - (beta * -1)), ((180 + (90 - (beta * -1))) * (np.pi / 180))
        elif alpha == 90 and gamma == 90 and beta > 0:
            return 270 + beta, ((270 + beta) * (np.pi / 180))
        
        return -1, -1 
    
    def moverRobo(self, alvo):
        vel_max = 20.0
        vel_min = 15.0
        
        while True:
            posRobot_xyz = self.sim.getObjectPosition(self.baseRobo, -1)
            posRobot = np.array([posRobot_xyz[0], posRobot_xyz[1]])
            
            # Obter orientação
            orientacao = np.array(self.sim.getObjectOrientation(self.baseRobo, -1))
            orientacao = orientacao * 180/np.pi
            orientacao = np.around(orientacao, decimals=0)
            ang, rad = self.calcularRotacao(orientacao[0], orientacao[1], orientacao[2])
            
            diferenca = alvo - posRobot
            distancia = np.linalg.norm(diferenca)
            
            if distancia < 0.09:
                self.setVelocidade(0)
                print("Destino alcançado!")
                break
            
            # Orientacao
            angulo_alvo = np.arctan2(diferenca[1], diferenca[0])
            # Erro angular com correção de descontinuidade
            erro_angular = angulo_alvo - rad
            erro_angular = (erro_angular + np.pi) % (2 * np.pi) - np.pi
            
            #print(f"Angulo alvo: {angulo_alvo * 180/np.pi}\nErro angular: {erro_angular* 180/np.pi}")
            
            # Só anda se estiver bem alinhado (erro pequeno)
            if erro_angular > 0.2:
                self.setVelocidade(0)
                self.virarRobo(-4, 4)
            elif erro_angular < -0.2:
                self.setVelocidade(0)
                self.virarRobo(+4, -4)
            else:
                velocidade = max(vel_min, min(vel_max, distancia * 2))
                self.setVelocidade(-velocidade)
                
            time.sleep(0.5)
    
    def orientarRobo(self, anguloAlvo=90):  
        angRad = (anguloAlvo * (np.pi / 180))
        
        while True:
            orientacao = np.array(self.sim.getObjectOrientation(self.baseRobo, -1))
            orientacao = orientacao * 180/np.pi
            orientacao = np.around(orientacao, decimals=0)
            
            ang, rad = self.calcularRotacao(orientacao[0], orientacao[1], orientacao[2])
            
            erro_angular = angRad - rad
            erro_angular = (erro_angular + np.pi) % (2 * np.pi) - np.pi
            
            if erro_angular > 0.001:
                self.setVelocidade(0)
                self.virarRobo(-4, +4)
            elif erro_angular < -0.001:
                self.setVelocidade(0)
                self.virarRobo(+4, -4)
            else: 
                self.setVelocidade(0)
                break
      
    def getPos(self, path):
        objeto = self.getObjeto(path)
        return self.sim.getObjectPosition(objeto, -1)
    
    def getObjeto(self, path):
        return self.sim.getObject(path)