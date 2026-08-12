import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import type { ChartSpec } from "@/lib/chart-data";

/** Monochrome-theme series palette (see --chart-1..5 in index.css). */
const SERIES_COLORS = [
    "var(--chart-1)",
    "var(--chart-2)",
    "var(--chart-3)",
    "var(--chart-4)",
    "var(--chart-5)",
];

/**
 * Bar or line chart of the query rows, chosen by the pure `analyzeResult` heuristic. Default export so
 * `result-view.tsx` can `React.lazy` it — Recharts is heavy (~900 kB) and the chart is opt-in behind the
 * Tabla/Gráfico toggle, so it must not weigh down the initial bundle.
 */
export default function ResultChart({ spec }: { spec: ChartSpec }) {
    const axis = { fontSize: 12, stroke: "var(--muted-foreground)" } as const;
    const common = (
        <>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey={spec.labelKey} tick={axis} />
            <YAxis tick={axis} width={72} />
            <Tooltip
                contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                    color: "var(--popover-foreground)",
                }}
            />
            {spec.series.length > 1 ? <Legend wrapperStyle={{ fontSize: 12 }} /> : null}
        </>
    );

    return (
        <div className="my-2 h-64 w-full" data-testid="result-chart">
            <ResponsiveContainer width="100%" height="100%">
                {spec.kind === "line" ? (
                    <LineChart data={spec.data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
                        {common}
                        {spec.series.map((name, i) => (
                            <Line
                                key={name}
                                type="monotone"
                                dataKey={name}
                                stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                                strokeWidth={2}
                                dot={false}
                            />
                        ))}
                    </LineChart>
                ) : (
                    <BarChart data={spec.data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
                        {common}
                        {spec.series.map((name, i) => (
                            <Bar
                                key={name}
                                dataKey={name}
                                fill={SERIES_COLORS[i % SERIES_COLORS.length]}
                            />
                        ))}
                    </BarChart>
                )}
            </ResponsiveContainer>
        </div>
    );
}
