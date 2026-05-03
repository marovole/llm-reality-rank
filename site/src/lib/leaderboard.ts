import { currentSnapshot, getModelForScore, rankedScores, scenarios, scoresForScenario } from './data';
import type { Score } from './data';

export type LeaderboardDataState = {
  ok: boolean;
  message: string;
  detail?: string;
};

export type LeaderboardFilterOption = {
  value: string;
  label: string;
};

export type LeaderboardFilterState = {
  scenarioId: string;
  query: string;
  confidence: string;
  eligibility: string;
};

export type LeaderboardRow = Score & {
  model?: ReturnType<typeof getModelForScore>;
  visibleScore?: number;
  displayRank: number;
  freshness: {
    newestDate?: string;
    oldestDate?: string;
    ageDays?: number;
    stale: boolean;
  };
};

export type LeaderboardViewModel = {
  dataState: LeaderboardDataState;
  rows: LeaderboardRow[];
  allRows: LeaderboardRow[];
  clientRows: LeaderboardRow[];
  filters: LeaderboardFilterState;
  confidenceOptions: LeaderboardFilterOption[];
  eligibilityOptions: LeaderboardFilterOption[];
  staleCount: number;
  missingDimensionCount: number;
};

const knownScenarioIds = new Set(scenarios.map((scenario) => scenario.id));
const todayUtc = Date.UTC(2026, 4, 3);
const staleThresholdDays = 90;

function parseDateUtc(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  return Number.isNaN(timestamp) ? undefined : timestamp;
}

function daysSince(value: string | undefined): number | undefined {
  const timestamp = parseDateUtc(value);
  if (typeof timestamp !== 'number') return undefined;
  return Math.max(0, Math.floor((todayUtc - timestamp) / 86_400_000));
}

function rowFreshness(score: Score): LeaderboardRow['freshness'] {
  const dates = score.source_refs
    .map((ref) => ref.date_observed)
    .filter((value): value is string => typeof value === 'string' && value.length > 0)
    .sort();
  const newestDate = dates.at(-1);
  const oldestDate = dates[0];
  const ageDays = daysSince(newestDate);
  return {
    newestDate,
    oldestDate,
    ageDays,
    stale: typeof ageDays === 'number' ? ageDays > staleThresholdDays : true,
  };
}

function optionList(values: string[], labels: Record<string, string>, allLabel: string): LeaderboardFilterOption[] {
  return [
    { value: 'all', label: allLabel },
    ...values.map((value) => ({ value, label: labels[value] ?? value })),
  ];
}

export function validateLeaderboardData(): LeaderboardDataState {
  if (!currentSnapshot) {
    return {
      ok: false,
      message: '缺少 reviewed snapshot manifest，无法渲染可信榜单。',
      detail: '请先生成 snapshots.json / manifest.json；页面不会回退到占位排名。',
    };
  }

  if (!Array.isArray(rankedScores) || rankedScores.length === 0) {
    return {
      ok: false,
      message: '缺少 reviewed scores 静态 JSON，当前没有可发布榜单。',
      detail: 'scores.json 为空或不存在有效 scores 数组；页面不会显示官方感占位数据。',
    };
  }

  const malformedScore = rankedScores.find((score) => (
    !score.canonical_id
    || typeof score.rank !== 'number'
    || typeof score.overall_score !== 'number'
    || !score.confidence
    || typeof score.confidence.label !== 'string'
    || !score.eligibility
    || typeof score.eligibility.status !== 'string'
    || !Array.isArray(score.missing_dimensions)
    || !score.source_coverage
    || !Array.isArray(score.source_refs)
  ));

  if (malformedScore) {
    return {
      ok: false,
      message: 'reviewed scores 静态 JSON 格式异常，榜单已安全停止渲染。',
      detail: `异常记录：${malformedScore.canonical_id ?? 'unknown canonical_id'}。请修复 JSON contract 后重新构建。`,
    };
  }

  return {
    ok: true,
    message: 'Reviewed alpha data loaded.',
  };
}

function enrichRows(baseScores: Score[], scenarioId: string): LeaderboardRow[] {
  return baseScores.map((score, index) => ({
    ...score,
    model: getModelForScore(score),
    visibleScore: scenarioId === 'overall' ? score.overall_score : score.dimension_scores[scenarioId],
    displayRank: scenarioId === 'overall' ? score.rank : index + 1,
    freshness: rowFreshness(score),
  }));
}

export function buildLeaderboardView(searchParams: URLSearchParams, defaultScenarioId = 'overall'): LeaderboardViewModel {
  const dataState = validateLeaderboardData();
  const requestedScenario = searchParams.get('scenario') ?? defaultScenarioId;
  const scenarioId = requestedScenario === 'overall' || knownScenarioIds.has(requestedScenario) ? requestedScenario : 'overall';
  const query = (searchParams.get('q') ?? '').trim().toLowerCase();
  const confidence = searchParams.get('confidence') ?? 'all';
  const eligibility = searchParams.get('eligibility') ?? 'all';

  const baseScores = scenarioId === 'overall' ? rankedScores : scoresForScenario(scenarioId);
  const allRows = enrichRows(baseScores, scenarioId);
  const clientRows = enrichRows(rankedScores, 'overall');

  const rows = dataState.ok
    ? allRows.filter((row) => {
      const haystack = [
        row.canonical_id,
        row.model?.display_name,
        row.model?.provider,
        row.confidence.label,
        row.eligibility.status,
      ].filter(Boolean).join(' ').toLowerCase();
      return (query.length === 0 || haystack.includes(query))
        && (confidence === 'all' || row.confidence.label.toLowerCase() === confidence.toLowerCase())
        && (eligibility === 'all' || row.eligibility.status.toLowerCase() === eligibility.toLowerCase());
    })
    : [];

  const confidenceValues = Array.from(new Set(rankedScores.map((score) => score.confidence.label))).sort();
  const eligibilityValues = Array.from(new Set(rankedScores.map((score) => score.eligibility.status))).sort();

  return {
    dataState,
    rows,
    allRows,
    clientRows,
    filters: { scenarioId, query, confidence, eligibility },
    confidenceOptions: optionList(confidenceValues, {}, '全部置信度'),
    eligibilityOptions: optionList(eligibilityValues, {
      ineligible: 'ineligible · 数据不足',
      provisional: 'provisional · 临时可读',
      official: 'official',
    }, '全部状态'),
    staleCount: allRows.filter((row) => row.freshness.stale).length,
    missingDimensionCount: allRows.filter((row) => row.missing_dimensions.length > 0).length,
  };
}
