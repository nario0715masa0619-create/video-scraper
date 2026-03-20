import json
import os
import sys
import io
import logging
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

class GrandMasterIntegrator:
    """
    【21拠点「知能（JSON）」大統合・推論執行エンジン】
    """
    def __init__(self, archive_dir):
        self.archive_dir = archive_dir
        
        logger.info(f"Initializing Grand Master Model ({MODEL_ID})...")
        self.gen_model = genai.GenerativeModel(
            model_name=MODEL_ID,
            generation_config={
                "response_mime_type": "application/json",
                # 長文コンテキスト処理と構造化出力のため高温は避ける
                "temperature": 0.2
            }
        )

    def execute_integration(self, output_path):
        master_list = []
        
        # 1. 物理的統合 (Logic Layer)
        logger.info("Step 1: 物理的統合を開始。全21拠点のJSONをロード...")
        for i in range(1, 22):
            video_id = f"{i:02d}"
            json_path = os.path.join(self.archive_dir, f"Mk2_Core_{video_id}.json")
            
            if not os.path.exists(json_path):
                logger.warning(f"File not found: {json_path}. Skipping.")
                continue
                
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    core_data = json.load(f)
                    for element in core_data:
                        # source_video_id をメタデータとして付与
                        element["source_video_id"] = video_id
                        master_list.append(element)
            except Exception as e:
                logger.error(f"Failed to read {json_path}: {e}")

        logger.info(f"マージ完了: 合計 {len(master_list)} 個の知能エレメントを収集。")

        # 2. 知的推論による再構築 (AI Reasoning Layer)
        logger.info("Step 2: 生成AIによる推論・構造化 (OFLOOP+) を開始...")
        
        prompt = f"""
あなたは最高峰のナレッジアーキテクト（Grand Master Delegator）です。
以下に提供されるJSON配列は、21本の連続したビジネス解説動画から抽出された知恵の断片（一事実・一論理・一手順・一事例からなるOFLOOP要素）の完全なリストです。

これらを単にマージするのではなく、全テキストを俯瞰・推論し、より高次元の構造化・抽象化を行った新たなJSONリストを生成してください。

【必須実行タスク (AI Reasoning Layer)】

1. 戦略的リレーションの抽出: 
   全要素に対し、動画02で語られている「DRM（ダイレクトレスポンスマーケティング）理論」やその他の大局的な戦略に対して、各要素の具体的アクションが「どの戦略的目的に寄与しているか」を推論し、`strategic_relation` キーとして文字列で付与せよ。関連が薄い場合は null とすること。

2. 一貫性バリデーション: 
   全要素を通しで見渡し、動画間で数値（予算、作業時間、目標月収など）や推奨手法に大きな齟齬や矛盾がある場合を検知せよ。最新情報やより具体的で現実的な手法を優先とし、古い、または抽象的な方の要素に対して `warning_flag` キー（警告文言）と `resolution_note` キー（「〜を優先すべき」というAIの判断）を記述せよ。問題がない場合は共に null とすること。
   
3. 暗黙の前提の言語化 (独立 STRATEGY の生成):
   21本の動画全体を貫く「成功者の思考（マインドセット）」や「共通の勝利法則」を暗黙の前提として読み取り、それらを独立した新規項目として3〜5個生成せよ。
   これらは `type: "STRATEGY"` とし、`element_id` は "GRAND_STRATEGY_0001" のような固有のものを付与し、JSON配列の**最上位（先頭）**に配置すること。

4. スコアの再評価:
   全要素に対して、局所的なスコアだけでなく21本全体のコンテキストを考慮した統合重要度スコア `integrated_importance_score` (0.0〜100.0) を新たに付与すること。

【出力要件】
提供された全ての既存要素（`source_video_id`等の元のデータを含む）に上記1, 2, 4のメタデータを追記したものと、3で新設した `STRATEGY` 要素を組み合わせた、単一のJSON配列（List[Dict]）を返却せよ。余計なマークダウンやテキストを含めず、JSONとしてのパースが通る完全な形式とすること。

【対象データ (物理的統合後の全要素)】
{json.dumps(master_list, ensure_ascii=False, indent=2)}
        """
        
        logger.info("Gemini 3 Proへプロンプトを送信中。データ量が大きいため、時間がかかる場合があります...")
        try:
            response = self.gen_model.generate_content(prompt)
            print("Grand Master API Response Received Successfully")
            
            # 3. 最終出力
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            logger.info(f"大統合推論が完了し、以下に出力しました: {output_path}")
            
        except Exception as e:
            logger.error(f"Integration Inference Failed: {e}")

if __name__ == "__main__":
    archive_dir = r"D:\Knowledge_Base\Brain_Marketing\archive"
    output_path = r"D:\Knowledge_Base\Brain_Marketing\archive\Mk2_Grand_Master_Logic.json"
    
    integrator = GrandMasterIntegrator(archive_dir)
    integrator.execute_integration(output_path)
