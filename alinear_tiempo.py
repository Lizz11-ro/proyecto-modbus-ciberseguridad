import glob
import os

import numpy as np
import pandas as pd

COLS = ["frame.time_epoch", "ip.src", "ip.dst", "mbtcp.trans_id"]
VENTANA = 12 * 3600  # buscamos desfases de hasta ±12 horas


def octeto(serie):
    return pd.to_numeric(serie.str.rsplit(".", n=1).str[-1], errors="coerce")


# 1) Paquetes Modbus de los 3 CSV de ataque (solo las columnas necesarias)
t_l, s_l, d_l, i_l = [], [], [], []
for ruta in sorted(glob.glob("data/procesado/ataque_hmi_*.csv")):
    print("Leyendo", os.path.basename(ruta))
    df = pd.read_csv(ruta, usecols=COLS, dtype=str)
    tid = pd.to_numeric(df["mbtcp.trans_id"], errors="coerce")
    ok = tid.notna()
    t_l.append(pd.to_numeric(df.loc[ok, "frame.time_epoch"]).to_numpy())
    s_l.append(octeto(df.loc[ok, "ip.src"]).fillna(-1).to_numpy(dtype=np.int16))
    d_l.append(octeto(df.loc[ok, "ip.dst"]).fillna(-1).to_numpy(dtype=np.int16))
    i_l.append(tid[ok].to_numpy(dtype=np.int64))
    del df

t = np.concatenate(t_l)
src = np.concatenate(s_l)
dst = np.concatenate(d_l)
tid = np.concatenate(i_l)
orden = np.argsort(tid, kind="stable")
t, src, dst, tid = t[orden], src[orden], dst[orden], tid[orden]
print("Paquetes Modbus con ID de transacción:", len(tid))

# 2) Registros de ataque
base = "modbus_dataset/attack/compromised-ied/attack logs"
ev = pd.concat([pd.read_csv(r) for r in sorted(glob.glob(base + "/**/*.csv", recursive=True))],
               ignore_index=True)
ev["TransactionID"] = pd.to_numeric(ev["TransactionID"], errors="coerce")
ev = ev.dropna(subset=["TransactionID"])
ev["epoch"] = (pd.to_datetime(ev["Timestamp"], format="ISO8601")
               - pd.Timestamp("1970-01-01")).dt.total_seconds()
ev["evento"] = ev["Attack"].str.split(r"[:.]", n=1, regex=True).str[0].str.strip()
ev["tipo"] = ev["evento"].str.replace(r"^Starting\s+", "", regex=True)
ev = ev[(ev["epoch"] > t.min() - VENTANA) & (ev["epoch"] < t.max() + VENTANA)].reset_index(drop=True)
print("Eventos de ataque candidatos:", len(ev))

# 3) Diferencias de hora entre cada evento y los paquetes con su mismo ID
marcas = []
for k, fila in ev.iterrows():
    T = int(fila["TransactionID"])
    lo = np.searchsorted(tid, T, "left")
    hi = np.searchsorted(tid, T, "right")
    for j in range(lo, hi):
        d = t[j] - fila["epoch"]
        if abs(d) <= VENTANA:
            marcas.append((k, d, j))

if not marcas:
    raise SystemExit("No se encontraron coincidencias por ID de transacción.")

m = pd.DataFrame(marcas, columns=["ev", "delta", "pkt"])
cuentas = np.bincount(np.rint(m["delta"]).astype(int) + VENTANA,
                      minlength=2 * VENTANA + 1).astype(float)
suave = np.convolve(cuentas, np.ones(5), mode="same")

picos = []
tmp = suave.copy()
for _ in range(3):
    i = int(tmp.argmax())
    picos.append((i - VENTANA, tmp[i]))
    tmp[max(0, i - 60): i + 61] = 0

print("\nDesfases más probables (hora del paquete - hora del registro):")
for d, c in picos:
    print(f"  {d:+7d} s = {d / 3600:+.3f} h | coincidencias: {int(c)}")

# 4) Qué paquetes coinciden con cada tipo de ataque (con el mejor desfase)
mejor = picos[0][0]
ok = m[(m["delta"] - mejor).abs() <= 2].copy()
print("\nEventos con paquete coincidente:", ok["ev"].nunique(), "de", len(ev))
ok["tipo"] = ev.loc[ok["ev"], "tipo"].to_numpy()
ok["par"] = [f"{src[j]}->{dst[j]}" for j in ok["pkt"]]
print("\nPares origen->destino (último octeto de la IP) por tipo:")
print(ok.groupby("tipo")["par"].value_counts().groupby(level=0).head(3).to_string())

print("\nEjemplos de texto por evento:")
for nombre, g in ev.groupby("evento"):
    print(" -", nombre, "|", g["Attack"].iloc[0][:90])