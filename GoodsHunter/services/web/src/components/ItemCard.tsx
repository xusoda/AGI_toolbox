import { useNavigate } from 'react-router-dom'
import type { ItemListItem } from '../api/types'
import './ItemCard.css'

interface ItemCardProps {
  item: ItemListItem
}

export default function ItemCard({ item }: ItemCardProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/items/${item.id}`)
  }

  const formatPrice = () => {
    if (!item.price) return '价格未定'
    return `${item.currency} ${item.price.toLocaleString()}`
  }

  return (
    <div className="item-card" onClick={handleClick}>
      <div className="item-card-image">
        {item.image_thumb_url ? (
          <img 
            src={item.image_thumb_url} 
            alt={item.model_name || '商品图片'}
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        ) : (
          <div className="item-card-placeholder">暂无图片</div>
        )}
      </div>
      <div className="item-card-info">
        {item.brand_name && (
          <div className="item-card-brand">{item.brand_name}</div>
        )}
        {item.model_name && (
          <div className="item-card-model">{item.model_name}</div>
        )}
        {item.model_no && (
          <div className="item-card-model-no">{item.model_no}</div>
        )}
        <div className="item-card-price">{formatPrice()}</div>
      </div>
    </div>
  )
}

