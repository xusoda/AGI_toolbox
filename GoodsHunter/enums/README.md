# 枚举值总结

本文档列出了 GoodsHunter 项目中所有已实现的枚举值及其使用情况。

## 目录结构

```
enums/
├── business/              # 业务相关枚举
│   ├── category.py/ts     # 商品类别
│   ├── status.py/ts       # 商品状态
│   ├── change_type.py     # 变更类型（仅 Python）
│   └── crawler_status.py  # 抓取日志状态（仅 Python）
├── display/               # 展示层相关枚举
│   ├── sort.py/ts         # 排序相关
│   └── lang.py/ts         # 语言代码
└── trade/                 # 交易相关枚举
    └── currency.py/ts     # 货币代码
```

---

## 已实现的枚举

### 1. Category（商品类别）- ✅ 已实现

**分类**: 业务相关  
**位置**: 
- Python: `enums/business/category.py`
- TypeScript: `enums/business/category.ts`

**枚举值**:
- `WATCH = "watch"` - 手表
- `BAG = "bag"` - 箱包
- `JEWELRY = "jewelry"` - 珠宝/首饰
- `CLOTHING = "clothing"` - 衣服
- `CAMERA = "camera"` - 相机

**使用场景**:
- 抓取配置（profile）中的 category 字段
- 商品列表筛选时的类别过滤
- 搜索接口的类别过滤
- 数据库查询中的类别过滤

**代码位置**:
- `services/api/app/routers/items.py:54` - 导入和使用
- `services/api/app/routers/search.py:12` - 搜索接口参数
- `services/api/app/db/queries.py:30` - 数据库查询
- `services/web/src/components/CategorySelector.tsx:3` - 类别选择器
- `services/web/src/api/types.ts:2` - API 类型定义

**状态**: ✅ 已完全实现并在代码中使用

---

### 2. ItemStatus（商品状态）- ✅ 已实现

**分类**: 业务相关  
**位置**: 
- Python: `enums/business/status.py`
- TypeScript: `enums/business/status.ts`

**枚举值**:
- `ACTIVE = "active"` - 在售
- `SOLD = "sold"` - 已售出
- `REMOVED = "removed"` - 已下架

**使用场景**:
- 商品列表筛选（`/items` 接口的 status 参数）
- 搜索接口的状态过滤（`/search` 接口的 status 参数）
- 商品详情展示状态
- 数据库查询中的状态过滤
- 数据库表 `crawler_item.status` 字段

**代码位置**:
- `services/api/app/routers/items.py:55` - 接口参数
- `services/api/app/routers/search.py:13` - 搜索接口参数
- `services/api/app/db/queries.py:31` - 查询参数
- `services/web/src/pages/ItemDetailPage.tsx:6` - 状态展示
- `services/web/src/pages/ItemsListPage.tsx:13` - 状态筛选
- `services/web/src/api/types.ts:3` - API 类型定义

**状态**: ✅ 已完全实现并在代码中使用

---

### 3. SortOption / SortField / SortOrder（排序相关）- ✅ 已实现

**分类**: 展示层相关  
**位置**: 
- Python: `enums/display/sort.py`
- TypeScript: `enums/display/sort.ts`

#### 3.1 SortOption（列表页排序选项）

**枚举值**:
- `FIRST_SEEN_DESC = "first_seen_desc"` - 首次发现时间（降序）
- `PRICE_ASC = "price_asc"` - 价格（升序）
- `PRICE_DESC = "price_desc"` - 价格（降序）

**使用场景**:
- 商品列表页的排序选项
- `/items` 接口的 sort 参数

**代码位置**:
- `services/api/app/routers/items.py:56` - 接口参数
- `services/api/app/db/queries.py:32` - 查询排序
- `services/web/src/pages/ItemsListPage.tsx:12` - 排序状态
- `services/web/src/api/types.ts:4` - API 类型定义

#### 3.2 SortField（搜索页排序字段）

**枚举值**:
- `PRICE = "price"` - 价格
- `LAST_SEEN_DT = "last_seen_dt"` - 最后发现时间
- `CREATED_AT = "created_at"` - 创建时间

**使用场景**:
- 搜索页的排序字段选择
- `/search` 接口的 sort_field 参数

**代码位置**:
- `services/api/app/routers/search.py:16` - 搜索接口参数
- `services/web/src/pages/ItemsListPage.tsx:12` - 排序字段状态
- `services/web/src/api/types.ts:4` - API 类型定义

#### 3.3 SortOrder（排序顺序）

**枚举值**:
- `ASC = "asc"` - 升序
- `DESC = "desc"` - 降序

**使用场景**:
- 搜索页的排序顺序选择
- `/search` 接口的 sort_order 参数

**代码位置**:
- `services/api/app/routers/search.py:16` - 搜索接口参数
- `services/web/src/pages/ItemsListPage.tsx:12` - 排序顺序状态
- `services/web/src/api/types.ts:4` - API 类型定义

**状态**: ✅ 已完全实现并在代码中使用

---

### 4. LanguageCode（语言代码）- ✅ 已实现

**分类**: 展示层相关  
**位置**: 
- Python: `enums/display/lang.py`
- TypeScript: `enums/display/lang.ts`

**枚举值**:
- `EN = "en"` - 英语
- `ZH = "zh"` - 中文（简体）
- `JA = "ja"` - 日语

**使用场景**:
- 接口语言参数（`/items` 和 `/search` 的 lang 参数）
- 前端语言切换
- 翻译映射的语言标识

