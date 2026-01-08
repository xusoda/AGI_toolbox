import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { getItems } from '../api/items'
import type { ItemListItem, ItemsListParams } from '../api/types'
import ItemCard from '../components/ItemCard'
import PaginationBar from '../components/PaginationBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import './ItemsListPage.css'

export default function ItemsListPage() {
  const { i18n, t } = useTranslation()
  const [items, setItems] = useState<ItemListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [sort, setSort] = useState<ItemsListParams['sort']>('last_seen_desc')

  useEffect(() => {
    loadItems()
  }, [page, sort, i18n.language])

  const loadItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: ItemsListParams = {
        page,
        page_size: pageSize,
        status: 'active',
        sort,
        lang: i18n.language,  // 传递当前语言
      }
      const response = await getItems(params)
      setItems(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'))
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
        <h1>{t('app.title')}</h1>
        <div className="sort-controls">
          <label>
            {t('app.sort_by')}：
            <select 
              value={sort} 
              onChange={(e) => setSort(e.target.value as ItemsListParams['sort'])}
            >
              <option value="last_seen_desc">{t('app.sort_last_seen_desc')}</option>
              <option value="price_asc">{t('app.sort_price_asc')}</option>
              <option value="price_desc">{t('app.sort_price_desc')}</option>
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
        <div className="empty-message">{t('app.no_items')}</div>
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

