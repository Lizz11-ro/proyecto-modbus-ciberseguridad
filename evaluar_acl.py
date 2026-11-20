import glob

import pandas as pd

ATACANTE = "185.175.0.7"
HMI_CONFIABLE = "185.175.0.2"
IEDS = ["185.175.0.4", "185.175.0.5", "185.175.0.8"]
COLS = ["ip.src", "ip.dst", "tcp.srcport", "tcp.dstport"]
MIN_PAQ = 10


def preparar(df):
    df = df.fillna("-")
    df = df[df["ip.src"] != "-"].copy()          # quita ARP y otros sin IP
    m502 = ((df["tcp.srcport"] == "502") | (df["tcp.dstport"] == "502")).astype(str)
    df["clave"] = df["ip.src"] + ">" + df["ip.dst"] + ">" + m502
    return df


def resumen(nombre, atq, permitido):
    n_atq, n_ben = int(atq.sum()), int((~atq).sum())
    bloq_atq = int((atq & ~permitido).sum())
    bloq_ben = int((~atq & ~permitido).sum())
    return {"escenario": nombre,
            "ataque_total": n_atq, "ataque_bloqueado": bloq_atq,
            "ataque_bloqueado_%": round(100 * bloq_atq / n_atq, 2) if n_atq else None,
            "legitimo_total": n_ben, "legitimo_bloqueado": bloq_ben,
            "legitimo_bloqueado_%": round(100 * bloq_ben / n_ben, 3) if n_ben else None}


def cargar_csv(ruta):
    return preparar(pd.read_csv(ruta, usecols=COLS, dtype=str))


# 1) Reglas aprendidas SOLO del tráfico benigno (enero)
ben = cargar_csv("data/acl/ben_nw14.csv")
cuentas = ben["clave"].value_counts()
lista = set(cuentas[cuentas >= MIN_PAQ].index)
print("Reglas aprendidas (origen>destino>modbus502):")
for k, n in cuentas[cuentas >= MIN_PAQ].items():
    print(f"  {k}   {n:,} paquetes")

filas = []

# 2) Escenario externo: atacante .7
for nombre in ["ext_nw0", "ext_nw1"]:
    df = cargar_csv(f"data/acl/{nombre}.csv")
    atq = (df["ip.src"] == ATACANTE) | (df["ip.dst"] == ATACANTE)
    permitido = df["clave"].isin(lista)
    filas.append(resumen(nombre, atq, permitido))
    mal = df[~atq & ~permitido]["clave"].value_counts().head(5)
    if len(mal):
        print(f"\n{nombre}: tráfico legítimo que la ACL bloquearía por error:")
        print(mal.to_string())

# 3) Escenario comprometido (HMI .2 hacia los IED): la HMI es legítima, se permite por diseño
lista_comp = set(lista)
for ied in IEDS:
    for m in ["True"]:
        lista_comp.add(f"{HMI_CONFIABLE}>{ied}>{m}")
        lista_comp.add(f"{ied}>{HMI_CONFIABLE}>{m}")

lista_comp.add(f"{HMI_CONFIABLE}>185.175.0.6>False")
lista_comp.add(f"185.175.0.6>{HMI_CONFIABLE}>False")
partes = []
for r in sorted(glob.glob("data/etiquetado/*.parquet")):
    d = pd.read_parquet(r, columns=COLS + ["etiqueta"])
    partes.append(preparar(d))
comp = pd.concat(partes, ignore_index=True)
atq = comp["etiqueta"] == 1
filas.append(resumen("comprometido", atq, comp["clave"].isin(lista_comp)))
bloq = comp[~comp["clave"].isin(lista_comp)]
print("\nClaves bloqueadas en el escenario comprometido:")
print(bloq.groupby(["clave", "etiqueta"]).size().sort_values(ascending=False).head(10).to_string())

res = pd.DataFrame(filas)
res.to_csv("data/resultados_acl.csv", index=False)
print("\n", res.to_string(index=False))