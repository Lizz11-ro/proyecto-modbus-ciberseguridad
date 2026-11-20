# Ciberseguridad en infraestructura eléctrica crítica (Modbus TCP)

Proyecto Integrador — Redes e Infraestructura, Computación Paralela y Distribuida, Analítica y Visualización.

**Integrantes:** Laura Daniela Pérez González

**Universidad Santo Tomas - Ingenieria de Datos e Inteligencia Artificial - 4 semestre**  
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
├── data/                               # resultados_*.csv (Datos pesados, no subidos)
├── packet_tracer/                      # packet_subestacion.pkt, packet_subestacion_acl.pkt
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
Pueden descargarlo desde el sitio oficial del CIC y colocarlo en `modbus_dataset/` conservando su estructura de carpetas.

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
- Equipo de pruebas de 2 núcleos: el speedup de Spark en modo local es limitado.
- 7 de los 9 tipos de ataque documentados tienen paquetes etiquetados.
- La ACL es una lista blanca por IP/puerto: no detecta ataques que reutilizan flujos permitidos.
- Etiquetado por ventanas de tiempo desde los logs, con un desfase de −2 s y márgenes; puede haber ruido en los bordes.

## Uso de IA

Se utilizó Claude (Anthropic) como herramienta de apoyo y consulta durante la parte técnica del proyecto: orientación para depurar scripts en Python, configurar el entorno de trabajo (Java y Hadoop en Windows) y construir las medidas y la distribución del dashboard en Power BI.

Como integrantes del equipo ejecutamos los códigos sobre el dataset CIC Modbus 2023, se configuro la topología y las ACL en Packet Tracer, se obtuvieron y verificaron los resultados, y se redactaron los documentos del proyecto.

## Referencias

[1] K. Boakye-Boateng, A. A. Ghorbani, and A. Habibi Lashkari, "CIC Modbus Dataset 2023," Canadian Institute for Cybersecurity, Univ. of New Brunswick, 2023. [Online]. Available: https://www.unb.ca/cic/datasets/modbus-2023.html (Accessed: Nov. 20, 2026).

[2] K. Boakye-Boateng, A. A. Ghorbani, and A. Habibi Lashkari, "Securing substations with trust, risk posture and multi-agent systems: A comprehensive approach," in *Proc. 20th Int. Conf. Privacy, Security and Trust (PST)*, Copenhagen, Denmark, Aug. 2023.

[3] K. Stouffer *et al.*, "Guide to operational technology (OT) security," NIST, Gaithersburg, MD, USA, Spec. Pub. 800-82 Rev. 3, Sep. 2023. doi: [10.6028/NIST.SP.800-82r3](https://doi.org/10.6028/NIST.SP.800-82r3).

[4] Modbus Organization, "Modbus application protocol specification V1.1b3," 2012. [Online]. Available: https://modbus.org/modbus-specifications (Accessed: Nov. 20, 2026).

[5] J. Moy, "OSPF version 2," IETF, RFC 2328, Apr. 1998. [Online]. Available: https://www.rfc-editor.org/rfc/rfc2328

[6] Python Software Foundation, "multiprocessing — Process-based parallelism," *Python 3 Documentation*. [Online]. Available: https://docs.python.org/3/library/multiprocessing.html (Accessed: Nov. 20, 2026).

[7] Apache Software Foundation, "Apache Spark documentation." [Online]. Available: https://spark.apache.org/docs/latest/ (Accessed: Nov. 20, 2026).

[8] Amdahl, G. M. (1967, April). Validity of the single processor approach to achieving large scale computing capabilities. In Proceedings of the April 18-20, 1967, spring joint computer conference (pp. 483-485).

[9] Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. Computing in science & engineering, 9(3), 90-95.

[10] Microsoft, "Power BI documentation." [Online]. Available: https://learn.microsoft.com/power-bi/ (Accessed: Nov. 20, 2026).
