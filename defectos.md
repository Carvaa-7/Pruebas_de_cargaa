# Registro de Defectos — Taller de Pruebas de Carga y Rendimiento

Curso: Testing y Validación de Software  
Proyecto: Pruebas de Carga y Rendimiento  
Fecha: 2026-09-18

---

## Introducción

Este documento recopila los defectos identificados durante la ejecución de pruebas de
rendimiento (Baseline, Load, Stress y Spike) sobre el servicio `POST /register` de la
Registraduría. Cada defecto incluye evidencia directa de los archivos `summary-*.json`
generados por k6.

---

## Defecto PERF-01 — Ausencia de pool de conexiones JDBC causa saturación bajo carga

- **Capa afectada:** Infraestructura / Persistencia (`RegistryRepository.java`)
- **Escenario donde se detectó:** Spike Test (50 → 300 VUs en 1 minuto)
- **SLO definido:** Error rate < 1%
- **Resultado esperado:** El servicio mantiene la tasa de error por debajo del 1% ante un pico súbito de tráfico.
- **Resultado obtenido:** Error rate = **39.7%** (270,054 errores sobre 680,453 peticiones)

### Evidencia

Extraída de `perf/results/summary-spike.json` (sin pool):

```
http_req_failed:   rate=0.39687  passes=270054  fails=410399
checks:            rate=0.6031   passes=820798  fails=540108
http_reqs:         count=680453  rate=2835 req/s
http_req_duration: avg=6.2ms  p(95)=25.2ms  max=359ms
```

Extraída de `perf/results/summary-load.json` (sin pool, 200 VUs):

```
http_req_failed:   rate=0.0000176  passes=222  fails=12578098
http_req_duration: avg=7.7ms  p(90)=13.6ms  p(95)=17.6ms  max=861ms
```

Extraída de `perf/results/summary-stress.json` (sin pool, 600 VUs):

```
http_req_failed:   rate=0.0000097  passes=76   fails=7871995
http_req_duration: avg=20.4ms  p(90)=40.9ms  p(95)=53.5ms  max=872ms
```

### Análisis técnico

`RegistryRepository.getConnection()` llamaba a `DriverManager.getConnection()` en cada
operación. El método `registerVoter` realiza dos operaciones por request (`existsById`
y `save`), lo que equivale a **dos conexiones JDBC nuevas por petición**. Con 300 VUs
subiendo en 1 minuto eso genera cientos de conexiones creándose y destruyéndose por
segundo. Cuando el gestor de H2 no puede atender más solicitudes simultáneas de
conexión, devuelve error — de ahí el 39.7% de fallos.

Este defecto **no es detectable con pruebas unitarias ni de integración**, ya que ambas
trabajan con un único hilo. Solo se manifiesta bajo concurrencia real, que es
exactamente el dominio de las pruebas de carga.

### Impacto

- Ante cualquier pico de tráfico (campaña, evento electoral), el servicio falla para
  4 de cada 10 usuarios.
- El throughput cae de ~16,000 req/s (con pool) a ~2,800 req/s (sin pool) bajo el
  mismo escenario.

### Causa raíz

Uso directo de `DriverManager.getConnection()` sin pool de conexiones. Cada operación
crea y destruye una conexión, en lugar de reutilizar conexiones preexistentes.

### Corrección aplicada

Se introdujo **HikariCP** como pool de conexiones en `RegistryConfig.java`:

```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl(jdbcUrl);
config.setMaximumPoolSize(20);
config.setMinimumIdle(5);
config.setConnectionTimeout(3000);
return new HikariDataSource(config);
```

`RegistryRepository` ahora recibe un `DataSource` e invoca `dataSource.getConnection()`
en lugar de `DriverManager.getConnection()`. Las conexiones se reutilizan del pool.

### Verificación (post-fix)

Extraída de `perf/results/summary-spike.json` (con HikariCP):

```
http_req_failed:   rate=0.0  passes=0  fails=4014220
checks:            rate=1.0  passes=8028440  fails=0
http_reqs:         count=4014220  rate=16726 req/s
http_req_duration: avg=5.6ms  p(95)=16.4ms  max=266ms
```

| Métrica | Sin pool | Con HikariCP | Mejora |
|---|---|---|---|
| Throughput | 2,835 req/s | 16,726 req/s | +490% |
| p95 latencia | 25.2 ms | 16.4 ms | -35% |
| Error rate | **39.7%** | **0%** | -100% |
| Checks fallidos | 270,054 | 0 | -100% |

### Estado

**Resuelto** — corregido en commit `af65dd6` y validado con nueva corrida de spike.

### Prioridad

**Crítica**

---

## Tabla de seguimiento

| ID | Escenario | SLO | Resultado obtenido | Estado | Prioridad |
|---|---|---|---|---|---|
| PERF-01 | Spike (50→300 VUs) | Error rate < 1% | 39.7% sin pool → 0% con HikariCP | Resuelto | Crítica |

---

## Convenciones de Estado

- **Abierto:** Defecto identificado sin corrección aplicada.
- **En progreso:** En proceso de corrección.
- **Resuelto:** Corregido y validado con nuevas pruebas.

---

Universidad de La Sabana — Facultad de Ingeniería  
Curso: Testing y Validación de Software (2025-2)
