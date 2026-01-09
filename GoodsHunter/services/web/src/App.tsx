import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import ItemsListPage from './pages/ItemsListPage'
import ItemDetailPage from './pages/ItemDetailPage'
import { LanguageSelector } from './components/LanguageSelector'
import { isValidLanguageCode } from '@enums/display/lang'

// 内部组件：处理语言初始化（需要在 BrowserRouter 内部）
function AppContent() {
  const { i18n } = useTranslation()
  const [searchParams] = useSearchParams()

  // 优先从 URL 读取语言，如果没有则从 localStorage 恢复
  useEffect(() => {
    const urlLang = searchParams.get('lang')
    if (urlLang && isValidLanguageCode(urlLang)) {
      // URL 中有语言参数，使用它
      i18n.changeLanguage(urlLang)
      localStorage.setItem('preferred_language', urlLang)
    } else {
      // URL 中没有语言参数，从 localStorage 恢复
      const savedLang = localStorage.getItem('preferred_language')
      if (savedLang && isValidLanguageCode(savedLang)) {
        i18n.changeLanguage(savedLang)
      }
    }
  }, [i18n, searchParams])

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-content">
          <h1 className="app-title">GoodsHunter</h1>
          <div className="app-header-language">
            <LanguageSelector />
          </div>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<ItemsListPage />} />
          <Route path="/items/:id" element={<ItemDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App

