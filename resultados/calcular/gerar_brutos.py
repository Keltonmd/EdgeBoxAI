import csv
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

OUT_DIR = '/home/kelton/Documentos/tcc/Monografia_TCC/apendices_pdf'
os.makedirs(OUT_DIR, exist_ok=True)

def fmt(v, decimals=2):
    try:
        return f"{float(v):.{decimals}f}".replace('.', ',')
    except:
        return str(v)

def draw_table_pdf(pdf_path, col_labels, col_widths, rows,
                   col_aligns=None, fontsize=8, rows_per_page=45):
    fig_w = sum(col_widths) + 0.5
    row_h = 0.22
    header_h = 0.4
    margin_h = 0.8

    if col_aligns is None:
        col_aligns = ['center'] * len(col_labels)

    chunks = [rows[i:i+rows_per_page] for i in range(0, max(len(rows),1), rows_per_page)]

    with PdfPages(pdf_path) as pdf:
        for page_idx, chunk in enumerate(chunks):
            n_rows = len(chunk)
            fig_h = header_h + n_rows * row_h + margin_h
            fig_h = max(fig_h, 3.0)

            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.axis('off')

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
            table.scale(1, 1.4)

            for j in range(len(col_labels)):
                cell = table[0, j]
                cell.set_facecolor('#1F3864')
                cell.set_text_props(color='white', fontweight='bold')

            for i, row_data in enumerate(chunk):
                facecolor = '#E8EDF5' if i % 2 == 0 else 'white'
                for j, val in enumerate(row_data):
                    cell = table[i + 1, j]
                    cell.set_facecolor(facecolor)
                    cell.set_text_props(ha=col_aligns[j])

            plt.tight_layout(rect=[0, 0.02, 1, 1.0])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

    print(f'  ✓ {os.path.basename(pdf_path)} ({len(rows)} linhas)')

def process_raw_data(base_path, glob_pattern, pdf_name):
    files = glob.glob(os.path.join(base_path, glob_pattern), recursive=True)
    rows = []
    
    for fpath in files:
        if 'metricas' in fpath: continue # Ignora consolidados
        if 'processamento' in fpath: continue
        
        # Tenta inferir o ambiente pela pasta
        parts = fpath.split('/')
        if 'Local' in parts or 'local' in parts: env = 'Local'
        elif 'Edison' in parts or 'edison' in parts: env = 'Edison'
        elif 'Nuvem' in parts or 'aws' in parts or 'AWS' in parts: env = 'Nuvem'
        else: env = 'Outro'

        with open(fpath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                if 'Latencia_ms' in r and 'Topico' in r:
                    lat = r['Latencia_ms']
                    # Filtra latências bizarras
                    try:
                        lat_val = float(lat)
                        if lat_val > 5000: continue # Pula valores anômalos
                    except:
                        continue

                    pub = r.get('Robo_Publicador', '')
                    sub = r.get('Robo_Assinante', '')
                    rows.append({
                        'Ambiente': env,
                        'Topico': r['Topico'],
                        'Pub': pub,
                        'Sub': sub,
                        'Latencia': lat_val
                    })
    
    # Ordena as linhas
    order = {'Local': 0, 'Edison': 1, 'Nuvem': 2, 'Outro': 3}
    rows.sort(key=lambda r: (order.get(r['Ambiente'], 9), r['Topico']))

    table_rows = []
    for r in rows:
        table_rows.append([r['Ambiente'], r['Topico'], r['Pub'], r['Sub'], fmt(r['Latencia'])])
    
    draw_table_pdf(
        pdf_path=f'{OUT_DIR}/{pdf_name}',
        col_labels=['Ambiente', 'Tópico', 'Pub.', 'Sub.', 'Lat. (ms)'],
        col_widths=[1.2, 3.5, 1.2, 1.2, 1.2],
        col_aligns=['center', 'left', 'center', 'center', 'center'],
        rows=table_rows
    )

if __name__ == '__main__':
    print('Gerando PDFs brutos...')
    process_raw_data('/home/kelton/Documentos/resultados/calcular/sem edge ai', '**/*.csv', 'apendice_D_brutos_sem_edge.pdf')
    process_raw_data('/home/kelton/Documentos/resultados/calcular/com edge ai/cnn_autoral', '**/*.csv', 'apendice_E_brutos_com_edge.pdf')
