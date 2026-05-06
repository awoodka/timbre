'use client'

import { createContext, useContext, useState } from 'react'

const RatingsContext = createContext(null)

export function RatingsProvider({ children }) {
  const [ratings, setRatings] = useState([])
  const [results, setResults] = useState(null)

  return (
    <RatingsContext.Provider value={{ ratings, setRatings, results, setResults }}>
      {children}
    </RatingsContext.Provider>
  )
}

export function useRatings() {
  const ctx = useContext(RatingsContext)
  if (!ctx) throw new Error('useRatings must be used within RatingsProvider')
  return ctx
}
