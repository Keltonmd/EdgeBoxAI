import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import glob

sns.set(style="whitegrid")

base_dir = '/home/kelton/Documentos/resultados/calcular/'

# ============================
# FUNÇÕES AUXILIARES
# ============================
def combinar_resultados(pasta, ambiente):
    """Combina todos os resultados_*.csv de uma pasta."""
    dfs = []
    arquivos = glob.glob(os.path.join(pasta, 'resultados_*.csv'))
    for arquivo in arquivos:
        try:
            df_temp = pd.read_csv(arquivo)
            if 'Topico' in df_temp.columns and 'Latencia_ms' in df_temp.columns:
                df_temp['Ambiente'] = ambiente
                dfs.append(df_temp[['Topico', 'Latencia_ms', 'Ambiente']])
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def calcular_offset_relogio(pasta):
    """Calcula o offset de relógio do ESP a partir de metricas_esp.csv.
    Offset = timestamp_envio (epoch) - timestamp_recebido (millis desde boot).
    Retorna o offset mediano em segundos."""
    caminho = os.path.join(pasta, 'metricas_esp.csv')
    if not os.path.exists(caminho):
        return None
    df = pd.read_csv(caminho)
    offsets = df['timestamp_envio'] - df['timestamp_recebido']
    return np.median(offsets)


def extrair_esp_classificar(pasta, ambiente):
    """Extrai latência do tópico /esp/classificar a partir do metricas_esp.csv.
    Latência = (timestamp_logger - timestamp_envio) * 1000 ms."""
    caminho = os.path.join(pasta, 'metricas_esp.csv')
    if not os.path.exists(caminho):
        return pd.DataFrame()
    df = pd.read_csv(caminho)
    latencias = (df['timestamp_logger'] - df['timestamp_envio']) * 1000.0
    return pd.DataFrame({
        'Topico': '/esp/classificar',
        'Latencia_ms': latencias,
        'Ambiente': ambiente
    })


# ============================================================
# GRÁFICO 1: Tempo Mediano de Inferência (V2 vs V3 vs Autoral)
# ============================================================
print("=== Gráfico 1: Tempo Mediano de Inferência ===")

modelos_esp = {
    'MobileNet V2': os.path.join(base_dir, 'v2', 'metricas_esp.csv'),
    'MobileNet V3': os.path.join(base_dir, 'v3', 'metricas_esp.csv'),
    'CNN Autoral':  os.path.join(base_dir, 'cnn_autoral', 'local', 'metricas_esp.csv'),
}

dados_inferencia = []
for nome, caminho in modelos_esp.items():
    df = pd.read_csv(caminho)
    dados_inferencia.append({
        'Modelo': nome,
        'Mediana Inferência (ms)': round(np.median(df['tempo_inferencia_ms']), 2),
        'N': len(df)
    })

df_inf = pd.DataFrame(dados_inferencia)
print(df_inf.to_string(index=False))

plt.figure(figsize=(8, 5))
ax = sns.barplot(data=df_inf, x='Modelo', y='Mediana Inferência (ms)',
                 hue='Modelo', legend=False, palette='coolwarm')
ax.set_title('Tempo Mediano de Inferência por Modelo (Edge AI)', fontsize=14)
ax.set_ylabel('Tempo de Inferência (ms)')
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
for i, row in df_inf.iterrows():
    ax.text(i, row['Mediana Inferência (ms)'] + 2,
            f"{row['Mediana Inferência (ms)']} ms", ha='center', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'grafico1_inferencia_modelos.png'), dpi=300)
plt.close()
print("Salvo: grafico1_inferencia_modelos.png\n")

# ============================================================
# GRÁFICOS 2 e 3: Mediana de Latência e Jitter (Local vs Edison vs AWS)
# ============================================================
print("=== Gráfico 2 e 3: Latência e Jitter por Tópico (Local, Edison, AWS) ===")

cenarios = {
    'Local':  os.path.join(base_dir, 'cnn_autoral', 'local'),
    'Edison': os.path.join(base_dir, 'cnn_autoral', 'edison'),
    'AWS':    os.path.join(base_dir, 'cnn_autoral', 'aws'),
}

partes = []
for ambiente, pasta in cenarios.items():
    # Tópicos dos resultados_*.csv
    df_res = combinar_resultados(pasta, ambiente)
    if not df_res.empty:
        # Corrigir /esp/resultado: subtrair o offset de relógio
        offset = calcular_offset_relogio(pasta)
        if offset is not None:
            mask = df_res['Topico'] == '/esp/resultado'
            # Latencia_ms armazenada = (epoch_recv - millis_send) em ms
            # Latencia corrigida = Latencia_ms - offset_ms
            offset_ms = offset * 1000.0
            df_res.loc[mask, 'Latencia_ms'] = df_res.loc[mask, 'Latencia_ms'] - offset_ms
            print(f"  {ambiente}: offset de relógio = {offset:.2f}s, corrigindo {mask.sum()} medições de /esp/resultado")
        partes.append(df_res)

    # Tópico /esp/classificar extraído do metricas_esp.csv
    df_classificar = extrair_esp_classificar(pasta, ambiente)
    if not df_classificar.empty:
        partes.append(df_classificar)

df_geral = pd.concat(partes, ignore_index=True)

if df_geral.empty:
    raise ValueError("Nenhum dado válido foi carregado.")

# Calcular métricas agrupadas por Ambiente e Tópico
metricas = df_geral.groupby(['Ambiente', 'Topico'])['Latencia_ms'].agg(
    Latencia_Mediana_ms='median',
    Jitter_ms='std',
    Amostras='count'
).reset_index()

# Arredondar para 2 casas decimais
metricas['Latencia_Mediana_ms'] = metricas['Latencia_Mediana_ms'].round(2)
metricas['Jitter_ms'] = metricas['Jitter_ms'].round(2)

metricas['Ambiente'] = pd.Categorical(metricas['Ambiente'],
                                       categories=['Local', 'Edison', 'AWS'], ordered=True)
metricas = metricas.sort_values(['Topico', 'Ambiente'])

print("\nMétricas completas:")
print(metricas.to_string(index=False))
metricas.to_csv(os.path.join(base_dir, 'metricas_topicos_final.csv'), index=False)
print("Salvo: metricas_topicos_final.csv\n")

# --- Gráfico 2: Mediana da Latência ---
plt.figure(figsize=(16, 7))
ax = sns.barplot(data=metricas, x='Topico', y='Latencia_Mediana_ms',
                 hue='Ambiente', palette='Set2')
ax.set_title('Mediana da Latência por Tópico e Cenário (CNN Autoral)', fontsize=14)
ax.set_ylabel('Latência Mediana (ms)')
ax.set_xlabel('Tópico')
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
plt.xticks(rotation=45, ha='right')
plt.legend(title='Cenário')
plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'grafico2_mediana_latencia.png'), dpi=300)
plt.close()
print("Salvo: grafico2_mediana_latencia.png")

# --- Gráfico 3: Jitter ---
plt.figure(figsize=(16, 7))
ax = sns.barplot(data=metricas, x='Topico', y='Jitter_ms',
                 hue='Ambiente', palette='Set2')
ax.set_title('Jitter por Tópico e Cenário (CNN Autoral)', fontsize=14)
ax.set_ylabel('Jitter (ms)')
ax.set_xlabel('Tópico')
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
plt.xticks(rotation=45, ha='right')
plt.legend(title='Cenário')
plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'grafico3_jitter.png'), dpi=300)
plt.close()
print("Salvo: grafico3_jitter.png")

print("\n✅ Todos os 3 gráficos e o CSV de métricas foram gerados com sucesso!")
