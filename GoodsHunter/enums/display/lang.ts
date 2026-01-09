/**
 * 语言代码枚举
 * 
 * 用于标识系统支持的语言。
 */
export enum LanguageCode {
  EN = 'en',  // 英语
  ZH = 'zh',  // 中文（简体）
  JA = 'ja',  // 日语
}

/**
 * 所有语言代码值列表
 */
export const LANGUAGE_CODE_VALUES: LanguageCode[] = Object.values(LanguageCode) as LanguageCode[]

/**
 * 检查值是否为有效的语言代码
 */
export function isValidLanguageCode(value: string | null | undefined): value is LanguageCode {
  if (!value) return false
  return LANGUAGE_CODE_VALUES.includes(value as LanguageCode)
}

/**
 * 获取默认语言代码
 */
export function getDefaultLanguageCode(): LanguageCode {
  return LanguageCode.EN
}
