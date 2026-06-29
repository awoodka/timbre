// Shown when a data fetch fails — so a backend blip reads as a retryable error, not
// as "you have no data" (the old silent-catch behavior).
export default function LoadError({ onRetry, message = 'Couldn’t load — check your connection.' }) {
  return (
    <div className="load-error">
      <p>{message}</p>
      {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
    </div>
  )
}
