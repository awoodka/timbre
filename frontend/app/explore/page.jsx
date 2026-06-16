'use client'

import { useEffect, useMemo, useState } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { getMediaType, MEDIA_TYPES } from '@/components/mediaType'
import { getEmotionColor } from '@/components/emotionColors'
import { useRatings } from '@/lib/ratings-context'

// Plotly is client-only; load it lazily so SSR doesn't touch `window`.
const Plot = dynamic(() => import('@/components/Plot3D'), {
  ssr: false,
  loading: () => <div className="loading"><span className="spinner" /> Loading 3D view…</div>,
})

const fmt = (s) => s.replace(/_/g, ' ')
const emotionColor = (k) => getEmotionColor(k)?.color || '#8a7f76'

// ---- Curated "feeling" axes: signed sums over the emotion dimensions. Each is an
// intuitive scale; overlaps (e.g. anger is negative-valence AND high-energy) are
// correct per the valence/arousal model. ----
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

// Archetype regions, defined on the (valence, energy, scope) scales so the labels
// stay meaningful even when an axis is overridden to a specific emotion.
const REGIONS = [
  { name: 'cozy · warm', test: (v, e) => v > 0.22 && e < -0.05 },
  { name: 'joyful · lively', test: (v, e) => v > 0.22 && e > 0.25 },
  { name: 'bleak · melancholy', test: (v, e) => v < -0.2 && e < 0.05 },
  { name: 'tense · harrowing', test: (v, e) => v < -0.2 && e > 0.2 },
  { name: 'awe · wonder', test: (v, e, s) => s > 0.35 && v > -0.1 },
  { name: 'intimate · tender', test: (v, e, s) => s < -0.3 && v > -0.05 },
]

// Recognizable works to pin when the user has no ratings yet (filtered to the corpus).
const LANDMARKS = [
  'The Road', 'Blood Meridian', '1984', 'The Shining', 'The Hobbit', 'Spirited Away',
  'Death Note', 'Attack on Titan', 'Outer Wilds', 'The Last of Us', 'Chernobyl',
  'Breaking Bad', 'Norwegian Wood', 'A Little Life', 'Interstellar', 'Arrival',
  'Cyberpunk 2077', 'Spiritfarer', 'Gone Girl', 'The Great Gatsby',
]

