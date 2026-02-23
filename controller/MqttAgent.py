import paho.mqtt.client as mqtt
from types import MappingProxyType
import json
import time
import os
import pandas as pd

class MqttAgent:
    # multiagent.ddns.net
    # ip: ip do edison
    # ip 10.73.186.74
    # ip: 192.168.1.223
    def __init__(self, id: str, topicos_mqtt: list, broker: str = "debian.local", port: int = 1883):
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        
        # Definindo autenticação
        self.client.username_pw_set(username="kelton", password="Projeto2025")
        
        # Estados internos
        self._espera_bloco = False
        self._destino_livre = False
        self._finalizado = False
        self._iniciar_entrega = False
        self._iniciar_coleta = False
        self._cubo = None
        self._capture = False
        self._resposta = False
        self._resultado = None
        
        # Mapeamento de tópicos dos agentes
        self.topic_map = MappingProxyType({
            "/entregador/coletaDisponivel": self.tratar_coleta_disponivel,
            "/bloco/disponivel": self.tratar_coleta_disponivel,
            "/entregador/pontoRecebimento": self.tratar_ponto_recebimento,
            "/entregador/encomendaDisponibilizada": self.tratar_encomenda_disponibilizada,
            "/entregador/encomendaColetada": self.tratar_encomenda_coletada,
            "/colaboracao/fim": self.tratar_fim_colaboracao,
            "/cam/capture": self.tratar_solicitar_imagem,
            "/esp/resultado": self.tratar_resultado_recebido
        })
        
        self.client.connect(broker, port, 60)
        
        self.subscribe(topicos_mqtt)
        self.iniciar()
        self.dados_latencia = []
        self.id_agente = id
    
    def subscribe(self, topics: list[tuple | str]):
        for topico in topics:
            if not isinstance(topico, tuple):
                self.client.subscribe(topico)                
            else:
                self.client.subscribe(topico[0], qos=topico[1])
    
    def on_message(self, client, userdata, msg):
        timestamp_recepcao = time.time()

        try:
            payload_str = msg.payload.decode("utf-8").strip()
            payload = json.loads(payload_str)

        except json.JSONDecodeError:
            print(f"[MQTT] Payload inválido (não é JSON): {msg.payload}")
            return

        except Exception as e:
            print(f"[MQTT] Erro ao decodificar payload: {e}")
            return
        
        # Registrar latência se timestamp_envio presente no payload
        if isinstance(payload, dict) and "timestamp_envio" in payload:
            timestamp_envio = payload.pop("timestamp_envio")
            latencia = (timestamp_recepcao - timestamp_envio) * 1000  # em ms
            
            self.dados_latencia.append({
                'Robo_Publicador': payload.get('id_publicador', 'Desconhecido'),
                'Robo_Assinante': self.id_agente,
                'Topico': msg.topic,
                'Latencia_ms': latencia
            })
            
        handler = self.topic_map.get(msg.topic)
        if handler:
            handler(payload)
        else:
            print(f"[MQTT] Aviso: tópico não tratado: {msg.topic}")
    
    def iniciar(self):
        self.client.loop_start()
        
    def publicar(self, canal: str, msg: dict, qos: int = 0):
        msg["timestamp_envio"] = time.time()
        msg["id_publicador"] = self.id_agente
        msg = json.dumps(msg)
        self.client.publish(canal, payload=msg, qos=qos)
        
    def publicar_bytes(self, canal: str, msg: bytes, qos: int = 0):
        self.client.publish(canal, payload=msg, qos=qos)
    
    def salvar_resultados(self):
        if not self.dados_latencia:
            print(f"[MQTT] Nenhum dado de latência para o agente '{self.id_agente}'.")
            return
        
        df = pd.DataFrame(self.dados_latencia)
        nome_arquivo = f"resultados_{self.id_agente}.csv"
        
        arquivo_existe = os.path.exists(nome_arquivo)
        
        df.to_csv(
            nome_arquivo,
            mode="a",
            header=not arquivo_existe,
            index=False
        )
        
        self.dados_latencia.clear()
        
        print(f"[MQTT] Dados de latência adicionados em '{nome_arquivo}'")
    
    def desconectar(self):
        print("[MQTT] Desconectando do broker...")
        self.salvar_resultados()
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Desconectado.")
        
    # Tratamentos
    def tratar_coleta_disponivel(self, payload):
        self.espera_bloco = True
        print("[MQTT] Bloco disponível, iniciando coleta.")
        
        if "cubo" in payload:
            self._cubo = payload["cubo"]

    def tratar_ponto_recebimento(self, payload):
        self.destino_livre = True
        print("[MQTT] Destino disponível, iniciando entrega.")

    def tratar_encomenda_disponibilizada(self, payload):
        self.iniciar_entrega = True
        print("[MQTT] Recebido: Bloco recebido. Indo entregar.")

    def tratar_encomenda_coletada(self, payload):
        self.iniciar_coleta = True
        print("[MQTT] Recebido: Bloco entregue. Indo coletar.")

    def tratar_fim_colaboracao(self, payload):
        self.finalizado = True
        print("[MQTT] Colaboração Finalizada.")
        
    def tratar_solicitar_imagem(self, payload):
        self.capture = True
        print("[MQTT] Solicitação de captura de imagem recebida.")
        
    def tratar_resultado_recebido(self, payload):
        self.resultado = payload["resultado"]
        self.resposta = True
        print(f"[MQTT] Resultado recebido: {payload}")
        print(f"[MQTT] resposta: {self.resposta}")
    
    # Fim dos Tratamentos
    
    @property
    def espera_bloco(self):
        return self._espera_bloco

    @espera_bloco.setter
    def espera_bloco(self, valor: bool):
        self._espera_bloco = valor

    @property
    def destino_livre(self):
        return self._destino_livre

    @destino_livre.setter
    def destino_livre(self, valor: bool):
        self._destino_livre = valor

    @property
    def finalizado(self):
        return self._finalizado

    @finalizado.setter
    def finalizado(self, valor: bool):
        self._finalizado = valor

    @property
    def iniciar_entrega(self):
        return self._iniciar_entrega

    @iniciar_entrega.setter
    def iniciar_entrega(self, valor: bool):
        self._iniciar_entrega = valor

    @property
    def iniciar_coleta(self):
        return self._iniciar_coleta

    @iniciar_coleta.setter
    def iniciar_coleta(self, valor: bool):
        self._iniciar_coleta = valor
        
    @property
    def cubo(self):
        return self._cubo
    
    @property
    def capture(self):
        return self._capture
    
    @capture.setter
    def capture(self, valor: bool):
        self._capture = valor
        
    @property
    def resposta(self):
        return self._resposta
    
    @resposta.setter
    def resposta(self, valor: bool):
        self._resposta = valor
        
    @property
    def resultado(self):
        return self._resultado
    
    @resultado.setter
    def resultado(self, valor):
        self._resultado = valor