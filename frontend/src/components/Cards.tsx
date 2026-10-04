import type { ReactNode } from "react";
import {
  AlertTriangleIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  ZapIcon,
} from "./Icons";

export function StatCard({
  label,
  value,
  tone = "default",
  icon,
}: {
  label: string;
  value: ReactNode;
  tone?: "default" | "warn" | "danger" | "good" | "info";
  icon?: ReactNode;
}) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <div className="stat-card-top">
        <div className="stat-card-value">{value}</div>
        {icon && <div className="stat-card-icon">{icon}</div>}
      </div>
      <div className="stat-card-label">{label}</div>
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const normSev = severity?.toLowerCase() === "moderate" ? "medium" : severity?.toLowerCase();
  
  if (normSev === "high") {
    return (
      <span className="severity-badge severity-high">
        <AlertTriangleIcon size={13} color="#C2413B" />
        HIGH PRIORITY
      </span>
    );
  }
  if (normSev === "medium") {
    return (
      <span className="severity-badge severity-medium">
        <AlertTriangleIcon size={13} color="#D97706" />
        MODERATE PRIORITY
      </span>
    );
  }
  return (
    <span className="severity-badge severity-low">
      <ShieldCheckIcon size={13} color="#0F766E" />
      LOW PRIORITY
    </span>
  );
}

export function SimulatedBadge() {
  return (
    <span className="badge sim-badge">
      <ZapIcon size={12} color="#6B21A8" />
      SIMULATED DATA
    </span>
  );
}

export function VerificationBadge({ status }: { status?: string | null }) {
  const norm = (status || "pending").toLowerCase();
  
  if (norm === "verified") {
    return (
      <span className="ver-badge ver-verified">
        <CheckCircleIcon size={14} color="#15803D" />
        ✓ VERIFIED (Ground Field Notes Submitted)
      </span>
    );
  }
  if (norm === "resolved") {
    return (
      <span className="ver-badge ver-resolved">
        <CheckCircleIcon size={14} color="#0369A1" />
        ✓ RESOLVED (Field Action Taken)
      </span>
    );
  }
  if (norm === "not_confirmed") {
    return (
      <span className="ver-badge ver-not-confirmed">
        <XCircleIcon size={14} color="#4B5563" />
        ✗ NOT CONFIRMED (No Anomaly Found)
      </span>
    );
  }
  return (
    <span className="ver-badge ver-pending">
      ⏳ PENDING VERIFICATION
    </span>
  );
}

const CATEGORY_MAP: Record<string, string> = {
  vector_borne: "Vector-Borne Disease Signal",
  fever_cluster: "Fever Cluster Signal",
  water_borne: "Water-Borne Illness Signal",
  gastrointestinal: "Gastrointestinal Signal",
  respiratory: "Respiratory Disease Signal",
  skin_rash: "Skin Rash & Lesions",
  skin_allergy: "Skin & Allergy Signal",
  chronic_disease: "Chronic Disease Signal",
  malaria: "MALARIA SIGNAL",
  dengue: "DENGUE SIGNAL",
  cholera: "CHOLERA SIGNAL",
  typhoid: "TYPHOID SIGNAL",
  influenza: "INFLUENZA SIGNAL",
  flu: "FLU SIGNAL",
  diarrhea: "DIARRHEA SIGNAL",
};

export function formatCategory(raw?: string | null): string {
  if (!raw) return "General Health Signal";
  const key = raw.toLowerCase().trim();
  if (CATEGORY_MAP[key]) return CATEGORY_MAP[key];
  return raw
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase()) + " Signal";
}

export function getRealisticMetrics(a: { observed_count: number; baseline_mean: number; z_score: number; severity?: string }) {
  const baseline = Number(a.baseline_mean.toFixed(1));
  const observed = a.observed_count;
  const z = Number(a.z_score.toFixed(2));
  const ratio = (observed / Math.max(1, baseline)).toFixed(1);

  return {
    baseline,
    observed,
    z,
    ratio,
  };
}
