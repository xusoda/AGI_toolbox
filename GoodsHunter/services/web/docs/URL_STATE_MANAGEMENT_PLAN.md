# URL 状态管理实现方案

## 一、概述

本文档描述了 GoodsHunter Web 应用中基于 URL 的状态管理（URL-based State Management）实现方案。

### 核心目标

1. **URL-based State Management (基于 URL 的状态管理)**：将应用当前的搜索、筛选、分页等 UI 状态实时同步到 URL 中
2. **Deep Linking (深层链接)**：通过特定 URL 直接触达应用深度页面的能力
3. **URLs as UI / URLs as State Containers**：URL 作为用户界面的一部分，承载状态

## 二、当前状态分析

### 技术栈
- React 18.2.0
- React Router DOM 6.20.0
- TypeScript 5.3.3
- Vite 5.0.8

### 已实现功能
- ✅ `category` 参数已同步到 URL
- ✅ `page` 参数已同步到 URL
- ✅ CategorySelector 使用 React Router 的 `navigate` 更新 URL

### 待实现功能
- ❌ `searchQuery` (搜索关键词) 未同步到 URL
- ❌ `sort` (列表模式排序) 未同步到 URL
- ❌ `sortField` (搜索模式排序字段) 未同步到 URL
- ❌ `sortOrder` (搜索模式排序顺序) 未同步到 URL
- ❌ `isSearchMode` (搜索模式状态) 未同步到 URL
- ❌ 状态管理不统一，部分使用 `window.history.pushState`，部分使用 `navigate`

## 三、方案设计

### 3.1 URL 参数映射规则

| UI 状态 | URL 参数名 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| 搜索关键词 | `q` | string | 搜索查询字符串 | `?q=爱马仕` |
| 分类筛选 | `category` | string | 商品类别 | `?category=hermes` |
| 页码 | `page` | number | 当前页码 | `?page=2` |
| 列表排序 | `sort` | string | 列表模式排序选项 | `?sort=price_asc` |
| 搜索排序字段 | `sort_field` | string | 搜索模式排序字段 | `?sort_field=price` |
| 搜索排序顺序 | `sort_order` | string | 搜索模式排序顺序 | `?sort_order=asc` |

### 3.2 URL 结构示例

**列表模式（无搜索）**：
```
/?category=hermes&page=2&sort=price_asc
```

**搜索模式**：
```
/?q=爱马仕&category=hermes&page=1&sort_field=price&sort_order=asc
```

**深层链接示例**：
```
/?q=二手爱马仕&category=hermes&page=1&sort_field=price&sort_order=asc
```

### 3.3 架构设计

#### 3.3.1 基于 React Router 的 `useSearchParams`

**核心思路**：使用 React Router 6.20 提供的 `useSearchParams` Hook，而不是完全自定义实现。

React Router 的 `useSearchParams` 提供了：
- ✅ 自动同步 URL 查询参数
- ✅ 浏览器历史记录管理
- ✅ 深层链接支持
- ✅ 类型安全的参数访问

**封装 Hook: `useURLState`**

创建一个基于 `useSearchParams` 的封装 Hook，提供类型安全和便捷方法：

```typescript
// hooks/useURLState.ts
import { useSearchParams } from 'react-router-dom'

interface URLState {
  // 搜索相关
  q?: string
  // 筛选相关
  category?: string
  // 分页相关
  page?: number
  // 排序相关（列表模式）
  sort?: string
  // 排序相关（搜索模式）
  sort_field?: string
  sort_order?: string
}

function useURLState() {
  const [searchParams, setSearchParams] = useSearchParams()
  
  // 读取状态（从 URL）
  const getState = (): URLState => ({
    q: searchParams.get('q') || undefined,
    category: searchParams.get('category') || undefined,
    page: parseInt(searchParams.get('page') || '1'),
    sort: searchParams.get('sort') || undefined,
    sort_field: searchParams.get('sort_field') || undefined,
    sort_order: searchParams.get('sort_order') || undefined,
  })
  
  // 更新状态（同步到 URL）
  const updateState = (updates: Partial<URLState>, options?: { replace?: boolean }) => {
    const newParams = new URLSearchParams(searchParams)
    
    // 更新参数
    Object.entries(updates).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        newParams.delete(key)
      } else {
        newParams.set(key, String(value))
      }
    })
    
    setSearchParams(newParams, { replace: options?.replace ?? false })
  }
  
  return { getState, updateState, searchParams }
}
```

**优势**：
- 🎯 充分利用 React Router 框架能力
- 🔒 类型安全的状态管理
- 🚀 无需手动管理浏览器历史
- 📦 代码简洁，易于维护

#### 3.3.2 状态同步策略

1. **单向数据流**：URL → State → UI
2. **状态更新**：UI 操作 → 更新 URL → 触发 useEffect → 更新 State → 重新渲染
3. **防抖处理**：搜索关键词输入使用防抖，避免频繁更新 URL
4. **默认值处理**：URL 中不存在的参数使用默认值，不写入 URL

## 四、实现计划

### 阶段 1：创建基于 `useSearchParams` 的封装 Hook
- [ ] 创建 `src/hooks/useURLState.ts`
- [ ] 基于 `useSearchParams` 封装，提供类型安全的状态访问
- [ ] 实现便捷的 `getState` 和 `updateState` 方法
- [ ] 处理默认值和参数验证

