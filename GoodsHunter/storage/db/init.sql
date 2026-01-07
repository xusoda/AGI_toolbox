-- GoodsHunter 数据库初始化脚本
-- 创建 crawler_log 表

-- 如果表已存在则删除（用于开发环境重置）
DROP TABLE IF EXISTS crawler_log CASCADE;

-- 创建 crawler_log 表
CREATE TABLE crawler_log (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    site TEXT NOT NULL,
    item_id TEXT NOT NULL,
    raw_json JSONB NOT NULL,
    brand_name TEXT NULL,
    model_name TEXT NULL,
    model_no TEXT NULL,
    currency TEXT NOT NULL DEFAULT 'JPY',
    price INTEGER NULL,
    image_original_key TEXT NULL,
    image_thumb_300_key TEXT NULL,
    image_thumb_600_key TEXT NULL,
    image_sha256 TEXT NULL,
    crawl_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    dt DATE NOT NULL DEFAULT CURRENT_DATE
);

-- 创建索引
CREATE INDEX idx_crawler_log_site ON crawler_log(site);
CREATE INDEX idx_crawler_log_item_id ON crawler_log(item_id);
CREATE INDEX idx_crawler_log_category ON crawler_log(category);
CREATE INDEX idx_crawler_log_brand_name ON crawler_log(brand_name);
CREATE INDEX idx_crawler_log_model_name ON crawler_log(model_name);
CREATE INDEX idx_crawler_log_model_no ON crawler_log(model_no);
CREATE INDEX idx_crawler_log_price ON crawler_log(price);
CREATE INDEX idx_crawler_log_crawl_time ON crawler_log(crawl_time DESC);
CREATE INDEX idx_crawler_log_dt ON crawler_log(dt);
CREATE INDEX idx_crawler_log_image_sha256 ON crawler_log(image_sha256);

-- 创建组合索引
CREATE INDEX idx_crawler_log_site_item_id ON crawler_log(site, item_id);
CREATE INDEX idx_crawler_log_brand_model ON crawler_log(brand_name, model_name);

-- 添加注释
COMMENT ON TABLE crawler_log IS '原始抓取记录表';
COMMENT ON COLUMN crawler_log.id IS '数据库自增ID';
COMMENT ON COLUMN crawler_log.category IS '商品类别（珠宝/手表/包/服饰/...）';
COMMENT ON COLUMN crawler_log.site IS '主域名，如 commit-watch.co.jp';
COMMENT ON COLUMN crawler_log.item_id IS '在对方网站上，item对应的id';
COMMENT ON COLUMN crawler_log.raw_json IS '原始数据（结构化原文）';
COMMENT ON COLUMN crawler_log.brand_name IS '品牌名称';
COMMENT ON COLUMN crawler_log.model_name IS '型号名称';
COMMENT ON COLUMN crawler_log.model_no IS '型号编号';
COMMENT ON COLUMN crawler_log.currency IS '货币单位，默认JPY';
COMMENT ON COLUMN crawler_log.price IS '价格（整数，*100避免小数）';
COMMENT ON COLUMN crawler_log.image_original_key IS 'MinIO原图key';
COMMENT ON COLUMN crawler_log.image_thumb_300_key IS 'MinIO 300px缩略图key';
COMMENT ON COLUMN crawler_log.image_thumb_600_key IS 'MinIO 600px缩略图key';
COMMENT ON COLUMN crawler_log.image_sha256 IS '图片SHA256哈希值（用于去重）';
COMMENT ON COLUMN crawler_log.crawl_time IS '抓取时间（精确时刻）';
COMMENT ON COLUMN crawler_log.dt IS '分区键（按天）';

