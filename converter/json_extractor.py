import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class JSONExtractor:
    """Mk2_Core_XX.json から知識系情報を抽出するクラス"""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.center_pins = self._load_center_pins()

    def _load_center_pins(self) -> List[Dict[str, Any]]:
        """Mk2_Core_XX.json を読み込み、center_pins を抽出"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                center_pins = data
            elif isinstance(data, dict) and "center_pins" in data:
                center_pins = data["center_pins"]
            else:
                center_pins = data if isinstance(data, list) else []

            logger.info(f"Loaded {len(center_pins)} center_pins from {self.json_path}")
            return center_pins

        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return []

    def get_knowledge_elements_count(self) -> int:
        """動画内の center_pins 総数"""
        return len(self.center_pins)

    def get_knowledge_type_distribution(self) -> Dict[str, int]:
        """知識要素のタイプ分布を計算"""
        distribution = {
            "FACT": 0,
            "LOGIC": 0,
            "SOP": 0,
            "CASE": 0
        }

        for pin in self.center_pins:
            pin_type = pin.get("type", "UNKNOWN")
            if pin_type in distribution:
                distribution[pin_type] += 1

        return distribution

    def get_high_purity_elements_ratio(self, threshold: float = 80.0) -> float:
        """高純度ノウハウ（purity >= threshold）の比率"""
        if not self.center_pins:
            return 0.0

        high_purity_count = sum(
            1 for pin in self.center_pins
            if pin.get("base_purity_score", 0) >= threshold
        )

        return high_purity_count / len(self.center_pins)

    def get_actionable_elements(self) -> List[Dict[str, Any]]:
        """実行可能なノウハウ（type: SOP or CASE）を抽出"""
        return [
            pin for pin in self.center_pins
            if pin.get("type") in ["SOP", "CASE"]
        ]

    def get_actionability_score(self) -> float:
        """実行可能性スコア = actionable items の平均 purity_score"""
        actionable = self.get_actionable_elements()

        if not actionable:
            return 0.0

        avg_purity = sum(
            pin.get("base_purity_score", 0) for pin in actionable
        ) / len(actionable)

        return min(100.0, max(0.0, avg_purity))

    def get_average_purity_score(self) -> float:
        """全 center_pins の平均 purity_score"""
        if not self.center_pins:
            return 0.0

        avg = sum(
            pin.get("base_purity_score", 0) for pin in self.center_pins
        ) / len(self.center_pins)

        return min(100.0, max(0.0, avg))

    def get_elements_by_type(self, element_type: str) -> List[Dict[str, Any]]:
        """特定のタイプの center_pins を取得"""
        return [
            pin for pin in self.center_pins
            if pin.get("type") == element_type
        ]

    def get_element_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """element_id から center_pin を検索"""
        for pin in self.center_pins:
            if pin.get("element_id") == element_id:
                return pin
        return None
