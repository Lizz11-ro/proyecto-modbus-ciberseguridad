# Ciberseguridad en infraestructura eléctrica crítica (Modbus TCP)

Proyecto Integrador — Redes e Infraestructura, Computación Paralela y Distribuida, Analítica y Visualización.

**Integrantes:** Laura Daniela Pérez González
**Universidad Santo Tomasn - Ingenieria de Datos e Inteligencia Artificial - 4 semestre**  
**Docentes:** Ivan Felipe Mariño Barreto, Zalma Valentina Galeano y Julian David Pareja Garzón

## Descripción
Se analiza tráfico Modbus TCP de una subestación eléctrica (dataset CIC Modbus 2023) para **cerrar el ciclo**:
analizar el tráfico de ataque → derivar una ACL desde el tráfico normal → evaluarla (% ataque bloqueado / % legítimo bloqueado) → validarla antes/después en Packet Tracer → mostrar los resultados en un dashboard.

## Resultados principales
| Indicador | Valor |
|---|---|
| Paquetes analizados | 3.093.393 (3 PCAP, 24 h, 23–24 mar 2023) |
| Paquetes de ataque | 44.908 (1,45 %) |
| Tipos de ataque etiquetados | 7 de 9 documentados |
| Multiprocessing (1 → 2 procesos) | 377,1 s → 268,4 s (speedup 1,40; eficiencia 0,70) |
| Spark local (1 vs 2 núcleos) | 10,2 s vs 10,4 s (speedup 0,98; eficiencia 0,49) |
| ACL, ataque externo | 100 % del ataque bloqueado, 0 % del tráfico legítimo bloqueado |
| ACL, escenario comprometido | 0 % / 0 % (el atacante usa un flujo permitido por diseño; la ACL no lo detecta) |

## Estructura
```
Proyecto_Modbus/
├── extraer.py, extraer_muestra.py      # tshark: PCAP -> CSV
├── rango_tiempo.py, alinear_tiempo.py  # alineación temporal (desfase -2 s)
├── etiquetar.py                        # etiquetado por ventanas de ataque -> Parquet
├── procesar_paralelo.py                # multiprocessing
├── spark_proceso.py                    # Apache Spark
├── graficas.py                         # 6 figuras (Matplotlib/Seaborn)
├── extraer_acl.py, evaluar_acl.py      # construcción y evaluación de la ACL
├── figuras/                            # PNG generados
├── data/                               # resultados_*.csv (los datos pesados no se suben)
├── packet_tracer/                      # subestacion.pkt, subestacion_acl.pkt
├── dashboard/                          # dashboard_modbus.pbix
└── informe/, poster/, video/           # entregables
```

## Requisitos
- Python 3.10+ (probado con 3.14), Wireshark/tshark en el PATH
- Java 21 (necesario para Spark); en Windows, `winutils.exe` y `hadoop.dll` en `C:\hadoop\bin`
- Cisco Packet Tracer (para abrir los `.pkt`) y Power BI Desktop (para el `.pbix`)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Datos
El dataset **CIC Modbus 2023** (Canadian Institute for Cybersecurity, Universidad de New Brunswick) no se incluye por su tamaño (PCAP de varios GB).
Descárguelo desde el sitio oficial del CIC y colóquelo en `modbus_dataset/` conservando su estructura de carpetas.

## Cómo reproducir (orden de ejecución)
```bash
python extraer.py            # 1. PCAP -> CSV con tshark
python alinear_tiempo.py     # 2. alineación temporal
python etiquetar.py          # 3. etiquetado -> data/etiquetado/*.parquet
python procesar_paralelo.py  # 4. benchmark multiprocessing -> data/resultados_multiprocessing.csv
python spark_proceso.py      # 5. Spark -> data/resultados_spark.csv y resumen_*.csv
python graficas.py           # 6. figuras en figuras/
python extraer_acl.py        # 7. flujos y lista blanca (ACL)
python evaluar_acl.py        # 8. evaluación -> data/resultados_acl.csv
```
Luego abrir `packet_tracer/subestacion.pkt` (sin ACL) y `subestacion_acl.pkt` (con ACL) y `dashboard/dashboard_modbus.pbix`.

## Limitaciones
- Equipo de pruebas de 2 núcleos: el speedup de Spark en modo local es limitado (overhead mayor que el trabajo).
- 7 de los 9 tipos de ataque documentados tienen paquetes etiquetados.
- La ACL es una lista blanca por IP/puerto: no detecta ataques que reutilizan flujos permitidos (escenario comprometido).
- Etiquetado por ventanas de tiempo desde los logs, con un desfase de −2 s y márgenes; puede haber ruido en los bordes.

## Uso de IA

Se utilizó Claude (Anthropic) como herramienta de apoyo y consulta durante la parte técnica del proyecto: orientación para depurar scripts en Python, configurar el entorno de trabajo (Java y Hadoop en Windows) y construir las medidas y la distribución del dashboard en Power BI.

Como integrantes del equipo ejecutamos los códigos sobre el dataset CIC Modbus 2023, se configuro la topología y las ACL en Packet Tracer, se obtuvieron y verificaron los resultados, y se redactaron los documentos del proyecto.

## Referencias
_(Dataset CIC Modbus 2023 y las referencias del informe.)_
