"""
video_downloader.py
Antigravity Ver.1.0 - Step 0: 動画自動ダウンロードエンジン

【役割】
UTAGEコースURLからレッスン動画を自動収集・ダウンロードし、
master_batch_refiner.py が処理できる形式でVIDEOS_INPUT_DIRに保存する。

【参照元】loom_auto.py（改造・統合）
【出力】{VIDEOS_INPUT_DIR}/{02d}_{タイトル}.mp4
"""

import os
import re
import subprocess
import time
import logging
import sys
import io
from datetime import datetime
from dotenv import load_dotenv

# .env ファイルをロード
load_dotenv()

# UTF-8 出力を徹底
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ─────────────────────────────────────────
# ロギング設定
# ─────────────────────────────────────────
logs_dir = os.getenv("LOGS_DIR", "./logs")
os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(
    logs_dir,
    f"downloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')

file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)
logger.info(f"Log file: {log_file}")

# ─────────────────────────────────────────
# 環境変数読み込み
# ─────────────────────────────────────────
UTAGE_COURSE_URL  = os.getenv("UTAGE_COURSE_URL")
VIDEOS_INPUT_DIR  = os.getenv("VIDEOS_INPUT_DIR",
                               r"D:\Knowledge_Base\Brain_Marketing\videos\downloaded_videos")
FFMPEG_PATH       = os.getenv("FFMPEG_PATH",
                               r"C:\Users\nario\ffmpeg\bin\ffmpeg.exe")
CHROME_USER_DATA  = os.getenv("CHROME_USER_DATA_DIR", "chrome_profile")
VIDEO_LIST_FILE   = os.getenv("VIDEO_LIST_FILE", "video_list.txt")

# 起動時バリデーション
if not UTAGE_COURSE_URL:
    raise ValueError(
        "UTAGE_COURSE_URL は .env ファイルで設定されている必要があります。\n"
        "例: UTAGE_COURSE_URL=https://utage-system.com/members/.../course/..."
    )

if not os.path.exists(FFMPEG_PATH):
    raise FileNotFoundError(
        f"FFmpegが見つかりません: {FFMPEG_PATH}\n"
        f"FFMPEG_PATH を .env で正しく設定してください。"
    )

os.makedirs(VIDEOS_INPUT_DIR, exist_ok=True)
logger.info(f"UTAGE_COURSE_URL : {UTAGE_COURSE_URL}")
logger.info(f"VIDEOS_INPUT_DIR : {VIDEOS_INPUT_DIR}")
logger.info(f"FFMPEG_PATH      : {FFMPEG_PATH}")
logger.info(f"CHROME_USER_DATA : {CHROME_USER_DATA}")


# ─────────────────────────────────────────
# Chrome パス自動検索（loom_auto.py より流用）
# ─────────────────────────────────────────
def get_chrome_path() -> str | None:
    """
    Windows上でChromeの実行ファイルパスを自動検索する。
    見つからない場合は None を返す。
    """
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            logger.info(f"Chrome found: {path}")
            return path
    logger.error("Chrome not found in any known location.")
    return None


