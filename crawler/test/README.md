# 测试说明

## 测试用例

### test_completeness.py - 字段完整性测试

验证yaml配置中定义的字段在指定比例以上的记录中都存在且满足检查标准。

#### 功能说明

1. **加载测试配置**：从 `test_config.yaml` 读取每个profile的测试URL列表和字段检查标准
2. **提取字段定义**：从profile的yaml配置中提取所有定义的字段
3. **执行抓取**：对每个测试URL执行实际的网页抓取和数据提取
4. **验证完整性**：根据配置的检查标准验证每个字段的完整性

#### 运行测试

```bash
# 安装依赖
pip install -r requirements.txt

# 运行所有测试
pytest test/

# 运行特定测试文件
pytest test/test_completeness.py

# 运行特定测试并显示详细输出
pytest test/test_completeness.py -v -s
```

#### 配置说明

编辑 `test_config.yaml` 文件，可以配置：

1. **默认配置**：为所有字段设置默认的检查标准和阈值
2. **字段级别配置**：为特定字段覆盖默认配置

##### 检查类型

- `0`: 任意非空内容 - 验证值不为None、空字符串、以及字符串"None"、"none"、"null"（不区分大小写）
- `1`: 数字 - 验证值是否为数字（支持int、float或可转换为数字的字符串）
- `2`: 非空字符串 - 验证值是否为非空字符串（去除空白后不为空）
- `3`: URL链接 - 验证值是否为有效的URL链接

##### 配置示例

```yaml
# 默认配置：所有字段的默认检查标准
defaults:
  type: 0  # 默认：任意非空内容
  threshold: 0.9  # 默认：90%

profiles:
  profile_name:
    urls:
      - https://example.com/page1
      - https://example.com/page2
    # 字段级别的检查标准（覆盖默认配置）
    fields:
      price_jpy:
        type: 1  # 数字
        threshold: 0.7  # 70%
      product_url:
        type: 3  # URL链接
        threshold: 0.95  # 95%
```

#### 测试标准

- **默认阈值**：90%（可在配置文件中修改）
- **默认类型**：任意非空内容（可在配置文件中修改）
- **字段级别配置**：可以为每个字段单独设置类型和阈值
- **空值定义**：None、空字符串""、字符串"None"、"none"、"null"（不区分大小写）都被视为空值

#### 测试失败时的输出

如果测试失败，会输出：
- 哪些字段不满足检查标准要求
- 每个字段的实际完整性百分比
- 每个字段的检查类型和要求的阈值
- 前3个items的字段示例，便于调试

