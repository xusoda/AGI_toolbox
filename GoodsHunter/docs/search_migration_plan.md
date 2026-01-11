# 搜索架构迁移方案：PostgreSQL → Elasticsearch + 多语言搜索支持

## 一、概述

### 1.1 目标
1. 将搜索框架从 PostgreSQL 全文搜索迁移到 Elasticsearch
2. 实现多语言搜索支持（跨语言搜索，如"劳力士" vs "rolex"）
3. 支持词表动态更新，搜索能力随词表优化自动提升

### 1.2 核心问题
- **问题1**：数据库存储为单一语言（如"劳力士"），搜索其他语言（如"rolex"）无法匹配
- **问题2**：词表映射（`i18n/dictionaries/watch.yaml`）可以更新，但搜索索引无法自动更新
- **问题3**：PostgreSQL 全文搜索对中文支持有限，多语言搜索能力不足

## 二、架构设计

### 2.1 新架构模块

```
search/
├── engine.py                  # 搜索引擎抽象接口（保持不变）
├── es_engine.py              # Elasticsearch 搜索引擎实现（需实现）
├── es_engine.py              # Elasticsearch 搜索引擎实现
├── data_manager.py           # 搜索数据管理器（需增强）
├── service.py                # 搜索服务层（保持不变）
├── i18n/                     # 多语言搜索模块（新增）
│   ├── __init__.py
│   ├── query_expander.py     # 查询扩展器（将查询词扩展为多语言同义词）
│   ├── alias_resolver.py     # 别名解析器（基于词表解析别名）
│   └── index_builder.py      # 索引构建器（构建包含多语言同义词的索引）
└── sync/                     # 数据同步模块（新增）
    ├── __init__.py
    ├── index_syncer.py       # 索引同步器（从数据库同步到ES）
    └── alias_updater.py      # 别名更新器（词表更新时更新索引）
```

### 2.2 核心设计理念

#### 2.2.1 多语言搜索策略：同义词扩展

**方案1：查询时扩展（Query-time Expansion）**
- 用户在搜索框输入"rolex"
- 查询扩展器通过词表查找"rolex"的同义词：["rolex", "劳力士", "ロレックス"]
- ES 使用这些同义词进行搜索

**方案2：索引时扩展（Index-time Expansion）**
- 索引商品时，将"劳力士"扩展为：["劳力士", "rolex", "ロレックス", "ROLEX"]
- 搜索时直接搜索，无需扩展查询

**推荐方案：混合策略**
- **索引时扩展**：在索引中存储多语言同义词数组
- **查询时扩展**：对于未知查询词，尝试在查询时扩展
- **优势**：索引时扩展性能更好，查询时扩展可以处理新词

#### 2.2.2 词表更新处理

**触发机制**：
1. **手动触发**：提供脚本/API，手动触发索引重建
2. **自动触发**：监听词表文件变更，自动触发增量更新
3. **定时任务**：定时检查词表变更，批量更新

**更新策略**：
1. **全量重建**：词表变更较多时，全量重建索引（可以后台运行，不影响搜索）
2. **增量更新**：仅更新受影响的商品（基于词表变更范围）
3. **混合更新**：小变更增量更新，大变更全量重建

### 2.3 Elasticsearch 索引设计

