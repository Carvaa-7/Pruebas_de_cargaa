"""Diapositivas conceptuales (no dependen de las mediciones)."""
from kit import *


def s_portada(d, curve):
    s = d.slide()
    text(s, 0.8, 1.35, 7.5, 0.35, 'TESTING Y VALIDACIÓN DE SOFTWARE', size=12, color=C['s1'], bold=True, spacing=1.5)
    text(s, 0.8, 1.8, 7.2, 2.0, 'Pruebas de carga y rendimiento', size=48, bold=True, line=0.95)
    text(s, 0.8, 3.75, 6.6, 1.2,
         'Cómo medir, leer y explicar el comportamiento de un servicio cuando muchos usuarios llegan a la vez.',
         size=18, color=C['ink2'], line=1.2)
    text(s, 0.8, 5.9, 7, 0.9, [
        [('Taller: Registraduría (Spring Boot + H2) medida con k6', {'color': C['ink2']})],
        [('César Augusto Vega Fernández · Universidad de La Sabana', {'color': C['muted']})],
    ], size=13, line=1.3)
    # curva real de fondo (p95 vs VUs) como imagen de marca del deck
    p = Plot(s, 8.1, 1.2, 4.8, 4.6, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, xy([('p95', curve)]),
             xr=(1, 800), yr=(0, max(v for _, v in curve) * 1.08), xlog=True,
             inner=(0.12, 0.04, 0.84, 0.8), xtitle='usuarios virtuales (escala log)', ytitle='p95 (ms)', font_size=10)
    p.style_series(0, C['s1'], width=3)
    text(s, 8.1, 5.9, 4.8, 0.6, 'Medición real de este taller: el p95 se mantiene plano y de pronto se dispara.',
         size=11, color=C['muted'], align=PP_ALIGN.CENTER)
    return s


def s_ruta(d):
    s = d.slide('La ruta de hoy', 'Agenda', notes=(
        'Cuatro bloques. Las gráficas de los bloques 2 y 3 son mediciones reales hechas con los scripts '
        'de k6 contra la registraduría del taller; no son curvas ilustrativas.'))
    blocks = [
        ('1', 'El vocabulario', 'Anatomía de una petición, tipos de prueba y por qué se habla de p95 y no de promedio.'),
        ('2', 'Qué pasa al saturar', 'Curvas reales: throughput, latencia, cola, modelo abierto vs. cerrado y un pico.'),
        ('3', 'Escribir la prueba', 'Reglas del script, el falso verde, errores comunes y herramientas.'),
        ('4', 'Del síntoma a la causa', 'Observabilidad, gates en CI y cómo madura un equipo en rendimiento.'),
    ]
    for i, (n, t, desc) in enumerate(blocks):
        x = 0.6 + i * 3.08
        box(s, x, 1.9, 2.85, 4.4, fill='#ffffff', line=C['border'])
        text(s, x + 0.3, 2.2, 2.3, 0.9, n, size=44, bold=True, color=C['s1'])
        text(s, x + 0.3, 3.3, 2.3, 0.8, t, size=19, bold=True, line=1.0)
        text(s, x + 0.3, 4.2, 2.3, 1.9, desc, size=14, color=C['ink2'], line=1.2)
    return s


