import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const siteRoot = resolve(import.meta.dirname, '..');

const files = [
  resolve(siteRoot, 'src/lib/leaderboard.ts'),
  resolve(siteRoot, 'src/components/LeaderboardControls.astro'),
  resolve(siteRoot, 'src/components/LeaderboardTable.astro'),
  resolve(siteRoot, 'src/pages/leaderboard/index.astro'),
  resolve(siteRoot, 'src/pages/leaderboard/[scenario].astro'),
].map((path) => [path, readFileSync(path, 'utf8')]);

const combined = files.map(([, text]) => text).join('\n');

const requiredSnippets = [
  ['scenario selector', 'name="scenario"'],
  ['search input', 'type="search"'],
  ['confidence filter', 'name="confidence"'],
  ['eligibility filter', 'name="eligibility"'],
  ['empty search state', '没有符合当前筛选条件的 reviewed alpha 记录'],
  ['missing data state', '缺少 reviewed scores 静态 JSON'],
  ['malformed data state', '静态 JSON 格式异常'],
  ['no placeholder fallback', '不会用占位数据补齐排名'],
  ['missing dimensions near row', 'missing_dimensions'],
  ['freshness warning', 'stale/unknown freshness'],
  ['scenario route uses filters', 'buildLeaderboardView(Astro.url.searchParams, scenarioId)'],
  ['overall route uses filters', 'buildLeaderboardView(Astro.url.searchParams)'],
];

const missing = requiredSnippets.filter(([, snippet]) => !combined.includes(snippet));

if (missing.length > 0) {
  console.error('Leaderboard content contract failed. Missing snippets:');
  for (const [label, snippet] of missing) {
    console.error(`- ${label}: ${snippet}`);
  }
  process.exit(1);
}

console.log('Leaderboard content contract passed.');
