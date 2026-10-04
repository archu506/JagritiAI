import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n } from "../context/I18nContext";
import { BuildingIcon, UserIcon, ShieldCheckIcon } from "../components/Icons";
import type { UserRole } from "../types";

export function LoginPage() {
  const { login } = useAuth();
  const { t } = useI18n();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      nav("/ask");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Login failed");
    }
  };

  return (
    <div className="card auth-card">
      <div style={{ textAlign: "center", marginBottom: "16px" }}>
        <div style={{ width: "48px", height: "48px", background: "var(--accent-green-bg)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 10px" }}>
          <BuildingIcon size={24} color="var(--secondary-teal)" />
        </div>
        <h2 style={{ fontSize: "1.4rem" }}>{t("login")}</h2>
        <p className="card-subtitle">Sign in to your JagritiAI account</p>
      </div>

      <form onSubmit={submit}>
        <div>
          <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>Email Address</label>
          <input type="email" placeholder="e.g. officer@health.gov.in" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ width: "100%" }} />
        </div>
        <div>
          <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>Password</label>
          <input type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: "100%" }} />
        </div>

        {error && <p className="error" style={{ fontSize: "0.85rem", fontWeight: 600 }}>⚠️ {error}</p>}

        <button type="submit" className="btn-primary" style={{ width: "100%", padding: "12px" }}>
          {t("login")}
        </button>
      </form>

      <div style={{ marginTop: "20px", textAlign: "center", paddingTop: "14px", borderTop: "1px solid var(--border-subtle)", fontSize: "0.85rem", color: "var(--muted)" }}>
        No account? <Link to="/register" style={{ color: "var(--secondary-teal)", fontWeight: 700 }}>{t("register")}</Link>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const { t } = useI18n();
  const nav = useNavigate();
  const [form, setForm] = useState({
    full_name: "", email: "", password: "",
    preferred_language: "en", district: "", state: "",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register({ ...form, role: "citizen" as UserRole });
      nav("/ask");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Registration failed");
    }
  };

  return (
    <div className="card auth-card" style={{ maxWidth: "460px" }}>
      <div style={{ textAlign: "center", marginBottom: "16px" }}>
        <div style={{ width: "48px", height: "48px", background: "var(--accent-green-bg)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 10px" }}>
          <UserIcon size={24} color="var(--secondary-teal)" />
        </div>
        <h2 style={{ fontSize: "1.4rem" }}>{t("register")}</h2>
        <p className="card-subtitle">Create a public citizen account</p>
      </div>

      <form onSubmit={submit}>
        <div>
          <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>Full Name</label>
          <input placeholder="e.g. Priyadarshini Mohanty" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required style={{ width: "100%" }} />
        </div>
        <div>
          <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>Email Address</label>
          <input type="email" placeholder="e.g. user@example.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required style={{ width: "100%" }} />
        </div>
        <div>
          <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>Password</label>
          <input type="password" placeholder="Minimum 8 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} style={{ width: "100%" }} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
          <div>
            <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>District</label>
            <input placeholder="e.g. Cuttack" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} style={{ width: "100%" }} />
          </div>
          <div>
            <label style={{ fontSize: "0.82rem", fontWeight: 700, display: "block", marginBottom: "4px" }}>State</label>
            <input placeholder="e.g. Odisha" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} style={{ width: "100%" }} />
          </div>
        </div>

        {error && <p className="error" style={{ fontSize: "0.85rem", fontWeight: 600 }}>⚠️ {error}</p>}

        <button type="submit" className="btn-primary" style={{ width: "100%", padding: "12px" }}>
          {t("register")}
        </button>
      </form>

      <div style={{ marginTop: "16px", background: "var(--bg)", padding: "12px", borderRadius: "8px", fontSize: "0.78rem", color: "var(--muted)" }}>
        <ShieldCheckIcon size={14} color="var(--secondary-teal)" /> Health official and admin accounts are provisioned directly by JagritiAI administrators.
      </div>
    </div>
  );
}
