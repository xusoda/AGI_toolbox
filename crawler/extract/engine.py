"""字段抽取引擎：执行策略链"""
from typing import Dict, Any

from core.types import Page, Profile, Record, FieldError, StrategyType
from extract.strategies.jsonld import JSONLDStrategy
from extract.strategies.xpath import XPathStrategy
from extract.strategies.regex import RegexStrategy


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
        record = Record(url=page.url)
        data = {}
        errors = []

        # 遍历每个字段的策略链
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

