export type UserRole = "citizen" | "health_official" | "asha_worker" | "admin";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  preferred_language: string;
  district?: string;
  state?: string;
}

export interface AshaWorker {
  id: string;
  full_name: string;
  email: string;
  district?: string;
  state?: string;
}

export interface AshaAlert {
  id: string;
  topic_category: string;
  topic_tag?: string;
  block_name: string;
  district: string;
  state: string;
  latitude?: number;
  longitude?: number;
  period_bucket: string;
  observed_count: number;
  baseline_mean: number;
  z_score: number;
  severity: "low" | "moderate" | "high";
  status: string;
  verification_status: "pending" | "verified" | "not_confirmed" | "resolved";
  field_observation?: string;
  assigned_at?: string;
  verified_at?: string;
  generated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SourceOut {
  title: string;
  source_name: string;
  source_url?: string;
  snippet: string;
}

export interface QueryResponse {
  query_id: string;
  answer: string;
  sources: SourceOut[];
  provider: string;
  safety_flag: string;
  detected_symptom_tags: string[];
}

export interface AwarenessSignal {
  id: string;
  symptom_tag: string;
  district_bucket: string;
  week_bucket: string;
  observed_count: number;
  baseline_mean: number;
  z_score: number;
  severity: "low" | "moderate" | "high";
  status: "pending_review" | "acknowledged" | "dismissed";
  created_at: string;
}

export interface HealthScheme {
  id: string;
  name: string;
  description: string;
  eligibility: string;
  how_to_apply: string;
  official_url?: string;
}

export interface MythFact {
  id: string;
  myth: string;
  fact: string;
  topic_tag: string;
  source_name?: string;
}

export interface HealthFacility {
  id: string;
  name: string;
  facility_type: string;
  district: string;
  state: string;
  latitude?: number;
  longitude?: number;
  phone?: string;
}
