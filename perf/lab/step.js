// Script de medicion para las graficas de la presentacion.
// MODE=closed -> constant-vus (VUS)   |  MODE=open -> constant-arrival-rate (RATE)
// PROFILE=spike -> ramping-vus con un pico abrupto
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const MODE = __ENV.MODE || 'closed';
const DUR = __ENV.DUR || '30s';
const ID_BASE = Number(__ENV.ID_BASE || 0);
const SLEEP_MS = Number(__ENV.SLEEP_MS || 0);
const OUT = __ENV.OUT || 'summary.json';

function scenario() {
  if (MODE === 'open') {
    return {
      executor: 'constant-arrival-rate', rate: Number(__ENV.RATE), timeUnit: '1s',
      duration: DUR, preAllocatedVUs: Number(__ENV.PRE || 200), maxVUs: Number(__ENV.MAXVUS || 2000),
    };
  }
  if (MODE === 'spike') {
    return {
      executor: 'ramping-vus', startVUs: Number(__ENV.LOW),
      stages: [
        { duration: '30s', target: Number(__ENV.LOW) },
        { duration: '5s', target: Number(__ENV.HIGH) },
        { duration: '40s', target: Number(__ENV.HIGH) },
        { duration: '5s', target: Number(__ENV.LOW) },
        { duration: '40s', target: Number(__ENV.LOW) },
      ],
      gracefulRampDown: '5s',
    };
  }
  return { executor: 'constant-vus', vus: Number(__ENV.VUS), duration: DUR, gracefulStop: '5s' };
}

export const options = {
  scenarios: { run: scenario() },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  discardResponseBodies: false,
};

export default function () {
  const id = ID_BASE + __VU * 100000 + (__ITER % 100000);
  const res = http.post(BASE_URL + '/register',
    JSON.stringify({ name: 'Ana', id: id, age: 30, gender: 'FEMALE', alive: true }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' });
  check(res, { 'VALID': (r) => r.status === 200 && String(r.body).trim() === 'VALID' });
  if (SLEEP_MS > 0) sleep(SLEEP_MS / 1000);
}

export function handleSummary(data) {
  return { [OUT]: JSON.stringify(data) };
}
