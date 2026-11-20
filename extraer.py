import subprocess
import time
import os

TSHARK = "C:/Program Files/Wireshark/tshark.exe"
CARPETA = "modbus_dataset/attack/compromised-ied/ied1a/ied1a-network-captures"
SALIDA = "data/procesado"

CAMPOS = [
    "frame.time_epoch", "ip.src", "ip.dst",
    "tcp.srcport", "tcp.dstport", "frame.len",
    "mbtcp.trans_id", "modbus.func_code", "modbus.reference_num",
]


def extraer(pcap, csv_salida):
    comando = [
        TSHARK, "-n", "-r", pcap,
        "-T", "fields", "-E", "separator=,", "-E", "header=y",
        "-E", "quote=d", "-E", "aggregator=;",
    ]
    for campo in CAMPOS:
        comando += ["-e", campo]

    inicio = time.time()
    with open(csv_salida, "w", encoding="utf-8", newline="") as f:
        r = subprocess.run(comando, stdout=f, stderr=subprocess.PIPE, text=True)
    return r.returncode, time.time() - inicio, r.stderr[:300]


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    nombre = "veth3614724-0.pcap"
    pcap = f"{CARPETA}/{nombre}"
    csv_salida = f"{SALIDA}/{nombre.replace('.pcap', '.csv')}"

    print("Extrayendo, puede tardar varios minutos en tu equipo...")
    codigo, segundos, error = extraer(pcap, csv_salida)

    filas = sum(1 for _ in open(csv_salida, encoding="utf-8")) - 1
    print("Código de salida:", codigo)
    print("Filas extraídas:", filas)
    print("Segundos:", round(segundos, 1))
    print(error)