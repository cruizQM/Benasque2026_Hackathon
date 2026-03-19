import sqlite3
import re
import matplotlib.pyplot as plt
import os
from collections import defaultdict

# === CONFIGURACIÓN ===
DB_NAME = "MaxCut_results.db"
OUTPUT_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/MaxCut/PCE_CUNQA"

# === DIRECTORIO DE IMÁGENES ===
IMAGES_DIR = os.path.join(OUTPUT_DIR, "Images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# === LEER BASE DE DATOS ===
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("SELECT filename, r, r_media FROM MaxCut_results")
rows = c.fetchall()
conn.close()

# === VALORES EXACTOS ===
EXACT_SOLUTIONS = {
    10: 25, 20: 97, 40: 355, 50: 602, 60: 852,
    100: 2224, 150: 4899, 200: 8717, 250: 13460, 300: 19267
}

# === ORGANIZAR DATOS ===
data_dict = defaultdict(list)

for filename, r, r_media in rows:
    name = filename.replace("Circuits_MaxCut_", "").replace(".json", "")
    parts = name.split("_")

    if len(parts) != 4:
        continue

    n = int(parts[0])
    optimizador = parts[1]
    k = int(parts[2])
    shots = int(parts[3])

    if n not in EXACT_SOLUTIONS:
        continue

    data_dict[(optimizador, k, shots)].append((n, r, r_media))

# === GRAFICAR COMPARATIVAS POR OPTIMIZADOR ===
for optimizador in ["DIFFERENTIALEVOLUTION"]:
    plt.figure(figsize=(9,5))

    k_value = 2

    shots_values = sorted(
        set(key[2] for key in data_dict if key[0] == optimizador and key[1] == k_value)
    )

    # NUEVO: listas de colores y marcadores
    colors = plt.cm.tab10.colors
    markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*', '<', '>']

    for shots in shots_values:
        key = (optimizador, k_value, shots)
        data = data_dict.get(key, [])
        if not data:
            continue

        data.sort(key=lambda x: x[0])
        n_vals = [d[0] for d in data]
        r_vals = [d[1] for d in data]

        # NUEVO: asignación de color y marcador
        idx = shots_values.index(shots)
        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]

        plt.plot(n_vals, r_vals,
                linestyle='None',
                marker=marker,
                color=color,
                markersize=7,
                label=f'r (shots={shots})')

    # Líneas de referencia
    r_barra = 16 / 17
    plt.axhline(y=r_barra, linestyle='--', linewidth=1, color='red', label=r'$\overline{r}=16/17$')
    plt.axhline(y=1, linestyle='--', linewidth=1, color='green')

    plt.xlabel("Number of nodes")
    plt.ylabel("Ratio of success (r)")
    plt.title(f"Simulation | Optimizer: {optimizador} | k=2")
    plt.grid(True, linestyle=':')
    plt.legend()

    plt.ylim(0.7, 1.1)

    plt.tight_layout()
    output_path = os.path.join(IMAGES_DIR, f"MaxCut_grafico_r_{optimizador}_k2_noisy_shots.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f":white_check_mark: Gráfico guardado: {output_path}")

print("\n:bar_chart: Gráficas generadas correctamente.")