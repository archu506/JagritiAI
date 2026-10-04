import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from "recharts";
import { formatCategory } from "./Cards";

export interface BarPoint {
  name: string;
  value: number;
}

const COLORS = ["#0b6e4f", "#0e8a63", "#22a37a", "#4bbf94", "#7fd4b3", "#a8e4cb"];

export function TopicBarChart({ data, height = 240 }: { data: BarPoint[]; height?: number }) {
  const formattedData = data.map((d) => ({
    ...d,
    name: formatCategory(d.name),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={formattedData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={55} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip formatter={(value: number) => [value, "Queries"]} labelFormatter={(label) => formatCategory(String(label))} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {formattedData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

