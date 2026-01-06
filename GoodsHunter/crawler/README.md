# 网页抓取和内容解析工具

基于 Playwright 的网页抓取和结构化内容抽取工具。

## 功能特性

- 支持批量URL处理
- 基于Profile的灵活配置
- 多种抽取策略（JSON-LD、XPath、正则表达式）
- 策略链回退机制
- JSONL格式输出

## 安装

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 安装Playwright浏览器：
```bash
playwright install
```

## 使用方法

### 基本用法

```bash
# 从文件读取URL列表
python -m app.run --urls urls.txt --out results.jsonl

# 处理单个URL
python -m app.run --urls "https://example.com" --out results.jsonl

# 指定自定义Profile配置
python -m app.run --urls urls.txt --out results.jsonl --profiles custom_profiles.yaml
```

### URL文件格式

创建 `urls.txt` 文件，每行一个URL：

```
https://example.com/page1
https://example.com/page2
# 这是注释，会被忽略
https://example.com/page3
```

### Profile配置

编辑 `profiles/profiles.yaml` 来定义不同站点的抽取规则。每个Profile包含：

- `match`: URL匹配规则（域名或正则表达式）
- `fetch`: 抓取配置（等待条件、超时等）
- `fields`: 字段抽取策略链

详细配置示例请参考 `profiles/profiles.yaml`。

## 目录结构

```
crawler/
  app/
    run.py              # CLI入口
  core/
    types.py            # 核心类型定义
    registry.py         # Profile注册表
  fetch/
    playwright_fetcher.py  # Playwright抓取器
  extract/
    engine.py          # 抽取引擎
    strategies/
      jsonld.py        # JSON-LD策略
      xpath.py         # XPath策略
      regex.py         # 正则表达式策略
  output/
    writer.py          # JSONL输出
  profiles/
    profiles.yaml      # Profile配置
```

## 输出格式

输出为JSONL格式，每行一个JSON对象：

```json
{"url": "https://example.com", "data": {"title": "示例标题", "price": "99.99"}, "errors": []}
```

- `url`: 处理的URL
- `data`: 成功抽取的字段数据
- `errors`: 字段级别的错误信息

