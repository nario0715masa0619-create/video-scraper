# Antigravity System Architecture (Ver.1.0)

本システムは、動画コンテンツから商用価値の高い「知恵」を抽出するための自律型パイプラインである。

## 1. 処理フロー（境界線の定義）

### Step 1: 物理抽出 (Physical Extraction)
- **Audio**: Whisperによる全音声の高精度文字起こし。
- **Vision**: FFmpegによるシーン変化（select='gt(scene,0.1)'）に基づく重要フレームの自動抽出。

### Step 2: 視覚純化 (OCR & Mud Filter)
- **EasyOCR**: 抽出フレーム内のテキスト情報を吸い上げ。
- **Mud Filter**: ブラウザUI等の不要なテキスト（泥）を正規表現により物理排除。

### Step 3: 論理抽出 (Logic Slicing)
- **OFLOOP**: 音声と視覚情報を統合し、「Fact」「Logic」「SOP」「Case」に分解。
- **Purity Scoring**: 執行の有用性に基づき 0.0〜100.0 で純度をスコアリング。

### Step 4: 物理台帳構築 (Evidence DB Build)
- **Core JSON**: 統合された論理エレメントをBOMなしUTF-8で出力。
- **Sidecar DB**: SQLite3形式で各エレメントのエビデンス位置を記録し、「source_video_path」を永続化。

## 2. 非機能要件・制約
- **Step 4 (FFmpeg出力/動画編集)**: 本パッケージのスコープ外とする。
- **出力形式**: 常に `Mk2_Core_{ID}.json` および `Mk2_Sidecar_{ID}.db` を生成する。