def s_anatomia(d):
    s = d.slide('Anatomía de una petición', 'Bloque 1 · Vocabulario', notes=(
        'Cada tramo es tiempo real que la petición pasa en algún lugar. La idea clave para el taller: '
        'Actuator (servidor) solo ve el tramo azul; k6 (cliente) ve desde que envía hasta que recibe. '
        'La diferencia entre ambos es red y, sobre todo, cola. Throughput no es un tramo: es cuántas '
        'peticiones terminan por segundo.'))
    y0, hbar = 2.95, 0.85
    segs = [('Conexión', 1.25, '#e9e8e3', C['ink2']), ('Envío + red', 1.35, '#e9e8e3', C['ink2']),
            ('Espera en cola', 2.75, C['s2'], '#ffffff'), ('Procesamiento: app + BD', 3.45, C['s1'], '#ffffff'),
            ('Red + recepción', 1.55, '#e9e8e3', C['ink2'])]
    x = 1.35
    xs = []
    for name, w, fill, fg in segs:
        b = box(s, x, y0, w - 0.04, hbar, fill=fill, radius=0.08)
        shape_text(b, name, size=13, color=fg, bold=True)
        xs.append((x, x + w - 0.04))
        x += w
    text(s, 0.35, y0 + 0.2, 0.9, 0.5, 'Cliente', size=13, color=C['ink2'], bold=True, align=PP_ALIGN.RIGHT)
    text(s, x + 0.1, y0 + 0.2, 1.2, 0.5, 'Cliente', size=13, color=C['ink2'], bold=True)
    text(s, xs[2][0], y0 - 0.42, 6.5, 0.3, 'dentro del servidor', size=11, color=C['muted'])
    line(s, xs[2][0], y0 - 0.1, xs[3][1], y0 - 0.1, color=C['axis'], width=1)

    def bracket(x1, x2, y, label, sub, color):
        line(s, x1, y, x2, y, color=color, width=2)
        line(s, x1, y - 0.12, x1, y, color=color, width=2)
        line(s, x2, y - 0.12, x2, y, color=color, width=2)
        text(s, x1, y + 0.08, x2 - x1, 0.3, label, size=13, bold=True, color=C['ink'])
        text(s, x1, y + 0.38, x2 - x1, 0.5, sub, size=11, color=C['ink2'], font=MONO)

    yb = y0 + hbar + 0.28
    bracket(xs[3][0], xs[3][1], yb, 'Lo que mide el servidor', 'Actuator: http.server.requests', C['s1'])
    bracket(xs[1][0], xs[4][1], yb + 0.98, 'Lo que mide k6', 'http_req_duration = sending + waiting + receiving', C['ink'])
    bracket(xs[0][0], xs[4][1], yb + 1.96, 'Tiempo de respuesta que percibe el usuario', 'incluye abrir la conexión (http_req_blocked / connecting)', C['ink2'])

    defs = [('Latencia', 'Tiempo que la petición pasa viajando por la red.'),
            ('Tiempo de procesamiento', 'Lo que tardan la aplicación y la base de datos.'),
            ('Tiempo de respuesta', 'Todo el recorrido, ida y vuelta, cola incluida.'),
            ('Throughput', 'Peticiones completadas por segundo. No es un tramo: es una tasa.')]
    for i, (t, desc) in enumerate(defs):
        xx = 0.6 + i * 3.08
        text(s, xx, 1.45, 2.9, 0.3, t, size=13, bold=True)
        text(s, xx, 1.75, 2.9, 0.6, desc, size=12, color=C['ink2'], line=1.1)
    return s


SCEN = {
    'baseline': [(0, 20), (5, 20)],
    'load': [(0, 0), (2, 200), (12, 200), (14, 0)],
    'stress': [(0, 200), (5, 600), (8, 600), (10, 0)],
    'spike': [(0, 50), (1, 300), (3, 50), (4, 0)],
    'soak': [(0, 100), (120, 100)],
}


