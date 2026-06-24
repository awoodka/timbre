'use client'

import { getEmotionColor } from '@/components/emotionColors'

// The taste profile as a smooth, glowing "aura" — an organic colour bloom rather than a
// spiky radar. The shape bulges toward the emotions you're drawn to; each direction is
// tinted by that emotion's hue (fading to neutral where you're indifferent); a soft glow
// + light core make it feel alive. Fully deterministic from the data → uniquely yours.
const SIZE = 320
const C = SIZE / 2
const R = 142
const BASE = 0.46 // floor radius → a rounded bloom, not collapsed spikes
const NEUTRAL = '#cdc3b6'

function hexToRgb(h) {
  const n = parseInt(h.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
function mix(a, b, t) {
  const A = hexToRgb(a), B = hexToRgb(b)
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`
}

// Catmull-Rom → cubic bezier, closed: a smooth organic outline through the polar points.
function smoothClosedPath(pts) {
  const n = pts.length
  let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)} `
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n]
    const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6
    const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6
    d += `C ${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)} `
  }
  return d + 'Z'
}

export default function FingerprintAura({ data }) {
  if (!data || !data.length) return null
  const n = data.length

  const pts = data.map((d, i) => {
    const a = (-90 + (i / n) * 360) * (Math.PI / 180)
    const r = (BASE + d.value * (1 - BASE)) * R
    return [C + r * Math.cos(a), C + r * Math.sin(a)]
  })
  const clip = `path('${smoothClosedPath(pts)}')`

  // each emotion's hue at its angle, faded to neutral where you're indifferent
  const tint = (d) => mix(getEmotionColor(d.key).color, NEUTRAL, 1 - Math.min(1, d.value * 1.25))
  const stops = data.map((d, i) => `${tint(d)} ${((i / n) * 360).toFixed(1)}deg`).join(', ')
  const conic = `conic-gradient(from -90deg at 50% 50%, ${stops}, ${tint(data[0])} 360deg)`

  return (
    <div className="aura" style={{ width: SIZE, height: SIZE }} aria-hidden="true">
      <div className="aura-glow" style={{ background: conic, clipPath: clip }} />
      <div className="aura-fill" style={{ background: conic, clipPath: clip }} />
      <div className="aura-core" style={{ clipPath: clip }} />
    </div>
  )
}
