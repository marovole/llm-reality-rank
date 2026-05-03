export const SELECTOR_DIMENSION_IDS = [
  'General',
  'Reasoning_Math',
  'Coding',
  'Chinese',
  'Multimodal_Doc',
  'Agent_ToolUse',
  'Practicality',
  'Ecosystem',
];

export function sanitizeWeights(weights = {}, dimensions = SELECTOR_DIMENSION_IDS) {
  const warnings = [];
  const sanitized = {};

  for (const dimension of dimensions) {
    const rawValue = weights[dimension] ?? 0;
    const numericValue = typeof rawValue === 'number' ? rawValue : Number(rawValue);
    if (!Number.isFinite(numericValue)) {
      sanitized[dimension] = 0;
      warnings.push(`维度 ${dimension} 的权重不是有效数字，已按 0 处理。`);
    } else if (numericValue < 0) {
      sanitized[dimension] = 0;
      warnings.push(`维度 ${dimension} 的负权重无效，已按 0 处理。`);
    } else {
      sanitized[dimension] = numericValue;
    }
  }

  const total = Object.values(sanitized).reduce((sum, value) => sum + value, 0);
  return {
    weights: sanitized,
    total,
    valid: total > 0,
    warnings,
  };
}

export function normalizeWeights(weights = {}, dimensions = SELECTOR_DIMENSION_IDS) {
  const sanitized = sanitizeWeights(weights, dimensions);
  if (!sanitized.valid) return { ...sanitized, normalized: { ...sanitized.weights } };
  const normalized = Object.fromEntries(
    Object.entries(sanitized.weights).map(([dimension, weight]) => [dimension, weight / sanitized.total]),
  );
  return { ...sanitized, normalized };
}

function confidenceScore(model) {
  const value = model?.confidence?.score;
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function dimensionScore(model, dimension) {
  const value = model?.scores?.dimensions?.[dimension];
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function matchesFilters(model, filters = {}) {
  if (filters.provider && filters.provider !== 'all' && model.provider !== filters.provider) return false;
  if (filters.model_type && filters.model_type !== 'all' && model.model_type !== filters.model_type) return false;
  if (filters.openOnly) {
    const type = String(model.model_type ?? '').toLowerCase();
    const access = String(model.access_type ?? '').toLowerCase();
    return type.includes('open') || access.includes('local');
  }
  return true;
}

export function scoreModel(model, weights = {}, dimensions = SELECTOR_DIMENSION_IDS) {
  const normalizedWeights = normalizeWeights(weights, dimensions);
  if (!normalizedWeights.valid) {
    return {
      canonical_id: model.canonical_id,
      weightedScore: 0,
      comparableWeight: 0,
      confidenceScore: confidenceScore(model),
      matchedDimensions: [],
      missingWeightedDimensions: dimensions.filter((dimension) => (normalizedWeights.weights[dimension] ?? 0) > 0),
      reasons: [],
      warnings: ['所有权重均为 0，无法生成有效推荐。'],
    };
  }

  let weightedScore = 0;
  let comparableWeight = 0;
  const matchedDimensions = [];
  const missingWeightedDimensions = [];

  for (const dimension of dimensions) {
    const weight = normalizedWeights.normalized[dimension] ?? 0;
    if (weight === 0) continue;
    const score = dimensionScore(model, dimension);
    if (typeof score === 'number') {
      weightedScore += score * weight;
      comparableWeight += weight;
      matchedDimensions.push({ dimension, score, weight });
    } else {
      missingWeightedDimensions.push(dimension);
    }
  }

  const sparsePenaltyScore = comparableWeight > 0 ? weightedScore * comparableWeight : 0;
  const topDimensions = [...matchedDimensions]
    .sort((a, b) => b.weight - a.weight || b.score - a.score || a.dimension.localeCompare(b.dimension))
    .slice(0, 3);
  const reasons = topDimensions.map(({ dimension, score }) => `${dimension} ${score.toFixed(1)}`);
  if (missingWeightedDimensions.length > 0) {
    reasons.push(`缺失 ${missingWeightedDimensions.length} 个加权维度`);
  }
  reasons.push(`置信度 ${model.confidence?.label ?? 'Unknown'} ${confidenceScore(model).toFixed(1)}`);

  return {
    canonical_id: model.canonical_id,
    weightedScore: sparsePenaltyScore,
    rawWeightedScore: weightedScore,
    comparableWeight,
    confidenceScore: confidenceScore(model),
    matchedDimensions,
    missingWeightedDimensions,
    reasons,
    warnings: missingWeightedDimensions.length > 0
      ? [`${model.display_name} 缺少 ${missingWeightedDimensions.join(', ')}，推荐分已按覆盖率折减。`]
      : [],
  };
}

export function rankModels(models = [], weights = {}, filters = {}, dimensions = SELECTOR_DIMENSION_IDS) {
  const normalizedWeights = normalizeWeights(weights, dimensions);
  const validationMessages = [...normalizedWeights.warnings];
  if (!normalizedWeights.valid) validationMessages.push('请至少设置一个大于 0 的权重；全零权重不会产生推荐。');

  const ranked = normalizedWeights.valid
    ? models
      .filter((model) => matchesFilters(model, filters))
      .map((model) => ({ ...model, selector: scoreModel(model, weights, dimensions) }))
      .sort((a, b) => (
        b.selector.weightedScore - a.selector.weightedScore
        || b.selector.confidenceScore - a.selector.confidenceScore
        || a.canonical_id.localeCompare(b.canonical_id)
      ))
    : [];

  const sparseCount = ranked.filter((model) => model.selector.missingWeightedDimensions.length > 0).length;
  if (sparseCount > 0) {
    validationMessages.push(`${sparseCount} 个模型缺少当前权重覆盖的部分维度，已显示不确定性并降低可比性。`);
  }
  if (normalizedWeights.valid && ranked.length === 0) {
    validationMessages.push('当前筛选条件下没有可推荐模型；请放宽厂商或开放权重筛选。');
  }

  return {
    ranked,
    validationMessages,
    normalizedWeights: normalizedWeights.normalized,
    totalWeight: normalizedWeights.total,
  };
}

export function encodeSelectorState({ presetId = 'coding', weights = {}, provider = 'all', modelType = 'all', openOnly = false } = {}) {
  const params = new URLSearchParams();
  params.set('preset', presetId);
  if (provider && provider !== 'all') params.set('provider', provider);
  if (modelType && modelType !== 'all') params.set('model_type', modelType);
  if (openOnly) params.set('open', '1');
  const compactWeights = Object.entries(weights)
    .filter(([, value]) => Number(value) > 0)
    .map(([key, value]) => `${key}:${Number(value)}`)
    .join(',');
  if (compactWeights) params.set('weights', compactWeights);
  return params.toString();
}

export function decodeSelectorState(search = '', presets = [], dimensions = SELECTOR_DIMENSION_IDS) {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const requestedPreset = params.get('preset') ?? presets[0]?.id ?? 'coding';
  const preset = presets.find((item) => item.id === requestedPreset) ?? presets[0];
  const weights = { ...(preset?.weights ?? {}) };
  const weightParam = params.get('weights');
  if (weightParam) {
    for (const pair of weightParam.split(',')) {
      const [dimension, rawValue] = pair.split(':');
      if (dimensions.includes(dimension)) weights[dimension] = Number(rawValue);
    }
  }
  return {
    presetId: preset?.id ?? requestedPreset,
    weights,
    provider: params.get('provider') ?? 'all',
    modelType: params.get('model_type') ?? 'all',
    openOnly: params.get('open') === '1' || (!params.has('open') && preset?.id === 'open_weight'),
  };
}
