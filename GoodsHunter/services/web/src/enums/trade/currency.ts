/**
 * 货币代码枚举
 * 
 * 用于标识商品价格的货币单位。
 */
export enum CurrencyCode {
  JPY = 'JPY',  // 日元
  USD = 'USD',  // 美元
  CNY = 'CNY',  // 人民币
}

/**
 * 所有货币代码值列表
 */
export const CURRENCY_CODE_VALUES: CurrencyCode[] = Object.values(CurrencyCode) as CurrencyCode[]

/**
 * 检查值是否为有效的货币代码
 */
export function isValidCurrencyCode(value: string | null | undefined): value is CurrencyCode {
  if (!value) return false
  return CURRENCY_CODE_VALUES.includes(value as CurrencyCode)
}

/**
 * 获取默认货币代码
 */
export function getDefaultCurrencyCode(): CurrencyCode {
  return CurrencyCode.JPY
}
