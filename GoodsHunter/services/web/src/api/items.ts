/** 商品 API 客户端 */
import request from './http'
import type { ItemsListResponse, ItemDetail, ItemsListParams } from './types'

export async function getItems(params: ItemsListParams = {}): Promise<ItemsListResponse> {
  const searchParams = new URLSearchParams()
  
  if (params.page) searchParams.append('page', params.page.toString())
  if (params.page_size) searchParams.append('page_size', params.page_size.toString())
  if (params.status) searchParams.append('status', params.status)
  if (params.sort) searchParams.append('sort', params.sort)
  if (params.lang) searchParams.append('lang', params.lang)
  if (params.category) searchParams.append('category', params.category)
  
  const query = searchParams.toString()
  const endpoint = `/items${query ? `?${query}` : ''}`
  
  return request<ItemsListResponse>(endpoint)
}

export async function getItemById(id: number, lang?: string): Promise<ItemDetail> {
  const searchParams = new URLSearchParams()
  if (lang) searchParams.append('lang', lang)
  const query = searchParams.toString()
  return request<ItemDetail>(`/items/${id}${query ? `?${query}` : ''}`)
}

