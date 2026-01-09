/**
 * 列表页排序选项枚举
 */
export enum SortOption {
  FIRST_SEEN_DESC = 'first_seen_desc',  // 首次发现时间（降序）
  PRICE_ASC = 'price_asc',               // 价格（升序）
  PRICE_DESC = 'price_desc',             // 价格（降序）
}

/**
 * 搜索页排序字段枚举
 */
export enum SortField {
  PRICE = 'price',           // 价格
  LAST_SEEN_DT = 'last_seen_dt',  // 最后发现时间
  CREATED_AT = 'created_at',       // 创建时间
}

/**
 * 排序顺序枚举
 */
export enum SortOrder {
  ASC = 'asc',    // 升序
  DESC = 'desc',  // 降序
}

/**
 * 获取默认排序选项
 */
export function getDefaultSortOption(): SortOption {
  return SortOption.FIRST_SEEN_DESC
}

/**
 * 获取默认排序字段
 */
export function getDefaultSortField(): SortField {
  return SortField.LAST_SEEN_DT
}

/**
 * 获取默认排序顺序
 */
export function getDefaultSortOrder(): SortOrder {
  return SortOrder.DESC
}
