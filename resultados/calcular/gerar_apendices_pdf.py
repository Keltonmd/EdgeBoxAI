#!/usr/bin/env python3
"""
Gera PDFs das planilhas de métricas para os apêndices do TCC.
Usa apenas matplotlib (sem openpyxl/reportlab).
"""

import csv
import os
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages

OUT_DIR = '/home/kelton/Documentos/tcc/Monografia_TCC/apendices_pdf'
os.makedirs(OUT_DIR, exist_ok=True)

BASE_SEM = '/home/kelton/Documentos/resultados/calcular/sem edge ai'
BASE_COM = '/home/kelton/Documentos/resultados/calcular/com edge ai'


# ─── helpers ─────────────────────────────────────────────────────────────────

def load_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def fmt(v, decimals=2):
    """Formata float com vírgula decimal (padrão ABNT)."""
    try:
        return f"{float(v):.{decimals}f}".replace('.', ',')
    except:
        return str(v)

def draw_table_pdf(pdf_path, title, col_labels, col_widths, rows,
                   col_aligns=None, fontsize=9, rows_per_page=30):
    """Gera um PDF com uma (ou mais páginas de) tabela formatada."""
    fig_w = sum(col_widths) + 1.0          # largura total A4 aprox.
    row_h = 0.38                            # altura por linha (pol)
    header_h = 0.55
    margin_h = 1.5                          # topo (título) + rodapé

    if col_aligns is None:
        col_aligns = ['center'] * len(col_labels)

    # divide em páginas
    chunks = [rows[i:i+rows_per_page] for i in range(0, max(len(rows),1), rows_per_page)]

    with PdfPages(pdf_path) as pdf:
        for page_idx, chunk in enumerate(chunks):
            n_rows = len(chunk)
            fig_h = header_h + n_rows * row_h + margin_h
            fig_h = max(fig_h, 4.0)

            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.axis('off')

            # fonte apenas na 1ª página
            if page_idx == 0:
                fig.text(0.5, 0.01, 'Fonte: elaborada pelo autor (2026).',
                         ha='center', va='bottom', fontsize=8, style='italic')

            # monta dados para plt.table
            cell_text = [list(r) for r in chunk]
            table = ax.table(
                cellText=cell_text,
                colLabels=col_labels,
                colWidths=[w / fig_w for w in col_widths],
                loc='center',
                cellLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(fontsize)
            table.scale(1, 1.6)

            # estilo cabeçalho
            for j in range(len(col_labels)):
                cell = table[0, j]
                cell.set_facecolor('#1F3864')
                cell.set_text_props(color='white', fontweight='bold')

            # zebra + alinhamento
            for i, row_data in enumerate(chunk):
                facecolor = '#E8EDF5' if i % 2 == 0 else 'white'
                for j, val in enumerate(row_data):
                    cell = table[i + 1, j]
                    cell.set_facecolor(facecolor)
                    cell.set_text_props(ha=col_aligns[j])

            plt.tight_layout(rect=[0, 0.04, 1, 1.0])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

    print(f'  ✓ {os.path.basename(pdf_path)}')


# ─── APÊNDICE A: sem Edge AI ─────────────────────────────────────────────────

def apendice_a():
    rows_raw = load_csv(f'{BASE_SEM}/metricas_completas_latencia_jitter.csv')
    # colunas: Ambiente,Topico,Latencia_Mediana_ms,Latencia_Media_ms,Jitter_ms,
    #          Latencia_P95_ms,Latencia_Max_ms,Latencia_Min_ms,Amostras

    order = {'Local': 0, 'Edison': 1, 'Nuvem': 2}
    rows_raw.sort(key=lambda r: (order.get(r['Ambiente'], 9), r['Topico']))

    col_labels = ['Ambiente', 'Tópico', 'Mediana (ms)', 'Média (ms)',
                  'Jitter (ms)', 'P95 (ms)', 'Mín (ms)', 'Máx (ms)', 'Vol.']
    col_widths = [1.2, 3.2, 1.4, 1.4, 1.3, 1.3, 1.3, 1.3, 0.8]
    col_aligns = ['center', 'left', 'center', 'center', 'center', 'center', 'center', 'center', 'center']

    rows = []
    prev_env = None
    for r in rows_raw:
        env = r['Ambiente']
        topico = r['Topico']
        rows.append([
            env if env != prev_env else '',
            topico,
            fmt(r['Latencia_Mediana_ms']),
            fmt(r['Latencia_Media_ms']),
            fmt(r['Jitter_ms']),
            fmt(r['Latencia_P95_ms']),
            fmt(r['Latencia_Min_ms']),
            fmt(r['Latencia_Max_ms']),
            r['Amostras'],
        ])
        prev_env = env

    draw_table_pdf(
        pdf_path=f'{OUT_DIR}/apendice_A_sem_edge_ai.pdf',
        title='',
        col_labels=col_labels,
        col_widths=col_widths,
        rows=rows,
        col_aligns=col_aligns,
        fontsize=8,
        rows_per_page=25,
    )


# ─── APÊNDICE B: com Edge AI ─────────────────────────────────────────────────

def apendice_b():
    rows_raw = load_csv(f'{BASE_COM}/metricas_topicos_final.csv')
    # colunas: Ambiente,Topico,Latencia_Mediana_ms,Jitter_ms,Amostras

    order = {'Local': 0, 'Edison': 1, 'AWS': 2}
    rows_raw.sort(key=lambda r: (order.get(r['Ambiente'], 9), r['Topico']))

    col_labels = ['Ambiente', 'Tópico', 'Lat. Mediana (ms)', 'Jitter (ms)', 'Amostras']
    col_widths = [1.2, 3.5, 1.8, 1.4, 1.0]
    col_aligns = ['center', 'left', 'center', 'center', 'center']

    rows = []
    prev_env = None
    for r in rows_raw:
        env = r['Ambiente']
        rows.append([
            env if env != prev_env else '',
            r['Topico'],
            fmt(r['Latencia_Mediana_ms']),
            fmt(r['Jitter_ms']),
            r['Amostras'],
        ])
        prev_env = env

    draw_table_pdf(
        pdf_path=f'{OUT_DIR}/apendice_B_com_edge_ai.pdf',
        title='Métricas de latência e jitter por tópico MQTT\nCenário com inferência embarcada (CNN Autoral)',
        col_labels=col_labels,
        col_widths=col_widths,
        rows=rows,
        col_aligns=col_aligns,
        fontsize=9,
        rows_per_page=30,
    )


# ─── APÊNDICE C: Tempo de inferência por modelo ──────────────────────────────

def load_inference(path):
    rows = load_csv(path)
    return [float(r['tempo_inferencia_ms']) for r in rows]

def apendice_c():
    cnn_local  = load_inference(f'{BASE_COM}/cnn_autoral/local/metricas_esp.csv')
    cnn_edison = load_inference(f'{BASE_COM}/cnn_autoral/edison/metricas_esp.csv')
    cnn_aws    = load_inference(f'{BASE_COM}/cnn_autoral/aws/metricas_esp.csv')
    v2_aws     = load_inference(f'{BASE_COM}/v2/metricas_esp.csv')
    v3_all     = load_inference(f'{BASE_COM}/v3/metricas_esp.csv')

    def stats_row(modelo, ambiente, vals):
        if not vals:
            return ['', '', '', '', '', '', '']
        return [
            modelo,
            ambiente,
            fmt(statistics.mean(vals)),
            fmt(min(vals), 3),
            fmt(max(vals), 3),
            fmt(statistics.stdev(vals) if len(vals) > 1 else 0),
            str(len(vals)),
        ]

    rows = [
        stats_row('CNN Autoral', 'Local',  cnn_local),
        stats_row('CNN Autoral', 'Edison', cnn_edison),
        stats_row('CNN Autoral', 'AWS',    cnn_aws),
        stats_row('', '', []),   # separador visual
        stats_row('MobileNetV3 Small', 'AWS*', v3_all),
        stats_row('', '', []),
        stats_row('MobileNetV2', 'AWS*', v2_aws),
    ]
    # remove linhas separadoras inválidas
    rows = [r for r in rows if r[2] != '0,00']

    col_labels = ['Modelo', 'Ambiente', 'Média (ms)', 'Mín (ms)', 'Máx (ms)', 'Desvio (ms)', 'N']
    col_widths  = [2.2, 1.4, 1.4, 1.4, 1.4, 1.4, 0.8]
    col_aligns  = ['left', 'center', 'center', 'center', 'center', 'center', 'center']

    draw_table_pdf(
        pdf_path=f'{OUT_DIR}/apendice_C_inferencia_esp32.pdf',
        title='Tempo de inferência no ESP32-S3 por arquitetura\n(*MobileNetV3 e V2 testados apenas em AWS)',
        col_labels=col_labels,
        col_widths=col_widths,
        rows=rows,
        col_aligns=col_aligns,
        fontsize=9,
        rows_per_page=30,
    )


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Gerando PDFs dos apêndices...')
    apendice_a()
    apendice_b()
    apendice_c()
    print(f'\nConcluído! PDFs em: {OUT_DIR}')
