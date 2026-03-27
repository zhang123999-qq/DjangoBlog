import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

const bizLatency = new Trend('biz_latency', true);
const bizError = new Rate('biz_error_rate');

export const options = {
  scenarios: {
    ramp_up_hold: {
      executor: 'ramping-vus',
      startVUs: Number(__ENV.START_VUS || 1),
      stages: [
        { duration: __ENV.STAGE1 || '30s', target: Number(__ENV.TARGET_VUS || 20) },
        { duration: __ENV.STAGE2 || '1m', target: Number(__ENV.TARGET_VUS || 20) },
        { duration: __ENV.STAGE3 || '30s', target: 0 },
      ],
      gracefulRampDown: '15s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
    biz_error_rate: ['rate<0.02'],
    checks: ['rate>0.98'],
  },
};

const weightedEndpoints = [
  { path: '/', w: 20 },
  { path: '/blog/', w: 20 },
  { path: '/forum/', w: 15 },
  { path: '/tools/', w: 20 },
  { path: '/accounts/login/', w: 10 },
  { path: '/api/posts/', w: 10 },
  { path: '/api/categories/', w: 5 },
];

function pickWeightedEndpoint() {
  const total = weightedEndpoints.reduce((s, e) => s + e.w, 0);
  let r = Math.random() * total;
  for (const e of weightedEndpoints) {
    r -= e.w;
    if (r <= 0) return e.path;
  }
  return '/';
}

export default function () {
  const ep = pickWeightedEndpoint();
  const start = Date.now();

  const res = http.get(`${BASE_URL}${ep}`, {
    timeout: __ENV.HTTP_TIMEOUT || '10s',
    tags: { endpoint: ep },
  });

  const ok = check(res, {
    'status is 200/302': (r) => r.status === 200 || r.status === 302,
  });

  bizLatency.add(Date.now() - start, { endpoint: ep });
  bizError.add(!ok, { endpoint: ep });

  sleep(Number(__ENV.THINK_TIME || 0.1));
}
