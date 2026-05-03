import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawn } from 'node:child_process';

const siteRoot = resolve(import.meta.dirname, '..');
const distDir = resolve(siteRoot, 'dist');
const port = 3101;
const host = '127.0.0.1';

if (!existsSync(resolve(distDir, 'selector/index.html'))) {
  console.error('site/dist/selector/index.html not found. Run npm --prefix site run build first.');
  process.exit(1);
}

function waitForServer(url, attempts = 50) {
  return new Promise((resolveWait, rejectWait) => {
    let attempt = 0;
    const tick = () => {
      fetch(url)
        .then((response) => {
          if (response.ok) resolveWait();
          else throw new Error(String(response.status));
        })
        .catch((error) => {
          attempt += 1;
          if (attempt >= attempts) rejectWait(error);
          else setTimeout(tick, 100);
        });
    };
    tick();
  });
}

const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', host, '--directory', distDir], {
  stdio: ['ignore', 'pipe', 'pipe'],
});

try {
  await waitForServer(`http://${host}:${port}/selector/`);
  const failures = [];
  const selectorResponse = await fetch(`http://${host}:${port}/selector/?preset=coding&provider=OpenAI&weights=Coding:0.7,Practicality:0.3`);
  const selectorHtml = await selectorResponse.text();
  const apiResponse = await fetch(`http://${host}:${port}/api/v1/selector-data.json`);
  const apiJson = await apiResponse.json();

  if (!selectorResponse.ok) failures.push(`/selector/: HTTP ${selectorResponse.status}`);
  if (!apiResponse.ok) failures.push(`/api/v1/selector-data.json: HTTP ${apiResponse.status}`);
  if (!apiResponse.headers.get('content-type')?.includes('application/json')) failures.push('selector-data API content-type is not JSON');
  if (!Array.isArray(apiJson.presets) || apiJson.presets.length < 6) failures.push('selector-data API is missing required presets');

  const requiredHtml = [
    ['selector app container', 'data-selector-app'],
    ['selector API fetch', '/api/v1/selector-data.json'],
    ['copy/share affordance', 'data-copy-url'],
    ['preset controls', 'data-preset-buttons'],
    ['custom weights', 'data-weight-inputs'],
    ['provider filter', 'data-provider-filter'],
    ['model type filter', 'data-model-type-filter'],
    ['results container', 'data-results'],
    ['uncertainty copy', '缺失维度'],
    ['shareable URL metadata', '可分享 URL 状态'],
  ];
  for (const [label, snippet] of requiredHtml) {
    if (!selectorHtml.includes(snippet)) failures.push(`/selector/ missing ${label}`);
  }

  const builtJs = readFileSync(resolve(distDir, '_astro', readFileSync(resolve(distDir, 'selector/index.html'), 'utf8').match(/_astro\/([^"']+\.js)/)?.[1] ?? ''), 'utf8');
  if (!builtJs.includes('weightedScore')) failures.push('built selector client bundle is missing ranking score logic');
  if (!builtJs.includes('URLSearchParams')) failures.push('built selector client bundle is missing URL state restore logic');

  const result = {
    status: failures.length ? 'failed' : 'passed',
    checked: ['/selector/', '/api/v1/selector-data.json'],
    presets: apiJson.presets?.map((preset) => preset.id) ?? [],
    failures,
  };
  console.log(JSON.stringify(result, null, 2));
  if (failures.length) process.exitCode = 1;
} finally {
  server.kill();
}
