import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from 'recharts';
import type { TelemetryPoint } from '../lib/types';
import { metricLabel, metricUnit } from '../lib/format';

interface Props {
  data: TelemetryPoint[];
  metric: keyof TelemetryPoint;
  color?: string;
  min?: number;
  max?: number;
  height?: number;
}

export default function TelemetryChart({ data, metric, color = '#00D9FF', min, max, height = 220 }: Props) {
  const chartData = data.map((p) => ({
    time: p.timestamp,
    value: p[metric] as number,
  }));

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="time"
            tickFormatter={(t) => new Date(t * 1000).toLocaleTimeString(undefined, { minute: '2-digit', second: '2-digit' })}
            stroke="rgba(255,255,255,0.15)"
            tick={{ fill: '#545E7A', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            minTickGap={40}
          />
          <YAxis
            stroke="rgba(255,255,255,0.15)"
            tick={{ fill: '#545E7A', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            domain={['auto', 'auto']}
            width={44}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(10,16,32,0.92)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10,
              fontSize: 12,
              fontFamily: 'JetBrains Mono',
            }}
            labelFormatter={(t) => new Date((t as number) * 1000).toLocaleTimeString()}
            formatter={(value) => [`${Number(value).toFixed(2)} ${metricUnit(metric as string)}`, metricLabel(metric as string)]}
          />
          {max !== undefined && (
            <ReferenceLine y={max} stroke="#FF5577" strokeDasharray="4 4" strokeWidth={1} label={{ value: 'max', fill: '#FF5577', fontSize: 10, position: 'insideTopRight' }} />
          )}
          {min !== undefined && (
            <ReferenceLine y={min} stroke="#FFCC66" strokeDasharray="4 4" strokeWidth={1} label={{ value: 'min', fill: '#FFCC66', fontSize: 10, position: 'insideBottomRight' }} />
          )}
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
