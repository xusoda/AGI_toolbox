/**
 * 商品状态枚举
 * 
 * 用于标识商品的当前状态。
 */
export enum ItemStatus {
  ACTIVE = 'active',      // 在售
  SOLD = 'sold',          // 已售出
  REMOVED = 'removed',    // 已下架
}

/**
 * 所有状态值列表
 */
export const ITEM_STATUS_VALUES: ItemStatus[] = Object.values(ItemStatus) as ItemStatus[]

/**
 * 检查值是否为有效的状态
 */
export function isValidItemStatus(value: string | null | undefined): value is ItemStatus {
  if (!value) return false
  return ITEM_STATUS_VALUES.includes(value as ItemStatus)
}

/**
 * 获取默认状态
 */
export function getDefaultItemStatus(): ItemStatus {
  return ItemStatus.ACTIVE
}
