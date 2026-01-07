import './LoadingSkeleton.css'

export default function LoadingSkeleton() {
  return (
    <div className="loading-skeleton">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-image"></div>
          <div className="skeleton-info">
            <div className="skeleton-line skeleton-line-short"></div>
            <div className="skeleton-line"></div>
            <div className="skeleton-line skeleton-line-short"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

