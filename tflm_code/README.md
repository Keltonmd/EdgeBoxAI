# Medição de Arena de Memória - TensorFlow Lite Micro

Este diretório (`tflm_code/`) contém o código e a estrutura necessários para **medir a estimativa de arena (memória RAM)** consumida pelos modelos `.tflite` quando executados no TensorFlow Lite Micro (TFLM).

Para garantir compatibilidade com o ESP32 e com a versão utilizada no treinamento, toda a compilação utilizará a versão **v2.6.5** do TensorFlow.

---

## 📁 Estrutura Esperada do Diretório

Após seguir os passos abaixo, seu diretório deverá ficar assim:

```text
tflm_code/
├── measure_all_models.cpp   # Código principal em C++ que faz as medições
├── Makefile                 # Automação de compilação
├── README.md                # Este passo a passo
├── tf_micro/                # Contém a biblioteca do TFLM gerada manualmente
└── modelos/                 # Contém os arrays em C/C++ dos modelos gerados
```

---

## 🚀 Passo a Passo Completo

### 1. Preparar a Biblioteca TFLM (v2.6.5)

Para conseguir compilar o código de medição (`measure_all_models.cpp`), o Makefile busca a biblioteca autônoma do TensorFlow Lite Micro. Você precisará extraí-la do repositório oficial do TensorFlow:

1. Baixe o repositório do TensorFlow exatamente na branch `v2.6.5`:
   ```bash
   git clone --depth 1 --branch v2.6.5 https://github.com/tensorflow/tensorflow.git tf_src
   cd tf_src
   ```

2. Utilize o script embutido no TF para gerar uma árvore (pasta standalone) do TFLM:
   ```bash
   python3 tensorflow/lite/micro/tools/project_generation/create_tflm_tree.py -e hello_world /tmp/tflm_out
   ```

3. Mova os arquivos gerados para dentro da subpasta `tf_micro` do seu projeto EdgeBoxAI:
   ```bash
   # Mude para a pasta tflm_code
   cd /caminho/para/EdgeBoxAI/tflm_code/
   
   # Traga os arquivos pra cá
   cp -r /tmp/tflm_out/* ./tf_micro/
   ```

4. Agora, compile a biblioteca do TFLM internamente:
   ```bash
   cd ./tf_micro
   make -j$(nproc)
   ```
   *Após rodar o make, ele deve gerar uma biblioteca estática, geralmente localizada num caminho como `tensorflow/lite/micro/tools/make/gen/linux_x86_64/lib/libtensorflow-microlite.a` (já configurado no Makefile do `measure_models`).*

---

### 2. Gerar os Arrays `.cc` dos Modelos

Antes de testar a memória, os modelos em `.tflite` precisam ser encapsulados em C/C++.

1. Use o script já existente no seu repositório:
   ```bash
   cd /caminho/para/EdgeBoxAI/modelos
   ./tflite_to_cc.sh
   ```
   *(Ele roda o `xxd` nas imagens iterativamente).*

2. Acesse as pastas onde o script jogou a saída (`/cc` e `/h`) e transfira todos os arquivos gerados para a pasta `tflm_code/modelos/`:
   ```bash
   cp /caminho/de/saida/cc/*.cc /caminho/para/EdgeBoxAI/tflm_code/modelos/
   cp /caminho/de/saida/h/*.h /caminho/para/EdgeBoxAI/tflm_code/modelos/
   ```

> Verifique no código fonte de `measure_all_models.cpp` se os nomes dos `#include` batem exatamente com o que você acabou de gerar.

---

### 3. Compilar e Executar os Cálculos de Arena

Tudo pronto! Com a biblioteca construída e os modelos importados:

1. Vá para a raiz de `tflm_code/` e utilize nosso Makefile:
   ```bash
   cd /caminho/para/EdgeBoxAI/tflm_code
   make clean
   make
   ```

2. Em seguida, execute o avaliador:
   ```bash
   ./measure_models
   ```

**O que vai acontecer:**
O programa carregará cara modelo em `modelos/`, instanciará os tensores individualmente usando o alocador do TensorFlow v2.6.5 e irá reportar (via terminal) a memória crua alocada. No final, será gerado automaticamente o arquivo **`arena_results.csv`** contendo os cálculos de bytes exigidos por cada versão quantizada do seu modelo!
