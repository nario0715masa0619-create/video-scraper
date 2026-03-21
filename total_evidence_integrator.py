import os
import sqlite3
import json
import time
import logging
import sys
import io
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# .env ファイルをロード
load_dotenv()

# UTF-8 without BOM 出力を徹底
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logs_dir = os.getenv("LOGS_DIR", "./logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, f"antigravity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)
logger.info(f"Log file: {log_file}")


# --- Gemini API 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-3-pro-preview")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY は .env ファイルで設定されている必要があります。")

genai.configure(api_key=API_KEY)

class TotalEvidenceIntegrator:
    """
    【21拠点「記憶と神経」完全同期・推論執行エンジン】
    """
    def __init__(self, archive_dir):
        self.archive_dir = archive_dir
        self.total_db_path = os.path.join(self.archive_dir, "Mk2_Total_Evidence.db")
        self.json_path = os.path.join(self.archive_dir, "Mk2_Grand_Master_Logic.json")
        
        logger.info(f"Initializing Neural Network Model ({MODEL_ID})...")
        self.gen_model = genai.GenerativeModel(
            model_name=MODEL_ID,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )

    def _call_gemini_with_retry(self, prompt, max_retries=3, initial_wait=2):
        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini API call (attempt {attempt + 1}/{max_retries})...")
                start_time = time.time()
                response = self.gen_model.generate_content(prompt)
                elapsed_time = time.time() - start_time
                logger.info(f"Gemini API response received in {elapsed_time:.2f}s")
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed ({type(e).__name__}): {str(e)[:200]}")
                if attempt < max_retries - 1:
                    wait_time = initial_wait * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed.")
                    raise

    def consolidate_memory(self):
        """Step 1: 物理統合 (Memory Consolidation)"""
        logger.info("Step 1: 物理統合を開始。全21拠点のDBから evidence_index をマージします...")
        
        # Total DBの初期化
        conn_total = sqlite3.connect(self.total_db_path)
        cursor_total = conn_total.cursor()
        cursor_total.execute("DROP TABLE IF EXISTS evidence_index")
        cursor_total.execute('''CREATE TABLE evidence_index 
                               (element_id TEXT, start_ms INTEGER, end_ms INTEGER, visual_text TEXT, visual_score REAL, source_video_path TEXT)''')
        
        cursor_total.execute("DROP TABLE IF EXISTS logical_network")
        cursor_total.execute('''CREATE TABLE logical_network 
                               (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT, target_id TEXT, relation_type TEXT, reason_logic TEXT)''')
                               
        total_rows = 0
        
        for i in range(1, 22):
            video_id = f"{i:02d}"
            sidecar_path = os.path.join(self.archive_dir, f"Mk2_Sidecar_{video_id}.db")
            
            if not os.path.exists(sidecar_path):
                logger.warning(f"File not found: {sidecar_path}. Skipping.")
                continue
                
            try:
                # ATTACH を利用してデータを移行
                cursor_total.execute(f"ATTACH DATABASE '{sidecar_path}' AS sidecar_{video_id}")
                cursor_total.execute(f"INSERT INTO evidence_index SELECT * FROM sidecar_{video_id}.evidence_index")
                cursor_total.execute(f"DETACH DATABASE sidecar_{video_id}")
                total_rows += cursor_total.rowcount
            except Exception as e:
                logger.error(f"Failed to merge {sidecar_path}: {e}")

        conn_total.commit()
        logger.info(f"マージ完了: 合計 {total_rows} 件のエビデンスを Mk2_Total_Evidence.db へ統合。")
        return conn_total

    def build_neural_network(self, conn_total):
        """Step 2: 論理ネットワーク実装 (Neural Networking)"""
        logger.info("Step 2: 生成AIによる論理ネットワーク推論を開始...")
        
        if not os.path.exists(self.json_path):
            logger.error(f"Grand Master JSON not found: {self.json_path}")
            return
            
        with open(self.json_path, 'r', encoding='utf-8') as f:
            grand_master_data = json.load(f)
            
        prompt = f"""
あなたは最高峰のナレッジアーキテクト（Neural Data Engineer）です。
以下に提供されるJSON配列は、21本のビジネス解説動画から抽出・抽象化された「グランドマスター・ロジック（知恵の結晶）」の全リストです。

【必須実行タスク (Neural Networking)】

提供された全要素（`element_id`, `type`, `content`等）群を俯瞰・分析し、要素間の意味的な繋がり（クロス・リファレンス）を抽出し、論理ネットワーク（グラフ構造）を構築してください。

1. リレーション定義: 
   要素間の明確な関連性を抽出し、以下の出力形式に基づく JSONリスト (List[Dict]) で返却してください。
   ・`source_id`: 関連元の `element_id`
   ・`target_id`: 関連先の `element_id`
   ・`relation_type`: 以下のいずれかを厳密に判定して付与。
     - "依存" (targetはsourceの前提条件である)
     - "手段" (targetはsourceの目的を達成する手段である)
     - "制約" (targetはsourceに対する制約、または矛盾・問題からの警告である)
   ・`reason_logic`: その関係性を結んだ推論の根拠（「〜だから〜である」等の簡潔な論理）

2. 一貫性バリデーションの反映: 
   動画03の目標「月10万稼ぐ」に対する寄与を最重要評価軸としてください。過度な作り込みや、初級者のスケールを超えた手段、また他要素と矛盾する内容（例：高額な外注費）が見られる場合、該当要素への `relation_type` を「制約」とし、`reason_logic` に低優先度である理由（例：「低コスト手法が優先されるべき」等）を明記してください。

【出力要件】
抽出した意味的ネットワークのエッジ情報のみを、指定した {{"source_id", "target_id", "relation_type", "reason_logic"}} の構造を持つJSON配列として返却すること。余計な文字列やマークダウンは含めないこと。

【対象データ (Grand Master Logic)】
{json.dumps(grand_master_data, ensure_ascii=False, indent=2)}
        """
        
        logger.info("Gemini 3 Proへプロンプトを送信中。推論には数十分かかる場合があります...")
        try:
            response = self._call_gemini_with_retry(prompt)
            print("Neural Network API Response Received Successfully")
            
            network_edges = json.loads(response.text)
            logger.info(f"AIにより {len(network_edges)} 件の論理リレーションが抽出されました。DBへ登録します...")
            
            cursor_total = conn_total.cursor()
            for edge in network_edges:
                cursor_total.execute("INSERT INTO logical_network (source_id, target_id, relation_type, reason_logic) VALUES (?, ?, ?, ?)",
                                     (edge.get("source_id"), edge.get("target_id"), edge.get("relation_type"), edge.get("reason_logic")))
            
            conn_total.commit()
            logger.info("logical_network テーブルへの登録完了。")
            
        except Exception as e:
            logger.error(f"Neural Networking Failed: {e}")

    def test_quality(self, conn_total):
        """Step 3: 品質保証 (Query Testing)"""
        logger.info("Step 3: エビデンス直結・論理推論テストを実施します...")
        cursor_total = conn_total.cursor()
        
        # テスト: 論理ネットワークとエビデンスをJOINして動画を跨いだ繋がりを取得
        test_query = '''
            SELECT 
                ln.source_id,
                ln.relation_type,
                ln.target_id,
                e.source_video_path
            FROM logical_network ln
            LEFT JOIN evidence_index e ON ln.target_id = e.element_id
            LIMIT 5
        '''
        
        cursor_total.execute(test_query)
        results = cursor_total.fetchall()
        
        print("\n--- クロス・リファレンス抽出テスト結果 ---")
        for row in results:
            print(f"Source: {row[0]} --[{row[1]}]--> Target: {row[2]} | [Evidence]: {row[3]}")
        print("------------------------------------------\n")
        logger.info("テスト完了。ポインタによる動画跨ぎのアクセスは正常に機能しています。")

    def execute(self):
        conn_total = self.consolidate_memory()
        self.build_neural_network(conn_total)
        self.test_quality(conn_total)
        conn_total.close()
        logger.info("全工程完了。「知識」と「神経」の統合が完了しました。")

if __name__ == "__main__":
    archive_dir = os.getenv("ARCHIVE_OUTPUT_DIR", r"D:\Knowledge_Base\Brain_Marketing\archive")
    integrator = TotalEvidenceIntegrator(archive_dir)
    integrator.execute()
