# URL 状态管理实现总结

## 实现完成情况

✅ **已完成所有核心功能**

### 1. 核心 Hook 和类型定义

#### `src/hooks/useURLState.ts`
- 基于 React Router 的 `useSearchParams` 实现
- 提供类型安全的状态访问和更新方法
- 支持深层链接和浏览器历史记录
- 自动处理 URL 参数编码/解码

#### `src/types/urlState.ts`
- 定义了完整的 URL 状态类型
- 包含所有当前和未来可能的状态字段
- 支持可扩展性设计

#### `src/hooks/useDebounce.ts`
- 防抖 Hook，用于搜索关键词输入
- 避免频繁更新 URL

#### `src/enums/display/lang.ts`
- 语言代码枚举定义（新增）

### 2. 组件更新

#### `ItemsListPage.tsx`
- ✅ 完全重构，使用 `useURLState` Hook
- ✅ 所有状态（搜索、筛选、分页、排序）同步到 URL
- ✅ 搜索关键词使用防抖处理（300ms）
- ✅ 支持深层链接

#### `CategorySelector.tsx`
- ✅ 使用 `useURLState` Hook
- ✅ 统一的状态管理方式
- ✅ 自动重置页码

#### `LanguageSelector.tsx`
- ✅ 语言选项同步到 URL
- ✅ 保持 localStorage 兼容性
- ✅ 支持从 URL 恢复语言

#### `App.tsx`
- ✅ 优先从 URL 读取语言
- ✅ 保持向后兼容（localStorage 作为后备）

## URL 参数映射

| UI 状态 | URL 参数名 | 类型 | 说明 |
|---------|-----------|------|------|
| 搜索关键词 | `q` | string | 搜索查询字符串 |
| 分类筛选 | `category` | string | 商品类别（空字符串表示"全部"） |
| 页码 | `page` | number | 当前页码 |
| 列表排序 | `sort` | string | 列表模式排序选项 |
| 搜索排序字段 | `sort_field` | string | 搜索模式排序字段 |
| 搜索排序顺序 | `sort_order` | string | 搜索模式排序顺序 |
| 语言 | `lang` | string | 语言代码（en/zh/ja） |

## 使用示例

### 基本使用

```typescript
import { useURLState } from '../hooks/useURLState'

function MyComponent() {
  const { getState, updateState, setValue } = useURLState()
  
  // 获取状态
  const state = getState()
  const category = state.category
  const page = state.page || 1
  
  // 更新状态（自动同步到 URL）
  updateState({ category: 'hermes', page: 1 })
  setValue('page', 2)
}
```

### 深层链接示例

用户可以直接访问：
```
/?q=爱马仕&category=hermes&page=1&sort_field=price&sort_order=asc&lang=zh
```

页面会自动：
- 显示搜索关键词"爱马仕"
- 筛选类别为 hermes
- 显示第 1 页
- 按价格升序排序
- 使用中文界面

## 可扩展性设计

### 未来可添加的筛选选项

URL 状态类型已预留以下字段，可直接使用：

```typescript
interface URLState {
  // 已实现
  q?: string
  category?: Category | ''
  page?: number
  sort?: SortOption
  sort_field?: SortField
  sort_order?: SortOrder
  lang?: LanguageCode
  
  // 未来扩展（已定义，可直接使用）
  status?: string        // 商品状态
  site?: string          // 站点
  brand_name?: string    // 品牌名称
  min_price?: number     // 最低价格
  max_price?: number     // 最高价格
  currency?: CurrencyCode // 货币代码
  page_size?: number     // 每页数量
}
```

### 添加新筛选选项的步骤

1. **在 `URLState` 接口中添加字段**（已完成，字段已预留）
2. **在 `useURLState` 的 `parseState` 中添加解析逻辑**
3. **在 `useURLState` 的 `keyToParamMap` 中添加映射**
4. **在组件中使用新字段**

示例：添加价格筛选

```typescript
// 1. URLState 中已有 min_price 和 max_price 字段

// 2. 在 parseState 中添加（已实现）
const minPrice = searchParams.get(URL_PARAM_KEYS.MIN_PRICE)
if (minPrice) {
  const parsed = parseInt(minPrice, 10)
  if (!isNaN(parsed)) state.min_price = parsed
}

// 3. 在 keyToParamMap 中添加（已实现）
min_price: URL_PARAM_KEYS.MIN_PRICE,
max_price: URL_PARAM_KEYS.MAX_PRICE,

// 4. 在组件中使用
const { getState, setValue } = useURLState()
const state = getState()
setValue('min_price', 1000)
```

## 技术特点

### 1. 类型安全
- 完整的 TypeScript 类型定义
- 编译时类型检查
- 智能代码提示

### 2. 性能优化
- 搜索关键词使用防抖（300ms）
- 状态更新合并处理
- 避免不必要的重新渲染

### 3. 用户体验
- 支持浏览器前进/后退
- 支持 URL 分享
- 刷新页面保持状态
- 深层链接支持

### 4. 向后兼容
- 保持 localStorage 语言偏好
- 支持旧版本 URL 格式
- 优雅降级处理

## 测试建议

### 1. 深层链接测试
- [ ] 直接访问 `/?q=爱马仕&category=hermes&page=1` 应正确显示搜索结果
- [ ] 直接访问 `/?category=hermes&sort=price_asc&page=2&lang=zh` 应正确显示筛选和排序结果

### 2. 状态同步测试
- [ ] 搜索关键词变更应同步到 URL
- [ ] 分类变更应同步到 URL
- [ ] 排序变更应同步到 URL
- [ ] 分页变更应同步到 URL
- [ ] 语言变更应同步到 URL

### 3. 浏览器功能测试
- [ ] 浏览器前进/后退应正确恢复状态
- [ ] URL 分享后应能正确打开相同状态
- [ ] 刷新页面应保持当前状态

### 4. 防抖测试
- [ ] 快速输入搜索关键词时，URL 不应频繁更新
- [ ] 停止输入 300ms 后，URL 应更新

## 注意事项

1. **空字符串处理**：`category=''` 表示"全部"，会保留在 URL 中
2. **URL 编码**：中文等特殊字符会自动编码/解码
3. **默认值**：URL 中不存在的参数使用组件默认值，不写入 URL
4. **历史记录**：默认使用 `replace: false`，保留浏览器历史

## 文件清单

### 新增文件
- `src/hooks/useURLState.ts` - URL 状态管理 Hook
- `src/hooks/useDebounce.ts` - 防抖 Hook
- `src/types/urlState.ts` - URL 状态类型定义
- `src/enums/display/lang.ts` - 语言代码枚举

### 修改文件
- `src/pages/ItemsListPage.tsx` - 重构使用 URL 状态管理
- `src/components/CategorySelector.tsx` - 使用统一的状态管理
- `src/components/LanguageSelector.tsx` - 同步语言到 URL
- `src/App.tsx` - 优先从 URL 读取语言

## 下一步

1. **测试**：按照测试建议进行完整测试
2. **文档**：更新用户文档，说明 URL 参数格式
3. **扩展**：根据需求添加新的筛选选项（价格、品牌等）
