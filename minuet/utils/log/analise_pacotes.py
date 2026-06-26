import matplotlib.pyplot as plt
import re
import os

def parse_log_folder(folderpath, bs_ids, event_id):
    """Verifica a pasta e conta os datagramas. Retorna 0 se o log da RSU não existir."""
    if not os.path.exists(folderpath):
        return None  

    filepath = os.path.join(folderpath, "logFileBaseStation.log")
    counts = 0

    if not os.path.exists(filepath):
        return 0  

    log_pattern = re.compile(r'Node #(?P<bs_id>\d+): .*?EventId = (?P<event_id>\d+)')

    with open(filepath, 'r') as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                bs_id = int(match.group('bs_id'))
                if bs_id in bs_ids and int(match.group('event_id')) == event_id:
                    counts += 1
                    
    return counts

def plot_degradation_line_chart(percentages, results_ahp, results_ahp_dt, results_random):
    # =========================================================================
    # MUDANÇA AQUI: Reduzi a largura de 11 para 8, mantendo a altura em 6.
    # Isso vai "espremer" o gráfico na horizontal e deixar as quedas mais íngremes.
    # =========================================================================
    plt.figure(figsize=(10, 6))

    valid_p = []
    valid_ahp = []
    valid_dt = []
    for p, a, d in zip(percentages, results_ahp, results_ahp_dt):
        if a is not None and d is not None:
            valid_p.append(p)
            valid_ahp.append(a)
            valid_dt.append(d)
            
    if valid_p:
        plt.fill_between(valid_p, valid_ahp, valid_dt, color='#2ca02c', alpha=0.15, label='Datagramas Salvos pela DT')

    plt.plot(percentages, results_ahp, marker='o', linestyle='-', color='#d62728', linewidth=2.5, markersize=8, label='AHP Tradicional')
    plt.plot(percentages, results_ahp_dt, marker='s', linestyle='-', color='#2ca02c', linewidth=2.5, markersize=8, label='AHP + Decision Tree')
    plt.plot(percentages, results_random, marker='^', linestyle='--', color='#7f7f7f', linewidth=2, markersize=8, label='Seleção Randômica')

    for i, p in enumerate(percentages):
        if results_random[i] is not None:
            plt.text(p, results_random[i] - 35, str(results_random[i]), color='#595959', fontsize=10, fontweight='bold', ha='center')
        
        if results_ahp[i] is not None:
            offset_ahp = 15 if results_ahp[i] < 20 else -35
            plt.text(p, results_ahp[i] + offset_ahp, str(results_ahp[i]), color='#d62728', fontsize=10, fontweight='bold', ha='center')

        if results_ahp_dt[i] is not None:
            plt.text(p, results_ahp_dt[i] + 20, str(results_ahp_dt[i]), color='#2ca02c', fontsize=10, fontweight='bold', ha='center')

        if i > 0 and results_ahp[i] is not None and results_ahp_dt[i] is not None and results_ahp[i] > 0:
            ganho_pct = ((results_ahp_dt[i] - results_ahp[i]) / results_ahp[i]) * 100
            if ganho_pct > 0:
                mid_y = results_ahp[i] + (results_ahp_dt[i] - results_ahp[i]) / 2
                plt.text(p, mid_y, f"+{ganho_pct:.1f}%", color='darkgreen', fontsize=9, fontweight='bold', 
                         ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    plt.xlabel('Concentração de Nós Maliciosos', fontsize=12, fontweight='bold')
    plt.ylabel('Nº de Datagramas Recebidos', fontsize=12, fontweight='bold')

    plt.xticks(percentages, [f"{x}%" for x in percentages])
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.legend(fontsize=11, loc='upper right', framealpha=0.95)

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    valores_validos = [v for v in results_ahp + results_ahp_dt + results_random if v is not None]
    if valores_validos:
        plt.ylim(-50, max(valores_validos) + 60) 
    
    plt.tight_layout()
    plt.savefig("grafico_degradacao_datagramas.png", dpi=300)
    print("\nGráfico de linhas com proporção ajustada salvo como 'grafico_degradacao_datagramas.png'!")

if __name__ == "__main__":
    BASE_STATION_IDS = [1332]
    EVENT_ID_TO_ANALYZE = 0 
    
    PERCENTAGES = [0, 10, 20, 30, 40, 50]
    
    counts_ahp = []
    counts_ahp_dt = []
    counts_random = []

    print(f"{'CENÁRIO':<20} | {'DATAGRAMAS RECEBIDOS':<10}")
    print("-" * 45)

    for p in PERCENTAGES:
        folder_puro = os.path.join(".", f"AHP_{p}")
        total_puro = parse_log_folder(folder_puro, BASE_STATION_IDS, EVENT_ID_TO_ANALYZE)
        counts_ahp.append(total_puro)
        print(f"{f'AHP ({p}%)':<20} | {total_puro if total_puro is not None else 'NÃO RODOU':<10}")

        folder_dt = os.path.join(".", f"AHP_DT_{p}")
        total_dt = parse_log_folder(folder_dt, BASE_STATION_IDS, EVENT_ID_TO_ANALYZE)
        counts_ahp_dt.append(total_dt)
        print(f"{f'AHP + DT ({p}%)':<20} | {total_dt if total_dt is not None else 'NÃO RODOU':<10}")

        folder_random = os.path.join(".", f"RANDOM_{p}")
        total_random = parse_log_folder(folder_random, BASE_STATION_IDS, EVENT_ID_TO_ANALYZE)
        counts_random.append(total_random)
        print(f"{f'RANDOM ({p}%)':<20} | {total_random if total_random is not None else 'NÃO RODOU':<10}")
        
        print("-" * 45)

    plot_degradation_line_chart(PERCENTAGES, counts_ahp, counts_ahp_dt, counts_random)