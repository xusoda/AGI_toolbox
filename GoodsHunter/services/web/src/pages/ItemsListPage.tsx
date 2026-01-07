import { useState, useEffect } from 'react'
import { getItems } from '../api/items'
import type { ItemListItem, ItemsListParams } from '../api/types'
import ItemCard from '../components/ItemCard'
import PaginationBar from '../components/PaginationBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import './ItemsListPage.css'

export default function ItemsListPage() {
  const [items, setItems] = useState<ItemListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [sort, setSort] = useState<ItemsListParams['sort']>('last_seen_desc')

  useEffect(() => {
    loadItems()
  }, [page, sort])

  const loadItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: ItemsListParams = {
        page,
        page_size: pageSize,
        status: 'active',
        sort,
      }
      const response = await getItems(params)
      setItems(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="items-list-page">
      <header className="page-header">
        <h1>商品列表</h1>
        <div className="sort-controls">
          <label>
            排序：
            <select 
              value={sort} 
              onChange={(e) => setSort(e.target.value as ItemsListParams['sort'])}
            >
              <option value="last_seen_desc">最新</option>
              <option value="price_asc">价格从低到高</option>
              <option value="price_desc">价格从高到低</option>
            </select>
          </label>
        </div>
      </header>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <LoadingSkeleton />
      ) : items.length === 0 ? (
        <div className="empty-message">暂无商品</div>
      ) : (
        <>
          <div className="items-grid">
            {items.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
          <PaginationBar
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  )
}

