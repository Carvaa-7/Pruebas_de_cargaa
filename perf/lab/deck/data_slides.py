"""Diapositivas construidas con las mediciones reales."""
import math
from kit import *
import data as D

SETUP = ('k6 1.3 contra la registraduría del taller (Spring Boot 2.7 + H2 en memoria), portátil i7-13620H. '
         'Servicio fijado a 1 núcleo y k6 a otros 14 hilos, para que el cuello de botella fuera el servidor y no el inyector.')


def es(v, dec=0):
    """Número con formato es-CO: miles con punto, decimales con coma."""
    s = f'{v:,.{dec}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


def ms(v):
    if v >= 10000:
        return es(v / 1000, 1) + ' s'
    if v >= 1000:
        return es(v / 1000, 2) + ' s'
    if v >= 10:
        return es(v) + ' ms'
    if v >= 1:
        return es(v, 1) + ' ms'
    return es(v, 2) + ' ms'


def source(s, extra=''):
    text(s, 0.6, 6.62, 12.1, 0.4, 'Fuente: ' + (extra + ' ' if extra else '') + SETUP, size=9, color=C['muted'], line=1.05)


def callout(s, x, y, w, title, body, color=None, size=12):
    text(s, x, y, w, 0.3, title, size=size + 1, bold=True, color=color or C['ink'])
    text(s, x, y + 0.32, w, 1.2, body, size=size, color=C['ink2'], line=1.15)


def label_at(s, x, y, t, color=None, size=11, bold=True, align=PP_ALIGN.LEFT, w=2.2):
    ox = {PP_ALIGN.LEFT: 0, PP_ALIGN.CENTER: -w / 2, PP_ALIGN.RIGHT: -w}[align]
    return text(s, x + ox, y, w, 0.3, t, size=size, bold=bold, color=color or C['ink'], align=align)


def nice_max(v):
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * exp >= v:
            return m * exp


def log_range(lo, hi):
    return 10 ** math.floor(math.log10(lo)), 10 ** math.ceil(math.log10(hi))


def runs_xy(steps, key):
    return [(r['step'], x[key]) for r in steps for x in r['runs'] if x.get(key)]


# ------------------------------------------------------------ percentiles

