'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { api } from '@/lib/api'
import { getMediaType, MEDIA_TYPES } from '@/components/mediaType'
import { getEmotionColor } from '@/components/emotionColors'
import { useRatings } from '@/lib/ratings-context'
import ExploreSidePanel from '@/components/ExploreSidePanel'

// Plotly is client-only; load it lazily so SSR doesn't touch `window`.
const Plot = dynamic(() => import('@/components/Plot3D'), {
  ssr: false,
  loading: () => <div className="loading"><span className="spinner" /> Loading 3D view…</div>,
})

const fmt = (s) => s.replace(/_/g, ' ')
const emotionColor = (k) => getEmotionColor(k)?.color || '#8a7f76'

// Cosine over the 31-dim emotion vectors (mirrors catalogue/page.jsx helper).
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
  return na && nb ? dot / (Math.sqrt(na) * Math.sqrt(nb)) : 0
}

// ---- Curated "feeling" axes: signed sums over the emotion dimensions. ----
const AXES = {
  valence: {
    title: 'Valence (pleasant)',
    label: 'distressing  ⟷  pleasant',
    pos: ['warmth', 'joy', 'hope', 'serenity', 'nostalgia', 'intimacy', 'empowerment', 'catharsis', 'ending_valence', 'sensuality', 'wonder'],
    neg: ['dread', 'grief', 'melancholy', 'isolation', 'alienation', 'anger', 'claustrophobia', 'obsession', 'confusion', 'vulnerability'],
  },
  energy: {
    title: 'Energy (intensity)',
    label: 'calm  ⟷  intense',
    pos: ['frenetic_energy', 'tension', 'pacing', 'anger', 'obsession', 'empowerment'],
    neg: ['stillness', 'serenity', 'melancholy', 'nostalgia', 'intimacy'],
  },
  scope: {
    title: 'Scope (scale)',
    label: 'intimate  ⟷  epic',
    pos: ['vastness', 'wonder', 'emotional_complexity', 'moral_ambiguity'],
    neg: ['intimacy', 'vulnerability', 'sensuality', 'claustrophobia'],
  },
}
const AXIS_KEYS = ['valence', 'energy', 'scope']
const DEFAULT_AXES = [
  { type: 'axis', key: 'valence' },
  { type: 'axis', key: 'energy' },
  { type: 'axis', key: 'scope' },
]

const REGIONS = [
  { name: 'cozy · warm', test: (v, e) => v > 0.22 && e < -0.05 },
  { name: 'joyful · lively', test: (v, e) => v > 0.22 && e > 0.25 },
  { name: 'bleak · melancholy', test: (v, e) => v < -0.2 && e < 0.05 },
  { name: 'tense · harrowing', test: (v, e) => v < -0.2 && e > 0.2 },
  { name: 'awe · wonder', test: (v, e, s) => s > 0.35 && v > -0.1 },
  { name: 'intimate · tender', test: (v, e, s) => s < -0.3 && v > -0.05 },
]

const LANDMARKS = [
  'The Road', 'Blood Meridian', '1984', 'The Shining', 'The Hobbit', 'Spirited Away',
  'Death Note', 'Attack on Titan', 'Outer Wilds', 'The Last of Us', 'Chernobyl',
  'Breaking Bad', 'Norwegian Wood', 'A Little Life', 'Interstellar', 'Arrival',
  'Cyberpunk 2077', 'Spiritfarer', 'Gone Girl', 'The Great Gatsby',
]

const COLOR_MODES = [
  { key: 'medium', label: 'Medium' },
  { key: 'dominant', label: 'Emotion' },
  { key: 'dimension', label: 'Dimension' },
]
const MEDIA_KEYS = Object.keys(MEDIA_TYPES)

function axisRawValue(bd, spec) {
  if (!bd) return 0
  if (spec.type === 'emotion') return bd[spec.key] ?? 0
  const a = AXES[spec.key]
  let s = 0
  for (const k of a.pos) s += bd[k] ?? 0
  for (const k of a.neg) s -= bd[k] ?? 0
  return s
}

