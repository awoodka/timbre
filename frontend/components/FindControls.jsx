'use client'

import { useState } from 'react'
import NlSearch from '@/components/NlSearch'
import MoodComposer from '@/components/MoodComposer'

// Two compact pills that expand a single panel inline — content-first, so the
// recommendation shelves lead and the search/compose tools stay quiet until needed.
export default function FindControls() {
  const [active, setActive] = useState(null) // 'describe' | 'compose' | null
  const toggle = (k) => setActive((cur) => (cur === k ? null : k))

  return (
    <div className="find-controls">
      <div className="find-pills">
        <button
          type="button"
          className={`find-pill${active === 'describe' ? ' on' : ''}`}
          onClick={() => toggle('describe')}
          aria-expanded={active === 'describe'}
        >
          <span className="find-pill-ic" aria-hidden>✨</span> Describe a feeling
        </button>
        <button
          type="button"
          className={`find-pill${active === 'compose' ? ' on' : ''}`}
          onClick={() => toggle('compose')}
          aria-expanded={active === 'compose'}
        >
          Compose a mood
        </button>
      </div>
      <NlSearch open={active === 'describe'} />
      <MoodComposer open={active === 'compose'} />
    </div>
  )
}
