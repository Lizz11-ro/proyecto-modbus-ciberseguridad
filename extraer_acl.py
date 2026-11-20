import os
import time

import pandas as pd

from extraer import extraer

ARCHIVOS = {
    "ext_nw0": "modbus_dataset/attack/external/network-wide/network-wide-normal-0.pcap",
    "ext_nw1": "modbus_dataset/attack/external/network-wide/network-wide-normal-1.pcap",
    "ben_nw14": "modbus_dataset/benign/network-wide-pcap-capture/network-wide/network-wide-normal-14.pcap",
}
os.makedirs("data/acl", exist_ok=True)

for nombre, ruta in ARCHIVOS.items():
    salida = f"data/acl/{nombre}.csv"
    if os.path.exists(salida):
        print("ya existe", salida)
    else:
        codigo, seg, err = extraer(ruta, salida)
        print(f"{nombre}: codigo {codigo}, {seg:.0f} s {err}", flush=True)

    df = pd.read_csv(salida, usecols=["frame.time_epoch", "ip.src", "ip.dst",
                                      "tcp.srcport", "tcp.dstport"], dtype=str)
    df = df.fillna("-")
    t = df["frame.time_epoch"].astype(float, errors="ignore")
    df["modbus502"] = (df["tcp.srcport"] == "502") | (df["tcp.dstport"] == "502")
    print(f"\n=== {nombre}: {len(df):,} filas ===")
    print("Desde", pd.to_datetime(pd.to_numeric(df['frame.time_epoch'], errors='coerce').min(), unit="s"),
          "hasta", pd.to_datetime(pd.to_numeric(df['frame.time_epoch'], errors='coerce').max(), unit="s"))
    res = (df.groupby(["ip.src", "ip.dst", "modbus502"]).size()
           .reset_index(name="paquetes").sort_values("paquetes", ascending=False).head(25))
    print(res.to_string(index=False))
    print()