# ─────────────────────────────────────────
# メインクラス
# ─────────────────────────────────────────
class VideoDownloader:
    """
    Antigravity Step 0: 動画自動ダウンロードエンジン

    処理フロー:
        1. Chrome を CDP モードで起動
        2. UTAGE コースページへ遷移・ログイン待機
        3. レッスンリンクを全件取得
        4. 各レッスンの iframe から Loom / YouTube URL を抽出
        5. video_list.txt に保存
        6. yt-dlp で全動画をダウンロード → VIDEOS_INPUT_DIR に保存
    """

    def __init__(self):
        self.chrome_path   = get_chrome_path()
        self.chrome_proc   = None
        self.video_list    = []   # [{"title": str, "url": str}]
        self.failed_list   = []   # ダウンロード失敗分

    # --------------------------------------------------
    # Step A: Chrome CDP 起動
    # --------------------------------------------------
    def launch_chrome(self) -> bool:
        """
        Chrome をリモートデバッグポート 9222 で起動する。
        成功時 True、失敗時 False を返す。
        （実装は #005-B）
        """
        logger.info("[STUB] launch_chrome() - 実装予定 (#005-B)")
        return True

    # --------------------------------------------------
    # Step B: UTAGE レッスンリンク収集
    # --------------------------------------------------
    def collect_lesson_links(self) -> list[dict]:
        """
        Playwright で UTAGE コースページを解析し、
        レッスンリンクのタイトルと URL を返す。
        戻り値: [{"title": str, "lesson_url": str}, ...]
        （実装は #005-B）
        """
        logger.info("[STUB] collect_lesson_links() - 実装予定 (#005-B)")
        return []

    # --------------------------------------------------
    # Step C: iframe から動画 URL 抽出
    # --------------------------------------------------
    def extract_video_url(self, lesson_url: str) -> str | None:
        """
        レッスンページの iframe src を解析し、
        Loom または YouTube の動画 URL を返す。
        見つからない場合は None を返す。
        （実装は #005-B）
        """
        logger.info(f"[STUB] extract_video_url({lesson_url}) - 実装予定 (#005-B)")
        return None

    # --------------------------------------------------
    # Step D: video_list.txt 保存
    # --------------------------------------------------
    def save_video_list(self) -> None:
        """
        self.video_list を VIDEO_LIST_FILE に
        「タイトル###URL」形式で保存する。
        （実装は #005-B）
        """
        logger.info("[STUB] save_video_list() - 実装予定 (#005-B)")

    # --------------------------------------------------
    # Step E: yt-dlp ダウンロード
    # --------------------------------------------------
    def download_all(self) -> None:
        """
        self.video_list の全動画を yt-dlp でダウンロードする。
        出力ファイル名: {02d}_{タイトル}.mp4
        失敗した動画は self.failed_list に記録する。
        （実装は #005-B）
        """
        logger.info("[STUB] download_all() - 実装予定 (#005-B)")

    # --------------------------------------------------
    # 失敗リスト保存
    # --------------------------------------------------
    def save_failed_list(self) -> None:
        """
        ダウンロード失敗した動画を
        logs/failed_downloads.txt に記録する。
        （実装は #005-B）
        """
        logger.info("[STUB] save_failed_list() - 実装予定 (#005-B)")

    # --------------------------------------------------
    # メイン実行
    # --------------------------------------------------
    def run(self) -> None:
        """
        Step 0 全体を順次実行するエントリーポイント。
        """
        logger.info("=" * 80)
        logger.info("Antigravity Step 0: Video Downloader Started")
        logger.info("=" * 80)

        # A: Chrome 起動
        if not self.launch_chrome():
            logger.error("Chrome の起動に失敗しました。処理を中断します。")
            return

        # B: レッスンリンク収集
        lessons = self.collect_lesson_links()
        if not lessons:
            logger.error("レッスンリンクが見つかりませんでした。処理を中断します。")
            return
        logger.info(f"レッスン数: {len(lessons)} 件")

        # C: 各レッスンから動画 URL 抽出
        for lesson in lessons:
            url = self.extract_video_url(lesson["lesson_url"])
            if url:
                self.video_list.append({
                    "title": lesson["title"],
                    "url":   url
                })
            else:
                logger.warning(f"動画URLが見つかりませんでした: {lesson['title']}")

        logger.info(f"動画URL取得: {len(self.video_list)} 件 / {len(lessons)} 件")

        # D: video_list.txt 保存
        self.save_video_list()

        # E: ダウンロード実行
        self.download_all()

        # 失敗リスト保存
        if self.failed_list:
            self.save_failed_list()

        logger.info("=" * 80)
        logger.info("Antigravity Step 0: Video Downloader Completed")
        logger.info(f"成功: {len(self.video_list) - len(self.failed_list)} 本 / "
                    f"失敗: {len(self.failed_list)} 本")
        logger.info("=" * 80)


# ─────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────
if __name__ == "__main__":
    downloader = VideoDownloader()
    downloader.run()
