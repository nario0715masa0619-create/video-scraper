【Antigravity】動画生成パイプライン論理抽出システム Ver.1.0

■ システム概要
本システムは、マーケティング講義動画から「一事実・一論理・一手順（OFLOOP）」を原子分解し、
高純度な知恵の結晶（Core JSON）とエビデンス台帳（Sidecar DB）を自律生成するパイプラインです。

■ 各ファイルの役割
1. run_antigravity.bat
   - システムのゲートウェイ。動画ファイルをドラッグ＆ドロップまたは引数指定して起動します。
2. master_batch_refiner.py
   - システムの心臓部。Whisper(音声), EasyOCR(視覚), Gemini 2.0 Proロジックによる統合精錬を執行します。
3. config_params.json
   - 解析閾値やフィルタ語彙などの制御パラメータ群。
4. instructions.md
   - 抽出時の論理的純度を担保するための思考プロトコル。
5. system_architecture.md
   - システムの設計思想と機能境界の定義。

■ 起動手順
1. Python環境およびFFmpegがインストールされていることを確認してください。
2. `pip install -r requirements.txt` を実行して必要なパッケージをインストールします。
3. `run_antigravity.bat "動画ファイルの絶対パス"` を実行します。
4. `D:\Knowledge_Base\Brain_Marketing\archive\` に成果物（.json / .db）が生成されます。
