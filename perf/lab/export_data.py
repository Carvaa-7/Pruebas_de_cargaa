"""Resume las corridas crudas de results/ en data/, que es lo que se versiona y lo
que lee el generador de la presentacion.

    python export_data.py [carpeta_de_resultados]

results/ no se versiona: el volcado --out csv de la prueba de pico pesa ~10 MB.
data/ pesa unos cientos de KB y basta para regenerar todas las graficas.
"""
import csv, gzip, json, math, os, shutil, statistics, sys
from collections import defaultdict

LAB = os.path.dirname(os.path.abspath(__file__))
RES = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(LAB, 'results')
OUT = os.path.join(LAB, 'data')
os.makedirs(OUT, exist_ok=True)


def rows(path):
    with gzip.open(path, 'rt', newline='') as f:
        yield from csv.DictReader(f)


# 1) Filas por escalon (una por corrida), tal cual las escribe driver.py
for name in ['closed-nopool', 'closed-pool', 'open-nopool', 'open-pool', 'hist-nopool', 'spike-nopool']:
    src = os.path.join(RES, name + '.jsonl')
    if os.path.exists(src):
        shutil.copy(src, os.path.join(OUT, name + '.jsonl'))

# 2) Duracion de cada peticion del experimento de percentiles
src = os.path.join(RES, 'hist-nopool.csv.gz')
if os.path.exists(src):
    vals = sorted(float(r['metric_value']) for r in rows(src) if r['metric_name'] == 'http_req_duration')
    json.dump(vals, open(os.path.join(OUT, 'hist-nopool.json'), 'w'), separators=(',', ':'))

# 3) Prueba de pico agregada por segundo
src = os.path.join(RES, 'spike-nopool.csv.gz')
if os.path.exists(src):
    reqs, fails, durs, vus = defaultdict(int), defaultdict(int), defaultdict(list), {}
    for r in rows(src):
        t = int(float(r['timestamp']))
        m = r['metric_name']
        if m == 'http_req_duration':
            durs[t].append(float(r['metric_value']))
        elif m == 'http_reqs':
            reqs[t] += 1
        elif m == 'http_req_failed' and float(r['metric_value']) > 0:
            fails[t] += 1
        elif m == 'vus':
            vus[t] = float(r['metric_value'])
    t0 = min(set(reqs) | set(vus))
    out, last = [], 0
    for t in sorted(set(reqs) | set(vus)):
        ds = sorted(durs.get(t, []))
        last = vus.get(t, last)
        out.append({'t': t - t0, 'rps': reqs.get(t, 0), 'p95': ds[int(0.95 * (len(ds) - 1))] if ds else None,
                    'vus': last, 'fails': fails.get(t, 0)})
    json.dump(out, open(os.path.join(OUT, 'spike-nopool-timeline.json'), 'w'))

# 4) Duracion media de la iteracion (para la ley de Little)
#    Solo las repeticiones registradas en closed-<variante>.jsonl: en results/ pueden
#    quedar resumenes de corridas de prueba anteriores con el mismo nombre de archivo.
iters = defaultdict(lambda: defaultdict(list))
for variant in ['nopool', 'pool']:
    src = os.path.join(RES, f'closed-{variant}.jsonl')
    if not os.path.exists(src):
        continue
    for r in (json.loads(l) for l in open(src) if l.strip()):
        f = os.path.join(RES, f'c-{variant}-{r["VUS"]}-{r["rep"]}.json')
        m = json.load(open(f))['metrics']
        iters[variant][str(r['VUS'])].append(m['iteration_duration']['values']['avg'])
json.dump({v: {k: statistics.mean(x) for k, x in d.items()} for v, d in iters.items()},
          open(os.path.join(OUT, 'iteration-avg.json'), 'w'), indent=1)

for f in sorted(os.listdir(OUT)):
    print(f'{os.path.getsize(os.path.join(OUT, f)) // 1024:>5} KB  data/{f}')
