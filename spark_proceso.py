import os
import sys
import time
import glob
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

jdk = sorted(glob.glob(r"C:\Program Files\Eclipse Adoptium\jdk-21*"))
if jdk:
    os.environ["JAVA_HOME"] = jdk[-1]
    os.environ["PATH"] = jdk[-1] + r"\bin;" + os.environ["PATH"]

os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

RUTA = "data/etiquetado"
REPETICIONES = 5
NUCLEOS = [1, 2]

from pyspark.sql import DataFrame


def _a_pandas(sdf):
    return pd.DataFrame([r.asDict() for r in sdf.collect()])


DataFrame.toPandas = _a_pandas


def crear(n):
    return (SparkSession.builder.master(f"local[{n}]").appName("modbus")
            .config("spark.driver.memory", "1500m")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


def trabajo(spark, guardar=False):
    df = (spark.read.parquet(RUTA)
          .withColumnRenamed("frame.time_epoch", "t")
          .withColumnRenamed("frame.len", "largo")
          .withColumnRenamed("modbus.func_code", "func"))

    # 1) paquetes y tamaño por clase
    por_clase = (df.groupBy("tipo_ataque")
                 .agg(F.count("*").alias("paquetes"),
                      F.round(F.avg("largo"), 2).alias("largo_medio"),
                      F.min("largo").alias("largo_min"),
                      F.max("largo").alias("largo_max"))
                 .orderBy(F.desc("paquetes")).toPandas())

    # 2) código de función Modbus por clase
    por_func = (df.groupBy("tipo_ataque", "func").count()
                .orderBy("tipo_ataque", F.desc("count")).toPandas())

    # 3) serie de tiempo: paquetes por minuto y clase (alimenta el dashboard)
    serie = (df.withColumn("minuto", (F.floor(F.col("t") / 60) * 60).cast("long"))
             .groupBy("minuto", "tipo_ataque").count()
             .orderBy("minuto").toPandas())
        # 4) características por ventana de 5 s (insumo para un detector)
    v5 = (df.withColumn("ventana", (F.floor(F.col("t") / 5) * 5).cast("long"))
          .groupBy("ventana")
          .agg(F.count("*").alias("paquetes"),
               F.round(F.avg("largo"), 2).alias("largo_medio"),
               F.round(F.stddev("largo"), 2).alias("largo_desv"),
               F.countDistinct("func").alias("funciones"),
               F.max(F.col("etiqueta")).alias("hay_ataque"))
          .orderBy("ventana").toPandas())

    if guardar:
        por_clase.to_csv("data/resumen_por_clase.csv", index=False)
        por_func.to_csv("data/resumen_por_funcion.csv", index=False)
        serie.to_csv("data/resumen_serie_tiempo.csv", index=False)
        v5.to_csv("data/resumen_ventanas_5s.csv", index=False)
        print(por_clase.to_string(index=False))
    return len(por_clase)
    


if __name__ == "__main__":
    filas = []
    print("calentamiento (no se cuenta)...")
    s0 = crear(1)
    trabajo(s0)
    s0.stop()
    for rep in range(1, REPETICIONES + 1):
        for n in NUCLEOS:
            spark = crear(n)
            inicio = time.time()
            trabajo(spark, guardar=(rep == 1 and n == 2))
            seg = time.time() - inicio
            spark.stop()
            print(f"repeticion {rep} | local[{n}] | {seg:.1f} s", flush=True)
            filas.append({"repeticion": rep, "nucleos": n, "segundos": seg})
            pd.DataFrame(filas).to_csv("data/resultados_spark.csv", index=False)

    df = pd.DataFrame(filas)
    t1 = df[df.nucleos == 1]["segundos"].mean()
    print("\nnucleos | media (s) | desv (s) | speedup | eficiencia")
    for n in NUCLEOS:
        s = df[df.nucleos == n]["segundos"]
        sp = t1 / s.mean()
        print(f"{n:>7} | {s.mean():>9.1f} | {s.std(ddof=0):>8.1f} | {sp:>7.2f} | {sp/n:>10.2f}")