#### 2.3.1 索引结构（products）

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "brand_name": {
        "type": "text",
        "analyzer": "ik_max_word",  // 中文分词（需要安装IK插件）
        "fields": {
          "keyword": { "type": "keyword" },
          "aliases": { 
            "type": "text",
            "analyzer": "ik_max_word"  // 存储品牌的多语言别名
          }
        }
      },
      "model_name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
          "keyword": { "type": "keyword" },
          "aliases": {
            "type": "text",
            "analyzer": "ik_max_word"  // 存储型号的多语言别名
          }
        }
      },
      "model_no": {
        "type": "keyword",
        "fields": {
          "text": { "type": "text", "analyzer": "standard" }
        }
      },
      "brand_aliases": {  // 新增：品牌别名数组（用于多语言搜索）
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "model_aliases": {  // 新增：型号别名数组（用于多语言搜索）
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "search_text": {  // 新增：合并的搜索文本（包含所有同义词）
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "price": { "type": "integer" },
      "currency": { "type": "keyword" },
      "site": { "type": "keyword" },
      "category": { "type": "keyword" },
      "status": { "type": "keyword" },
      "last_seen_dt": { "type": "date" },
      "created_at": { "type": "date" },
      "image_thumb_300_key": { "type": "keyword" },
      "product_url": { "type": "keyword" }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "ik_max_word": {
          "type": "ik_max_word"  // 需要安装IK分词插件
        }
      }
    },
    "number_of_shards": 1,
    "number_of_replicas": 0  // 开发环境，生产环境建议1
  }
}
```

#### 2.3.2 文档示例

```json
{
  "id": 123,
  "brand_name": "Rolex",
  "model_name": "Submariner",
  "model_no": "116610LN",
  "brand_aliases": ["Rolex", "rolex", "劳力士", "ロレックス", "ROLEX"],  // 从词表扩展
  "model_aliases": ["Submariner", "潜航者", "サブマリナー", "サブマリーナー"],
  "search_text": "Rolex rolex 劳力士 ロレックス ROLEX Submariner 潜航者 サブマリナー サブマリーナー 116610LN",
  "price": 1000000,
  "currency": "JPY",
  "site": "commit-watch.co.jp",
  "category": "watch",
  "status": "active",
  "last_seen_dt": "2024-01-15",
  "created_at": "2024-01-01T00:00:00Z",
  "image_thumb_300_key": "watchnian/gik-00-0702136.jpg",
  "product_url": "https://..."
}
```

### 2.4 查询设计

#### 2.4.1 搜索查询（multi_match + bool）

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "rolex",
            "fields": ["brand_name^3", "brand_aliases^2", "model_name^2", "model_aliases^1.5", "search_text^1"],
            "type": "best_fields",
            "operator": "or"
          }
        },
        {
          "match": {
            "brand_name": {
              "query": "rolex",
              "boost": 3
            }
          }
        },
        {
          "match": {
            "model_no": {
              "query": "rolex"
            }
          }
        }
      ],
      "minimum_should_match": 1,
      "filter": [
        { "term": { "status": "active" } },
        { "range": { "price": { "gte": 1000 } } }
      ]
    }
  },
  "sort": [
    { "last_seen_dt": { "order": "desc" } },
    { "_score": { "order": "desc" } }
  ]
}
```

#### 2.4.2 搜索建议（completion suggester）

```json
{
  "suggest": {
    "product_suggest": {
      "prefix": "rol",
      "completion": {
        "field": "brand_name_suggest",
        "size": 5
      }
    }
  }
}
```

## 三、实现模块

### 3.1 search/i18n/alias_resolver.py（新增）

**职责**：基于词表解析别名

```python
"""别名解析器：基于词表解析品牌/型号别名"""
from typing import List, Dict, Optional
from i18n.translation.loader import DictionaryLoader

class AliasResolver:
    """别名解析器，负责从词表中获取同义词"""
    
    @staticmethod
    def get_brand_aliases(brand_name: str, category: str = "watch") -> List[str]:
        """
        获取品牌的别名列表（包含原始名称和所有同义词）
        
        Args:
            brand_name: 标准品牌名
            category: 商品类别
            
        Returns:
            别名列表，包含原始名称和所有同义词
        """
        aliases_map = DictionaryLoader.get_brand_aliases(category)
        aliases = aliases_map.get(brand_name, [])
        # 返回原始名称 + 所有别名（去重，不区分大小写）
        result = [brand_name] + aliases
        # 去重（忽略大小写）
        seen = set()
        unique_result = []
        for alias in result:
            alias_lower = alias.lower()
            if alias_lower not in seen:
                seen.add(alias_lower)
                unique_result.append(alias)
        return unique_result
    
    @staticmethod
    def get_model_aliases(
        brand_name: str, 
        model_name: str, 
        category: str = "watch"
    ) -> List[str]:
        """
        获取型号的别名列表
        
        Args:
            brand_name: 标准品牌名
            model_name: 标准型号名
            category: 商品类别
            
        Returns:
            别名列表
        """
        aliases_map = DictionaryLoader.get_model_aliases(brand_name, category)
        aliases = aliases_map.get(model_name, [])
        result = [model_name] + aliases
        # 去重
        seen = set()
        unique_result = []
        for alias in result:
            alias_lower = alias.lower()
            if alias_lower not in seen:
                seen.add(alias_lower)
                unique_result.append(alias)
        return unique_result
```

### 3.2 search/i18n/index_builder.py（新增）

**职责**：构建包含多语言同义词的索引文档

