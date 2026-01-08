-- 搜索功能数据库索引初始化脚本
-- 用于为搜索功能添加必要的索引

-- ============================================================================
-- 搜索相关索引（用于全文搜索优化）
-- ============================================================================

-- 为品牌名、型号名、型号编号创建文本索引，优化 ILIKE 查询
-- text_pattern_ops 操作符类支持前缀匹配，适合搜索建议功能
CREATE INDEX IF NOT EXISTS idx_crawler_item_brand_name_text
    ON crawler_item(brand_name text_pattern_ops) WHERE brand_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_crawler_item_model_name_text
    ON crawler_item(model_name text_pattern_ops) WHERE model_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_crawler_item_model_no_text
    ON crawler_item(model_no text_pattern_ops) WHERE model_no IS NOT NULL;

-- 组合索引用于搜索建议（SUG）
CREATE INDEX IF NOT EXISTS idx_crawler_item_search_suggest
    ON crawler_item(brand_name, model_name, model_no) 
    WHERE brand_name IS NOT NULL OR model_name IS NOT NULL OR model_no IS NOT NULL;

-- 添加注释
COMMENT ON INDEX idx_crawler_item_brand_name_text IS '品牌名文本索引，用于优化搜索和搜索建议';
COMMENT ON INDEX idx_crawler_item_model_name_text IS '型号名文本索引，用于优化搜索和搜索建议';
COMMENT ON INDEX idx_crawler_item_model_no_text IS '型号编号文本索引，用于优化搜索和搜索建议';
COMMENT ON INDEX idx_crawler_item_search_suggest IS '搜索建议组合索引，用于优化搜索建议查询';
