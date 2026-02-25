import pandas as pd
import matplotlib.pyplot as plt
import os

locale_pt = True

def parse_float(val):
    if isinstance(val, str):
        return float(val.replace(',', '.'))
    return float(val)

def format_float(val, decimals=2):
    s = f"{val:.{decimals}f}"
    if locale_pt:
        return s.replace('.', ',')
    return s

def get_col(df, cols):
    for c in cols:
        if c in df.columns:
            return c
    return df.columns[3] if len(df.columns) > 3 else None

def process_table_a(base_path):
    envs = ['Local', 'Edison', 'Nuvem']
    topics = [
        ('/bloco/disponivel', 'resultados_sensor.csv', 'resultados_sensor_Edison.csv', 'resultados_sensorNuvem.csv'),
        ('/cam/capture', 'resultados_Cam.csv', 'resultados_Cam_Edison.csv', 'resultados_CamNuvem.csv'),
        ('/colaboracao/fim', 'resultados_UR10.csv', 'resultados_UR10_Edison.csv', 'resultados_UR10Nuvem.csv'),
        ('/entregador/coletaDisponivel', 'resultados_Franka.csv', 'resultados_Franka_Edison.csv', 'resultados_FrankaNuvem.csv'),
        ('/entregador/encomendaColetada', 'resultados_youBot.csv', 'resultados_youBot_Edison.csv', 'resultados_youBotNuvem.csv'),
        ('/entregador/encomendaDisponibilizada', 'resultados_youBot.csv', 'resultados_youBot_Edison.csv', 'resultados_youBotNuvem.csv'),
        ('/entregador/pontoRecebimento', 'resultados_youBot.csv', 'resultados_youBot_Edison.csv', 'resultados_youBotNuvem.csv')
    ]
    
    rows = []
    for env in envs:
        for t_name, f_local, f_edison, f_nuvem in topics:
            if env == 'Local':
                file_name = f_local
            elif env == 'Edison':
                file_name = f_edison
            else:
                file_name = f_nuvem
                
            path = os.path.join(base_path, 'sem edge ai', env, file_name)
            if not os.path.exists(path):
                # Fallback to try another name based on what we found
                continue
                
            try:
                df = pd.read_csv(path)
                topico_col = get_col(df, ['Topico', 'Tópico'])
                df_topic = df[df[topico_col] == t_name]
                if len(df_topic) == 0:
                    continue
                
                val_col = get_col(df, ['Latencia_ms', 'Latencia (ms)'])
                latencies = df_topic[val_col].apply(parse_float)
                median = latencies.median()
                jitter = latencies.std()
                std_dev = latencies.std() # same as jitter here but explicit
                count = len(latencies)
                
                env_display = 'AWS' if env == 'Nuvem' else env
                rows.append([env_display, t_name, format_float(median), format_float(jitter), format_float(std_dev), count])
            except Exception as e:
                print(f"Error reading A {path}: {e}")
                
    return pd.DataFrame(rows, columns=['Ambiente', 'Tópico', 'Lat. Mediana (ms)', 'Jitter (ms)', 'Desvio Padrão (ms)', 'Amostras'])

def process_table_b(base_path):
    envs = ['local', 'edison', 'aws']
    topics_agents = [
        ('/bloco/disponivel', 'resultados_sensor.csv'),
        ('/cam/capture', 'resultados_Cam.csv'),
        ('/colaboracao/fim', 'resultados_UR10.csv'),
        ('/entregador/coletaDisponivel', 'resultados_Franka.csv'),
        ('/entregador/encomendaColetada', 'resultados_youBot.csv'),
        ('/entregador/encomendaDisponibilizada', 'resultados_youBot.csv'),
        ('/entregador/pontoRecebimento', 'resultados_youBot.csv')
    ]
    
    rows = []
    for env in envs:
        # Agents first
        for t_name, f_name in topics_agents:
            path = os.path.join(base_path, 'com edge ai', 'cnn_autoral', env, f_name)
            if not os.path.exists(path):
                continue
            try:
                df = pd.read_csv(path)
                topico_col = get_col(df, ['Topico', 'Tópico'])
                df_topic = df[df[topico_col] == t_name]
                if len(df_topic) == 0:
                    continue
                val_col = get_col(df, ['Latencia_ms', 'Latencia (ms)'])
                latencies = df_topic[val_col].apply(parse_float)
                rows.append([env.capitalize() if env != 'aws' else 'AWS', t_name, format_float(latencies.median()), format_float(latencies.std()), format_float(latencies.std()), len(latencies)])
            except Exception as e:
                print(f"Error reading B {path}: {e}")
                
        # ESP metrics
        esp_path = os.path.join(base_path, 'com edge ai', 'cnn_autoral', env, 'metricas_esp.csv')
        if os.path.exists(esp_path):
            try:
                df_esp = pd.read_csv(esp_path)
                topico_col = get_col(df_esp, ['Topico', 'Tópico'])
                # esp classificar
                classificar = df_esp[df_esp[topico_col] == '/esp/classificar']
                if len(classificar) > 0:
                    val_col = get_col(df_esp, ['Latencia_ms', 'Latencia (ms)', 'Latencia'])
                    lats = classificar[val_col].apply(parse_float)
                    rows.append([env.capitalize() if env != 'aws' else 'AWS', '/esp/classificar', format_float(lats.median()), format_float(lats.std()), format_float(lats.std()), len(lats)])
            except Exception as e:
                print(f"Error reading B esp {esp_path}: {e}")
                
        # esp resultado is in ur10
        ur10_path = os.path.join(base_path, 'com edge ai', 'cnn_autoral', env, 'resultados_UR10.csv')
        if os.path.exists(ur10_path):
            try:
                df_ur10 = pd.read_csv(ur10_path)
                topico_col = get_col(df_ur10, ['Topico', 'Tópico'])
                resultado = df_ur10[df_ur10[topico_col] == '/esp/resultado']
                if len(resultado) > 0:
                    val_col = get_col(df_ur10, ['Latencia_ms', 'Latencia (ms)'])
                    lats = resultado[val_col].apply(parse_float)
                    rows.append([env.capitalize() if env != 'aws' else 'AWS', '/esp/resultado', format_float(lats.median()), format_float(lats.std()), format_float(lats.std()), len(lats)])
            except Exception as e:
                print(f"Error reading B ur10 {ur10_path}: {e}")
                
    # Sort logically
    return pd.DataFrame(rows, columns=['Ambiente', 'Tópico', 'Lat. Mediana (ms)', 'Jitter (ms)', 'Desvio Padrão (ms)', 'Amostras'])

