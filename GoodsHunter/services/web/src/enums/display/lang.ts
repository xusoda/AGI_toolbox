/**
 * 语言代码枚举
 */
export enum LanguageCode {
  EN = 'en',
  ZH = 'zh',
  JA = 'ja',
}

/**
 * 所有语言代码列表
 */
export const LANGUAGE_VALUES: LanguageCode[] = Object.values(LanguageCode) as LanguageCode[]

/**
 * 检查值是否为有效的语言代码
 */
export function isValidLanguageCode(value: string | null | undefined): value is LanguageCode {
  if (!value) return false
  return LANGUAGE_VALUES.includes(value as LanguageCode)
}

/**
 * 获取默认语言代码
 */
export function getDefaultLanguageCode(): LanguageCode {
  return LanguageCode.EN
}