```python
"""索引构建器：构建包含多语言同义词的ES文档"""
from typing import Dict, Any
from search.i18n.alias_resolver import AliasResolver

class IndexBuilder:
    """索引构建器，负责构建ES索引文档"""
    
    @staticmethod
    def build_document(item_data: Dict[str, Any], category: str = "watch") -> Dict[str, Any]:
        """
        构建ES索引文档（包含多语言同义词）
        
        Args:
            item_data: 商品数据（来自数据库）
            category: 商品类别
            
        Returns:
            ES文档
        """
        brand_name = item_data.get("brand_name", "")
        model_name = item_data.get("model_name", "")
        model_no = item_data.get("model_no", "")
        
        # 获取别名
        brand_aliases = AliasResolver.get_brand_aliases(brand_name, category)
        model_aliases = AliasResolver.get_model_aliases(brand_name, model_name, category)
        
        # 构建搜索文本（合并所有同义词）
        search_text_parts = brand_aliases + model_aliases
        if model_no:
            search_text_parts.append(model_no)
        search_text = " ".join(search_text_parts)
        
        # 构建ES文档
        doc = {
            "id": item_data.get("id"),
            "brand_name": brand_name,
            "model_name": model_name,
            "model_no": model_no,
            "brand_aliases": brand_aliases,
            "model_aliases": model_aliases,
            "search_text": search_text,
            "price": item_data.get("price"),
            "currency": item_data.get("currency"),
            "site": item_data.get("site"),
            "category": category or item_data.get("category"),
            "status": item_data.get("status"),
            "last_seen_dt": item_data.get("last_seen_dt"),
            "created_at": item_data.get("created_at"),
            "image_thumb_300_key": item_data.get("image_thumb_300_key"),
            "product_url": item_data.get("product_url"),
        }
        
        return doc
```

### 3.3 search/es_engine.py（需实现）

**职责**：实现 Elasticsearch 搜索引擎

```python
"""Elasticsearch 搜索引擎实现"""
from typing import Dict, List, Optional, Any
from elasticsearch import Elasticsearch
from search.engine import SearchEngine, SearchResult, SearchFilters, SortOption
from search.i18n.index_builder import IndexBuilder

class ElasticsearchSearchEngine(SearchEngine):
    """Elasticsearch 搜索引擎实现"""
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        index_name: str = "products",
        category: str = "watch"
    ):
        self.es_client = Elasticsearch([f"{es_host}:{es_port}"])
        self.index_name = index_name
        self.category = category
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """确保索引存在，如果不存在则创建"""
        # 实现索引创建逻辑
        pass
    
    def search(self, query: str, filters: Optional[SearchFilters] = None, ...) -> SearchResult:
        """执行搜索（支持多语言）"""
        # 使用 multi_match 在 brand_name, brand_aliases, model_name, model_aliases, search_text 中搜索
        pass
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """索引文档（使用 IndexBuilder 构建）"""
        es_doc = IndexBuilder.build_document(document, self.category)
        # 使用 ES client 索引文档
        pass
```

### 3.4 search/sync/index_syncer.py（新增）

**职责**：从数据库同步数据到ES

```python
"""索引同步器：从数据库同步到ES"""
from typing import Optional, List
from sqlalchemy.orm import Session
from search.es_engine import ElasticsearchSearchEngine
from search.data_manager import SearchDataManager

class IndexSyncer:
    """索引同步器，负责从数据库同步到ES"""
    
    def __init__(self, es_engine: ElasticsearchSearchEngine):
        self.es_engine = es_engine
        self.data_manager = SearchDataManager(es_engine)
    
    def sync_all(self, session: Session, batch_size: int = 100) -> int:
        """全量同步所有商品"""
        return self.data_manager.sync_from_database(session, batch_size)
    
    def sync_items(self, session: Session, item_ids: List[int]) -> int:
        """同步指定的商品"""
        return self.data_manager.sync_from_database(session, item_ids=item_ids)
    
    def sync_incremental(self, session: Session, last_sync_time: Optional[str] = None) -> int:
        """增量同步（基于最后同步时间）"""
        # 实现增量同步逻辑
        pass
```

### 3.5 search/sync/alias_updater.py（新增）

**职责**：词表更新时更新索引

