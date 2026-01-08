"""商品匹配器：判断两个商品是否为同一商品"""
from typing import Dict, Optional
from ..translation.normalizer import Normalizer


class ProductMatcher:
    """商品匹配器，负责判断两个商品是否为同一商品"""
    
    @staticmethod
    def match_products(
        item1: Dict[str, Optional[str]],
        item2: Dict[str, Optional[str]],
        category: str = "watch"
    ) -> bool:
        """
        判断两个商品是否为同一商品
        
        匹配规则：
        1. category 必须相同
        2. brand_name, model_name, model_no 归一化后必须完全相同
        
        Args:
            item1: 商品1，包含 brand_name, model_name, model_no, category
            item2: 商品2，包含 brand_name, model_name, model_no, category
            category: 商品类别
            
        Returns:
            True 如果两个商品是同一商品，否则 False
        """
        # 检查类别
        cat1 = item1.get("category", category)
        cat2 = item2.get("category", category)
        if cat1 != cat2:
            return False
        
        # 归一化商品信息
        brand1, model1, model_no1 = Normalizer.normalize_item(
            item1.get("brand_name"),
            item1.get("model_name"),
            item1.get("model_no"),
            cat1
        )
        
        brand2, model2, model_no2 = Normalizer.normalize_item(
            item2.get("brand_name"),
            item2.get("model_name"),
            item2.get("model_no"),
            cat2
        )
        
        # 比较归一化后的值
        if brand1 != brand2:
            return False
        
        if model1 != model2:
            return False
        
        if model_no1 != model_no2:
            return False
        
        return True
    
    @staticmethod
    def get_product_key(
        brand_name: Optional[str],
        model_name: Optional[str],
        model_no: Optional[str],
        category: str = "watch"
    ) -> str:
        """
        生成商品的唯一键（用于匹配和聚合）
        
        Args:
            brand_name: 品牌名
            model_name: 型号名
            model_no: 型号编号
            category: 商品类别
            
        Returns:
            商品的唯一键字符串
        """
        normalized_brand, normalized_model, normalized_model_no = Normalizer.normalize_item(
            brand_name,
            model_name,
            model_no,
            category
        )
        
        # 生成唯一键
        parts = [category, normalized_brand, normalized_model, normalized_model_no]
        return "|".join(parts)

