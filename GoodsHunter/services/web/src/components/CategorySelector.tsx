import { useTranslation } from 'react-i18next'
import { CategoryOrAll, CATEGORY_VALUES } from '@enums/business/category'
import { useURLState } from '../hooks/useURLState'
import './CategorySelector.css'

export function CategorySelector() {
  const { t } = useTranslation()
  const { getValue, setValue } = useURLState()

  // 从 URL 获取当前 category
  const category = getValue('category')
  const currentCategory: CategoryOrAll = category || ''

  const categories: { value: CategoryOrAll; labelKey: string }[] = [
    { value: '', labelKey: 'category.all' },
    ...CATEGORY_VALUES.map((cat) => ({
      value: cat as CategoryOrAll,
      labelKey: `category.${cat}` as const,
    })),
  ]

  const handleCategoryChange = (category: CategoryOrAll) => {
    // 使用 useURLState 更新，自动重置页码
    setValue('category', category || undefined, { resetPage: true, replace: false })
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
