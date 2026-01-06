"""JSONL输出写入器"""
import json
from pathlib import Path
from typing import List

from core.types import Record, FieldError


class JSONLWriter:
    """JSONL格式输出写入器"""

    def __init__(self, output_path: str):
        """
        初始化写入器
        
        Args:
            output_path: 输出文件路径
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_record(self, record: Record):
        """
        写入单条记录
        
        Args:
            record: Record对象
        """
        # 将Record转换为可序列化的字典
        record_dict = {
            "url": record.url,
            "data": record.data,
            "errors": [
                {
                    "field": err.field,
                    "error": err.error,
                    "strategy": err.strategy,
                }
                for err in record.errors
            ],
        }

        # 追加写入JSONL格式（每行一个JSON对象）
        with open(self.output_path, "a", encoding="utf-8") as f:
            json.dump(record_dict, f, ensure_ascii=False)
            f.write("\n")

    def write_records(self, records: List[Record]):
        """
        批量写入记录
        
        Args:
            records: Record对象列表
        """
        for record in records:
            self.write_record(record)

