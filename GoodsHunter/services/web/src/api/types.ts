/** API 类型定义 */

export interface ItemListItem {
  id: number
  brand_name: string | null
  model_name: string | null
  model_no: string | null
  currency: string
  price: number | null
  image_thumb_url: string | null
  last_seen_dt: string
  status: string
}

export interface ItemDetail {
  id: number
  source_uid: string
  site: string
  category: string
  item_id: string
  brand_name: string | null
  model_name: string | null
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
  sort?: 'last_seen_desc' | 'price_asc' | 'price_desc'
}

