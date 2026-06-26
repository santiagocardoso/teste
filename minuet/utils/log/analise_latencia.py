import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import re
import os

# Paleta de cores oficial
COLOR_MAP = {
    'RANDOM': '#7f7f7f', # Cinza
    'AHP': '#d62728',    # Vermelho
    'AHP_DT': '#2ca02c'  # Verde
}

LABELS = {
    'RANDOM': 'Seleção Randômica',
    'AHP': 'AHP Tradicional',
    'AHP_DT': 'AHP + Decision Tree'
}

def parse_creation_times(filepath, event_id_to_analyze):
    creation_times = {}
    pattern = re.compile(
        r'^(?P<time_ns>\d+)ns - MonitoringLayer - Node #(?P<node_id>\d+).*?'
        r': Sending Monitoring Message: Event = (?P<event_id>\d+) Seq = (?P<seq>\d+)'
    )
    if not os.path.exists(filepath):
        return creation_times

    with open(filepath, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                ev_id = int(match.group('event_id'))
                if ev_id == event_id_to_analyze:
                    node_id = int(match.group('node_id'))
                    seq = int(match.group('seq'))
                    time_ns = int(match.group('time_ns'))
                    msg_key = (node_id, ev_id, seq)
                    creation_times[msg_key] = time_ns
    return creation_times

def calculate_latencies(filepath, bs_ids, creation_times):
    latencies = []
    processed_messages = set()
    
    if not os.path.exists(filepath):
        return latencies

    pattern = re.compile(
        r'^(?P<time_ns>\d+)ns - BASE STATION - Node #(?P<bs_id>\d+): '
        r'.*?MonitorId = (?P<monitor_id>\d+).*?Seq = (?P<seq>\d+).*?EventId = (?P<event_id>\d+)'
    )
    
    with open(filepath, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                bs_id = int(match.group('bs_id'))
                if bs_id in bs_ids:
                    monitor_id = int(match.group('monitor_id'))
                    event_id = int(match.group('event_id'))
                    seq = int(match.group('seq'))
                    time_ns = int(match.group('time_ns'))
                    
                    msg_key = (bs_id, monitor_id, event_id, seq)
                    origin_key = (monitor_id, event_id, seq)
                    
                    if origin_key in creation_times and msg_key not in processed_messages:
                        latency_ms = (time_ns - creation_times[origin_key]) / 1000000.0
                        if latency_ms >= 0:
                            latencies.append(latency_ms)
                            processed_messages.add(msg_key)
    return latencies

def plot_grouped_boxplot(all_data, percentages, methods):
    # =========================================================================
    # Ajustado para (10, 6) para padronizar com o gráfico de linhas
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    data_to_plot = []
    positions = []
    box_colors = []

    base_pos = 1
    base_ticks = []

    # Ajuste do espaçamento (caixas mais afastadas entre si)
    offsets = [-0.25, 0, 0.25] 
    width = 0.18

    for p in percentages:
        base_ticks.append(base_pos)
        
        for i, m in enumerate(methods):
            latencies = all_data[p][m]
            if len(latencies) > 0:
                data_to_plot.append(latencies)
                positions.append(base_pos + offsets[i])
                box_colors.append(COLOR_MAP[m])
                
        base_pos += 1.5 

    if data_to_plot:
        # Linha da mediana em branco e bordas mais grossas para melhor leitura
        box = ax.boxplot(data_to_plot, positions=positions, widths=width, patch_artist=True, showfliers=False,
                         medianprops=dict(color='white', linewidth=2),
                         boxprops=dict(linewidth=1.2),
                         whiskerprops=dict(linewidth=1.2),
                         capprops=dict(linewidth=1.2))

        for patch, color in zip(box['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.9) 

    # =========================================================================
    # TRUQUE DE DESTAQUE: Desenhar Diamante em cenários com apenas 1 pacote
    # =========================================================================
    for pos, latencies, color in zip(positions, data_to_plot, box_colors):
        if len(latencies) == 1:
            val = latencies[0]
            # Desenha um diamante na mesma cor da respectiva caixa
            ax.plot(pos, val, marker='D', color=color, markersize=8, markeredgecolor='black', zorder=5)
            # Escreve "1 dtg" embaixo do diamante
            ax.text(pos, val * 0.85, '1 dtg', ha='center', va='top', fontsize=9, fontweight='bold', color='#595959')
    # =========================================================================

    # Configuração do Eixo Y (Escala Logarítmica convertida para números normais: 100, 1000)
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
    
    # Trava os limites do Eixo Y para garantir espaço limpo para a legenda
    ax.set_ylim(10, 30000)

    # Nomes do Eixo X
    ax.set_xticks(base_ticks)
    ax.set_xticklabels([f"{p}%" for p in percentages])
    
    # Títulos maiores
    ax.set_ylabel('Latência (ms) [Escala Logarítmica]', fontsize=12, fontweight='bold')
    ax.set_xlabel('Concentração de Nós Maliciosos', fontsize=12, fontweight='bold')
    ax.tick_params(axis='both', labelsize=11)

    # LEGENDA MOVIDA PARA O CANTO INFERIOR DIREITO
    legend_patches = [mpatches.Patch(color=COLOR_MAP[m], label=LABELS[m]) for m in methods]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=11, framealpha=0.95, edgecolor='gray')

    # Estética limpa
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Grade de fundo
    ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.5)
    ax.yaxis.grid(True, linestyle=':', which='minor', color='lightgrey', alpha=0.3)

    fig.tight_layout()
    plt.savefig("grafico_latencia_agrupado.png", dpi=300)
    print("\nGráfico agrupado de latência salvo como 'grafico_latencia_agrupado.png'!")

if __name__ == "__main__":
    BASE_STATION_IDS = [1332]
    EVENT_ID_TO_ANALYZE = 0      
    
    PERCENTAGES = [0, 10, 20, 30, 40, 50]
    METHODS = ["RANDOM", "AHP", "AHP_DT"]
    
    all_data = {p: {m: [] for m in METHODS} for p in PERCENTAGES}
    
    print(f"{'CENÁRIO':<20} | {'MÍNIMA (ms)':<12} | {'MÁXIMA (ms)':<12} | {'MÉDIA (ms)':<12} | {'PAC_RECEBIDOS':<10}")
    print("-" * 75)

    for p in PERCENTAGES:
        for m in METHODS:
            folder_name = f"{m}_{p}"
            mon_path = os.path.join(".", folder_name, "logFileMonitoringLayer.log")
            bs_path = os.path.join(".", folder_name, "logFileBaseStation.log")
            
            c_times = parse_creation_times(mon_path, EVENT_ID_TO_ANALYZE)
            lats = calculate_latencies(bs_path, BASE_STATION_IDS, c_times)
            all_data[p][m] = lats
            
            if lats:
                print(f"{folder_name:<20} | {min(lats):<12.2f} | {max(lats):<12.2f} | {sum(lats)/len(lats):<12.2f} | {len(lats):<10}")
            else:
                print(f"{folder_name:<20} | {'N/A':<12} | {'N/A':<12} | {'N/A':<12} | {0:<10}")
        print("-" * 75)
            
    plot_grouped_boxplot(all_data, PERCENTAGES, METHODS)