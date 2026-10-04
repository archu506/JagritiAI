import { useState, useEffect } from "react";
import { api } from "../api/client";
import { useI18n } from "../context/I18nContext";
import { LoadingState, ErrorState } from "../components/States";
import { formatCategory, getRealisticMetrics, SeverityBadge, VerificationBadge } from "../components/Cards";
import {
  UserCheckIcon,
  MapPinIcon,
  FileTextIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  ActivityIcon,
} from "../components/Icons";
import type { AshaAlert } from "../types";

export default function AshaDashboard() {
  const { t } = useI18n();
  const [alerts, setAlerts] = useState<AshaAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [formState, setFormState] = useState<Record<string, { status: string; notes: string }>>({});
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [tab, setTab] = useState<"assigned" | "history">("assigned");

  const fetchAlerts = async (showLoadingScreen: boolean = true) => {
    if (showLoadingScreen) setLoading(true);
    setError(null);
    try {
      const res = await api.get<AshaAlert[]>("/asha/alerts");
      setAlerts(res.data);

      setFormState(() => {
        const updated: Record<string, { status: string; notes: string }> = {};
        res.data.forEach((a) => {
          updated[a.id] = {
            status: a.verification_status || "pending",
            notes: a.field_observation || "",
          };
        });
        return updated;
      });
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to load assigned alerts.");
    } finally {
      if (showLoadingScreen) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts(true);
  }, []);

  const handleUpdate = async (alertId: string) => {
    const alertItem = alerts.find((a) => a.id === alertId);
    const current = formState[alertId] || {
      status: alertItem?.verification_status || "pending",
      notes: alertItem?.field_observation || "",
    };

    setUpdatingId(alertId);
    setSuccessMsg(null);
    try {
      await api.post(`/asha/alerts/${alertId}/verify`, {
        verification_status: current.status,
        field_observation: current.notes,
      });
      setSuccessMsg("Field verification updated successfully.");
      await fetchAlerts(false);
    } catch (e: any) {
      alert(e?.response?.data?.detail ?? "Failed to update field status.");
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) return <LoadingState label="Loading assigned field alerts..." />;
  if (error) return <ErrorState message={error} onRetry={() => fetchAlerts(true)} />;

  const activeAlerts = alerts.filter((a) => !a.verification_status || a.verification_status === "pending");
  const completedAlerts = alerts.filter((a) => a.verification_status && a.verification_status !== "pending");
  const displayAlerts = tab === "assigned" ? activeAlerts : completedAlerts;

  return (
    <div className="app-body">
      {/* Left Sidebar for ASHA Navigation */}
      <aside className="app-sidebar desktop-only">
        <div>
          <div className="sidebar-section-label">ASHA Worker Portal</div>
          <nav className="sidebar-nav">
            <button
              className={`sidebar-nav-item ${tab === "assigned" ? "active" : ""}`}
              onClick={() => setTab("assigned")}
            >
              <AlertTriangleIcon size={18} />
              My Alerts ({activeAlerts.length})
            </button>
            <button
              className={`sidebar-nav-item ${tab === "history" ? "active" : ""}`}
              onClick={() => setTab("history")}
            >
              <FileTextIcon size={18} />
              Verification History ({completedAlerts.length})
            </button>
          </nav>
        </div>

        <div style={{ marginTop: "auto", background: "var(--bg)", padding: "12px", borderRadius: "8px" }}>
          <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "var(--secondary-teal)", display: "flex", alignItems: "center", gap: "5px" }}>
            <ShieldCheckIcon size={14} />
            Field Privacy Protocol
          </div>
          <p style={{ fontSize: "0.72rem", color: "var(--muted)", marginTop: "4px" }}>
            All citizen data is strictly anonymized and aggregate protected.
          </p>
        </div>
      </aside>

      {/* Main ASHA Field Content */}
      <main className="app-main full-width">
        <div className="card" style={{ borderLeft: "5px solid var(--secondary-teal)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <span className="sidebar-section-label" style={{ border: "none", padding: 0 }}>
                GROUND HEALTH WORKER PORTAL
              </span>
              <h1 style={{ fontSize: "1.6rem", margin: "2px 0" }}>{t("ashaPortal")}</h1>
              <p className="card-subtitle">
                Ground Field Verification Panel. Review assigned block early-awareness signals and submit field observation notes.
              </p>
            </div>
            <span className="ver-badge ver-verified" style={{ background: "#E6FFFA", color: "#0F766E", border: "1px solid #B2F5EA", padding: "6px 14px" }}>
              <UserCheckIcon size={16} /> Signal Verification Active
            </span>
          </div>
        </div>

        {successMsg && (
          <div
            style={{
              marginBottom: "16px",
              padding: "12px 16px",
              background: "#DCFCE7",
              color: "#15803D",
              border: "1px solid #86EFAC",
              borderRadius: "10px",
              fontWeight: 600,
              fontSize: "0.9rem",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <CheckCircleIcon size={18} />
            {successMsg}
          </div>
        )}

        {displayAlerts.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "40px" }}>
            <UserCheckIcon size={40} color="var(--secondary-teal)" style={{ margin: "0 auto 12px" }} />
            <h3>{tab === "assigned" ? "No Early Awareness Field Alerts Assigned" : "No Verification History Yet"}</h3>
            <p style={{ marginTop: "6px", color: "var(--muted)" }}>
              {tab === "assigned"
                ? "You currently have no pending early-awareness signals assigned to your block for field verification."
                : "No completed field verification notes in your history. Verify an assigned alert to see it here."}
            </p>
          </div>
        ) : (
          <div className="alerts-list" style={{ display: "grid", gap: "16px" }}>
            {displayAlerts.map((alert) => {
              const form = formState[alert.id] || {
                status: alert.verification_status || "pending",
                notes: alert.field_observation || "",
              };
              const m = getRealisticMetrics(alert);
              const title = formatCategory(alert.topic_tag || alert.topic_category);

              return (
                <div
                  key={alert.id}
                  className="card"
                  style={{
                    padding: "20px",
                    borderLeft: `5px solid ${alert.severity === "high" ? "var(--danger)" : alert.severity === "moderate" ? "var(--warning)" : "var(--secondary-teal)"}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", flexWrap: "wrap" }}>
                    <div>
                      <div className="badge-group" style={{ marginBottom: "6px" }}>
                        <SeverityBadge severity={alert.severity} />
                        <VerificationBadge status={alert.verification_status} />
                      </div>
                      <h3 style={{ fontSize: "1.2rem", margin: "2px 0" }}>
                        {title} — {alert.block_name} Block, {alert.district} District
                      </h3>
                      <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "4px 0 0 0", display: "flex", alignItems: "center", gap: "6px" }}>
                        <MapPinIcon size={14} color="var(--secondary-teal)" />
                        Period: <strong>{alert.period_bucket}</strong> · Observed Queries: <strong className="text-danger">{m.observed}</strong> (Baseline: {m.baseline.toFixed(1)}) · Z-Score: <strong>{m.z.toFixed(2)}</strong>
                      </p>
                    </div>
                  </div>

                  {/* Verification Form */}
                  <div
                    style={{
                      marginTop: "16px",
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      padding: "16px",
                      borderRadius: "12px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <label style={{ fontWeight: 700, fontSize: "0.88rem", display: "block", marginBottom: "6px", color: "var(--primary-dark)" }}>
                        Ground Field Status:
                      </label>
                      <select
                        value={form.status}
                        onChange={(e) => {
                          const val = e.target.value;
                          setFormState((prev) => ({
                            ...prev,
                            [alert.id]: {
                              status: val,
                              notes: prev[alert.id]?.notes ?? alert.field_observation ?? "",
                            },
                          }));
                        }}
                        style={{ width: "100%", padding: "10px", fontWeight: 600 }}
                      >
                        <option value="pending">Pending Verification</option>
                        <option value="verified">Verified (Ground Field Notes Submitted)</option>
                        <option value="not_confirmed">Not Confirmed (No Anomaly Found)</option>
                        <option value="resolved">Resolved (Field Action Taken)</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ fontWeight: 700, fontSize: "0.88rem", display: "block", marginBottom: "6px", color: "var(--primary-dark)" }}>
                        Field Observation & Survey Notes:
                      </label>
                      <textarea
                        rows={3}
                        value={form.notes}
                        onChange={(e) => {
                          const val = e.target.value;
                          setFormState((prev) => ({
                            ...prev,
                            [alert.id]: {
                              status: prev[alert.id]?.status ?? alert.verification_status ?? "pending",
                              notes: val,
                            },
                          }));
                        }}
                        placeholder="e.g. Conducted door-to-door survey in Niali Block. Identified 4 fever cases, distributed ORS and fever medications."
                        style={{ width: "100%", padding: "10px" }}
                      />
                    </div>

                    <button
                      className="btn-primary"
                      onClick={() => handleUpdate(alert.id)}
                      disabled={updatingId === alert.id}
                      style={{ alignSelf: "flex-start", marginTop: "4px" }}
                    >
                      <FileTextIcon size={16} />
                      {updatingId === alert.id ? "Saving..." : "Save Field Verification"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
