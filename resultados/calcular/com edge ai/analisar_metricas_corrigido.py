import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
import glob

# Configurações de estilo para os gráficos
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

base_dir = '/home/kelton/Documentos/resultados/calcular/'

# =============================================================================
# PARTE 1: Comparação metricas_esp.csv (v2, v3, cnn_autoral/local)
# =============================================================================
print("--- Iniciando Análise 1: metricas_esp.csv (v2, v3, autoral local) ---")
scenarios_esp = {
    'MobileNet V2': os.path.join(base_dir, 'v2'),
    'MobileNet V3': os.path.join(base_dir, 'v3'),
    'CNN Autoral (Local)': os.path.join(base_dir, 'cnn_autoral/local')
}

results_esp = []
all_data_esp = []

for name, path in scenarios_esp.items():
    csv_file = os.path.join(path, 'metricas_esp.csv')
    if not os.path.exists(csv_file):
        print(f"Aviso: Arquivo não encontrado - {csv_file}")
        continue
    try:
        df = pd.read_csv(csv_file)
        
        # Calcular latência: timestamp_logger - timestamp_envio
        df['latencia_real_ms'] = (df['timestamp_logger'] - df['timestamp_envio']) * 1000.0
        
        latencias = df['latencia_real_ms'].values
        N = len(latencias)
        
        if N > 0:
            latencia_mediana = np.median(latencias)
            latencia_media = np.mean(latencias)
            
            # Cálculo do Jitter (desvio padrão)
            jitter = np.sqrt(np.mean((latencias - latencia_media)**2))
            
            results_esp.append({
                'Cenário': name,
                'N_Medições': N,
                'Latência_Mediana_ms': round(latencia_mediana, 2),
                'Jitter_ms': round(jitter, 2)
            })
            
            df['Cenário'] = name
            all_data_esp.append(df[['Cenário', 'timestamp_envio', 'latencia_real_ms']])
    except Exception as e:
        print(f"Erro ao processar {name}: {e}")

df_results_esp = pd.DataFrame(results_esp)
print(df_results_esp.to_string(index=False))
df_results_esp.to_csv(os.path.join(base_dir, 'resumo_esp_v2_v3_local.csv'), index=False)

if all_data_esp:
    df_all_esp = pd.concat(all_data_esp, ignore_index=True)
    
    # Plot - metricas esp
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    sns.barplot(data=df_results_esp, x='Cenário', y='Latência_Mediana_ms', ax=ax1, hue='Cenário', legend=False, palette='Blues_d')
    ax1.set_title('Mediana da Latência ESP')
    ax1.set_ylabel('Latência Mediana (ms)')
    
    for i, v in enumerate(df_results_esp['Latência_Mediana_ms']):
        ax1.text(i, v + 2, str(v), ha='center')

    sns.barplot(data=df_results_esp, x='Cenário', y='Jitter_ms', ax=ax2, hue='Cenário', legend=False, palette='Reds_d')
    ax2.set_title('Jitter ESP')
    ax2.set_ylabel('Jitter (ms)')
    
    for i, v in enumerate(df_results_esp['Jitter_ms']):
        ax2.text(i, v + 1, str(v), ha='center')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'grafico_esp_comparativo.png'), dpi=300)

# =============================================================================
# PARTE 2: Análise por Tópicos (resultados_*.csv em local, edison, aws)
# =============================================================================
print("\n--- Iniciando Análise 2: Resultados por Tópicos da CNN Autoral ---")
scenarios_topicos = {
    'Local': os.path.join(base_dir, 'cnn_autoral/local'),
    'Edison': os.path.join(base_dir, 'cnn_autoral/edison'),
    'AWS': os.path.join(base_dir, 'cnn_autoral/aws')
}

all_topic_data = []

for cenario, path in scenarios_topicos.items():
    arquivos_resultados = glob.glob(os.path.join(path, 'resultados_*.csv'))
    
    for arquivo in arquivos_resultados:
        try:
            df = pd.read_csv(arquivo)
            if 'Topico' in df.columns and 'Latencia_ms' in df.columns:
                df['Cenário'] = cenario
                all_topic_data.append(df[['Cenário', 'Topico', 'Latencia_ms']])
        except Exception as e:
            print(f"Erro lendo {arquivo}: {e}")

if not all_topic_data:
    print("Nenhum dado de tópicos encontrado nas pastas especificadas.")
    exit()

df_topics = pd.concat(all_topic_data, ignore_index=True)

# Calcular Mediana e Jitter agrupado por Cenário e Topico
resultados_topicos = []

for (cenario, topico), group in df_topics.groupby(['Cenário', 'Topico']):
    latencias = group['Latencia_ms'].values
    N = len(latencias)
    
    if N > 0:
        latencia_mediana = np.median(latencias)
        latencia_media = np.mean(latencias)
        
        # Jitter é a raiz da média das diferenças quadradas (desvio padrão)
        jitter = np.sqrt(np.mean((latencias - latencia_media)**2))
        
        resultados_topicos.append({
            'Cenário': cenario,
            'Tópico': topico,
            'N_Medições': N,
            'Latência_Mediana_ms': round(latencia_mediana, 2),
            'Jitter_ms': round(jitter, 2)
        })

df_resumo_topicos = pd.DataFrame(resultados_topicos)

# Ordenar para ficar bonito: Local, Edison, AWS
df_resumo_topicos['Cenário_Cat'] = pd.Categorical(df_resumo_topicos['Cenário'], categories=['Local', 'Edison', 'AWS'], ordered=True)
df_resumo_topicos = df_resumo_topicos.sort_values(['Tópico', 'Cenário_Cat']).drop('Cenário_Cat', axis=1)

print("\nResultados por Tópico e Cenário:")
print(df_resumo_topicos.to_string(index=False))
df_resumo_topicos.to_csv(os.path.join(base_dir, 'resumo_topicos_cnn_autoral.csv'), index=False)

# Plotando gráficos para a Parte 2
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# Mediana da Latência por Tópico
sns.barplot(data=df_resumo_topicos, x='Tópico', y='Latência_Mediana_ms', hue='Cenário', ax=ax1, palette='viridis')
ax1.set_title('Mediana da Latência por Tópico (CNN Autoral)')
ax1.set_ylabel('Latência Mediana (ms)')
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
ax1.set_yscale('log') # Eixo log se a AWS for muito maior que os demais
ax1.set_ylabel('Latência Mediana (ms - Log Scale)')

# Jitter por Tópico
sns.barplot(data=df_resumo_topicos, x='Tópico', y='Jitter_ms', hue='Cenário', ax=ax2, palette='magma')
ax2.set_title('Jitter por Tópico (CNN Autoral)')
ax2.set_ylabel('Jitter (ms)')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
ax2.set_yscale('log')

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'grafico_topicos_comparativo.png'), dpi=300)

print("\nTodos os gráficos e CSVs foram gerados com sucesso.")
