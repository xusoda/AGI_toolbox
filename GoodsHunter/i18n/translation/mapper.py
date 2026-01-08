"""翻译映射器：将标准英文格式转换为目标语言"""
import json
import os
from typing import Optional, Dict, Any
from .loader import DictionaryLoader
from .language_detector import LanguageDetector
from .normalizer import Normalizer

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


class TranslationMapper:
    """翻译映射器，负责将标准英文转换为目标语言"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化翻译映射器
        
        Args:
            database_url: 数据库连接URL，如果为None则从环境变量读取
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._translation_cache: Dict[str, Dict[str, str]] = {}
    
    def _get_db_connection(self):
        """获取数据库连接"""
        if psycopg2 is None:
            raise ImportError("psycopg2 未安装")
        if not self.database_url:
            raise ValueError("数据库连接URL未设置")
        return psycopg2.connect(self.database_url)
    
    def translate_brand(
        self,
        brand_name: str,
        target_lang: str = "zh"
    ) -> str:
        """
        将品牌名翻译为目标语言

        Args:
            brand_name: 品牌名（可能是各种语言）
            target_lang: 目标语言代码（en/zh/ja）

        Returns:
            翻译后的品牌名，如果不需要翻译或翻译不存在则返回原始值
        """
        if not brand_name:
            return ""

        # 检测源语言，如果与目标语言相同，不需要翻译
        if not LanguageDetector.needs_translation(brand_name, target_lang):
            return brand_name
        
        # 检查缓存
        cache_key = f"brand:{brand_name}:{target_lang}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT translations FROM brand_translations WHERE brand_name = %s",
                (brand_name,)
            )
            row = cursor.fetchone()
            
            if row and row['translations']:
                translations = row['translations']
                # PostgreSQL JSONB 字段在 psycopg2 中可能自动解析为 dict，也可能返回字符串
                if isinstance(translations, str):
                    translations = json.loads(translations)
                elif not isinstance(translations, dict):
                    # 如果既不是字符串也不是字典，尝试转换
                    translations = dict(translations) if hasattr(translations, '__iter__') else {}
                
                translated = translations.get(target_lang)
                if translated:
                    self._translation_cache[cache_key] = translated
                    cursor.close()
                    conn.close()
                    return translated
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"[TranslationMapper] 翻译品牌失败: {e}")
        
        # 如果数据库中没有，尝试从字典中查找
        if target_lang == "ja":
            # 从字典中查找日文别名
            aliases_map = DictionaryLoader.get_brand_aliases("watch")
            if brand_name in aliases_map:
                aliases = aliases_map[brand_name]
                # 查找日文别名（包含日文字符）
                for alias in aliases:
                    if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                        return alias
            
            # 使用规范化匹配查找品牌（忽略标点符号）
            brand_for_matching = Normalizer.normalize_for_matching(brand_name).lower()
            for canonical_brand, aliases in aliases_map.items():
                canonical_for_matching = Normalizer.normalize_for_matching(canonical_brand).lower()
                if canonical_for_matching == brand_for_matching:
                    # 找到标准品牌，返回其日文别名
                    for alias in aliases:
                        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                            return alias
                # 检查别名
                for alias in aliases:
                    alias_for_matching = Normalizer.normalize_for_matching(alias).lower()
                    if alias_for_matching == brand_for_matching:
                        # 找到匹配的别名，返回其日文别名（如果存在）
                        for a in aliases:
                            if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in a):
                                return a
        
        # 如果都找不到，返回原始值
        return brand_name
    
    def translate_model_name(
        self,
        brand_name: str,
        model_name: str,
        target_lang: str = "zh"
    ) -> str:
        """
        将型号名翻译为目标语言

        Args:
            brand_name: 品牌名（可能是各种语言）
            model_name: 型号名（可能是各种语言）
            target_lang: 目标语言代码（en/zh/ja）

        Returns:
            翻译后的型号名，如果不需要翻译或翻译不存在则返回原始值
        """
        if not model_name:
            return ""

        # 检测源语言，如果与目标语言相同，不需要翻译
        if not LanguageDetector.needs_translation(model_name, target_lang):
            return model_name
        
        # 检查缓存
        cache_key = f"model_name:{brand_name}:{model_name}:{target_lang}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                """
                SELECT translations FROM model_name_translations 
                WHERE brand_name = %s AND model_name = %s
                """,
                (brand_name, model_name)
            )
            row = cursor.fetchone()
            
            if row and row['translations']:
                translations = row['translations']
                # PostgreSQL JSONB 字段在 psycopg2 中可能自动解析为 dict，也可能返回字符串
                if isinstance(translations, str):
                    translations = json.loads(translations)
                elif not isinstance(translations, dict):
                    # 如果既不是字符串也不是字典，尝试转换
                    translations = dict(translations) if hasattr(translations, '__iter__') else {}
                
                translated = translations.get(target_lang)
                if translated:
                    self._translation_cache[cache_key] = translated
                    cursor.close()
                    conn.close()
                    return translated
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"[TranslationMapper] 翻译型号名失败: {e}")
        
        # 如果数据库中没有，尝试从字典中查找
        if target_lang == "ja":
            aliases_map = DictionaryLoader.get_model_aliases(brand_name, "watch")
            if model_name in aliases_map:
                aliases = aliases_map[model_name]
                # 查找日文别名
                for alias in aliases:
                    if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                        return alias
            
            # 使用规范化匹配查找型号（忽略标点符号）
            model_for_matching = Normalizer.normalize_for_matching(model_name).lower()
            for canonical_model, aliases in aliases_map.items():
                canonical_for_matching = Normalizer.normalize_for_matching(canonical_model).lower()
                if canonical_for_matching == model_for_matching:
                    # 找到标准型号，返回其日文别名
                    for alias in aliases:
                        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                            return alias
                # 检查别名
                for alias in aliases:
                    alias_for_matching = Normalizer.normalize_for_matching(alias).lower()
                    if alias_for_matching == model_for_matching:
                        # 找到匹配的别名，返回其日文别名（如果存在）
                        for a in aliases:
                            if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in a):
                                return a
        
        # 如果都找不到，返回原始值
        return model_name
    
    def translate_model_no(
        self,
        model_no: str,
        target_lang: str = "zh"
    ) -> str:
        """
        将型号编号翻译为目标语言（通常型号编号不需要翻译，但保留接口）
        
        Args:
            model_no: 型号编号
            target_lang: 目标语言代码（en/zh/ja）
            
        Returns:
            翻译后的型号编号，通常直接返回原始值
        """
        # 型号编号通常不需要翻译，直接返回
        return model_no
    
    def translate_item(
        self,
        brand_name: str,
        model_name: str,
        model_no: str,
        target_lang: str = "zh"
    ) -> Dict[str, str]:
        """
        翻译整个商品信息
        
        Args:
            brand_name: 标准英文品牌名
            model_name: 标准英文型号名
            model_no: 型号编号
            target_lang: 目标语言代码（en/zh/ja）
            
        Returns:
            {
                "brand_name": 翻译后的品牌名,
                "model_name": 翻译后的型号名,
                "model_no": 翻译后的型号编号
            }
        """
        return {
            "brand_name": self.translate_brand(brand_name, target_lang),
            "model_name": self.translate_model_name(brand_name, model_name, target_lang),
            "model_no": self.translate_model_no(model_no, target_lang),
        }

