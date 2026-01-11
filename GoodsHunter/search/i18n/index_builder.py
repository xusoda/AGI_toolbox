"""索引构建器：构建包含多语言同义词的ES文档"""
import logging
from typing import Dict, Any, Optional
from search.i18n.alias_resolver import AliasResolver

# 延迟导入 DictionaryLoader 以避免循环导入
try:
    from i18n.translation.loader import DictionaryLoader
except ImportError:
    DictionaryLoader = None
    logging.warning("DictionaryLoader 不可用，别名解析功能受限")

logger = logging.getLogger(__name__)


class IndexBuilder:
    """索引构建器，负责构建ES索引文档"""
    
    @staticmethod
    def build_document(item_data: Dict[str, Any], category: Optional[str] = None) -> Dict[str, Any]:
        """
        构建ES索引文档（包含多语言同义词）
        
        Args:
            item_data: 商品数据（来自数据库）
            category: 商品类别，如果为None则从item_data中获取
            
        Returns:
            ES文档
        """
        try:
            brand_name = item_data.get("brand_name") or ""
            model_name = item_data.get("model_name") or ""
            model_no = item_data.get("model_no") or ""
            item_category = category or item_data.get("category") or "watch"
            
            # 第一步：将品牌别名转换为标准品牌名（如果数据库中的brand_name是别名，如"ロレックス"，需要找到标准名称"Rolex"）
            standard_brand_name = brand_name
            if DictionaryLoader and brand_name:
                found_standard_brand = DictionaryLoader.find_brand_by_alias(brand_name, item_category)
                if found_standard_brand:
                    standard_brand_name = found_standard_brand
                    logger.debug(f"品牌别名 '{brand_name}' 映射到标准名称 '{standard_brand_name}'")
            
            # 第二步：使用标准品牌名获取所有别名（包括原始名称和所有同义词）
            brand_aliases = AliasResolver.get_brand_aliases(standard_brand_name, item_category)
            
            # 第三步：将型号别名转换为标准型号名（需要先有标准品牌名）
            standard_model_name = model_name
            if DictionaryLoader and standard_brand_name and model_name:
                found_standard_model = DictionaryLoader.find_model_by_alias(
                    standard_brand_name, model_name, item_category
                )
                if found_standard_model:
                    standard_model_name = found_standard_model
                    logger.debug(f"型号别名 '{model_name}' 映射到标准名称 '{standard_model_name}'")
            
            # 第四步：使用标准品牌名和标准型号名获取所有别名
            model_aliases = AliasResolver.get_model_aliases(standard_brand_name, standard_model_name, item_category)
            
            # 构建搜索文本（合并所有同义词）
            search_text_parts = brand_aliases + model_aliases
            if model_no:
                search_text_parts.append(model_no)
            search_text = " ".join(filter(None, search_text_parts))
            
            # 构建completion字段的输入词（用于搜索建议）
            # 包含品牌名、型号名、型号编号和所有别名
            suggest_inputs = []
            
            # 添加品牌名（如果存在）
            if brand_name:
                suggest_inputs.append(brand_name)
            
            # 添加型号名（如果存在）
            if model_name:
                suggest_inputs.append(model_name)
            
            # 添加型号编号（如果存在）
            if model_no:
                suggest_inputs.append(model_no)
            
            # 添加品牌别名（去重）
            for alias in brand_aliases:
                if alias and alias not in suggest_inputs:
                    suggest_inputs.append(alias)
            
            # 添加型号别名（去重）
            for alias in model_aliases:
                if alias and alias not in suggest_inputs:
                    suggest_inputs.append(alias)
            
            # 构建ES文档
            doc = {
                "id": item_data.get("id"),
                "brand_name": brand_name,
                "model_name": model_name,
                "model_no": model_no,
                "brand_aliases": brand_aliases,
                "model_aliases": model_aliases,
                "search_text": search_text,
                "suggest": {
                    "input": suggest_inputs
                } if suggest_inputs else None,
                "price": item_data.get("price"),
                "currency": item_data.get("currency"),
                "site": item_data.get("site"),
                "category": item_category,
                "status": item_data.get("status"),
                "last_seen_dt": item_data.get("last_seen_dt"),
                "created_at": item_data.get("created_at"),
                "image_thumb_300_key": item_data.get("image_thumb_300_key"),
                "product_url": item_data.get("product_url"),
            }
            
            return doc
        except Exception as e:
            logger.error(f"构建索引文档失败 (item_id={item_data.get('id')}): {e}", exc_info=True)
            # 返回基本文档（不包含别名）
            basic_brand = item_data.get("brand_name", "")
            basic_model = item_data.get("model_name", "")
            basic_model_no = item_data.get("model_no", "")
            
            # 构建基本的completion字段
            basic_suggest_inputs = []
            if basic_brand:
                basic_suggest_inputs.append(basic_brand)
            if basic_model:
                basic_suggest_inputs.append(basic_model)
            if basic_model_no:
                basic_suggest_inputs.append(basic_model_no)
            
            return {
                "id": item_data.get("id"),
                "brand_name": basic_brand,
                "model_name": basic_model,
                "model_no": basic_model_no,
                "brand_aliases": [basic_brand] if basic_brand else [],
                "model_aliases": [basic_model] if basic_model else [],
                "search_text": f"{basic_brand} {basic_model} {basic_model_no}".strip(),
                "suggest": {
                    "input": basic_suggest_inputs
                } if basic_suggest_inputs else None,
                "price": item_data.get("price"),
                "currency": item_data.get("currency"),
                "site": item_data.get("site"),
                "category": category or item_data.get("category", "watch"),
                "status": item_data.get("status"),
                "last_seen_dt": item_data.get("last_seen_dt"),
                "created_at": item_data.get("created_at"),
                "image_thumb_300_key": item_data.get("image_thumb_300_key"),
                "product_url": item_data.get("product_url"),
            }
