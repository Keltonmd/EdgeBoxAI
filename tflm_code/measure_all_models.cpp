// measure_all_models.cpp
// Medir arena real de vários modelos com resolvers distintos

#include <cstdio>
#include <cstring>
#include <iostream>
#include <fstream>
#include <cstdint>  // Necessário para uint8_t
#include <cstddef>  // Necessário para size_t

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"

// Inclua aqui seus headers gerados (arrays .tflite)
#include "modelo_Normal_model.h"
#include "modelo_Inteira_model.h"
#include "modelo_Dinamica_model.h"

#include "v2_Normal_model.h"
#include "v2_Inteira_model.h"
#include "v2_Dinamica_model.h"

#include "v3_Normal_model.h"
#include "v3_Inteira_model.h"
#include "v3_Dinamica_model.h"

// -------------------------------------------------
// Configurações da arena
// -------------------------------------------------
constexpr int kTensorArenaSize = 1024 * 1024; 
static uint8_t tensor_arena[kTensorArenaSize];

tflite::ErrorReporter* error_reporter = nullptr;

// -------------------------------------------------
// Tipos
// -------------------------------------------------
using ResolverFn = void(*)(tflite::MicroMutableOpResolver<25>&); 

// -------------------------------------------------
// Construir resolvers
// -------------------------------------------------

// Resolver para "modelo" (v1 - Custom CNN Simples)
void build_resolver_v1(tflite::MicroMutableOpResolver<25>& resolver) {
    resolver.AddConv2D();
    resolver.AddLeakyRelu();
    resolver.AddMaxPool2D();
    resolver.AddReshape();
    resolver.AddFullyConnected();
    resolver.AddLogistic(); // Sigmoid
    resolver.AddQuantize();
    resolver.AddDequantize();
    resolver.AddMul();
    resolver.AddSoftmax();
}

// Resolver para v2 e v3 (MobileNetV2/V3 requerem mais ops)
void build_resolver_v2v3(tflite::MicroMutableOpResolver<25>& resolver) {
    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();
    resolver.AddRelu6();          // Comum em MobileNetV2
    resolver.AddHardSwish();      // ESSENCIAL PARA V3 (MobileNetV3)
    resolver.AddAdd();
    resolver.AddMean();           // GlobalAveragePooling
    resolver.AddPad();            // Algumas convs usam PAD explícito
    resolver.AddFullyConnected();
    resolver.AddLeakyRelu();
    resolver.AddLogistic();       // Sigmoid
    resolver.AddReshape();
    resolver.AddQuantize();
    resolver.AddDequantize();
    resolver.AddMul();
    resolver.AddSoftmax();
    resolver.AddConcatenation();  // Às vezes usado em skip connections
}

// -------------------------------------------------
// Estrutura com informações do modelo
// -------------------------------------------------
struct ModeloInfo {
    const char* nome;
    const unsigned char* data;
    ResolverFn build_resolver;
};

// -------------------------------------------------
// Lista de modelos
// -------------------------------------------------
ModeloInfo modelos[] = {
    // v1
    { "modelo_Normal",   modelo_Normal_tflite,    build_resolver_v1 },
    { "modelo_Inteira",  modelo_Inteira_tflite,   build_resolver_v1 },
    { "modelo_Dinamica", modelo_Dinamica_tflite,  build_resolver_v1 },

    // v2
    { "v2_Normal",   v2_Normal_tflite,    build_resolver_v2v3 },
    { "v2_Inteira",  v2_Inteira_tflite,   build_resolver_v2v3 },
    { "v2_Dinamica", v2_Dinamica_tflite,  build_resolver_v2v3 },

    // v3
    { "v3_Normal",   v3_Normal_tflite,    build_resolver_v2v3 },
    { "v3_Inteira",  v3_Inteira_tflite,   build_resolver_v2v3 },
    { "v3_Dinamica", v3_Dinamica_tflite,  build_resolver_v2v3 }
};

constexpr int NUM_MODELOS = sizeof(modelos) / sizeof(modelos[0]);