def s_tipos(d):
    s = d.slide('Cinco preguntas, cinco perfiles de carga', 'Bloque 1 · Tipos de prueba', notes=(
        'Las formas son exactamente las de los escenarios de register_person_k6.js y register_voter_k6.js. '
        'Se elige el perfil por la pregunta que se quiere responder, no por costumbre. regression usa la misma '
        'forma que baseline para comparar dos builds; arrival es el modelo abierto (se ve más adelante).'))
    cards = [
        ('baseline', 'Línea base', '¿Cuál es nuestra referencia para comparar?', '20 VUs · 5 min', 5),
        ('load', 'Carga', '¿Cumplimos el SLO con la demanda esperada?', '0→200 VUs · 14 min', 14),
        ('stress', 'Estrés', '¿Dónde se rompe y cómo se degrada?', '200→600 VUs · 10 min', 10),
        ('spike', 'Pico', '¿Se recupera tras un salto brusco?', '50→300→50 VUs · 4 min', 4),
        ('soak', 'Resistencia', '¿Se degrada con las horas? Fugas, GC, conexiones.', '100 VUs · 2 h', 120),
    ]
    cw = 2.35
    for i, (key, name, q, shape, dur) in enumerate(cards):
        x = 0.6 + i * (cw + 0.12)
        box(s, x, 1.55, cw, 5.25, fill='#ffffff', line=C['border'])
        text(s, x + 0.2, 1.75, cw - 0.4, 0.4, name, size=17, bold=True)
        text(s, x + 0.2, 2.2, cw - 0.4, 0.3, f'SCENARIO={key}', size=10.5, color=C['s1'], font=MONO)
        pts = SCEN[key]
        p = Plot(s, x + 0.05, 2.6, cw - 0.1, 2.0, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, xy([(key, pts)]),
                 xr=(0, dur), yr=(0, 700), ymajor=200, inner=(0.2, 0.06, 0.74, 0.72), font_size=9,
                 xmajor=max(1, dur // 4) if dur < 100 else 30, xtitle='min')
        p.style_series(0, C['s1'], width=2.5)
        text(s, x + 0.2, 4.75, cw - 0.4, 0.3, shape, size=12, bold=True, color=C['ink2'])
        text(s, x + 0.2, 5.15, cw - 0.4, 1.5, q, size=13, color=C['ink'], line=1.15)
    text(s, 0.6, 6.85, 12, 0.25, 'Eje vertical: usuarios virtuales, con la misma escala en las cinco tarjetas para poder compararlas.',
         size=10, color=C['muted'])
    return s


def s_tabla_tipos(d):
    s = d.slide('Carga, estrés, pico y resistencia no son lo mismo', 'Bloque 1 · Tipos de prueba', notes=(
        'Corrección respecto a la versión anterior: soak (resistencia) no es una variante del estrés; es su '
        'propio tipo de prueba, con carga normal y larga duración. El estrés busca el límite; el soak busca '
        'lo que se acumula con el tiempo.'))
    rows = [
        ('', 'Carga', 'Estrés', 'Pico', 'Resistencia'),
        ('Pregunta', '¿Cumple el SLO con la demanda esperada?', '¿Dónde está el límite y cómo falla?', '¿Aguanta un salto brusco y se recupera?', '¿Se degrada con el paso de las horas?'),
        ('Perfil', 'Rampa realista hasta el nivel esperado', 'Escalones por encima de lo esperado', 'Salto de ×5 a ×10 en segundos', 'Carga normal, constante'),
        ('Duración', 'Minutos a una hora', 'Hasta encontrar el quiebre', 'Pocos minutos', 'Horas (2 h en el taller)'),
        ('Qué mirar', 'p95/p99 y tasa de error contra el SLO', 'Punto de quiebre y tipo de fallo', 'Tiempo de recuperación', 'Memoria, GC, conexiones abiertas'),
        ('Alarma', 'p95 > 300 ms o errores > 1 %', 'Errores que no bajan al quitar carga', 'Latencia que no vuelve a la base', 'Memoria que sube y no baja'),
    ]
    nrows, ncols = len(rows), len(rows[0])
    gs = s.shapes.add_table(nrows, ncols, Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.0))
    tbl = gs.table
    tblPr = gs._element.graphic.graphicData.tbl.tblPr
    style = tblPr.find(qn('a:tableStyleId'))
    if style is not None:
        style.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'  # sin estilo
    widths = [1.6, 2.625, 2.625, 2.625, 2.625]
    for j, w in enumerate(widths):
        tbl.columns[j].width = Inches(w)
    colors = [None, C['s1'], C['s2'], C['s7'], C['s3']]
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(0.6 if i == 0 else 0.88)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb('#ffffff' if i % 2 else C['bg'])
            cell.margin_left = cell.margin_right = Inches(0.12)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = val
            r.font.name = FONT
            if i == 0:
                r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = rgb(colors[j] or C['ink'])
            elif j == 0:
                r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = rgb(C['ink2'])
            else:
                r.font.size = Pt(13); r.font.color.rgb = rgb(C['ink'])
    return s


def s_falso_verde(d):
    s = d.slide('Un 200 OK no significa que funcionó', 'Bloque 3 · Escribir la prueba', notes=(
        'POST /register devuelve 200 para todos los resultados de negocio. Un script que solo mire el código '
        'HTTP reporta 0 % de error aunque el servicio rechace todo. Y cuidado con validar con includes: '
        '"INVALID_AGE" contiene la palabra "VALID". register_voter_k6.js compara con igualdad exacta contra la '
        'columna expected del CSV; esa es la forma correcta.'))
    text(s, 0.6, 1.5, 5.6, 0.4, 'Respuestas reales de POST /register', size=15, bold=True)
    outs = [('VALID', 'persona viva, mayor de edad, id nuevo'), ('UNDERAGE', 'edad de 0 a 17'),
            ('DEAD', 'alive = false'), ('INVALID_AGE', 'edad negativa o mayor de 120'), ('DUPLICATED', 'el id ya existe')]
    for i, (o, why) in enumerate(outs):
        y = 2.05 + i * 0.72
        box(s, 0.6, y, 5.6, 0.6, fill='#ffffff', line=C['border'])
        text(s, 0.8, y + 0.15, 1.0, 0.3, '200 OK', size=12, bold=True, color=C['goodtext'], font=MONO)
        text(s, 1.85, y + 0.15, 1.7, 0.3, o, size=13, bold=True, font=MONO)
        text(s, 3.6, y + 0.16, 2.5, 0.3, why, size=11.5, color=C['ink2'])
    text(s, 0.6, 5.75, 5.6, 0.9, 'Mismo código HTTP, cinco resultados de negocio distintos. Solo uno es un registro exitoso.',
         size=13, color=C['ink2'], line=1.2)

    text(s, 6.7, 1.5, 6, 0.4, 'Tres formas de validar, de peor a mejor', size=15, bold=True)
    pill(s, 6.7, 2.05, 'Falso verde', C['critical'], '#fbe4e4')
    code(s, 6.7, 2.45, 6.0, 0.55, "check(res, { 'ok': (r) => r.status === 200 });", size=12)
    pill(s, 6.7, 3.2, 'Trampa sutil', C['critical'], '#fbe4e4')
    code(s, 6.7, 3.6, 6.0, 0.85,
         "'body VALID': () => body.includes('VALID')\n// 'INVALID_AGE'.includes('VALID') === true", size=12, highlight={1: C['critical']})
    pill(s, 6.7, 4.65, 'Correcto', C['goodtext'], '#dff3df')
    code(s, 6.7, 5.05, 6.0, 1.15,
         "'resultado de negocio esperado': () =>\n    outcome === v.expected\n// expected viene de voters.csv",
         size=12, highlight={1: C['goodtext']})
    text(s, 6.7, 6.35, 6.0, 0.5, 'register_voter_k6.js ya usa la tercera forma, con la métrica register_failed.',
         size=11.5, color=C['muted'])
    return s


def s_reglas(d):
    s = d.slide('Cuatro reglas para que el script se parezca a la realidad', 'Bloque 3 · Escribir la prueba', notes=(
        'Cada regla tiene su contraparte en los scripts del taller. La regla 4 es la que más se rompe: si se '
        'repite la prueba sin reiniciar el servicio, los ids ya existen y todo lo que esperaba VALID devuelve '
        'DUPLICATED. No es un fallo del servicio, es estado de prueba mal gestionado.'))
    cards = [
        ('01', 'Validar el contenido, no solo el código', 'Un 200 puede traer un rechazo de negocio. Compare el cuerpo con el resultado esperado.',
         "outcome === v.expected"),
        ('02', 'Datos variados desde un CSV', 'Repetir el mismo registro calienta cachés y dispara reglas de duplicado. SharedArray carga el CSV una vez para todos los VUs.',
         "new SharedArray('voters', () => parse(open(csv)))"),
        ('03', 'Pausas de usuario (think time)', 'Un usuario lee antes de hacer clic. Sin pausas, pocos VUs generan una carga que nadie produciría.',
         "sleep(SLEEP_MS / 1000)   // 100 ms por defecto"),
        ('04', 'Gestionar el estado de la prueba', 'Ids únicos por VU e iteración. Entre corridas, reinicie el servicio o desplace el rango.',
         "ID_BASE + __VU * 1000000 + (__ITER % 1000000)"),
    ]
    for i, (n, t, desc, snippet) in enumerate(cards):
        col, row = i % 2, i // 2
        x, y = 0.6 + col * 6.15, 1.55 + row * 2.72
        box(s, x, y, 5.95, 2.55, fill='#ffffff', line=C['border'])
        text(s, x + 0.3, y + 0.22, 0.9, 0.6, n, size=26, bold=True, color=C['s2'])
        text(s, x + 1.15, y + 0.3, 4.6, 0.45, t, size=16, bold=True)
        text(s, x + 1.15, y + 0.78, 4.55, 0.95, desc, size=12.5, color=C['ink2'], line=1.15)
        code(s, x + 1.15, y + 1.8, 4.55, 0.5, snippet, size=11)
    return s


def s_errores(d, evidence):
    s = d.slide('Errores comunes y cómo reconocerlos', 'Bloque 3 · Escribir la prueba', notes=(
        'La evidencia del inyector sobrecargado es real: en la calibración de estas gráficas, con k6 y el servicio '
        'compartiendo los 16 hilos del portátil, la CPU llegó al 99 %. k6 reportaba un p95 mucho mayor que el '
        'del servidor, y la diferencia era k6 esperando CPU, no el servicio. Por eso las mediciones reales del '
        'deck se hicieron fijando el servicio a 2 núcleos y k6 al resto.'))
    rows = [
        ('Inyector sobrecargado', 'La máquina que genera la carga se queda sin CPU o red y los tiempos salen inflados.',
         'Monitorear también el inyector; separar CPUs o máquinas.', evidence),
        ('Estado de prueba sucio', 'Una segunda corrida reusa ids ya registrados y todo sale DUPLICATED.',
         'Reiniciar el servicio o usar ID_BASE entre corridas.', None),
        ('Probar solo al final', 'El cuello de botella aparece en preproducción, cuando cambiar el diseño es caro.',
         'Escenario corto en cada PR (shift-left).', None),
        ('Ignorar errores intermitentes', 'Un 0,2 % de fallos "de vez en cuando" suele ser un pool agotado o un timeout.',
         'Leer el tipo de error en k6 y el log del servidor, no solo la tasa.', None),
        ('Aleatoriedad pura', 'Con pocas iteraciones, el azar no reparte bien los casos y dos corridas no se comparan.',
         'Recorrer los datos barajados en orden, como un mazo de cartas.', None),
    ]
    text(s, 0.6, 1.5, 3.0, 0.3, 'ERROR', size=11, bold=True, color=C['muted'], spacing=1)
    text(s, 3.5, 1.5, 5.0, 0.3, 'CÓMO SE VE', size=11, bold=True, color=C['muted'], spacing=1)
    text(s, 8.7, 1.5, 4.0, 0.3, 'CÓMO EVITARLO', size=11, bold=True, color=C['muted'], spacing=1)
    y = 1.9
    for i, (e, sym, fix, ev) in enumerate(rows):
        hh = 1.25 if ev else 0.9
        line(s, 0.6, y - 0.08, 12.7, y - 0.08, color=C['grid'], width=0.75)
        text(s, 0.6, y + 0.05, 2.8, 0.6, e, size=14.5, bold=True, line=1.05)
        text(s, 3.5, y + 0.05, 5.0, 0.8, sym, size=12.5, color=C['ink2'], line=1.12)
        if ev:
            text(s, 3.5, y + 0.62, 5.0, 0.55, ev, size=11.5, color=C['s2'], bold=True, line=1.1)
        text(s, 8.7, y + 0.05, 4.0, 0.8, fix, size=12.5, line=1.12)
        y += hh
    return s


def s_distribuida(d):
    s = d.slide('Cuando un solo inyector no alcanza', 'Bloque 3 · Arquitectura de la prueba', notes=(
        'Versión sin proveedor de nube. Las tres reglas aplican igual en AWS, Azure, GCP o en un laboratorio. '
        'k6 puede distribuirse con varias instancias o con el operador de k6 en Kubernetes; JMeter y Locust '
        'tienen modo controlador/trabajadores.'))
    # inyectores
    box(s, 0.6, 1.7, 3.0, 3.3, fill='#ffffff', line=C['border'])
    text(s, 0.8, 1.85, 2.6, 0.35, 'Inyectores de carga', size=15, bold=True)
    for i in range(3):
        b = box(s, 0.9, 2.4 + i * 0.8, 2.4, 0.6, fill=C['plane'], radius=0.12)
        shape_text(b, f'k6 · nodo {i + 1}', size=12, color=C['ink2'], font=MONO)
    # balanceador
    b = box(s, 4.85, 2.9, 2.2, 0.9, fill='#ffffff', line=C['ink2'], radius=0.5)
    shape_text(b, 'Balanceador', size=14, bold=True)
    # servicio
    box(s, 8.3, 1.7, 2.3, 3.3, fill='#ffffff', line=C['border'])
    text(s, 8.5, 1.85, 2.0, 0.35, 'Sistema bajo prueba', size=15, bold=True)
    for i in range(3):
        b = box(s, 8.55, 2.4 + i * 0.8, 1.8, 0.6, fill=C['s1'], radius=0.12)
        shape_text(b, f'instancia {i + 1}', size=12, color='#ffffff', bold=True)
    b = box(s, 11.3, 2.9, 1.4, 0.9, fill=C['plane'], line=C['axis'], radius=0.12)
    shape_text(b, 'Base de\ndatos', size=13, bold=True, color=C['ink2'])
    for i in range(3):
        line(s, 3.3, 2.7 + i * 0.8, 4.85, 3.35, color=C['ink2'], arrow_end=True)
        line(s, 7.05, 3.35, 8.55, 2.7 + i * 0.8, color=C['ink2'], arrow_end=True)
    line(s, 10.35, 3.35, 11.3, 3.35, color=C['ink2'], arrow_end=True)
    # observabilidad
    b = box(s, 0.6, 5.3, 12.1, 0.55, fill=C['orange100'], radius=0.2)
    shape_text(b, 'Observabilidad de TODOS los nodos: CPU y red de los inyectores, métricas del servicio, base de datos',
               size=13, color='#8a3a14', bold=True)
    rules = [('El inyector nunca es el cuello de botella', 'Si su CPU pasa del ~80 %, los tiempos que reporta ya no son del servicio.'),
             ('Pocas IPs de origen', 'Un balanceo por IP puede mandar toda la carga a una sola instancia.'),
             ('Rampa con tiempo para escalar', 'El autoescalado reacciona en minutos; una rampa de segundos lo prueba mal.')]
    for i, (t, desc) in enumerate(rules):
        x = 0.6 + i * 4.1
        text(s, x, 6.05, 3.9, 0.3, t, size=13, bold=True)
        text(s, x, 6.37, 3.9, 0.6, desc, size=11.5, color=C['ink2'], line=1.1)
    return s


def s_herramientas(d):
    s = d.slide('Herramientas: se elige por el equipo, no por moda', 'Bloque 3 · Herramientas', notes=(
        'Se retiró TestSprite de la versión anterior: no es una herramienta de generación de carga comparable a '
        'las otras y aparecía como protagonista sin justificación. Todas estas son de código abierto. Gatling hoy '
        'tiene DSL en Java, Kotlin y Scala, no solo Scala.'))
    rows = [
        ('Herramienta', 'Cómo se escribe la prueba', 'Fortaleza', 'Buena elección cuando…'),
        ('k6', 'JavaScript; motor en Go', 'Scripts versionables, thresholds como gate de CI', 'el equipo vive en el repositorio y en CI'),
        ('Apache JMeter', 'Plan .jmx con interfaz gráfica', 'Muchos protocolos y plugins; muy conocido', 'se prueban protocolos variados o hay equipos QA sin código'),
        ('Gatling', 'DSL en Java, Kotlin o Scala', 'Alta concurrencia por nodo; reporte HTML', 'el equipo es JVM y necesita mucho volumen'),
        ('Locust', 'Python', 'Usuarios modelados como clases; UI web en vivo', 'el comportamiento del usuario es complejo'),
        ('Artillery', 'YAML + JavaScript (Node.js)', 'Configuración corta; HTTP, WebSocket', 'se quiere algo liviano en un proyecto Node'),
    ]
    gs = s.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.6), Inches(12.1), Inches(4.9))
    tbl = gs.table
    tblPr = gs._element.graphic.graphicData.tbl.tblPr
    st = tblPr.find(qn('a:tableStyleId'))
    if st is not None:
        st.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
    for j, w in enumerate([2.0, 3.1, 3.6, 3.4]):
        tbl.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(0.55 if i == 0 else 0.87)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(C['blue100'] if i == 1 else ('#ffffff' if i % 2 == 0 else C['bg']))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.14)
            p = cell.text_frame.paragraphs[0]
            cell.text_frame.word_wrap = True
            r = p.add_run()
            r.text = val
            r.font.name = FONT
            r.font.size = Pt(12 if i == 0 else 13)
            r.font.bold = i == 0 or j == 0
            r.font.color.rgb = rgb(C['ink2'] if i == 0 else C['ink'])
    text(s, 0.6, 6.6, 12, 0.3, 'Resaltada: la herramienta del taller. Los conceptos (VUs, rampas, percentiles, umbrales) son los mismos en todas.',
         size=11, color=C['muted'])
    return s


