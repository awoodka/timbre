import { useState } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import BookDetail from './pages/BookDetail'
import Library from './pages/Library'

export default function App() {
  // Shared ratings state so Home can show recommendations
  const [ratings, setRatings] = useState([])
  const [results, setResults] = useState(null)

  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="nav-logo">Timbre</Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/library">Library</Link>
        </div>
      </nav>
      <main className="main-content">
        <Routes>
          <Route path="/" element={
            <Home
              ratings={ratings}
              setRatings={setRatings}
              results={results}
              setResults={setResults}
            />
          } />
          <Route path="/book/:id" element={<BookDetail />} />
          <Route path="/library" element={<Library />} />
        </Routes>
      </main>
    </div>
  )
}
