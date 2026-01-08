import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import ItemsListPage from './pages/ItemsListPage'
import ItemDetailPage from './pages/ItemDetailPage'
import { LanguageSelector } from './components/LanguageSelector'

function App() {
  const { i18n } = useTranslation()

  // 从 localStorage 恢复用户的语言偏好
  useEffect(() => {
    const savedLang = localStorage.getItem('preferred_language')
    if (savedLang && ['en', 'zh', 'ja'].includes(savedLang)) {
      i18n.changeLanguage(savedLang)
    }
  }, [i18n])

  return (
    <BrowserRouter>
      <div className="app-container">
        <header className="app-header">
          <div className="app-header-content">
            <h1>GoodsHunter</h1>
            <LanguageSelector />
          </div>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<ItemsListPage />} />
            <Route path="/items/:id" element={<ItemDetailPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