def s_embudo(d):
    s = d.slide('Del síntoma a la causa en tres niveles', 'Bloque 4 · Diagnóstico', notes=(
        'Corrección: "memory leak" es fuga de memoria, no bloqueo. Cada nivel responde una pregunta distinta y '
        'usa una fuente distinta. En el taller: nivel 1 es el resumen de k6, nivel 2 es comparar con '
        'http.server.requests de Actuator, nivel 3 son hilos, pool y GC.'))
    levels = [
        ('1', '¿Qué ve el usuario?', 'El síntoma', 'k6: p95 / p99, http_req_failed, register_failed, peticiones por segundo', 12.1, C['blue250']),
        ('2', '¿Dónde se va el tiempo?', 'La ubicación', 'Actuator: http.server.requests. Si el servidor dice 1 ms y k6 dice 90 ms, el tiempo está en la cola, no en el código. Con varios servicios: trazas distribuidas (OpenTelemetry).', 10.5, C['s1']),
        ('3', '¿Por qué?', 'La causa raíz', 'tomcat.threads.busy, jvm.threads.live, jvm.gc.pause, CPU, conexiones del pool. Causas típicas: conexión nueva por petición, pool agotado, fuga de memoria, consulta sin índice.', 8.9, C['blue600']),
    ]
    y = 1.6
    for n, q, tag, desc, w, color in levels:
        x = 0.6 + (12.1 - w) / 2
        b = box(s, x, y, w, 1.55, fill=color, radius=0.08)
        fg = C['ink'] if color == C['blue250'] else '#ffffff'
        text(s, x + 0.35, y + 0.2, 0.6, 0.8, n, size=36, bold=True, color=fg)
        text(s, x + 1.1, y + 0.2, 3.3, 0.4, q, size=17, bold=True, color=fg)
        text(s, x + 1.1, y + 0.62, 3.0, 0.3, tag, size=12, color=fg)
        text(s, x + 4.3, y + 0.2, w - 4.6, 1.2, desc, size=12.5, color=fg, line=1.15, anchor=MSO_ANCHOR.MIDDLE)
        y += 1.72
    return s


