import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import './CategorySelector.css'

export type Category = 'watch' | 'bag' | 'jewelry' | 'clothing' | 'camera' | ''

export function CategorySelector() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  // 从 URL 参数获取当前 category
  const searchParams = new URLSearchParams(location.search)
  const currentCategory = (searchParams.get('category') || '') as Category

  const categories: { value: Category; labelKey: string }[] = [
    { value: '', labelKey: 'category.all' },
    { value: 'watch', labelKey: 'category.watch' },
    { value: 'bag', labelKey: 'category.bag' },
    { value: 'jewelry', labelKey: 'category.jewelry' },
    { value: 'clothing', labelKey: 'category.clothing' },
    { value: 'camera', labelKey: 'category.camera' },
  ]

  const handleCategoryChange = (category: Category) => {
    const newSearchParams = new URLSearchParams(location.search)
    if (category) {
      newSearchParams.set('category', category)
    } else {
      newSearchParams.delete('category')
    }
    // 重置到第一页
    newSearchParams.set('page', '1')
    navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true })
  }

  return (
    <div className="category-selector">
      <select
        value={currentCategory}
        onChange={(e) => handleCategoryChange(e.target.value as Category)}
        className="category-select"
      >
        {categories.map((cat) => (
          <option key={cat.value} value={cat.value}>
            {t(cat.labelKey)}
          </option>
        ))}
      </select>
    </div>
  )
}
