import glob
import os
from datetime import datetime, timezone

import pandas as pd

print("=== CSV extraídos: rango de tiempo (UTC) e IPs más frecuentes ===")
for ruta in sorted(glob.glob("data/procesado/*.csv")):
    df = pd.read_csv(ruta, usecols=["frame.time_epoch", "ip.src"])
    t = df["frame.time_epoch"].dropna()
    ini = datetime.fromtimestamp(t.min(), tz=timezone.utc)
    fin = datetime.fromtimestamp(t.max(), tz=timezone.utc)
    print(os.path.basename(ruta), "|", ini.strftime("%Y-%m-%d %H:%M:%S"),
          "->", fin.strftime("%Y-%m-%d %H:%M:%S"), "| filas:", len(t))
    print("    IPs origen:", df["ip.src"].value_counts().head(4).to_dict())

print("\n=== Registros de ataque: rango (tal como están escritos) ===")
base = "modbus_dataset/attack/compromised-ied/attack logs"
logs = sorted(glob.glob(base + "/**/*.csv", recursive=True))
todos = []
for ruta in logs:
    df = pd.read_csv(ruta)
    print(os.path.relpath(ruta, base), "|", df["Timestamp"].min(), "->",
          df["Timestamp"].max(), "| filas:", len(df))
    todos.append(df)

print("\n=== Tipos de evento en los registros ===")
ev = pd.concat(todos)["Attack"].str.split(r"[:.]", n=1, regex=True).str[0].str.strip()
print(ev.value_counts().head(25).to_string())