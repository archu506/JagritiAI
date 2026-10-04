import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n, Lang } from "../context/I18nContext";
import {
  GlobeIcon,
  LogOutIcon,
  UserIcon,
  ActivityIcon,
  SearchIcon,
  HospitalIcon,
  HelpCircleIcon,
  LayoutDashboardIcon,
  BuildingIcon,
  UserCheckIcon,
} from "./Icons";

export default function NavBar() {
  const { user, logout } = useAuth();
  const { t, lang, setLang } = useI18n();
  const nav = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const path = location.pathname;

  return (
    <>
      {/* Top Institutional Header */}
      <header className="app-topbar">
        <div className="topbar-left">
          <Link to="/" className="brand-link" onClick={() => setMobileOpen(false)}>
            <ActivityIcon size={24} color="#19A974" />
            <div>
              <span>{t("appName")}</span>
              <span className="brand-sub">Public Health Intelligence Platform</span>
            </div>
          </Link>
          <span className="national-badge desktop-only">
            🇮🇳 SIH25049 Surveillance Engine
          </span>
        </div>

        <div className="topbar-right">
          {/* Multilingual Selector */}
          <div className="lang-selector-wrap">
            <GlobeIcon size={16} color="#A7F3D0" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as Lang)}
              aria-label="Select Language"
            >
              <option value="en">English (EN)</option>
              <option value="hi">हिंदी (HI)</option>
              <option value="or">ଓଡ଼ିଆ (OR)</option>
            </select>
          </div>

          {/* User Context & Logout */}
          {user ? (
            <div className="desktop-only" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span className="user-chip">
                <UserIcon size={15} color="#A7F3D0" />
                {user.full_name} ({user.role.replace("_", " ")})
              </span>
              <button
                className="btn-logout"
                onClick={() => {
                  logout();
                  nav("/");
                }}
              >
                <LogOutIcon size={15} />
                {t("logout")}
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn-logout desktop-only" style={{ textDecoration: "none" }}>
              <UserIcon size={15} />
              {t("login")}
            </Link>
          )}
        </div>
      </header>

      {/* Main Role-Based Navigation Bar */}
      <nav className="citizen-topnav desktop-only">
        <Link to="/ask" className={`citizen-nav-link ${path === "/ask" ? "active" : ""}`}>
          <SearchIcon size={16} />
          {t("askJagriti")}
        </Link>
        <Link to="/schemes" className={`citizen-nav-link ${path === "/schemes" ? "active" : ""}`}>
          <HospitalIcon size={16} />
          {t("schemes")}
        </Link>
        <Link to="/myths" className={`citizen-nav-link ${path === "/myths" ? "active" : ""}`}>
          <HelpCircleIcon size={16} />
          {t("myths")}
        </Link>
        <Link to="/nearby" className={`citizen-nav-link ${path === "/nearby" ? "active" : ""}`}>
          <HospitalIcon size={16} />
          {t("nearby")}
        </Link>
        {user && (
          <Link to="/dashboard" className={`citizen-nav-link ${path === "/dashboard" ? "active" : ""}`}>
            <LayoutDashboardIcon size={16} />
            {t("dashboard")}
          </Link>
        )}
        {user && (user.role === "health_official" || user.role === "admin") && (
          <Link to="/gov" className={`citizen-nav-link ${path === "/gov" ? "active" : ""}`}>
            <BuildingIcon size={16} />
            {t("govDashboard")}
          </Link>
        )}
        {user && (user.role === "asha_worker" || user.role === "admin") && (
          <Link to="/asha" className={`citizen-nav-link ${path === "/asha" ? "active" : ""}`}>
            <UserCheckIcon size={16} />
            {t("ashaPortal")}
          </Link>
        )}
      </nav>
    </>
  );
}
