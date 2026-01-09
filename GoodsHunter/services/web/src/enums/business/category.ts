/**
 * 商品类别枚举
 * 
 * 用于标识商品的类别，如手表、珠宝、箱包等。
 * 这个枚举值在抓取配置（profile）和筛选展示时都会使用。
 */
export enum Category {
  WATCH = 'watch',        // 手表
  BAG = 'bag',            // 箱包
  JEWELRY = 'jewelry',    // 珠宝/首饰
  CLOTHING = 'clothing',  // 衣服
  CAMERA = 'camera',      // 相机
}

/**
 * 所有类别值列表
 */
export const CATEGORY_VALUES: Category[] = Object.values(Category) as Category[]

/**
 * 检查值是否为有效的类别
 */
export function isValidCategory(value: string | null | undefined): value is Category {
  if (!value) return false
  return CATEGORY_VALUES.includes(value as Category)
}

/**
 * 获取默认类别
 */
export function getDefaultCategory(): Category {
  return Category.WATCH
}

/**
 * 类别类型（包含空字符串，用于"全部"选项）
 */
export type CategoryOrAll = Category | ''
