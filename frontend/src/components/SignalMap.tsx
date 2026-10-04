import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { formatCategory } from "./Cards";

export interface MapPoint {
  id: string;
  latitude: number;
  longitude: number;
  label: string;
  sublabel?: string;
  intensity: number; // drives radius, e.g. observed_count or z_score
  severity?: "low" | "moderate" | "high";
}

const SEVERITY_COLOR: Record<string, string> = {
  high: "#b91c1c",
  moderate: "#d97706",
  low: "#ca8a04",
};

const DEFAULT_CENTER: [number, number] = [20.2961, 85.8245]; // Bhubaneswar, Odisha

export default function SignalMap({ points, height = 360 }: { points: MapPoint[]; height?: number }) {
  const maxIntensity = Math.max(1, ...points.map((p) => p.intensity));

  return (
    <div className="map-wrapper" style={{ height, position: "relative" }}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={8}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoomControl position="bottomright" />
        {points.map((p) => {
          const color = p.severity ? SEVERITY_COLOR[p.severity] : "#0b6e4f";
          const radius = 8 + (p.intensity / maxIntensity) * 20;
          return (
            <CircleMarker
              key={p.id}
              center={[p.latitude, p.longitude]}
              radius={radius}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.5, weight: 2 }}
            >
              <Popup>
                <div style={{ padding: "4px 2px", minWidth: "140px" }}>
                  <strong style={{ fontSize: "0.95rem", color: "#074e38" }}>{formatCategory(p.label)}</strong>
                  {p.sublabel && <div style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "2px" }}>{p.sublabel}</div>}
                  <div style={{ fontSize: "0.8rem", marginTop: "4px" }}>Signal Volume: {p.intensity} queries</div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}

