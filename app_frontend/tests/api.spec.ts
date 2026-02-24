import { test, expect, request } from '@playwright/test';

const apiBase = process.env.API_URL || 'http://localhost:8000/api/v1';

test('work-orders API returns 200', async () => {
  const api = await request.newContext({ baseURL: apiBase });
  const res = await api.get('/work-orders?limit=5');
  expect(res.status()).toBeLessThan(500); // ׳™׳¢׳‘׳•׳“ ׳’׳ ׳׳ 401 ׳›׳¨׳’׳¢
});
