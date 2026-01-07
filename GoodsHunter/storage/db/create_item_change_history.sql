-- 仅创建 item_change_history 表（如果不存在）
-- 用于手动修复缺失的表

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

