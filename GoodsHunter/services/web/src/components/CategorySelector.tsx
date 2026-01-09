import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import { Category, CategoryOrAll, CATEGORY_VALUES, isValidCategory } from '@enums/business/category'
import './CategorySelector.css'

export function CategorySelector() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  // 从 URL 参数获取当前 category
  const searchParams = new URLSearchParams(location.search)
  const categoryParam = searchParams.get('category') || ''
  const currentCategory: CategoryOrAll = isValidCategory(categoryParam) ? categoryParam : ''

  const categories: { value: CategoryOrAll; labelKey: string }[] = [
    { value: '', labelKey: 'category.all' },
    ...CATEGORY_VALUES.map(cat => ({
      value: cat as CategoryOrAll,
      labelKey: `category.${cat}` as const,
    })),
  ]

  const handleCategoryChange = (category: CategoryOrAll) => {
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
        onChange={(e) => handleCategoryChange(e.target.value as CategoryOrAll)}
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
