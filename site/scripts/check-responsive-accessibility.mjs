import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const siteRoot = resolve(import.meta.dirname, '..');

const files = [
  'src/styles/global.css',
  'src/layouts/BaseLayout.astro',
  'src/components/LeaderboardControls.astro',
  'src/components/LeaderboardTable.astro',
  'src/components/ScenarioNav.astro',
  'src/pages/index.astro',
  'src/pages/models/[...id].astro',
  'src/pages/methodology/index.astro',
  'src/pages/sources/index.astro',
  'src/pages/selector/index.astro',
].map((path) => [path, readFileSync(resolve(siteRoot, path), 'utf8')]);

const combined = files.map(([, text]) => text).join('\n');

const requiredSnippets = [
  ['responsive table class', 'class="responsive-table"'],
  ['table cell labels for mobile cards', 'data-label='],
  ['mobile table card breakpoint', '@media (max-width: 640px)'],
  ['mobile table removes min width', 'min-width: 0'],
  ['tap target minimum', 'min-height: 44px'],
  ['mobile overflow containment', 'overflow-wrap: anywhere'],
  ['focus-visible box shadow', 'box-shadow: 0 0 0 3px'],
  ['nav link accessible label', 'aria-label="打开综合排行榜"'],
  ['brand accessible label', 'aria-label="LLM Reality Rank 首页"'],
  ['scenario nav link labels', 'aria-label={`打开${scenario.label_zh}场景榜`}'],
  ['scenario select label', 'aria-label="选择榜单场景"'],
  ['search input label', 'aria-label="搜索模型或厂商"'],
  ['confidence filter label', 'aria-label="筛选置信度"'],
  ['eligibility filter label', 'aria-label="筛选资格状态"'],
  ['leaderboard table caption', '<caption>'],
  ['model detail link label', 'aria-label={`查看${model?.display_name ?? score.canonical_id}模型详情`}'],
  ['confidence badge label', 'aria-label={`置信度：${score.confidence.label}，分数 ${formatScore(score.confidence.score)}`}'],
  ['missing badge label', 'aria-label={score.missing_dimensions.length > 0 ?'],
  ['eligibility badge label', 'aria-label={`资格状态：${score.eligibility.status}`}'],
  ['rendered client row labels', 'aria-label="查看${escapeHtml(modelName)}模型详情"'],
  ['external evidence link label', 'aria-label={`打开外部来源：${evidenceUrl}`}'],
  ['source external link label', 'aria-label={`打开外部来源：${source.source_url}`}'],
  ['semantic source article label', 'aria-labelledby={`source-${source.source_id}`}'],
  ['selector preset accessible buttons', 'aria-label="选择 ${escapeHtml(preset.display_name)} preset"'],
  ['selector provider filter label', 'aria-label="筛选模型厂商"'],
  ['selector model type filter label', 'aria-label="筛选模型开放权重状态"'],
  ['selector copy link accessible label', 'aria-label="复制当前选择器分享链接"'],
  ['methodology section labelled', 'aria-labelledby="score-construction-title"'],
];

const missing = requiredSnippets.filter(([, snippet]) => !combined.includes(snippet));

if (missing.length > 0) {
  console.error('Responsive/accessibility static contract failed. Missing snippets:');
  for (const [label, snippet] of missing) {
    console.error(`- ${label}: ${snippet}`);
  }
  process.exit(1);
}

console.log('Responsive/accessibility static contract passed.');
