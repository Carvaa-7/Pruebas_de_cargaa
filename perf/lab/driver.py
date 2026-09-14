"""Driver de mediciones: levanta la registraduria (nopool | pool), corre k6 y
registra metricas de cliente (k6) y de servidor (Actuator/Prometheus).
Uso: ver perf/lab/README.md."""
import ctypes, json, os, re, subprocess, sys, threading, time, urllib.request

# Mascaras de afinidad pensadas para un i7-13620H (16 hilos): el servicio en el
# hilo 4 (nucleo P) y k6 en todos menos el 4 y su hermano de hyperthreading, el 5.
# Ajustelas a su CPU. Fuera de Windows no se fija afinidad (use taskset).
SRV_MASK = int(os.environ.get('SRV_MASK', '0x10'), 16)
K6_MASK = int(os.environ.get('K6_MASK', '0xFFCF'), 16)
WINDOWS = os.name == 'nt'


def pin(popen, mask):
    if not WINDOWS:
        return
    ok = ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.c_void_p(int(popen._handle)), ctypes.c_size_t(mask))
    if not ok:
        raise RuntimeError('no se pudo fijar afinidad')


LAB = os.path.dirname(os.path.abspath(__file__))
BASE = 'http://localhost:8080'
RESULTS = os.path.join(LAB, 'results')
os.makedirs(RESULTS, exist_ok=True)
JARS = {
    # el servicio del taller tal cual (mvn package dentro de registraduria/)
    'nopool': os.path.join(LAB, '..', '..', 'registraduria', 'target', 'registraduria-1.0-SNAPSHOT.jar'),
    # la variante con HikariCP que genera prepare_pool.py
    'pool': os.path.join(LAB, 'pool', 'target', 'registraduria-1.0-SNAPSHOT.jar'),
}
# Rangos de ids por repeticion. step.js usa ID_BASE + __VU*100000 + (__ITER % 100000),
# y con maxVUs=3000 cada corrida ocupa hasta 3,0e8 ids: las bases deben separarse mas
# que eso (con 1e8 se solapaban y aparecian DUPLICATED). Caben 3 repeticiones en un int.
REP_BASE = 600_000_000
WARMUP_BASE = 1_900_000_000


def http_get(path, timeout=5):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode('utf8')


class Server:
    def __init__(self, variant):
        self.variant = variant
        jar = os.path.abspath(JARS[variant])
        if not os.path.exists(jar):
            raise SystemExit(f'No existe {jar}. Vea perf/lab/README.md para construir la variante "{variant}".')
        self.log = open(os.path.join(RESULTS, f'server-{variant}.log'), 'w')
        self.p = subprocess.Popen(['java', '-XX:ActiveProcessorCount=1', '-Xms1g', '-Xmx1g', '-jar', jar, '--server.tomcat.mbeanregistry.enabled=true',
                                   '--management.metrics.distribution.minimum-expected-value.http.server.requests=50us'], stdout=self.log, stderr=subprocess.STDOUT)
        pin(self.p, SRV_MASK)
        for _ in range(120):
            try:
                if '"UP"' in http_get('/actuator/health', 2):
                    return
            except Exception:
                pass
            time.sleep(1)
        raise RuntimeError('servidor no arranco')

    def stop(self):
        self.p.terminate()
        try:
            self.p.wait(20)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.log.close()


BUCKET_RE = re.compile(r'^http_server_requests_seconds_bucket\{(.*?)\} ([0-9.eE+]+)$')


def server_buckets():
    """Histograma acumulado de /register (le -> count), sumando todas las series."""
    out = {}
    for line in http_get('/actuator/prometheus', 90).splitlines():
        m = BUCKET_RE.match(line)
        if not m or 'uri="/register"' not in m.group(1):
            continue
        le = re.search(r'le="([^"]+)"', m.group(1)).group(1)
        le = float('inf') if le == '+Inf' else float(le)
        out[le] = out.get(le, 0) + float(m.group(2))
    return out


def pct_from_delta(before, after, q):
    les = sorted(after)
    delta = [(le, after[le] - before.get(le, 0)) for le in les]
    total = delta[-1][1]
    if total <= 0:
        return None
    target = q * total
    prev_le, prev_c = 0.0, 0.0
    for le, c in delta:
        if c >= target:
            if le == float('inf'):
                return prev_le * 1000
            frac = (target - prev_c) / (c - prev_c) if c > prev_c else 1
            return (prev_le + frac * (le - prev_le)) * 1000
        prev_le, prev_c = le, c
    return None


def metric(name, tag=None):
    q = f'/actuator/metrics/{name}' + (f'?tag={tag}' if tag else '')
    d = json.loads(http_get(q))
    return {m['statistic']: m['value'] for m in d['measurements']}


