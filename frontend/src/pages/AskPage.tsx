import { useState } from "react";
import { api } from "../api/client";
import { useI18n } from "../context/I18nContext";
import { useVoice } from "../api/useVoice";
import { LoadingState, ErrorState } from "../components/States";
import {
  SearchIcon,
  MicIcon,
  ShieldCheckIcon,
  SparklesIcon,
  FileTextIcon,
  AlertTriangleIcon,
} from "../components/Icons";
import type { QueryResponse } from "../types";

const SESSION_ID = (() => {
  const existing = sessionStorage.getItem("jagriti_session_id");
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  sessionStorage.setItem("jagriti_session_id", fresh);
  return fresh;
})();

export default function AskPage() {
  const { t, lang } = useI18n();
  const voice = useVoice(lang);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [consentGiven, setConsentGiven] = useState<null | boolean>(null);
  const [error, setError] = useState<string | null>(null);

  const suggestions = [
    "What are the symptoms of dengue?",
    "How can I prevent malaria?",
    "Is drinking alcohol enough to prevent dengue?",
  ];

  const submit = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setConsentGiven(null);
    try {
      const res = await api.post<QueryResponse>("/query", {
        question,
        session_id: SESSION_ID,
        language: lang,
      });
      setResult(res.data);
      console.debug(`[JagritiAI Dev] provider: ${res.data.provider} · safety: ${res.data.safety_flag}`);
      voice.speak(res.data.answer);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleConsent = async (granted: boolean) => {
    if (!result) return;
    await api.post("/consent", { query_id: result.query_id, granted });
    setConsentGiven(granted);
  };

  const showConsentPrompt =
    result &&
    consentGiven === null &&
    result.safety_flag === "ok";

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto" }}>
      <div className="ask-box-card">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <SparklesIcon size={22} color="var(--secondary-teal)" />
          <h2 style={{ fontSize: "1.5rem" }}>{t("askQuestion")}</h2>
        </div>
        <p style={{ fontSize: "0.88rem", color: "var(--muted)", marginBottom: "16px" }}>
          Get grounded, source-backed public health answers in your own language.
        </p>

        <div className="ask-row">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t("askPlaceholder")}
            rows={3}
          />
          <div className="ask-actions">
            {voice.supported && (
              <button
                type="button"
                className={voice.listening ? "btn-mic listening" : "btn-mic"}
                onClick={() => voice.startListening((text) => setQuestion(text))}
                title="Voice input"
              >
                <MicIcon size={18} />
              </button>
            )}
            <button className="btn-primary" onClick={submit} disabled={loading || !question.trim()}>
              <SearchIcon size={16} />
              {loading ? "Analyzing..." : t("send")}
            </button>
          </div>
        </div>

        {!question && !result && (
          <div style={{ marginTop: "16px" }}>
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>
              Suggested Health Topics:
            </span>
            <div className="suggestion-chips">
              {suggestions.map((s) => (
                <button key={s} className="chip" onClick={() => setQuestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && <LoadingState label="Getting a grounded, source-backed answer..." />}
        {error && <ErrorState message={error} onRetry={submit} />}

        {result && (
          <div className={`answer-box flag-${result.safety_flag}`}>
            {result.safety_flag !== "ok" && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--danger)", fontWeight: 700, marginBottom: "8px", fontSize: "0.88rem" }}>
                <AlertTriangleIcon size={16} />
                Safety Triage Alert
              </div>
            )}

            <p className="answer-text">{result.answer}</p>

            {result.sources.length > 0 && (
              <div className="sources">
                <strong style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--primary-dark)" }}>
                  <FileTextIcon size={15} /> Verified Sources:
                </strong>
                <ul>
                  {result.sources.map((s, i) => (
                    <li key={i}>
                      {s.source_name} — {s.title}
                      {s.source_url && (
                        <a href={s.source_url} target="_blank" rel="noreferrer" style={{ marginLeft: "4px", color: "var(--secondary-teal)" }}>
                          ↗
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <details className="dev-details" style={{ marginTop: "12px", fontSize: "0.75rem", color: "var(--muted)" }}>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>Developer Audit Info</summary>
              <p className="provider-tag" style={{ margin: "4px 0 0 0" }}>
                provider: {result.provider} · safety: {result.safety_flag} · session: {SESSION_ID.slice(0, 8)}
              </p>
            </details>

            {showConsentPrompt && (
              <div className="consent-box">
                <p style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <ShieldCheckIcon size={18} color="var(--secondary-teal)" />
                  {t("consentPrompt")}
                </p>
                <div className="consent-actions">
                  <button className="btn-primary" style={{ padding: "6px 14px", fontSize: "0.82rem" }} onClick={() => handleConsent(true)}>
                    {t("consentYes")}
                  </button>
                  <button className="btn-secondary" style={{ padding: "6px 14px", fontSize: "0.82rem" }} onClick={() => handleConsent(false)}>
                    {t("consentNo")}
                  </button>
                </div>
              </div>
            )}
            {consentGiven === true && (
              <p className="consent-ack" style={{ marginTop: "10px", fontSize: "0.85rem", color: "var(--secondary-teal)", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                <ShieldCheckIcon size={16} /> ✓ Thank you — contributed anonymously to public health monitoring.
              </p>
            )}
            {consentGiven === false && (
              <p className="consent-ack" style={{ marginTop: "10px", fontSize: "0.85rem", color: "var(--muted)", fontWeight: 600 }}>
                No data was shared. Your query remains private.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
