import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

os.makedirs("figuras", exist_ok=True)
sns.set_theme(style="whitegrid")
AZUL, ROJO = "#2b6cb0", "#c0392b"

clase = pd.read_csv("data/resumen_por_clase.csv")
func = pd.read_csv("data/resumen_por_funcion.csv")
serie = pd.read_csv("data/resumen_serie_tiempo.csv")
v5 = pd.read_csv("data/resumen_ventanas_5s.csv")
mp = pd.read_csv("data/resultados_multiprocessing.csv")
sp = pd.read_csv("data/resultados_spark.csv")


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(f"figuras/{nombre}.png", dpi=200)
    plt.close()
    print("guardada", nombre)


# 1) Paquetes por clase (escala log)
fig, ax = plt.subplots(figsize=(8, 4.5))
colores = [AZUL if c == "normal" else ROJO for c in clase["tipo_ataque"]]
ax.barh(clase["tipo_ataque"], clase["paquetes"], color=colores)
ax.set_xscale("log")
ax.invert_yaxis()
ax.set_xlabel("Paquetes (escala logarítmica)")
ax.set_title("Paquetes por clase: el ataque es el 1.5 % del tráfico")
for i, v in enumerate(clase["paquetes"]):
    ax.text(v * 1.1, i, f"{v:,}", va="center", fontsize=8)
guardar("01_paquetes_por_clase")

# 2) Serie de tiempo: normal vs ataque por minuto
serie["hora"] = pd.to_datetime(serie["minuto"], unit="s")
serie["grupo"] = np.where(serie["tipo_ataque"] == "normal", "normal", "ataque")
p = serie.pivot_table(index="hora", columns="grupo", values="count", aggfunc="sum").fillna(0)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
a1.plot(p.index, p["normal"], color=AZUL, lw=0.9)
a1.set_ylabel("Normal\n(paquetes/min)")
a2.vlines(p.index[p["ataque"] > 0], 0, p["ataque"][p["ataque"] > 0], color=ROJO, lw=1.5)
a2.set_ylim(0, p["ataque"].max() * 1.1)
a2.set_ylabel("Ataque\n(paquetes/min)")
a2.set_xlabel("Hora (UTC), 23-24 de marzo de 2023")
a1.set_title("Tráfico por minuto: normal y ataque")
guardar("02_serie_tiempo")

# 3) Código de función Modbus por clase (proporción por fila)
func["func"] = func["func"].astype(str)
top = func.groupby("func")["count"].sum().nlargest(6).index
m = func[func["func"].isin(top)].pivot_table(index="tipo_ataque", columns="func",
                                             values="count", aggfunc="sum").fillna(0)
m = m.div(m.sum(axis=1), axis=0)
fig, ax = plt.subplots(figsize=(8, 4.5))
sns.heatmap(m, annot=True, fmt=".2f", cmap="Blues", cbar_kws={"label": "proporción"}, ax=ax)
ax.set_xlabel("Código de función Modbus")
ax.set_ylabel("")
ax.set_title("Funciones Modbus usadas por clase")
guardar("03_funcion_por_clase")

# 4) Paquetes por ventana de 5 s, con y sin ataque
v5["ventana_tipo"] = np.where(v5["hay_ataque"] == 1, "con ataque", "sin ataque")
fig, ax = plt.subplots(figsize=(6, 4.5))
sns.boxplot(data=v5, x="ventana_tipo", y="paquetes", hue="ventana_tipo",
            palette={"sin ataque": AZUL, "con ataque": ROJO}, legend=False, ax=ax)
ax.set_yscale("log")
ax.set_xlabel("")
ax.set_ylabel("Paquetes por ventana de 5 s (log)")
ax.set_title("Volumen por ventana de 5 s")
guardar("04_paquetes_por_ventana")

# 5) Tamaño medio vs volumen por ventana
fig, ax = plt.subplots(figsize=(7, 4.5))
norm = v5[v5["hay_ataque"] == 0].sample(min(8000, int((v5["hay_ataque"] == 0).sum())), random_state=1)
atq = v5[v5["hay_ataque"] == 1]
ax.scatter(norm["paquetes"], norm["largo_medio"], s=10, alpha=0.35, color=AZUL, label="sin ataque")
ax.scatter(atq["paquetes"], atq["largo_medio"], s=28, color=ROJO, edgecolor="white", linewidth=0.5, label="con ataque", zorder=3)
ax.set_xlabel("Paquetes por ventana de 5 s")
ax.set_ylabel("Tamaño medio del paquete (bytes)")
ax.set_title("Las ventanas con ataque se mezclan con las normales")
ax.legend(title="")
guardar("05_tamano_vs_volumen")

# 6) Rendimiento paralelo: multiprocessing vs Spark
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4))
r = mp.groupby("procesos")["segundos"].agg(["mean", "std"]).reset_index()
a1.bar(r["procesos"].astype(str), r["mean"], yerr=r["std"], color=[AZUL, ROJO], capsize=4)
a1.set_title("multiprocessing (tshark)")
a1.set_xlabel("Procesos")
a1.set_ylabel("Tiempo (s)")
r = sp.groupby("nucleos")["segundos"].agg(["mean", "std"]).reset_index()
a2.bar(r["nucleos"].astype(str), r["mean"], yerr=r["std"], color=[AZUL, ROJO], capsize=4)
a2.set_title("Spark local")
a2.set_xlabel("Núcleos")
guardar("06_rendimiento_paralelo")
