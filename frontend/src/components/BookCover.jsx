export default function BookCover({ url, size = 'medium' }) {
  const sizes = {
    small: { width: 40, height: 60 },
    medium: { width: 64, height: 96 },
  }
  const { width, height } = sizes[size] || sizes.medium

  if (url) {
    return <img src={url} alt="" className="book-cover-img" style={{ width, height }} />
  }

  return (
    <div className="book-cover-placeholder" style={{ width, height }}>
      <svg viewBox="0 0 24 32" fill="none" width={width * 0.4} height={height * 0.4}>
        <rect x="2" y="1" width="20" height="30" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <line x1="6" y1="8" x2="18" y2="8" stroke="currentColor" strokeWidth="1" />
        <line x1="6" y1="12" x2="15" y2="12" stroke="currentColor" strokeWidth="1" />
        <line x1="6" y1="16" x2="16" y2="16" stroke="currentColor" strokeWidth="1" />
      </svg>
    </div>
  )
}