function standardize(rows) {
  const D = rows[0]?.length || 0
  const out = rows.map((r) => r.slice())
  for (let d = 0; d < D; d++) {
    let mean = 0
    for (const r of rows) mean += r[d]
    mean /= rows.length || 1
    let span = 0
    for (const r of rows) span = Math.max(span, Math.abs(r[d] - mean))
    span = span || 1
    for (let i = 0; i < rows.length; i++) out[i][d] = (rows[i][d] - mean) / span
  }
  return out
}

function dominantEmotion(bd) {
  if (!bd) return 'unknown'
  let best = 'unknown', bv = -Infinity
  for (const [k, v] of Object.entries(bd)) if (v > bv) { bv = v; best = k }
  return best
}

// RMS distance of a set of points from their centroid (spatial spread).
function spread(pts, c) {
  if (!pts.length) return 0
  let s = 0
  for (const p of pts) s += (p.x - c[0]) ** 2 + (p.y - c[1]) ** 2 + (p.z - c[2]) ** 2
  return Math.sqrt(s / pts.length)
}
const centroid = (pts) => pts.reduce((a, p) => [a[0] + p.x, a[1] + p.y, a[2] + p.z], [0, 0, 0]).map((v) => v / pts.length)

const axisLabel = (spec) => (spec.type === 'emotion' ? `more ${fmt(spec.key)} →` : AXES[spec.key].label)

// Native (themed) hover label content: title, then creator · medium.
const hoverText = (p) => `<b>${p.title}</b><br>${p.creator} · ${getMediaType(p.medium).label}`

const axisCfg = (spec) => ({
  title: { text: axisLabel(spec), font: { size: 10, color: '#b9a795' } },
  showticklabels: false,
  showgrid: true,
  gridcolor: 'rgba(214,191,170,0.10)',
  zeroline: false,
  showspikes: false,
  showbackground: false,
  color: '#b9a795',
})

