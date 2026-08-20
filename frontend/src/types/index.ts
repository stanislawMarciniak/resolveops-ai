export type CaseStage =
  | "NEW"
  | "INVESTIGATING"
  | "PLANNING"
  | "REVIEW"
  | "AWAITING_APPROVAL"
  | "EXECUTING"
  | "VERIFYING"
  | "RESOLVED"
  | "ESCALATED"
  | "FAILED";

export type EvidenceSource = "CRM" | "BILLING" | "POLICY" | "USER";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type ReviewVerdict = "APPROVE" | "REVISE" | "ESCALATE";
export type ApprovalDecision = "PENDING" | "APPROVED" | "REJECTED";
export type ExecutionStatus = "PENDING" | "SUCCESS" | "FAILED";
export type EvalVariant = "multi_agent" | "single_agent" | "no_reviewer";

export type ScalarValue = string | number | boolean | null;

export interface Evidence {
  evidence_id: string;
  source: EvidenceSource;
  description: string;
  details: Record<string, ScalarValue>;
}

export interface Hypothesis {
  hypothesis_id: string;
  description: string;
  evidence_ids: string[];
  confidence: number;
}

export interface PlannedAction {
  tool_name: string;
  arguments: Record<string, ScalarValue>;
  reason: string;
  evidence_ids: string[];
  risk: RiskLevel;
  requires_approval: boolean;
}

export interface ResolutionPlan {
  explanation: string;
  actions: PlannedAction[];
  risk: RiskLevel;
  requires_approval: boolean;
}

export interface PlanReview {
  verdict: ReviewVerdict;
  summary: string;
  issues: string[];
  revision_feedback: string | null;
}

export interface Approval {
  approval_id: string;
  user_id: string | null;
  decision: ApprovalDecision;
  created_at: string;
  decided_at: string | null;
  plan_digest: string;
}

export interface ExecutedAction {
  tool_name: string;
  arguments: Record<string, ScalarValue>;
  status: ExecutionStatus;
  started_at: string;
  completed_at: string | null;
  result_summary: string | null;
  error: string | null;
}

export interface VerificationCheck {
  name: string;
  expected: string;
  actual: string;
  passed: boolean;
}

export interface VerificationResult {
  success: boolean;
  checks: VerificationCheck[];
  summary: string;
}

export interface CaseState {
  case_id: string;
  customer_id: string;
  description: string;
  stage: CaseStage;
  evidence: Evidence[];
  hypotheses: Hypothesis[];
  root_cause: string | null;
  resolution_plan: ResolutionPlan | null;
  review: PlanReview | null;
  plan_revision_count: number;
  approval: Approval | null;
  executed_actions: ExecutedAction[];
  verification: VerificationResult | null;
  model_calls: number;
  tool_calls: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  tool_input_tokens: number;
  thinking_tokens: number;
  llm_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface CaseListResponse {
  total: number;
  items: CaseState[];
}

export interface EvalCaseResult {
  eval_id: string;
  case_id: string;
  passed: boolean;
  expected_stage: string;
  actual_stage: string;
  stage_correct: boolean;
  root_cause_score: number | null;
  root_cause_correct: boolean | null;
  expected_actions: string[] | null;
  tags: string[];
  actual_actions: string[];
  plan_correct: boolean | null;
  customer_id_correct: boolean | null;
  expected_review_verdict: string | null;
  actual_review_verdict: string | null;
  review_correct: boolean | null;
  model_calls: number;
  tool_calls: number;
  input_tokens: number;
  tool_input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  total_tokens: number;
  llm_latency_ms: number;
  estimated_cost_usd: number;
  plan_revision_count: number;
  run_error: string | null;
}

export interface EvalSummary {
  variant: EvalVariant;
  dataset_name: string;
  dataset_version: string;
  total_cases: number;
  passed_cases: number;
  pass_rate: number;
  stage_accuracy: number;
  root_cause_accuracy: number | null;
  plan_accuracy: number | null;
  review_accuracy: number | null;
  customer_id_accuracy: number | null;
  average_model_calls: number;
  average_tool_calls: number;
  average_tokens: number;
  average_llm_latency_ms: number;
  p50_llm_latency_ms: number;
  p95_llm_latency_ms: number;
  average_cost_usd: number;
  total_cost_usd: number;
  average_plan_revisions: number;
  tag_pass_rates: Record<string, number>;
}

export interface EvalReport {
  summary: EvalSummary;
  cases: EvalCaseResult[];
}

export interface EvaluationOverview {
  dataset_name: string;
  dataset_version: string;
  total_cases: number;
  variants: Record<string, EvalSummary>;
  comparison_available: boolean;
}

export interface FinalComparison {
  dataset: {
    name: string;
    version: string;
    cases: number;
  };
  variants: Record<
    string,
    {
      pass_rate: number;
      stage_accuracy: number;
      root_cause_accuracy: number | null;
      plan_accuracy: number | null;
      review_accuracy: number | null;
      customer_id_accuracy: number | null;
      average_model_calls: number;
      average_tool_calls: number;
      average_tokens: number;
      average_llm_latency_ms: number;
      p50_llm_latency_ms: number;
      p95_llm_latency_ms: number;
      average_cost_usd: number;
      total_cost_usd: number;
      error_cases: number;
      tag_pass_rates: Record<string, number>;
    }
  >;
  multi_vs_single: {
    pass_rate_delta: number;
    stage_accuracy_delta: number;
    average_cost_delta_usd: number;
    average_model_calls_delta: number;
    average_latency_delta_ms: number;
    multi_agent_only_passes: string[];
    single_agent_only_passes: string[];
  };
  reviewer_ablation: {
    pass_rate_delta: number;
    average_cost_delta_usd: number;
    average_model_calls_delta: number;
    average_latency_delta_ms: number;
    reviewer_saved_cases: string[];
    reviewer_hurt_cases: string[];
  };
  tag_comparison: Record<
    string,
    {
      multi_agent: number;
      single_agent: number;
      no_reviewer: number;
    }
  >;
}

export interface EvalDatasetCase {
  eval_id: string;
  customer_id: string;
  description: string;
  tags: string[];
  ground_truth: {
    expected_final_stage: string;
    root_cause_keyword_groups: string[][];
    expected_actions: string[] | null;
    expected_customer_id: string | null;
    expected_review_verdict: string | null;
    expected_requires_approval: boolean | null;
  };
}

export interface EvalDataset {
  name: string;
  version: string;
  cases: EvalDatasetCase[];
}

export interface ShowcaseScenario {
  scenario: string;
  customer_id: string;
  eval_ids: string[];
  description: string;
  tags: string[];
  expected_safe_behavior: string | null;
  results: Record<
    string,
    {
      passed_cases: number;
      total_cases: number;
      pass_rate: number;
      cases: Array<{
        eval_id: string;
        passed: boolean;
        actual_stage: string;
        case_id: string;
        run_error: string | null;
      }>;
    }
  >;
}

export interface EvalCaseComparison {
  eval_id: string;
  dataset_case: EvalDatasetCase | null;
  variants: Partial<Record<EvalVariant, EvalCaseResult>>;
}

export interface ComponentStatus {
  name: string;
  status: string;
  detail: string | null;
}

export interface SystemStatus {
  environment: string;
  backend: ComponentStatus;
  mcp: ComponentStatus;
  crm: ComponentStatus;
  billing: ComponentStatus;
}

export interface SystemInfo {
  app_name: string;
  environment: string;
  adk_model: string;
  otel_enabled: boolean;
  auth_configured: boolean;
}

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}
