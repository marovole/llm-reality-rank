import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  decodeSelectorState,
  encodeSelectorState,
  rankModels,
  sanitizeWeights,
} from '../src/lib/selector.mjs';

const siteRoot = resolve(import.meta.dirname, '..');
const selectorData = JSON.parse(readFileSync(resolve(siteRoot, 'public/api/v1/selector-data.json'), 'utf8'));
const dimensions = selectorData.dimensions.map((dimension) => dimension.id);

const requiredPresetIds = ['coding', 'chinese_writing', 'agent_workflows', 'budget_api', 'multimodal', 'open_weight'];
assert.deepEqual(
  requiredPresetIds.filter((id) => !selectorData.presets.some((preset) => preset.id === id)),
  [],
  'selector data must expose every required preset',
);

for (const preset of selectorData.presets) {
  const result = rankModels(selectorData.models, preset.weights, preset.filters ?? {}, dimensions);
  if (preset.id === 'open_weight' && result.ranked.length === 0) {
    assert.ok(
      result.validationMessages.some((message) => message.includes('没有可推荐模型')),
      'open-weight preset with sparse alpha data must show an empty-state validation message',
    );
  } else {
    assert.ok(result.ranked.length > 0, `${preset.id} should return recommendations when eligible data exists`);
    assert.ok(result.ranked[0].selector.reasons.length > 0, `${preset.id} should explain top recommendation`);
  }
}

const tieModels = [
  {
    canonical_id: 'provider/z-low-confidence',
    display_name: 'Z Low Confidence',
    provider: 'Tie',
    model_type: 'closed',
    access_type: 'api',
    confidence: { label: 'Low', score: 10 },
    scores: { dimensions: { Coding: 90 }, overall_score: 90 },
    missing_dimensions: [],
  },
  {
    canonical_id: 'provider/a-high-confidence',
    display_name: 'A High Confidence',
    provider: 'Tie',
    model_type: 'closed',
    access_type: 'api',
    confidence: { label: 'High', score: 90 },
    scores: { dimensions: { Coding: 90 }, overall_score: 90 },
    missing_dimensions: [],
  },
  {
    canonical_id: 'provider/b-high-confidence',
    display_name: 'B High Confidence',
    provider: 'Tie',
    model_type: 'closed',
    access_type: 'api',
    confidence: { label: 'High', score: 90 },
    scores: { dimensions: { Coding: 90 }, overall_score: 90 },
    missing_dimensions: [],
  },
];
const deterministicA = rankModels(tieModels, { Coding: 1 }, {}, dimensions).ranked.map((model) => model.canonical_id);
const deterministicB = rankModels(tieModels, { Coding: 1 }, {}, dimensions).ranked.map((model) => model.canonical_id);
assert.deepEqual(deterministicA, deterministicB, 'rankings should be deterministic across repeated runs');
assert.deepEqual(deterministicA, [
  'provider/a-high-confidence',
  'provider/b-high-confidence',
  'provider/z-low-confidence',
], 'ties should break by score, confidence, then canonical ID');

const invalid = sanitizeWeights({ Coding: -1, Chinese: 'not-a-number' }, dimensions);
assert.equal(invalid.weights.Coding, 0, 'negative weights should be rejected to zero');
assert.equal(invalid.weights.Chinese, 0, 'non-numeric weights should be rejected to zero');
assert.ok(invalid.warnings.length >= 2, 'invalid weights should produce visible warnings');

const allZero = rankModels(selectorData.models, Object.fromEntries(dimensions.map((id) => [id, 0])), {}, dimensions);
assert.equal(allZero.ranked.length, 0, 'all-zero weights should not rank models');
assert.ok(
  allZero.validationMessages.some((message) => message.includes('全零权重') || message.includes('大于 0')),
  'all-zero weights should explain how to recover',
);

const sparse = rankModels(selectorData.models, { Chinese: 1 }, {}, dimensions);
assert.ok(
  sparse.validationMessages.some((message) => message.includes('缺少当前权重覆盖的部分维度')),
  'sparse weighted dimensions should show uncertainty warning',
);
assert.ok(
  sparse.ranked.every((model) => model.selector.comparableWeight < 1 || model.selector.missingWeightedDimensions.length === 0),
  'sparse models should expose comparable weight and missing dimensions',
);

const encoded = encodeSelectorState({
  presetId: 'coding',
  provider: 'OpenAI',
  modelType: 'closed',
  openOnly: false,
  weights: { Coding: 0.7, Practicality: 0.3 },
});
const decoded = decodeSelectorState(encoded, selectorData.presets, dimensions);
assert.equal(decoded.presetId, 'coding', 'URL state should preserve preset');
assert.equal(decoded.provider, 'OpenAI', 'URL state should preserve provider filter');
assert.equal(decoded.modelType, 'closed', 'URL state should preserve model-type filter');
assert.equal(decoded.weights.Coding, 0.7, 'URL state should preserve custom weights');
assert.equal(decoded.weights.Practicality, 0.3, 'URL state should preserve custom weights');

console.log('Selector behavior contract passed.');