def run_k6(env, out_name, extra=None):
    out = os.path.join(RESULTS, out_name)
    cmd = ['k6', 'run', '--quiet', '--no-color', '--summary-mode=legacy']
    for k, v in env.items():
        cmd += ['--env', f'{k}={v}']
    cmd += ['--env', f'OUT={out}']
    cmd += (extra or []) + [os.path.join(LAB, 'step.js')]
    samples = {'proc_cpu': [], 'sys_cpu': [], 'threads': [], 'tomcat_busy': []}
    stop = threading.Event()

    def sampler():
        while not stop.wait(2):
            try:
                samples['proc_cpu'].append(metric('process.cpu.usage')['VALUE'])
                samples['sys_cpu'].append(metric('system.cpu.usage')['VALUE'])
                samples['threads'].append(metric('jvm.threads.live')['VALUE'])
                try:
                    samples['tomcat_busy'].append(metric('tomcat.threads.busy')['VALUE'])
                except Exception:
                    pass
            except Exception:
                pass

    b0 = server_buckets()
    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    kp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pin(kp, K6_MASK)
    _, err = kp.communicate()
    r = subprocess.CompletedProcess(cmd, kp.returncode, '', err)
    stop.set()
    t.join()
    b1 = server_buckets()
    data = json.load(open(out))
    m = data['metrics']
    dur = m['http_req_duration']['values']
    avg = lambda xs: sum(xs) / len(xs) if xs else None
    row = {
        **env,
        'k6_exit': r.returncode,
        'reqs': m['http_reqs']['values']['count'],
        'rps': m['http_reqs']['values']['rate'],
        'avg': dur['avg'], 'p50': dur['med'], 'p90': dur['p(90)'], 'p95': dur['p(95)'], 'p99': dur['p(99)'], 'max': dur['max'],
        'waiting_p95': m['http_req_waiting']['values']['p(95)'],
        'blocked_p95': m['http_req_blocked']['values']['p(95)'],
        'fail_rate': m['http_req_failed']['values']['rate'],
        'checks_rate': m['checks']['values']['rate'],
        'dropped': m.get('dropped_iterations', {}).get('values', {}).get('count', 0),
        'vus_max': m.get('vus_max', {}).get('values', {}).get('value'),
        'srv_p50': pct_from_delta(b0, b1, 0.50),
        'srv_p95': pct_from_delta(b0, b1, 0.95),
        'srv_p99': pct_from_delta(b0, b1, 0.99),
        'proc_cpu': avg(samples['proc_cpu']), 'sys_cpu': avg(samples['sys_cpu']),
        'threads_max': max(samples['threads']) if samples['threads'] else None,
        'tomcat_busy_max': max(samples['tomcat_busy']) if samples['tomcat_busy'] else None,
    }
    if r.returncode not in (0, 99):
        row['stderr'] = r.stderr[-2000:]
    return row


def fmt(row):
    keys = ['VUS', 'RATE', 'rps', 'avg', 'p50', 'p95', 'p99', 'srv_p50', 'srv_p95', 'srv_p99', 'vus_max', 'fail_rate', 'checks_rate', 'dropped', 'sys_cpu', 'threads_max', 'tomcat_busy_max']
    return '  '.join(f'{k}={row[k]:.3g}' if isinstance(row.get(k), float) else f'{k}={row.get(k)}' for k in keys if k in row)


def append(fname, row):
    with open(os.path.join(RESULTS, fname), 'a') as f:
        f.write(json.dumps(row) + '\n')


def fresh(variant):
    """Servicio recien arrancado + calentamiento: cada escalon parte de una base vacia."""
    srv = Server(variant)
    run_k6({'MODE': 'closed', 'VUS': 50, 'DUR': '20s', 'ID_BASE': WARMUP_BASE}, 'warmup.json')
    return srv


def main():
    if WINDOWS:
        # evita que Windows suspenda el equipo mientras mide (se libera al terminar el proceso)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    exp = sys.argv[1]
    variant = sys.argv[2]
    if exp in ('closed', 'open'):
        steps = [int(x) for x in sys.argv[3].split(',')]
        reps = int(sys.argv[5]) if len(sys.argv) > 5 else 1
        if reps > 3:
            raise SystemExit('Maximo 3 repeticiones por escalon (ver REP_BASE).')
        key = 'VUS' if exp == 'closed' else 'RATE'
        fname = os.path.join(RESULTS, f'{exp}-{variant}.jsonl')
        done = [json.loads(l)[key] for l in open(fname)] if os.path.exists(fname) else []
        for v in steps:
            if done.count(v) >= reps:
                print(f'ya medido: {key}={v}', flush=True)
                continue
            srv = fresh(variant)
            try:
                for rep in range(reps):
                    base = REP_BASE * rep
                    if exp == 'closed':
                        row = run_k6({'MODE': 'closed', 'VUS': v, 'DUR': sys.argv[4], 'ID_BASE': base, 'variant': variant}, f'c-{variant}-{v}-{rep}.json')
                    else:
                        row = run_k6({'MODE': 'open', 'RATE': v, 'DUR': sys.argv[4], 'ID_BASE': base, 'variant': variant,
                                      'PRE': 300, 'MAXVUS': 3000}, f'o-{variant}-{v}-{rep}.json')
                    row['rep'] = rep
                    append(f'{exp}-{variant}.jsonl', row)
                    print(fmt(row), flush=True)
            finally:
                srv.stop()
        return
    if os.path.exists(os.path.join(RESULTS, f'{exp}-{variant}.jsonl')):
        print(f'ya medido: {exp}', flush=True)
        return
    srv = fresh(variant)
    try:
        if exp == 'hist':
            csv = os.path.join(RESULTS, f'hist-{variant}.csv.gz')
            if os.path.exists(csv):
                os.remove(csv)
            row = run_k6({'MODE': 'closed', 'VUS': sys.argv[3], 'DUR': '30s', 'ID_BASE': 0, 'variant': variant}, f'hist-{variant}.json',
                         ['--out', f'csv={csv}'])
            append(f'hist-{variant}.jsonl', row)
            print(fmt(row), flush=True)
        elif exp == 'spike':
            low, high = sys.argv[3], sys.argv[4]
            csv = os.path.join(RESULTS, f'spike-{variant}.csv.gz')
            if os.path.exists(csv):
                os.remove(csv)
            row = run_k6({'MODE': 'spike', 'LOW': low, 'HIGH': high, 'ID_BASE': 0, 'variant': variant}, f'spike-{variant}.json',
                         ['--out', f'csv={csv}'])
            append(f'spike-{variant}.jsonl', row)
            print(fmt(row), flush=True)
    finally:
        srv.stop()


if __name__ == '__main__':
    main()
