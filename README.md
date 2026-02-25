# 🤖 EdgeBoxAI

> Arquitetura IoRT multiagente com comunicação MQTT e inferência de visão computacional embarcada no ESP32.

Este projeto propõe, implementa e avalia uma arquitetura de comunicação e colaboração baseada em **mensageria orientada a eventos** para coordenação de **agentes robóticos heterogêneos** em ambiente industrial simulado, incorporando **Edge AI** para apoio à tomada de decisão distribuída.

O sistema integra dois manipuladores robóticos (**Franka Emika Panda** e **UR10**), um robô móvel (**KUKA youBot**) e um dispositivo embarcado (**ESP32-S3-WROOM-1-N16R8**), coordenados pelo protocolo **MQTT** via *broker* **Eclipse Mosquitto** em uma arquitetura de quatro camadas — simulados no **CoppeliaSim EDU v4.10.0**, controlados por scripts **Python**.

> 🎓 **Trabalho de Conclusão de Curso** — Bacharelado em Sistemas de Informação  
> IFNMG – Campus Januária  
> **Autor:** Kelton — keltonm6@gmail.com  
> **Orientador:** Prof. Felipe Augusto Oliveira Mota

---

## 📑 Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Resultados Experimentais](#2-resultados-experimentais)
3. [Pré-requisitos de Hardware](#3-pré-requisitos-de-hardware)
4. [Instalando o ESP-IDF (via Extensão VS Code)](#4-instalando-o-esp-idf-via-extensão-vs-code)
5. [Instalando o CoppeliaSim](#5-instalando-o-coppeliaism)
6. [Instalando o Broker MQTT (Mosquitto)](#6-instalando-o-broker-mqtt-mosquitto)
7. [Configurando o Ambiente Python (Controller)](#7-configurando-o-ambiente-python-controller)
8. [Configurando o Firmware ESP32](#8-configurando-o-firmware-esp32)
9. [Estrutura do Repositório](#9-estrutura-do-repositório)
10. [Modelos de IA Disponíveis](#10-modelos-de-ia-disponíveis)
11. [Alternando entre Modelos](#11-alternando-entre-modelos)
12. [Executando o Projeto Completo](#12-executando-o-projeto-completo)
13. [Tópicos MQTT](#13-tópicos-mqtt)
14. [Dataset e Treinamento](#14-dataset-e-treinamento)

---

## 1. Visão Geral da Arquitetura

O sistema é organizado em **quatro camadas**:

| Camada | Componentes | Responsabilidade |
|---|---|---|
| **Física** | Franka Panda, UR10, youBot, sensores, ESP32 | Execução de ações e interação com o ambiente |
| **Rede** | Wi-Fi 802.11 b/g/n | Conectividade entre os dispositivos |
| **Comunicação** | MQTT + Eclipse Mosquitto | Troca de mensagens (pub/sub) entre agentes |
| **Controle** | Scripts Python + CoppeliaSim ZMQ API | Processamento e orquestração do fluxo operacional |

```
┌─────────────────────────────────────────────────────────────────┐
│                         COMPUTADOR HOST                         │
│                                                                 │
│  ┌──────────────┐    ZMQ     ┌─────────────────────────────┐   │
│  │ CoppeliaSim  │◄──────────►│   Controller (Python)       │   │
│  │  EDU v4.10   │            │                             │   │
│  │  - UR10      │            │  main.py       → orquestra  │   │
│  │  - Franka    │            │  ur10.py       → braço UR10 │   │
│  │  - youBot    │            │  franka.py     → braço Frnk │   │
│  │  - Câmera    │            │  youBot.py     → robô móvel │   │
│  │  - Esteira   │            │  cam.py        → captura img│   │
│  │  - Sensor IR │            │  sensorEsteira.py → IR      │   │
│  └──────────────┘            │  logger_esp.py → métricas   │   │
│                              └──────────────┬──────────────┘   │
│                                             │ MQTT (paho)      │
│  ┌──────────────────────────────────────────▼──────────────┐   │
│  │            Broker Eclipse Mosquitto (porta 1883)         │   │
│  └──────────────────────────────────────────┬──────────────┘   │
└───────────────────────────────────────────  │  ────────────────┘
                                              │ Wi-Fi / MQTT
                                    ┌─────────▼──────────────┐
                                    │   ESP32-S3-WROOM-1      │
                                    │   N16R8 (240 MHz LX7)   │
                                    │                         │
                                    │   TFLite Micro v1.3.5   │
                                    │   CNN Autoral (38.4 KB) │
                                    │   Confiança média: 99.6%│
                                    └────────────────────────┘
```

**Fluxo operacional:**
1. O **sensor infravermelho** detecta uma caixa ao final da esteira e publica um evento MQTT.
2. O **Franka Panda** coleta a caixa e a deposita sobre o **youBot**.
3. O **youBot** transporta a caixa até a zona de atuação do **UR10**.
4. O **UR10** pega a caixa e sinaliza para captura de imagem (`/cam/capture`).
5. O **`cam.py`** captura a imagem do sensor virtual, pré-processa para 32×32 px (int8) e publica os bytes no tópico `/esp/classificar`, com *timestamp* de 8 bytes.
6. O **ESP32** recebe a imagem, executa a inferência com o modelo TFLite embarcado e publica a classe predita em `/esp/resultado` (`0` = Azul, `1` = Vermelho).
7. O **UR10** lê o resultado e armazena a caixa na prateleira correta.
8. Ao encher todas as prateleiras, o sistema publica `/colaboracao/fim` e encerra todos os agentes.

---

## 2. Resultados Experimentais

### 2.1 Desempenho dos Modelos de Classificação

| Modelo | Acurácia (Keras) | Tamanho Normal | Tamanho Inteira | Redução | Arena Real (ESP32) | Requer PSRAM? |
|---|---|---|---|---|---|---|
| **MobileNet V2** | 95,18% | ~8,6 MB | ~2,6 MB | > 69% | 558.504 bytes | ✅ Sim |
| **MobileNet V3 Small** | 93,57% | ~3,6 MB | ~1,2 MB | > 66% | 170.328 bytes | ✅ Sim |
| **CNN Autoral** ⭐ | 93,17% | ~655 KB | ~171 KB | > 73% | **38.400 bytes** | ❌ Não |

> ⭐ **A CNN Autoral foi adotada como modelo definitivo** por seu consumo reduzido de arena (38,4 KB na SRAM interna) e **ausência de erros de classificação** no hardware real, ao contrário das arquiteturas de transferência de aprendizado.

### 2.2 Desempenho da Comunicação (150 ciclos × 3 configurações de broker)

| Configuração do Broker | Latência Mediana | Taxa de Sucesso |
|---|---|---|
| **Local** (mesmo host) | < 25 ms | 100% |
| **Amazon EC2** (nuvem) | > 200 ms | 100% |
| **Intel Edison** (borda) | > 200 ms | 100% |

### 2.3 Sistema Integrado (Edge AI + MQTT)

- **200 operações completas** de classificação em 5 execuções
- **Taxa de sucesso: 100%** nos três ambientes
- **Confiança média: 99,6%**

---

## 3. Pré-requisitos de Hardware

| Componente | Especificação utilizada |
|---|---|
| **ESP32** | ESP32-S3-WROOM-1-N16R8 — Dual-Core Xtensa LX7, 240 MHz |
| **SRAM interna** | 512 KB (suficiente para CNN Autoral) |
| **Flash** | 16 MB |
| **PSRAM** | 8 MB (necessária para MobileNet V2/V3) |
| **Wi-Fi** | 802.11 b/g/n (2,4 GHz) — integrado |
| **Computador host** | Linux (Ubuntu 20.04+ ou Debian 11+) — recomendado |
| **RAM do host** | ≥ 8 GB (CoppeliaSim + Python + broker) |
| **Python** | 3.10 ou superior |
| **Cabo USB** | USB-C ou micro-USB para gravar o ESP32 |

---

## 4. Instalando o ESP-IDF (via Extensão VS Code)

O **ESP-IDF** é a SDK oficial da Espressif e é necessário para compilar e gravar o firmware no ESP32.

> 📺 **Tutorial em vídeo (recomendado):** [Como instalar o ESP-IDF pela extensão do VS Code](https://youtu.be/WpDiva4yoYo?si=4MZFjV5d064e6uZR)

### 4.1 Pré-requisitos do sistema (Ubuntu/Debian)

Antes de instalar a extensão, instale as dependências necessárias no terminal:

```bash
sudo apt update
sudo apt install -y git wget flex bison gperf python3 python3-pip \
  python3-venv cmake ninja-build ccache libffi-dev libssl-dev \
  dfu-util libusb-1.0-0
```

### 4.2 Instalar o VS Code

Se ainda não tiver o VS Code instalado:

```bash
# Baixar e instalar via .deb
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
sudo apt update
sudo apt install -y code
```

Ou baixe diretamente em: [https://code.visualstudio.com/](https://code.visualstudio.com/)

### 4.3 Instalar a Extensão ESP-IDF no VS Code

1. Abra o **VS Code**.
2. Acesse o painel de extensões (`Ctrl+Shift+X`).
3. Pesquise por **`ESP-IDF`**.
4. Instale a extensão oficial: **"ESP-IDF"** publicada pela **Espressif Systems**.

### 4.4 Configurar o ESP-IDF pela extensão

1. Após instalar a extensão, pressione `Ctrl+Shift+P` para abrir a paleta de comandos.
2. Digite e selecione: **`ESP-IDF: Configure ESP-IDF Extension`**.
3. Na tela de configuração que abrirá, escolha: **`EXPRESS`** (instalação guiada).
4. Selecione a versão do ESP-IDF. Para este projeto, selecione **v5.2.x** ou superior.
5. Escolha o diretório de instalação (padrão: `~/esp/esp-idf`) e clique em **Install**.

> ⚠️ A instalação baixa o compilador `xtensa-esp-elf-gcc` e demais ferramentas. Pode levar de 5 a 15 minutos dependendo da sua conexão. Aguarde a barra de progresso concluir.

### 4.5 Verificar a instalação

Após a instalação, na barra de status inferior do VS Code você verá o ícone do ESP-IDF com a versão selecionada (ex: `ESP-IDF v5.2.3`). Clique nele para abrir o terminal ESP-IDF integrado.

Execute no terminal integrado:
```bash
idf.py --version
```

A saída esperada é algo como `ESP-IDF v5.2.3`.

### 4.6 Abrir o projeto ESP32 no VS Code

1. No VS Code: `File → Open Folder` → selecione a pasta `EdgeBoxAI/esp32/`.
2. A extensão detectará automaticamente o projeto ESP-IDF pelo `CMakeLists.txt`.
3. Na barra inferior, selecione o **chip alvo**: clique em `Set Espressif Device Target` e escolha **`esp32s3`**.
4. Selecione a **porta serial** do seu ESP32 (ex: `/dev/ttyUSB0`).

### 4.7 Permissão para a porta serial (se necessário)

Se aparecer erro de permissão ao acessar a porta USB:

```bash
sudo usermod -aG dialout $USER
# Faça logout e login novamente para aplicar
```

Para confirmar a porta do ESP32:
```bash
ls /dev/tty*
# Geralmente /dev/ttyUSB0 ou /dev/ttyACM0
```

---

## 5. Instalando o CoppeliaSim

O **CoppeliaSim EDU** é o simulador de robótica onde a cena com todos os robôs é executada. Este projeto foi desenvolvido e validado na **versão 4.10.0**.

### 5.1 Download

1. Acesse: [https://www.coppeliarobotics.com/downloads](https://www.coppeliarobotics.com/downloads)
2. Baixe a versão **CoppeliaSim Edu** (gratuita) para **Linux** — arquivo `.tar.xz`.

### 5.2 Extrair

```bash
mkdir -p ~/Applications
tar -xf CoppeliaSim_Edu_V4_10_0_*.tar.xz -C ~/Applications/
```

### 5.3 Executar

```bash
~/Applications/CoppeliaSim_Edu_V4_10_0_*/coppeliaSim.sh
```

O simulador abrirá. Para carregar a cena do projeto:

**`File → Open Scene`** → navegue até `EdgeBoxAI/cenario/cenario_novo.ttt`

> **Importante:** O CoppeliaSim deve estar **aberto com a cena carregada** *antes* de executar o `main.py` do controller. O script Python aciona o *play* da simulação automaticamente via API ZMQ.

### 5.4 Plugin ZMQ Remote API

A API ZMQ já vem incluída no CoppeliaSim 4.4+. Para verificar, acesse `Tools → Console` no simulador e confirme a linha:
```
Plugin 'ZMQ Remote API': load succeeded.
```

---

## 6. Instalando o Broker MQTT (Mosquitto)

O **MQTT** é o protocolo de mensagens que conecta todos os agentes. O **Eclipse Mosquitto** é o *broker* que gerencia as mensagens.

### 6.1 Instalar

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

### 6.2 Criar usuário com senha

O projeto usa autenticação por usuário e senha:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd kelton
# Informe a senha: Projeto2025
```

> 💡 Para usar um usuário/senha diferente, atualize também no arquivo `controller/MqttAgent.py` (linha `self.client.username_pw_set(...)`) e no firmware ESP32 (`main/main_functions.cc`).

### 6.3 Criar arquivo de configuração

```bash
sudo nano /etc/mosquitto/conf.d/projeto.conf
```

Cole o conteúdo abaixo e salve (`Ctrl+O`, `Enter`, `Ctrl+X`):

```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### 6.4 Iniciar o serviço

```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto   # inicia automaticamente com o sistema
sudo systemctl status mosquitto   # deve mostrar "Active: active (running)"
```

### 6.5 Testar a conexão

Em um terminal, assine um tópico:
```bash
mosquitto_sub -h localhost -u kelton -P Projeto2025 -t "teste"
```

Em outro terminal, publique uma mensagem:
```bash
mosquitto_pub -h localhost -u kelton -P Projeto2025 -t "teste" -m "Olá!"
```

Se a mensagem aparecer no primeiro terminal, o broker está funcionando corretamente.

---

## 7. Configurando o Ambiente Python (Controller)

Os scripts em `controller/` rodam no computador host e coordenam os robôs via CoppeliaSim (ZMQ) e MQTT.

### 7.1 Criar ambiente virtual

```bash
cd EdgeBoxAI/controller
python3 -m venv .venv
source .venv/bin/activate
```

O prompt do terminal mudará para `(.venv) ...`.

### 7.2 Instalar dependências

```bash
pip install -r requirements.txt
```

| Pacote | Versão | Função |
|---|---|---|
| `coppeliasim_zmqremoteapi_client` | 2.0.4 | API Python para controlar o CoppeliaSim via ZMQ |
| `paho-mqtt` | 2.1.0 | Cliente MQTT (pub/sub) |
| `pyzmq` | 27.0.0 | Comunicação ZeroMQ com o simulador |
| `numpy` | 2.3.1 | Cálculos numéricos e manipulação de arrays de imagem |
| `cbor` | 1.0.0 | Serialização compacta de dados |
| `pandas` | — | Salva dados de latência em CSV |
| `openpyxl` | — | Exportação de dados em Excel |

### 7.3 Configurar o endereço do broker MQTT

Abra `controller/MqttAgent.py` e ajuste o parâmetro `broker`:

```python
# Linha 13 — altere para o IP ou hostname do seu broker
def __init__(self, id: str, topicos_mqtt: list, broker: str = "debian.local", port: int = 1883):
```

Se o broker rodar na mesma máquina do controller, use `"localhost"` ou `"127.0.0.1"`.

Para descobrir o IP do seu computador:
```bash
hostname -I
```

---

## 8. Configurando o Firmware ESP32

### 8.1 Configurar Wi-Fi e MQTT no código

Abra `esp32/main/main_functions.cc` no VS Code e localize os trechos abaixo para substituir pelos seus dados reais:

```cpp
// ── Wi-Fi ──────────────────────────────────────────────────────
strcpy((char*)wifi_config.sta.ssid,     "NOME_DA_SUA_REDE");
strcpy((char*)wifi_config.sta.password, "SENHA_DA_SUA_REDE");

// ── MQTT ───────────────────────────────────────────────────────
// Coloque o IP do computador onde o Mosquitto está rodando
cfg.broker.address.uri = "mqtt://192.168.1.XXX:1883";
cfg.credentials.username = "kelton";
cfg.credentials.authentication.password = "Projeto2025";
```

### 8.2 Selecionar o chip e compilar (via VS Code)

1. Na barra inferior do VS Code, clique em **`Set Espressif Device Target`** → selecione **`esp32s3`**.
2. Clique no ícone de **compilação** (⚙️ *Build*) na barra inferior, ou pressione `Ctrl+Shift+P` → **`ESP-IDF: Build your project`**.

A primeira compilação baixa o componente `espressif/esp-tflite-micro` e pode demorar **5–15 minutos**.

### 8.3 Gravar (flash) no ESP32

1. Conecte o ESP32 via USB.
2. Selecione a porta serial na barra inferior do VS Code.
3. Clique no ícone **⚡ Flash** (ou `Ctrl+Shift+P` → **`ESP-IDF: Flash your project`**).
4. Para monitorar os logs em tempo real após o flash: **`ESP-IDF: Monitor your project`**.

Após o flash você verá no monitor serial:
```
I (xxxx) wifi: connected to ap NOME_DA_SUA_REDE
I (xxxx) MQTT: Connected to broker
I (xxxx) MAIN: Aguardando imagem no topico /esp/classificar ...
```

---

## 9. Estrutura do Repositório

```
EdgeBoxAI/
│
├── cenario/
│   └── cenario_novo.ttt          # Cena CoppeliaSim com todos os robôs e sensores
│
├── controller/                   # Scripts Python — rodam no host
│   ├── main.py                   # Ponto de entrada: inicia simulação e todos os agentes
│   ├── MqttAgent.py              # Cliente MQTT com pub/sub e medição de latência
│   ├── CoppeliaBracoAgent.py     # Controla braços robóticos (UR10, Franka) via IK
│   ├── CoppeliaMobileAgent.py    # Controla o robô móvel (youBot)
│   ├── CoppeliaSensorAgent.py    # Lê sensores de visão do CoppeliaSim
│   ├── ur10.py                   # Lógica do UR10: pegar caixa → classificar → guardar
│   ├── youBot.py                 # Lógica do robô móvel transportador
│   ├── franka.py                 # Lógica do Franka: coletar da esteira → entregar
│   ├── cam.py                    # Captura imagem do sensor e envia bytes ao ESP32
│   ├── sensorEsteira.py          # Monitora sensor infravermelho da esteira
│   ├── logger_esp.py             # Coleta e salva métricas publicadas pelo ESP32 (CSV)
│   └── requirements.txt          # Dependências Python
│
├── esp32/                        # Firmware ESP32 (ESP-IDF v5.5.2)
│   ├── main/
│   │   ├── main.cpp              # Entry point do firmware (chama setup/loop)
│   │   ├── main_functions.cc     # Wi-Fi, MQTT, pré-processamento e inferência TFLite
│   │   ├── main_functions.h      # Header da lógica principal
│   │   ├── model.h               # Header do modelo TFLite
│   │   ├── model_data.cc         # CNN Autoral convertida em array C (modelo padrão)
│   │   ├── CMakeLists.txt        # Build config do componente main
│   │   └── idf_component.yml     # Dependência: espressif/esp-tflite-micro v1.3.5
│   ├── modelos/                  # Modelos alternativos (MobileNet V2/V3) em array C
│   ├── CMakeLists.txt            # Build config do projeto
│   ├── partitions.csv            # Tabela de partições customizada (Flash 16 MB)
│   ├── codigos.txt               # Backup do main_functions.cc (CNN Autoral)
│   └── codigos2.txt              # Versão do main_functions.cc para MobileNet V2/V3
│
├── modelos/                      # Modelos treinados exportados
│   ├── model.keras               # CNN Autoral (Keras, 93,17% acurácia)
│   ├── modeloV2.keras            # MobileNet V2 (Keras, 95,18%)
│   ├── modeloV3.keras            # MobileNet V3 Small (Keras, 93,57%)
│   ├── modelo_Normal.tflite      # CNN Autoral — sem quantização (~655 KB)
│   ├── modelo_Dinamica.tflite    # CNN Autoral — quantização dinâmica
│   ├── modelo_Inteira.tflite     # CNN Autoral — quantização inteira (~171 KB)
│   ├── v2_*.tflite               # MobileNet V2 nas 3 variantes de quantização
│   ├── v3_*.tflite               # MobileNet V3 nas 3 variantes de quantização
│   └── tflite_to_cc.sh           # Script: converte .tflite → array C (.cc/.h) via xxd
│
├── Dataset/
│   ├── 0_Azul/                   # 540 imagens de objetos predominantemente azuis
│   ├── 1_Vermelho/               # 540 imagens de objetos predominantemente vermelhos
│   └── 2_background/             # 576 imagens de fundo (sem objeto de interesse)
│
└── Treinamento/                  # Notebooks/scripts de treinamento (Google Colab)
```

---

## 10. Modelos de IA Disponíveis

Três arquiteturas foram treinadas e validadas para classificação de imagens 32×32 px em três classes: **Azul (0)**, **Vermelho (1)** e **Background (2)**.

| Modelo | Acurácia | Arena Real | PSRAM? | TFLite Inteira |
|---|---|---|---|---|
| **CNN Autoral** ⭐ | 93,17% | 38.400 bytes (SRAM) | ❌ Não | ~171 KB |
| **MobileNet V3 Small** | 93,57% | 170.328 bytes (PSRAM) | ✅ Sim | ~1,2 MB |
| **MobileNet V2** | 95,18% | 558.504 bytes (PSRAM) | ✅ Sim | ~2,6 MB |

Cada modelo existe em 3 variantes de quantização (pasta `modelos/`):
- **Normal** — ponto flutuante, sem quantização (referência)
- **Dinâmica** — pesos em int8, ativações em float32
- **Inteira** — pesos, ativações, entradas e saídas em int8 (melhor para microcontroladores)

---

## 11. Alternando entre Modelos

### 11.1 CNN Autoral (padrão — já configurado)

Nenhuma ação necessária. O modelo já está em `esp32/main/model_data.cc`.

### 11.2 Usando MobileNet V2 ou V3

#### Passo 1 — Gerar os arquivos C a partir do `.tflite`

```bash
cd modelos/
bash tflite_to_cc.sh
```

Isso usa o comando `xxd` para gerar os arquivos `v3_Inteira.cc` e `v3_Inteira.h` (por exemplo).

#### Passo 2 — Copiar os arquivos para `main/`

```bash
# Exemplo com MobileNet V3 quantização inteira
cp modelos/v3_Inteira.cc esp32/main/model_data.cc
cp modelos/v3_Inteira.h  esp32/main/model.h
```

#### Passo 3 — Substituir o `main_functions.cc` pela versão PSRAM

```bash
cp esp32/codigos2.txt esp32/main/main_functions.cc
```

> ⚠️ Reconfigure os dados de Wi-Fi e MQTT no novo arquivo (seção 8.1).

#### Passo 4 — Configurar PSRAM e Flash via menuconfig

> **Antes de abrir o menuconfig**, verifique se no `esp32/CMakeLists.txt` existe:
> ```cmake
> idf_build_set_property(MINIMAL_BUILD OFF)
> ```
> Se estiver `ON`, mude para `OFF`. Caso contrário, o menu ocultará opções críticas.

No VS Code, pressione `Ctrl+Shift+P` → **`ESP-IDF: SDK Configuration editor (Menuconfig)`**, ou no terminal ESP-IDF integrado:

```bash
idf.py menuconfig
```

**a) Habilitar PSRAM** — navegue em `Component config → ESP PSRAM`:
- **Support for external, SPI-connected RAM**: `[*]` (marque)
- **Type of SPI RAM**: `Octal Mode PSRAM`
- **PSRAM Clock Speed**: `80 MHz`
- **PSRAM access method**: `Make RAM allocatable using heap_caps_malloc`

**b) Tabela de Partições Customizada** — navegue em `Partition Table`:
- **Partition Table**: `Custom partition table CSV`
- **Custom partition table CSV file**: `partitions.csv`

**c) Tamanho da Flash** — navegue em `Serial flasher config`:
- **Flash size**: `16 MB`

Pressione **`S`** para salvar e **`Esc`** para sair.

---

## 12. Executando o Projeto Completo

Siga **exatamente esta ordem**:

### ① Iniciar o Broker MQTT

```bash
sudo systemctl start mosquitto
```

### ② Ligar o ESP32 e monitorar (opcional)

Conecte o ESP32 via USB. No VS Code: `Ctrl+Shift+P` → **`ESP-IDF: Monitor your project`**.  
O ESP32 conectará ao Wi-Fi e ao broker automaticamente.

### ③ Abrir o CoppeliaSim e carregar a cena

```bash
~/Applications/CoppeliaSim_Edu_V4_10_0_*/coppeliaSim.sh
```

`File → Open Scene → EdgeBoxAI/cenario/cenario_novo.ttt`

> **Não clique em *Play* ainda.** O script Python iniciará a simulação automaticamente.

### ④ Executar o Controller Python

```bash
cd EdgeBoxAI/controller
source .venv/bin/activate
python3 main.py
```

O `main.py` irá:
1. Conectar ao CoppeliaSim via ZMQ e acionar o *play* (`sim.startSimulation()`)
2. Lançar todos os agentes em subprocessos paralelos:

```
Iniciando franka.py...
Iniciando sensorEsteira.py...
Iniciando youBot.py...
Iniciando ur10.py...
Iniciando cam.py...
Iniciando logger_esp.py...
```

A simulação roda até que todas as caixas sejam classificadas e armazenadas. Ao final, os dados de latência são salvos automaticamente em arquivos `resultados_<AGENTE>.csv` na pasta `controller/`.

---

## 13. Tópicos MQTT

| Tópico | Publicador | Assinante | Conteúdo / Função |
|---|---|---|---|
| `/esp/classificar` | `cam.py` | ESP32 | 8 bytes de timestamp + bytes da imagem 32×32 int8 |
| `/esp/resultado` | ESP32 | `ur10.py` | JSON com `{"resultado": 0}` (0=Azul) ou `{"resultado": 1}` (Vermelho) |
| `/esp/metricas` | ESP32 | `logger_esp.py` | JSON com latência, nome do modelo e tempo de inferência |
| `/cam/capture` | `ur10.py` | `cam.py` | Sinaliza para capturar e enviar imagem ao ESP32 |
| `/entregador/coletaDisponivel` | `franka.py` | `ur10.py` | Caixa disponível para coleta pelo UR10 |
| `/entregador/encomendaColetada` | `ur10.py` | `franka.py` | UR10 confirmou coleta da caixa |
| `/bloco/disponivel` | `youBot.py` | `ur10.py` | youBot chegou ao ponto de entrega com a caixa |
| `/colaboracao/fim` | `ur10.py` | Todos | Encerra todos os agentes (todas as prateleiras cheias) |

---

## 14. Dataset e Treinamento

### Dataset

O conjunto de dados foi coletado especificamente para este projeto:

| Classe | Pasta | Quantidade |
|---|---|---|
| 0 — Azul | `Dataset/0_Azul/` | 540 imagens |
| 1 — Vermelho | `Dataset/1_Vermelho/` | 540 imagens |
| 2 — Background | `Dataset/2_background/` | 576 imagens |
| **Total** | — | **1.656 imagens** |

Divisão: **70% treino / 15% validação / 15% teste** (amostragem estratificada).

### Treinamento

Os modelos foram treinados no **Google Colaboratory** com:
- **TensorFlow / Keras 2.17.0** + Python 3.10
- **GPU NVIDIA T4** (aceleração de hardware)
- Entrada: imagens **32×32 px RGB**

As arquiteturas MobileNet V2 e V3 usaram **fine-tuning** em duas fases; a CNN Autoral foi treinada do zero.

### Conversão para TFLite e array C

Após treinar, os modelos `.keras` são convertidos para `.tflite` com o TFLite Converter (versão 2.17.0) e então convertidos para array C com a ferramenta `xxd`:

```bash
cd modelos/
bash tflite_to_cc.sh
```

---

## 📄 Citação

Se este projeto foi útil para sua pesquisa, considere citar o TCC:

```
Autor: Kelton
Título: Arquitetura IoRT Multiagente com Comunicação MQTT e Inferência Embarcada no ESP32
Instituição: IFNMG – Campus Januária
Curso: Bacharelado em Sistemas de Informação
Orientador: Prof. Felipe Augusto Oliveira Mota
Ano: 2026
```

## 📝 Licença

Este projeto está licenciado sob a MIT License. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✉️ Contato

**Kelton** — keltonm6@gmail.com  
Orientador: **Prof. Felipe Augusto Oliveira Mota**  
IFNMG – Instituto Federal do Norte de Minas Gerais, Campus Januária
