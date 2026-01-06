# MVP Scraper Plan

## 目标（MVP范围）
1. 输入一批 URL（命令行或文件）
2. 根据 URL 匹配到对应 Profile（可配置）
3. 使用 Playwright 抓取页面 HTML（支持最基本的 goto/wait）
4. 根据 Profile 的字段策略链，结构化抽取字段（JSON-LD / XPath / Regex）
5. 输出 JSONL：每行一个 Record（包含 data 与 field-level errors）

## 非目标（MVP不做）
- 队列调度、分布式 worker
- 监控指标、告警
- 回归测试、黄金样本
- 反爬对抗（代理池、验证码处理、复杂登录）
- 浏览器交互编排（点击/滚动/分页）——仅预留配置字段

## 技术栈
- Python 3.10+
- Playwright（浏览器抓取）：playwright.async_api
- HTML解析：lxml（XPath）
- JSON-LD解析：json + regex（script[type=application/ld+json]）
- 配置：PyYAML
- 输出：JSONL（标准库 json）

## 安装与运行
1) 安装依赖：
- pip install playwright lxml pyyaml
- playwright install

2) 运行示例：
- python -m app.run --urls urls.txt --out results.jsonl

## 配置（profiles/profiles.yaml）
- 通过新增/修改 profile 来支持新站点或新页面类型
- 每个 profile 定义：
  - match: domains / url_regex / priority
  - fetch: wait_until / timeout_ms / user_agent
  - fields: 字段 -> 策略链（按顺序回退）
  - 可选：plugin（MVP不实现，仅预留）

## 迭代策略（推荐实践）
1) 优先用 JSON-LD 或内嵌 JSON（若站点提供），稳定性最好
2) XPath 作为通用兜底
3) Regex 仅做最后兜底（价格/日期等）

## 后续演进（不破坏现有接口）
Phase 1: 增加 fetch.actions（滚动/点击/等待 selector）与 browser context 复用
Phase 2: 增加并发（async gather + semaphore），输出仍是 Record JSONL
Phase 3: 引入队列/worker，run.py 变为 producer/consumer，但 fetch/extract/core 不变
Phase 4: 增加回归测试：保存 HTML 快照，直接喂给 extract.engine 进行离线对比


MVP版本目录结构：
crawler/
  Plan.md
  pyproject.toml                 # 可选：依赖声明（也可用 requirements.txt）

  app/
    run.py                       # CLI入口：批量URL -> 结果JSONL

  core/
    types.py                     # Page / Profile / Record / StrategySpec
    registry.py                  # 加载profiles.yaml + URL匹配

  fetch/
    playwright_fetcher.py        # Playwright抓取：返回Page

  extract/
    engine.py                    # 字段抽取策略链执行
    strategies/
      jsonld.py                  # JSON-LD抽取
      xpath.py                   # XPath抽取
      regex.py                   # Regex抽取

  profiles/
    profiles.yaml                # 多Profile配置（核心迭代点）

  output/
    writer.py                    # JSONL输出
