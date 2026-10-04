import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useI18n } from "../context/I18nContext";
import { LoadingState, EmptyState } from "../components/States";
import SignalMap, { MapPoint } from "../components/SignalMap";
import {
  HospitalIcon,
  HelpCircleIcon,
  SearchIcon,
  MapPinIcon,
  ShieldCheckIcon,
} from "../components/Icons";
import type { HealthScheme, MythFact, HealthFacility } from "../types";

export function SchemesPage() {
  const { t, lang } = useI18n();
  const [schemes, setSchemes] = useState<HealthScheme[] | null>(null);

  useEffect(() => {
    setSchemes(null);
    api.get<HealthScheme[]>("/content/schemes", { params: { language: lang } }).then((r) => setSchemes(r.data));
  }, [lang]);

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <HospitalIcon size={24} color="var(--secondary-teal)" />
          <h2 style={{ fontSize: "1.5rem", margin: 0 }}>{t("schemes")}</h2>
        </div>
        {schemes === null ? (
          <LoadingState label="Loading national & state health schemes..." />
        ) : schemes.length === 0 ? (
          <EmptyState message="No health schemes catalogued yet for this language." icon="🏛️" />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {schemes.map((s) => (
              <div key={s.id} className="scheme-item" style={{ background: "var(--bg)", padding: "16px 20px", borderRadius: "12px", border: "1px solid var(--border-subtle)" }}>
                <h3 style={{ fontSize: "1.1rem", marginBottom: "6px", color: "var(--primary-dark)" }}>{s.name}</h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text)", marginBottom: "8px" }}>{s.description}</p>
                <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  <p><strong>Eligibility:</strong> {s.eligibility}</p>
                  <p><strong>How to apply:</strong> {s.how_to_apply}</p>
                </div>
                {s.official_url && (
                  <a href={s.official_url} target="_blank" rel="noreferrer" className="btn-secondary" style={{ marginTop: "10px", padding: "4px 12px", fontSize: "0.8rem", textDecoration: "none" }}>
                    Official Govt Page ↗
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function MythsPage() {
  const { t, lang } = useI18n();
  const [myths, setMyths] = useState<MythFact[] | null>(null);

  useEffect(() => {
    setMyths(null);
    api.get<MythFact[]>("/content/myths", { params: { language: lang } }).then((r) => setMyths(r.data));
  }, [lang]);

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <HelpCircleIcon size={24} color="var(--secondary-teal)" />
          <h2 style={{ fontSize: "1.5rem", margin: 0 }}>{t("myths")}</h2>
        </div>
        {myths === null ? (
          <LoadingState label="Loading verified myth-busters..." />
        ) : myths.length === 0 ? (
          <EmptyState message="No myth-busters catalogued yet." icon="❓" />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {myths.map((m) => (
              <div key={m.id} className="myth-item" style={{ background: "var(--bg)", padding: "16px 20px", borderRadius: "12px", border: "1px solid var(--border-subtle)" }}>
                <p className="myth" style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "8px" }}>
                  <span className="tag-myth">MYTH</span> {m.myth}
                </p>
                <p className="fact" style={{ fontSize: "0.92rem", color: "var(--text)", lineHeight: 1.5 }}>
                  <span className="tag-fact">FACT</span> {m.fact}
                </p>
                {m.source_name && (
                  <p style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "8px" }}>
                    Source: {m.source_name}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function NearbyPage() {
  const { t } = useI18n();
  const [district, setDistrict] = useState("Khordha");
  const [facilities, setFacilities] = useState<HealthFacility[]>([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const r = await api.get<HealthFacility[]>("/content/facilities/nearby", { params: { district } });
      setFacilities(r.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { search(); }, []);

  const mapPoints: MapPoint[] = facilities
    .filter((f) => f.latitude != null && f.longitude != null)
    .map((f) => ({
      id: f.id,
      latitude: f.latitude!,
      longitude: f.longitude!,
      label: f.name,
      sublabel: f.facility_type,
      intensity: 1,
    }));

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <HospitalIcon size={24} color="var(--secondary-teal)" />
          <h2 style={{ fontSize: "1.5rem", margin: 0 }}>{t("nearby")}</h2>
        </div>

        <div className="ask-row" style={{ marginBottom: "16px" }}>
          <input
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            placeholder="Search by District (e.g. Khordha, Cuttack)"
            style={{ flex: 1 }}
          />
          <button className="btn-primary" onClick={search} disabled={loading}>
            <SearchIcon size={16} />
            {loading ? "Searching..." : "Search Facilities"}
          </button>
        </div>

        {mapPoints.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <SignalMap points={mapPoints} height={300} />
          </div>
        )}

        {loading ? (
          <LoadingState label="Searching nearby government health facilities..." />
        ) : facilities.length === 0 ? (
          <EmptyState message="No health facilities found for this district." icon="🏥" />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "12px" }}>
            {facilities.map((f) => (
              <div key={f.id} className="facility-item" style={{ background: "var(--bg)", padding: "14px 16px", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
                <strong style={{ fontSize: "0.95rem", color: "var(--primary-dark)" }}>{f.name}</strong>
                <div style={{ fontSize: "0.82rem", color: "var(--secondary-teal)", fontWeight: 600, marginTop: "2px" }}>
                  {f.facility_type}
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "6px" }}>
                  <MapPinIcon size={12} /> {f.district}, {f.state} {f.phone && `· 📞 ${f.phone}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
