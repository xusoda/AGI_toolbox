import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { getItems } from '../api/items'
import { searchProducts } from '../api/search'
import type { ItemListItem, ItemsListParams, SearchParams, SearchItemResult } from '../api/types'
import ItemCard from '../components/ItemCard'
import PaginationBar from '../components/PaginationBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import SearchBar from '../components/SearchBar'
import { CategorySelector } from '../components/CategorySelector'
import { SortOption, SortField, SortOrder, getDefaultSortOption, getDefaultSortField, getDefaultSortOrder } from '@enums/display/sort'
import { getDefaultItemStatus } from '@enums/business/status'
import { useURLState } from '../hooks/useURLState'
import { useDebounce } from '../hooks/useDebounce'
import './ItemsListPage.css'

export default function ItemsListPage() {
  const { i18n, t } = useTranslation()
  const { getState, updateState, setValue } = useURLState()
  const [items, setItems] = useState<ItemListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  // 从 URL 获取所有状态
  const urlState = getState()
  const searchQuery = urlState.q || ''
  const category = urlState.category
  const page = urlState.page || 1
  const sort = urlState.sort || getDefaultSortOption()
  const sortField = urlState.sort_field || getDefaultSortField()
  const sortOrder = urlState.sort_order || getDefaultSortOrder()
  const lang = urlState.lang || (i18n.language as any)

  // 判断是否为搜索模式
  const isSearchMode = useMemo(() => {
    return Boolean(searchQuery && searchQuery.trim().length > 0)
  }, [searchQuery])

  // 防抖更新搜索关键词
  const debouncedUpdateSearch = useDebounce((query: string) => {
    if (query.trim()) {
      updateState({ q: query, page: 1 }, { replace: false })
    } else {
      updateState({ q: undefined, page: 1 }, { replace: false })
    }
  }, 300, [updateState])

  // 当 URL 状态变化时，重新加载数据
  useEffect(() => {
    if (isSearchMode && searchQuery) {
      loadSearchResults()
    } else {
      loadItems()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sort, lang, isSearchMode, searchQuery, sortField, sortOrder, category])

  const loadItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: ItemsListParams = {
        page,
        page_size: pageSize,
        status: getDefaultItemStatus(),
        sort: sort as ItemsListParams['sort'],
        lang: lang,
        // 空字符串表示"全部"，传递 undefined
        category: category && category !== '' ? (category as any) : undefined,
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
        status: getDefaultItemStatus(),
        lang: lang,
        // 空字符串表示"全部"，传递 undefined
        category: category && category !== '' ? (category as any) : undefined,
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
    // 使用防抖更新搜索关键词
    debouncedUpdateSearch(query)
  }

  const handleClearSearch = () => {
    // 立即清除搜索（不使用防抖）
    updateState({ q: undefined, page: 1 }, { replace: false })
  }

  const handlePageChange = (newPage: number) => {
    setValue('page', newPage, { replace: false })
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
              onChange={(e) => setValue('sort_field', e.target.value as SortField, { replace: false })}
              className="sort-select"
            >
              <option value={SortField.LAST_SEEN_DT}>{t('app.sort_last_seen', '最后发现时间')}</option>
              <option value={SortField.PRICE}>{t('app.sort_price', '价格')}</option>
              <option value={SortField.CREATED_AT}>{t('app.sort_created', '创建时间')}</option>
            </select>
          </label>
          <label className="sort-label">
            <span className="sort-label-text">{t('app.sort_order', '顺序')}：</span>
            <select 
              value={sortOrder} 
              onChange={(e) => setValue('sort_order', e.target.value as SortOrder, { replace: false })}
              className="sort-select"
            >
              <option value={SortOrder.DESC}>{t('app.sort_desc', '降序')}</option>
              <option value={SortOrder.ASC}>{t('app.sort_asc', '升序')}</option>
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
            onChange={(e) => setValue('sort', e.target.value as SortOption, { replace: false })}
            className="sort-select"
          >
            <option value={SortOption.FIRST_SEEN_DESC}>{t('app.sort_first_seen_desc', '首次发现时间（降序）')}</option>
            <option value={SortOption.PRICE_ASC}>{t('app.sort_price_asc', '价格（升序）')}</option>
            <option value={SortOption.PRICE_DESC}>{t('app.sort_price_desc', '价格（降序）')}</option>
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

