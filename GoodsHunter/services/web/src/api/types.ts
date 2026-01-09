/** API 类型定义 */

export interface ItemListItem {
  id: number
  brand_name: string | null
  brand_name_translated: string | null  // 翻译后的品牌名
  model_name: string | null
  model_name_translated: string | null  // 翻译后的型号名
  model_no: string | null
  currency: string
  price: number | null
  image_thumb_url: string | null
  last_seen_dt: string
  status: string
  product_id: number | null
}

export interface ItemDetail {
  id: number
  source_uid: string
  site: string
  category: string
  item_id: string
  brand_name: string | null
  brand_name_translated: string | null  // 翻译后的品牌名
  model_name: string | null
  model_name_translated: string | null  // 翻译后的型号名
  model_no: string | null
  currency: string
  price: number | null
  image_thumb_url: string | null
  image_600_url: string | null
  image_original_url: string | null
  product_url: string | null
  status: string
  first_seen_dt: string
  last_seen_dt: string
  sold_dt: string | null
  sold_reason: string | null
  last_crawl_time: string
  created_at: string
  updated_at: string
  product_id: number | null
}

export interface ItemsListResponse {
  total: number
  page: number
  page_size: number
  items: ItemListItem[]
}

export interface ItemsListParams {
  page?: number
  page_size?: number
  status?: string
  sort?: 'first_seen_desc' | 'price_asc' | 'price_desc'
  lang?: string  // 语言代码（en/zh/ja）
  category?: string  // 商品类别（watch/bag/jewelry/clothing/camera）
}

// 搜索相关类型
export interface SearchItemResult {
  id: number
  brand_name: string | null
  model_name: string | null
  model_no: string | null
  price: number | null
  currency: string
  site: string
  category: string
  status: string
  last_seen_dt: string | null
  image_thumb_300_key: string | null
  product_url: string | null
  created_at: string | null
  image_thumb_url: string | null
  brand_name_translated: string | null
  model_name_translated: string | null
}

export interface SearchResponse {
  total: number
  page: number
  page_size: number
  items: SearchItemResult[]
}

export interface SuggestResponse {
  suggestions: string[]
}

export interface SearchParams {
  q: string  // 搜索关键词（必需）
  page?: number
  page_size?: number
  sort_field?: 'price' | 'last_seen_dt' | 'created_at'
  sort_order?: 'asc' | 'desc'
  status?: string
  site?: string
  category?: string
  brand_name?: string
  min_price?: number
  max_price?: number
  currency?: string
  lang?: string
}
