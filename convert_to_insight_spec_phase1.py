#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: Convert video-scraper output to video-insight-spec format
Data sources: Mk2_Core_XX.json + Mk2_Sidecar_XX.db only
No YouTube API integration
"""

import os
import json
import argparse
import logging
import sys
from pathlib import Path
from converter.db_helper import SidecarDBHelper
from converter.json_extractor import JSONExtractor
from converter.knowledge_analyzer import KnowledgeAnalyzer
from converter.keyword_extractor import KeywordExtractor
from converter.views_competitive_builder import ViewsCompetitiveBuilder
from converter.insights_converter import InsightsConverter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Convert video-scraper output to video-insight-spec format (Phase 1)"
    )
    parser.add_argument(
        "--lecture-id",
        type=str,
        required=True,
        help="Lecture ID (e.g., '01')"
    )
    parser.add_argument(
        "--core-json",
        type=str,
        help="Path to Mk2_Core_XX.json (auto-detect if not specified)"
    )
    parser.add_argument(
        "--sidecar-db",
        type=str,
        help="Path to Mk2_Sidecar_XX.db (auto-detect if not specified)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for insight_spec JSON"
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default=r"D:\Knowledge_Base\Brain_Marketing\archive",
        help="Archive directory containing Mk2 files"
    )

    args = parser.parse_args()

    # パス自動検出
    lecture_id = args.lecture_id
    core_json_path = args.core_json or os.path.join(
        args.archive_dir, f"Mk2_Core_{lecture_id}.json"
    )
    sidecar_db_path = args.sidecar_db or os.path.join(
        args.archive_dir, f"Mk2_Sidecar_{lecture_id}.db"
    )
    output_path = args.output or os.path.join(
        args.archive_dir, f"insight_spec_{lecture_id}.json"
    )

    # ファイル存在確認
    if not os.path.exists(core_json_path):
        logger.error(f"Core JSON not found: {core_json_path}")
        sys.exit(1)

    if not os.path.exists(sidecar_db_path):
        logger.error(f"Sidecar DB not found: {sidecar_db_path}")
        sys.exit(1)

    logger.info(f"Processing lecture_id: {lecture_id}")
    logger.info(f"Core JSON: {core_json_path}")
    logger.info(f"Sidecar DB: {sidecar_db_path}")

    try:
        # Step 1: Load JSON
        json_extractor = JSONExtractor(core_json_path)
        
        # Step 2: Load DB
        evidence_records = SidecarDBHelper.load_evidence_index(sidecar_db_path)
        
        # Step 3: Analyze knowledge
        # Get video duration from evidence records
        duration_ms = sum(
            record.get("end_ms", 0) - record.get("start_ms", 0)
            for record in evidence_records
        )
        duration_seconds = max(duration_ms / 1000, 1.0)  # At least 1 second
        
        knowledge_analyzer = KnowledgeAnalyzer(
            json_extractor,
            evidence_records,
            duration_seconds
        )
        
        # Step 4: Extract keywords
        keyword_extractor = KeywordExtractor(
            json_extractor,
            evidence_records
        )
        
        # Step 5: Build views.competitive
        views_builder = ViewsCompetitiveBuilder(
            json_extractor,
            knowledge_analyzer,
            keyword_extractor,
            duration_seconds
        )
        
        views_competitive = views_builder.build(
            video_title=f"Lecture {lecture_id}",
            view_count=0,  # No data available in Phase 1
            like_count=None,
            comment_count=None
        )
        
        # Step 6: Build video_meta and knowledge_core
        video_meta = {
            "video_id": lecture_id,
            "channel_id": None,
            "title": f"Lecture {lecture_id}",
            "url": None,
            "published_at": None
        }
        
        knowledge_core = {
            "center_pins": json_extractor.center_pins,
            "knowledge_points": []
        }
        
        # Step 7: Generate final JSON
        insight_spec = InsightsConverter.build_insight_spec(
            video_meta,
            knowledge_core,
            views_competitive
        )
        
        # Step 8: Save
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        if InsightsConverter.save_to_file(insight_spec, output_path):
            logger.info(f"✅ Successfully saved to {output_path}")
        else:
            logger.error("Failed to save output file")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
