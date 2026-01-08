import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getItemById } from '../api/items'
import type { ItemDetail } from '../api/types'
import './ItemDetailPage.css'

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { i18n, t } = useTranslation()
  const [item, setItem] = useState<ItemDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showOriginal, setShowOriginal] = useState(false)

  useEffect(() => {
    if (id) {
      loadItem(parseInt(id))
    }
  }, [id, i18n.language])

  const loadItem = async (itemId: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getItemById(itemId, i18n.language)
      setItem(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'))
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = () => {
    if (!item?.price) return t('item.price') + ': ' + t('app.loading')
    const currencySymbol = t(`currency.${item.currency}`) || item.currency
    return `${currencySymbol} ${item.price.toLocaleString()}`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : i18n.language === 'ja' ? 'ja-JP' : 'en-US')
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
        <div className="loading">{t('app.loading')}</div>
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="item-detail-page">
        <div className="error-message">{error || t('app.no_items')}</div>
        <button onClick={handleBack} className="back-button">{t('app.back_to_list')}</button>
      </div>
    )
  }

  const displayImage = showOriginal && item.image_original_url 
    ? item.image_original_url 
    : (item.image_600_url || item.image_thumb_url)

  // 使用翻译后的名称，如果没有则使用原始名称
  const displayBrand = item.brand_name_translated || item.brand_name
  const displayModel = item.model_name_translated || item.model_name

  return (
    <div className="item-detail-page">
      <header className="detail-header">
        <button onClick={handleBack} className="back-button">← {t('app.back_to_list')}</button>
        <h1>{displayBrand || t('app.title')}</h1>
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
                  {t('app.loading')}
                </button>
              )}
            </div>
          ) : (
            <div className="image-placeholder">{t('app.loading')}</div>
          )}
        </div>

        <div className="detail-info-section">
          <div className="info-group">
            <h2>{t('item.brand')}</h2>
            <div className="info-item">
              <span className="info-label">{t('item.brand')}：</span>
              <span className="info-value">{displayBrand || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">{t('item.model')}：</span>
              <span className="info-value">{displayModel || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">{t('item.model_no')}：</span>
              <span className="info-value">{item.model_no || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">{t('item.price')}：</span>
              <span className="info-value price">{formatPrice()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">{t('item.status')}：</span>
              <span className="info-value status">
                {item.status === 'active' ? t('app.active') : item.status === 'sold' ? t('app.sold') : t('app.removed')}
              </span>
            </div>
          </div>

          <div className="info-group">
            <h2>{t('item.last_seen')}</h2>
            <div className="info-item">
              <span className="info-label">{t('item.first_seen')}：</span>
              <span className="info-value">{formatDate(item.first_seen_dt)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">{t('item.last_seen')}：</span>
              <span className="info-value">{formatDate(item.last_seen_dt)}</span>
            </div>
            {item.sold_dt && (
              <div className="info-item">
                <span className="info-label">{t('item.sold_date')}：</span>
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
                {t('app.visit_product_page')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

