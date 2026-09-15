# Laboratorio de mediciones y generador de la presentación

Material del profesor. Aquí están las mediciones reales que alimentan las gráficas de
`Pruebas de Carga y Rendimiento.pptx` y el código para repetirlas y regenerar la
presentación. Los estudiantes no necesitan esta carpeta para hacer el taller.

## Qué hay

| Archivo | Para qué |
|---|---|
| `step.js` | Script de k6 de las mediciones: modelo cerrado, abierto o pico, según `MODE`. |
| `driver.py` | Arranca el servicio, lo calienta, corre k6 y guarda métricas de cliente (k6) y de servidor (Actuator). |
| `prepare_pool.py` | Construye en `pool/` la variante con HikariCP (el mismo código, con pool). |
| `run_all.sh` | La batería completa que se usó para las gráficas (~45 min). |
| `export_data.py` | Resume `results/` (crudo, no versionado) en `data/` (versionado). |
| `data/` | Las mediciones resumidas que usa el generador. |
| `deck/` | Generador de la presentación con python-pptx (`build.py`) y render a PNG con PowerPoint (`render.ps1`). |
| `guia/` | Generador de `guia-visual-pruebas-de-carga.html` (raíz del repo): `construir.js` y `plantilla.html`. También calibra el modelo del simulador de ejecución. |

## Regenerar solo la presentación

Con los datos que ya están en `data/`:

```bash
pip install python-pptx
python perf/lab/deck/build.py "Pruebas de Carga y Rendimiento.pptx"
```

Para revisar el resultado como imágenes (solo en Windows, con PowerPoint instalado):

```powershell
powershell -File perf/lab/deck/render.ps1 -Pptx "<ruta absoluta>.pptx" -OutDir "<carpeta>"
```

## Regenerar la guía visual

La guía lleva las mediciones incrustadas: **si se repiten las mediciones, hay que regenerarla**, o seguirá mostrando los números viejos.

```bash
node perf/lab/guia/construir.js
```

Además de resumir `data/`, el script calibra el modelo del simulador de ejecución y lo imprime en la consola:

- **Throughput:** ajuste de la ley de escalabilidad universal (USL) a las medias por escalón. Las medias son ruidosas y no se pueden interpolar sin que una rampa suba y baje de golpe.
- **p95 y fallos:** interpolación en escala logarítmica de VUs, forzada a no decrecer.
- **Variación por segundo:** tomada de la línea de tiempo real del pico.

La página publica el error del ajuste junto a la variación entre corridas idénticas, para que el simulador no pase por medición. Si al regenerar el error del ajuste crece mucho más que esa variación, revise el modelo antes de usar la guía en clase.

## Repetir las mediciones

Requisitos: JDK 17+, Maven, k6 y Python 3.

```bash
cd registraduria && mvn -DskipTests package && cd ..   # variante sin pool
python perf/lab/prepare_pool.py                        # variante con pool
bash perf/lab/run_all.sh                               # mide y exporta a data/
python perf/lab/deck/build.py "Pruebas de Carga y Rendimiento.pptx"
```

Cierre los servicios que usen el puerto 8080 antes de empezar. `results/` y `pool/`
no se versionan.

## Cómo se midió y por qué así

Cada decisión de abajo corrige un problema que apareció al medir. La presentación
cuenta varios en la diapositiva "Lo que salió mal al medir para esta clase".

- **Servicio y k6 en núcleos separados.** Sin separarlos, en un portátil de 16 hilos la
  CPU llegó al 99 % y parte del tiempo que reportaba k6 era k6 esperando CPU. El driver
  fija el servicio a un núcleo y k6 al resto (`SRV_MASK`, `K6_MASK`; están pensadas para
  un i7-13620H, ajústelas a su CPU). Fuera de Windows no se fija afinidad: use `taskset`.
- **`-XX:ActiveProcessorCount=1`.** La JVM arranca antes de que se le fije la afinidad;
  sin esta opción dimensiona sus hilos de GC para todos los núcleos y aparecen pausas de
  cientos de milisegundos.
- **Servicio reiniciado en cada escalón, con 20 s de calentamiento.** Evita que las filas
  acumuladas en H2 y el JIT sin calentar cambien el resultado.
- **Dos repeticiones por escalón.** En un portátil la variación entre corridas idénticas
  es grande; las gráficas muestran cada corrida, no solo el promedio.
- **Resolución del histograma del servidor.** Se arranca el servicio con
  `minimum-expected-value` en 50 µs; con el valor por defecto (1 ms), todo el p95 del
  servidor caía en el primer intervalo.
- **Rangos de ids por repetición** (`REP_BASE` en `driver.py`). En la batería original las
  bases estaban separadas 1e8 y, con más de 1.000 VUs en el modelo abierto, la segunda
  repetición reutilizó ids y recibió `DUPLICATED`. Eso afectó el porcentaje de resultados
  de negocio correctos de esas corridas, no sus tiempos ni su throughput. Ya está corregido.

## Límites de estos datos

- Un portátil con otras aplicaciones abiertas no es un entorno de laboratorio: los números
  sirven para ver la forma de las curvas, no como referencia de capacidad.
- H2 en memoria abre conexiones mucho más baratas que una base de datos real por red. Aun
  así el pool marca la diferencia; contra PostgreSQL o MySQL la diferencia sería mayor.
- El p95 del servidor se estima a partir de los intervalos del histograma de Actuator.