```python
"""别名更新器：词表更新时更新索引"""
from typing import List, Optional
from sqlalchemy.orm import Session
from search.es_engine import ElasticsearchSearchEngine
from search.sync.index_syncer import IndexSyncer

class AliasUpdater:
    """别名更新器，负责在词表更新时更新索引"""
    
    def __init__(self, es_engine: ElasticsearchSearchEngine):
        self.es_engine = es_engine
        self.index_syncer = IndexSyncer(es_engine)
    
    def update_affected_items(
        self,
        session: Session,
        updated_brands: Optional[List[str]] = None,
        updated_models: Optional[Dict[str, List[str]]] = None  # {brand: [models]}
    ) -> int:
        """
        更新受影响的商品（增量更新）
        
        Args:
            session: 数据库会话
            updated_brands: 更新的品牌列表
            updated_models: 更新的型号字典 {brand: [models]}
        
        Returns:
            更新的商品数量
        """
        # 查询受影响的商品ID
        affected_item_ids = self._find_affected_items(session, updated_brands, updated_models)
        
        # 重新索引这些商品
        return self.index_syncer.sync_items(session, affected_item_ids)
    
    def rebuild_all(self, session: Session) -> int:
        """全量重建索引"""
        return self.index_syncer.sync_all(session)
    
    def _find_affected_items(
        self,
        session: Session,
        updated_brands: Optional[List[str]],
        updated_models: Optional[Dict[str, List[str]]]
    ) -> List[int]:
        """查找受影响的商品ID"""
        # 实现查询逻辑
        pass
```

## 四、迁移步骤

### 阶段1：环境准备

#### 步骤1.1：添加 Elasticsearch 到 docker-compose.yml

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: goodshunter-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false  # 开发环境禁用安全
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - goodshunter-network

  # 如果需要中文分词，可以添加IK插件（通过自定义镜像）
  # 或者使用 elasticsearch-analysis-ik 插件

volumes:
  es_data:
```

#### 步骤1.2：安装 Python 依赖

在 `requirements.txt` 中添加：
```
elasticsearch>=8.11.0
```

#### 步骤1.3：安装 IK 分词插件（可选，用于中文分词）

如果使用中文搜索，需要安装 IK 分词插件。可以通过以下方式：
1. 使用包含 IK 插件的镜像（如 `elasticsearch-ik:8.11.0`）
2. 或者在容器启动后安装插件

### 阶段2：实现核心模块

#### 步骤2.1：实现 `search/i18n/alias_resolver.py`
- 基于 `DictionaryLoader` 获取别名
- 实现别名解析逻辑

#### 步骤2.2：实现 `search/i18n/index_builder.py`
- 使用 `AliasResolver` 获取别名
- 构建包含多语言同义词的ES文档

#### 步骤2.3：实现 `search/es_engine.py`
- 实现 `SearchEngine` 接口
- 实现索引创建、搜索、建议等功能
- 支持多语言搜索（使用 multi_match）

#### 步骤2.4：实现 `search/sync/index_syncer.py`
- 实现全量同步、增量同步功能

#### 步骤2.5：实现 `search/sync/alias_updater.py`
- 实现词表更新时的索引更新逻辑

### 阶段3：数据迁移

#### 步骤3.1：创建ES索引

提供脚本 `search/scripts/create_index.py`：
```python
"""创建ES索引"""
from search.es_engine import ElasticsearchSearchEngine

def create_index():
    es_engine = ElasticsearchSearchEngine()
    es_engine._ensure_index_exists()
    print("索引创建成功")

if __name__ == "__main__":
    create_index()
```

#### 步骤3.2：全量数据同步

提供脚本 `search/scripts/sync_all_data.py`：
```python
"""全量同步数据到ES"""
from sqlalchemy.orm import Session
from app.db.session import get_db
from search.es_engine import ElasticsearchSearchEngine
from search.sync.index_syncer import IndexSyncer

def sync_all():
    es_engine = ElasticsearchSearchEngine()
    syncer = IndexSyncer(es_engine)
    
    db = next(get_db())
    try:
        count = syncer.sync_all(db, batch_size=100)
        print(f"同步完成，共同步 {count} 个商品")
    finally:
        db.close()

if __name__ == "__main__":
    sync_all()
```

### 阶段4：API层切换

#### 步骤4.1：修改 API 路由（`services/api/app/routers/search.py`）

```python
# 使用Elasticsearch搜索引擎
from search.es_engine import ElasticsearchSearchEngine

