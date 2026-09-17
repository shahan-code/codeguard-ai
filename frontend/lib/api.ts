const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("codeguard_token");
}

export function setToken(token: string) {
  window.localStorage.setItem("codeguard_token", token);
}

export function clearToken() {
  window.localStorage.removeItem("codeguard_token");
}

export function isAuthed(): boolean {
  return !!getToken();
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) detail = body.detail[0].msg;
    } catch {
      // ignore parse errors, keep default message
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

// --- Types ---
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AnalysisSummary {
  id: string;
  filename: string;
  language: string;
  status: string;
  quality_score: number | null;
  risk_level: string | null;
  from_cache: boolean;
  created_at: string;
}

export interface Finding {
  title: string;
  category: string;
  severity: string;
  line: number | null;
  description: string;
  why_it_matters: string;
  recommendation: string;
}

export interface SecurityFinding {
  severity: string;
  line: number | null;
  issue: string;
  explanation: string;
  recommendation: string;
}

export interface FunctionRisk {
  name: string;
  line: number;
  complexity: number;
  length: number;
  risk: string;
}

export interface Recommendation {
  rank: number;
  priority_label: string;
  title: string;
  recommendation: string;
  line: number | null;
}

export interface AnalysisDetail extends AnalysisSummary {
  error_message: string | null;
  risk_score: number | null;
  metrics: Record<string, any> | null;
  findings: Finding[] | null;
  security_findings: SecurityFinding[] | null;
  function_risk: FunctionRisk[] | null;
  sub_scores: Record<string, number> | null;
  recommendations: Recommendation[] | null;
  ai_explanation: string | null;
  source_code: string | null;
}

// --- API calls ---
export const api = {
  register: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  createAnalysis: (code: string, filename: string) =>
    request<AnalysisDetail>("/api/analysis", {
      method: "POST",
      body: JSON.stringify({ code, filename, language: "python" }),
    }),

  listAnalyses: () => request<AnalysisSummary[]>("/api/analysis"),

  getAnalysis: (id: string) => request<AnalysisDetail>(`/api/analysis/${id}`),

  getStatus: (id: string) => request<{ id: string; status: string; error_message: string | null }>(`/api/analysis/${id}/status`),

  reportUrl: (id: string) => {
    const token = getToken();
    return `${API_URL}/api/analysis/${id}/report?_t=${token ?? ""}`;
  },

  downloadReport: async (id: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/analysis/${id}/report`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError(res.status, "Could not generate report");
    return res.blob();
  },
};
