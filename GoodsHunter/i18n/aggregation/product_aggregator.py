"""商品聚合器：将 crawler_item 记录聚合到 product 表"""
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    psycopg2 = None

from ..translation.normalizer import Normalizer
from .matcher import ProductMatcher


class ProductAggregator:
    """商品聚合器，负责将 crawler_item 记录聚合到 product 表"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化商品聚合器
        
        Args:
            database_url: 数据库连接URL，如果为None则从环境变量读取
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("数据库连接URL未设置（请设置 DATABASE_URL 环境变量）")
    
    def _get_db_connection(self):
        """获取数据库连接"""
        if psycopg2 is None:
            raise ImportError("psycopg2 未安装，请运行: pip install psycopg2-binary")
        return psycopg2.connect(self.database_url)
    
    def find_or_create_product(
        self,
        category: str,
        brand_name: str,
        model_name: str,
        model_no: str
    ) -> int:
        """
        查找或创建 product 记录
        
        Args:
            category: 商品类别
            brand_name: 标准化品牌名（英文）
            model_name: 标准化型号名（英文）
            model_no: 标准化型号编号（英文）
            
        Returns:
            product.id
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 先查找是否已存在
            cursor.execute(
                """
                SELECT id FROM product
                WHERE category = %s
                  AND brand_name = %s
                  AND model_name = %s
                  AND model_no = %s
                """,
                (category, brand_name, model_name, model_no)
            )
            row = cursor.fetchone()
            
            if row:
                product_id = row[0]
                cursor.close()
                conn.close()
                return product_id
            
            # 不存在，创建新记录
            cursor.execute(
                """
                INSERT INTO product (category, brand_name, model_name, model_no)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (category, brand_name, model_name, model_no)
            )
            product_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return product_id
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise Exception(f"查找或创建 product 失败: {e}")
    
    def aggregate_single_item(self, item_id: int) -> Optional[int]:
        """
        聚合单个商品
        
        Args:
            item_id: crawler_item.id
            
        Returns:
            product_id，如果失败则返回 None
        """
        conn = self._get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # 读取商品信息
            cursor.execute(
                """
                SELECT id, category, brand_name, model_name, model_no, product_id
                FROM crawler_item
                WHERE id = %s
                """,
                (item_id,)
            )
            item = cursor.fetchone()
            
            if not item:
                cursor.close()
                conn.close()
                return None
            
            # 如果已经关联了 product_id，直接返回
            if item['product_id']:
                cursor.close()
                conn.close()
                return item['product_id']
            
            # 归一化商品信息
            category = item['category'] or "watch"
            normalized_brand, normalized_model, normalized_model_no = Normalizer.normalize_item(
                item['brand_name'],
                item['model_name'],
                item['model_no'],
                category
            )
            
            # 如果归一化后仍有缺失，无法聚合
            if not normalized_brand or not normalized_model or not normalized_model_no:
                cursor.close()
                conn.close()
                return None
            
            # 查找或创建 product
            product_id = self.find_or_create_product(
                category,
                normalized_brand,
                normalized_model,
                normalized_model_no
            )
            
            # 更新 crawler_item 的 product_id
            cursor.execute(
                """
                UPDATE crawler_item
                SET product_id = %s
                WHERE id = %s
                """,
                (product_id, item_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            return product_id
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            print(f"[ProductAggregator] 聚合商品失败 (item_id={item_id}): {e}")
            return None
    
    def aggregate_items(
        self,
        batch_size: int = 100,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        批量聚合商品
        
        Args:
            batch_size: 每批处理的商品数量
            limit: 最多处理的商品数量，如果为None则处理所有未关联的商品
            
        Returns:
            统计信息字典：
            {
                "processed": 处理的商品数量,
                "success": 成功聚合的数量,
                "failed": 失败的数量,
                "skipped": 跳过的数量（已关联或数据不完整）
            }
        """
        conn = self._get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # 查询未关联的商品
            query = """
                SELECT id, category, brand_name, model_name, model_no, product_id
                FROM crawler_item
                WHERE product_id IS NULL
                ORDER BY id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            items = cursor.fetchall()
            
            print(f"[ProductAggregator] 找到 {len(items)} 个未关联的商品")
            
            for item in items:
                stats["processed"] += 1
                
                # 如果已经关联，跳过
                if item['product_id']:
                    stats["skipped"] += 1
                    continue
                
                # 归一化商品信息
                category = item['category'] or "watch"
                normalized_brand, normalized_model, normalized_model_no = Normalizer.normalize_item(
                    item['brand_name'],
                    item['model_name'],
                    item['model_no'],
                    category
                )
                
                # 如果归一化后仍有缺失，跳过
                if not normalized_brand or not normalized_model or not normalized_model_no:
                    stats["skipped"] += 1
                    continue
                
                try:
                    # 查找或创建 product
                    product_id = self.find_or_create_product(
                        category,
                        normalized_brand,
                        normalized_model,
                        normalized_model_no
                    )
                    
                    # 更新 crawler_item 的 product_id
                    cursor.execute(
                        """
                        UPDATE crawler_item
                        SET product_id = %s
                        WHERE id = %s
                        """,
                        (product_id, item['id'])
                    )
                    stats["success"] += 1
                    
                    # 每批提交一次
                    if stats["success"] % batch_size == 0:
                        conn.commit()
                        print(f"[ProductAggregator] 已处理 {stats['processed']} 个商品，成功 {stats['success']} 个")
                    
                except Exception as e:
                    stats["failed"] += 1
                    print(f"[ProductAggregator] 聚合商品失败 (item_id={item['id']}): {e}")
            
            # 最终提交
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[ProductAggregator] 聚合完成: {stats}")
            return stats
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            print(f"[ProductAggregator] 批量聚合失败: {e}")
            raise

