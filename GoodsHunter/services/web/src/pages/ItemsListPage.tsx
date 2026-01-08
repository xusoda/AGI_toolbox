import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'
import { getItems } from '../api/items'
import { searchProducts } from '../api/search'
import type { ItemListItem, ItemsListParams, SearchParams, SearchItemResult } from '../api/types'
import ItemCard from '../components/ItemCard'
import PaginationBar from '../components/PaginationBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import SearchBar from '../components/SearchBar'
import { CategorySelector } from '../components/CategorySelector'
import './ItemsListPage.css'

export default function ItemsListPage() {
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const [items, setItems] = useState<ItemListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [sort, setSort] = useState<ItemsListParams['sort']>('last_seen_desc')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [sortField, setSortField] = useState<'price' | 'last_seen_dt' | 'created_at'>('last_seen_dt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // 从 URL 参数获取 category 和 page
  const searchParams = new URLSearchParams(location.search)
  const category = searchParams.get('category') || undefined

  useEffect(() => {
    // 从 URL 参数更新 page
    const urlPage = parseInt(new URLSearchParams(location.search).get('page') || '1')
    if (urlPage !== page && urlPage > 0) {
      setPage(urlPage)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search])

  useEffect(() => {
    if (isSearchMode && searchQuery) {
      loadSearchResults()
    } else {
      loadItems()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sort, i18n.language, isSearchMode, searchQuery, sortField, sortOrder, category])

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
        category,  // 传递 category
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

  const loadSearchResults = async () => {
    if (!searchQuery.trim()) {
      setIsSearchMode(false)
      loadItems()
      return
    }

    setLoading(true)
    setError(null)
    try {
      const params: SearchParams = {
        q: searchQuery,
        page,
        page_size: pageSize,
        sort_field: sortField,
        sort_order: sortOrder,
        status: 'active',
        lang: i18n.language,
        category,  // 传递 category
      }
      const response = await searchProducts(params)
      
      // 将搜索结果转换为 ItemListItem 格式
      const convertedItems: ItemListItem[] = response.items.map((item: SearchItemResult) => ({
        id: item.id,
        brand_name: item.brand_name,
        brand_name_translated: item.brand_name_translated,
        model_name: item.model_name,
        model_name_translated: item.model_name_translated,
        model_no: item.model_no,
        currency: item.currency,
        price: item.price,
        image_thumb_url: item.image_thumb_url,
        last_seen_dt: item.last_seen_dt || '',
        status: item.status,
        product_id: null,
      }))
      
      setItems(convertedItems)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'))
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setIsSearchMode(query.trim().length > 0)
    setPage(1) // 重置到第一页
  }

  const handleClearSearch = () => {
    setSearchQuery('')
    setIsSearchMode(false)
    setPage(1)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    // 更新 URL 参数
    const newSearchParams = new URLSearchParams(location.search)
    newSearchParams.set('page', newPage.toString())
    window.history.pushState({}, '', `${location.pathname}?${newSearchParams.toString()}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // 根据模式获取排序选项
  const getSortOptions = () => {
    if (isSearchMode) {
      return (
        <>
          <label className="sort-label">
            <span className="sort-label-text">{t('app.sort_by', '排序')}：</span>
            <select 
              value={sortField} 
              onChange={(e) => setSortField(e.target.value as 'price' | 'last_seen_dt' | 'created_at')}
              className="sort-select"
            >
              <option value="last_seen_dt">{t('app.sort_last_seen', '最后发现时间')}</option>
              <option value="price">{t('app.sort_price', '价格')}</option>
              <option value="created_at">{t('app.sort_created', '创建时间')}</option>
            </select>
          </label>
          <label className="sort-label">
            <span className="sort-label-text">{t('app.sort_order', '顺序')}：</span>
            <select 
              value={sortOrder} 
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              className="sort-select"
            >
              <option value="desc">{t('app.sort_desc', '降序')}</option>
              <option value="asc">{t('app.sort_asc', '升序')}</option>
            </select>
          </label>
        </>
      )
    } else {
      return (
        <label className="sort-label">
          <span className="sort-label-text">{t('app.sort_by', '排序')}：</span>
          <select 
            value={sort} 
            onChange={(e) => setSort(e.target.value as ItemsListParams['sort'])}
            className="sort-select"
          >
            <option value="last_seen_desc">{t('app.sort_last_seen_desc', '最后发现时间（降序）')}</option>
            <option value="price_asc">{t('app.sort_price_asc', '价格（升序）')}</option>
            <option value="price_desc">{t('app.sort_price_desc', '价格（降序）')}</option>
          </select>
        </label>
      )
    }
  }

  return (
    <div className="items-list-page">
      <header className="page-header">
        <div className="page-header-top">
          <div className="category-sort-row">
            <div className="category-selector-wrapper">
              <CategorySelector />
            </div>
            <div className="sort-controls">
              {getSortOptions()}
            </div>
          </div>
        </div>
        <div className="header-controls">
          <div className="search-container">
            <SearchBar 
              onSearch={handleSearch} 
              initialQuery={searchQuery}
              onClear={handleClearSearch}
            />
          </div>
        </div>
      </header>

      {isSearchMode && searchQuery && (
        <div className="search-info">
          {t('search.results_for', '搜索结果')}: <strong>"{searchQuery}"</strong> ({total} {t('search.items', '个结果')})
        </div>
      )}

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

