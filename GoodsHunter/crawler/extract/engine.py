"""字段抽取引擎：执行策略链，支持新旧两种格式"""
from typing import Dict, Any, List, Optional
from lxml import html

# 尝试导入 cssselect，如果不可用则使用 XPath 回退
try:
    from lxml import cssselect
    CSSSELECT_AVAILABLE = True
except ImportError:
    CSSSELECT_AVAILABLE = False

from core.types import Page, Profile, Record, FieldError, StrategyType
from extract.strategies.jsonld import JSONLDStrategy
from extract.strategies.xpath import XPathStrategy
from extract.strategies.regex import RegexStrategy
from extract.transforms import TransformProcessor
from extract.parse_tool import ParseTool


def _css_has_to_xpath(selector: str) -> str:
    """
    将包含 :has() 的 CSS selector 转换为 XPath
    简单实现：将 :has(selector) 转换为 [.//selector]
    """
    import re
    
    # 匹配 :has(...) 模式
    def replace_has(match):
        has_content = match.group(1)
        # 简化处理：将 :has(a[href*='/products/']) 转换为 [.//a[contains(@href, '/products/')]]
        # 这里需要更复杂的解析，但先做简单替换
        xpath_condition = has_content.replace('*=', 'contains(@').replace(']', ', \'') + '\')]'
        return f"[.//{xpath_condition}]"
    
    # 简单替换 :has() 为 XPath
    if ':has(' in selector:
        # 对于复杂情况，先尝试简单的 XPath 转换
        # main li:has(a[href*='/products/']) -> //main//li[.//a[contains(@href, '/products/')]]
        xpath = selector
        
        # 替换标签选择器
        xpath = re.sub(r'(\w+)\s*:', r'//\1', xpath)
        xpath = xpath.replace('main', '//main')
        
        # 处理 :has() - 简化版本
        if ':has(a[href*=' in xpath:
            xpath = xpath.replace(':has(a[href*=\'', '[.//a[contains(@href, \'')
            xpath = xpath.replace('\'])', '\')]')
        elif ':has(' in xpath:
            # 通用处理：移除 :has() 并添加条件
            xpath = re.sub(r':has\(([^)]+)\)', r'[.//\1]', xpath)
        
        return xpath
    
    return selector


