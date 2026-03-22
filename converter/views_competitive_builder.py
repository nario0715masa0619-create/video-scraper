import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ViewsCompetitiveBuilder:
    """views.competitive を構築するクラス（Phase 1）"""

    def __init__(
        self,
        json_extractor,
        knowledge_analyzer,
        keyword_extractor,
        duration_seconds: float
    ):
        self.json_extractor = json_extractor
        self.knowledge_analyzer = knowledge_analyzer
        self.keyword_extractor = keyword_extractor
        self.duration_seconds = duration_seconds

    def build(
        self,
        video_title: str = "",
        view_count: Optional[int] = None,
        like_count: Optional[int] = None,
        comment_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """views.competitive 全体を構築"""
        view_count = view_count or 0
        like_count = like_count
        comment_count = comment_count

        engagement_rate = self._calculate_engagement_rate(
            view_count, like_count, comment_count
        )

        knowledge_value_index = self.knowledge_analyzer.get_knowledge_value_index(
            engagement_rate
        )
        expected_roi_score = self.knowledge_analyzer.get_expected_roi_score(
            engagement_rate
        )
        content_intelligence_score = self.knowledge_analyzer.get_content_intelligence_score(
            engagement_rate
        )

        primary_theme_keywords = self.keyword_extractor.extract_primary_theme_keywords(
            video_title=video_title
        )
        keyword_mention_frequency = self.keyword_extractor.get_keyword_mention_frequency()
        keyword_segment_count = self.keyword_extractor.get_keyword_segment_count()

        performance_score = self._calculate_performance_score(
            engagement_rate,
            content_intelligence_score
        )
        trend_score = self._calculate_trend_score(
            view_count, engagement_rate
        )

        content_role = self._estimate_content_role()

        return {
            "###_metadata": {
                "measurement_timestamp": self._get_iso_timestamp(),
                "data_sources": {
                    "youtube_api": False,
                    "sidecar_db": True,
                    "video_scraper": True
                },
                "note": "Phase 1: YouTube API なし。Mk2_Sidecar_XX.db と JSON のみを使用"
            },

            "view_count": view_count,
            "impression_count": None,
            "click_through_rate": None,
            "average_view_duration_sec": None,
            "average_view_duration_percent": None,
            "total_watch_time_hours": None,
            "unique_viewers": None,
            "days_since_publish": 0,
            "daily_average_views": 0.0,

            "like_count": like_count,
            "comment_count": comment_count,
            "like_to_view_ratio": self._calculate_ratio(like_count, view_count),
            "comment_to_view_ratio": self._calculate_ratio(comment_count, view_count),
            "engagement_rate": round(engagement_rate, 4),
            "shares_count": None,

            "subscriber_gain": None,
            "subscriber_loss": None,
            "net_subscriber_gain": None,

            "trend_score": round(trend_score, 2),
            "trend_velocity": None,
            "momentum_score": None,
            "primary_traffic_sources": None,
            "youtube_search_traffic_ratio": None,
            "external_traffic_ratio": None,
            "direct_traffic_ratio": None,

            "knowledge_elements_count": self.json_extractor.get_knowledge_elements_count(),
            "knowledge_density_per_minute": round(
                self.knowledge_analyzer.get_knowledge_density_per_minute(), 3
            ),
            "high_purity_elements_ratio": round(
                self.json_extractor.get_high_purity_elements_ratio(), 3
            ),
            "knowledge_type_distribution": self.json_extractor.get_knowledge_type_distribution(),

            "knowledge_coverage_seconds": self.knowledge_analyzer.get_knowledge_coverage_seconds(),
            "knowledge_coverage_ratio": round(
                self.knowledge_analyzer.get_knowledge_coverage_ratio(), 3
            ),
            "knowledge_distribution_balance": round(
                self.knowledge_analyzer.get_knowledge_distribution_balance(), 2
            ),
            "critical_segments_count": self.knowledge_analyzer.get_critical_segments_count(),

            "primary_theme_keywords": primary_theme_keywords,
            "keyword_mention_frequency": keyword_mention_frequency,
            "keyword_first_appearance_ms": {},
            "keyword_segment_count": keyword_segment_count,

            "actionability_score": round(
                self.json_extractor.get_actionability_score(), 1
            ),
            "content_maturity_score": round(
                self.knowledge_analyzer.get_content_maturity_score(), 2
            ),
            "knowledge_value_index": round(knowledge_value_index, 1),
            "expected_roi_score": round(expected_roi_score, 2),

            "visual_evidence_coverage": self.knowledge_analyzer.get_visual_evidence_coverage(),
            "visual_text_richness_score": round(
                self._calculate_visual_text_richness(), 2
            ),
            "evidence_credibility_average": round(
                self.knowledge_analyzer.get_evidence_credibility_average(), 2
            ),
            "screenshot_worthy_segments": len([
                r for r in self.knowledge_analyzer.evidence_records
                if r.get("visual_score", 0) > 0.8
            ]),

            "content_intelligence_score": round(content_intelligence_score, 1),
            "visual_knowledge_synthesis_ratio": round(
                self.knowledge_analyzer.get_visual_knowledge_synthesis_ratio(), 2
            ),
            "competitive_moat_strength": round(
                self._calculate_competitive_moat_strength(), 2
            ),

            "performance_score": round(performance_score, 1),
            "trend_score": round(trend_score, 2),
            "content_role": content_role,
            "recommended_reuse_score": round(
                self._calculate_recommended_reuse_score(
                    knowledge_value_index,
                    engagement_rate,
                    performance_score
                ),
                2
            ),
            "reuse_recommendation": self._generate_reuse_recommendation(
                content_intelligence_score,
                self.knowledge_analyzer.get_knowledge_density_per_minute(),
                self.knowledge_analyzer.get_visual_knowledge_synthesis_ratio(),
                expected_roi_score
            )
        }

    def _calculate_engagement_rate(
        self,
        view_count: int,
        like_count: Optional[int],
        comment_count: Optional[int]
    ) -> float:
        """エンゲージメント率を計算"""
        if view_count == 0 or like_count is None or comment_count is None:
            return 0.0

        return (like_count + comment_count * 2) / view_count

    def _calculate_ratio(
        self,
        numerator: Optional[int],
        denominator: int
    ) -> Optional[float]:
        """比率を計算（推定値の場合は None を返す）"""
        if numerator is None or denominator == 0:
            return None

        return round(numerator / denominator, 4)

    def _calculate_performance_score(
        self,
        engagement_rate: float,
        content_intelligence_score: float
    ) -> float:
        """Performance score を計算"""
        return (engagement_rate * 10 + content_intelligence_score / 1.5) / 2

    def _calculate_trend_score(
        self,
        view_count: int,
        engagement_rate: float
    ) -> float:
        """Trend score を計算"""
        normalized_views = min(1.0, view_count / 100000)
        normalized_engagement = min(1.0, engagement_rate / 0.1)

        return (normalized_views * 0.6 + normalized_engagement * 0.4)

    def _estimate_content_role(self) -> str:
        """Content role を推定"""
        avg_purity = self.json_extractor.get_average_purity_score()

        if avg_purity >= 85:
            return "education"
        elif avg_purity >= 70:
            return "sales"
        elif avg_purity >= 50:
            return "branding"
        else:
            return "hiring"

    def _calculate_visual_text_richness(self) -> float:
        """ビジュアルテキストの豊富さスコア"""
        total_length = sum(
            len(record.get("visual_text", ""))
            for record in self.knowledge_analyzer.evidence_records
        )

        max_length = 10000

        return min(1.0, total_length / max_length)

    def _calculate_competitive_moat_strength(self) -> float:
        """競争優位性強度を計算"""
        high_purity = self.json_extractor.get_high_purity_elements_ratio()
        density = self.knowledge_analyzer.get_knowledge_density_per_minute()
        actionability = self.json_extractor.get_actionability_score() / 100.0

        normalized_density = min(1.0, density / 0.5)

        return high_purity * 0.4 + normalized_density * 0.3 + actionability * 0.3

    def _calculate_recommended_reuse_score(
        self,
        knowledge_value_index: float,
        engagement_rate: float,
        performance_score: float
    ) -> float:
        """再利用推奨スコア（0.0 ~ 1.0）"""
        kvi_factor = min(1.0, knowledge_value_index / 100.0)
        engagement_factor = min(1.0, engagement_rate * 10)
        perf_factor = min(1.0, performance_score / 100.0)

        return (kvi_factor * 0.4 + engagement_factor * 0.3 + perf_factor * 0.3)

    def _generate_reuse_recommendation(
        self,
        content_intelligence_score: float,
        knowledge_density: float,
        visual_synthesis_ratio: float,
        expected_roi_score: float
    ) -> str:
        """再利用推奨テキストを生成"""
        reasons = []

        if content_intelligence_score >= 75:
            reasons.append(
                f"コンテンツ知性スコアが高い（{content_intelligence_score:.1f}）"
            )

        if knowledge_density >= 0.5:
            reasons.append(
                f"知識密度が高い（{knowledge_density:.2f}/分）"
            )

        if visual_synthesis_ratio >= 0.7:
            reasons.append(
                f"{int(visual_synthesis_ratio*100)}%が視覚的エビデンス付き"
            )

        if expected_roi_score >= 0.75:
            reasons.append(
                f"ROI期待値スコアが高い（{expected_roi_score:.2f}）"
            )

        if not reasons:
            return "このコンテンツの再利用可能性は限定的です"

        return "このコンテンツは以下の理由から再利用価値が高い：（1）" + "，（2）".join(reasons)

    @staticmethod
    def _get_iso_timestamp() -> str:
        """現在時刻を ISO 8601 形式で返す"""
        return datetime.utcnow().isoformat() + "Z"
