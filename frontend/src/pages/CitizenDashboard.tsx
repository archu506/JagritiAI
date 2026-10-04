import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { StatCard } from "../components/Cards";
import { LoadingState, EmptyState, ErrorState } from "../components/States";
import {
  HelpCircleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  ActivityIcon,
} from "../components/Icons";

interface HistoryItem {
  id: string;
  question: string;
  answer: string;
  language: string;
  safety_flag: string;
  contributed_to_public_health: boolean;
  created_at: string;
}

export default function CitizenDashboard() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setItems(null);
    setError(null);
    api.get<HistoryItem[]>("/dashboard/citizen/history")
      .then((res) => setItems(res.data))
      .catch((e) => setError(e?.response?.data?.detail ?? "Could not load your history."));
  };

  useEffect(() => { load(); }, []);

  if (items === null && !error) return <LoadingState label="Loading your health portal..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const contributedCount = items!.filter((i) => i.contributed_to_public_health).length;

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      {/* Warm Welcome Banner & Prominent Ask CTA */}
      <div
        className="card"
        style={{
          background: "linear-gradient(135deg, #0B3B3A 0%, #0F766E 100%)",
          color: "var(--white)",
          padding: "28px 32px",
          borderRadius: "16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <span style={{ fontSize: "0.75rem", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", color: "#A7F3D0" }}>
            MY HEALTH PORTAL
          </span>
          <h2 style={{ color: "var(--white)", fontSize: "1.6rem", margin: "4px 0" }}>
            Welcome to JagritiAI
          </h2>
          <p style={{ color: "#E2E8F0", fontSize: "0.92rem", margin: 0 }}>
            Ask health questions in your language and get grounded guidance.
          </p>
        </div>
        <Link to="/ask" className="btn-primary" style={{ background: "var(--accent-green)", color: "#0B3B3A", padding: "12px 24px", fontSize: "0.95rem", fontWeight: 800, textDecoration: "none" }}>
          <SparklesIcon size={18} color="#0B3B3A" />
          Ask JagritiAI Now
        </Link>
      </div>

      {/* KPI Stats */}
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
        <StatCard
          label="Questions Asked"
          value={items!.length}
          tone="info"
          icon={<HelpCircleIcon size={20} />}
        />
        <StatCard
          label="Contributed Anonymously"
          value={contributedCount}
          tone="good"
          icon={<ShieldCheckIcon size={20} />}
        />
      </div>

      {/* Compact Question History */}
      <div className="card">
        <div className="card-header-row">
          <h3 className="card-title">
            <ActivityIcon size={18} color="var(--secondary-teal)" />
            Your Question History
          </h3>
          <span className="card-subtitle">{items!.length} queries recorded</span>
        </div>

        {items!.length === 0 ? (
          <EmptyState message="You haven't asked any health questions yet. Click 'Ask JagritiAI Now' above to get started!" icon="💬" />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {items!.map((item) => (
              <div
                key={item.id}
                className="history-item"
                style={{
                  background: "var(--bg)",
                  padding: "14px 16px",
                  borderRadius: "10px",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <p style={{ fontWeight: 700, color: "var(--primary-dark)", fontSize: "0.95rem", marginBottom: "4px" }}>
                  Q: {item.question}
                </p>
                <p style={{ fontSize: "0.9rem", color: "var(--text)", lineHeight: 1.5, marginBottom: "8px" }}>
                  {item.answer}
                </p>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--muted)" }}>
                  <span>
                    {new Date(item.created_at).toLocaleDateString()} · Language: {item.language.toUpperCase()}
                  </span>
                  {item.contributed_to_public_health && (
                    <span className="ver-badge ver-verified" style={{ fontSize: "0.7rem", padding: "2px 8px" }}>
                      <ShieldCheckIcon size={12} /> Contributed Anonymously
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
