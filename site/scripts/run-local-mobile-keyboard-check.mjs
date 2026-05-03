import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawn } from 'node:child_process';

const siteRoot = resolve(import.meta.dirname, '..');
const distDir = resolve(siteRoot, 'dist');
const port = 3101;
const host = '127.0.0.1';
if (!existsSync(resolve(distDir, 'index.html'))) {
  console.error('site/dist/index.html not found. Run npm --prefix site run build first.');
  process.exit(1);
}

const scoresPayload = JSON.parse(readFileSync(resolve(siteRoot, 'public/api/v1/scores.json'), 'utf8'));
const firstModelId = scoresPayload.scores?.[0]?.canonical_id;
const modelRoute = firstModelId ? `/models/${firstModelId}/` : '/leaderboard/';

const routes = ['/', '/leaderboard/', '/leaderboard/Coding/', modelRoute, '/methodology/', '/sources/', '/selector/'];

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
  await waitForServer(`http://${host}:${port}/`);
  const failures = [];
  const checked = [];
  for (const route of routes) {
    const response = await fetch(`http://${host}:${port}${route}`);
    if (!response.ok) {
      failures.push(`${route}: HTTP ${response.status}`);
      continue;
    }
    const html = await response.text();
    checked.push({ route, bytes: html.length });
    if (!html.includes('name="viewport"')) failures.push(`${route}: missing viewport meta`);
    if (!html.includes('skip-link')) failures.push(`${route}: missing skip link`);
    if (!html.includes('aria-label=')) failures.push(`${route}: missing accessible labels`);
    if (route.includes('/leaderboard') && !html.includes('class="responsive-table"')) failures.push(`${route}: missing responsive table markup`);
    if ((route.includes('/leaderboard') || route === '/') && !html.includes('data-label=')) failures.push(`${route}: missing mobile data-label cells`);
    if (route.includes('/models/') && !html.includes('aria-label="打开外部来源：')) failures.push(`${route}: missing evidence link accessible labels`);
  }
  const cssFiles = [...new Set((await (await fetch(`http://${host}:${port}/`)).text()).match(/\/_astro\/[^"']+\.css/g) || [])];
  let css = '';
  for (const cssFile of cssFiles) css += await (await fetch(`http://${host}:${port}${cssFile}`)).text();
  const cssChecks = [
    ['mobile table card breakpoint', '@media(max-width:640px)'],
    ['tap target minimum', 'min-height:44px'],
    ['focus-visible styling', ':focus-visible'],
    ['overflow containment', 'overflow-wrap:anywhere'],
    ['responsive min width reset', 'min-width:0'],
  ];
  const compactCss = css.replace(/\s+/g, '');
  for (const [label, snippet] of cssChecks) {
    if (!compactCss.includes(snippet)) failures.push(`CSS: missing ${label}`);
  }
  const result = { status: failures.length ? 'failed' : 'passed', checked, failures };
  console.log(JSON.stringify(result, null, 2));
  if (failures.length) process.exitCode = 1;
} finally {
  server.kill();
}
