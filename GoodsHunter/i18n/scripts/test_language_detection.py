#!/usr/bin/env python3
"""测试语言检测器"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from i18n.translation.language_detector import LanguageDetector

def test_language_detection():
    """测试语言检测功能"""

    test_cases = [
        # 英文测试
        ("Rolex", "en"),
        ("Grand Seiko", "en"),
        ("Daytona", "en"),

        # 中文测试
        ("劳力士", "zh"),
        ("格拉苏蒂", "zh"),
        ("迪通拿", "zh"),
        ("传承系列", "zh"),

        # 日文测试
        ("ロレックス", "ja"),
        ("グランドセイコー", "ja"),
        ("デイトナ", "ja"),
        ("ヘリテージコレクション", "ja"),

        # 混合测试
        ("Rolex 劳力士", "zh"),  # 优先中文
        ("Rolex ロレックス", "ja"),  # 优先日文
        ("123", "en"),  # 数字默认英文
        ("", "en"),  # 空字符串默认英文
    ]

    print("=== 语言检测测试 ===")
    for text, expected in test_cases:
        detected = LanguageDetector.detect_language(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text}' -> 期望: {expected}, 检测: {detected}")

def test_translation_need():
    """测试是否需要翻译"""

    test_cases = [
        # 不需要翻译的情况
        ("Rolex", "en", False),
        ("劳力士", "zh", False),
        ("ロレックス", "ja", False),

        # 需要翻译的情况
        ("Rolex", "zh", True),
        ("Rolex", "ja", True),
        ("劳力士", "en", True),
        ("劳力士", "ja", True),
        ("ロレックス", "en", True),
        ("ロレックス", "zh", True),
    ]

    print("\n=== 翻译需求测试 ===")
    for text, target_lang, expected in test_cases:
        needs = LanguageDetector.needs_translation(text, target_lang)
        status = "✓" if needs == expected else "✗"
        print(f"{status} '{text}' -> {target_lang}: 期望: {expected}, 实际: {needs}")

if __name__ == "__main__":
    test_language_detection()
    test_translation_need()