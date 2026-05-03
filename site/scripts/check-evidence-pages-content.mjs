import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const siteRoot = resolve(import.meta.dirname, '..');

const files = [
  'src/lib/data.ts',
  'src/pages/models/[...id].astro',
  'src/pages/methodology/index.astro',
  'src/pages/sources/index.astro',
  'src/pages/index.astro',
  'src/layouts/BaseLayout.astro',
].map((path) => [path, readFileSync(resolve(siteRoot, path), 'utf8')]);

const byPath = new Map(files);
const combined = files.map(([, text]) => text).join('\n');

const requiredSnippets = [
  ['source evidence payload imported', 'sourceEvidence'],
  ['model raw evidence fields', 'model_name_raw'],
  ['model evidence score raw', 'score_raw'],
  ['canonicalization caveat', 'canonicalization_status'],
  ['version caveat', 'version: unknown'],
  ['external link safe rel', 'rel="noopener noreferrer external"'],
  ['visible destination URL label', '目标 URL'],
  ['unavailable evidence label', 'URL unavailable'],
  ['methodology score construction', '分数构造'],
  ['methodology scenario weighting', '场景权重'],
  ['methodology confidence eligibility', '置信度与 eligibility'],
  ['methodology limitations', '局限与不适用场景'],
  ['methodology traceability', '可追溯性要求'],
  ['source coverage update dates', '覆盖范围与更新日期'],
  ['source registry traceability', 'traceability expectations'],
  ['article link reachable', '/methodology/article/2026-05-alpha/'],
  ['article links snapshot', '/snapshots/'],
  ['article links sources', '/sources/'],
  ['article links rankings', '/leaderboard/'],
];

const missing = requiredSnippets.filter(([, snippet]) => !combined.includes(snippet));

const modelPage = byPath.get('src/pages/models/[...id].astro') ?? '';
if (!modelPage.includes('target="_blank"') || !modelPage.includes('rel="noopener noreferrer external"')) {
  missing.push(['safe external target/rel pairing', 'target + rel']);
}

if (missing.length > 0) {
  console.error('Evidence pages content contract failed. Missing snippets:');
  for (const [label, snippet] of missing) {
    console.error(`- ${label}: ${snippet}`);
  }
  process.exit(1);
}

console.log('Evidence pages content contract passed.');
