"""归一化处理器：将多语言文本归一化为标准英文格式"""
import re
import html
import unicodedata
from typing import Optional, Tuple
# 延迟导入 DictionaryLoader 以避免循环导入
# from .loader import DictionaryLoader


class Normalizer:
    """归一化处理器，负责将多语言文本转换为标准英文格式"""
    
    @staticmethod
    def normalize_for_matching(text: str) -> str:
        """
        规范化文本用于匹配，移除空格、逗号、点等标点符号，统一特殊符号的不同版本
        
        例如：
        - "ヴァシュロン・コンスタンタン" -> "ヴァシュロンコンスタンタン"
        - "ヴァシュロンコンスタンタン" -> "ヴァシュロンコンスタンタン"
        - "A. Lange & Söhne" -> "ALange&Söhne"
        - "A. Lange ＆ Söhne" -> "ALange&Söhne" (全角&转换为半角)
        - "A. Lange &amp; Söhne" -> "ALange&Söhne" (HTML实体解码)
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本（移除标点符号，统一特殊符号）
        """
        if not text:
            return ""
        
        # 1. HTML实体解码（如 &amp; -> &）
        normalized = html.unescape(text)
        
        # 2. Unicode标准化（NFKC：兼容字符分解并重新组合）
        # 这会将全角字符转换为半角，组合字符标准化等
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # 3. 特殊符号映射表：将不同版本的符号统一为标准版本
        symbol_mappings = {
            # & 符号的不同版本
            '\uFF06': '&',  # 全角 & (＆)
            '\u214B': '&',  # 转置符号 (&)
            # 其他常见符号的变体
            '\u2013': '-',  # 短破折号 (–)
            '\u2014': '-',  # 长破折号 (—)
            '\u2015': '-',  # 水平线 (―)
            '\u2212': '-',  # 减号 (−)
            '\uFF0D': '-',  # 全角减号 (－)
            '\u2018': "'",  # 左单引号 (')
            '\u2019': "'",  # 右单引号 (')
            '\u201C': '"',  # 左双引号 (")
            '\u201D': '"',  # 右双引号 (")
            '\uFF02': '"',  # 全角双引号 (")
            '\uFF07': "'",  # 全角单引号 (')
            '\u00A0': ' ',  # 不间断空格 -> 普通空格
            '\u2000': ' ',  # 半角空格
            '\u2001': ' ',  # 全角空格
            '\u2002': ' ',  # 半角空格
            '\u2003': ' ',  # 全角空格
            '\u2004': ' ',  # 三分之一空格
            '\u2005': ' ',  # 四分之一空格
            '\u2006': ' ',  # 六分之一空格
            '\u2007': ' ',  # 数字空格
            '\u2008': ' ',  # 标点空格
            '\u2009': ' ',  # 细空格
            '\u200A': ' ',  # 超细空格
            '\u202F': ' ',  # 窄不间断空格
            '\u205F': ' ',  # 中等数学空格
            '\u3000': ' ',  # 表意文字空格（全角空格）
        }
        
        # 应用符号映射
        for old_char, new_char in symbol_mappings.items():
            normalized = normalized.replace(old_char, new_char)
        
        # 4. 移除常见的标点符号和空格：空格、逗号、点、中黑点（・）等
        # 保留字母、数字、日文假名、汉字等
        normalized = re.sub(r'[\s,\.・。、，\u00B7\u2022\u2027\u2219]', '', normalized)
        
        return normalized
    
    @staticmethod
    def normalize_brand(brand_name: str, category: str = "watch") -> str:
        """
        将品牌名归一化为标准英文格式
        
        Args:
            brand_name: 原始品牌名（可能是日文、中文、英文等）
            category: 商品类别
            
        Returns:
            标准化的英文品牌名
        """
        if not brand_name:
            return ""
        
        # 去除首尾空格
        brand_name = brand_name.strip()
        
        # 尝试通过字典查找标准品牌名
        # 延迟导入以避免循环导入
        from .loader import DictionaryLoader
        standard_brand = DictionaryLoader.find_brand_by_alias(brand_name, category)
        if standard_brand:
            return standard_brand
        
        # 如果找不到，返回原始值（可能是新的品牌，需要后续处理）
        return brand_name
    
    @staticmethod
    def normalize_model_name(
        brand_name: str,
        model_name: str,
        category: str = "watch"
    ) -> str:
        """
        将型号名归一化为标准英文格式
        
        Args:
            brand_name: 品牌名（已归一化）
            model_name: 原始型号名（可能是日文、中文、英文等）
            category: 商品类别
            
        Returns:
            标准化的英文型号名
        """
        if not model_name:
            return ""
        
        # 去除首尾空格
        model_name = model_name.strip()
        
        # 先归一化品牌名
        normalized_brand = Normalizer.normalize_brand(brand_name, category)
        
        # 尝试通过字典查找标准型号名
        # 延迟导入以避免循环导入
        from .loader import DictionaryLoader
        standard_model = DictionaryLoader.find_model_by_alias(
            normalized_brand,
            model_name,
            category
        )
        if standard_model:
            return standard_model
        
        # 如果找不到，返回原始值
        return model_name
    
    @staticmethod
    def normalize_model_no(model_no: str) -> str:
        """
        将型号编号标准化（去除空格、统一格式等）
        
        Args:
            model_no: 原始型号编号
            
        Returns:
            标准化后的型号编号
        """
        if not model_no:
            return ""
        
        # 去除首尾空格
        model_no = model_no.strip()
        
        # 去除中间空格
        model_no = re.sub(r'\s+', '', model_no)
        
        # 统一大小写（通常型号编号是大写）
        model_no = model_no.upper()
        
        return model_no
    
    @staticmethod
    def normalize_item(
        brand_name: Optional[str],
        model_name: Optional[str],
        model_no: Optional[str],
        category: str = "watch"
    ) -> Tuple[str, str, str]:
        """
        归一化整个商品信息
        
        Args:
            brand_name: 原始品牌名
            model_name: 原始型号名
            model_no: 原始型号编号
            category: 商品类别
            
        Returns:
            (归一化后的品牌名, 归一化后的型号名, 归一化后的型号编号)
        """
        normalized_brand = Normalizer.normalize_brand(
            brand_name or "", 
            category
        )
        normalized_model = Normalizer.normalize_model_name(
            normalized_brand,
            model_name or "",
            category
        )
        normalized_model_no = Normalizer.normalize_model_no(model_no or "")
        
        return (normalized_brand, normalized_model, normalized_model_no)

