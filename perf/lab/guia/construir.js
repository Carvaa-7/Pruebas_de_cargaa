// @ts-check
/**
 * Genera la guia visual del taller (guia-visual-pruebas-de-carga.html, en la
 * raiz del repositorio) a partir de las mediciones de perf/lab/data.
 *
 *   node perf/lab/guia/construir.js                  -> guia-visual-pruebas-de-carga.html
 *   node perf/lab/guia/construir.js <salida> --fragmento   -> sin <html>/<head>, para publicar como artifact
 *
 * Es el equivalente de deck/build.py para la presentacion: la pagina lleva los
 * datos incrustados, asi que si se repiten las mediciones hay que regenerarla.
 * Sin este paso quedaria mostrando los numeros viejos sin que nadie lo note.
 *
 * Ademas de resumir las mediciones, calibra el modelo del simulador de
 * ejecucion. Ver la seccion "Modelo" mas abajo: todo lo que el simulador
 * muestra sale de aqui, y la pagina publica la calidad del ajuste.
 */
const fs = require('fs');
const path = require('path');

const DATA = path.join(__dirname, '..', 'data');
const PLANTILLA = path.join(__dirname, 'plantilla.html');
const ARGS = process.argv.slice(2).filter((x) => !x.startsWith('--'));
const SALIDA = ARGS[0]
  ? path.resolve(ARGS[0])
  : path.join(__dirname, '..', '..', '..', 'guia-visual-pruebas-de-carga.html');

const jl = (f) => fs.readFileSync(path.join(DATA, f), 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
const json = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), 'utf8'));
const r = (x, d = 1) => (x == null ? null : Math.round(x * 10 ** d) / 10 ** d);
const media = (a) => a.reduce((s, v) => s + v, 0) / a.length;
const desv = (a) => { const m = media(a); return Math.sqrt(media(a.map((v) => (v - m) ** 2))); };

/* ---------------------------------------------------------------------------
 * Mediciones resumidas (lo mismo que agrega deck/data.py: media por escalon,
 * conservando cada corrida)
 * ------------------------------------------------------------------------- */

function porEscalon(archivo, clave) {
  const g = {};
  for (const x of jl(archivo)) (g[+x[clave]] ??= []).push(x);
  return Object.keys(g).map(Number).sort((a, b) => a - b).map((k) => {
    const rs = g[k];
    return {
      x: k,
      rps: r(media(rs.map((v) => v.rps)), 0),
      p95: r(media(rs.map((v) => v.p95)), 1),
      srv: r(media(rs.map((v) => v.srv_p95)), 3),
      fail: r(media(rs.map((v) => v.fail_rate)) * 100, 2),
      drop: r(media(rs.map((v) => v.dropped)), 0),
      vusMax: r(media(rs.map((v) => v.vus_max)), 0),
      runs: rs.map((v) => ({ rps: r(v.rps, 0), p95: r(v.p95, 1), srv: r(v.srv_p95, 3), fail: r(v.fail_rate * 100, 2) })),
    };
  });
}

function histograma() {
  const h = json('hist-nopool.json');
  const pct = (q) => h[Math.min(h.length - 1, Math.ceil(q * h.length) - 1)];
  const bordes = [0, 0.5];
  while (bordes[bordes.length - 1] < 4096) bordes.push(bordes[bordes.length - 1] * 2);
  const bins = [];
  for (let i = 0; i < bordes.length - 1; i++) {
    const a = bordes[i], b = bordes[i + 1];
    const n = h.filter((v) => v >= a && v < b).length;
    bins.push({ a, b, n, pct: r((n / h.length) * 100, 2) });
  }
  const fuera = h.filter((v) => v >= bordes[bordes.length - 1]).length;
  if (fuera) { bins[bins.length - 1].n += fuera; bins[bins.length - 1].pct = r((bins[bins.length - 1].n / h.length) * 100, 2); }
  const corrida = jl('hist-nopool.jsonl')[0];
  const suma = bins.reduce((s, b) => s + b.n, 0);
  if (suma !== h.length) throw new Error(`El histograma perdio muestras: ${suma} de ${h.length}`);
  return {
    bins, n: h.length, avg: r(media(h), 2), p50: r(pct(0.5), 2), p90: r(pct(0.9), 2), p95: r(pct(0.95), 2),
    p99: r(pct(0.99), 2), max: r(h[h.length - 1], 1), vus: +corrida.VUS, dur: corrida.DUR, reqs: corrida.reqs,
    rps: r(corrida.rps, 1), srvP95: r(corrida.srv_p95, 1),
    k6: { avg: corrida.avg, p50: corrida.p50, p90: corrida.p90, p95: corrida.p95, p99: corrida.p99, max: corrida.max, fail: corrida.fail_rate },
  };
}

