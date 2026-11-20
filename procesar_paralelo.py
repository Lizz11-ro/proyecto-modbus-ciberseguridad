import glob
import os
import shutil
import statistics as st
import time
from multiprocessing import Pool

import pandas as pd

from extraer import extraer

CARPETAS = [
    "modbus_dataset/attack/compromised-ied/trust-scada-hmi/trust-scada-network-captures",
    "modbus_dataset/benign/scada-hmi/scada-hmi-network-capture",
]
# Los 4 archivos que ya usamos en el proyecto
CLAVES = ["veth3efd353-1.pcap", "veth3efd353-2.pcap",
          "veth5bbeaa2-normal-13.pcap", "veth5bbeaa2-normal-14.pcap"]
PROCESOS = [1, 2]
REPETICIONES = 3
TMP = "data/benchmark_tmp"


def buscar_archivos():
    rutas = []
    for c in CARPETAS:
        for r in glob.glob(c + "/**/*.pcap", recursive=True):
            if any(r.replace("\\", "/").endswith(k) for k in CLAVES):
                rutas.append(r)
    rutas.sort(key=os.path.getsize, reverse=True)   # los grandes primero
    return rutas


def tarea(pcap):
    salida = os.path.join(TMP, os.path.basename(pcap) + ".csv")
    codigo, seg, err = extraer(pcap, salida)
    if codigo != 0:
        print("ERROR en", pcap, err)
    return seg


def correr(archivos, p):
    inicio = time.time()
    if p == 1:
        for a in archivos:
            tarea(a)
    else:
        with Pool(p) as pool:
            list(pool.imap_unordered(tarea, archivos, chunksize=1))
    total = time.time() - inicio
    shutil.rmtree(TMP, ignore_errors=True)   # liberar disco
    os.makedirs(TMP, exist_ok=True)
    return total


if __name__ == "__main__":
    archivos = buscar_archivos()
    if len(archivos) != len(CLAVES):
        raise SystemExit(f"Se esperaban {len(CLAVES)} archivos y encontré {len(archivos)}: {archivos}")
    mb = sum(os.path.getsize(a) for a in archivos) / 1e6
    print(f"{len(archivos)} archivos, {mb:.0f} MB en total\n")
    os.makedirs(TMP, exist_ok=True)

    filas = []
    for rep in range(1, REPETICIONES + 1):      # intercalado: 1,2,1,2,1,2
        for p in PROCESOS:
            seg = correr(archivos, p)
            print(f"repeticion {rep} | procesos {p} | {seg:.1f} s", flush=True)
            filas.append({"repeticion": rep, "procesos": p, "segundos": seg})
            pd.DataFrame(filas).to_csv("data/resultados_multiprocessing.csv", index=False)

    df = pd.DataFrame(filas)
    t1 = df[df.procesos == 1]["segundos"].mean()
    print("\nprocesos | media (s) | desv (s) | speedup | eficiencia")
    for p in PROCESOS:
        s = df[df.procesos == p]["segundos"]
        sp = t1 / s.mean()
        print(f"{p:>8} | {s.mean():>9.1f} | {st.pstdev(s):>8.1f} | {sp:>7.2f} | {sp/p:>10.2f}")
    shutil.rmtree(TMP, ignore_errors=True)