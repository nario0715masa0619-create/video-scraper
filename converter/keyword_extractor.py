import re
import logging
from typing import Dict, List, Any
from collections import Counter

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """キーワード抽出・分析クラス（Phase 1：簡易版）"""

    def __init__(
        self,
        json_extractor,
        evidence_records: List[Dict[str, Any]]
    ):
        self.json_extractor = json_extractor
        self.evidence_records = evidence_records

    def extract_primary_theme_keywords(
        self,
        video_title: str = "",
        max_keywords: int = 5
    ) -> List[str]:
        """主要なテーマキーワードを抽出（簡易版）"""
        text_parts = []

        if video_title:
            text_parts.append(video_title)

        for pin in self.json_extractor.center_pins:
            content = pin.get("content", "")
            if content:
                text_parts.append(content)

        combined_text = " ".join(text_parts)

        keywords = self._extract_words_simple(combined_text)

        keyword_freq = Counter(keywords)
        top_keywords = [
            word for word, freq in keyword_freq.most_common(max_keywords)
        ]

        logger.info(f"Extracted {len(top_keywords)} primary theme keywords")
        return top_keywords

    def get_keyword_mention_frequency(self) -> Dict[str, int]:
        """キーワードの言及頻度を計算"""
        if not self.evidence_records:
            return {}

        all_visual_text = " ".join(
            record.get("visual_text", "") for record in self.evidence_records
            if record.get("visual_text")
        )

        keywords = self._extract_words_simple(all_visual_text)
        frequency = Counter(keywords)

        return {
            word: count for word, count in frequency.items()
            if count >= 3
        }

    def get_keyword_segment_count(self) -> Dict[str, int]:
        """各キーワードが登場するシーン（segment）数を計算"""
        if not self.evidence_records:
            return {}

        keyword_segments = {}

        for record in self.evidence_records:
            visual_text = record.get("visual_text", "")
            if not visual_text:
                continue

            keywords = self._extract_words_simple(visual_text)

            for keyword in set(keywords):
                if keyword not in keyword_segments:
                    keyword_segments[keyword] = 0
                keyword_segments[keyword] += 1

        return {
            word: count for word, count in keyword_segments.items()
            if count >= 2
        }

    def _extract_words_simple(self, text: str, min_length: int = 2) -> List[str]:
        """テキストから単語を簡易抽出（Phase 1）"""
        english_words = re.findall(r'[A-Za-z]{' + str(min_length) + r',}', text)

        japanese_words = re.findall(
            r'[぀-ゟ゠-ヿ一-鿿]{' + str(min_length) + r',}',
            text
        )

        english_words = [w.lower() for w in english_words]

        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        english_words = [w for w in english_words if w not in stopwords]

        return english_words + japanese_words