/* ---------------------------------------------------------------------------
 * Modelo del simulador de ejecucion
 *
 * El simulador "reproduce" los escenarios del script (baseline, load, stress,
 * spike, soak, arrival) segundo a segundo. No son corridas: aplica a la forma
 * de cada escenario lo que se midio en regimen estable para cada numero de VUs.
 *
 * 1. THROUGHPUT. Las medias por escalon son ruidosas (con pool pasa de 9.442
 *    req/s con 10 VUs a 5.124 con 25). Interpolarlas haria que una rampa
 *    subiera y bajara de golpe, y eso se leeria como comportamiento. Se ajusta
 *    la Ley de Escalabilidad Universal (USL, Gunther):
 *        X(N) = lambda N / (1 + sigma (N - 1) + kappa N (N - 1))
 *    sigma es la contencion (trabajo que no se paraleliza) y kappa la
 *    coherencia (coordinacion que crece con el cuadrado de N). Se publica el
 *    error del ajuste junto a la variacion entre corridas identicas.
 *
 * 2. p95 Y FALLOS. Interpolacion en escala logaritmica de VUs entre las medias
 *    medidas, forzada a no decrecer: con mas carga el p95 no mejora, y los
 *    descensos medidos (sin pool, 1.420 ms con 400 VUs y 1.086 con 800) son
 *    ruido de dos corridas que difieren hasta un 77 %.
 *
 * 3. VARIACION SEGUNDO A SEGUNDO. Una simulacion lisa enganaria: las corridas
 *    reales oscilan. La amplitud se toma de la linea de tiempo real del pico
 *    (desviacion del logaritmo en tramos de carga constante).
 * ------------------------------------------------------------------------- */

function ajustarUSL(pts) {
  const error = (s, k) => {
    const res = pts.map(([N, X]) => Math.log(X) - Math.log(N) + Math.log(1 + s * (N - 1) + k * N * (N - 1)));
    const m = media(res);
    return { e: res.reduce((a, b) => a + (b - m) ** 2, 0), lambda: Math.exp(m) };
  };
  let mejor = { e: Infinity, lambda: 0, s: 0, k: 0 };
  for (let i = 0; i <= 200; i++) {
    for (let j = 0; j <= 200; j++) {
      const s = i === 0 ? 0 : 10 ** (-5 + (5 * i) / 200);
      const k = j === 0 ? 0 : 10 ** (-9 + (7 * j) / 200);
      const res = error(s, k);
      if (res.e < mejor.e) mejor = { ...res, s, k };
    }
  }
  const pred = (N) => (mejor.lambda * N) / (1 + mejor.s * (N - 1) + mejor.k * N * (N - 1));
  const errores = pts.map(([N, X]) => Math.abs(pred(N) / X - 1) * 100);
  return { lambda: r(mejor.lambda, 1), sigma: mejor.s, kappa: mejor.k, errorMedio: r(media(errores), 0), errorMax: r(Math.max(...errores), 0) };
}

function tablaNoDecreciente(escalones, campo) {
  let max = -Infinity;
  return escalones.map((e) => { max = Math.max(max, e[campo]); return [e.x, r(max, 3)]; });
}