### 阶段 2：定义类型定义
- [ ] 创建 `src/types/urlState.ts` 定义 URL 状态类型
- [ ] 确保类型与 API 参数类型一致

### 阶段 3：重构 ItemsListPage
- [ ] 使用 `useURLState` Hook 替换现有的 `useLocation` + `URLSearchParams`
- [ ] 移除手动的 `window.history.pushState` 调用
- [ ] 移除手动的 `URLSearchParams` 创建和解析
- [ ] 确保所有状态变更都通过 Hook 更新 URL
- [ ] 实现搜索关键词的防抖处理（使用 `useDebouncedCallback`）

### 阶段 4：更新 CategorySelector
- [ ] 统一使用 `useURLState` Hook
- [ ] 移除直接使用 `navigate` 的代码
- [ ] 使用 `updateState` 方法更新 category

### 阶段 5：测试和优化
- [ ] 测试深层链接功能
- [ ] 测试浏览器前进/后退功能
- [ ] 测试 URL 分享功能
- [ ] 性能优化（防抖、节流）

## 五、技术细节

### 5.1 URL 参数编码

- 中文搜索关键词使用 `encodeURIComponent` 编码
- 所有参数值都进行 URL 编码处理

### 5.2 状态同步时机

- **立即同步**：分类、排序、分页变更立即更新 URL
- **防抖同步**：搜索关键词输入使用 300ms 防抖
- **批量更新**：多个状态同时变更时，合并为一次 URL 更新

### 5.3 浏览器历史记录

- `useSearchParams` 的 `setSearchParams` 默认使用 `replace: false`，保留浏览器历史记录
- React Router 自动支持浏览器前进/后退功能
- 初始加载或批量更新时，可选择性使用 `replace: true`，避免在历史记录中留下过多条目

### 5.4 类型安全

- 使用 TypeScript 严格类型检查
- URL 参数值验证和类型转换
- 提供类型安全的参数访问接口

## 六、示例代码结构

```
src/
├── hooks/
│   └── useURLState.ts          # 基于 useSearchParams 的封装 Hook
├── types/
│   └── urlState.ts             # URL 状态类型定义
└── pages/
    └── ItemsListPage.tsx       # 使用 useURLState 的页面
```

### 6.1 使用示例

```typescript
// ItemsListPage.tsx
import { useURLState } from '../hooks/useURLState'
import { useDebouncedCallback } from 'use-debounce' // 需要安装 use-debounce

function ItemsListPage() {
  const { getState, updateState } = useURLState()
  const state = getState()
  
  // 防抖更新搜索关键词
  const debouncedUpdateSearch = useDebouncedCallback((q: string) => {
    updateState({ q, page: 1 }, { replace: false })
  }, 300)
  
  // 立即更新其他状态
  const handleCategoryChange = (category: string) => {
    updateState({ category, page: 1 }, { replace: false })
  }
  
  const handlePageChange = (page: number) => {
    updateState({ page }, { replace: false })
  }
  
  // 使用 state.q, state.category, state.page 等
}
```

## 七、测试用例

### 7.1 深层链接测试
- [ ] 直接访问 `/?q=爱马仕&category=hermes&page=1` 应正确显示搜索结果
- [ ] 直接访问 `/?category=hermes&sort=price_asc&page=2` 应正确显示筛选和排序结果

### 7.2 状态同步测试
- [ ] 搜索关键词变更应同步到 URL
- [ ] 分类变更应同步到 URL
- [ ] 排序变更应同步到 URL
- [ ] 分页变更应同步到 URL

### 7.3 浏览器功能测试
- [ ] 浏览器前进/后退应正确恢复状态
- [ ] URL 分享后应能正确打开相同状态
- [ ] 刷新页面应保持当前状态

## 八、技术选型说明

### 8.1 为什么使用 `useSearchParams` 而不是自定义实现？

✅ **框架原生支持**：React Router 6.20 已提供完善的 URL 状态管理能力  
✅ **自动历史管理**：无需手动处理浏览器历史记录  
✅ **深层链接支持**：框架自动处理 URL 变化和组件更新  
✅ **代码简洁**：减少自定义代码，降低维护成本  
✅ **社区标准**：使用框架推荐的方式，便于团队协作  

### 8.2 为什么需要封装 Hook？

虽然可以直接使用 `useSearchParams`，但封装 Hook 可以：
- 🔒 提供类型安全的状态访问
- 🎯 统一状态更新逻辑
- 🛠️ 处理默认值和参数验证
- 📝 简化组件代码

## 九、注意事项

1. **性能考虑**：避免频繁的 URL 更新导致性能问题（使用防抖）
2. **SEO 友好**：URL 参数应保持语义化，便于搜索引擎理解
3. **用户体验**：URL 应保持简洁，避免过长
4. **向后兼容**：考虑旧版本 URL 的兼容性处理
5. **依赖安装**：如需防抖功能，需要安装 `use-debounce` 或使用自定义防抖 Hook

## 十、后续优化

1. **URL 压缩**：对于复杂状态，考虑使用压缩算法
2. **状态持久化**：结合 localStorage 实现状态持久化
3. **状态验证**：添加 URL 参数验证和错误处理
4. **状态迁移**：提供 URL 参数版本管理机制