// -------------------------------------------------
// Função que mede um modelo
// -------------------------------------------------
size_t medir_modelo(const ModeloInfo& info) {
    printf("\n----------------------------------------\n");
    printf("Medindo modelo: %s\n", info.nome);
    printf("----------------------------------------\n");

    const tflite::Model* model = tflite::GetModel(info.data);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        printf("ERRO: Schema version mismatch.\n");
        return 0;
    }

    memset(tensor_arena, 0, kTensorArenaSize);

    tflite::MicroMutableOpResolver<25> resolver;
    info.build_resolver(resolver);

    tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, kTensorArenaSize, error_reporter);

    TfLiteStatus status = interpreter.AllocateTensors();
    if (status != kTfLiteOk) {
        printf("ERRO: AllocateTensors() falhou para %s\n", info.nome);
        return 0;
    }

    size_t arena_used = interpreter.arena_used_bytes();
    
    // Tentativa segura de pegar tensores
    TfLiteTensor* input = interpreter.input(0);
    TfLiteTensor* output = interpreter.output(0);
    
    unsigned in_bytes = input ? (unsigned)input->bytes : 0;
    unsigned out_bytes = output ? (unsigned)output->bytes : 0;

    printf("Arena usada (bytes): %u\n", (unsigned)arena_used);
    printf("Input tensor bytes: %u\n", in_bytes);
    printf("Output tensor bytes: %u\n", out_bytes);

    // Retorna para imprimir no CSV final
    return arena_used;
}

// -------------------------------------------------
// Main
// -------------------------------------------------
int main() {
    static tflite::MicroErrorReporter micro_error_reporter;
    error_reporter = &micro_error_reporter;

    printf("======= Medição de arena para múltiplos modelos =======\n");
    printf("modelo,arena_used_bytes,input_bytes,output_bytes\n");

    // CSV em arquivo
    std::ofstream csv("arena_results.csv");
    if (!csv.is_open()) {
        printf("ERRO: não foi possível criar arena_results.csv\n");
        return 1;
    }

    // Cabeçalho do CSV
    csv << "modelo,arena_bytes,input_bytes,output_bytes\n";

    struct Result {
        const char* nome;
        size_t arena;
        size_t in_size;
        size_t out_size;
        bool error;
    } resultados[NUM_MODELOS];

    for (int i = 0; i < NUM_MODELOS; ++i) {
        size_t used = medir_modelo(modelos[i]);

        resultados[i].nome  = modelos[i].nome;
        resultados[i].arena = used;
        resultados[i].error = (used == 0);

        if (used > 0) {
            const tflite::Model* m = tflite::GetModel(modelos[i].data);
            tflite::MicroMutableOpResolver<25> r;
            modelos[i].build_resolver(r);

            tflite::MicroInterpreter interp(
                m, r, tensor_arena, kTensorArenaSize, error_reporter);

            if (interp.AllocateTensors() == kTfLiteOk) {
                resultados[i].in_size  = interp.input(0)->bytes;
                resultados[i].out_size = interp.output(0)->bytes;
            } else {
                resultados[i].in_size = 0;
                resultados[i].out_size = 0;
            }
        } else {
            resultados[i].in_size = 0;
            resultados[i].out_size = 0;
        }
    }

    printf("\n======= CSV FINAL =======\n");

    for (int i = 0; i < NUM_MODELOS; ++i) {
        if (resultados[i].error) {
            printf("%s,ERROR,0,0\n", resultados[i].nome);
            csv << resultados[i].nome << ",ERROR,0,0\n";
        } else {
            printf("%s,%u,%u,%u\n",
                   resultados[i].nome,
                   (unsigned)resultados[i].arena,
                   (unsigned)resultados[i].in_size,
                   (unsigned)resultados[i].out_size);

            csv << resultados[i].nome << ","
                << resultados[i].arena << ","
                << resultados[i].in_size << ","
                << resultados[i].out_size << "\n";
        }
    }

    csv.close();

    printf("\nArquivo 'arena_results.csv' gerado com sucesso!\n");
    printf("Medicoes finalizadas.\n");

    return 0;
}