const COLOR_MODES = [
  { key: 'medium', label: 'By medium' },
  { key: 'dominant', label: 'By dominant emotion' },
  { key: 'dimension', label: 'By dimension' },
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

// Center each axis on 0 and scale to ~[-1,1] so the cloud frames nicely.
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
function topEmotions(bd, n = 3) {
  if (!bd) return []
  return Object.entries(bd).sort((a, b) => b[1] - a[1]).slice(0, n).map(([k]) => fmt(k))
}

const axisLabel = (spec) => (spec.type === 'emotion' ? `more ${fmt(spec.key)} →` : AXES[spec.key].label)

export default function Explore() {
  const router = useRouter()
  const { ratings } = useRatings()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [colorMode, setColorMode] = useState('medium')
  const [dimension, setDimension] = useState('melancholy')
  const [axisSel, setAxisSel] = useState(DEFAULT_AXES)
  const [showRegions, setShowRegions] = useState(true)
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [mediaSel, setMediaSel] = useState(MEDIA_KEYS)

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

  // Display coordinates (from the chosen axes) plus the fixed valence/energy/scope
  // scales (for region membership), both standardized over the WHOLE corpus so
  // positions stay put when you filter media types.
  const points = useMemo(() => {
    if (!items.length) return []
    const xyz = standardize(items.map((it) => axisSel.map((spec) => axisRawValue(it.emotion_breakdown, spec))))
    const ves = standardize(items.map((it) => AXIS_KEYS.map((k) => axisRawValue(it.emotion_breakdown, { type: 'axis', key: k }))))
    return items.map((it, i) => ({
      ...it, x: xyz[i][0], y: xyz[i][1], z: xyz[i][2], v: ves[i][0], e: ves[i][1], s: ves[i][2],
    }))
  }, [items, axisSel])

  // Points filtered to the selected media types (positions unchanged).
  const visible = useMemo(() => points.filter((p) => mediaSel.includes(p.medium)), [points, mediaSel])

  const regions = useMemo(() => {
    if (!visible.length) return []
    return REGIONS.map((r) => {
      const mem = visible.filter((p) => r.test(p.v, p.e, p.s))
      if (mem.length < 4) return null
      const c = mem.reduce((a, p) => [a[0] + p.x, a[1] + p.y, a[2] + p.z], [0, 0, 0])
      return { name: r.name, x: c[0] / mem.length, y: c[1] / mem.length, z: c[2] / mem.length }
    }).filter(Boolean)
  }, [visible])

  // Personalized anchors: the signed-in user's top-rated works (among the visible
  // media). Falls back to the iconic list when signed out or not yet rated.
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

  const hoverText = (p) =>
    `<b>${p.title}</b><br>${p.creator}<br>${getMediaType(p.medium).label} · ${topEmotions(p.emotion_breakdown).join(', ')}`

  const traces = useMemo(() => {
    if (!visible.length) return []
    const out = []

    if (colorMode === 'dimension') {
      out.push({
        type: 'scatter3d', mode: 'markers',
        x: visible.map((p) => p.x), y: visible.map((p) => p.y), z: visible.map((p) => p.z),
        text: visible.map(hoverText), customdata: visible.map((p) => p.id), hoverinfo: 'text',
        marker: {
          size: 5, opacity: 0.9,
          color: visible.map((p) => p.emotion_breakdown?.[dimension] ?? 0),
          colorscale: 'YlOrRd', cmin: 0, cmax: 1,
          colorbar: { title: { text: fmt(dimension) }, thickness: 12, len: 0.55 },
        },
      })
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
        out.push({
          type: 'scatter3d', mode: 'markers', name: labelFor(k),
          x: g.map((p) => p.x), y: g.map((p) => p.y), z: g.map((p) => p.z),
          text: g.map(hoverText), customdata: g.map((p) => p.id), hoverinfo: 'text',
          marker: { size: 5, opacity: 0.85, color: colorFor(k) },
        })
      }
    }

    if (showRegions && regions.length) {
      out.push({
        type: 'scatter3d', mode: 'text',
        x: regions.map((r) => r.x), y: regions.map((r) => r.y), z: regions.map((r) => r.z),
        text: regions.map((r) => r.name),
        textfont: { size: 13, color: 'rgba(58,51,48,0.45)' },
        hoverinfo: 'skip', showlegend: false,
      })
    }
    if (showLandmarks && landmarks.items.length) {
      const lm = landmarks.items
      const personal = landmarks.personalized
      out.push({
        type: 'scatter3d', mode: 'markers+text',
        x: lm.map((p) => p.x), y: lm.map((p) => p.y), z: lm.map((p) => p.z),
        text: lm.map((p) => (personal ? `${p.title}  ★${Math.round(p.rating)}` : p.title)),
        textposition: 'top center',
        textfont: { size: 9, color: personal ? '#9a7d2e' : '#3a3330' },
        marker: { size: personal ? 4.5 : 3, color: personal ? '#c4a24e' : '#3a3330' },
        hoverinfo: 'skip', showlegend: false,
      })
    }
    return out
  }, [visible, colorMode, dimension, regions, landmarks, showRegions, showLandmarks])

  const axisCfg = (spec) => ({
    title: { text: axisLabel(spec), font: { size: 10, color: '#8a7f76' } },
    showticklabels: false, showgrid: true, gridcolor: 'rgba(0,0,0,0.07)', zeroline: false, showspikes: false,
  })

  const layout = {
    autosize: true,
    margin: { l: 0, r: 0, t: 0, b: 0 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    showlegend: colorMode !== 'dimension',
    legend: { itemsizing: 'constant', font: { size: 11 }, bgcolor: 'rgba(255,255,255,0.65)' },
    uirevision: 'explore',
    scene: {
      xaxis: axisCfg(axisSel[0]),
      yaxis: axisCfg(axisSel[1]),
      zaxis: axisCfg(axisSel[2]),
      bgcolor: 'rgba(0,0,0,0)',
    },
  }

  const onPointClick = (e) => {
    const id = e?.points?.[0]?.customdata
    if (id) router.push(`/book/${id}`)
  }

  const setAxis = (i, value) => {
    const [type, key] = value.split(':')
    setAxisSel((prev) => prev.map((s, j) => (j === i ? { type, key } : s)))
  }

  const toggleMedium = (k) =>
    setMediaSel((prev) => (prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k]))

  if (loading) return <div className="loading"><span className="spinner" /> Loading the emotional space…</div>
  if (error) return <p style={{ color: 'var(--error)', marginTop: '1rem' }}>Couldn’t load: {error}</p>

  return (
    <div className="explore">
      <div className="page-header">
        <h1>Explore the space</h1>
        <p>{visible.length} works · drag to rotate, scroll to zoom, hover for details, click a point to open it</p>
      </div>

      <div className="explore-controls">
        {['X', 'Y', 'Z'].map((axis, i) => (
          <label key={axis} className="control">
            <span className="control-label">{axis} axis</span>
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

      <div className="explore-controls">
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
        <label className="explore-toggle">
          <input type="checkbox" checked={showRegions} onChange={(e) => setShowRegions(e.target.checked)} /> Regions
        </label>
        <label className="explore-toggle">
          <input type="checkbox" checked={showLandmarks} onChange={(e) => setShowLandmarks(e.target.checked)} /> {landmarks.personalized ? 'Your top-rated' : 'Landmarks'}
        </label>
      </div>

      <p className="explore-hint">
        Each point is a work; <strong>nearby points feel emotionally similar</strong>. Axes are intuitive
        feeling scales (set any axis to a single emotion via the dropdowns). Faint labels mark emotional
        regions; the gold ★ works are <strong>your top-rated</strong> (notable landmarks when you’re signed out).
      </p>

      <div className="explore-plot">
        <Plot
          data={traces}
          layout={layout}
          config={{ displayModeBar: true, displaylogo: false, responsive: true }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
          onClick={onPointClick}
        />
      </div>
    </div>
  )
}
