# EdgeBoxAI - Classificação de Imagens com ESP32 (TFLite Micro e MQTT)

Este projeto contém a implementação de um sistema que recebe imagens via MQTT de uma câmera (ou outro publicador), processa localmente no ESP32 usando TensorFlow Lite for Microcontrollers (TFLM) e publica o resultado de volta por MQTT, além de coletar métricas de latência e tempo de inferência.

## 🧠 Modelos de Inteligência Artificial Disponíveis

O projeto foi validado com 3 modelos de classificação distintos, sendo 1 padrão e 2 alternativos:

1. **CNN Autoral** (Padrão)
   * Localização: Já pré-configurado na pasta `main/`.
   * Memória (Arena REAL utilizada): **39.352 bytes**
   * Pode ser executado na memória interna do ESP32 (sem configurações extras de RAM).

2. **MobileNet V3**
   * Localização: Pasta `modelos/`.
   * Memória (Arena REAL utilizada): **170.328 bytes**
   * Requer PSRAM externa.

3. **MobileNet V2**
   * Localização: Pasta `modelos/`.
   * Memória (Arena REAL utilizada): **558.504 bytes**
   * Requer PSRAM externa.

---

## 🔄 Como Alternar os Modelos (Ex: Usando V2 ou V3)

Para utilizar os modelos MobileNet V2 ou V3, é necessário alterar o modelo ativo e o código principal para suportar o novo consumo de ram e novas camadas (ops) matemáticas. Siga os passos:

### Passo 1: Substituir os Arquivos do Modelo
Pegue o arquivo do modelo convertido em C-array (`.cc` e `.h`) dentro da pasta `modelos` respectiva e substitua os arquivos equivalentes na pasta `main`.

### Passo 2: Atualizar o CMakeLists.txt
Se o nome do arquivo do modelo for diferente do padrão `model.cc`, abra o arquivo `main/CMakeLists.txt` e substitua o nome da fonte lá para que o compilador do ESP-IDF consiga enxergar o novo arquivo.

### Passo 3: Substituir o Código Fonte (`main`)
Para os modelos V2 e V3, a arquitetura exige o carregamento do limite de Memória (Tensor Arena) direto na PSRAM, assim como o registro de novas operações de Convolution. 
Você deve **substituir totalmente** o conteúdo de `main/main_functions.cc` pelo conteúdo que está em `codigos2.txt` (localizado na raiz do projeto). 
*Nota: O arquivo `codigos.txt` também na raiz é apenas um backup de segurança do código principal da CNN Autoral original.*

---

## ⚙️ Configurações Obrigatórias para V2 e V3 (Menuconfig)

Como o consumo de RAM dos modelos V2 e V3 vai muito além da memória SRAM interna, você deve habilitar o uso do CI de PSRAM do hardware, bem como expandir a Flash e utilizar uma tabela de partições customizada.

> [!WARNING]
> **Antes de abrir o Menuconfig:** Verifique se, no arquivo `CMakeLists.txt` na raiz do projeto (não o da pasta `main`), existe a linha `idf_build_set_property(MINIMAL_BUILD OFF)`. Caso esteja `ON` ou ausente, ative-a como `OFF`. Caso contrário, o menu virá no formato mínimo, escondendo opções críticas para as etapas abaixo.

Abra o terminal do ESP-IDF e execute:
```bash
idf.py menuconfig
```

### 1. Habilitando e Configurando a PSRAM (Ex: Chip N16R8)
Vá em: `Component config --->` -> `ESP PSRAM --->` (ou busque por PSRAM diretamente).
Configure **exatamente** assim:
* **Support for external, SPI-connected RAM**: Marque `[*]`
* Dentro de **SPI RAM config**:
  * **Type of SPI RAM**: Selecione `Octal Mode PSRAM`
  * **PSRAM Clock Speed**: Se disponível, coloque `80MHz`
  * **PSRAM access method**: Escolha `Make RAM allocatable using heap_caps_malloc` (Isso é o que permite ao comando `MALLOC_CAP_SPIRAM` no código alocar o tensor).

### 2. Configurando a Tabela de Partições
Vá em: `Partition Table --->`
* Em **Partition Table**, mude de `"Single factory app, no OTA"` para `"Custom partition table CSV"`.
* Em **Custom partition table CSV file**, digite o nome do seu arquivo: `partitions.csv`.

### 3. Corrigindo o Tamanho da Flash
Vá em: `Serial flasher config --->`
* Procure por **Flash size**.
* Altere de `2 MB` para `16 MB`.

Após as três modificações, pressione **`S`** para salvar e **`Esc`** para sair do Menuconfig.

---

## 🛠️ Instalação e Execução Inicial

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/EdgeBoxAI.git
cd EdgeBoxAI/esp32
```

### 2️⃣ Configure suas credenciais de Wi-Fi e MQTT
Abra o arquivo `main/main_functions.cc` (ou `codigos2.txt` se for usar V2/V3) e substitua os placeholders genéricos para a sua rede real:

**Wi-Fi:**
```cpp
strcpy((char*)wifi_config.sta.ssid,     "SEU_WIFI_AQUI");
strcpy((char*)wifi_config.sta.password, "SUA_SENHA_AQUI");
```

**MQTT:**
```cpp
cfg.broker.address.uri = "mqtt://SEU_BROKER_MQTT_IP:1883";
cfg.credentials.username = "SEU_USUARIO_MQTT"; // Vazio caso não tenha
cfg.credentials.authentication.password = "SUA_SENHA_MQTT";
```

### 3️⃣ Compile e Grave (Flash)
No terminal ESP-IDF:
```bash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

---

## 📡 Tópicos MQTT do Projeto

| Tópico | Função |
|---|---|
| `/esp/classificar` | Recebe a imagem (bytes) e o Timestamp para start das predições locais. |
| `/colaboracao/fim` | Comando que encerra o client e o loop do ESP32. |
| `/esp/resultado` | Retorna o ID numérico da classe predita. |
| `/esp/metricas` | Publica o relatório do Edge contendo Latência, Nome do Modelo e Tempo de Inferência. |