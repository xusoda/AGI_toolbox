import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getItemById } from '../api/items'
import type { ItemDetail } from '../api/types'
import './ItemDetailPage.css'

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { i18n, t } = useTranslation()
  const tRef = useRef(t)
  tRef.current = t // 始终保持最新的 t 函数
  
  const [item, setItem] = useState<ItemDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showOriginal, setShowOriginal] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    if (!id) {
      setLoading(false)
      setError(tRef.current('app.no_items'))
      setItem(null)
      return
    }

    const itemId = parseInt(id)
    if (isNaN(itemId)) {
      setLoading(false)
      setError(tRef.current('app.error') + ': 无效的商品ID')
      setItem(null)
      return
    }

    let isCancelled = false
    
    const loadItem = async () => {
      setLoading(true)
      setError(null)
      
      // 设置超时，确保 loading 状态不会一直显示
      const timeoutId = setTimeout(() => {
        if (!isCancelled) {
          setLoading(false)
          setError(tRef.current('app.error') + ': 请求超时，请稍后重试')
        }
      }, 30000) // 30 秒超时
      
      try {
        const data = await getItemById(itemId, i18n.language)
        
        if (isCancelled) {
          clearTimeout(timeoutId)
          return
        }
        
        clearTimeout(timeoutId)
        
        // 确保数据有效
        if (data && data.id) {
          setItem(data)
          setLoading(false)
          setError(null)
        } else {
          setLoading(false)
          setError(tRef.current('app.error') + ': 无效的商品数据')
          setItem(null)
        }
      } catch (err) {
        if (isCancelled) {
          clearTimeout(timeoutId)
          return
        }
        
        clearTimeout(timeoutId)
        const errorMessage = err instanceof Error ? err.message : tRef.current('app.error')
        setError(errorMessage)
        setLoading(false)
        setItem(null)
      }
    }

    loadItem()

    // 清理函数
    return () => {
      isCancelled = true
    }
  }, [id, i18n.language])

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

  // 当 item 加载完成时，重置图片加载状态
  // 注意：这个 useEffect 必须在所有条件返回之前，遵守 React Hooks 规则
  useEffect(() => {
    if (item && item.id) {
      setImageLoading(true)
      setImageError(false)
    }
  }, [item?.id])

  const handleImageLoad = () => {
    setImageLoading(false)
    setImageError(false)
  }

  const handleImageError = () => {
    setImageLoading(false)
    setImageError(true)
  }

  const handleToggleImage = () => {
    setImageLoading(true)
    setImageError(false)
    setShowOriginal(!showOriginal)
  }

  // 条件返回必须在所有 Hooks 之后
  if (loading) {
    return (
      <div className="item-detail-page">
        <div className="loading">{t('app.loading')}</div>
      </div>
    )
  }

  if (!item) {
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
              {imageLoading && (
                <div className="image-loading-overlay">
                  <div className="image-loading-text">{t('app.loading')}</div>
                </div>
              )}
              {imageError ? (
                <div className="image-error-placeholder">
                  <div className="image-error-text">{t('app.error')}: {t('app.image_load_failed')}</div>
                  {item.image_original_url && showOriginal && (
                    <button 
                      className="back-to-thumbnail-button"
                      onClick={() => {
                        setShowOriginal(false)
                        setImageError(false)
                      }}
                    >
                      {t('app.back_to_thumbnail')}
                    </button>
                  )}
                </div>
              ) : (
                <img 
                  src={displayImage} 
                  alt={item.model_name || '商品图片'}
                  onLoad={handleImageLoad}
                  onError={handleImageError}
                  style={{ display: imageLoading ? 'none' : 'block' }}
                />
              )}
              {!imageError && item.image_original_url && (
                <button 
                  className="view-original-button"
                  onClick={handleToggleImage}
                >
                  {showOriginal ? t('app.back_to_thumbnail') : t('app.view_original_image')}
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