def s_ci(d):
    s = d.slide('El rendimiento como gate del pipeline', 'Bloque 4 · Integración continua', notes=(
        'Umbrales iguales a los del script del taller (p95 < 300 ms, p99 < 800 ms, error < 1 %). La versión '
        'anterior decía 200 ms; se alineó con el taller. k6 termina con código 99 cuando se cruza un threshold, '
        'así que el paso de CI falla sin lógica adicional. En PR solo el escenario corto; load/stress/soak en '
        'ejecución nocturna o manual.'))
    steps = [('Build', 'mvn package\npruebas unitarias'), ('Levantar servicio', 'java -jar …\nespera /actuator/health'),
             ('Prueba de carga', 'k6 run\nSCENARIO=baseline'), ('Gate', 'thresholds\nexit code 99 = falla'),
             ('Publicar evidencia', 'summary-*.json\ncomo artefacto')]
    for i, (t, sub) in enumerate(steps):
        x = 0.6 + i * 2.48
        gate = i == 3
        b = box(s, x, 1.65, 2.2, 1.6, fill=C['orange100'] if gate else '#ffffff', line=C['s2'] if gate else C['border'], line_w=2 if gate else 1)
        text(s, x + 0.2, 1.8, 1.8, 0.4, t, size=15, bold=True)
        text(s, x + 0.2, 2.3, 1.9, 0.9, sub, size=11, color=C['ink2'], font=MONO, line=1.2)
        if i < 4:
            line(s, x + 2.22, 2.45, x + 2.46, 2.45, color=C['ink2'], width=1.5, arrow_end=True)
    code(s, 0.6, 3.6, 6.6, 2.75,
         "thresholds: {\n"
         "  http_req_failed: ['rate<0.01'],\n"
         "  'http_req_duration{status:200}':\n"
         "      ['p(95)<300', 'p(99)<800'],\n"
         "  register_failed: ['rate<0.01'],\n"
         "}", size=14)
    text(s, 0.6, 6.45, 6.6, 0.4, 'Tomado de perf/scripts/register_voter_k6.js', size=11, color=C['muted'])
    notes = [('El umbral es el SLO escrito en código', 'Si el p95 pasa de 300 ms o los errores del 1 %, k6 sale con código 99 y el paso falla solo.'),
             ('Corto en cada PR, largo de noche', 'load dura 14 minutos y soak dos horas: bloquearían la revisión.'),
             ('El pipeline levanta el servicio', 'Y espera a /actuator/health con un bucle, no con un sleep fijo.')]
    for i, (t, desc) in enumerate(notes):
        y = 3.6 + i * 0.97
        text(s, 7.6, y, 5.1, 0.35, t, size=14, bold=True)
        text(s, 7.6, y + 0.35, 5.1, 0.6, desc, size=12, color=C['ink2'], line=1.12)
    return s


