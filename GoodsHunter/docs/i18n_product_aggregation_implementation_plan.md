# i18n 与商品聚合实施计划

## 概述

本文档详细说明了如何实现多语言商品聚合和动态翻译功能。主要目标：
1. 对抓取的多国网站商品进行关联，通过翻译归一化为相同格式，匹配到归一化的商品 product 层面
2. 在展示页面支持动态翻译，根据用户选择的语言自动转换显示内容

## 一、目录结构设计

### 1.1 新的全球化目录结构

```
GoodsHunter/
├── i18n/                          # 新增：全球化模块根目录
│   ├── __init__.py
│   ├── dictionaries/              # 字典文件目录（从 crawler/extract/dictionary 迁移）
│   │   ├── watch.yaml            # 从 crawler/extract/dictionary/watch.yaml 移动
│   │   └── ...                   # 未来可扩展其他类别字典
│   ├── translation/               # 翻译映射模块
│   │   ├── __init__.py
│   │   ├── mapper.py             # 翻译映射核心逻辑
│   │   ├── normalizer.py         # 归一化处理（多语言 -> 英文）
│   │   └── loader.py             # 字典加载器
│   └── aggregation/               # 商品聚合模块
│       ├── __init__.py
│       ├── product_aggregator.py # 商品聚合核心逻辑
│       └── matcher.py            # 商品匹配逻辑
```

### 1.2 需要修改的现有文件

- `crawler/extract/transforms.py`: 更新 `watch.yaml` 的引用路径
- `crawler/extract/dictionary/watch.yaml`: 移动到 `i18n/dictionaries/watch.yaml`

## 二、数据库表设计

### 2.1 修改 crawler_item 表

在 `crawler_item` 表中添加 `product_id` 字段：

```sql
ALTER TABLE crawler_item ADD COLUMN product_id BIGINT NULL;
CREATE INDEX idx_crawler_item_product_id ON crawler_item(product_id);
COMMENT ON COLUMN crawler_item.product_id IS '关联的聚合商品ID，NULL表示未关联';
```

### 2.2 创建 product 表（聚合商品表）

```sql
CREATE TABLE IF NOT EXISTS product (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL,                    -- 商品类别（手表/珠宝/包/衣服/相机等）
    brand_name TEXT NOT NULL,                 -- 标准化品牌名（英文）
    model_name TEXT NOT NULL,                 -- 标准化型号名（英文）
    model_no TEXT NOT NULL,                  -- 标准化型号编号（英文）
    
    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 创建唯一索引，确保同一商品不重复
CREATE UNIQUE INDEX idx_product_unique 
    ON product(category, brand_name, model_name, model_no);

-- 创建其他索引
CREATE INDEX idx_product_category ON product(category);
CREATE INDEX idx_product_brand_name ON product(brand_name);
CREATE INDEX idx_product_model_no ON product(model_no);

COMMENT ON TABLE product IS '聚合商品表，存储标准化后的商品信息';
COMMENT ON COLUMN product.brand_name IS '标准化品牌名（英文）';
COMMENT ON COLUMN product.model_name IS '标准化型号名（英文）';
COMMENT ON COLUMN product.model_no IS '标准化型号编号（英文）';
```

### 2.3 创建 brand_translations 表（品牌翻译表）

```sql
CREATE TABLE IF NOT EXISTS brand_translations (
    brand_name TEXT PRIMARY KEY,              -- 标准化品牌名（英文，作为主键）
    translations JSONB NOT NULL,             -- 多语言翻译映射
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE brand_translations IS '品牌翻译表，存储品牌的多语言翻译';
COMMENT ON COLUMN brand_translations.translations IS 'JSON格式，如：{"en": "Rolex", "zh": "劳力士", "ja": "ロレックス"}';
```

### 2.4 创建 model_translations 表（型号翻译表）

