export default function EmotionBar({ breakdown }) {
  if (!breakdown) return null

  const sorted = Object.entries(breakdown).sort((a, b) => b[1] - a[1])

  return (
    <div className="chart-container">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {sorted.map(([key, value]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{
              width: 140, fontSize: '0.78rem', color: '#8a7f76',
              textTransform: 'capitalize', flexShrink: 0,
            }}>
              {key.replace(/_/g, ' ')}
            </span>
            <div style={{
              flex: 1, height: 18, background: '#f0ebe5',
              borderRadius: 4, overflow: 'hidden', position: 'relative',
            }}>
              <div style={{
                width: `${value * 100}%`, height: '100%',
                background: `linear-gradient(90deg, #c4b5d4, ${value > 0.7 ? '#b48b6e' : '#b0c4a8'})`,
                borderRadius: 4, transition: 'width 0.5s ease',
              }} />
            </div>
            <span style={{ width: 36, fontSize: '0.78rem', color: '#8a7f76', textAlign: 'right' }}>
              {value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
