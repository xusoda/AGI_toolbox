# 翻译功能故障排查指南

## 问题：切换语言后显示没有改变

### 可能的原因和解决方案

#### 1. **服务需要重启**
如果修改了后端代码，需要重启 API 服务才能生效。

```bash
# 停止当前服务
# 然后重新启动
cd services/api
python -m uvicorn app.main:app --reload
```

#### 2. **检查数据库中的翻译数据**

运行以下 SQL 查询检查翻译数据是否存在：

```sql
-- 检查品牌翻译
SELECT brand_name, translations FROM brand_translations LIMIT 5;

-- 检查型号翻译
SELECT brand_name, model_name, translations FROM model_name_translations LIMIT 5;
```

确保 `translations` 字段包含目标语言的翻译，例如：
```json
{"en": "Rolex", "zh": "劳力士", "ja": "ロレックス"}
```

#### 3. **测试翻译功能**

运行测试脚本验证翻译是否正常工作：

```bash
export DATABASE_URL="postgresql://user:password@host:port/dbname"
python i18n/scripts/test_translation.py
```

#### 4. **检查 API 日志**

查看 API 服务的日志输出，应该能看到调试信息：
```
[DEBUG] 翻译: brand=Rolex -> 劳力士, model=Daytona -> 迪通拿
```

如果没有看到这些日志，说明：
- 翻译映射器初始化失败
- 或者 lang 参数没有正确传递

#### 5. **检查前端请求**

在浏览器开发者工具中检查网络请求：
- 请求 URL 应该包含 `lang=zh` 或 `lang=ja` 参数
- 响应中应该包含 `brand_name_translated` 和 `model_name_translated` 字段

#### 6. **常见问题**

**问题：翻译返回 None**
- 原因：数据库中没有对应的翻译数据
- 解决：运行 `init_translations.py` 初始化翻译数据

**问题：翻译后的值和原始值相同**
- 原因：翻译表中可能只有英文值，没有其他语言的翻译
- 解决：检查 `init_translations.py` 是否正确识别了日文/中文字符

**问题：JSONB 字段解析错误**
- 原因：PostgreSQL JSONB 字段在不同驱动中的处理方式不同
- 解决：已修复 `mapper.py` 中的 JSONB 处理逻辑

### 调试步骤

1. **确认翻译数据存在**：
   ```sql
   SELECT brand_name, translations->>'zh' as zh_translation 
   FROM brand_translations 
   WHERE brand_name = 'Rolex';
   ```

2. **测试翻译函数**：
   ```python
   from i18n.translation.mapper import TranslationMapper
   mapper = TranslationMapper()
   result = mapper.translate_brand("Rolex", "zh")
   print(result)  # 应该输出 "劳力士"
   ```

3. **检查 API 响应**：
   访问 `http://localhost:8000/api/items?lang=zh&page=1`
   检查响应中的 `brand_name_translated` 字段

4. **检查前端代码**：
   确认 `ItemsListPage.tsx` 中正确使用了 `i18n.language` 作为 lang 参数

### 修复记录

已修复的问题：
1. ✅ JSONB 字段处理：现在可以正确处理 PostgreSQL JSONB 字段（自动解析或手动解析）
2. ✅ 翻译逻辑：只有当翻译后的值确实不同时才返回翻译值
3. ✅ 调试信息：添加了调试日志，方便排查问题
4. ✅ 错误处理：改进了异常处理和日志输出

