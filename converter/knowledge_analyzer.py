import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class KnowledgeAnalyzer:
    """知識コンテンツの分析・スコアリングを行うクラス"""

    def __init__(
        self,
        json_extractor,
        db_helper_result: List[Dict[str, Any]],
        duration_seconds: float
    ):
        self.json_extractor = json_extractor
        self.evidence_records = db_helper_result
        self.duration_seconds = duration_seconds

    def get_knowledge_density_per_minute(self) -> float:
        """1分あたりのノウハウ密度"""
        if self.duration_seconds == 0:
            return 0.0

        elements_count = self.json_extractor.get_knowledge_elements_count()
        duration_minutes = self.duration_seconds / 60

        return elements_count / duration_minutes if duration_minutes > 0 else 0.0

    def get_knowledge_coverage_seconds(self) -> int:
        """ノウハウが登場する総時間（秒）"""
        if not self.evidence_records:
            return 0

        total_ms = sum(
            record.get("end_ms", 0) - record.get("start_ms", 0)
            for record in self.evidence_records
        )

        return int(total_ms / 1000)

    def get_knowledge_coverage_ratio(self) -> float:
        """動画全体に対するノウハウカバレッジ率"""
        if self.duration_seconds == 0:
            return 0.0

        coverage_seconds = self.get_knowledge_coverage_seconds()
        return min(1.0, coverage_seconds / self.duration_seconds)

    def get_visual_evidence_coverage(self) -> int:
        """視覚的エビデンスがある時間数（秒）"""
        if not self.evidence_records:
            return 0

        total_ms = sum(
            record.get("end_ms", 0) - record.get("start_ms", 0)
            for record in self.evidence_records
            if record.get("visual_score", 0) > 0.5
        )

        return int(total_ms / 1000)

    def get_evidence_credibility_average(self) -> float:
        """エビデンス信頼性の平均"""
        if not self.evidence_records:
            return 0.0

        avg_score = sum(
            record.get("visual_score", 0) for record in self.evidence_records
        ) / len(self.evidence_records)

        return min(1.0, max(0.0, avg_score))

    def get_critical_segments_count(self, purity_threshold: float = 90.0) -> int:
        """重要シーン数（purity > threshold）"""
        center_pins = self.json_extractor.center_pins

        return sum(
            1 for pin in center_pins
            if pin.get("base_purity_score", 0) > purity_threshold
        )

    def get_knowledge_distribution_balance(self) -> float:
        """ノウハウの分布バランス"""
        if not self.evidence_records or len(self.evidence_records) < 2:
            return 0.5

        start_times = [
            record.get("start_ms", 0) for record in self.evidence_records
        ]

        mean_time = sum(start_times) / len(start_times)
        variance = sum(
            (x - mean_time) ** 2 for x in start_times
        ) / len(start_times)
        std_dev = variance ** 0.5

        max_time = max(start_times)
        if max_time == 0:
            return 0.5

        relative_std = std_dev / max_time
        balance_score = min(1.0, relative_std / 0.5)

        return balance_score

    def get_content_maturity_score(self) -> float:
        """コンテンツ成熟度スコア"""
        density = self.get_knowledge_density_per_minute()
        high_purity_ratio = self.json_extractor.get_high_purity_elements_ratio()

        normalized_density = min(1.0, density / 0.5)

        return (normalized_density * 0.6 + high_purity_ratio * 0.4)

    def get_knowledge_value_index(self, engagement_rate: float = 0.0) -> float:
        """ノウハウ価値指数（0.0 ~ 100.0）"""
        density = self.get_knowledge_density_per_minute()
        actionability = self.json_extractor.get_actionability_score() / 100.0

        engagement_factor = min(1.0, engagement_rate)

        index = (density * 0.3 + actionability * 0.4 + engagement_factor * 0.3) * 100

        return min(100.0, max(0.0, index))

    def get_expected_roi_score(self, engagement_rate: float = 0.0) -> float:
        """ROI 期待値スコア（0.0 ~ 1.0）"""
        density = self.get_knowledge_density_per_minute()
        normalized_density = min(1.0, density / 0.5)

        actionability = self.json_extractor.get_actionability_score() / 100.0
        engagement_factor = min(1.0, engagement_rate)
        coverage = self.get_knowledge_coverage_ratio()

        roi_score = (
            normalized_density * 0.3 +
            actionability * 0.3 +
            engagement_factor * 0.2 +
            coverage * 0.2
        )

        return min(1.0, max(0.0, roi_score))

    def get_visual_knowledge_synthesis_ratio(self) -> float:
        """ビジュアル・知識シナジー率（0.0 ~ 1.0）"""
        visual_coverage = self.get_visual_evidence_coverage()
        knowledge_coverage = self.get_knowledge_coverage_seconds()

        if knowledge_coverage == 0:
            return 0.0

        return min(1.0, visual_coverage / knowledge_coverage)

    def get_content_intelligence_score(self, engagement_rate: float = 0.0) -> float:
        """コンテンツ知性スコア（0.0 ~ 100.0）"""
        density = self.get_knowledge_density_per_minute()
        normalized_density = min(1.0, density / 0.5)

        actionability = self.json_extractor.get_actionability_score() / 100.0
        engagement_factor = min(1.0, engagement_rate)
        coverage = self.get_knowledge_coverage_ratio()
        credibility = self.get_evidence_credibility_average()

        intelligence_score = (
            normalized_density * 0.25 +
            actionability * 0.25 +
            engagement_factor * 0.15 +
            coverage * 0.20 +
            credibility * 0.15
        ) * 100

        return min(100.0, max(0.0, intelligence_score))
