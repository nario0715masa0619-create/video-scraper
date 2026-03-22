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
        """
        if not self.chrome_path:
            logger.error("Chrome が見つかりません。インストール状況を確認してください。")
            return False

        logger.info(f"Chrome を CDP モードで起動します: {self.chrome_path}")
        try:
            self.chrome_proc = subprocess.Popen([
                self.chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={CHROME_USER_DATA}",
                "--no-first-run",
                UTAGE_COURSE_URL
            ])
            time.sleep(5)  # Chrome 起動待機
            logger.info("Chrome 起動完了。ログイン待機中...")
            return True
        except Exception as e:
            logger.error(f"Chrome 起動失敗: {e}")
            return False

    # --------------------------------------------------
    # Step B: UTAGE レッスンリンク収集
    # --------------------------------------------------
    def collect_lesson_links(self) -> list[dict]:
        """
        Playwright で UTAGE コースページを解析し、
        レッスンリンクのタイトルと URL を返す。
        """
        from playwright.sync_api import sync_playwright

        lessons = []
        try:
            with sync_playwright() as p:
                logger.info("Playwright で Chrome に接続します...")
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                page = browser.contexts[0].pages[0]
                page.bring_to_front()

                print("\n" + "=" * 50)
                print("🔑 UTAGE にログインして、コース一覧画面を表示してください。")
                print("   準備ができたら Enter を押してください。")
                print("=" * 50)
                input()

                # レッスンリンクを取得
                page.wait_for_selector(
                    'a:has-text("受講する"), a:has-text("視聴する")',
                    timeout=15000
                )
                links = page.locator(
                    'a:has-text("受講する"), a:has-text("視聴する")'
                ).all()

                logger.info(f"{len(links)} 件のレッスンリンクを検出しました。")

                new_page = browser.contexts[0].new_page()
                for i, link in enumerate(links):
                    try:
                        # タイトル取得
                        title_raw = link.evaluate(
                            "node => node.closest('tr')?.innerText || node.innerText"
                        )
                        title = re.sub(
                            r'[\\/:*?"<>|]', "_",
                            title_raw.split('\n')[0]
                                .replace("受講する", "")
                                .replace("視聴する", "")
                                .strip()
                        )
                        # URL 取得
                        href = link.get_attribute("href")
                        if not href:
                            continue
                        full_url = (
                            href if href.startswith("http")
                            else f"https://utage-system.com{href}"
                        )
                        lessons.append({"title": title, "lesson_url": full_url})
                        logger.info(f"  [{i+1}/{len(links)}] {title}")
                    except Exception as e:
                        logger.warning(f"  [{i+1}] リンク解析スキップ: {e}")
                        continue

                # URL 抽出も同一セッションで実施
                for lesson in lessons:
                    url = self._extract_video_url_in_session(new_page, lesson["lesson_url"])
                    if url:
                        lesson["url"] = url
                    else:
                        lesson["url"] = None

                new_page.close()
                logger.info(f"レッスンリンク収集完了: {len(lessons)} 件")

        except Exception as e:
            logger.error(f"collect_lesson_links 失敗: {e}")

        return lessons

    # --------------------------------------------------
    # Step C: iframe から動画 URL 抽出
    # --------------------------------------------------
    def _extract_video_url_in_session(self, page, lesson_url: str) -> str | None:
        """
        既存の Playwright ページオブジェクトを使って
        レッスンページの iframe から動画 URL を取得する。
        （collect_lesson_links() の内部から呼ばれる）
        """
        try:
            page.goto(lesson_url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            iframes = page.locator('iframe').all()
            for frame in iframes:
                src = frame.get_attribute("src")
                if not src:
                    continue

                if "loom.com" in src:
                    url = src.replace("/embed/", "/share/").split("?")[0]
                    logger.info(f"    Loom URL: {url}")
                    return url

                if "youtube.com" in src or "youtu.be" in src:
                    m = re.search(r'embed/([^/?]+)', src)
                    if m:
                        url = f"https://www.youtube.com/watch?v={m.group(1)}"
                        logger.info(f"    YouTube URL: {url}")
                        return url

            logger.warning(f"    動画 URL なし: {lesson_url}")
            return None

        except Exception as e:
            logger.error(f"    URL 抽出失敗: {e}")
            return None

    # --------------------------------------------------
    # Step D: video_list.txt 保存
    # --------------------------------------------------
    def save_video_list(self) -> None:
        """
        self.video_list を VIDEO_LIST_FILE に
        「タイトル###URL」形式で保存する。
        """
        try:
            with open(VIDEO_LIST_FILE, "w", encoding="utf-8") as f:
                for item in self.video_list:
                    f.write(f"{item['title']}###{item['url']}\n")
            logger.info(f"video_list.txt 保存完了: {VIDEO_LIST_FILE} ({len(self.video_list)} 件)")
        except Exception as e:
            logger.error(f"save_video_list 失敗: {e}")

    # --------------------------------------------------
    # Step E: yt-dlp ダウンロード
    # --------------------------------------------------
    def download_all(self) -> None:
        """
        self.video_list の全動画を yt-dlp でダウンロードする。
        出力ファイル名: {02d}_{タイトル}.mp4
        """
        print("\n" + "!" * 50)
        print("🚀 【重要】Chrome を完全に閉じてください！")
        print("   閉じ終わったら Enter を押してダウンロードを開始します。")
        print("!" * 50)
        input()

        # Chrome プロセスを終了
        if self.chrome_proc:
            self.chrome_proc.terminate()
            logger.info("Chrome プロセスを終了しました。")

        logger.info(f"ダウンロード開始: 合計 {len(self.video_list)} 本")

        for i, item in enumerate(self.video_list, 1):
            title = item["title"]
            url   = item["url"]
            filename = os.path.join(
                VIDEOS_INPUT_DIR,
                f"{i:02d}_{title}.mp4"
            )

            logger.info(f"[{i}/{len(self.video_list)}] ダウンロード開始: {title}")

            cmd = [
                "yt-dlp",
                "--cookies-from-browser", "firefox",
                "--ffmpeg-location", FFMPEG_PATH,
                "--recode-video", "mp4",
                "--force-overwrites",
                "--concurrent-fragments", "5",
                "-o", filename,
                url
            ]

            try:
                subprocess.run(
                    cmd,
                    check=True,
                    encoding="utf-8",
                    errors="replace"
                )
                logger.info(f"  ✅ 完了: {filename}")
            except subprocess.CalledProcessError as e:
                logger.error(f"  ❌ 失敗: {title} - {e}")
                self.failed_list.append(item)

    # --------------------------------------------------
    # 失敗リスト保存
    # --------------------------------------------------
    def save_failed_list(self) -> None:
        """
        ダウンロード失敗した動画を
        logs/failed_downloads.txt に記録する。
        """
        failed_file = os.path.join(logs_dir, "failed_downloads.txt")
        try:
            with open(failed_file, "w", encoding="utf-8") as f:
                for item in self.failed_list:
                    f.write(f"{item['title']}###{item['url']}\n")
            logger.warning(
                f"失敗リストを保存しました: {failed_file} "
                f"({len(self.failed_list)} 件)"
            )
        except Exception as e:
            logger.error(f"save_failed_list 失敗: {e}")

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
        lessons_with_url = [l for l in lessons if l.get("url")]
        if not lessons_with_url:
            logger.error("レッスンリンクが見つかりませんでした。処理を中断します。")
            return
        logger.info(f"レッスン数: {len(lessons)} 件 / 動画URL取得: {len(lessons_with_url)} 件")

        # C: video_list に反映（collect_lesson_links 内で URL 取得済み）
        self.video_list = lessons_with_url

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