def process_table_c(base_path):
    models = [('cnn_autoral', 'CNN Autoral'), ('v2', 'MobileNetV2'), ('v3', 'MobileNetV3 Small')]
    envs = ['local', 'edison', 'aws']
    
    rows = []
    for m_dir, m_name in models:
        all_inf = []
        for env in envs:
            esp_path = os.path.join(base_path, 'com edge ai', m_dir, env, 'metricas_esp.csv')
            if os.path.exists(esp_path):
                try:
                    df = pd.read_csv(esp_path)
                    val_col = get_col(df, ['Inferencia_ms', 'Inferencia (ms)', 'Inferência (ms)'])
                    infs = df[val_col].dropna().apply(parse_float)
                    all_inf.extend(infs.tolist())
                except Exception as e:
                    print(f"Error reading C {esp_path}: {e}")
        if all_inf:
            s_inf = pd.Series(all_inf)
            rows.append([m_name, format_float(s_inf.median()), format_float(s_inf.std()), len(all_inf)])
            
    return pd.DataFrame(rows, columns=['Arquitetura do Modelo', 'Tempo Mediano (ms)', 'Desvio Padrão (ms)', 'Amostras'])

def wrap_text(text, width=25):
    import textwrap
    if len(text) > width:
        return '\n'.join(textwrap.wrap(text, width))
    return text

def create_pdf(df, filename, is_landscape=False):
    # Calculate height based on newlines in string columns only
    max_newlines_per_col = []
    for col in df.columns:
        if df[col].dtype == object:
            max_newlines_per_col.append(df[col].astype(str).str.count('\n').max())
        else:
            max_newlines_per_col.append(0)
    
    max_newlines = max(max_newlines_per_col) if max_newlines_per_col else 0
    fig_height = max_newlines * 0.4 + len(df) * 0.5 + 2

    if is_landscape:
        fig, ax = plt.subplots(figsize=(14, fig_height))
    else:
        fig, ax = plt.subplots(figsize=(11, fig_height))
        
    ax.axis('tight')
    ax.axis('off')
    
    # Text wrap topics if needed
    if 'Tópico' in df.columns:
        df['Tópico'] = df['Tópico'].apply(lambda x: wrap_text(x, 28))
    
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)
    
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('black')
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#f0f0f0')
            cell.set_edgecolor('black')
            cell.set_linewidth(1.5)
        else:
            cell.set_linewidth(0.5)
            
    plt.text(0.5, -0.05, "Fonte: elaborada pelo autor (2026).", ha='center', va='top', transform=ax.transAxes, fontsize=10)
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()

base = '/home/kelton/Documentos/resultados/calcular'

print("Generating Appendix A...")
df_a = process_table_a(base)
create_pdf(df_a, '/home/kelton/Documentos/tcc/Monografia_TCC/apendices_pdf/apendice_A_sem_edge_ai.pdf', True)

print("Generating Appendix B...")
df_b = process_table_b(base)
create_pdf(df_b, '/home/kelton/Documentos/tcc/Monografia_TCC/apendices_pdf/apendice_B_com_edge_ai.pdf', True)

print("Generating Appendix C...")
df_c = process_table_c(base)
create_pdf(df_c, '/home/kelton/Documentos/tcc/Monografia_TCC/apendices_pdf/apendice_C_inferencia_esp32.pdf', False)

print("Done!")
