# Item Extract 模块代码规划

## 概述
从 `crawler_log` 表中提取 item 数据，同步到 `crawler_item` 表，并记录变更历史到 `item_change_history` 表。

## 数据库表结构

### 1. pipeline_state 表（游标管理）
- `key` TEXT PRIMARY KEY
- `value` TEXT NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

### 2. crawler_item 表（Item主表）
- 唯一键：`source_uid`
- 字段：id, source_uid, site, category, item_id, brand_name, model_name, model_no, currency, price, image_sha256, image_original_key, image_thumb_300_key, image_thumb_600_key, status, first_seen_dt, last_seen_dt, sold_dt, sold_reason, last_crawl_time, last_log_id, price_last_changed_at, price_last_changed_dt, version

### 3. item_change_history 表（变更历史）
- 分区表：按 `dt` 分区（按月）
- 字段：id, dt, source_uid, change_time, change_type, old_value, new_value, currency, reason, log_id, item_version, event_key
- 唯一约束：`UNIQUE(dt, event_key)`（幂等保证）

## 代码模块规划

### 1. `models.py` - 数据模型定义
**职责**：
- 定义表结构 SQL（CREATE TABLE 语句）
- 定义字段映射和数据类型
- 提供表初始化方法

**主要函数**：
- `create_tables(conn)`: 创建所有需要的表
- `get_table_schemas()`: 返回表结构定义

---

### 2. `state_manager.py` - 游标状态管理
**职责**：
- 管理 `pipeline_state` 表的读写
- 提供游标（last_log_id）的获取和更新

**主要函数**：
- `get_last_log_id(conn) -> Optional[int]`: 获取上次处理的 log_id
- `update_last_log_id(conn, log_id: int)`: 更新游标
- `get_state(conn, key: str) -> Optional[str]`: 通用状态获取
- `set_state(conn, key: str, value: str)`: 通用状态设置

---

### 3. `price_normalizer.py` - 价格规范化
**职责**：
- 将价格字符串转换为整数
- 处理各种格式（带逗号、货币符号等）
- 处理空值和异常值

**主要函数**：
- `normalize_price(price: Any, currency: str = 'JPY') -> Optional[int]`: 规范化价格
- `is_price_changed(old_price: Optional[int], new_price: Optional[int]) -> bool`: 判断价格是否变化（处理 NULL）

---

### 4. `source_uid_generator.py` - Source UID 生成
**职责**：
- 生成标准化的 `source_uid`
- 格式：`{site}:{category}:{item_id}`

**主要函数**：
- `generate_source_uid(site: str, category: str, item_id: str) -> str`: 生成 source_uid
- `parse_source_uid(source_uid: str) -> Tuple[str, str, str]`: 解析 source_uid（可选，用于调试）

---

### 5. `event_key_generator.py` - Event Key 生成（幂等保证）
**职责**：
- 生成 `event_key` 用于去重
- 使用 SHA256 哈希

**主要函数**：
- `generate_price_event_key(source_uid: str, log_id: int) -> str`: 生成价格变化事件的 event_key
- `generate_status_event_key(source_uid: str, sold_dt: date, status: str) -> str`: 生成状态变化事件的 event_key（预留）

---

### 6. `change_detector.py` - 变化检测逻辑
**职责**：
- 检测价格变化
- 预留状态变化检测接口
- 封装变化判断逻辑

**主要函数**：
- `detect_price_change(old_price: Optional[int], new_price: Optional[int]) -> bool`: 检测价格是否变化
- `should_record_price_change(old_price: Optional[int], new_price: Optional[int]) -> bool`: 判断是否需要记录价格变化（新商品不记录初始价格）

---

### 7. `item_upserter.py` - Item 表 Upsert 逻辑
**职责**：
- 从 `crawler_log` 记录构建 item 数据
- 执行 upsert 操作（INSERT ... ON CONFLICT UPDATE）
- 处理新商品 vs 已存在商品的逻辑
- 使用 `SELECT ... FOR UPDATE` 防止并发问题

**主要函数**：
- `upsert_item(conn, log_record: Dict) -> Tuple[Dict, Optional[int]]`: 
  - 输入：crawler_log 记录
  - 返回：(item_data, old_price)
  - 逻辑：
    - 如果不存在：插入新记录，返回 (item_data, None)
    - 如果存在：更新 last_seen_dt/last_crawl_time/last_log_id，返回 (item_data, old_price)

---

### 8. `history_writer.py` - 变更历史写入
**职责**：
- 写入 `item_change_history` 表
- 处理幂等性（通过 event_key 唯一约束）
- 处理分区表写入

**主要函数**：
- `write_price_change(conn, source_uid: str, old_price: Optional[int], new_price: Optional[int], currency: str, log_id: int, crawl_time: datetime, dt: date, item_version: int) -> bool`: 写入价格变化记录
- `write_status_change(conn, source_uid: str, old_status: str, new_status: str, sold_dt: date, reason: str, item_version: int) -> bool`: 写入状态变化记录（预留）