export default function Explore() {
  const { ratings } = useRatings()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [colorMode, setColorMode] = useState('medium')
  const [dimension, setDimension] = useState('melancholy')
  const [axisSel, setAxisSel] = useState(DEFAULT_AXES)
  const [showRegions, setShowRegions] = useState(true)
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [showClouds, setShowClouds] = useState(true)
  const [mediaSel, setMediaSel] = useState(MEDIA_KEYS)
  const [selected, setSelected] = useState(null) // a point

  useEffect(() => {
    api.getMedia()
      .then((all) => setItems(all.filter((i) => i.emotion_breakdown)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const dimensions = useMemo(
    () => (items[0]?.emotion_breakdown ? Object.keys(items[0].emotion_breakdown).sort() : []),
    [items]
  )

  // Display coords {x,y,z} from the chosen axes + fixed {v,e,s} for region membership.
  const points = useMemo(() => {
    if (!items.length) return []
    const xyz = standardize(items.map((it) => axisSel.map((spec) => axisRawValue(it.emotion_breakdown, spec))))
    const ves = standardize(items.map((it) => AXIS_KEYS.map((k) => axisRawValue(it.emotion_breakdown, { type: 'axis', key: k }))))
    return items.map((it, i) => ({
      ...it, x: xyz[i][0], y: xyz[i][1], z: xyz[i][2], v: ves[i][0], e: ves[i][1], s: ves[i][2],
    }))
  }, [items, axisSel])

  const visible = useMemo(() => points.filter((p) => mediaSel.includes(p.medium)), [points, mediaSel])
  const pointById = useMemo(() => new Map(points.map((p) => [p.id, p])), [points])

  // Nearest emotional neighbors (top 2) — used only by the side panel's "feels like".
  const neighborsById = useMemo(() => {
    const m = new Map()
    const wv = items.filter((it) => it.emotion_vector)
    for (let i = 0; i < wv.length; i++) {
      let b1 = null, b2 = null, s1 = -Infinity, s2 = -Infinity
      const vi = wv[i].emotion_vector
      for (let j = 0; j < wv.length; j++) {
        if (i === j) continue
        const s = cosine(vi, wv[j].emotion_vector)
        if (s > s1) { s2 = s1; b2 = b1; s1 = s; b1 = wv[j].id }
        else if (s > s2) { s2 = s; b2 = wv[j].id }
      }
      m.set(wv[i].id, [b1, b2].filter(Boolean))
    }
    return m
  }, [items])

  const regions = useMemo(() => {
    if (!visible.length) return []
    return REGIONS.map((r) => {
      const mem = visible.filter((p) => r.test(p.v, p.e, p.s))
      if (mem.length < 4) return null
      const c = centroid(mem)
      return { name: r.name, x: c[0], y: c[1], z: c[2] }
    }).filter(Boolean)
  }, [visible])

  const landmarks = useMemo(() => {
    if (!visible.length) return { items: [], personalized: false }
    const byId = new Map(visible.map((p) => [p.id, p]))
    if (ratings.length) {
      const top = [...ratings]
        .sort((a, b) => b.rating - a.rating)
        .map((r) => { const p = byId.get(r.media_id); return p ? { ...p, rating: r.rating } : null })
        .filter(Boolean)
        .slice(0, 10)
      if (top.length) return { items: top, personalized: true }
    }
    const byTitle = new Map(visible.map((p) => [p.title, p]))
    return { items: LANDMARKS.map((t) => byTitle.get(t)).filter(Boolean), personalized: false }
  }, [visible, ratings])

  // Soft colour clouds — only for colour groups that actually CONCENTRATE in space
  // (an "obvious grouping"), so By-medium (media are interspersed) stays clean while
  // By-emotion reveals colored neighbourhoods. A big, very-low-opacity marker layer.
  const cloudTraces = useMemo(() => {
    if (!showClouds || colorMode === 'dimension' || visible.length < 12) return []
    const gSpread = spread(visible, centroid(visible)) || 1
    const groupKey = colorMode === 'medium' ? (p) => p.medium : (p) => dominantEmotion(p.emotion_breakdown)
    const colorFor = colorMode === 'medium' ? (k) => getMediaType(k).color : emotionColor
    const groups = {}
    for (const p of visible) (groups[groupKey(p)] ||= []).push(p)
    const out = []
    for (const [k, g] of Object.entries(groups)) {
      if (g.length < 8) continue
      if (spread(g, centroid(g)) > 0.72 * gSpread) continue // diffuse → no obvious grouping
      out.push({ type: 'scatter3d', mode: 'markers',
        x: g.map((p) => p.x), y: g.map((p) => p.y), z: g.map((p) => p.z),
        marker: { size: 30, color: colorFor(k), opacity: 0.06 }, hoverinfo: 'skip', showlegend: false })
    }
    return out
  }, [visible, colorMode, showClouds])

  const selectedNeighbors = useMemo(() => (selected
    ? (neighborsById.get(selected.id) || []).map((id) => pointById.get(id)).filter(Boolean)
    : []), [selected, neighborsById, pointById])

  const traces = useMemo(() => {
    if (!visible.length) return []
    const halos = []
    const markers = []

    if (colorMode === 'dimension') {
      const colors = visible.map((p) => p.emotion_breakdown?.[dimension] ?? 0)
      const base = { x: visible.map((p) => p.x), y: visible.map((p) => p.y), z: visible.map((p) => p.z) }
      halos.push({ type: 'scatter3d', mode: 'markers', ...base, customdata: visible.map((p) => p.id),
        text: visible.map(hoverText), hovertemplate: '%{text}<extra></extra>', showlegend: false,
        marker: { size: 14, opacity: 0.13, color: colors, colorscale: 'YlOrRd', cmin: 0, cmax: 1 } })
      markers.push({ type: 'scatter3d', mode: 'markers', ...base, hoverinfo: 'skip',
        marker: { size: 5, opacity: 0.95, color: colors, colorscale: 'YlOrRd', cmin: 0, cmax: 1,
          colorbar: { title: { text: fmt(dimension), font: { color: '#c9b8a8' } }, tickfont: { color: '#c9b8a8' }, thickness: 12, len: 0.5, outlinewidth: 0 } } })
    } else {
      const groupKey = colorMode === 'medium' ? (p) => p.medium : (p) => dominantEmotion(p.emotion_breakdown)
      const colorFor = colorMode === 'medium' ? (k) => getMediaType(k).color : emotionColor
      const labelFor = colorMode === 'medium' ? (k) => getMediaType(k).label : fmt
      const groups = {}
      for (const p of visible) (groups[groupKey(p)] ||= []).push(p)
      const keys = colorMode === 'medium'
        ? Object.keys(MEDIA_TYPES).filter((k) => groups[k])
        : Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length)
      for (const k of keys) {
        const g = groups[k]
        const base = { x: g.map((p) => p.x), y: g.map((p) => p.y), z: g.map((p) => p.z) }
        // Hover/click live on the bigger halo so points are easy to target; the crisp dot is cosmetic.
        halos.push({ type: 'scatter3d', mode: 'markers', ...base, customdata: g.map((p) => p.id),
          text: g.map(hoverText), hovertemplate: '%{text}<extra></extra>', showlegend: false,
          marker: { size: 14, opacity: 0.14, color: colorFor(k) } })
        markers.push({ type: 'scatter3d', mode: 'markers', name: labelFor(k), ...base, hoverinfo: 'skip',
          marker: { size: 5, opacity: 0.92, color: colorFor(k) } })
      }
    }

    const out = []
    out.push(...cloudTraces, ...halos, ...markers)
    if (showRegions && regions.length) {
      out.push({ type: 'scatter3d', mode: 'text',
        x: regions.map((r) => r.x), y: regions.map((r) => r.y), z: regions.map((r) => r.z),
        text: regions.map((r) => r.name), textfont: { size: 13, color: 'rgba(243,233,221,0.62)' },
        hoverinfo: 'skip', showlegend: false })
    }
    if (showLandmarks && landmarks.items.length) {
      const lm = landmarks.items, personal = landmarks.personalized
      out.push({ type: 'scatter3d', mode: 'markers+text',
        x: lm.map((p) => p.x), y: lm.map((p) => p.y), z: lm.map((p) => p.z),
        text: lm.map((p) => (personal ? `${p.title}  ★${Math.round(p.rating)}` : p.title)),
        textposition: 'top center', textfont: { size: 9, color: personal ? '#e3c66a' : '#e8dccb' },
        marker: { size: personal ? 4.5 : 3, color: personal ? '#e3c66a' : '#e8dccb' },
        hoverinfo: 'skip', showlegend: false })
    }
    return out
  }, [visible, colorMode, dimension, regions, landmarks, showRegions, showLandmarks, cloudTraces])

  const layout = useMemo(() => ({
    autosize: true,
    margin: { l: 0, r: 0, t: 0, b: 0 },
    paper_bgcolor: '#211a16',
    showlegend: false,
    uirevision: 'explore',
    hoverlabel: { bgcolor: 'rgba(33,26,22,0.96)', bordercolor: 'rgba(214,191,170,0.35)', font: { color: '#f3e9dd', size: 12 }, align: 'left' },
    scene: {
      xaxis: axisCfg(axisSel[0]),
      yaxis: axisCfg(axisSel[1]),
      zaxis: axisCfg(axisSel[2]),
      bgcolor: '#211a16',
    },
  }), [axisSel])

  // ---- One-time intro spin (~1.1s), cancelled the moment the user grabs the map ----
  const gdRef = useRef(null)
  const introRaf = useRef(0)
  const introDone = useRef(false)

  const onInitialized = useCallback((fig, gd) => {
    gdRef.current = gd
    if (introDone.current || typeof window === 'undefined' || !window.Plotly) return
    introDone.current = true
    const eye = gd._fullLayout?.scene?.camera?.eye
    if (!eye) return
    const r = Math.hypot(eye.x, eye.y) || 1.7
    const a0 = Math.atan2(eye.y, eye.x)
    const z = eye.z
    let start = null
    const cancel = () => { if (introRaf.current) cancelAnimationFrame(introRaf.current); introRaf.current = 0 }
    gd.addEventListener('pointerdown', cancel, { once: true })
    const ease = (t) => 1 - Math.pow(1 - t, 3) // easeOutCubic
    const tick = (ts) => {
      if (!gdRef.current || !window.Plotly) return
      if (start == null) start = ts
      const t = Math.min(1, (ts - start) / 1100)
      const a = a0 + 0.5 * ease(t)
      window.Plotly.relayout(gdRef.current, { 'scene.camera.eye': { x: r * Math.cos(a), y: r * Math.sin(a), z } })
      if (t < 1) introRaf.current = requestAnimationFrame(tick)
    }
    introRaf.current = requestAnimationFrame(tick)
  }, [])

  useEffect(() => () => { if (introRaf.current) cancelAnimationFrame(introRaf.current) }, [])

  const onPointClick = useCallback((e) => {
    const id = e?.points?.[0]?.customdata
    const p = id ? pointById.get(id) : null
    if (p) setSelected(p)
  }, [pointById])

  const setAxis = (i, value) => {
    const [type, key] = value.split(':')
    setAxisSel((prev) => prev.map((s, j) => (j === i ? { type, key } : s)))
  }
  const toggleMedium = (k) => setMediaSel((prev) => (prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k]))

  if (loading) return <div className="loading"><span className="spinner" /> Loading the emotional space…</div>
  if (error) return <p style={{ color: 'var(--error)', marginTop: '1rem' }}>Couldn’t load: {error}</p>

  return (
    <div className="explore-stage warm-dark">
      <div className="explore-canvas">
        <Plot
          data={traces}
          layout={layout}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
          onInitialized={onInitialized}
          onClick={onPointClick}
        />
      </div>

      {/* Lens panel (top-left) */}
      <div className="xp-panel xp-lens">
        <div className="xp-lens-axes">
          {['X', 'Y', 'Z'].map((axis, i) => (
            <label key={axis} className="xp-lens-row">
              <span className="control-label">{axis}</span>
              <select className="sort-select" value={`${axisSel[i].type}:${axisSel[i].key}`} onChange={(e) => setAxis(i, e.target.value)}>
                <optgroup label="Feeling scales">
                  {AXIS_KEYS.map((k) => <option key={k} value={`axis:${k}`}>{AXES[k].title}</option>)}
                </optgroup>
                <optgroup label="Single emotion">
                  {dimensions.map((d) => <option key={d} value={`emotion:${d}`}>{fmt(d)}</option>)}
                </optgroup>
              </select>
            </label>
          ))}
        </div>

        <div className="seg">
          {COLOR_MODES.map((m) => (
            <button key={m.key} className={`seg-btn${colorMode === m.key ? ' on' : ''}`} onClick={() => setColorMode(m.key)}>
              {m.label}
            </button>
          ))}
        </div>
        {colorMode === 'dimension' && (
          <select className="sort-select" value={dimension} onChange={(e) => setDimension(e.target.value)}>
            {dimensions.map((d) => <option key={d} value={d}>{fmt(d)}</option>)}
          </select>
        )}

        <div className="xp-lens-toggles">
          <label className="explore-toggle"><input type="checkbox" checked={showClouds} onChange={(e) => setShowClouds(e.target.checked)} /> Clouds</label>
          <label className="explore-toggle"><input type="checkbox" checked={showRegions} onChange={(e) => setShowRegions(e.target.checked)} /> Regions</label>
          <label className="explore-toggle"><input type="checkbox" checked={showLandmarks} onChange={(e) => setShowLandmarks(e.target.checked)} /> {landmarks.personalized ? 'Top-rated' : 'Landmarks'}</label>
        </div>
      </div>

      {/* Legend + media filter (bottom-left) */}
      <div className="xp-panel xp-legend">
        <div className="catalogue-filters">
          {MEDIA_KEYS.map((k) => {
            const color = getMediaType(k).color
            const active = mediaSel.includes(k)
            const count = points.filter((p) => p.medium === k).length
            return (
              <button
                key={k}
                className={`filter-pill${active ? ' active' : ''}`}
                onClick={() => toggleMedium(k)}
                style={active ? { background: color, borderColor: color, color: '#fff' } : { borderColor: color, color }}
              >
                {getMediaType(k).label} <span className="filter-count">{count}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Caption (bottom-right) */}
      <div className="xp-panel xp-caption">
        <strong>{visible.length} works.</strong> Nearby points feel similar. Drag to rotate, scroll to zoom, hover for details, click to preview.
      </div>

      <ExploreSidePanel point={selected} neighbors={selectedNeighbors} onClose={() => setSelected(null)} />
    </div>
  )
}