**代码位置**:
- `services/api/app/routers/items.py:57` - 接口参数
- `services/api/app/routers/search.py:14` - 搜索接口参数
- `services/web/src/api/types.ts:5` - API 类型定义

**状态**: ✅ 已完全实现并在代码中使用

---

### 5. CurrencyCode（货币代码）- ✅ 已实现

**分类**: 交易相关  
**位置**: 
- Python: `enums/trade/currency.py`
- TypeScript: `enums/trade/currency.ts`

**枚举值**:
- `JPY = "JPY"` - 日元（默认值）
- `USD = "USD"` - 美元
- `CNY = "CNY"` - 人民币

**使用场景**:
- 商品价格货币单位
- 数据库字段 `crawler_item.currency` 默认值
- 价格展示时的货币符号映射
- 搜索接口的货币过滤

**代码位置**:
- `services/api/app/routers/search.py:15` - 搜索接口参数
- `services/web/src/api/types.ts:6` - API 类型定义
- `storage/db/init.sql:119` - 数据库字段默认值 'JPY'

**状态**: ✅ 已完全实现并在代码中使用

---

### 6. ChangeType（变更类型）- ✅ 已实现（仅 Python）

**分类**: 业务相关（变更历史）  
**位置**: 
- Python: `enums/business/change_type.py`
- TypeScript: 不需要（主要在服务端使用）

**枚举值**:
- `PRICE = "price"` - 价格变更
- `STATUS = "status"` - 状态变更

**使用场景**:
- 数据库表 `item_change_history.change_type` 字段
- 变更历史查询和统计
- 变更检测逻辑

**代码位置**:
- `item_extract/history_writer.py:23` - 变更历史写入
- `storage/db/init.sql:198,220` - 数据库字段和注释

**状态**: ✅ 已实现（仅服务端使用）

---

### 7. CrawlerLogStatus（抓取日志状态）- ✅ 已实现（仅 Python）

**分类**: 业务相关（抓取流程）  
**位置**: 
- Python: `enums/business/crawler_status.py`
- TypeScript: 不需要（主要在服务端使用）

**枚举值**:
- `SUCCESS = "success"` - 成功
- `FAILED = "failed"` - 失败

**使用场景**:
- 数据库表 `crawler_log.status` 字段
- 抓取日志查询和统计
- 抓取结果状态标识

**代码位置**:
- `storage/output/db_writer.py:475` - 数据库写入
- `storage/db/init.sql:29,77` - 数据库字段和注释

**状态**: ✅ 已实现（仅服务端使用）

---

## 枚举使用方式

### Python 后端

```python
from enums.business.category import Category
from enums.business.status import ItemStatus
from enums.display.sort import SortOption
from enums.display.lang import LanguageCode
from enums.trade.currency import CurrencyCode

# 使用枚举值
category = Category.WATCH.value  # "watch"
status = ItemStatus.ACTIVE.value  # "active"

# 验证枚举值
if Category.is_valid(category):
    # 处理类别
    pass

# 获取默认值
default_category = Category.get_default()  # "watch"
default_status = ItemStatus.get_default()  # "active"
```

### TypeScript 前端

```typescript
import { Category } from '@enums/business/category'
import { ItemStatus } from '@enums/business/status'
import { SortOption, SortField, SortOrder } from '@enums/display/sort'
import { LanguageCode } from '@enums/display/lang'
import { CurrencyCode } from '@enums/trade/currency'

// 使用枚举值
const category: Category = Category.WATCH
const status: ItemStatus = ItemStatus.ACTIVE

// 验证枚举值
if (isValidCategory(value)) {
  // 处理类别
}

// 获取默认值
const defaultCategory = getDefaultCategory()  // Category.WATCH
const defaultStatus = getDefaultItemStatus()  // ItemStatus.ACTIVE
```

**注意**: 前端项目配置了路径别名 `@enums`，指向全局的 `enums/` 目录。这需要：
- 在 `tsconfig.json` 中配置 `paths` 别名
- 在 `vite.config.ts` 中配置 `resolve.alias`

---

## 枚举实现特点

### Python 枚举

所有 Python 枚举都继承自 `str, Enum`，提供以下方法：
- `all_values()`: 获取所有枚举值列表
- `is_valid(value)`: 检查值是否为有效的枚举值
- `get_default()`: 获取默认枚举值（部分枚举提供）

### TypeScript 枚举

所有 TypeScript 枚举都提供以下辅助函数：
- `*_VALUES`: 所有枚举值数组
- `isValid*()`: 类型守卫函数，检查值是否为有效的枚举值
- `getDefault*()`: 获取默认枚举值

---

## 总结

### 已完全实现的枚举

1. ✅ **Category** - 商品类别（Python + TypeScript）
2. ✅ **ItemStatus** - 商品状态（Python + TypeScript）
3. ✅ **SortOption / SortField / SortOrder** - 排序相关（Python + TypeScript）
4. ✅ **LanguageCode** - 语言代码（Python + TypeScript）
5. ✅ **CurrencyCode** - 货币代码（Python + TypeScript）
6. ✅ **ChangeType** - 变更类型（仅 Python）
7. ✅ **CrawlerLogStatus** - 抓取日志状态（仅 Python）

所有枚举都已实现并在代码中广泛使用，确保了类型安全和代码一致性。

---

## 相关文档

- **架构文档**: `docs/architecture/architecture.md` - 包含枚举使用的详细说明
- **枚举目录**: `enums/` - 所有枚举定义的源代码位置
