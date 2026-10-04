import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from "recharts";

export interface SeriesPoint {
  day_bucket: string;
  count: number;
}

export function TrendLineChart({ series, baselineMean, height = 260 }: { series: SeriesPoint[]; baselineMean?: number; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="day_bucket" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        {baselineMean !== undefined && (
          <ReferenceLine y={baselineMean} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: "Baseline", fontSize: 10, fill: "#64748b" }} />
        )}
        <Line type="monotone" dataKey="count" stroke="#0b6e4f" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
