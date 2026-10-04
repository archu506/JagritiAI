import { Link } from "react-router-dom";
import { useI18n } from "../context/I18nContext";
import {
  ActivityIcon,
  SearchIcon,
  ShieldCheckIcon,
  BuildingIcon,
  HelpCircleIcon,
  ArrowRightIcon,
  SparklesIcon,
  UserCheckIcon,
} from "../components/Icons";

export default function LandingPage() {
  const { t } = useI18n();

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
      {/* Hero Section */}
      <div
        className="card"
        style={{
          background: "linear-gradient(135deg, #0B3B3A 0%, #0F766E 100%)",
          color: "var(--white)",
          padding: "48px 36px",
          borderRadius: "18px",
          marginBottom: "28px",
          boxShadow: "var(--shadow-md)",
        }}
      >
        <span style={{ fontSize: "0.78rem", fontWeight: 800, letterSpacing: "1.2px", textTransform: "uppercase", color: "#A7F3D0", display: "inline-flex", alignItems: "center", gap: "6px" }}>
          <ActivityIcon size={16} color="#A7F3D0" />
          NATIONAL PUBLIC HEALTH INTELLIGENCE PLATFORM
        </span>
        <h1 style={{ color: "var(--white)", fontSize: "2.4rem", margin: "10px 0", letterSpacing: "-0.03em" }}>
          {t("appName")}
        </h1>
        <p style={{ color: "#E2E8F0", fontSize: "1.15rem", fontWeight: 600, marginBottom: "8px" }}>
          {t("landingSubtitle")} — {t("tagline")}
        </p>
        <p style={{ color: "#CBD5E1", fontSize: "0.95rem", maxWidth: "780px", marginBottom: "24px" }}>
          An integrated public-health awareness engine bridging everyday citizen health queries with district-level statistical anomaly surveillance.
        </p>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <Link to="/ask" className="btn-primary" style={{ background: "var(--accent-green)", color: "#0B3B3A", padding: "12px 24px", fontSize: "0.95rem", fontWeight: 800, textDecoration: "none" }}>
            <SparklesIcon size={18} color="#0B3B3A" />
            {t("askJagriti")}
          </Link>
          <Link to="/myths" className="btn-secondary" style={{ background: "rgba(255,255,255,0.12)", color: "var(--white)", border: "1px solid rgba(255,255,255,0.3)", padding: "12px 20px", textDecoration: "none" }}>
            <HelpCircleIcon size={18} />
            {t("exploreDisease")}
          </Link>
          <Link to="/login" className="btn-secondary" style={{ background: "transparent", color: "#A7F3D0", border: "1px solid #A7F3D0", padding: "12px 20px", textDecoration: "none" }}>
            <BuildingIcon size={18} />
            {t("forHealthOfficials")}
          </Link>
        </div>
      </div>

      {/* Problem & Solution Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px", marginBottom: "28px" }}>
        <div className="card" style={{ borderTop: "4px solid var(--warning)" }}>
          <h2 style={{ fontSize: "1.25rem", color: "var(--primary-dark)", marginBottom: "8px" }}>
            ⚠️ {t("landingProblemTitle")}
          </h2>
          <p style={{ fontSize: "0.92rem", color: "var(--text)", lineHeight: 1.6 }}>
            {t("landingProblemText")}
          </p>
        </div>
        <div className="card" style={{ borderTop: "4px solid var(--accent-green)" }}>
          <h2 style={{ fontSize: "1.25rem", color: "var(--primary-dark)", marginBottom: "8px" }}>
            ⚡ {t("landingSolutionTitle")}
          </h2>
          <p style={{ fontSize: "0.92rem", color: "var(--text)", lineHeight: 1.6 }}>
            {t("landingSolutionText")}
          </p>
        </div>
      </div>

      {/* 3-Step Pipeline Flow */}
      <div className="card" style={{ marginBottom: "28px" }}>
        <h2 style={{ fontSize: "1.3rem", textAlign: "center", marginBottom: "20px" }}>
          {t("flowTitle")}
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
          <div style={{ background: "var(--bg)", padding: "20px", borderRadius: "12px", textAlign: "center" }}>
            <div style={{ width: "48px", height: "48px", background: "var(--accent-green-bg)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
              <SearchIcon size={24} color="var(--secondary-teal)" />
            </div>
            <h3 style={{ fontSize: "1rem", marginBottom: "6px" }}>{t("flowStep1Title")}</h3>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{t("flowStep1Text")}</p>
          </div>

          <div style={{ background: "var(--bg)", padding: "20px", borderRadius: "12px", textAlign: "center" }}>
            <div style={{ width: "48px", height: "48px", background: "#FEF3C7", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
              <ShieldCheckIcon size={24} color="var(--warning)" />
            </div>
            <h3 style={{ fontSize: "1rem", marginBottom: "6px" }}>{t("flowStep2Title")}</h3>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{t("flowStep2Text")}</p>
          </div>

          <div style={{ background: "var(--bg)", padding: "20px", borderRadius: "12px", textAlign: "center" }}>
            <div style={{ width: "48px", height: "48px", background: "#E0F2FE", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
              <BuildingIcon size={24} color="var(--secondary-teal)" />
            </div>
            <h3 style={{ fontSize: "1rem", marginBottom: "6px" }}>{t("flowStep3Title")}</h3>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{t("flowStep3Text")}</p>
          </div>
        </div>
      </div>

      {/* Privacy & Clinical AI Notice */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
        <div className="card">
          <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <ShieldCheckIcon size={20} color="var(--secondary-teal)" />
            {t("privacyTitle")}
          </h3>
          <p style={{ fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.6 }}>
            {t("privacyText")}
          </p>
        </div>

        <div className="card" style={{ background: "#FFFBEB", borderColor: "#FDE68A" }}>
          <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", color: "#92400E" }}>
            ⚕️ {t("aiDisclaimerTitle")}
          </h3>
          <p style={{ fontSize: "0.88rem", color: "#78350F", lineHeight: 1.6 }}>
            {t("aiDisclaimerText")}
          </p>
        </div>
      </div>
    </div>
  );
}