def s_percentiles(d):
    h = D.hist()
    run = D.jsonl('hist-nopool.jsonl')[-1]
    s = d.slide(f'Promedio: {ms(h["avg"])}. El 1 % más lento: más de {ms(h["p99"])}.',
                'Bloque 1 · Percentiles', notes=(
        f'Distribución real de {es(h["n"])} peticiones con {run["VUS"]} VUs durante 30 s, con el código del taller tal cual '
        f'(sin pool). Los intervalos se duplican (0-5, 5-10, 10-20...) porque la cola es muy larga. El promedio mezcla a los '
        f'rápidos con los lentos y no describe a nadie. El p95 dice: el 95 % de las peticiones tardó esto o menos. '
        f'Por eso los SLO del taller se escriben en p95 y p99. Máximo observado: {ms(h["max"])}.'))
    vals = h['vals']
    edges = [0, 5, 10, 20, 40, 80, 160, 320, 640, 1280]
    counts = [0] * len(edges)
    for v in vals:
        i = max(j for j, e in enumerate(edges) if v >= e)
        counts[i] += 1
    pct = [100 * c / len(vals) for c in counts]
    cats = [f'{edges[i]}–{edges[i + 1]}' for i in range(len(edges) - 1)] + [f'>{edges[-1]}']
    ymax = nice_max(max(pct) * 1.25)
    p = Plot(s, 0.5, 1.6, 8.5, 4.9, XL_CHART_TYPE.COLUMN_CLUSTERED, cat(cats, [('% de peticiones', pct)]),
             yr=(0, ymax), inner=(0.08, 0.05, 0.9, 0.8), xtitle='tiempo de respuesta (ms); cada intervalo duplica al anterior',
             ytitle='% de peticiones', gap=12, font_size=10, yfmt='0"%"')
    p.style_series(0, C['blue250'])
    n = len(cats)

    def xpos(v):
        i = max(j for j, e in enumerate(edges) if v >= e)
        if i == n - 1:
            f = 0.5
        elif i == 0:
            f = v / edges[1]
        else:
            f = math.log(v / edges[i]) / math.log(edges[i + 1] / edges[i])
        return p.left + (p.right - p.left) * (i + f) / n

    marks = [('p50', h['p50'], C['ink2']), ('promedio', h['avg'], C['ink2']), ('p95', h['p95'], C['s2']), ('p99', h['p99'], C['critical'])]
    for i, (name, v, col) in enumerate(marks):
        x = xpos(v)
        line(s, x, p.top + 0.05 + 0.34 * i + 0.3, x, p.bottom, color=col, width=2 if name in ('p95', 'p99') else 1.25)
        label_at(s, x + 0.06, p.top + 0.05 + 0.34 * i, f'{name} {ms(v)}', color=col, size=11)
    x0 = 9.35
    callout(s, x0, 1.7, 3.45, 'Cómo leerlo', 'Cada barra es la fracción de peticiones que tardó ese tiempo. Las barras de la derecha son los usuarios con peor suerte.')
    rows = [('p50', h['p50'], 'la mitad tardó menos'), ('p95', h['p95'], '95 de cada 100 tardaron menos'), ('p99', h['p99'], '99 de cada 100 tardaron menos')]
    for i, (k, v, desc) in enumerate(rows):
        y = 3.45 + i * 0.8
        text(s, x0, y, 1.0, 0.4, k, size=16, bold=True, color=[C['ink2'], C['s2'], C['critical']][i])
        text(s, x0 + 0.85, y, 2.6, 0.4, ms(v), size=16, bold=True)
        text(s, x0 + 0.85, y + 0.35, 2.6, 0.3, desc, size=11, color=C['ink2'])
    text(s, x0, 5.9, 3.45, 0.6, f'El p99 es {es(h["p99"] / h["avg"], 0)} veces el promedio.', size=14, bold=True)
    source(s, f'{es(h["n"])} peticiones, {run["VUS"]} VUs, 30 s, código sin pool.')
    return s


# ------------------------------------------------------------ saturación

