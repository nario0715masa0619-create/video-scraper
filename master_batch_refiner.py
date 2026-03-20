import json
import os
import subprocess
import sqlite3
import re
import whisper
import easyocr
import logging
import sys
import io
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import time

# .env ファイルをロード
load_dotenv()

# UTF-8 without BOM 出力を徹底
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ロギングディレクトリを作成
logs_dir = os.getenv("LOGS_DIR", "./logs")
os.makedirs(logs_dir, exist_ok=True)

# ログファイルパス
log_file = os.path.join(logs_dir, f"antigravity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# ハンドラーを設定（コンソール出力 + ファイル出力）
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

# --- Gemini API 設定（環境変数から読み込み） ---
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-3-pro-preview")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY は .env ファイルで設定されている必要があります。")

genai.configure(api_key=API_KEY)
logger.info(f"Gemini API initialized with model: {MODEL_ID}")

class MasterBatchRefiner:
    """
    【原子分解・一括執行マスターエンジン Ver.4.0】
    """
    MUD_KEYWORDS = [
        'chrome', 'ファイル', '編集', '表示', '履歴', 'ブックマーク', 'タブ', 'ヘルプ', '設定', '共有',
        'http', 'https', 'www', 'index', 'html', 'php', 'users', 'nario', 'AppData',
        'クリック', 'ドラッグ', '選択', '閉じる', '最小化', '最大化', '元に戻す', 'プロファイル'
    ]

    def __init__(self, archive_dir):
        self.archive_dir = archive_dir
        self.temp_dir = "batch_refine_work"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        
        logger.info("Initializing Engines (CPU Mode) for Maximum Stability...")
        
        # 環境変数からパラメータを読み込み
        whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", "small")
        whisper_device = os.getenv("WHISPER_DEVICE", "cpu")
        easyocr_gpu = os.getenv("EASYOCR_GPU", "false").lower() == "true"
        easyocr_languages = os.getenv("EASYOCR_LANGUAGES", "ja,en").split(",")
        
        self.whisper_model = whisper.load_model(whisper_model_size, device=whisper_device)
        self.reader = easyocr.Reader(easyocr_languages, gpu=easyocr_gpu)
        
        # Gemini Model 初期化
        self.gen_model = genai.GenerativeModel(
            model_name=MODEL_ID,
            generation_config={"response_mime_type": "application/json"}
        )
        
        logger.info(f"Whisper model loaded: {whisper_model_size} on {whisper_device}")
        logger.info(f"EasyOCR initialized with languages: {easyocr_languages}")

    def filter_mud(self, text):
        words = re.findall(r'[^\s\w]|[\w]+', text)
        clean = [w for w in words if w.lower() not in self.MUD_KEYWORDS and len(w) >= 2]
        return " ".join(clean)

    def _call_gemini_with_retry(self, prompt, max_retries=3, initial_wait=1):
        """
        Gemini API を指数バックオフで再試行する
        
        Args:
            prompt (str): API に送信するプロンプト
            max_retries (int): 最大再試行回数
            initial_wait (int): 初期待機時間（秒）
        
        Returns:
            response: Gemini からの応答
        """
        import time
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini API call (attempt {attempt + 1}/{max_retries})...")
                start_time = time.time()
                
                response = self.gen_model.generate_content(prompt)
                
                elapsed_time = time.time() - start_time
                logger.info(f"Gemini API response received in {elapsed_time:.2f}s")
                
                return response
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                error_type = type(e).__name__
                logger.warning(f"Attempt {attempt + 1} failed ({error_type}): {str(e)[:200]}")
                
                if attempt < max_retries - 1:
                    wait_time = initial_wait * (2 ** attempt)  # 指数バックオフ
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed. Returning empty result.")
                    raise

    def process_video(self, video_path, core_out_path):
        filename = os.path.basename(video_path)
        lecture_id = filename.split('_')[0] # ファイル名から XX 部分を抽出
        
        ocr_intermediate_out = os.path.join(self.archive_dir, f"Mk2_OCR_{lecture_id}.txt")
        sidecar_out = os.path.join(self.archive_dir, f"Mk2_Sidecar_{lecture_id}.db")
        
        logger.info(f"Processing Lecture {lecture_id}: {filename}")
        
        # Step 1: 音声文字起こし
        logger.info(f"Step 1: Transcribing audio from {filename}...")
        try:
            start_time = time.time()
            result = self.whisper_model.transcribe(video_path, language="ja")
            segments = result['segments']
            
            elapsed_time = time.time() - start_time
            logger.info(f"Step 1 completed: {len(segments)} segments in {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Step 1 Failed: Whisper transcription error - {e}")
            raise
        
        # Step 2: シーン抽出（FFmpeg）
        logger.info(f"Step 2: Extracting frames using FFmpeg...")
        try:
            frames_dir = os.path.join(self.temp_dir, f"frames_{lecture_id}")
            os.makedirs(frames_dir, exist_ok=True)
            
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", "select='gt(scene,0.1)',metadata=print",
                "-vsync", "vfr", os.path.join(frames_dir, "frame_%04d.jpg"), "-f", "null", "-"
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=600)
            
            if result.returncode != 0:
                logger.warning(f"FFmpeg stderr: {result.stderr[:500]}")
            
            frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
            logger.info(f"Step 2 completed: {len(frame_files)} frames extracted")
            
        except subprocess.TimeoutExpired:
            logger.error(f"Step 2 Failed: FFmpeg timeout (>600s)")
            raise
        except Exception as e:
            logger.error(f"Step 2 Failed: Frame extraction error - {e}")
            raise
        
        # 3. 原子分解 (Atomic Slicing) & Step 2 中間出力
        all_purified_ocr_text = []
        conn = sqlite3.connect(sidecar_out)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS evidence_index")
        cursor.execute('''CREATE TABLE evidence_index 
                         (element_id TEXT, start_ms INTEGER, end_ms INTEGER, visual_text TEXT, visual_score REAL, source_video_path TEXT)''')
        
        segments_data = [] # LLM送信用

        for i, seg in enumerate(segments):
            text = seg['text'].strip()
            if len(text) < 10: continue

            frame_idx = int(seg['start'] / 10)
            visual_text = ""
            if frame_idx < len(frame_files):
                frame_path = os.path.join(frames_dir, frame_files[frame_idx])
                ocr_res = self.reader.readtext(frame_path)
                visual_text = self.filter_mud(" ".join([res[1] for res in ocr_res]))
                if visual_text:
                    all_purified_ocr_text.append(visual_text)

            segments_data.append({
                "index": i,
                "text": text,
                "visual_text": visual_text,
                "start": seg['start'],
                "end": seg['end']
            })

        # Step 2 中間出力: Mk2_OCR_XX.txt
        with open(ocr_intermediate_out, "w", encoding="utf-8") as f:
            f.write("\n".join(all_purified_ocr_text))
        logger.info(f"Step 2: Purified OCR text saved to {ocr_intermediate_out}")

        # Step 3: Gemini API Implementation (OFLOOP) - Absolute Sync with Reference
        prompt = f"""
        あなたは最高峰のナレッジデリゲーターです。
        以下の「音声書き起こし」と「視覚テキスト」の断片リストを分析し、
        「一事実・一論理・一手順（OFLOOP）」に基づいた原子分解を執行してください。

        【解析・変換ルール】
        1. 抽出タグは "FACT", "LOGIC", "SOP", "CASE" の4種に完全に固定すること。
        2. 各セグメントの「内容」を、ビジネスナレッジとして完結した文体（〜すること、〜である）に変換すること。
        3. 評価キー名は "base_purity_score" とし、0.0〜100.0で評価すること。
           - 具体的ハックや利益直結情報は100.0、雑談や挨拶は10.0以下とする。
        4. 出力は以下の構造のJSON配列（List[Dict]）のみを返せ。

        【JSON構造例】
        [
          {{
            "element_id": "CRYSTAL_{lecture_id}_0001",
            "type": "FACT",
            "content": "具体的事実の内容...",
            "base_purity_score": 95.0
          }},
          ...
        ]

        【対象データ】
        {json.dumps(segments_data, ensure_ascii=False, indent=2)}
        """

        logger.info("Step 3: Requesting Gemini API (OFLOOP)...")
        try:
            response = self._call_gemini_with_retry(prompt, max_retries=3, initial_wait=2)
            
            with open(core_out_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Sidecar DB へのエビデンス登録（解析結果の反映）
            try:
                core_data = json.loads(response.text)
                for segment, crystal in zip(segments_data, core_data):
                    element_id = crystal.get("element_id", f"CRYSTAL_{lecture_id}_{segment['index']:04d}")
                    purity = crystal.get("base_purity_score", 60.0)
                    cursor.execute("INSERT INTO evidence_index VALUES (?, ?, ?, ?, ?, ?)",
                                   (element_id, int(segment['start']*1000), int(segment['end']*1000), segment['visual_text'], purity/100.0, video_path))
            except json.JSONDecodeError:
                logger.error("Failed to parse API response for Sidecar DB index.")
            
        except Exception as e:
            logger.error(f"Step 3 Failed (final): {e}")
            with open(core_out_path, "w", encoding="utf-8") as f:
                f.write("[]")
        
        conn.commit()
        conn.close()
        logger.info(f"SUCCESS: {filename} complete.")
        
        # 【新規追加】Step 5: 出力ファイル検証
        logger.info("Step 5: Validating output files...")
        
        try:
            # Core JSON の内容を検証
            with open(core_out_path, "r", encoding="utf-8") as f:
                core_content = f.read().strip()
            
            # JSON をパース
            try:
                core_data = json.loads(core_content)
            except json.JSONDecodeError as e:
                logger.error(f"Step 5 Failed: Invalid JSON in {core_out_path} - {e}")
                return False
            
            # 空の配列 [] または空の dict {} をチェック
            is_empty = (
                (isinstance(core_data, list) and len(core_data) == 0) or
                (isinstance(core_data, dict) and len(core_data) == 0)
            )
            
            if is_empty:
                logger.error(f"Step 5 Failed: Core JSON is empty (likely Step 3 Gemini API error)")
                logger.error(f"File: {core_out_path}")
                logger.error(f"This indicates Step 3 (Gemini API) failed. Please check API key and retry.")
                return False
            
            # JSON の構造を検証（element_id や type が含まれているか確認）
            if isinstance(core_data, list) and len(core_data) > 0:
                first_element = core_data[0]
                required_fields = ["element_id", "type", "content", "base_purity_score"]
                missing_fields = [f for f in required_fields if f not in first_element]
                
                if missing_fields:
                    logger.warning(f"Step 5 Warning: Core JSON missing fields {missing_fields}")
            
            logger.info(f"Step 5: Output validation successful")
            logger.info(f"  - Core JSON: {len(core_data)} elements")
            return True
            
        except Exception as e:
            logger.error(f"Step 5 Failed: Unexpected error during output validation - {e}")
            return False

if __name__ == "__main__":
    from tqdm import tqdm
    
    logger.info("="*80)
    logger.info("Antigravity Batch Processing Started")
    logger.info("="*80)
    
    v_dir = os.getenv("VIDEOS_INPUT_DIR", r"D:\Knowledge_Base\Brain_Marketing\videos\downloaded_videos")
    a_dir = os.getenv("ARCHIVE_OUTPUT_DIR", r"D:\Knowledge_Base\Brain_Marketing\archive")
    
    refiner = MasterBatchRefiner(a_dir)
    
    import sys
    
    if len(sys.argv) > 1:
        # 引数として渡されたファイルの basename だけを抽出
        input_target = os.path.basename(sys.argv[1])
        targets = [input_target]
    else:
        targets = sorted([f for f in os.listdir(v_dir) if not f.startswith("01_") and f.endswith(".mp4")])
    logger.info(f"Found {len(targets)} videos to process")
    
    success_count = 0
    failed_count = 0
    failed_files = []  # ← ← ← 追加
    processing_results = []
    
    start_time = time.time()
    
    # tqdm でプログレスバーを表示
    for idx, filename in enumerate(tqdm(targets, desc="Processing videos"), 1):
        logger.info(f"\n[{idx}/{len(targets)}] Processing: {filename}")
        
        v_path = os.path.join(v_dir, filename)
        lecture_id = filename.split('_')[0]
        c_out = os.path.join(a_dir, f"Mk2_Core_{lecture_id}.json")
        
        step_start = time.time()
        
        try:
            # ← ← ← 戻り値を受け取る
            is_success = refiner.process_video(v_path, c_out)
            step_elapsed = time.time() - step_start
            
            # ← ← ← 戻り値をチェック
            if not is_success:
                # Step 5 の検証で失敗
                raise RuntimeError("Output file validation failed (Step 3 likely failed due to API error)")
            
            logger.info(f"✓ SUCCESS: {filename} ({step_elapsed:.1f}s)")
            success_count += 1
            
            processing_results.append({
                "filename": filename,
                "lecture_id": lecture_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "elapsed_time_sec": step_elapsed,
                "output_files": [
                    f"Mk2_Core_{lecture_id}.json",
                    f"Mk2_Sidecar_{lecture_id}.db",
                    f"Mk2_OCR_{lecture_id}.txt"
                ]
            })
            
        except Exception as e:
            step_elapsed = time.time() - step_start
            
            logger.error(f"✗ FAILED: {filename} ({step_elapsed:.1f}s) - {str(e)[:100]}")
            failed_count += 1
            failed_files.append(filename)  # ← ← ← 追加
            
            processing_results.append({
                "filename": filename,
                "lecture_id": lecture_id,
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "elapsed_time_sec": step_elapsed,
                "error": str(e)[:200]
            })
    
    elapsed_time = time.time() - start_time
    
    # 処理結果を JSON で保存
    logs_dir = os.getenv("LOGS_DIR", "./logs")
    results_file = os.path.join(logs_dir, f"processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    summary = {
        "execution_timestamp": datetime.now().isoformat(),
        "total_videos": len(targets),
        "successful": success_count,
        "failed": failed_count,
        "total_elapsed_time_sec": elapsed_time,
        "average_time_per_video_sec": elapsed_time / len(targets) if targets else 0,
        "details": processing_results
    }
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info("\n" + "="*80)
    logger.info("Antigravity Batch Processing Completed")
    logger.info("="*80)
    logger.info(f"Total: {len(targets)} | Success: {success_count} | Failed: {failed_count}")
    logger.info(f"Total elapsed time: {elapsed_time/60:.1f} minutes ({elapsed_time:.0f}s)")
    
    if len(targets) > 0:
        logger.info(f"Average per video: {elapsed_time/len(targets):.1f}s")
    
    logger.info(f"Results saved to: {results_file}")
    
    # ← ← ← 以下を追加
    if failed_count > 0:
        logger.warning(f"\n⚠️  {failed_count} video(s) failed:")
        for failed_file in failed_files:
            logger.warning(f"  - {failed_file}")
        
        retry_file = os.path.join(logs_dir, f"retry_targets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(retry_file, "w", encoding="utf-8") as f:
            f.write("\n".join(failed_files))
        logger.warning(f"\nRetry target list saved to: {retry_file}")
    else:
        logger.info("✓ All videos processed successfully!")
    
    logger.info("="*80)
