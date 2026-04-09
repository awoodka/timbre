import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip,
} from 'recharts'

export default function EmotionRadar({ breakdown, size = 400 }) {
  if (!breakdown) return null

  const data = Object.entries(breakdown)
    .map(([key, value]) => ({
      dimension: key.replace(/_/g, ' '),
      value: Math.round(value * 100) / 100,
      fullMark: 1,
    }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={size}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#e8e0d8" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#8a7f76', fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={{ fill: '#b0a89e', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              background: '#ffffff',
              border: '1px solid #e8e0d8',
              borderRadius: 8,
              color: '#3a3330',
              fontSize: 13,
            }}
            formatter={(value) => [value.toFixed(2), 'Score']}
          />
          <Radar
            dataKey="value"
            stroke="#b48b6e"
            fill="#b48b6e"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
