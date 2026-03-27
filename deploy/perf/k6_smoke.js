import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: Number(__ENV.VUS || 5),
  duration: __ENV.DURATION || '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
    checks: ['rate>0.99'],
  },
};

const endpoints = [
  '/',
  '/blog/',
  '/forum/',
  '/tools/',
  '/accounts/login/',
  '/api/',
];

export default function () {
  const ep = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE_URL}${ep}`, {
    timeout: __ENV.HTTP_TIMEOUT || '10s',
    tags: { endpoint: ep },
  });

  check(res, {
    'status is 200/302': (r) => r.status === 200 || r.status === 302,
  });

  sleep(0.2);
}
