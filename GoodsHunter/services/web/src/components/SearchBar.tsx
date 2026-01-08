import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { getSearchSuggestions } from '../api/search'
import './SearchBar.css'

interface SearchBarProps {
  onSearch: (query: string) => void
  initialQuery?: string
  onClear?: () => void
}

export default function SearchBar({ onSearch, initialQuery = '', onClear }: SearchBarProps) {
  const { t } = useTranslation()
  const [query, setQuery] = useState(initialQuery)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // 同步外部 initialQuery 的变化
  useEffect(() => {
    setQuery(initialQuery)
  }, [initialQuery])

  // 点击外部关闭建议列表
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // 获取搜索建议
  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    // 防抖处理
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    setLoading(true)
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await getSearchSuggestions(query.trim(), 5)
        setSuggestions(response.suggestions)
        setShowSuggestions(response.suggestions.length > 0)
      } catch (error) {
        console.error('获取搜索建议失败:', error)
        setSuggestions([])
        setShowSuggestions(false)
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [query])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
      setShowSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    onSearch(suggestion)
    setShowSuggestions(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const handleInputFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true)
    }
  }

  const handleClear = () => {
    setQuery('')
    setSuggestions([])
    setShowSuggestions(false)
    onSearch('')
    if (onClear) {
      onClear()
    }
  }

  const showClearButton = query.trim().length > 0

  return (
    <div className="search-bar-container" ref={suggestionsRef}>
      <form className="search-bar" onSubmit={handleSubmit}>
        <div className="search-input-wrapper">
          <input
            type="text"
            className="search-input"
            placeholder={t('search.placeholder', '搜索商品...')}
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
          />
          {showClearButton && (
            <button
              type="button"
              className="search-clear-button"
              onClick={handleClear}
              aria-label={t('search.clear', '清除搜索')}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
        <button type="submit" className="search-button" aria-label={t('search.search', '搜索')}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </button>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}

      {loading && (
        <div className="suggestions-loading">
          {t('search.loading', '加载中...')}
        </div>
      )}
    </div>
  )
}
