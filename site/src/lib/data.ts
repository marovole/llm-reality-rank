import manifest from '../../public/api/v1/manifest.json';
import modelsPayload from '../../public/api/v1/models.json';
import scenariosPayload from '../../public/api/v1/scenarios.json';
import scoresPayload from '../../public/api/v1/scores.json';
import selectorPayload from '../../public/api/v1/selector-data.json';
import snapshotsPayload from '../../public/api/v1/snapshots.json';
import sourceEvidencePayload from '../../public/api/v1/source-evidence.json';
import sourcesPayload from '../../public/api/v1/sources.json';

type Model = {
  canonical_id: string;
  display_name: string;
  provider: string;
  aliases?: string[];
  source_names?: string[];
  access_type?: string;
  model_type?: string;
  model_family?: string;
  model_variant?: string;
  version?: string;
  notes?: string;
  open_weight?: boolean;
  status?: string;
};

type Score = {
  canonical_id: string;
  snapshot_id: string;
  rank: number;
  overall_score: number;
  dimension_scores: Record<string, number>;
  confidence: { label: string; score: number; proxy?: string };
  eligibility: { status: string; reason: string };
  missing_dimensions: string[];
  source_coverage: { source_count: number; scenario_count: number; evidence_count: number };
  source_refs: Array<{
    source_id: string;
    evidence_id: string;
    metric_name: string;
    dimension: string;
    date_observed: string;
    url: string;
    notes: string;
  }>;
  uncertainty_flags: string[];
};

type Scenario = { id: string; label_zh: string; display_name: string };
type Preset = { id: string; display_name: string; description: string; weights: Record<string, number> };
type Source = {
  source_id: string;
  name: string;
  organization?: string;
  priority?: string;
  categories?: string[];
  dimensions?: string[];
  metric_types?: string[];
  source_trust?: string;
  contamination_risk?: string;
  evaluation_independence?: string;
  source_url: string;
  urls?: Record<string, string>;
  last_observed?: string;
  notes?: string;
  status?: string;
};

type SourceEvidence = {
  evidence_id: string;
  snapshot_id: string;
  canonical_id: string;
  source_id: string;
  metric_name: string;
  category_primary: string;
  model_name_raw: string;
  rank_raw?: number | null;
  score_raw?: number | null;
  score_normalized?: number | null;
  source_effective_weight?: number | null;
  source_url?: string;
  date_observed: string;
  notes: string;
};

type Snapshot = {
  snapshot_id: string;
  date: string;
  current?: boolean;
  latest?: boolean;
  review_status: string;
  publication_status: string;
  limitations: string[];
};

export type { Model, Score, Scenario, Preset, Source, Snapshot, SourceEvidence };

export const apiManifest = manifest;
export const models = (modelsPayload as unknown as { models: Model[] }).models;
export const scores = (scoresPayload as unknown as { scores: Score[] }).scores;
export const scenarios = (scenariosPayload as unknown as { dimensions: Scenario[]; presets: Preset[] }).dimensions;
export const presets = (scenariosPayload as unknown as { dimensions: Scenario[]; presets: Preset[] }).presets;
export const sources = (sourcesPayload as unknown as { sources: Source[] }).sources;
export const sourceEvidence = (sourceEvidencePayload as unknown as { source_evidence: SourceEvidence[] }).source_evidence;
export const snapshots = (snapshotsPayload as unknown as { current_snapshot_id: string; snapshots: Snapshot[] }).snapshots;
export const selectorData = selectorPayload;

export const modelById = new Map(models.map((model) => [model.canonical_id, model]));
export const sourceById = new Map(sources.map((source) => [source.source_id, source]));
export const evidenceById = new Map(sourceEvidence.map((evidence) => [evidence.evidence_id, evidence]));
export const currentSnapshot = snapshots.find((snapshot) => snapshot.current || snapshot.latest) ?? snapshots[0];

export const rankedScores = [...scores].sort((a, b) => a.rank - b.rank || a.canonical_id.localeCompare(b.canonical_id));

export function getModelPath(canonicalId: string): string {
  return `/models/${canonicalId}/`;
}

export function getModelForScore(score: Score): Model | undefined {
  return modelById.get(score.canonical_id);
}

export function scenarioLabel(id: string): string {
  return scenarios.find((scenario) => scenario.id === id)?.label_zh ?? id;
}

export function scoresForScenario(scenarioId: string): Score[] {
  return rankedScores
    .filter((score) => typeof score.dimension_scores[scenarioId] === 'number')
    .sort((a, b) => (b.dimension_scores[scenarioId] ?? -Infinity) - (a.dimension_scores[scenarioId] ?? -Infinity) || a.canonical_id.localeCompare(b.canonical_id));
}

export function formatScore(value: number | undefined): string {
  return typeof value === 'number' ? value.toFixed(1) : '—';
}

export function pageTitle(title: string): string {
  return `${title} | LLM Reality Rank`;
}
