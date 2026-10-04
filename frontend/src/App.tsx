import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { I18nProvider, useI18n } from "./context/I18nContext";
import NavBar from "./components/NavBar";
import { ProtectedRoute } from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import { LoadingState } from "./components/States";

// Route-based code splitting: everything except the landing page (which is
// the very first thing most visitors see) is loaded on demand, so the
// initial JS bundle only has to include what's needed to render "/".
const AskPage = lazy(() => import("./pages/AskPage"));
const CitizenDashboard = lazy(() => import("./pages/CitizenDashboard"));
const GovDashboard = lazy(() => import("./pages/GovDashboard"));
const AshaDashboard = lazy(() => import("./pages/AshaDashboard"));
const LoginPage = lazy(() => import("./pages/AuthPages").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("./pages/AuthPages").then((m) => ({ default: m.RegisterPage })));
const SchemesPage = lazy(() => import("./pages/ContentPages").then((m) => ({ default: m.SchemesPage })));
const MythsPage = lazy(() => import("./pages/ContentPages").then((m) => ({ default: m.MythsPage })));
const NearbyPage = lazy(() => import("./pages/ContentPages").then((m) => ({ default: m.NearbyPage })));

function DisclaimerBanner() {
  const { t } = useI18n();
  return <div className="disclaimer-banner">{t("disclaimerBanner")}</div>;
}

function PageFallback() {
  return <LoadingState label="Loading..." />;
}

function AppShell() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <NavBar />
        <DisclaimerBanner />
        <div style={{ flex: 1, padding: "20px 0" }}>
          <Suspense fallback={<PageFallback />}>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/ask" element={<AskPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/schemes" element={<SchemesPage />} />
              <Route path="/myths" element={<MythsPage />} />
              <Route path="/nearby" element={<NearbyPage />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <CitizenDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/gov"
                element={
                  <ProtectedRoute roles={["health_official", "admin"]}>
                    <GovDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/asha"
                element={
                  <ProtectedRoute roles={["asha_worker", "admin"]}>
                    <AshaDashboard />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Suspense>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </I18nProvider>
  );
}
