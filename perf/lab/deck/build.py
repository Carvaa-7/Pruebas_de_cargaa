"""Genera la presentación a partir de perf/lab/data.

    pip install python-pptx
    python build.py [salida.pptx]      # por defecto: deck/out/deck.pptx

Las tarjetas de "Lo que salió mal al medir" (FACTS, abajo) usan números de las corridas
de calibración previas a la batería final; esas corridas no están en data/.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Deck
import static_slides as S
import data_slides as DS
import data as D

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'deck.pptx')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

d = Deck()
closed = D.by_step(D.jsonl('closed-pool.jsonl'), 'VUS')
S.s_portada(d, [(r['step'], r['p95']) for r in closed])
S.s_ruta(d)
S.s_anatomia(d)
S.s_tipos(d)
S.s_tabla_tipos(d)
DS.s_percentiles(d)
DS.s_saturacion(d)
DS.s_cliente_servidor(d)
DS.s_abierto(d)
DS.s_pico(d)
S.s_reglas(d)
S.s_falso_verde(d)
S.s_errores(d, 'Visto al preparar esta clase: CPU del portátil al 99 %; k6 reportaba p95 de 8,3 ms y el servidor menos de 1 ms.')
DS.s_lecciones(d, FACTS := [
    ('El inyector compitiendo con el servicio',
     'k6 y el servicio en los mismos 16 hilos: CPU al 99 %.',
     'servicio en 1 núcleo, k6 en otros 14 hilos.',
     'Sin separarlos, parte del tiempo que reporta k6 es k6 esperando CPU.'),
    ('La JVM no sabía cuántos núcleos tenía',
     'p99 del servidor de hasta 476 ms con 100 VUs.',
     'menos de 1 ms con -XX:ActiveProcessorCount.',
     'Una JVM que cree tener 16 CPUs pero corre en 2 dimensiona mal sus hilos de GC. Además no compartía núcleo con k6.'),
    ('Medir sin calentar',
     '3.370 req/s en la primera corrida tras arrancar.',
     '6.420 req/s en la siguiente, idéntica.',
     'El compilador JIT todavía estaba trabajando. Siempre hay un calentamiento que no se mide.'),
    ('Buscar el error solo en el log',
     '10 % de peticiones fallidas con 400 VUs.',
     'ni una sola excepción en el log del servidor.',
     'Bajo saturación, muchos fallos ocurren antes de llegar a la aplicación: conexiones y timeouts. Hay que leer los errores en k6.',
     ('Síntoma: ', 'En el log: ')),
])
S.s_distribuida(d)
S.s_herramientas(d)
S.s_embudo(d)
DS.s_pool(d)
S.s_ci(d)
S.s_madurez(d)
S.s_cierre(d)
d.save(OUT)
print('ok', OUT, d.n, 'diapositivas')
