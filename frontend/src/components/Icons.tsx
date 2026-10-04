import React from "react";

export interface IconProps {
  className?: string;
  size?: number;
  color?: string;
  style?: React.CSSProperties;
}

export const IconWrapper = ({ children, size = 18, color = "currentColor", className = "", style }: IconProps & { children: React.ReactNode }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={`lucide-icon ${className}`}
    style={{ verticalAlign: "middle", display: "inline-block", flexShrink: 0, ...style }}
  >
    {children}
  </svg>
);

export const ActivityIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <polyline points="22 12 18 12 14 21 10 3 6 12 2 12" />
  </IconWrapper>
);

export const ShieldCheckIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </IconWrapper>
);

export const AlertTriangleIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </IconWrapper>
);

export const MapPinIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z" />
    <circle cx="12" cy="10" r="3" />
  </IconWrapper>
);

export const UserCheckIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <polyline points="16 11 18 13 22 9" />
  </IconWrapper>
);

export const StethoscopeIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M4.8 2.3A.3.3 0 0 0 4.5 2h-1a.5.5 0 0 0-.5.5V9a6 6 0 0 0 12 0V2.5a.5.5 0 0 0-.5-.5h-1a.3.3 0 0 0-.3.3A2.5 2.5 0 0 1 10.7 4.8 2.5 2.5 0 0 1 4.8 2.3z" />
    <path d="M8 15v1a6 6 0 0 0 6 6h2a3 3 0 0 0 3-3v-4.5" />
    <circle cx="19" cy="11.5" r="2.5" />
  </IconWrapper>
);

export const FileTextIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <line x1="10" y1="9" x2="8" y2="9" />
  </IconWrapper>
);

export const SearchIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </IconWrapper>
);

export const MicIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="22" />
  </IconWrapper>
);

export const HelpCircleIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </IconWrapper>
);

export const HospitalIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M12 6v4" />
    <path d="M10 8h4" />
    <path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18" />
    <path d="M4 22h16" />
  </IconWrapper>
);

export const BuildingIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
    <path d="M9 22v-4h6v4" />
    <path d="M8 6h.01" />
    <path d="M16 6h.01" />
    <path d="M12 6h.01" />
    <path d="M12 10h.01" />
    <path d="M12 14h.01" />
    <path d="M16 10h.01" />
    <path d="M16 14h.01" />
    <path d="M8 10h.01" />
    <path d="M8 14h.01" />
  </IconWrapper>
);

export const CheckCircleIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </IconWrapper>
);

export const XCircleIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <circle cx="12" cy="12" r="10" />
    <line x1="15" y1="9" x2="9" y2="15" />
    <line x1="9" y1="9" x2="15" y2="15" />
  </IconWrapper>
);

export const ArrowRightIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </IconWrapper>
);

export const TrendingUpIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </IconWrapper>
);

export const BarChartIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <line x1="12" y1="20" x2="12" y2="10" />
    <line x1="18" y1="20" x2="18" y2="4" />
    <line x1="6" y1="20" x2="6" y2="16" />
  </IconWrapper>
);

export const FilterIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </IconWrapper>
);

export const LogOutIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </IconWrapper>
);

export const UserIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </IconWrapper>
);

export const GlobeIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </IconWrapper>
);

export const RefreshCwIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <polyline points="23 4 23 10 17 10" />
    <polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </IconWrapper>
);

export const SparklesIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3z" />
  </IconWrapper>
);

export const LayoutDashboardIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <rect x="3" y="3" width="7" height="9" rx="1" />
    <rect x="14" y="3" width="7" height="5" rx="1" />
    <rect x="14" y="12" width="7" height="9" rx="1" />
    <rect x="3" y="16" width="7" height="5" rx="1" />
  </IconWrapper>
);

export const ZapIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </IconWrapper>
);