search_engine = ElasticsearchSearchEngine(
    es_host=settings.ES_HOST,  # 从环境变量读取
    es_port=settings.ES_PORT,
    index_name=settings.ES_INDEX_NAME
)
```

#### 步骤4.2：添加环境变量配置（`services/api/app/settings.py`）

```python
ES_HOST: str = os.getenv("ES_HOST", "localhost")
ES_PORT: int = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME: str = os.getenv("ES_INDEX_NAME", "products")
```

#### 步骤4.3：更新 docker-compose.yml（API服务依赖ES）

```yaml
api:
  environment:
    ES_HOST: elasticsearch
    ES_PORT: 9200
    ES_INDEX_NAME: products
  depends_on:
    elasticsearch:
      condition: service_healthy
```

### 阶段5：词表更新机制

#### 步骤5.1：提供手动更新脚本

`search/scripts/update_aliases.py`：
```python
"""更新词表后，更新ES索引"""
from sqlalchemy.orm import Session
from app.db.session import get_db
from search.es_engine import ElasticsearchSearchEngine
from search.sync.alias_updater import AliasUpdater

def update_aliases(rebuild_all: bool = False):
    es_engine = ElasticsearchSearchEngine()
    updater = AliasUpdater(es_engine)
    
    db = next(get_db())
    try:
        if rebuild_all:
            count = updater.rebuild_all(db)
            print(f"全量重建完成，更新 {count} 个商品")
        else:
            # 增量更新（需要传入变更的品牌/型号）
            # 这里简化处理，实际可以解析词表变更
            count = updater.update_affected_items(db)
            print(f"增量更新完成，更新 {count} 个商品")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    rebuild_all = "--rebuild-all" in sys.argv
    update_aliases(rebuild_all)
```

#### 步骤5.2：提供API端点（可选）

在 `services/api/app/routers/search.py` 中添加：
```python
@router.post("/search/reindex")
async def reindex_all(db: Session = Depends(get_db)):
    """手动触发全量重建索引"""
    # 实现重建逻辑
    pass
```

### 阶段6：测试和验证

#### 步骤6.1：功能测试
- 测试多语言搜索（如搜索"rolex"可以找到"劳力士"）
- 测试词表更新后的搜索能力
- 测试搜索建议功能

#### 步骤6.2：性能测试
- 对比 PostgreSQL 和 ES 的搜索性能
- 测试并发搜索性能

#### 步骤6.3：数据一致性测试
- 验证 ES 索引与数据库数据的一致性

### 阶段7：部署和监控

#### 步骤7.1：生产环境配置
- 配置 ES 集群（如果需要）
- 配置 IK 分词插件
- 配置索引分片和副本

#### 步骤7.2：监控和告警
- 监控 ES 集群状态
- 监控索引同步状态
- 设置告警规则

## 五、架构文档更新

### 5.1 `docs/architecture/architecture.md` 修改点

1. **更新 Search 模块章节**：
   - 添加 ES 搜索引擎说明
   - 添加多语言搜索模块说明
   - 添加数据同步模块说明

2. **更新模块依赖关系图**：
   - 添加 Elasticsearch 服务
   - 更新 Search 模块依赖

3. **更新数据流图**：
   - 添加 ES 索引同步流程
   - 添加词表更新流程

## 六、回退方案

### 6.1 双写策略（可选）
- 在迁移期间，同时写入 PostgreSQL 和 ES
- 可以通过配置开关切换搜索引擎

### 6.2 回退策略
- 已完全迁移到 Elasticsearch，不再使用 PostgreSQL 作为搜索引擎
- 如果 ES 不可用，需要修复 ES 服务或使用备用 ES 集群

## 七、注意事项

1. **数据一致性**：
   - ES 索引与数据库数据可能存在延迟
   - 需要考虑数据同步策略（实时同步 vs 批量同步）

2. **性能优化**：
   - ES 索引需要定期优化（force merge）
   - 需要考虑索引大小和分片策略

3. **词表更新频率**：
   - 词表更新频率低时，可以手动触发更新
   - 词表更新频率高时，需要考虑自动化机制

4. **中文分词**：
   - 建议安装 IK 分词插件以获得更好的中文搜索效果
   - 如果没有 IK 插件，可以使用 ES 的 standard 分析器

5. **索引重建**：
   - 全量重建索引可能耗时较长
   - 可以考虑使用别名（aliases）实现零停机重建