```sql
CREATE TABLE IF NOT EXISTS model_translations (
    model_no TEXT PRIMARY KEY,               -- 型号编号（作为主键）
    translations JSONB NOT NULL,             -- 多语言翻译映射
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE model_translations IS '型号翻译表，存储型号的多语言翻译';
COMMENT ON COLUMN model_translations.translations IS 'JSON格式，如：{"en": "Daytona", "zh": "迪通拿", "ja": "デイトナ"}';
```

### 2.5 创建 model_name_translations 表（型号名称翻译表）

```sql
CREATE TABLE IF NOT EXISTS model_name_translations (
    brand_name TEXT NOT NULL,                 -- 品牌名（用于区分不同品牌的同名型号）
    model_name TEXT NOT NULL,                 -- 标准化型号名（英文）
    translations JSONB NOT NULL,             -- 多语言翻译映射
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    PRIMARY KEY (brand_name, model_name)
);

COMMENT ON TABLE model_name_translations IS '型号名称翻译表，存储型号名称的多语言翻译';
COMMENT ON COLUMN model_name_translations.translations IS 'JSON格式，如：{"en": "Heritage Collection", "zh": "传承系列", "ja": "ヘリテージコレクション"}';
```

## 三、后端模块设计

### 3.1 翻译映射模块（i18n/translation/）

#### 3.1.1 loader.py - 字典加载器

负责从 YAML 文件加载字典数据，并提供统一的访问接口。

**功能：**
- 加载 `watch.yaml` 等字典文件
- 缓存字典数据
- 提供品牌、型号、型号编号的别名查询

#### 3.1.2 normalizer.py - 归一化处理器

负责将多语言的品牌名、型号名、型号编号归一化为标准英文格式。

**功能：**
- 根据字典将日文/中文品牌名转换为英文标准名
- 根据字典将日文/中文型号名转换为英文标准名
- 处理型号编号的标准化

**核心方法：**
```python
def normalize_brand(brand_name: str, category: str = "watch") -> str:
    """将品牌名归一化为标准英文格式"""
    
def normalize_model_name(brand_name: str, model_name: str, category: str = "watch") -> str:
    """将型号名归一化为标准英文格式"""
    
def normalize_model_no(model_no: str) -> str:
    """将型号编号标准化（去除空格、统一大小写等）"""
```

#### 3.1.3 mapper.py - 翻译映射器

负责将标准英文格式转换为目标语言。

**功能：**
- 从数据库加载翻译映射
- 将标准英文转换为目标语言（中文/日文/英文）
- 处理翻译缺失的情况（返回原始值）

**核心方法：**
```python
def translate_brand(brand_name: str, target_lang: str) -> str:
    """将品牌名翻译为目标语言"""
    
def translate_model_name(brand_name: str, model_name: str, target_lang: str) -> str:
    """将型号名翻译为目标语言"""
    
def translate_model_no(model_no: str, target_lang: str) -> str:
    """将型号编号翻译为目标语言"""
```

### 3.2 商品聚合模块（i18n/aggregation/）

#### 3.2.1 matcher.py - 商品匹配器

负责匹配两个商品是否为同一商品。

**功能：**
- 根据品牌、型号、型号编号进行匹配
- 支持模糊匹配（处理别名）

**核心方法：**
```python
def match_products(item1: dict, item2: dict) -> bool:
    """判断两个商品是否为同一商品"""
```

#### 3.2.2 product_aggregator.py - 商品聚合器

负责将 `crawler_item` 记录聚合到 `product` 表。

**功能：**
- 读取 `crawler_item` 表中未关联的记录
- 归一化品牌、型号、型号编号
- 查找或创建对应的 `product` 记录
- 更新 `crawler_item.product_id`

**核心方法：**
```python
def aggregate_items(batch_size: int = 100) -> dict:
    """批量聚合商品，返回统计信息"""
    
def aggregate_single_item(item_id: int) -> Optional[int]:
    """聚合单个商品，返回 product_id"""
```

