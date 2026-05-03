import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const siteRoot = resolve(import.meta.dirname, '..');
const homepage = readFileSync(resolve(siteRoot, 'src/pages/index.astro'), 'utf8');

const requiredSnippets = [
  ['overall leaderboard link', 'href="/leaderboard/"'],
  ['scenario rankings link', 'href="/leaderboard/Coding/"'],
  ['model selector link', 'href="/selector/"'],
  ['methodology link', 'href="/methodology/"'],
  ['source registry link', 'href="/sources/"'],
  ['latest snapshot link', 'href="/snapshots/"'],
  ['static API manifest link', 'href="/api/v1/manifest.json"'],
  ['Chinese positioning', '面向中文高阶 AI 用户'],
  ['reviewed alpha context', 'reviewed alpha'],
  ['confidence wording', '置信度'],
  ['non-official caveat', '非最终官方排名'],
];

const missing = requiredSnippets.filter(([, snippet]) => !homepage.includes(snippet));

if (missing.length > 0) {
  console.error('Homepage content contract failed. Missing snippets:');
  for (const [label, snippet] of missing) {
    console.error(`- ${label}: ${snippet}`);
  }
  process.exit(1);
}

console.log('Homepage content contract passed.');