class ExtractEngine:
    """抽取引擎"""

    def __init__(self):
        """初始化引擎，注册策略"""
        self.strategies = {
            StrategyType.JSONLD: JSONLDStrategy.extract,
            StrategyType.XPATH: XPathStrategy.extract,
            StrategyType.REGEX: RegexStrategy.extract,
        }

    def extract(self, page: Page, profile: Profile) -> Record:
        """
        根据Profile抽取页面字段
        
        Args:
            page: 页面对象
            profile: 配置Profile
            
        Returns:
            Record对象，包含抽取的数据和错误信息
        """
        print(f"[ExtractEngine] 开始提取，URL: {page.url}")
        print(f"[ExtractEngine] Profile: {profile.name}")
        
        record = Record(url=page.url, status_code=page.status_code)
        data = {}
        errors = []

        # 支持新格式（parse配置）
        if profile.parse:
            print(f"[ExtractEngine] 使用新格式，parse.type: {profile.parse.type}")
            print(f"[ExtractEngine] 字段数量: {len(profile.parse.fields)}")
            for field_name in profile.parse.fields.keys():
                print(f"[ExtractEngine]   - 字段: {field_name}")
            
            if profile.parse.type == "list":
                # 列表提取
                print(f"[ExtractEngine] 开始列表提取...")
                # 传递页面资源（如果可用）
                page_resources = page.resources if hasattr(page, 'resources') and page.resources else None
                items = self._extract_list(page, profile.parse, profile, page_resources)
                print(f"[ExtractEngine] 列表提取完成，找到 {len(items)} 个项")
                data["items"] = items
                if not items:
                    errors.append(
                        FieldError(
                            field="items",
                            error="未能提取到任何列表项",
                        )
                    )
                else:
                    # 打印每个项的字段信息
                    for i, item in enumerate(items):
                        print(f"[ExtractEngine] 项 {i+1}: {list(item.keys())} 个字段")
            else:
                # 单条提取（使用新格式的字段配置）
                print(f"[ExtractEngine] 开始单条提取...")
                for field_name, field_config in profile.parse.fields.items():
                    print(f"[ExtractEngine] 提取字段: {field_name}")
                    value, error, extra_fields = self._extract_field_new_format(page, field_name, field_config)
                    if extra_fields:
                        for k, v in extra_fields.items():
                            if v is not None:
                                data[k] = v
                                print(f"[ExtractEngine]   ↳ 附加字段: {k} = {str(v)[:100]}")
                    if value is not None:
                        data[field_name] = value
                        print(f"[ExtractEngine]   ✓ 成功: {field_name} = {str(value)[:100]}")
                    elif error:
                        errors.append(error)
                        print(f"[ExtractEngine]   ✗ 失败: {field_name} - {error.error}")
                    else:
                        print(f"[ExtractEngine]   - 未找到: {field_name}")
                
                # 如果 profile 有 category，添加到 data 中
                if profile.category:
                    data["category"] = profile.category
                    print(f"[ExtractEngine] 添加 category: {profile.category}")
        
        # 支持旧格式（fields配置，兼容）
        elif profile.fields:
            for field_name, strategies in profile.fields.items():
                value = None
                field_error = None

                # 按顺序尝试每个策略
                for strategy in strategies:
                    try:
                        extract_func = self.strategies.get(strategy.type)
                        if not extract_func:
                            field_error = FieldError(
                                field=field_name,
                                error=f"未知的策略类型: {strategy.type}",
                                strategy=strategy.type.value,
                            )
                            continue

                        value = extract_func(page.html, strategy.config)
                        if value is not None:
                            # 成功提取，跳出策略链
                            break

                    except Exception as e:
                        field_error = FieldError(
                            field=field_name,
                            error=str(e),
                            strategy=strategy.type.value,
                        )
                        # 继续尝试下一个策略
                        continue

                # 记录结果
                if value is not None:
                    data[field_name] = value
                else:
                    # 所有策略都失败
                    if field_error:
                        errors.append(field_error)
                    else:
                        errors.append(
                            FieldError(
                                field=field_name,
                                error="所有策略均未能提取到值",
                            )
                        )

        record.data = data
        record.errors = errors
        return record

    def _extract_list(self, page: Page, parse_config, profile: Profile, page_resources: Optional[Dict[str, bytes]] = None) -> List[Dict[str, Any]]:
        """提取列表数据"""
        try:
            print(f"[ExtractList] 解析HTML...")
            tree = html.fromstring(page.html)
            print(f"[ExtractList] HTML长度: {len(page.html)} 字符")
            
            # 找到所有列表项容器
            item_elements = []
            if parse_config.item_selector_candidates:
                print(f"[ExtractList] 尝试 {len(parse_config.item_selector_candidates)} 个item selector候选...")
                for idx, selector in enumerate(parse_config.item_selector_candidates):
                    print(f"[ExtractList]  尝试 selector {idx+1}: {selector}")
                    
                    # 检查是否包含 :has()，如果包含则转换为 XPath
                    xpath_selector = None
                    if ':has(' in selector:
                        print(f"[ExtractList]    检测到 :has()，尝试转换为 XPath")
                        # 手动转换常见的 :has() 模式
                        if selector == "main li:has(a[href*='/products/'])":
                            xpath_selector = "//main//li[.//a[contains(@href, '/products/')]]"
                        elif selector == "main div:has(a[href*='/products/']):has(img)":
                            xpath_selector = "//main//div[.//a[contains(@href, '/products/')] and .//img]"
                        else:
                            # 尝试通用转换
                            xpath_selector = _css_has_to_xpath(selector)
                        print(f"[ExtractList]    转换后的 XPath: {xpath_selector}")
                    
                    try:
                        # 优先使用 XPath（如果已转换）
                        if xpath_selector:
                            print(f"[ExtractList]    使用转换后的 XPath")
                            elements = tree.xpath(xpath_selector)
                            print(f"[ExtractList]    找到 {len(elements)} 个元素")
                            if elements:
                                item_elements = elements
                                print(f"[ExtractList]    ✓ XPath成功")
                                break
                        else:
                            # 尝试使用 CSS selector
                            if CSSSELECT_AVAILABLE:
                                print(f"[ExtractList]    使用 CSS selector (cssselect可用)")
                                elements = tree.cssselect(selector)
                            else:
                                # 回退到 XPath（假设 selector 可能是 XPath）
                                print(f"[ExtractList]    使用 XPath (cssselect不可用)")
                                elements = tree.xpath(selector)
                            print(f"[ExtractList]    找到 {len(elements)} 个元素")
                            if elements:
                                item_elements = elements
                                print(f"[ExtractList]    ✓ 成功使用 selector: {selector}")
                                break
                    except Exception as e:
                        print(f"[ExtractList]    CSS selector失败: {str(e)}")
                        # CSS selector 失败，尝试 XPath
                        try:
                            print(f"[ExtractList]    尝试 XPath回退...")
                            if not xpath_selector:
                                # 如果还没有 XPath，尝试直接使用原 selector 作为 XPath
                                elements = tree.xpath(selector)
                            else:
                                elements = tree.xpath(xpath_selector)
                            print(f"[ExtractList]    XPath找到 {len(elements)} 个元素")
                            if elements:
                                item_elements = elements
                                print(f"[ExtractList]    ✓ XPath成功")
                                break
                        except Exception as e2:
                            print(f"[ExtractList]    XPath也失败: {str(e2)}")
                            continue
            else:
                print(f"[ExtractList]  警告: 没有item_selector_candidates配置")
            
            if not item_elements:
                print(f"[ExtractList]  ✗ 未找到任何列表项元素")
                return []
            
            print(f"[ExtractList] 找到 {len(item_elements)} 个列表项容器")
            print(f"[ExtractList] 需要提取的字段: {list(parse_config.fields.keys())}")
            
            # 提取每个列表项的字段
            items = []
            total_fields = len(parse_config.fields)
            for item_idx, item_elem in enumerate[Any](item_elements):
                print(f"[ExtractList] 处理项 {item_idx+1}/{len(item_elements)}")
                item_data = {}
                item_errors = []
                extracted_count = 0
                
                for field_name, field_config in parse_config.fields.items():
                    print(f"[ExtractList]  提取字段: {field_name} ({extracted_count+1}/{total_fields})")
                    value, error, extra_fields = self._extract_field_from_element(item_elem, field_config)
                    if extra_fields:
                        for k, v in extra_fields.items():
                            if v is not None:
                                item_data[k] = v
                                print(f"[ExtractList]    ↳ 附加字段: {k} = {str(v)[:50]}")
                    if value is not None:
                        item_data[field_name] = value
                        extracted_count += 1
                        print(f"[ExtractList]    ✓ {field_name} = {str(value)[:50]}")
                    else:
                        if error:
                            print(f"[ExtractList]    ✗ {field_name} - {error.error}")
                            item_errors.append(f"{field_name}: {error.error}")
                        else:
                            print(f"[ExtractList]    - {field_name} 未找到值（可能selector不匹配）")
                
                print(f"[ExtractList]  项 {item_idx+1} 提取结果: {extracted_count}/{total_fields} 个字段成功")
                if item_errors:
                    print(f"[ExtractList]    错误详情: {', '.join(item_errors)}")
                
                # 如果 profile 有 category，添加到 item_data 中
                if profile.category:
                    item_data["category"] = profile.category
                    print(f"[ExtractList]  添加 category: {profile.category}")
                
                # 至少提取到一个字段才添加（可以根据需要调整这个条件）
                if item_data:
                    items.append(item_data)
                    print(f"[ExtractList]  ✓ 项 {item_idx+1} 添加成功，包含字段: {list(item_data.keys())}")
                else:
                    print(f"[ExtractList]  ✗ 项 {item_idx+1} 未提取到任何字段，跳过")
            
            print(f"[ExtractList] 总共提取到 {len(items)} 个有效项")
            
            # 执行后处理步骤
            if parse_config.post_list_process:
                print(f"[ExtractList] 执行 {len(parse_config.post_list_process)} 个后处理步骤...")
                for step_idx, step in enumerate(parse_config.post_list_process):
                    print(f"[ExtractList]  后处理步骤 {step_idx+1}: {step.method}")
                    items = ParseTool.process(step.method, items, step.config)
                    print(f"[ExtractList]    处理后剩余 {len(items)} 个项")
            
            # 获取图片数据到内存（如果存在image字段和item_id字段）
            if profile.site:
                print(f"[ExtractList] 开始获取图片数据，站点: {profile.site}")
                # 使用页面资源（如果可用）
                resources = page_resources if page_resources is not None else (page.resources if hasattr(page, 'resources') and page.resources else None)
                if resources:
                    print(f"[ExtractList] 检测到 {len(resources)} 个已加载的资源，将优先使用")
                    # TODO，这里可能有风险，会将lazyloading.png作为图片链接。可能要做的修改是：加一个“预先检测的步骤”：若加载的资源中，有超过2个image的url是相同的，则认为资源中的这个url是lazyloading的url，需要去寻找上述读取每个item的image url的字段获取的image连接作为
                fetched_count = 0
                for item_idx, item in enumerate(items):
                    image_url = item.get("image")
                    item_id = item.get("item_id")
                    if image_url and item_id:
                        print(f"[ExtractList]  获取项 {item_idx+1} 的图片数据: {item_id}")
                        image_data = TransformProcessor.get_image_data(
                            image_url=image_url,
                            page_resources=resources
                        )
                        if image_data:
                            # 将图片数据保存到 item 中（使用 _image_data 字段）
                            item["_image_data"] = image_data
                            item["_image_url"] = image_url  # 保存原始URL用于后续保存文件时获取扩展名
                            fetched_count += 1
                            print(f"[ExtractList]    ✓ 图片数据已获取，大小: {len(image_data)} 字节")
                        else:
                            print(f"[ExtractList]    ✗ 图片数据获取失败")
                    else:
                        if not image_url:
                            print(f"[ExtractList]  项 {item_idx+1} 缺少 image 字段")
                        if not item_id:
                            print(f"[ExtractList]  项 {item_idx+1} 缺少 item_id 字段")
                print(f"[ExtractList] 图片数据获取完成: {fetched_count}/{len(items)} 个图片已获取")
            
            print(f"[ExtractList] 最终返回 {len(items)} 个项")
            return items
        
        except Exception as e:
            print(f"[ExtractList] 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_field_new_format(self, page: Page, field_name: str, field_config) -> tuple[Optional[Any], Optional[FieldError], Optional[Dict[str, Any]]]:
        """使用新格式提取字段"""
        try:
            tree = html.fromstring(page.html)
            value, error, extra_fields = self._extract_field_from_element(tree, field_config)
            return value, error, extra_fields
        except Exception as e:
            return None, FieldError(
                field=field_name,
                error=f"解析HTML失败: {str(e)}",
            ), None

    def _extract_field_from_element(self, root_elem, field_config) -> tuple[Optional[Any], Optional[FieldError], Optional[Dict[str, Any]]]:
        """从元素中提取字段值"""
        try:
            # 优先使用selector_candidates，如果没有则使用selector
            selectors_to_try = []
            if field_config.selector_candidates:
                selectors_to_try = field_config.selector_candidates
                print(f"[ExtractField]    使用selector_candidates: {selectors_to_try}")
            elif field_config.selector:
                selectors_to_try = [field_config.selector]
                print(f"[ExtractField]    使用selector: {field_config.selector}")
            else:
                return None, FieldError(
                    field="unknown",
                    error="未指定selector或selector_candidates",
                ), None
            
            elements = []
            last_error = None
            
            # 尝试每个selector候选
            for selector in selectors_to_try:
                print(f"[ExtractField]    尝试selector: {selector}")
                
                # 处理特殊 selector
                if selector == ":root":
                    # 使用根元素本身
                    print(f"[ExtractField]      使用 :root (根元素)")
                    elements = [root_elem]
                    break
                
                # 使用 CSS selector 或 XPath
                try:
                    if CSSSELECT_AVAILABLE:
                        print(f"[ExtractField]      尝试 CSS selector")
                        elements = root_elem.cssselect(selector)
                    else:
                        # 回退到 XPath
                        print(f"[ExtractField]      尝试 XPath (cssselect不可用)")
                        elements = root_elem.xpath(selector)
                    print(f"[ExtractField]      找到 {len(elements)} 个元素")
                    if elements:
                        # 找到元素，跳出循环
                        break
                except Exception as e:
                    print(f"[ExtractField]      CSS selector/XPath失败: {str(e)}")
                    last_error = e
                    # CSS selector 失败，尝试 XPath
                    try:
                        print(f"[ExtractField]      尝试 XPath回退")
                        elements = root_elem.xpath(selector)
                        print(f"[ExtractField]      XPath找到 {len(elements)} 个元素")
                        if elements:
                            # 找到元素，跳出循环
                            break
                    except Exception as e2:
                        print(f"[ExtractField]      XPath也失败: {str(e2)}")
                        last_error = e2
                        # 继续尝试下一个selector
                        continue
            
            # 如果所有selector都失败
            if not elements and last_error:
                return None, FieldError(
                    field="unknown",
                    error=f"所有selector均失败，最后一个错误: {str(last_error)}",
                ), None
            
            if not elements:
                print(f"[ExtractField]    未找到元素")
                return None, None, None  # 未找到，但不报错（可能是可选的）
            
            # 提取值
            values = []
            extra_fields_result = None
            for elem_idx, elem in enumerate(elements):
                value = None
                print(f"[ExtractField]    处理元素 {elem_idx+1}/{len(elements)}")
                
                # 提取属性
                if field_config.attr:
                    print(f"[ExtractField]      提取属性: {field_config.attr}")
                    if hasattr(elem, "get"):
                        value = elem.get(field_config.attr)
                        print(f"[ExtractField]        值: {value}")
                elif field_config.attr_candidates:
                    print(f"[ExtractField]      尝试属性候选: {field_config.attr_candidates}")
                    for attr_name in field_config.attr_candidates:
                        if hasattr(elem, "get"):
                            value = elem.get(attr_name)
                            if value:
                                print(f"[ExtractField]        找到: {attr_name} = {value}")
                                break
                
                # 提取文本
                if value is None and field_config.text:
                    print(f"[ExtractField]      提取文本内容")
                    if hasattr(elem, "text_content"):
                        value = elem.text_content()
                        print(f"[ExtractField]        text_content: {value[:100] if value else None}")
                    elif hasattr(elem, "text"):
                        value = elem.text
                        print(f"[ExtractField]        text: {value[:100] if value else None}")
                    elif isinstance(elem, str):
                        value = elem
                        print(f"[ExtractField]        字符串值: {value[:100] if value else None}")
                
                if value:
                    print(f"[ExtractField]      原始值: {str(value)[:100]}")
                    # 应用 transforms
                    if field_config.transforms:
                        print(f"[ExtractField]      应用 {len(field_config.transforms)} 个transforms")
                        original_value = value
                        value = TransformProcessor.apply_transforms(value, field_config.transforms)
                        if isinstance(value, dict) and "__extra_fields__" in value:
                            if extra_fields_result is None:
                                extra_fields_result = value.get("__extra_fields__") or None
                            value = value.get("__value__")
                        print(f"[ExtractField]        转换后: {str(value)[:100] if value else None}")
                    # 即使transforms返回None，也记录原始值（用于调试）
                    # 但只有当最终值不为None时才添加到values
                    if value is not None:
                        values.append(value)
                else:
                    print(f"[ExtractField]      未提取到值")
            
            if not values:
                print(f"[ExtractField]    所有元素都未提取到值")
                return None, None, None
            
            # 对于列表提取，每个item应该只返回第一个匹配的值
            # 这样可以确保每个item只有一个url、一个image等
            result = values[0]
            print(f"[ExtractField]    最终结果: {str(result)[:100] if result else None} (从{len(values)}个匹配值中选择第一个)")
            return result, None, extra_fields_result
        
        except Exception as e:
            print(f"[ExtractField]    异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, FieldError(
                field="unknown",
                error=f"提取字段失败: {str(e)}",
            ), None

