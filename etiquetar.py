import glob
import os

import numpy as np
import pandas as pd

BASE_LOGS = "modbus_dataset/attack/compromised-ied/attack logs"
SALIDA = "data/etiquetado"
DESFASE = -2.0     # paquete - registro, medido en alinear_tiempo.py
MARGEN = 1.0       # segundos de holgura a cada lado
PUNTUAL = 30.0     # ventana (s) para eventos sin "Starting"/"Complete"

os.makedirs(SALIDA, exist_ok=True)

# 1) Registros de ataque
ev = pd.concat([pd.read_csv(r) for r in sorted(glob.glob(BASE_LOGS + "/**/*.csv", recursive=True))],
               ignore_index=True)
ev["epoch"] = (pd.to_datetime(ev["Timestamp"], format="ISO8601")
               - pd.Timestamp("1970-01-01")).dt.total_seconds() + DESFASE
ev["evento"] = ev["Attack"].str.split(r"[:.]", n=1, regex=True).str[0].str.strip()
ev["inicio"] = ev["evento"].str.startswith("Starting")
ev["tipo"] = (ev["evento"].str.replace(r"^Starting\s+", "", regex=True)
              .str.replace(r"\s+Attack$", "", regex=True)
              .str.capitalize())
ev = ev.sort_values("epoch").reset_index(drop=True)

# 2) Rango de tiempo de los PCAP de ataque
rutas = sorted(glob.glob("data/procesado/ataque_hmi_*.csv"))
tmin, tmax = np.inf, -np.inf
for r in rutas:
    s = pd.read_csv(r, usecols=["frame.time_epoch"])["frame.time_epoch"]
    tmin, tmax = min(tmin, s.min()), max(tmax, s.max())
ev = ev[(ev["epoch"] >= tmin - 600) & (ev["epoch"] <= tmax + 600)].reset_index(drop=True)
print(f"Eventos en el rango de captura: {len(ev)}")

# 3) Ventanas: de "Starting X" al siguiente "X ... Complete"
completos = ev[ev["evento"].str.endswith("Complete") | ev["Attack"].str.contains("Complete")]
ventanas = []
duraciones = {}
for i, f in ev[ev["inicio"]].iterrows():
    fin = completos[(completos["tipo"] == f["tipo"]) & (completos["epoch"] >= f["epoch"])]
    sig = ev[ev["inicio"] & (ev["epoch"] > f["epoch"])]
    if len(fin):
        t_fin = fin["epoch"].iloc[0]
        if len(sig) and sig["epoch"].iloc[0] < t_fin:   # otro inicio antes: no sirve
            t_fin = np.nan
    else:
        t_fin = np.nan
    ventanas.append([f["tipo"], f["epoch"], t_fin])
v = pd.DataFrame(ventanas, columns=["tipo", "t0", "t1"])

# Inicios sin final: duración típica del tipo, sin pasar del siguiente inicio
med = (v["t1"] - v["t0"]).groupby(v["tipo"]).median()
sin_fin = v["t1"].isna()
print(f"Ventanas con final: {(~sin_fin).sum()} | sin final: {sin_fin.sum()}")
for k in v[sin_fin].index:
    tipo, t0 = v.loc[k, "tipo"], v.loc[k, "t0"]
    dur = med.get(tipo, np.nan)
    dur = PUNTUAL if np.isnan(dur) else dur
    sig = v[v["t0"] > t0]["t0"]
    v.loc[k, "t1"] = min(t0 + dur, sig.iloc[0]) if len(sig) else t0 + dur

# Eventos puntuales (Baseline Replay, Delay response, False Data Injection...)
puntuales = ev[~ev["inicio"] & ~ev["Attack"].str.contains("Complete")].copy()
puntuales = puntuales[~puntuales["tipo"].isin(v["tipo"].unique())]
extra = pd.DataFrame({"tipo": puntuales["tipo"], "t0": puntuales["epoch"],
                      "t1": puntuales["epoch"] + PUNTUAL})
v = pd.concat([v, extra], ignore_index=True)
CORTOS = ["Frame stacking", "Length manipulation", "Payload injection", "Query flooding"]
es_corto = v["tipo"].isin(CORTOS) & ((v["t1"] - v["t0"]) < 3)
v.loc[es_corto, "t1"] = v.loc[es_corto, "t0"] + 3.0   # con el margen queda en +4 s
v["t0"] -= MARGEN
v["t1"] += MARGEN
v = v.sort_values("t0").reset_index(drop=True)
v["dur_s"] = v["t1"] - v["t0"]
print("\nVentanas por tipo (cantidad, duración mediana en s):")
print(v.groupby("tipo")["dur_s"].agg(["count", "median"]).round(1))
v.to_csv("data/ventanas_ataque.csv", index=False)

# 4) Etiquetar cada CSV de ataque
t0s, t1s, tipos = v["t0"].to_numpy(), v["t1"].to_numpy(), v["tipo"].to_numpy()
tot = {}
for r in rutas:
    df = pd.read_csv(r, dtype=str)
    df["frame.time_epoch"] = df["frame.time_epoch"].astype(float)
    df["frame.len"] = pd.to_numeric(df["frame.len"], errors="coerce")
    t = df["frame.time_epoch"].to_numpy()
    idx = np.searchsorted(t0s, t, side="right") - 1
    idx_ok = idx >= 0
    dentro = np.zeros(len(t), dtype=bool)
    dentro[idx_ok] = t[idx_ok] <= t1s[idx[idx_ok]]
    df["etiqueta"] = dentro.astype(np.int8)
    df["tipo_ataque"] = np.where(dentro, tipos[np.clip(idx, 0, None)], "normal")
    nombre = os.path.basename(r).replace(".csv", "")
    try:
        df.to_parquet(f"{SALIDA}/{nombre}.parquet", index=False)
    except ImportError:
        df.to_csv(f"{SALIDA}/{nombre}.csv", index=False)
    for k, n in df["tipo_ataque"].value_counts().items():
        tot[k] = tot.get(k, 0) + int(n)
    print(f"{nombre}: {len(df):,} filas | ataque {dentro.mean()*100:.1f}%")
    del df

print("\nPaquetes por clase (total):")
for k, n in sorted(tot.items(), key=lambda x: -x[1]):
    print(f"  {k:<30}{n:>10,}")