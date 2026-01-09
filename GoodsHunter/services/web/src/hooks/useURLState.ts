/**
 * URL 状态管理 Hook
 * 
 * 基于 React Router 的 useSearchParams 实现统一的 URL 状态管理。
 * 提供类型安全的状态访问和更新方法，支持深层链接和浏览器历史记录。
 */

import { useSearchParams } from 'react-router-dom'
import { useMemo, useCallback } from 'react'
import type { URLState, URLStateUpdateOptions } from '../types/urlState'
import { SortOption, SortField, SortOrder } from '@enums/display/sort'
import { isValidCategory } from '@enums/business/category'
import { isValidLanguageCode } from '@enums/display/lang'
import { URL_PARAM_KEYS } from '../types/urlState'

/**
 * URL 状态管理 Hook 返回值
 */
export interface UseURLStateReturn {
  /** 获取当前 URL 状态（已解析和验证） */
  getState: () => URLState
  /** 更新 URL 状态 */
  updateState: (updates: Partial<URLState>, options?: URLStateUpdateOptions) => void
  /** 获取单个状态值 */
  getValue: <K extends keyof URLState>(key: K) => URLState[K]
  /** 设置单个状态值 */
  setValue: <K extends keyof URLState>(key: K, value: URLState[K], options?: URLStateUpdateOptions) => void
  /** 清除所有状态（重置到默认值） */
  clearState: (options?: URLStateUpdateOptions) => void
  /** 原始 searchParams 对象（用于特殊场景） */
  searchParams: URLSearchParams
}

/**
 * URL 状态管理 Hook
 */
export function useURLState(): UseURLStateReturn {
  const [searchParams, setSearchParams] = useSearchParams()

  const parseState = useCallback((): URLState => {
    const state: URLState = {}

    const q = searchParams.get(URL_PARAM_KEYS.Q)
    if (q) state.q = decodeURIComponent(q)

    const category = searchParams.get(URL_PARAM_KEYS.CATEGORY)
    if (category !== null) {
      if (category === '') {
        state.category = ''
      } else if (isValidCategory(category)) {
        state.category = category
      }
    }

    const status = searchParams.get(URL_PARAM_KEYS.STATUS)
    if (status) state.status = status

    const site = searchParams.get(URL_PARAM_KEYS.SITE)
    if (site) state.site = site

    const brandName = searchParams.get(URL_PARAM_KEYS.BRAND_NAME)
    if (brandName) state.brand_name = decodeURIComponent(brandName)

    const minPrice = searchParams.get(URL_PARAM_KEYS.MIN_PRICE)
    if (minPrice) {
      const parsed = parseInt(minPrice, 10)
      if (!isNaN(parsed)) state.min_price = parsed
    }

    const maxPrice = searchParams.get(URL_PARAM_KEYS.MAX_PRICE)
    if (maxPrice) {
      const parsed = parseInt(maxPrice, 10)
      if (!isNaN(parsed)) state.max_price = parsed
    }

    const currency = searchParams.get(URL_PARAM_KEYS.CURRENCY)
    if (currency) state.currency = currency as any

    const page = searchParams.get(URL_PARAM_KEYS.PAGE)
    if (page) {
      const parsed = parseInt(page, 10)
      if (!isNaN(parsed) && parsed > 0) state.page = parsed
    }

    const pageSize = searchParams.get(URL_PARAM_KEYS.PAGE_SIZE)
    if (pageSize) {
      const parsed = parseInt(pageSize, 10)
      if (!isNaN(parsed) && parsed > 0) state.page_size = parsed
    }

    const sort = searchParams.get(URL_PARAM_KEYS.SORT)
    if (sort && Object.values(SortOption).includes(sort as SortOption)) {
      state.sort = sort as SortOption
    }

    const sortField = searchParams.get(URL_PARAM_KEYS.SORT_FIELD)
    if (sortField && Object.values(SortField).includes(sortField as SortField)) {
      state.sort_field = sortField as SortField
    }

    const sortOrder = searchParams.get(URL_PARAM_KEYS.SORT_ORDER)
    if (sortOrder && Object.values(SortOrder).includes(sortOrder as SortOrder)) {
      state.sort_order = sortOrder as SortOrder
    }

    const lang = searchParams.get(URL_PARAM_KEYS.LANG)
    if (lang && isValidLanguageCode(lang)) {
      state.lang = lang
    }

    return state
  }, [searchParams])

  const getState = useCallback((): URLState => {
    return parseState()
  }, [parseState])

  const updateState = useCallback(
    (updates: Partial<URLState>, options?: URLStateUpdateOptions) => {
      const newParams = new URLSearchParams(searchParams)

      if (options?.resetPage) {
        newParams.set(URL_PARAM_KEYS.PAGE, '1')
      }

      const keyToParamMap: Record<keyof URLState, string> = {
        q: URL_PARAM_KEYS.Q,
        category: URL_PARAM_KEYS.CATEGORY,
        status: URL_PARAM_KEYS.STATUS,
        site: URL_PARAM_KEYS.SITE,
        brand_name: URL_PARAM_KEYS.BRAND_NAME,
        min_price: URL_PARAM_KEYS.MIN_PRICE,
        max_price: URL_PARAM_KEYS.MAX_PRICE,
        currency: URL_PARAM_KEYS.CURRENCY,
        page: URL_PARAM_KEYS.PAGE,
        page_size: URL_PARAM_KEYS.PAGE_SIZE,
        sort: URL_PARAM_KEYS.SORT,
        sort_field: URL_PARAM_KEYS.SORT_FIELD,
        sort_order: URL_PARAM_KEYS.SORT_ORDER,
        lang: URL_PARAM_KEYS.LANG,
      }

      Object.entries(updates).forEach(([key, value]) => {
        const urlKey = keyToParamMap[key as keyof URLState] || key

        if (value === undefined || value === null) {
          newParams.delete(urlKey)
        } else if (value === '' && key === 'category') {
          newParams.set(urlKey, '')
        } else if (typeof value === 'string') {
          newParams.set(urlKey, encodeURIComponent(value))
        } else {
          newParams.set(urlKey, String(value))
        }
      })

      setSearchParams(newParams, { replace: options?.replace ?? false })
    },
    [searchParams, setSearchParams]
  )

  const getValue = useCallback(
    <K extends keyof URLState>(key: K): URLState[K] => {
      const state = getState()
      return state[key]
    },
    [getState]
  )

  const setValue = useCallback(
    <K extends keyof URLState>(key: K, value: URLState[K], options?: URLStateUpdateOptions) => {
      updateState({ [key]: value } as Partial<URLState>, options)
    },
    [updateState]
  )

  const clearState = useCallback(
    (options?: URLStateUpdateOptions) => {
      setSearchParams(new URLSearchParams(), { replace: options?.replace ?? false })
    },
    [setSearchParams]
  )

  return useMemo(
    () => ({
      getState,
      updateState,
      getValue,
      setValue,
      clearState,
      searchParams,
    }),
    [getState, updateState, getValue, setValue, clearState, searchParams]
  )
}
