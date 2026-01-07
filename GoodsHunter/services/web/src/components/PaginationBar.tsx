import './PaginationBar.css'

interface PaginationBarProps {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export default function PaginationBar({ page, pageSize, total, onPageChange }: PaginationBarProps) {
  const totalPages = Math.ceil(total / pageSize)
  const hasPrev = page > 1
  const hasNext = page < totalPages

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="pagination-bar">
      <button
        className="pagination-button"
        disabled={!hasPrev}
        onClick={() => hasPrev && onPageChange(page - 1)}
      >
        上一页
      </button>
      <span className="pagination-info">
        第 {page} / {totalPages} 页（共 {total} 项）
      </span>
      <button
        className="pagination-button"
        disabled={!hasNext}
        onClick={() => hasNext && onPageChange(page + 1)}
      >
        下一页
      </button>
    </div>
  )
}

