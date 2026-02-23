from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import time
import numpy as np

class CoppeliaBracoAgent:
    def __init__(self, caminho):
        self.caminho = caminho
        
        # variaveis padrão
        self.client = None
        self.sim = None
        self.simIK = None
        
        # Variaveis para o handle
        self.baseRobo = None
        self.juntas = []
        self.target = None
        
        # Exclusivo para os robos que possuem garra
        self.ikEnv = None
        self.baseGarra = None
        self.active = []
        self.group = []
        self.tip = []
        self.targetIk = []
        
        self.script_handle = None
        
        self.inicializar()
    
    def inicializar(self):
        self.conectar()
        self.obterBase()
        self.obterTarget()
        self.obterGarra()
        self.configurarIK()
    
    # Metodo padrão para realizar a conexão com o CoppeliaSim
    def conectar(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.require('sim')
        self.simIK = self.client.require('simIK')
    
    # Metodos para obter os handles do robo
    def obterBase(self):
        self.baseRobo = self.sim.getObject(self.caminho)
                
    def obterJuntas(self, quant):
        for i in range(quant):
            junta = self.sim.getObject(self.caminho + "/joint", {'index': i})
            self.juntas.append(junta)

    def obterTarget(self):
        self.target = self.sim.getObject(self.caminho + "/target")
    
    def obterScriptHandle(self):
        self.script_handle = self.sim.getScript(
            self.sim.scripttype_childscript,
            self.baseRobo
        )

    def obterGarra(self):
        self.baseGarra = self.sim.getObject(self.caminho + "/ROBOTIQ85")
        for i in range(2):
            self.active.append(self.sim.getObject(self.caminho + f"/ROBOTIQ85/active{i + 1}"))
        
    def configurarIK(self):
        self.ikEnv = self.simIK.createEnvironment()
        
        for i in range(2):
            lado = "L" if i == 0 else "R"
            self.group.append(self.simIK.createGroup(self.ikEnv))
            
            tip_path = f"{self.caminho}/ROBOTIQ85/{lado}closureDummyA"
            target_path = f"{self.caminho}/ROBOTIQ85/{lado}closureDummyB"
            
            self.tip.append(self.sim.getObject(tip_path))
            self.targetIk.append(self.sim.getObject(target_path))
            
            self.simIK.addElementFromScene(
                self.ikEnv, 
                self.group[i], 
                self.baseRobo, 
                self.tip[i], 
                self.targetIk[i], 
                self.simIK.constraint_x+self.simIK.constraint_z
            )
            
    def abrirGarra(self):
        p1 = self.sim.getJointPosition(self.active[0])
        p2 = self.sim.getJointPosition(self.active[1])
        
        if p1 < p2:
            self.sim.setJointTargetVelocity(self.active[0], 0.04)
            self.sim.setJointTargetVelocity(self.active[1], 0.02)
        else:
            self.sim.setJointTargetVelocity(self.active[0], 0.02)
            self.sim.setJointTargetVelocity(self.active[1], 0.04)
        
        self.simIK.handleGroup(self.ikEnv, self.group[0], {"syncWorlds": True})
        self.simIK.handleGroup(self.ikEnv, self.group[1], {"syncWorlds": True})
    
    def fecharGarra(self):
        p1 = self.sim.getJointPosition(self.active[0])
        p2 = self.sim.getJointPosition(self.active[1])
        
        if p1 < p2 - 0.008:
            self.sim.setJointTargetVelocity(self.active[0], -0.01)
            self.sim.setJointTargetVelocity(self.active[1], -0.04)
        else:
            self.sim.setJointTargetVelocity(self.active[0], -0.04)
            self.sim.setJointTargetVelocity(self.active[1], -0.04)
        
        self.simIK.handleGroup(self.ikEnv, self.group[0], {"syncWorlds": True})
        self.simIK.handleGroup(self.ikEnv, self.group[1], {"syncWorlds": True})
    
    def descerBraco(self, z_final, velocidade = 0.001, intervalo = 0.0001):
        nova_pos = self.sim.getObjectPosition(self.target, -1)
        z_atual = nova_pos[2]
        while z_atual > z_final:
            z_atual -= velocidade
            if z_atual < z_final: 
                z_atual = z_final
            
            nova_pos[2] = z_atual
            self.sim.setObjectPosition(self.target, -1, nova_pos)
            time.sleep(intervalo)

    def calcularRotacao(self, alpha, beta, gamma):
        # Quando alpha e beta são diferentes de 0
        
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
        
        # Quando alpha e beta são 0
        
        if (alpha, beta, gamma) == (0, 0, 0):
            return 0, (0 * (np.pi / 180))
        elif (alpha, beta, gamma) == (0, 0, 90):
            return 90, (90 * (np.pi / 180))
        elif (alpha, beta, gamma) == (0, 0, -180) or (alpha, beta, gamma) == (0, 0, 180):
            return 180, (180 * (np.pi / 180))
        elif (alpha, beta, gamma) == (0, 0, -90):
            return 270, (270 * (np.pi / 180))
        
        if alpha == 0 and beta == -0 and gamma > 0 and gamma < 180:
            return gamma, (gamma * (np.pi / 180))
        elif alpha == 0 and beta == 0 and gamma < 0:
            return 180 + (180 - (gamma * -1)), ((180 + (180 - (gamma * -1))) * (np.pi / 180))
        
        return -1, -1 
            
    def subirBraco(self, z_final, velocidade = 0.001, intervalo = 0.0001):
        nova_pos = self.sim.getObjectPosition(self.target, -1)
        z_atual = nova_pos[2]
        while z_atual < z_final:
            z_atual += velocidade
            
            if z_atual > z_final: 
                z_atual = z_final
            
            nova_pos[2] = z_atual
            self.sim.setObjectPosition(self.target, -1, nova_pos)
            time.sleep(intervalo)

    def mover_para_posicao_xyz(self, posicoes, velocidade=0.001, intervalo=0.0001):
        nova_pos = list(self.sim.getObjectPosition(self.target, -1))
        x_atual, y_atual, z_atual = nova_pos
                
        x_alvo, y_alvo, z_alvo = [
            pos if pos is not None else atual
            for pos, atual in zip(posicoes, nova_pos)
        ]
        
        while x_atual != x_alvo or y_atual != y_alvo or z_atual != z_alvo:
            if x_atual != x_alvo:
                if x_atual < x_alvo:
                    x_atual += velocidade
                    if x_atual > x_alvo:
                        x_atual = x_alvo
                else:
                    x_atual -= velocidade
                    if x_atual < x_alvo:
                        x_atual = x_alvo
            if y_atual != y_alvo:
                if y_atual < y_alvo:
                    y_atual += velocidade
                    if y_atual > y_alvo:
                        y_atual = y_alvo
                else:
                    y_atual -= velocidade
                    if y_atual < y_alvo:
                        y_atual = y_alvo
            if z_atual != z_alvo:
                if z_atual < z_alvo:
                    z_atual += velocidade
                    if z_atual > z_alvo:
                        z_atual = z_alvo
                else:
                    z_atual -= velocidade
                    if z_atual < z_alvo:
                        z_atual = z_alvo
                
            nova_pos[0] = x_atual
            nova_pos[1] = y_atual
            nova_pos[2] = z_atual
            self.sim.setObjectPosition(self.target, -1, nova_pos)
            time.sleep(intervalo)
            
    def rotacionar_para_posicao_xyz(self, ang_final, espera, velocidade = 0.5, intervalo = 0.001):
        nova_ori = self.sim.getObjectOrientation(self.target, -1)
        orientacao = np.around(np.degrees(np.array(nova_ori)), decimals=0)
        ang_atual, _ = self.calcularRotacao(orientacao[0], orientacao[1], orientacao[2])
        
        nova_pos = self.sim.getObjectPosition(self.target, -1)
        posEspera = self.sim.getObjectPosition(espera, -1)
        x_atual = nova_pos[0]
        y_atual = nova_pos[1]
        x_alvo = posEspera[0]
        y_alvo = posEspera[1]

        while ang_atual != ang_final or x_atual != x_alvo or y_atual != y_alvo:
            if x_atual != x_alvo:
                if x_atual < x_alvo:
                    x_atual += velocidade * 0.005
                    if x_atual > x_alvo:
                        x_atual = x_alvo
                else:
                    x_atual -= velocidade * 0.005
                    if x_atual < x_alvo:
                        x_atual = x_alvo
                        
            if y_atual != y_alvo:
                if y_atual < y_alvo:
                    y_atual += velocidade * 0.005
                    if y_atual > y_alvo:
                        y_atual = y_alvo
                else:
                    y_atual -= velocidade * 0.005
                    if y_atual < y_alvo:
                        y_atual = y_alvo
                        
            if ang_atual != ang_final:
                if ang_atual > ang_final:
                    ang_atual -= velocidade
                    if ang_atual < ang_final: 
                        ang_atual = ang_final
                    
                if ang_atual < ang_final:
                    ang_atual += velocidade
                    if ang_atual > ang_final: 
                        ang_atual = ang_final
            
            nova_ori[2] = np.radians(ang_atual)
            self.sim.setObjectOrientation(self.target, -1, nova_ori)
            
            nova_pos[0] = x_atual
            nova_pos[1] = y_atual
            self.sim.setObjectPosition(self.target, -1, nova_pos)
            
            time.sleep(intervalo)
            
    def alinharComObjeto(self, obj_path):
        pos_alvo = self.sim.getObjectPosition(self.sim.getObject(obj_path), -1)
        pos_atual = self.sim.getObjectPosition(self.target, -1)
        
        nova_pos = [pos_alvo[0], pos_alvo[1], pos_atual[2]]
        self.sim.setObjectPosition(self.target, -1, nova_pos)
        time.sleep(0.1)
        
    def getPos(self, path):
        objeto = self.getObjeto(path)
        return self.sim.getObjectPosition(objeto, -1)
    
    def getPosicoesRack(self, path, quant):
        posDisponivel = []

        for i in range(quant):
            pos = self.sim.getObjectPosition(self.sim.getObject(path, {'index': i}), -1)
            posDisponivel.append({'pos': pos, 'livre': True})
        
        return posDisponivel

    def getObjeto(self, path):
        return self.sim.getObject(path)
    

    def mover(self, x, y, z, rx, ry, rz):
        args = [self.target, x, y, z, rx, ry, rz]

        try:

            # 2. Chama a função (O Lua vai começar a mover)
            self.sim.callScriptFunction(
                "remoteMoveToPosition",
                self.script_handle,
                args
            )

            print("Aguardando robô chegar na posição...")
            time.sleep(4)

            print("Movimento Finalizado com Sucesso!")
            return True

        except Exception as e:
            print("Erro no mover():", e)
            return False
        
    def corrigirCaixa(self, caixa, posicao_correta):
        # Obtém o handle numérico a partir da string (ex: '/cubo_1')
        handle_caixa = self.sim.getObject(caixa)
        
        # Usa o handle numérico para setar a posição
        self.sim.setObjectPosition(handle_caixa, -1, posicao_correta)
            