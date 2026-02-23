from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import subprocess
import time

client = RemoteAPIClient()
sim = client.require('sim')
sim.startSimulation()

# Lista dos seus scripts
scripts = [
    "franka.py",
    "sensorEsteira.py",
    "youBot.py",
    "ur10.py",
    "cam.py",
    "logger_esp.py"
]

processos = []

# Iniciar todos em subprocessos
for script in scripts:
    print(f"Iniciando {script}...")
    p = subprocess.Popen(["python3", script])
    processos.append(p)
    time.sleep(1) 

for p in processos:
    p.wait()

sim.stopSimulation()