import { copyFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const siteRoot = dirname(fileURLToPath(import.meta.url)).replace(/\/scripts$/, '');
const repoRoot = resolve(siteRoot, '..');
const sourceDir = resolve(repoRoot, 'outputs/llm-reality-rank/api/v1');
const publicApiDir = resolve(siteRoot, 'public/api/v1');

if (!existsSync(sourceDir)) {
  throw new Error(`Static API source directory not found: ${sourceDir}`);
}

mkdirSync(publicApiDir, { recursive: true });

for (const entry of readdirSync(sourceDir, { withFileTypes: true })) {
  if (entry.isFile() && entry.name.endsWith('.json')) {
    copyFileSync(join(sourceDir, entry.name), join(publicApiDir, entry.name));
  }
}

console.log(`Copied static API JSON from ${sourceDir} to ${publicApiDir}`);
