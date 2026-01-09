import { useTranslation } from 'react-i18next'
import { useEffect } from 'react'
import { useURLState } from '../hooks/useURLState'
import { LanguageCode } from '@enums/display/lang'
import './LanguageSelector.css'

export function LanguageSelector() {
  const { i18n } = useTranslation()
  const { getValue, setValue } = useURLState()

  // 从 URL 获取语言，如果没有则从 i18n 获取
  const urlLang = getValue('lang')
  const currentLang = (urlLang || i18n.language || 'en') as LanguageCode

  // 同步 URL 语言到 i18n（如果 URL 中有语言参数）
  useEffect(() => {
    if (urlLang && urlLang !== i18n.language) {
      i18n.changeLanguage(urlLang)
      // 同时保存到 localStorage 保持兼容性
      localStorage.setItem('preferred_language', urlLang)
    }
  }, [urlLang, i18n])

  const changeLanguage = (lang: string) => {
    const langCode = lang as LanguageCode
    // 更新 URL
    setValue('lang', langCode, { replace: false })
    // 更新 i18n
    i18n.changeLanguage(langCode)
    // 保存到 localStorage 保持兼容性
    localStorage.setItem('preferred_language', langCode)
  }

  const languages = [
    { value: LanguageCode.EN, label: 'EN' },
    { value: LanguageCode.ZH, label: '中文' },
    { value: LanguageCode.JA, label: '日本語' },
  ]

  return (
    <div className="language-selector">
      <select
        value={currentLang}
        onChange={(e) => changeLanguage(e.target.value)}
        className="language-select"
      >
        {languages.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  )
}

