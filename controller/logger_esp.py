import paho.mqtt.client as mqtt
import json
import time
import pandas as pd
import os

ARQUIVO = "metricas_esp.csv"
dados = []
rodando = True  # Variável que controla o encerramento

def on_message(client, userdata, msg):
    global dados, rodando

    # Se for métricas da ESP
    if msg.topic == "/esp/metricas":
        try:
            payload = json.loads(msg.payload.decode())
            print("[METRICA] Recebido")
            dados.append({
                "timestamp_logger": time.time(),
                "id_publicador": payload["id_publicador"],
                "modelo": payload["modelo"],
                "timestamp_envio": payload["timestamp_envio"],
                "timestamp_recebido": payload["timestamp_recebido"],
                "latencia_ms": payload["latencia_ms"],
                "tempo_inferencia_ms": payload["tempo_inferencia_ms"],
                "resultado": payload["resultado"]
            })
        except Exception as e:
            print(f"Erro no processamento: {e}")

    # Se for fim da colaboração
    elif msg.topic == "/colaboracao/fim":
        print("\n[FIM] Sinal de finalização recebido.")
        rodando = False # APENAS sinaliza para sair do loop principal

def salvar():
    global dados
    if not dados:
        print("[SALVAR] Nenhum dado para salvar.")
        return

    print(f"[AGUARDE] Salvando {len(dados)} registros...")
    df = pd.DataFrame(dados)
    existe = os.path.exists(ARQUIVO)
    
    df.to_csv(ARQUIVO, mode="a", header=not existe, index=False)
    print("[OK] Arquivo salvo com sucesso.")
    dados.clear()

# ======================
# MQTT setup
# ======================
client = mqtt.Client()
client.username_pw_set("kelton", "Projeto2025")
client.on_message = on_message

client.connect("debian.local", 1883)
client.subscribe("/esp/metricas")
client.subscribe("/colaboracao/fim")

# Inicia o loop em background (igual aos seus agentes de robô)
client.loop_start()
print("Aguardando métricas da ESP... (O script fechará sozinho ao terminar)")

# O script fica "preso" aqui até a variável rodando virar False no on_message
try:
    while rodando:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n[AVISO] Interrupção manual.")

# --- SÓ CHEGA AQUI QUANDO RECEBE O FIM OU CTRL+C ---
client.loop_stop()  # Para o loop MQTT com segurança
salvar()            # Salva os dados de vez
client.disconnect() # Desconecta do broker
print("Conexão encerrada. Script finalizado.")