### 3.3 字典数据初始化

需要将 `watch.yaml` 中的数据导入到翻译表中。

**功能模块：** `i18n/scripts/init_translations.py`

**功能：**
- 读取 `watch.yaml` 文件
- 解析品牌、型号、型号编号的别名
- 插入到 `brand_translations`、`model_name_translations`、`model_translations` 表

## 四、前端 i18n 配置

### 4.1 安装依赖

```bash
cd services/web
npm install react-i18next i18next i18next-browser-languagedetector i18next-http-backend
```

### 4.2 目录结构

```
services/web/
├── src/
│   ├── i18n/                      # 新增：i18n 配置目录
│   │   ├── index.ts               # i18n 初始化配置
│   │   └── locales/               # 翻译文件目录
│   │       ├── en/
│   │       │   └── translation.json
│   │       ├── zh/
│   │       │   └── translation.json
│   │       └── ja/
│   │           └── translation.json
│   └── ...
```

### 4.3 i18n 配置（src/i18n/index.ts）

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 翻译资源（可以从 API 动态加载）
import enTranslations from './locales/en/translation.json';
import zhTranslations from './locales/zh/translation.json';
import jaTranslations from './locales/ja/translation.json';

i18n
  .use(LanguageDetector)  // 自动检测用户语言
  .use(initReactI18next)  // 连接 react-i18next
  .init({
    resources: {
      en: { translation: enTranslations },
      zh: { translation: zhTranslations },
      ja: { translation: jaTranslations },
    },
    fallbackLng: 'en',  // 默认语言
    debug: false,
    interpolation: {
      escapeValue: false,  // React 已经转义
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
```

### 4.4 翻译工具函数

创建 `src/utils/translation.ts` 用于处理商品信息的动态翻译：

```typescript
import { useTranslation } from 'react-i18next';

/**
 * 翻译商品信息（品牌、型号等）
 * 如果翻译不存在，返回原始值
 */
export function useItemTranslation() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language;

  const translateBrand = (brandName: string, originalBrandName?: string): string => {
    // 优先使用 API 返回的翻译，如果没有则使用原始值
    // 这里可以调用 API 获取翻译，或使用本地翻译文件
    return originalBrandName || brandName;
  };

  const translateModelName = (modelName: string, originalModelName?: string): string => {
    return originalModelName || modelName;
  };

  return {
    currentLang,
    translateBrand,
    translateModelName,
  };
}
```

### 4.5 语言切换组件

创建 `src/components/LanguageSelector.tsx`：

```typescript
import { useTranslation } from 'react-i18next';

export function LanguageSelector() {
  const { i18n } = useTranslation();

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  return (
    <div className="language-selector">
      <button onClick={() => changeLanguage('en')}>English</button>
      <button onClick={() => changeLanguage('zh')}>中文</button>
      <button onClick={() => changeLanguage('ja')}>日本語</button>
    </div>
  );
}
```

## 五、API 接口设计

### 5.1 商品列表接口增强

**现有接口：** `GET /api/items`

**增强功能：**
- 支持 `lang` 查询参数（en/zh/ja）
- 返回商品信息时，根据 `lang` 参数返回对应语言的翻译

**响应格式：**
```json
{
  "items": [
    {
      "id": 1,
      "brand_name": "Rolex",           // 标准化英文名
      "brand_name_translated": "劳力士", // 翻译后的名称（如果 lang=zh）
      "model_name": "Daytona",
      "model_name_translated": "迪通拿",
      "model_no": "116515LNA",
      "price": 1500000,
      "currency": "JPY",
      "product_id": 123
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 5.2 商品详情接口增强

**现有接口：** `GET /api/items/{item_id}`

**增强功能：**
- 支持 `lang` 查询参数
- 返回翻译后的商品信息

### 5.3 新增：翻译查询接口

**接口：** `GET /api/translations/brand/{brand_name}?lang={lang}`

**功能：** 查询品牌翻译

**响应：**
```json
{
  "brand_name": "Rolex",
  "translated": "劳力士",
  "lang": "zh"
}
```

## 六、实施步骤

### 阶段一：目录结构调整和字典迁移

1. ✅ 创建 `i18n/` 目录结构
2. ✅ 移动 `watch.yaml` 到 `i18n/dictionaries/watch.yaml`
3. ✅ 更新 `crawler/extract/transforms.py` 中的字典路径引用
4. ✅ 测试确保现有功能正常

### 阶段二：数据库表创建

1. ✅ 在 `init.sql` 中添加新表定义
2. ✅ 执行数据库迁移（添加 `product_id` 字段）
3. ✅ 创建翻译表

### 阶段三：后端模块开发

1. ✅ 实现 `i18n/translation/loader.py` - 字典加载器
2. ✅ 实现 `i18n/translation/normalizer.py` - 归一化处理器
3. ✅ 实现 `i18n/translation/mapper.py` - 翻译映射器
4. ✅ 实现 `i18n/aggregation/matcher.py` - 商品匹配器
5. ✅ 实现 `i18n/aggregation/product_aggregator.py` - 商品聚合器
6. ✅ 实现 `i18n/scripts/init_translations.py` - 字典数据初始化脚本

### 阶段四：商品聚合功能

1. ✅ 运行初始化脚本，将 `watch.yaml` 数据导入翻译表
2. ✅ 开发聚合任务脚本（可独立运行，与抓取解耦）
3. ✅ 测试商品聚合功能

### 阶段五：前端 i18n 配置

1. ✅ 安装 react-i18next 依赖
2. ✅ 创建 i18n 配置文件和翻译文件
3. ✅ 创建语言切换组件
4. ✅ 更新现有组件以支持多语言

### 阶段六：API 接口增强

1. ✅ 修改商品列表接口，支持 `lang` 参数
2. ✅ 修改商品详情接口，支持 `lang` 参数
3. ✅ 实现翻译查询接口（可选）

### 阶段七：测试和优化

1. ✅ 端到端测试多语言功能
2. ✅ 测试商品聚合功能
3. ✅ 性能优化
4. ✅ 文档更新

## 七、关键设计决策

### 7.1 为什么 crawler_item 保留多语言原始数据？

- **原因：** 保留原始数据可以：
  1. 支持未来更精确的翻译
  2. 便于调试和问题排查
  3. 支持用户查看原始信息

### 7.2 为什么使用独立的聚合流程？

- **原因：** 解耦抓取和聚合，使得：
  1. 抓取流程更简单，性能更好
  2. 聚合逻辑可以独立优化和重试
  3. 便于处理历史数据

### 7.3 翻译策略

- **归一化阶段：** 多语言 → 标准英文（用于匹配和聚合）
- **展示阶段：** 标准英文 → 目标语言（根据用户选择）

### 7.4 翻译缺失处理

- 如果某个品牌/型号没有目标语言的翻译，则：
  1. 优先使用原始值（如果原始值已经是目标语言）
  2. 否则使用标准英文值
  3. 前端可以标记为"未翻译"

## 八、注意事项

1. **向后兼容：** 确保移动 `watch.yaml` 后，现有的 transform 功能仍然正常
2. **数据一致性：** 聚合过程需要保证数据一致性，考虑使用事务
3. **性能考虑：** 翻译查询需要缓存，避免频繁查询数据库
4. **扩展性：** 字典结构需要支持未来扩展其他商品类别（珠宝、包等）

## 九、后续优化方向

1. **自动翻译：** 对于缺失的翻译，可以考虑使用翻译 API 自动补充
2. **翻译质量：** 建立翻译审核机制
3. **缓存优化：** 使用 Redis 缓存翻译数据
4. **批量处理：** 优化商品聚合的批量处理性能

