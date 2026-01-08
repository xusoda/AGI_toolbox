"""测试翻译功能"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
script_file = Path(__file__).resolve()
script_dir = script_file.parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from i18n.translation.mapper import TranslationMapper
from i18n.translation.normalizer import Normalizer

def test_translation():
    """测试翻译功能"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("错误: 环境变量 DATABASE_URL 未设置")
        sys.exit(1)
    
    print("=" * 60)
    print("测试翻译功能")
    print("=" * 60)
    
    # 测试品牌翻译
    print("\n1. 测试品牌翻译...")
    mapper = TranslationMapper(database_url)
    
    test_brands = ["Rolex", "Grand Seiko", "Omega"]
    for brand in test_brands:
        normalized = Normalizer.normalize_brand(brand, "watch")
        print(f"\n   品牌: {brand} -> 归一化: {normalized}")
        
        for lang in ["zh", "ja"]:
            translated = mapper.translate_brand(normalized, lang)
            print(f"      {lang}: {translated}")
    
    # 测试型号翻译
    print("\n2. 测试型号翻译...")
    test_models = [
        ("Rolex", "Daytona"),
        ("Grand Seiko", "Heritage Collection"),
    ]
    
    for brand, model in test_models:
        normalized_brand = Normalizer.normalize_brand(brand, "watch")
        normalized_model = Normalizer.normalize_model_name(normalized_brand, model, "watch")
        print(f"\n   品牌: {brand}, 型号: {model}")
        print(f"   归一化: {normalized_brand} / {normalized_model}")
        
        for lang in ["zh", "ja"]:
            translated = mapper.translate_model_name(normalized_brand, normalized_model, lang)
            print(f"      {lang}: {translated}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_translation()

