"""
resume.ts — Shared TypeScript interfaces matching backend Pydantic schemas.
"""

export interface ResumeUploadResponse {
  resume_id: string;
  file_url: string;
  created_at: string;
  job_id?: string;
  message: string;
}

export interface ResumeResponse {
  id: string;
  user_id: string;
  file_url: string;
  raw_text?: string | null;
  parsed_json?: Record<string, any> | null;
  ats_score?: number | null;
  created_at: string;
  updated_at: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: "queued" | "in_progress" | "complete" | "failed";
  result?: Record<string, any> | null;
}

export interface ScoreResumeResponse {
  resume_id: string;
  job_id: string;
  message: string;
}

export interface AtsBreakdown {
  overall_score: number;
  formatting: number;
  structure: number;
  parseability: number;
  feedback?: string[];
}

export interface GrammarSuggestion {
  location: string;
  issue: string;
  suggestion: string;
}

export interface KeywordGap {
  keyword: string;
  importance: "high" | "medium" | "low";
  category?: string;
  reason?: string;
}

export interface ActionItem {
  priority: number;
  section?: string;
  action: string;
  impact?: string;
}

export interface ResumeReportResponse {
  id: string;
  resume_id: string;
  job_description_id?: string | null;
  ats_breakdown?: AtsBreakdown | null;
  grammar_suggestions?: GrammarSuggestion[] | null;
  keyword_gaps?: KeywordGap[] | null;
  action_items?: ActionItem[] | null;
  created_at: string;
}
