/** 搜索 API 客户端 */
import request from './http'
import type { SearchResponse, SuggestResponse, SearchParams } from './types'

export async function searchProducts(params: SearchParams): Promise<SearchResponse> {
  const searchParams = new URLSearchParams()
  
  // 必需参数
  searchParams.append('q', params.q)
  
  // 可选参数
  if (params.page) searchParams.append('page', params.page.toString())
  if (params.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params.sort_field) searchParams.append('sort_field', params.sort_field)
  if (params.sort_order) searchParams.append('sort_order', params.sort_order)
  if (params.status) searchParams.append('status', params.status)
  if (params.site) searchParams.append('site', params.site)
  if (params.category) searchParams.append('category', params.category)
  if (params.brand_name) searchParams.append('brand_name', params.brand_name)
  if (params.min_price !== undefined) searchParams.append('min_price', params.min_price.toString())
  if (params.max_price !== undefined) searchParams.append('max_price', params.max_price.toString())
  if (params.currency) searchParams.append('currency', params.currency)
  if (params.lang) searchParams.append('lang', params.lang)
  
  const query = searchParams.toString()
  const endpoint = `/search?${query}`
  
  return request<SearchResponse>(endpoint)
}

export async function getSearchSuggestions(query: string, size: number = 5): Promise<SuggestResponse> {
  const searchParams = new URLSearchParams()
  searchParams.append('q', query)
  searchParams.append('size', size.toString())
  
  const endpoint = `/search/suggest?${searchParams.toString()}`
  
  return request<SuggestResponse>(endpoint)
}