def s_madurez(d):
    s = d.slide('¿En qué nivel está su equipo?', 'Bloque 4 · Madurez', notes=(
        'Se reemplazó el nivel 4 anterior (centrado en una plataforma comercial) por prácticas verificables. '
        'El taller lleva al estudiante del nivel 1 al 3.'))
    levels = [
        ('1', 'Reactivo', 'Se prueba cuando algo falla en producción. Herramienta básica, sin escenarios ni SLO.'),
        ('2', 'Scripting realista', 'Datos variados, validación de negocio, pausas, estado de prueba controlado.'),
        ('3', 'Continuo', 'Escenario corto en cada PR con gate; los largos, programados. Regresiones detectadas antes de producción.'),
        ('4', 'Guiado por SLO', 'Observabilidad en producción, presupuesto de error y experimentos de caos para validar la recuperación.'),
    ]
    for i, (n, t, desc) in enumerate(levels):
        x = 0.6 + i * 3.08
        y = 4.35 - i * 0.8
        h = 6.75 - y
        fill = C['s1'] if i == 2 else ('#ffffff' if i < 2 else C['plane'])
        fg = '#ffffff' if i == 2 else C['ink']
        box(s, x, y, 2.9, h, fill=fill, line=None if i == 2 else C['border'], radius=0.04)
        text(s, x + 0.25, y + 0.2, 0.8, 0.6, n, size=30, bold=True, color=fg if i == 2 else C['s1'])
        text(s, x + 0.25, y + 0.85, 2.45, 0.4, t, size=16, bold=True, color=fg)
        text(s, x + 0.25, y + 1.3, 2.45, 1.7, desc, size=12, color='#ffffff' if i == 2 else C['ink2'], line=1.15)
    text(s, 0.6, 1.55, 6.0, 0.6, 'Al terminar el taller, un equipo debería estar en el nivel 3.', size=15, color=C['ink2'])
    return s


def s_cierre(d):
    s = d.slide(notes='Cierre: conecta con los entregables del README.')
    text(s, 0.8, 1.2, 11.5, 1.6, 'El rendimiento no se agrega al final.\nSe diseña, se mide y se vigila.', size=38, bold=True, line=1.05)
    text(s, 0.8, 3.0, 11, 0.4, 'Para entregar en este taller', size=16, bold=True, color=C['s1'])
    items = ['Baseline, carga y estrés ejecutados, con su summary-*.json',
             'Matriz de rendimiento: escenario, SLO, resultado',
             'p95 de k6 comparado con el p95 de Actuator, y la explicación de la diferencia',
             'Antes y después de agregar un pool de conexiones',
             'Pipeline con gate y al menos un defecto documentado en defectos.md']
    for i, it in enumerate(items):
        y = 3.55 + i * 0.58
        dot(s, 0.95, y + 0.17, 0.14, C['s1'])
        text(s, 1.25, y, 11, 0.4, it, size=16)
    return s
