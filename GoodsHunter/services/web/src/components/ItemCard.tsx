import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { ItemListItem } from '../api/types'
import './ItemCard.css'

interface ItemCardProps {
  item: ItemListItem
}

export default function ItemCard({ item }: ItemCardProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const handleClick = () => {
    navigate(`/items/${item.id}`)
  }

  const formatPrice = () => {
    if (!item.price) return t('item.price') + ': ' + t('app.loading')
    const currencySymbol = t(`currency.${item.currency}`) || item.currency
    return `${currencySymbol} ${item.price.toLocaleString()}`
  }

  // 使用翻译后的名称，如果没有则使用原始名称
  const displayBrand = item.brand_name_translated || item.brand_name
  const displayModel = item.model_name_translated || item.model_name

  return (
    <div className="item-card" onClick={handleClick}>
      <div className="item-card-image">
        {item.image_thumb_url ? (
          <img 
            src={item.image_thumb_url} 
            alt={displayModel || t('item.model')}
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        ) : (
          <div className="item-card-placeholder">{t('app.loading')}</div>
        )}
      </div>
      <div className="item-card-info">
        {displayBrand && (
          <div className="item-card-brand">{displayBrand}</div>
        )}
        {displayModel && (
          <div className="item-card-model">{displayModel}</div>
        )}
        {item.model_no && (
          <div className="item-card-model-no">{item.model_no}</div>
        )}
        <div className="item-card-price">{formatPrice()}</div>
      </div>
    </div>
  )
}

