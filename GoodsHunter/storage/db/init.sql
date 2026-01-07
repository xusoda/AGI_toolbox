-- GoodsHunter 数据库初始化脚本
-- 统一管理所有表结构

-- ============================================================================
-- 1. crawler_log 表（原始抓取记录表）
-- ============================================================================

-- 如果表已存在则删除（用于开发环境重置）
-- DROP TABLE IF EXISTS crawler_log CASCADE;

-- 创建 crawler_log 表
CREATE TABLE IF NOT EXISTS crawler_log (
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
    source_uid TEXT NOT NULL,
    raw_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'success',
    error TEXT NULL,
    http_status INT NULL,
    fetch_url TEXT NULL,
    run_id BIGINT NULL,
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
CREATE INDEX idx_crawler_log_source_uid ON crawler_log(source_uid);
CREATE INDEX idx_crawler_log_raw_hash ON crawler_log(raw_hash);
CREATE INDEX idx_crawler_log_status ON crawler_log(status);
CREATE INDEX idx_crawler_log_run_id ON crawler_log(run_id);

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
COMMENT ON COLUMN crawler_log.source_uid IS '幂等去重键：{site}:{item_id}';
COMMENT ON COLUMN crawler_log.raw_hash IS 'raw_json的SHA256哈希值（用于判断内容是否变化）';
COMMENT ON COLUMN crawler_log.status IS '抓取状态：success/failed';
COMMENT ON COLUMN crawler_log.error IS '失败原因（如果status为failed）';
COMMENT ON COLUMN crawler_log.http_status IS 'HTTP状态码';
COMMENT ON COLUMN crawler_log.fetch_url IS '实际抓取的URL';
COMMENT ON COLUMN crawler_log.run_id IS '关联一次crawl run（用于任务调度）';
COMMENT ON COLUMN crawler_log.crawl_time IS '抓取时间（精确时刻）';
COMMENT ON COLUMN crawler_log.dt IS '分区键（按天）';

-- ============================================================================
-- 2. pipeline_state 表（流水线状态表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_state_updated_at 
    ON pipeline_state(updated_at);

COMMENT ON TABLE pipeline_state IS '流水线状态表，用于存储处理进度等状态信息';
COMMENT ON COLUMN pipeline_state.key IS '状态键';
COMMENT ON COLUMN pipeline_state.value IS '状态值（JSON 字符串）';
COMMENT ON COLUMN pipeline_state.updated_at IS '更新时间';

-- ============================================================================
-- 3. crawler_item 表（商品主表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS crawler_item (
    id BIGSERIAL PRIMARY KEY,
    source_uid TEXT NOT NULL UNIQUE,
    site TEXT NOT NULL,
    category TEXT NOT NULL,
    item_id TEXT NOT NULL,
    
    -- 展示字段（最新值）
    brand_name TEXT NULL,
    model_name TEXT NULL,
    model_no TEXT NULL,
    currency TEXT NOT NULL DEFAULT 'JPY',
    price INTEGER NULL,
    
    -- 图片引用（MinIO keys）
    image_sha256 TEXT NULL,
    image_original_key TEXT NULL,
    image_thumb_300_key TEXT NULL,
    image_thumb_600_key TEXT NULL,
    
    -- 状态字段
    status TEXT NOT NULL DEFAULT 'active',
    first_seen_dt DATE NOT NULL,
    last_seen_dt DATE NOT NULL,
    sold_dt DATE NULL,
    sold_reason TEXT NULL,
    
    -- 时间戳字段
    last_crawl_time TIMESTAMPTZ NOT NULL,
    last_log_id BIGINT NULL,
    price_last_changed_at TIMESTAMPTZ NULL,
    price_last_changed_dt DATE NULL,
    
    -- 版本号
    version INTEGER NOT NULL DEFAULT 1,
    
    -- 创建和更新时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 创建索引（为 APP 检索）
CREATE INDEX IF NOT EXISTS idx_crawler_item_site_category_status 
    ON crawler_item(site, category, status);
CREATE INDEX IF NOT EXISTS idx_crawler_item_brand_name 
    ON crawler_item(brand_name);
CREATE INDEX IF NOT EXISTS idx_crawler_item_model_no 
    ON crawler_item(model_no);
CREATE INDEX IF NOT EXISTS idx_crawler_item_price 
    ON crawler_item(price);
CREATE INDEX IF NOT EXISTS idx_crawler_item_last_seen_dt 
    ON crawler_item(last_seen_dt DESC);
CREATE INDEX IF NOT EXISTS idx_crawler_item_status 
    ON crawler_item(status);

COMMENT ON TABLE crawler_item IS '商品主表，存储从 crawler_log 提取的商品信息';
COMMENT ON COLUMN crawler_item.source_uid IS '幂等去重键：{site}:{item_id}';
COMMENT ON COLUMN crawler_item.status IS '商品状态：active/sold/removed';

-- ============================================================================
-- 4. item_change_history 表（商品变更历史表）
-- ============================================================================

CREATE TABLE IF NOT EXISTS item_change_history (
    id BIGSERIAL PRIMARY KEY,
    dt DATE NOT NULL,
    source_uid TEXT NOT NULL,
    change_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    change_type TEXT NOT NULL,
    old_value TEXT NULL,
    new_value TEXT NULL,
    currency TEXT NULL,
    reason TEXT NULL,
    log_id BIGINT NULL,
    item_version INTEGER NULL,
    event_key TEXT NOT NULL UNIQUE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_item_chg_uid_time 
    ON item_change_history (source_uid, change_time DESC);
CREATE INDEX IF NOT EXISTS idx_item_chg_dt_type 
    ON item_change_history (dt, change_type);
CREATE INDEX IF NOT EXISTS idx_item_chg_source_uid 
    ON item_change_history (source_uid);
CREATE INDEX IF NOT EXISTS idx_item_chg_dt 
    ON item_change_history (dt);

COMMENT ON TABLE item_change_history IS '商品变更历史表，记录价格、状态等变更';
COMMENT ON COLUMN item_change_history.dt IS '变更日期';
COMMENT ON COLUMN item_change_history.change_type IS '变更类型：price/status 等';
COMMENT ON COLUMN item_change_history.event_key IS '事件唯一键，用于去重（全局唯一）';

