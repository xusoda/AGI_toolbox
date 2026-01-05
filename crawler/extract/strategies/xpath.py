"""XPath抽取策略"""
import re
from typing import Any, Dict, Optional

from lxml import html


class XPathStrategy:
    """XPath抽取策略"""

    @staticmethod
    def extract(page_html: str, config: Dict[str, Any]) -> Optional[str]:
        """
        使用XPath从HTML中提取内容
        
        Args:
            page_html: 页面HTML内容
            config: 配置字典，必须包含：
                - xpath: XPath表达式
                可选：
                - attribute: 要提取的属性名（如 "href", "src"），默认提取文本内容
                - strip: 是否去除首尾空白（默认True）
                
        Returns:
            提取的文本内容，如果未找到则返回None
        """
        if "xpath" not in config:
            return None

        try:
            tree = html.fromstring(page_html)
            elements = tree.xpath(config["xpath"])

            if not elements:
                return None

            # 如果配置了attribute，提取属性值
            if "attribute" in config:
                values = []
                for elem in elements:
                    if hasattr(elem, "get"):
                        attr_value = elem.get(config["attribute"])
                        if attr_value:
                            values.append(attr_value)
                if values:
                    return " ".join(values) if len(values) > 1 else values[0]
                return None

            # 提取文本内容
            texts = []
            for elem in elements:
                if hasattr(elem, "text_content"):
                    text = elem.text_content()
                elif isinstance(elem, str):
                    text = elem
                else:
                    continue

                if text:
                    text = text.strip() if config.get("strip", True) else text
                    if text:
                        texts.append(text)

            if texts:
                result = " ".join(texts) if len(texts) > 1 else texts[0]
                return result.strip() if config.get("strip", True) else result

            return None

        except Exception:
            return None