def s_saturacion(d):
    st = D.by_step(D.jsonl('closed-pool.jsonl'), 'VUS')
    plateau = [r for r in st if r['step'] >= 10]
    cap = sorted(r['rps'] for r in plateau)[len(plateau) // 2]
    s = d.slide('Más usuarios no es más throughput: es más espera', 'Bloque 2 · Qué pasa al saturar', notes=(
        'Modelo cerrado (constant-vus), sin pausas, servicio con pool. Con 1 VU el núcleo del servidor tiene tiempo libre; '
        'con 10 ya está lleno y el throughput deja de crecer (varía entre corridas porque es un portátil, ver los puntos). '
        'Desde ahí cada VU extra solo agrega cola. Ley de Little: usuarios en el sistema = throughput × tiempo por iteración. '
        'Si el throughput no puede crecer, lo único que crece es el tiempo. La iteración incluye el trabajo del propio k6 '
        '(armar el JSON, validar), por eso es mayor que http_req_duration.'))
    xr = (1, 1000)
    ymax = nice_max(max(x['rps'] for r in st for x in r['runs']) * 1.1)
    lo_b = min(x['rps'] for r in plateau for x in r['runs'])
    hi_b = max(x['rps'] for r in plateau for x in r['runs'])
    p1 = Plot(s, 0.5, 1.55, 6.1, 4.9, XL_CHART_TYPE.XY_SCATTER_LINES,
              xy([('mediana', [(10, cap), (1000, cap)]), ('cada corrida', runs_xy(st, 'rps'))]),
              xr=xr, yr=(0, ymax), xlog=True, inner=(0.15, 0.14, 0.8, 0.7), xtitle='usuarios virtuales (escala log)',
              ytitle='peticiones por segundo', yfmt='#,##0', font_size=10)
    p1.style_series(0, C['s1'], width=2)
    p1.style_series(1, C['s1'], marker=True, no_line=True, marker_size=7)
    band = box(s, p1.px(10), p1.py(hi_b), p1.right - p1.px(10), p1.py(lo_b) - p1.py(hi_b), fill=C['blue100'], radius=0)
    s.shapes._spTree.remove(band._element)
    s.shapes._spTree.insert(2, band._element)
    text(s, 0.6, 1.55, 5.8, 0.35, 'Throughput', size=15, bold=True)
    text(s, 0.6, 1.88, 5.8, 0.3, 'puntos: cada corrida · franja: rango entre corridas desde 10 VUs', size=10, color=C['muted'])
    label_at(s, p1.px(10) + 0.1, p1.py(lo_b) + 0.05, f'techo ≈ {es(round(cap, -3))} req/s; entre {es(round(lo_b, -2))} y {es(round(hi_b, -2))} según la corrida', color=C['ink2'], size=10.5, w=4.6)

    ymax2 = nice_max(max(x['p95'] for r in st for x in r['runs']) * 1.1)
    p2 = Plot(s, 6.75, 1.55, 6.1, 4.9, XL_CHART_TYPE.XY_SCATTER_LINES,
              xy([('p95', [(r['step'], r['p95']) for r in st]), ('cada corrida', runs_xy(st, 'p95'))]),
              xr=xr, yr=(0, ymax2), xlog=True, inner=(0.13, 0.14, 0.8, 0.7), xtitle='usuarios virtuales (escala log)',
              ytitle='p95 (ms)', font_size=10)
    p2.style_series(0, C['s2'], marker=True)
    p2.style_series(1, '#f3b497', marker=True, no_line=True, marker_size=6)
    text(s, 6.85, 1.55, 5.8, 0.35, 'Tiempo de respuesta (p95)', size=15, bold=True)
    text(s, 6.85, 1.88, 5.8, 0.3, 'línea: promedio · puntos claros: cada corrida', size=10, color=C['muted'])
    last = st[-1]
    label_at(s, p2.px(last['step']) - 0.15, p2.py(last['p95']) - 0.12, f'p95 {ms(last["p95"])}', color=C['s2'], size=11, align=PP_ALIGN.RIGHT)
    it = D.iter_avg('pool', last['step'])
    little = last['step'] / last['rps'] * 1000
    bx, by = p2.left + 0.15, p2.top + 0.05
    box(s, bx, by, 3.35, 1.1, fill='#ffffff', line=C['border'])
    text(s, bx + 0.15, by + 0.1, 3.1, 0.3, f'Ley de Little con {last["step"]} VUs', size=11, bold=True)
    text(s, bx + 0.15, by + 0.4, 3.1, 0.6,
         f'{last["step"]} ÷ {es(last["rps"])} req/s = {es(little)} ms\niteración medida:  {es(it)} ms', size=11, color=C['ink2'], font=MONO, line=1.2)
    source(s, 'Servicio con pool, 20 s por escalón, dos corridas.')
    return s


# ------------------------------------------------------------ cliente vs servidor

def s_cliente_servidor(d):
    st = [r for r in D.by_step(D.jsonl('closed-pool.jsonl'), 'VUS') if r['srv_p95']]
    s = d.slide('Servidor rápido, usuario esperando: los dos tienen razón',
                'Bloque 2 · Cliente vs. servidor', notes=(
        'Mismo experimento que la diapositiva anterior. Azul: p95 que calcula Actuator con http.server.requests, que solo '
        'cuenta desde que un hilo de Tomcat toma la petición. Naranja: p95 de k6. La brecha es red, cola y el propio cliente. '
        'Si el servidor dice 0,1 ms y el cliente 100 ms, optimizar el código de negocio no sirve: el problema es capacidad. '
        'Es el ejercicio "cliente contra servidor" del README. El p95 del servidor se estima del histograma de Actuator '
        '(se configuró minimum-expected-value en 50 µs para tener resolución por debajo de 1 ms).'))
    lo, hi = log_range(min(r['srv_p95'] for r in st), max(r['p95'] for r in st))
    p = Plot(s, 0.5, 1.55, 8.3, 4.95, XL_CHART_TYPE.XY_SCATTER_LINES,
             xy([('p95 medido por k6 (cliente)', [(r['step'], r['p95']) for r in st]),
                 ('p95 medido por Actuator (servidor)', [(r['step'], r['srv_p95']) for r in st])]),
             xr=(1, 1000), yr=(lo, hi), xlog=True, ylog=True, inner=(0.1, 0.05, 0.84, 0.8),
             xtitle='usuarios virtuales (escala log)', ytitle='p95 (ms, escala log)', font_size=10)
    p.style_series(0, C['s2'], marker=True)
    p.style_series(1, C['s1'], marker=True)
    r = st[-1]
    label_at(s, p.px(r['step']) - 0.25, p.py(r['p95']) - 0.4, f'k6 (cliente): {ms(r["p95"])}', color=C['s2'], size=11, align=PP_ALIGN.RIGHT, w=3)
    label_at(s, p.px(r['step']) - 0.25, p.py(r['srv_p95']) - 0.42, f'Actuator (servidor): {ms(r["srv_p95"])}', color=C['s1'], size=11, align=PP_ALIGN.RIGHT, w=3)
    xg = p.px(r['step']) + 0.14
    line(s, xg, p.py(r['p95']) + 0.1, xg, p.py(r['srv_p95']) - 0.1, color=C['ink'], width=1.5, arrow_start=True, arrow_end=True)
    ratio = r['p95'] / r['srv_p95']
    x0 = 9.2
    text(s, x0, 1.65, 3.7, 0.5, [[(ms(r['p95']), {'color': C['s2']}), (' vs. ', {'color': C['muted'], 'size': 20}), (ms(r['srv_p95']), {'color': C['s1']})]], size=30, bold=True)
    text(s, x0, 2.35, 3.6, 0.9, f'Con {r["step"]} VUs, el p95 del cliente fue más de mil veces el del servidor.', size=14, color=C['ink2'], line=1.15)
    callout(s, x0, 3.6, 3.6, '¿Dónde está la diferencia?', 'En la red, en el propio cliente y sobre todo en la cola: peticiones que ya llegaron y esperan un hilo libre. Actuator empieza a medir cuando salen de ahí.')
    callout(s, x0, 5.2, 3.6, 'Qué hacer con esto', 'No tocar el código de negocio: aumentar capacidad o reducir el trabajo por petición.')
    source(s, 'Servicio con pool.')
    return s


# ------------------------------------------------------------ abierto vs cerrado

def s_abierto(d):
    op = D.by_step(D.jsonl('open-pool.jsonl'), 'RATE')
    opn = D.by_step(D.jsonl('open-nopool.jsonl'), 'RATE')
    s = d.slide('Modelo abierto: el tráfico no espera a que el servidor termine', 'Bloque 2 · Modelo de carga', notes=(
        'constant-arrival-rate (escenario arrival del taller) fija cuántas peticiones llegan por segundo, sin importar lo que '
        'tarde el servidor, como el tráfico real. Por debajo de la capacidad se atiende todo. Por encima, la cola crece sin '
        'límite: la latencia pasa de milisegundos a segundos, k6 necesita cada vez más VUs y descarta iteraciones '
        '(dropped_iterations). En el modelo cerrado esto no se ve: si el servidor se pone lento, los VUs envían menos, justo '
        'cuando deberían enviar más. Recuadro inferior: el código sin pool bajo el mismo experimento. '
        'Advertencia: en la segunda corrida de los escalones con más de 1.000 VUs, el esquema de ids del script de medición '
        'se solapó y parte de las respuestas fueron DUPLICATED. Es el error de estado de prueba de la regla 04; afecta el '
        'porcentaje de resultados de negocio correctos, no la forma de estas curvas.'))
    xmax = nice_max(max(r['step'] for r in op) * 1.05)
    p1 = Plot(s, 0.5, 1.55, 6.1, 4.6, XL_CHART_TYPE.XY_SCATTER_LINES,
              xy([('atendidas', [(r['step'], r['rps']) for r in op]), ('ideal', [(0, 0), (xmax, xmax)])]),
              xr=(0, xmax), yr=(0, xmax), inner=(0.15, 0.1, 0.8, 0.72), xtitle='peticiones que llegan por segundo',
              ytitle='peticiones atendidas por segundo', xfmt='#,##0', yfmt='#,##0', font_size=10)
    p1.style_series(0, C['s1'], marker=True)
    p1.style_series(1, C['axis'], width=1.25)
    text(s, 0.6, 1.55, 5.8, 0.35, 'Lo que llega vs. lo que se atiende', size=15, bold=True)
    label_at(s, p1.px(xmax * 0.1) - 0.3, p1.py(xmax * 0.1) - 0.75, 'ideal: se atiende todo', color=C['muted'], size=10, bold=False, w=2.5)
    best = max(op, key=lambda r: r['rps'])
    label_at(s, p1.px(best['step']) - 0.15, p1.py(best['rps']) - 0.15, f'máximo: {es(round(best["rps"], -2))} req/s', color=C['s1'], size=11, align=PP_ALIGN.RIGHT, w=2.6)

    lo, hi = log_range(min(r['p95'] for r in op), max(r['p95'] for r in op))
    p2 = Plot(s, 6.75, 1.55, 6.1, 4.6, XL_CHART_TYPE.XY_SCATTER_LINES, xy([('p95', [(r['step'], r['p95']) for r in op])]),
              xr=(0, xmax), yr=(lo, hi), ylog=True, inner=(0.13, 0.1, 0.8, 0.72),
              xtitle='peticiones que llegan por segundo', ytitle='p95 (ms, escala log)', xfmt='#,##0', font_size=10)
    p2.style_series(0, C['s2'], marker=True)
    text(s, 6.85, 1.55, 5.8, 0.35, 'La latencia al pasar el límite', size=15, bold=True)
    worst = op[-1]
    label_at(s, p2.px(worst['step']) - 0.15, p2.py(worst['p95']) - 0.05, f'p95 {ms(worst["p95"])}', color=C['s2'], size=11, align=PP_ALIGN.RIGHT)
    drops = [r for r in op if (r['dropped'] or 0) > 0]
    if drops:
        label_at(s, p2.left + 0.15, p2.top + 0.08, f'Con {es(worst["step"])} req/s: {es(worst["dropped"])} iteraciones', color=C['ink'], size=11, w=4.4)
        label_at(s, p2.left + 0.15, p2.top + 0.36, f'descartadas y {es(worst["vus_max"] or 0)} VUs en uso', color=C['ink'], size=11, w=4.4)
    n2 = [r for r in opn if r['step'] == 2000]
    if n2:
        r = n2[0]
        box(s, 0.6, 6.12, 12.1, 0.45, fill=C['orange100'], radius=0.2)
        text(s, 0.8, 6.2, 11.8, 0.3,
             f'Mismo experimento con el código sin pool: con 2.000 req/s llegando atendió solo {es(r["rps_min"])}–{es(r["rps_max"])} y falló el '
             f'{es(r["fail_rate_min"] * 100)}–{es(r["fail_rate_max"] * 100)} % de las peticiones.', size=12, color='#8a3a14', bold=True)
    source(s, 'constant-arrival-rate, 20 s por escalón, promedio de dos corridas.')
    return s


# ------------------------------------------------------------ pico

def s_pico(d):
    tl = D.timeline()
    tl = [r for r in tl[:-1] if r['t'] >= 10]
    run = D.jsonl('spike-nopool.jsonl')[-1]
    s = d.slide('Un pico, segundo a segundo', 'Bloque 2 · Prueba de pico', notes=(
        f'Perfil: {run["LOW"]} VUs durante 30 s, salto a {run["HIGH"]} VUs en 5 s, 40 s sostenido y regreso. Código del taller '
        'tal cual (sin pool). Tres gráficas con el mismo eje de tiempo y cada una con su escala: no se mezclan unidades en '
        'un eje. Qué observar: el throughput casi no sube porque el servidor ya estaba cerca del techo; lo que se dispara '
        'es la latencia. La pregunta clave de un spike: al bajar la carga, ¿la latencia vuelve a la base? '
        'Se omiten los primeros 10 s (k6 abriendo conexiones) y el último segundo, que queda incompleto.'))
    tmax = max(r['t'] for r in tl)
    specs = [('Usuarios virtuales', 'vus', C['ink2'], 'General'), ('Peticiones por segundo', 'rps', C['s1'], '#,##0'),
             ('p95 por segundo (ms)', 'p95', C['s2'], 'General')]
    ph = 1.55
    for i, (title, key, col, fmt) in enumerate(specs):
        y = 1.45 + i * (ph + 0.1)
        pts = [(r['t'], r[key]) for r in tl if r[key] is not None]
        ymax = nice_max(max(v for _, v in pts) * 1.1)
        p = Plot(s, 0.5, y, 9.0, ph, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, xy([(title, pts)]),
                 xr=(10, math.ceil(tmax / 10) * 10), yr=(0, ymax), inner=(0.27, 0.08, 0.7, 0.7 if i < 2 else 0.6),
                 xmajor=10, ymajor=ymax / 2, yfmt=fmt, font_size=9, xtitle='segundos desde el inicio' if i == 2 else None)
        p.style_series(0, col, width=2)
        text(s, 0.6, y + 0.4, 1.75, 0.7, title, size=12, bold=True, line=1.0)
    low = float(run['LOW'])
    base = [r for r in tl if 8 <= r['t'] <= 28 and r['p95']]
    peak = [r for r in tl if 42 <= r['t'] <= 72 and r['p95']]
    after = [r for r in tl if r['t'] >= 88 and r['p95'] and r['vus'] <= low * 1.2]
    med = lambda xs, k: sorted(x[k] for x in xs)[len(xs) // 2]
    x0 = 9.9
    text(s, x0, 1.5, 3.0, 0.3, 'MEDIANA POR TRAMO', size=10, bold=True, color=C['muted'], spacing=1)
    for i, (name, xs) in enumerate([('antes del pico', base), ('durante el pico', peak), ('después', after)]):
        y = 1.9 + i * 1.3
        text(s, x0, y, 3.0, 0.3, name, size=13, bold=True)
        if xs:
            text(s, x0, y + 0.32, 3.0, 0.45, [[('p95 ', {'color': C['ink2'], 'size': 12}), (ms(med(xs, 'p95')), {'bold': True, 'size': 18, 'color': C['s2']})]])
            text(s, x0, y + 0.78, 3.0, 0.3, f'{es(med(xs, "rps"))} req/s', size=12, color=C['ink2'])
    source(s, 'ramping-vus con --out csv, agregado por segundo, código sin pool.')
    return s


# ------------------------------------------------------------ pool

def s_pool(d):
    a = D.by_step(D.jsonl('closed-nopool.jsonl'), 'VUS')
    b = D.by_step(D.jsonl('closed-pool.jsonl'), 'VUS')
    ka, kb = {r['step']: r for r in a}, {r['step']: r for r in b}
    common = [k for k in sorted(ka) if k in kb]
    s = d.slide('Sin pool de conexiones: un defecto que solo aparece con carga', 'Bloque 4 · Antes y después', notes=(
        'RegistryRepository.getConnection() abre una conexión nueva en cada operación, dos por petición. La variante "con pool" '
        'es el mismo código usando HikariCP con 20 conexiones; el resto es idéntico, en el mismo núcleo. Con pocos VUs no hay '
        'diferencia clara: por eso ni la prueba unitaria ni la de integración lo detectan. Con concurrencia, sin pool el throughput '
        'cae, la dispersión entre corridas es enorme y aparecen errores. Y eso con H2 en memoria, sin red ni autenticación: '
        'contra una base de datos real por red, abrir cada conexión cuesta todavía más.'))
    xr = (1, 1000)
    ymax = nice_max(max(x['rps'] for r in a + b for x in r['runs']) * 1.1)
    p1 = Plot(s, 0.5, 1.55, 6.1, 4.55, XL_CHART_TYPE.XY_SCATTER_LINES,
              xy([('con pool (HikariCP)', [(r['step'], r['rps']) for r in b]), ('sin pool', [(r['step'], r['rps']) for r in a]),
                  ('con pool, corridas', runs_xy(b, 'rps')), ('sin pool, corridas', runs_xy(a, 'rps'))]),
              xr=xr, yr=(0, ymax), xlog=True, inner=(0.15, 0.16, 0.8, 0.66), xtitle='usuarios virtuales (escala log)',
              ytitle='peticiones por segundo', yfmt='#,##0', legend=True, font_size=10)
    p1.style_series(0, C['s1'], marker=True)
    p1.style_series(1, C['s2'], marker=True)
    p1.style_series(2, C['blue250'], marker=True, no_line=True, marker_size=5)
    p1.style_series(3, '#f3b497', marker=True, no_line=True, marker_size=5)
    hide_legend_entry(p1.chart, 2)
    hide_legend_entry(p1.chart, 3)
    text(s, 0.6, 1.55, 5.8, 0.35, 'Throughput', size=15, bold=True)

    lo, hi = log_range(min(x['p95'] for r in a + b for x in r['runs']), max(x['p95'] for r in a + b for x in r['runs']))
    p2 = Plot(s, 6.75, 1.55, 6.1, 4.55, XL_CHART_TYPE.XY_SCATTER_LINES,
              xy([('con pool (HikariCP)', [(r['step'], r['p95']) for r in b]), ('sin pool', [(r['step'], r['p95']) for r in a]),
                  ('con pool, corridas', runs_xy(b, 'p95')), ('sin pool, corridas', runs_xy(a, 'p95'))]),
              xr=xr, yr=(lo, hi), xlog=True, ylog=True, inner=(0.13, 0.16, 0.8, 0.66), xtitle='usuarios virtuales (escala log)',
              ytitle='p95 (ms, escala log)', legend=True, font_size=10)
    p2.style_series(0, C['s1'], marker=True)
    p2.style_series(1, C['s2'], marker=True)
    p2.style_series(2, C['blue250'], marker=True, no_line=True, marker_size=5)
    p2.style_series(3, '#f3b497', marker=True, no_line=True, marker_size=5)
    hide_legend_entry(p2.chart, 2)
    hide_legend_entry(p2.chart, 3)
    text(s, 6.85, 1.55, 5.8, 0.35, 'p95', size=15, bold=True)

    hi_steps = [k for k in common if k >= 50]
    ratios = [ka[k]['rps'] / kb[k]['rps'] for k in hi_steps]
    worst_fail = max(x['fail_rate'] for r in a for x in r['runs'])
    box(s, 0.6, 6.13, 12.1, 0.45, fill=C['blue100'], radius=0.2)
    text(s, 0.8, 6.21, 11.8, 0.3,
         f'Hasta 25 VUs, sin diferencia clara. Desde 50, sin pool atiende del {es(min(ratios) * 100)} al '
         f'{es(max(ratios) * 100)} % de lo que atiende con pool, y su peor corrida falló el {es(worst_fail * 100)} %.',
         size=12, color=C['blue600'], bold=True)
    source(s, 'Mismo código salvo el pool, 20 s por escalón, dos corridas (puntos claros).')
    return s


# ------------------------------------------------------------ lecciones al medir

def s_lecciones(d, facts):
    s = d.slide('Lo que salió mal al medir para esta clase', 'Bloque 3 · Errores reales', notes=(
        'Todo esto pasó preparando las gráficas de este deck. Son los mismos errores que pueden cometer en el taller, '
        'y cada uno produjo números que parecían válidos.'))
    for i, fact in enumerate(facts):
        title, before, after, lesson = fact[:4]
        labs = fact[4] if len(fact) > 4 else ('Antes: ', 'Después: ')
        col, row = i % 2, i // 2
        x, y = 0.6 + col * 6.15, 1.55 + row * 2.6
        box(s, x, y, 5.95, 2.42, fill='#ffffff', line=C['border'])
        text(s, x + 0.3, y + 0.2, 5.4, 0.35, title, size=16, bold=True)
        text(s, x + 0.3, y + 0.65, 5.4, 0.3, [[(labs[0], {'bold': True, 'color': C['critical']}), (before, {'color': C['ink']})]], size=12.5)
        text(s, x + 0.3, y + 1.05, 5.4, 0.3, [[(labs[1], {'bold': True, 'color': C['goodtext'] if len(fact) <= 4 else C['ink2']}), (after, {'color': C['ink']})]], size=12.5)
        text(s, x + 0.3, y + 1.5, 5.4, 0.8, lesson, size=12, color=C['ink2'], line=1.15)
    return s
