import csv
import glob
import os
import re

from extraer import extraer

SALIDA = "data/procesado"
LOG = "data/tiempos_extraccion.csv"

# (prefijo de salida, carpeta, cuántos PCAP tomar)
MUESTRA = [
    ("ataque_hmi", "modbus_dataset/attack/compromised-ied/trust-scada-hmi", 3),
    ("benigno_hmi", "modbus_dataset/benign/scada-hmi", 2),
]


def numero(ruta):
    m = re.search(r"-(\d+)\.pcap$", ruta)
    return int(m.group(1)) if m else -1


def registrar(fila):
    nuevo = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["archivo", "tamano_mb", "filas", "segundos"])
        w.writerow(fila)


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    for prefijo, carpeta, n in MUESTRA:
        pcaps = sorted(glob.glob(f"{carpeta}/**/*.pcap", recursive=True), key=numero)[:n]
        print("Archivos a procesar en", carpeta, ":", len(pcaps))
        for pcap in pcaps:
            nombre = os.path.basename(pcap).replace(".pcap", "")
            salida = f"{SALIDA}/{prefijo}_{nombre}.csv"
            if os.path.exists(salida):
                print("Ya existe, se omite:", salida)
                continue
            print("Extrayendo", pcap)
            codigo, segundos, error = extraer(pcap, salida)
            filas = sum(1 for _ in open(salida, encoding="utf-8")) - 1
            mb = round(os.path.getsize(pcap) / 1e6)
            print(f"  código {codigo} | {filas} filas | {segundos:.1f} s")
            if error:
                print(error)
            registrar([os.path.basename(pcap), mb, filas, round(segundos, 1)])