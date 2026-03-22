import sqlite3
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class SidecarDBHelper:
    """Mk2_Sidecar_XX.db の SQLite ヘルパークラス"""

    @staticmethod
    def load_evidence_index(db_path: str) -> List[Dict[str, Any]]:
        """evidence_index テーブル全体を読み込む"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM evidence_index ORDER BY start_ms"
            )
            rows = cursor.fetchall()

            evidence_list = [dict(row) for row in rows]
            conn.close()

            logger.info(
                f"Loaded {len(evidence_list)} records from {db_path}"
            )
            return evidence_list

        except sqlite3.OperationalError as e:
            logger.error(f"DB Error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading evidence_index: {e}")
            return []

    @staticmethod
    def get_timestamp_for_element(
        element_id: str, db_path: str
    ) -> Optional[Dict[str, int]]:
        """特定の element_id のタイムスタンプを取得"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT start_ms, end_ms FROM evidence_index WHERE element_id = ?",
                (element_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {"start_ms": row[0], "end_ms": row[1]}
            return None

        except Exception as e:
            logger.error(
                f"Error getting timestamp for {element_id}: {e}"
            )
            return None

    @staticmethod
    def get_visual_text_for_element(
        element_id: str, db_path: str
    ) -> Optional[str]:
        """特定の element_id の visual_text を取得"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT visual_text FROM evidence_index WHERE element_id = ?",
                (element_id,)
            )
            row = cursor.fetchone()
            conn.close()

            return row[0] if row else None

        except Exception as e:
            logger.error(
                f"Error getting visual_text for {element_id}: {e}"
            )
            return None

    @staticmethod
    def get_high_confidence_records(
        db_path: str, min_visual_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """信頼度の高いレコードのみを取得"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM evidence_index WHERE visual_score >= ? ORDER BY start_ms",
                (min_visual_score,)
            )
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting high confidence records: {e}")
            return []

    @staticmethod
    def get_coverage_duration(db_path: str) -> int:
        """evidence_index 全体がカバーする総時間（ミリ秒）を計算"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT SUM(end_ms - start_ms) as total_duration FROM evidence_index"
            )
            result = cursor.fetchone()
            conn.close()

            return int(result[0]) if result[0] else 0

        except Exception as e:
            logger.error(f"Error calculating coverage duration: {e}")
            return 0