---

### 9. `log_reader.py` - Crawler Log 读取
**职责**：
- 从 `crawler_log` 表读取未处理的记录
- 支持批量读取和游标管理

**主要函数**：
- `fetch_unprocessed_logs(conn, last_log_id: int, batch_size: int = 100) -> List[Dict]`: 获取未处理的日志记录
- `get_log_count(conn, last_log_id: int) -> int`: 获取待处理记录数（用于进度显示）

---

### 10. `sync_processor.py` - 主处理流程
**职责**：
- 协调各个模块
- 实现完整的同步流程
- 错误处理和事务管理

**主要函数**：
- `process_single_log(conn, log_record: Dict) -> Dict`: 处理单条 log 记录
  - 步骤：
    1. 规范化价格
    2. 生成 source_uid
    3. Upsert item（获取 old_price）
    4. 检测价格变化
    5. 如果变化，写入 history
    6. 返回处理结果
- `process_batch(conn, log_records: List[Dict]) -> Dict`: 批量处理
- `run_sync(batch_size: int = 100, max_records: Optional[int] = None) -> Dict`: 主运行函数
  - 流程：
    1. 获取 last_log_id
    2. 读取未处理记录
    3. 批量处理
    4. 更新 last_log_id
    5. 返回统计信息

---

### 11. `main.py` - 入口脚本
**职责**：
- 命令行接口
- 配置管理
- 日志设置
- 定时任务支持

**主要功能**：
- 支持命令行参数：`--batch-size`, `--max-records`, `--once`（只运行一次）
- 支持持续运行模式（定期轮询）
- 初始化数据库表（如果不存在）
- 日志输出

---

### 12. `exceptions.py` - 自定义异常
**职责**：
- 定义项目特定的异常类

**异常类**：
- `ItemExtractError`: 基础异常
- `DatabaseError`: 数据库相关错误
- `ValidationError`: 数据验证错误

---

### 13. `utils.py` - 工具函数
**职责**：
- 通用工具函数
- 数据库连接管理（复用 DBWriter 的连接池模式）

**主要函数**：
- `get_db_connection(database_url: str)`: 获取数据库连接
- `create_connection_pool(database_url: str, pool_size: int)`: 创建连接池
- `format_datetime(dt: datetime) -> str`: 日期时间格式化
- `safe_int(value: Any) -> Optional[int]`: 安全转换为整数

---

## 文件结构

```
item_extract/
├── __init__.py
├── models.py              # 表结构定义
├── state_manager.py       # 游标状态管理
├── price_normalizer.py    # 价格规范化
├── source_uid_generator.py # Source UID 生成
├── event_key_generator.py  # Event Key 生成
├── change_detector.py     # 变化检测
├── item_upserter.py       # Item Upsert
├── history_writer.py      # 历史记录写入
├── log_reader.py          # Log 读取
├── sync_processor.py      # 主处理流程
├── main.py                # 入口脚本
├── exceptions.py          # 自定义异常
├── utils.py               # 工具函数
└── CODE_PLAN.md           # 本文档
```

## 依赖关系

```
main.py
  └─> sync_processor.py
       ├─> log_reader.py
       ├─> item_upserter.py
       │    ├─> source_uid_generator.py
       │    ├─> price_normalizer.py
       │    └─> change_detector.py
       ├─> history_writer.py
       │    ├─> event_key_generator.py
       │    └─> price_normalizer.py
       └─> state_manager.py
            └─> utils.py (数据库连接)
```

## 设计原则

1. **单一职责**：每个模块只负责一个明确的功能
2. **幂等性**：通过 event_key 唯一约束保证历史记录不重复
3. **事务安全**：使用 `SELECT ... FOR UPDATE` 防止并发问题
4. **错误处理**：每个模块都有明确的错误处理逻辑
5. **可测试性**：模块之间依赖清晰，便于单元测试
6. **可扩展性**：预留状态变化检测接口，便于后续扩展

## 实现顺序建议

1. **第一阶段**：基础模块
   - `models.py` - 表结构
   - `utils.py` - 工具函数
   - `exceptions.py` - 异常定义

2. **第二阶段**：数据处理模块
   - `price_normalizer.py`
   - `source_uid_generator.py`
   - `event_key_generator.py`
   - `change_detector.py`

3. **第三阶段**：数据库操作模块
   - `state_manager.py`
   - `log_reader.py`
   - `item_upserter.py`
   - `history_writer.py`

4. **第四阶段**：主流程
   - `sync_processor.py`
   - `main.py`

## 注意事项

1. **并发控制**：使用 `SELECT ... FOR UPDATE` 确保同一商品不会并发更新
2. **分区表**：`item_change_history` 需要按月分区，注意分区创建逻辑
3. **游标恢复**：如果处理失败，游标不更新，下次可以继续处理
4. **批量处理**：建议批量大小 100-500，根据实际情况调整
5. **日志记录**：关键操作需要记录日志，便于排查问题

