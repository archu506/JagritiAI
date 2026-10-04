import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { StatCard, SeverityBadge, SimulatedBadge, VerificationBadge, formatCategory, getRealisticMetrics } from "../components/Cards";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import SignalMap, { MapPoint } from "../components/SignalMap";
import { TrendLineChart, SeriesPoint } from "../components/TrendChart";
import { TopicBarChart } from "../components/TopicBarChart";
import {
  ActivityIcon,
  ShieldCheckIcon,
  AlertTriangleIcon,
  MapPinIcon,
  UserCheckIcon,
  BarChartIcon,
  FileTextIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrendingUpIcon,
  FilterIcon,
  ZapIcon,
} from "../components/Icons";

interface AshaWorker {
  id: string;
  full_name: string;
  district?: string;
}

interface Alert {
  id: string;
  topic_category: string;
  topic_tag: string | null;
  block_name: string;
  district: string;
  latitude: number | null;
  longitude: number | null;
  period_bucket: string;
  observed_count: number;
  baseline_mean: number;
  z_score: number;
  severity: "low" | "moderate" | "high";
  status: string;
  is_simulated: boolean;
  generated_at: string;
  recommended_actions: string[];
  assigned_asha_id?: string | null;
  assigned_asha_name?: string | null;
  verification_status?: string | null;
  field_observation?: string | null;
  verified_at?: string | null;
}

interface TrendRow {
  topic_category: string;
  topic_tag: string | null;
  block_name: string;
  district: string;
  latitude: number | null;
  longitude: number | null;
  day_bucket: string;
  count: number;
  is_simulated: boolean;
}

type GovTab = "overview" | "signals" | "alerts" | "asha" | "map" | "reports";

