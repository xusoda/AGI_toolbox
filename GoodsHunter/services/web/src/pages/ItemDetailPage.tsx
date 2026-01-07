import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getItemById } from '../api/items'
import type { ItemDetail } from '../api/types'
import './ItemDetailPage.css'

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [item, setItem] = useState<ItemDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showOriginal, setShowOriginal] = useState(false)

  useEffect(() => {
    if (id) {
      loadItem(parseInt(id))
    }
  }, [id])

  const loadItem = async (itemId: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getItemById(itemId)
      setItem(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = () => {
    if (!item?.price) return '价格未定'
    return `${item.currency} ${item.price.toLocaleString()}`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  }

  const handleBack = () => {
    navigate(-1)
  }

  const handleOpenProduct = () => {
    if (item?.product_url) {
      window.open(item.product_url, '_blank')
    }
  }

  if (loading) {
    return (
      <div className="item-detail-page">
        <div className="loading">加载中...</div>
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="item-detail-page">
        <div className="error-message">{error || '商品不存在'}</div>
        <button onClick={handleBack} className="back-button">返回</button>
      </div>
    )
  }

  const displayImage = showOriginal && item.image_original_url 
    ? item.image_original_url 
    : (item.image_600_url || item.image_thumb_url)

  return (
    <div className="item-detail-page">
      <header className="detail-header">
        <button onClick={handleBack} className="back-button">← 返回</button>
        <h1>{item.brand_name || '商品详情'}</h1>
      </header>

      <div className="detail-content">
        <div className="detail-image-section">
          {displayImage ? (
            <div className="image-container">
              <img 
                src={displayImage} 
                alt={item.model_name || '商品图片'}
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
              {item.image_original_url && !showOriginal && (
                <button 
                  className="view-original-button"
                  onClick={() => setShowOriginal(true)}
                >
                  查看原图
                </button>
              )}
            </div>
          ) : (
            <div className="image-placeholder">暂无图片</div>
          )}
        </div>

        <div className="detail-info-section">
          <div className="info-group">
            <h2>基本信息</h2>
            <div className="info-item">
              <span className="info-label">品牌：</span>
              <span className="info-value">{item.brand_name || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">型号：</span>
              <span className="info-value">{item.model_name || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">型号编号：</span>
              <span className="info-value">{item.model_no || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">价格：</span>
              <span className="info-value price">{formatPrice()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">状态：</span>
              <span className="info-value status">{item.status === 'active' ? '在售' : '已售'}</span>
            </div>
          </div>

          <div className="info-group">
            <h2>时间信息</h2>
            <div className="info-item">
              <span className="info-label">首次发现：</span>
              <span className="info-value">{formatDate(item.first_seen_dt)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">最后更新：</span>
              <span className="info-value">{formatDate(item.last_seen_dt)}</span>
            </div>
            {item.sold_dt && (
              <div className="info-item">
                <span className="info-label">售出日期：</span>
                <span className="info-value">{formatDate(item.sold_dt)}</span>
              </div>
            )}
          </div>

          {item.product_url && (
            <div className="action-group">
              <button 
                className="product-link-button"
                onClick={handleOpenProduct}
              >
                打开商品页面
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

