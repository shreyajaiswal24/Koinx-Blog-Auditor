const BASE = '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export interface Finding {
  id: number;
  run_id: number;
  blog_url: string;
  blog_title: string;
  section_heading: string;
  exact_quote: string;
  issue_type: string;
  description: string;
  suggested_update: string;
  source: string;
  llm_confidence: number;
  confidence: number;
  priority: string;
  status: string;
  finding_hash: string;
}

export interface PaginatedFindings {
  items: Finding[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Run {
  id: number;
  started_at: number | null;
  completed_at: number | null;
  total_posts: number;
  total_findings: number;
  total_api_calls: number;
  total_tokens: number;
}

export interface Stats {
  total_findings: number;
  high: number;
  medium: number;
  low: number;
  new: number;
  previously_identified: number;
  resolved: number;
  total_runs: number;
  last_run: Run | null;
}

export interface AuditStatus {
  running: boolean;
  progress: Record<string, unknown> | null;
}

export function fetchStats() {
  return request<Stats>('/api/stats');
}

export function fetchFindings(params: Record<string, string>) {
  const qs = new URLSearchParams(params).toString();
  return request<PaginatedFindings>(`/api/findings?${qs}`);
}

export function fetchRuns() {
  return request<Run[]>('/api/runs');
}

export function fetchAuditStatus() {
  return request<AuditStatus>('/api/audit/status');
}

export function startAudit(postId?: number) {
  return request<{ message: string; status: string }>('/api/audit/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ post_id: postId ?? null }),
  });
}

export function getReportDownloadUrl() {
  return '/api/reports/download';
}
