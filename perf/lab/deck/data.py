"""Lee las mediciones resumidas de perf/lab/data (las genera export_data.py)."""
import json, math, os, statistics
from collections import defaultdict

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def jsonl(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def by_step(rows, key):
    """Agrupa las corridas por escalón (VUS o RATE) y promedia cada métrica."""
    g = defaultdict(list)
    for r in rows:
        g[int(r[key])].append(r)
    out = []
    for k in sorted(g):
        rs = g[k]
        agg = {'step': k, 'n': len(rs), 'runs': rs}
        for f in ['rps', 'avg', 'p50', 'p90', 'p95', 'p99', 'srv_p50', 'srv_p95', 'srv_p99', 'fail_rate', 'dropped', 'vus_max', 'proc_cpu']:
            vals = [r[f] for r in rs if r.get(f) is not None]
            agg[f] = statistics.mean(vals) if vals else None
            agg[f + '_min'] = min(vals) if vals else None
            agg[f + '_max'] = max(vals) if vals else None
        out.append(agg)
    return out


def hist(name='hist-nopool.json'):
    vals = json.load(open(os.path.join(DATA, name)))

    def pct(q):
        return vals[min(len(vals) - 1, int(math.ceil(q * len(vals))) - 1)]

    return {'vals': vals, 'n': len(vals), 'avg': statistics.mean(vals), 'p50': pct(0.5), 'p90': pct(0.9),
            'p95': pct(0.95), 'p99': pct(0.99), 'max': vals[-1]}


def timeline(name='spike-nopool-timeline.json'):
    return json.load(open(os.path.join(DATA, name)))


def iter_avg(variant, vus):
    """Duración media de la iteración (ms) de un escalón del modelo cerrado."""
    return json.load(open(os.path.join(DATA, 'iteration-avg.json'))).get(variant, {}).get(str(vus))
