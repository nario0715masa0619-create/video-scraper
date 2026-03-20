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

# UTF-8 without BOM 出力を徹底
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Gemini API 設定 ---
API_KEY = "AIzaSyCaJoTN7Q0kYA_lFAj3dakVHdSTu3XHLEo"
MODEL_ID = "gemini-3-pro-preview"
genai.configure(api_key=API_KEY)

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
        self.whisper_model = whisper.load_model("small", device="cpu")
        self.reader = easyocr.Reader(['ja', 'en'], gpu=False)
        
        # Gemini Model 初期化
        self.gen_model = genai.GenerativeModel(
            model_name=MODEL_ID,
            generation_config={"response_mime_type": "application/json"}
        )

    def filter_mud(self, text):
        words = re.findall(r'[^\s\w]|[\w]+', text)
        clean = [w for w in words if w.lower() not in self.MUD_KEYWORDS and len(w) >= 2]
        return " ".join(clean)

    def process_video(self, video_path, core_out_path):
        filename = os.path.basename(video_path)
        lecture_id = filename.split('_')[0] # ファイル名から XX 部分を抽出
        
        ocr_intermediate_out = os.path.join(self.archive_dir, f"Mk2_OCR_{lecture_id}.txt")
        sidecar_out = os.path.join(self.archive_dir, f"Mk2_Sidecar_{lecture_id}.db")
        
        logger.info(f"Processing Lecture {lecture_id}: {filename}")
        
        # 1. 音声文字起こし
        result = self.whisper_model.transcribe(video_path, language="ja")
        segments = result['segments']
        
        # 2. シーン抽出（FFmpeg）
        frames_dir = os.path.join(self.temp_dir, f"frames_{lecture_id}")
        os.makedirs(frames_dir, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "select='gt(scene,0.1)',metadata=print",
            "-vsync", "vfr", os.path.join(frames_dir, "frame_%04d.jpg"), "-f", "null", "-"
        ], capture_output=True)
        
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
        
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
            # 参照元 (step5_text_to_knowledge.py) の構文を完全トレース
            response = self.gen_model.generate_content(prompt)
            print("API Response Received Successfully") # 必須ログ出力
            
            # response.text を直接ファイルに出力し、プログラム側での「フェイク生成」を物理的に排除
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
            logger.error(f"Step 3 Failed: {e}")
            # エラー時は空のリストを生成して安全に終了させる
            with open(core_out_path, "w", encoding="utf-8") as f:
                f.write("[]")
        
        conn.commit()
        conn.close()
        logger.info(f"SUCCESS: {filename} complete.")

if __name__ == "__main__":
    v_dir = r"D:\Knowledge_Base\Brain_Marketing\videos\downloaded_videos"
    a_dir = r"D:\Knowledge_Base\Brain_Marketing\archive"
    
    refiner = MasterBatchRefiner(a_dir)
    
    # 01_ は処理済みのため除外
    targets = sorted([f for f in os.listdir(v_dir) if not f.startswith("01_") and f.endswith(".mp4")])
    
    for filename in targets:
        v_path = os.path.join(v_dir, filename)
        lecture_id = filename.split('_')[0]
        c_out = os.path.join(a_dir, f"Mk2_Core_{lecture_id}.json")
        
        try:
            refiner.process_video(v_path, c_out)
            print(f"Processing Complete: {filename}")
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            # エラーが発生しても停止せず、次のファイルの処理を継続
            continue
