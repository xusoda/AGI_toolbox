/**
 * URL 状态类型定义
 * 
 * 定义所有可以通过 URL 参数管理的应用状态。
 * 设计为可扩展的，方便后续添加新的筛选和搜索选项。
 */

import { Category } from '@enums/business/category'
import { SortOption, SortField, SortOrder } from '@enums/display/sort'
import { LanguageCode } from '@enums/display/lang'
import { CurrencyCode } from '@enums/trade/currency'

/**
 * URL 状态接口
 * 
 * 包含所有可以通过 URL 参数管理的状态：
 * - 搜索相关：q（搜索关键词）
 * - 筛选相关：category（分类）、status（状态）、site（站点）、brand_name（品牌）
 * - 价格筛选：min_price、max_price、currency
 * - 分页相关：page、page_size
 * - 排序相关：sort（列表模式）、sort_field、sort_order（搜索模式）
 * - 语言相关：lang
 */
export interface URLState {
  // ========== 搜索相关 ==========
  /** 搜索关键词 */
  q?: string

  // ========== 筛选相关 ==========
  /** 商品类别 */
  category?: Category | ''
  /** 商品状态（未来扩展） */
  status?: string
  /** 站点（未来扩展） */
  site?: string
  /** 品牌名称（未来扩展） */
  brand_name?: string

  // ========== 价格筛选（未来扩展） ==========
  /** 最低价格 */
  min_price?: number
  /** 最高价格 */
  max_price?: number
  /** 货币代码 */
  currency?: CurrencyCode

  // ========== 分页相关 ==========
  /** 当前页码 */
  page?: number
  /** 每页数量（通常不暴露在 URL，但保留扩展性） */
  page_size?: number

  // ========== 排序相关 ==========
  /** 列表模式排序选项 */
  sort?: SortOption
  /** 搜索模式排序字段 */
  sort_field?: SortField
  /** 搜索模式排序顺序 */
  sort_order?: SortOrder

  // ========== 语言相关 ==========
  /** 语言代码 */
  lang?: LanguageCode
}

/**
 * URL 状态更新选项
 */
export interface URLStateUpdateOptions {
  /** 是否替换当前历史记录条目（而不是添加新条目） */
  replace?: boolean
  /** 是否重置页码到第一页（当筛选条件变更时） */
  resetPage?: boolean
}

/**
 * URL 参数键名映射
 * 
 * 定义 URL 参数名与状态属性的映射关系
 */
export const URL_PARAM_KEYS = {
  Q: 'q',
  CATEGORY: 'category',
  STATUS: 'status',
  SITE: 'site',
  BRAND_NAME: 'brand_name',
  MIN_PRICE: 'min_price',
  MAX_PRICE: 'max_price',
  CURRENCY: 'currency',
  PAGE: 'page',
  PAGE_SIZE: 'page_size',
  SORT: 'sort',
  SORT_FIELD: 'sort_field',
  SORT_ORDER: 'sort_order',
  LANG: 'lang',
} as const
