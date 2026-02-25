import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ============================
# CONFIGURAÇÃO
# ============================
SLA_LIMITE = 200  # Limite de latência em ms para SLA

arquivos_locais = [
    'Local/resultados_Franka.csv',
    'Local/resultados_youBot.csv',
    'Local/resultados_UR10.csv',
    'Local/resultados_sensor.csv'
]

arquivos_nuvem = [
    'Nuvem/resultados_FrankaNuvem.csv',
    'Nuvem/resultados_youBotNuvem.csv',
    'Nuvem/resultados_UR10Nuvem.csv',
    'Nuvem/resultados_sensorNuvem.csv'
]

arquivos_edison = [
    'Nuvem/resultados_FrankaNuvem.csv',
    'Nuvem/resultados_youBotNuvem.csv',
    'Nuvem/resultados_UR10Nuvem.csv',
    'Nuvem/resultados_sensorNuvem.csv'
]

# ============================
# FUNÇÃO PARA COMBINAR CSVs
# ============================
def combinar_arquivos_csv(lista_de_arquivos, ambiente):
    dfs = []
    colunas_necessarias = {'Topico', 'Latencia_ms'}

    for arquivo in lista_de_arquivos:
        if not os.path.exists(arquivo):
            print(f"⚠ Arquivo não encontrado: {arquivo}")
            continue

        try:
            df_temp = pd.read_csv(arquivo)

            if not colunas_necessarias.issubset(df_temp.columns):
                print(f"⚠ Arquivo ignorado por falta de colunas: {arquivo}")
                continue

            df_temp['Ambiente'] = ambiente
            dfs.append(df_temp)

        except Exception as e:
            print(f"❌ Erro ao ler {arquivo}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ============================
# CARREGAR DADOS
# ============================
df_local = combinar_arquivos_csv(arquivos_locais, 'Local')
df_nuvem = combinar_arquivos_csv(arquivos_nuvem, 'Nuvem')
df_edison = combinar_arquivos_csv(arquivos_edison, 'Edison')
df_geral = pd.concat([df_local, df_nuvem, df_edison], ignore_index=True)

if df_geral.empty:
    raise ValueError("Nenhum dado válido foi carregado.")

# ============================
# CALCULAR MÉTRICAS
# ============================

metricas = df_geral.groupby(['Ambiente', 'Topico'])['Latencia_ms'].agg(
    Latencia_Mediana_ms='median',
    Latencia_Media_ms='mean',
    Jitter_ms='std',
    Latencia_P95_ms=lambda x: np.percentile(x, 95),
    Latencia_Max_ms='max',
    Latencia_Min_ms='min',
    Amostras='count'
).reset_index()

# ============================
# SALVAR RESULTADO
# ============================
metricas.to_csv('metricas_completas_latencia_jitter.csv', index=False)
print("📄 Métricas salvas em: metricas_completas_latencia_jitter.csv")
print(metricas)


sns.set(style="whitegrid")

# ============================
# Gráfico 1: Mediana de Latência
# ============================
plt.figure(figsize=(12,6))
ax = sns.barplot(data=metricas, x="Topico", y="Latencia_Mediana_ms",
                 hue="Environment", palette="Set2")
ax.set_title("Mediana de Latência por Tópico e Ambiente")
ax.set_ylabel("Latência Mediana (ms)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("mediana_latencia.png")
plt.close()

# ============================
# Gráfico 2: Latência Média
# ============================
plt.figure(figsize=(12,6))
ax = sns.barplot(data=metricas, x="Topico", y="Latencia_Media_ms",
                 hue="Environment", palette="Set2")
ax.set_title("Latência Média por Tópico e Ambiente")
ax.set_ylabel("Latência Média (ms)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("media_latencia.png")
plt.close()

# ============================
# Gráfico 3: Jitter
# ============================
plt.figure(figsize=(12,6))
ax = sns.barplot(data=metricas, x="Topico", y="Jitter_ms",
                 hue="Environment", palette="Set2")
ax.set_title("Jitter (Desvio-Padrão) por Tópico e Ambiente")
ax.set_ylabel("Jitter (ms)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("jitter_latencia.png")
plt.close()

# ============================
# Gráfico 4: P95
# ============================
plt.figure(figsize=(12,6))
ax = sns.barplot(data=metricas, x="Topico", y="Latencia_P95_ms",
                 hue="Environment", palette="Set2")
ax.set_title("Latência P95 por Tópico e Ambiente")
ax.set_ylabel("P95 (ms)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("p95_latencia.png")
plt.close()

# ============================
# Gráfico 5: Boxplot da Distribuição
# ============================
plt.figure(figsize=(16,8))
sns.boxplot(
    data=df_geral,
    x="Topico",
    y="Latencia_ms",
    hue="Ambiente",
    palette="Set2",
    showfliers=True,   # ou False para ignorar outliers
    width=0.6,
    dodge=True
)
plt.title("Distribuição da Latência por Tópico e Ambiente", fontsize=16)
plt.ylabel("Latência (ms)")
plt.xlabel("Tópico MQTT")
plt.xticks(rotation=45, ha="right")

# Limite superior para zoom visual, opcional
plt.ylim(0, 500)  # ajusta para focar na maioria dos dados

plt.tight_layout()
plt.savefig("boxplot_latencia_ajustado.png")
plt.show()