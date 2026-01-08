"""语言检测器：检测文本的语言"""
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    LANGDETECT_AVAILABLE = True
    # 设置随机种子以确保结果一致性
    DetectorFactory.seed = 0
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("警告: langdetect 未安装，将使用简单的字符检测方法。建议运行: pip install langdetect")


class LanguageDetector:
    """语言检测器，支持通用的语言检测方法"""

    # 语言代码映射：langdetect 返回的语言代码 -> 我们的标准代码
    LANG_CODE_MAP = {
        'zh-cn': 'zh',
        'zh-tw': 'zh',
        'ja': 'ja',
        'en': 'en',
    }

    @staticmethod
    def detect_language(text: str) -> str:
        """
        检测文本的语言（通用方法，适用于各种商品类别）

        Args:
            text: 要检测的文本

        Returns:
            语言代码：'zh' (中文), 'ja' (日文), 'en' (英文)
        """
        if not text or not text.strip():
            return 'en'  # 默认英文

        # 对于非常短的文本（少于3个字符），直接使用字符检测
        # langdetect 对短文本不太准确
        if len(text.strip()) < 3:
            return LanguageDetector._detect_by_chars(text)

        # 优先使用 langdetect 库（更通用、更准确）
        if LANGDETECT_AVAILABLE:
            try:
                detected = detect(text)
                # 转换为标准语言代码
                lang_code = LanguageDetector.LANG_CODE_MAP.get(detected.lower(), 'en')
                return lang_code
            except (LangDetectException, Exception) as e:
                # 如果 langdetect 失败，回退到字符检测
                # 静默处理异常，不打印错误（避免日志噪音）
                pass

        # 回退方案：基于字符特征检测（适用于短文本或 langdetect 不可用时）
        return LanguageDetector._detect_by_chars(text)

    @staticmethod
    def _detect_by_chars(text: str) -> str:
        """
        基于字符特征检测语言（回退方案）

        Args:
            text: 要检测的文本

        Returns:
            语言代码：'zh' (中文), 'ja' (日文), 'en' (英文)
        """
        # 检查是否包含中文字符 (CJK Unified Ideographs)
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)

        # 检查是否包含日文平假名 (Hiragana)
        has_hiragana = any('\u3040' <= char <= '\u309f' for char in text)

        # 检查是否包含日文片假名 (Katakana)
        has_katakana = any('\u30a0' <= char <= '\u30ff' for char in text)

        # 优先级：中文 > 日文 > 英文
        if has_chinese:
            return 'zh'
        elif has_hiragana or has_katakana:
            return 'ja'
        else:
            return 'en'

    @staticmethod
    def detect_product_language(brand_name: str = None, model_name: str = None) -> str:
        """
        检测商品的语言（基于品牌名和型号名）

        Args:
            brand_name: 品牌名
            model_name: 型号名

        Returns:
            检测到的语言代码
        """
        # 合并品牌名和型号名进行检测
        text_parts = []
        if brand_name and str(brand_name).strip():
            text_parts.append(str(brand_name).strip())
        if model_name and str(model_name).strip():
            text_parts.append(str(model_name).strip())
        
        if not text_parts:
            return 'en'  # 如果没有文本，默认返回英文
        
        combined_text = ' '.join(text_parts)
        return LanguageDetector.detect_language(combined_text)

    @staticmethod
    def needs_translation(source_text: str, target_lang: str) -> bool:
        """
        判断文本是否需要翻译

        Args:
            source_text: 源文本
            target_lang: 目标语言代码

        Returns:
            是否需要翻译
        """
        if not source_text:
            return False
        
        source_lang = LanguageDetector.detect_language(source_text)
        return source_lang != target_lang