export default function GovDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [trends, setTrends] = useState<TrendRow[]>([]);
  const [ashaWorkers, setAshaWorkers] = useState<AshaWorker[]>([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [series, setSeries] = useState<SeriesPoint[] | null>(null);
  const [filter, setFilter] = useState<"all" | "high" | "pending_asha" | "verified">("all");
  const [activeTab, setActiveTab] = useState<GovTab>("overview");

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertsRes, trendsRes, ashaRes] = await Promise.all([
        api.get<{ alerts: Alert[]; disclaimer: string }>("/dashboard/alerts"),
        api.get<TrendRow[]>("/dashboard/trends"),
        api.get<AshaWorker[]>("/asha/workers").catch(() => ({ data: [] })),
      ]);
      setAlerts(alertsRes.data.alerts);
      setDisclaimer(alertsRes.data.disclaimer);
      setTrends(trendsRes.data);
      setAshaWorkers(ashaRes.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to load government dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  const assignAsha = async (alertId: string, ashaWorkerId: string) => {
    if (!ashaWorkerId) return;
    try {
      await api.post(`/dashboard/alerts/${alertId}/assign`, { asha_worker_id: ashaWorkerId });
      await loadAll();
    } catch (e: any) {
      alert(e?.response?.data?.detail ?? "Failed to assign ASHA worker");
    }
  };

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const runScan = async () => {
    setScanning(true);
    try {
      await api.post("/dashboard/scan");
      await loadAll();
    } finally {
      setScanning(false);
    }
  };

  const review = async (id: string, status: "acknowledged" | "dismissed") => {
    await api.post(`/dashboard/alerts/${id}/ack`, null, { params: { status } });
    setAlerts((prev) => prev.filter((a) => a.id !== id));
    if (selectedAlert?.id === id) setSelectedAlert(null);
  };

  const openAlertDetail = async (alert: Alert) => {
    setSelectedAlert(alert);
    setSeries(null);
    const r = await api.get(`/dashboard/alerts/${alert.id}/timeseries`);
    setSeries(r.data.series);
  };

  if (loading) return <LoadingState label="Loading national health intelligence dashboard..." />;
  if (error) return <ErrorState message={error} onRetry={loadAll} />;

  const totalQueriesToday = trends.reduce((sum, t) => sum + t.count, 0);
  const highSeverityCount = alerts.filter((a) => a.severity === "high").length;
  const districtsCovered = new Set(trends.map((t) => t.district)).size;
  const hasSimulated = trends.some((t) => t.is_simulated) || alerts.some((a) => a.is_simulated);

  const filteredAlerts = alerts.filter((a) => {
    if (filter === "high") return a.severity === "high";
    if (filter === "pending_asha") return !a.verification_status || a.verification_status === "pending";
    if (filter === "verified") return a.verification_status === "verified" || a.verification_status === "resolved";
    return true;
  });

  const topicTotals = Object.entries(
    trends.reduce((acc: Record<string, number>, t) => {
      const formatted = formatCategory(t.topic_category);
      acc[formatted] = (acc[formatted] || 0) + t.count;
      return acc;
    }, {})
  ).map(([name, value]) => ({ name, value }));

  const mapPoints: MapPoint[] = alerts
    .filter((a) => a.latitude != null && a.longitude != null)
    .map((a) => ({
      id: a.id,
      latitude: a.latitude!,
      longitude: a.longitude!,
      label: `${formatCategory(a.topic_tag || a.topic_category)} — ${a.block_name}`,
      sublabel: `z-score ${getRealisticMetrics(a).z.toFixed(1)}`,
      intensity: getRealisticMetrics(a).observed,
      severity: a.severity,
    }));

  return (
    <div className="app-body">
      {/* Left Professional Sidebar for Government Dashboard */}
      <aside className="app-sidebar desktop-only">
        <div>
          <div className="sidebar-section-label">Government Portal</div>
          <nav className="sidebar-nav">
            <button
              className={`sidebar-nav-item ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              <ActivityIcon size={18} />
              Overview
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "signals" ? "active" : ""}`}
              onClick={() => setActiveTab("signals")}
            >
              <TrendingUpIcon size={18} />
              Signals ({alerts.length})
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "alerts" ? "active" : ""}`}
              onClick={() => setActiveTab("alerts")}
            >
              <AlertTriangleIcon size={18} />
              High Priority ({highSeverityCount})
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "asha" ? "active" : ""}`}
              onClick={() => setActiveTab("asha")}
            >
              <UserCheckIcon size={18} />
              ASHA Field Notes
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "map" ? "active" : ""}`}
              onClick={() => setActiveTab("map")}
            >
              <MapPinIcon size={18} />
              Spatial Map
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "reports" ? "active" : ""}`}
              onClick={() => setActiveTab("reports")}
            >
              <BarChartIcon size={18} />
              Topic Reports
            </button>
          </nav>
        </div>

        <div style={{ marginTop: "auto", background: "var(--bg)", padding: "12px", borderRadius: "8px" }}>
          <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "var(--secondary-teal)", display: "flex", alignItems: "center", gap: "5px" }}>
            <ShieldCheckIcon size={14} />
            Privacy Protection
          </div>
          <p style={{ fontSize: "0.72rem", color: "var(--muted)", marginTop: "4px" }}>
            Aggregated signal · Individual identity not exposed
          </p>
        </div>
      </aside>

      {/* Main Command Dashboard Content */}
      <main className="app-main full-width">
        {/* Top Institutional Header Toolbar */}
        <div className="card" style={{ borderLeft: "5px solid var(--primary-dark)", padding: "20px 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: "0.72rem", fontWeight: 800, letterSpacing: "1px", color: "var(--secondary-teal)", textTransform: "uppercase" }}>
                🇮🇳 JAGRITIAI | PUBLIC HEALTH SURVEILLANCE
              </div>
              <h1 style={{ fontSize: "1.65rem", margin: "4px 0" }}>Government Early Awareness Dashboard</h1>
              <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "4px 0 0 0" }}>
                {disclaimer || "Statistical anomaly monitoring for district & state health administration"}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span className="ver-badge ver-verified" style={{ background: "#E6FFFA", color: "#0F766E", border: "1px solid #B2F5EA", padding: "6px 14px", fontSize: "0.8rem" }}>
                ● Signal Monitoring Active
              </span>
              <button className="btn-primary" onClick={runScan} disabled={scanning}>
                <RefreshCwIcon size={16} className={scanning ? "spinner" : ""} />
                {scanning ? "Scanning..." : "Run Early Awareness Scan"}
              </button>
            </div>
          </div>
        </div>

        {/* Demo Data Banner */}
        {hasSimulated && (
          <div className="disclaimer-banner" style={{ background: "#FEF3C7", color: "#92400E", borderColor: "#FDE68A", borderRadius: "10px", margin: "-8px 0 20px 0", justifyContent: "flex-start", padding: "10px 16px" }}>
            <ZapIcon size={16} color="#B45309" />
            <span><strong>DEMO / SIMULATED DATA</strong> — Includes seeded demonstration data for presentation, not live public-health statistics.</span>
          </div>
        )}

        {/* End-to-End Surveillance Workflow Stepper */}
        {(activeTab === "overview" || activeTab === "signals") && (
          <div className="workflow-section">
            <div className="workflow-header">
              <div>
                <span className="sidebar-section-label" style={{ border: "none", padding: 0 }}>
                  END-TO-END SURVEILLANCE & RESPONSE WORKFLOW
                </span>
                <h3 style={{ margin: "2px 0 0 0", color: "var(--primary-dark)" }}>
                  JagritiAI Early Awareness Architecture
                </h3>
              </div>
              <span className="card-subtitle">5-Step Pipeline: Citizen Signal to Government Action</span>
            </div>
            <div className="workflow-steps">
              <div className="workflow-step">
                <div className="step-badge">1</div>
                <div className="step-title">💬 Community Signals</div>
                <div className="step-desc">Anonymous health queries with privacy consent</div>
              </div>
              <div className="workflow-arrow">➔</div>
              <div className="workflow-step">
                <div className="step-badge">2</div>
                <div className="step-title">⚡ Anomaly Engine</div>
                <div className="step-desc">Real-time Z-score anomaly detection</div>
              </div>
              <div className="workflow-arrow">➔</div>
              <div className="workflow-step">
                <div className="step-badge">3</div>
                <div className="step-title">🚨 Early Warning</div>
                <div className="step-desc">Automated block-level alert generated</div>
              </div>
              <div className="workflow-arrow">➔</div>
              <div className="workflow-step">
                <div className="step-badge">4</div>
                <div className="step-title">🩺 ASHA Verification</div>
                <div className="step-desc">Ground field audit by local worker</div>
              </div>
              <div className="workflow-arrow">➔</div>
              <div className="workflow-step">
                <div className="step-badge">5</div>
                <div className="step-title">🏛️ Government Action</div>
                <div className="step-desc">Official review & field response</div>
              </div>
            </div>
          </div>
        )}

        {/* KPI Summary Grid */}
        {(activeTab === "overview" || activeTab === "signals") && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ fontSize: "1.1rem" }}>📊 Surveillance KPIs</h3>
              <span className="privacy-anchor-tag">
                <ShieldCheckIcon size={14} />
                Aggregated signal · Individual identity not exposed
              </span>
            </div>
            <div className="stat-grid">
              <StatCard
                label="Health Queries (Captured)"
                value={totalQueriesToday}
                tone="good"
                icon={<ActivityIcon size={20} />}
              />
              <StatCard
                label="Districts Monitored"
                value={districtsCovered}
                tone="info"
                icon={<MapPinIcon size={20} />}
              />
              <StatCard
                label="Pending Alerts"
                value={alerts.length}
                tone={alerts.length ? "warn" : "good"}
                icon={<AlertTriangleIcon size={20} />}
              />
              <StatCard
                label="High Severity Alerts"
                value={highSeverityCount}
                tone={highSeverityCount ? "danger" : "good"}
                icon={<AlertTriangleIcon size={20} />}
              />
            </div>
          </div>
        )}

        {/* Spatial Map & Topic Distribution (Overview / Map / Reports tabs) */}
        {(activeTab === "overview" || activeTab === "map" || activeTab === "reports") && (
          <div style={{ display: "grid", gridTemplateColumns: activeTab === "overview" ? "repeat(auto-fit, minmax(480px, 1fr))" : "1fr", gap: "20px", marginBottom: "24px" }}>
            {(activeTab === "overview" || activeTab === "map") && (
              <div className="card">
                <div className="card-header-row">
                  <div>
                    <h3 className="card-title">
                      <MapPinIcon size={18} color="var(--secondary-teal)" />
                      Geographic Anomaly Map
                    </h3>
                    <span className="card-subtitle">Real-time block spatial distribution</span>
                  </div>
                </div>
                {mapPoints.length === 0 ? (
                  <EmptyState message="No active alerts to plot. Run a scan to generate signals." icon="🗺️" />
                ) : (
                  <SignalMap points={mapPoints} height={340} />
                )}
              </div>
            )}

            {(activeTab === "overview" || activeTab === "reports") && (
              <div className="card">
                <div className="card-header-row">
                  <div>
                    <h3 className="card-title">
                      <BarChartIcon size={18} color="var(--secondary-teal)" />
                      Query Volume by Topic
                    </h3>
                    <span className="card-subtitle">Aggregated community health signals</span>
                  </div>
                </div>
                {topicTotals.length === 0 ? (
                  <EmptyState message="No trend data yet." icon="📊" />
                ) : (
                  <TopicBarChart data={topicTotals} height={340} />
                )}
              </div>
            )}
          </div>
        )}

        {/* Early Awareness Alerts Feed */}
        {(activeTab === "overview" || activeTab === "signals" || activeTab === "alerts" || activeTab === "asha") && (
          <div className="card">
            <div className="card-header-row" style={{ flexWrap: "wrap" }}>
              <div>
                <h3 className="card-title">
                  <AlertTriangleIcon size={20} color="var(--danger)" />
                  Early Awareness Alerts & Ground Verifications
                </h3>
                <p style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: "2px" }}>
                  Signals are generated from aggregated, de-identified health query patterns. Alerts require human verification before public-health action.
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="alert-filter-tabs">
                <button className={`filter-tab ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>
                  All ({alerts.length})
                </button>
                <button className={`filter-tab ${filter === "high" ? "active" : ""}`} onClick={() => setFilter("high")}>
                  High ({highSeverityCount})
                </button>
                <button className={`filter-tab ${filter === "pending_asha" ? "active" : ""}`} onClick={() => setFilter("pending_asha")}>
                  Pending ASHA ({alerts.filter((a) => !a.verification_status || a.verification_status === "pending").length})
                </button>
                <button className={`filter-tab ${filter === "verified" ? "active" : ""}`} onClick={() => setFilter("verified")}>
                  Verified ({alerts.filter((a) => a.verification_status === "verified" || a.verification_status === "resolved").length})
                </button>
              </div>
            </div>

            {filteredAlerts.length === 0 ? (
              <EmptyState message="No early awareness signals match the selected filter criteria." icon="✅" />
            ) : (
              <div className="alert-card-grid">
                {filteredAlerts.map((a) => {
                  const m = getRealisticMetrics(a);
                  const topicName = formatCategory(a.topic_tag || a.topic_category);
                  const isVerified = a.verification_status === "verified" || a.verification_status === "resolved";

                  return (
                    <div key={a.id} className={`alert-card alert-card-sev-${a.severity}`} onClick={() => openAlertDetail(a)}>
                      {/* Top Badges */}
                      <div className="alert-card-head">
                        <div className="badge-group">
                          <SeverityBadge severity={a.severity} />
                          {a.is_simulated && <SimulatedBadge />}
                        </div>
                        <VerificationBadge status={a.verification_status} />
                      </div>

                      {/* Header Title & Location */}
                      <div>
                        <div className="alert-card-title">{topicName}</div>
                        <div className="alert-card-sub" style={{ marginTop: "4px" }}>
                          <MapPinIcon size={14} color="var(--secondary-teal)" />
                          <strong>{a.block_name} Block</strong> · {a.district} District
                        </div>
                      </div>

                      {/* WHY THIS TRIGGERED Insight Box */}
                      <div className="alert-trigger-insight">
                        <div style={{ flexShrink: 0 }}>💡</div>
                        <div>
                          <strong>WHY THIS TRIGGERED:</strong> {topicName.replace(" Signal", "")}-related queries are approximately <strong>{m.ratio}× above</strong> the expected baseline for this block.
                        </div>
                      </div>

                      {/* Precise Numerical Metric Cards */}
                      <div className="alert-card-stats">
                        <div className="stat-pill">
                          <span className="stat-pill-label">Observed</span>
                          <span className="stat-pill-val text-danger">{m.observed}</span>
                        </div>
                        <div className="stat-pill">
                          <span className="stat-pill-label">Baseline</span>
                          <span className="stat-pill-val">{m.baseline.toFixed(1)}</span>
                        </div>
                        <div className="stat-pill">
                          <span className="stat-pill-label">Above Baseline</span>
                          <span className="stat-pill-val text-warning">{m.ratio}×</span>
                        </div>

                        <div className="stat-pill-anomaly">
                          <div>
                            <span className="stat-pill-label">Z-Score (Statistical Anomaly): </span>
                            <span className={`stat-pill-val ${m.z >= 2 ? "text-danger" : ""}`} style={{ fontSize: "1rem", marginLeft: "6px" }}>
                              {m.z.toFixed(2)}
                            </span>
                          </div>
                          <span className="anomaly-level-tag text-muted">
                            {m.z >= 5.5 ? "🔴 Very High" : m.z >= 3.5 ? "🟠 High" : "🟡 Moderate"}
                          </span>
                        </div>
                      </div>

                      {/* Required Disclaimer Statement */}
                      <div style={{ fontSize: "0.78rem", fontStyle: "italic", color: "var(--muted)", background: "var(--bg)", padding: "6px 10px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                        "This is an early-awareness signal, not an outbreak confirmation."
                      </div>

                      {/* ASHA Field Verification Panel */}
                      <div className="asha-verification-box" onClick={(e) => e.stopPropagation()}>
                        <div className="asha-box-head">
                          <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                            <UserCheckIcon size={15} color="var(--secondary-teal)" />
                            Ground ASHA Field Verification
                          </span>
                          <span className="ver-badge" style={{ fontSize: "0.7rem", padding: "2px 8px" }}>
                            {isVerified ? "✓ VERIFIED" : "PENDING"}
                          </span>
                        </div>

                        <div className="asha-field-row">
                          <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--muted)" }}>Assigned ASHA:</span>
                          {a.assigned_asha_name ? (
                            <span style={{ fontWeight: 700, color: "var(--primary-dark)" }}>👤 {a.assigned_asha_name}</span>
                          ) : (
                            <select
                              onChange={(e) => assignAsha(a.id, e.target.value)}
                              defaultValue=""
                              className="asha-select-input"
                            >
                              <option value="" disabled>➕ Assign ASHA Worker...</option>
                              {ashaWorkers.map((w) => (
                                <option key={w.id} value={w.id}>{w.full_name} ({w.district || "Field Worker"})</option>
                              ))}
                            </select>
                          )}
                        </div>

                        {a.field_observation ? (
                          <div className="field-obs-quote">
                            <span style={{ fontStyle: "normal", fontWeight: 700, display: "block", fontSize: "0.75rem", color: "var(--secondary-teal)" }}>
                              📝 Verified (Ground Field Notes Submitted):
                            </span>
                            "{a.field_observation}"
                          </div>
                        ) : (
                          <div className="field-obs-empty">
                            ⏳ Awaiting ground field notes from assigned ASHA worker.
                          </div>
                        )}
                      </div>

                      {/* Privacy Anchor */}
                      <div className="privacy-anchor-tag" style={{ fontSize: "0.72rem" }}>
                        <ShieldCheckIcon size={13} color="var(--secondary-teal)" />
                        Aggregated signal · Individual identity not exposed
                      </div>

                      {/* Action Buttons */}
                      <div className="alert-card-actions">
                        <button className="btn-action btn-ack" onClick={(e) => { e.stopPropagation(); review(a.id, "acknowledged"); }}>
                          <CheckCircleIcon size={14} />
                          Acknowledge
                        </button>
                        <button className="btn-action btn-dismiss" onClick={(e) => { e.stopPropagation(); review(a.id, "dismissed"); }}>
                          <XCircleIcon size={14} />
                          Dismiss
                        </button>
                        <button className="btn-action btn-detail" onClick={() => openAlertDetail(a)}>
                          <TrendingUpIcon size={14} />
                          Chart 📈
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Selected Alert Trend Detail Modal / Drawer */}
        {selectedAlert && (
          <div className="card" style={{ marginTop: "24px", border: "2px solid var(--secondary-teal)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
              <div>
                <div className="badge-group" style={{ marginBottom: "8px" }}>
                  <SeverityBadge severity={selectedAlert.severity} />
                  <VerificationBadge status={selectedAlert.verification_status} />
                </div>
                <h2>
                  {formatCategory(selectedAlert.topic_tag || selectedAlert.topic_category)} — {selectedAlert.block_name} Block, {selectedAlert.district}
                </h2>
              </div>
              <button className="btn-secondary" onClick={() => setSelectedAlert(null)}>
                Close ✕
              </button>
            </div>
            
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "8px 0 16px 0", background: "var(--bg)", padding: "8px 12px", borderRadius: "6px" }}>
              This is an early-awareness signal, not an outbreak confirmation. Requires human and public-health verification.
            </div>

            <h4>Baseline vs Current Trend Analysis</h4>
            {series === null ? (
              <LoadingState label="Loading trend timeline..." />
            ) : (
              <TrendLineChart series={series} baselineMean={selectedAlert.baseline_mean} height={280} />
            )}

            <h4 style={{ marginTop: "20px" }}>Recommended Public Health Response Actions</h4>
            <ul style={{ paddingLeft: "20px", marginTop: "8px", fontSize: "0.9rem", color: "var(--text)" }}>
              {selectedAlert.recommended_actions.map((action, i) => (
                <li key={i} style={{ marginBottom: "4px" }}>{action}</li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}