function variacionEntreCorridas(escalones) {
  const d = escalones.map((e) => { const [a, b] = e.runs.map((v) => v.rps); const m = (a + b) / 2; return (Math.abs(a - b) / 2 / m) * 100; });
  return { media: r(media(d), 0), max: r(Math.max(...d), 0) };
}

function variacionSegundoASegundo(puntos) {
  const tramos = [[46, 65], [86, 119]];
  const sig = (campo) => media(tramos.map(([a, b]) => desv(puntos.filter((p) => p.t >= a && p.t <= b && p[campo] > 0).map((p) => Math.log(p[campo])))));
  return { rps: r(sig('rps'), 3), p95: r(sig('p95'), 3) };
}

/* ---------------------------------------------------------------------------
 * Construccion
 * ------------------------------------------------------------------------- */

const closedPool = porEscalon('closed-pool.jsonl', 'VUS');
const closedNoPool = porEscalon('closed-nopool.jsonl', 'VUS');
const openPool = porEscalon('open-pool.jsonl', 'RATE');
const openNoPool = porEscalon('open-nopool.jsonl', 'RATE');
const pico = jl('spike-nopool.jsonl')[0];
const lineaPico = json('spike-nopool-timeline.json');
const puntosPico = lineaPico.filter((p) => p.t >= 10 && p.t < 120).map((p) => ({ t: p.t, rps: p.rps, p95: r(p.p95, 1), vus: Math.round(p.vus) }));

const modelo = {
  pool: {
    usl: ajustarUSL(closedPool.map((e) => [e.x, e.rps])),
    p95: tablaNoDecreciente(closedPool, 'p95'),
    fail: tablaNoDecreciente(closedPool, 'fail'),
    corridas: variacionEntreCorridas(closedPool),
  },
  nopool: {
    usl: ajustarUSL(closedNoPool.map((e) => [e.x, e.rps])),
    p95: tablaNoDecreciente(closedNoPool, 'p95'),
    fail: tablaNoDecreciente(closedNoPool, 'fail'),
    corridas: variacionEntreCorridas(closedNoPool),
  },
  ruido: variacionSegundoASegundo(puntosPico),
};

const datos = {
  closedPool, closedNoPool, openPool, openNoPool,
  hist: histograma(),
  spike: { low: +pico.LOW, high: +pico.HIGH, reqs: pico.reqs, p95: r(pico.p95, 1), fail: pico.fail_rate, points: puntosPico },
  iter: json('iteration-avg.json'),
  modelo,
};

const plantilla = fs.readFileSync(PLANTILLA, 'utf8');
if (!plantilla.includes('/*__DATOS__*/null')) throw new Error('La plantilla no tiene el marcador /*__DATOS__*/null');
const cuerpo = plantilla.replace('/*__DATOS__*/null', JSON.stringify(datos));
// Por defecto, un documento completo: el archivo del repositorio se abre con
// doble clic, y sin <meta charset> las tildes pueden verse rotas. Con
// --fragmento sale sin envoltura, que es lo que espera un artifact.
const html = process.argv.includes('--fragmento')
  ? cuerpo
  : `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
${cuerpo.slice(0, cuerpo.indexOf('<div class="envoltura">'))}</head>
<body>
${cuerpo.slice(cuerpo.indexOf('<div class="envoltura">'))}
</body>
</html>
`;
fs.writeFileSync(SALIDA, html, 'utf8');

const u = (m) => `lambda=${m.usl.lambda} sigma=${m.usl.sigma.toExponential(2)} kappa=${m.usl.kappa.toExponential(2)} error medio ${m.usl.errorMedio} % (max ${m.usl.errorMax} %) · corridas identicas difieren ${m.corridas.media} % (max ${m.corridas.max} %)`;
console.log(`Guia generada: ${SALIDA}`);
console.log(`  modelo con pool: ${u(modelo.pool)}`);
console.log(`  modelo sin pool: ${u(modelo.nopool)}`);
console.log(`  variacion por segundo (desv. del log): rps ${modelo.ruido.rps} · p95 ${modelo.ruido.p95}`);
