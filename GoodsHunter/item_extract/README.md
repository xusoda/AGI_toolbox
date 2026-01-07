# Item Extract 模块

从 `crawler_log` 表中提取 item 数据，同步到 `crawler_item` 表，并记录变更历史到 `item_change_history` 表。

## 功能特性

- ✅ 从 `crawler_log` 增量同步到 `crawler_item` 表
- ✅ 自动检测价格变化并记录到 `item_change_history`
- ✅ 使用游标机制支持批量处理和崩溃恢复
- ✅ 幂等性保证（通过 event_key 唯一约束）
- ✅ 并发安全（使用 SELECT ... FOR UPDATE）
- ✅ 预留状态变化检测接口

## 模块结构

```
item_extract/
├── __init__.py                 # 模块初始化
├── exceptions.py                # 自定义异常
├── utils.py                     # 工具函数（数据库连接等）
├── models.py                    # 表结构定义
├── state_manager.py             # 游标状态管理
├── price_normalizer.py         # 价格规范化
├── source_uid_generator.py      # Source UID 生成
├── event_key_generator.py       # Event Key 生成（幂等）
├── change_detector.py           # 变化检测逻辑
├── log_reader.py                # Crawler Log 读取
├── item_upserter.py             # Item 表 Upsert
├── history_writer.py            # 变更历史写入
├── sync_processor.py           # 主处理流程
└── main.py                      # 入口脚本
```

## 数据库表

### 1. pipeline_state
游标状态表，用于记录处理进度。

### 2. crawler_item
Item 主表，存储去重后的商品信息。

### 3. item_change_history
变更历史表（按月分区），记录价格变化和状态变化。

## 使用方法

### 1. 初始化数据库表

```bash
# 设置数据库连接URL
export DATABASE_URL="postgresql://user:password@host:port/dbname"

# 初始化表结构
python -m item_extract.main --init-db
```

### 2. 运行一次同步

```bash
# 处理所有待处理的记录
python -m item_extract.main --once

# 限制处理数量（用于测试）
python -m item_extract.main --once --max-records 1000

# 自定义批量大小
python -m item_extract.main --once --batch-size 200
```

### 3. 持续运行模式

```bash
# 默认每60秒轮询一次
python -m item_extract.main

# 自定义轮询间隔（秒）
python -m item_extract.main --interval 30
```

### 4. 命令行参数

```
--database-url     数据库连接URL（默认从环境变量 DATABASE_URL 读取）
--batch-size       批量处理大小（默认: 100）
--max-records      最大处理记录数（默认: 不限制）
--once             只运行一次（默认: 持续运行）
--interval         持续运行模式的轮询间隔（秒，默认: 60）
--init-db          初始化数据库表（如果不存在）
```

## 处理流程

1. **读取游标**：从 `pipeline_state` 表获取 `last_log_id`
2. **读取日志**：从 `crawler_log` 表读取 `id > last_log_id` 且 `status='success'` 的记录
3. **处理每条记录**：
   - 规范化价格
   - 生成 `source_uid`
   - Upsert 到 `crawler_item` 表（获取旧价格）
   - 检测价格变化
   - 如果价格变化，更新 item 价格字段并写入 `item_change_history`
4. **更新游标**：处理成功后更新 `last_log_id`

## 设计原则

1. **幂等性**：通过 `event_key` 唯一约束保证历史记录不重复
2. **并发安全**：使用 `SELECT ... FOR UPDATE` 防止并发问题
3. **崩溃恢复**：游标机制支持从上次中断处继续处理
4. **批量处理**：支持批量读取和处理，提高效率

## 注意事项

1. **新商品不记录初始价格**：只有价格变化时才写入历史记录
2. **分区表**：`item_change_history` 按月分区，首次运行会自动创建当前月份分区
3. **游标恢复**：如果处理失败，游标不更新，下次可以继续处理
4. **批量大小**：建议批量大小 100-500，根据实际情况调整

## 错误处理

- 单条记录处理失败不会影响其他记录
- 错误信息会记录在返回结果中
- 建议定期检查错误日志

## 扩展性

- 预留了状态变化检测接口（`write_status_change`）
- 可以轻松添加其他类型的变化检测（如属性变化）

