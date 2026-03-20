\# Antigravity Ver.1.0 - システム構成完全ガイド



\## 1. システム全体構成図



┌─────────────────────────────────────────────────────────────────────────────┐ │ Antigravity システム Ver.1.0 │ │ 動画から商用知識を抽出する自律型パイプライン │ └─────────────────────────────────────────────────────────────────────────────┘



入力層 ↓ 

┌──────────────────────────────────────────────────────────────────────────┐ │ 動画ファイル │ │ D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos\*.mp4 │ │ （ただし 01\_ プレフィックスのファイルは処理済みで除外） │ └──────────────────────────────────────────────────────────────────────────┘ ↓ 処理層 ↓ ┌──────────────────────────────────────────────────────────────────────────┐ │ Step 1: 物理抽出層 (Physical Extraction) │ ├─────────────────────────────────────────────────────────────────────────┤ │ ・Whisper API → 音声全文字起こし（日本語） │ │ ・FFmpeg → シーン変化検出（threshold=0.1）→ 重要フレーム自動抽出 │ └──────────────────────────────────────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────────────────────────────────────┐ │ Step 2: 視覚純化層 (OCR \& Mud Filter) │ ├─────────────────────────────────────────────────────────────────────────┤ │ ・EasyOCR → 抽出フレーム内のテキスト認識（日本語・英語） │ │ ・Mud Filter → ブラウザUIやパス情報など不要テキストを正規表現で排除 │ │ ・結果を Mk2\_OCR\_{lecture\_id}.txt として保存 │ └──────────────────────────────────────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────────────────────────────────────┐ │ Step 3: 論理抽出層 (Logic Slicing / OFLOOP) │ ├─────────────────────────────────────────────────────────────────────────┤ │ ・Gemini 2.0 Pro API → 音声＋視覚情報の統合分析 │ │ ・原子分解（FACT/LOGIC/SOP/CASE）による知識構造化 │ │ ・各要素に pure\_score（0.0～100.0）を付与 │ └──────────────────────────────────────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────────────────────────────────────┐ │ Step 4: 物理台帳構築層 (Evidence DB Build) │ ├─────────────────────────────────────────────────────────────────────────┤ │ ・知識エレメント → Mk2\_Core\_{lecture\_id}.json（UTF-8 BOM無し） │ │ ・エビデンス索引 → Mk2\_Sidecar\_{lecture\_id}.db（SQLite3） │ └──────────────────────────────────────────────────────────────────────────┘ ↓ 出力層 ↓ ┌──────────────────────────────────────────────────────────────────────────┐ │ 出力ファイル群 │ │ D:\\Knowledge\_Base\\Brain\_Marketing\\archive\\ │ │ ├─ Mk2\_Core\_{lecture\_id}.json \[知識結晶化データ] │ │ ├─ Mk2\_Sidecar\_{lecture\_id}.db \[エビデンス索引] │ │ └─ Mk2\_OCR\_{lecture\_id}.txt \[中間出力：純化視覚テキスト] │ └──────────────────────────────────────────────────────────────────────────┘



\## 2. ファイル構成と役割



\### 2.1 実行エントリーポイント



\#### \*\*run\_antigravity.bat\*\*

\- \*\*役割\*\*：Windows環境でのシステム起動バッチスクリプト

\- \*\*入力\*\*：動画ファイルの絶対パス（コマンドライン引数）

\- \*\*処理\*\*：

&#x20; - 引数の検証（パスが指定されているか確認）

&#x20; - master\_batch\_refiner.py をPythonで実行

&#x20; - エラー時にユーザーへ通知

\- \*\*出力\*\*：システム処理の実行開始

\- \*\*使用例\*\*：`run\_antigravity.bat "D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos\\03\_sample\_video.mp4"`



\---



\### 2.2 コアエンジン



\#### \*\*master\_batch\_refiner.py\*\*

\- \*\*役割\*\*：Antigravity システムの中枢エンジン。4段階処理全体を統制

\- \*\*主要クラス\*\*：MasterBatchRefiner

\- \*\*初期化処理\*\*：

&#x20; - Whisper モデル（small、CPU モード）をロード

&#x20; - EasyOCR リーダー（日本語・英語対応、GPU無効）をロード

&#x20; - Gemini API を初期化（gemini-3-pro-preview）

&#x20; - 作業ディレクトリ（batch\_refine\_work）の作成

&#x20; 

\- \*\*主要メソッド\*\*：

&#x20; - `\_\_init\_\_(archive\_dir)` ：各エンジンを初期化

&#x20; - `filter\_mud(text)` ：MUD\_KEYWORDS リストに基づく不要テキスト排除

&#x20; - `process\_video(video\_path, core\_out\_path)` ：4段階処理をまとめて実行

&#x20; 

\- \*\*process\_video メソッドの詳細処理\*\*：

&#x20; 

&#x20; 1. \*\*ファイル名解析\*\*：動画ファイル名から lecture\_id を抽出

&#x20; 2. \*\*Step 1 - 音声抽出\*\*：Whisper で動画全体を文字起こし、segments を取得

&#x20; 3. \*\*Step 1 - フレーム抽出\*\*：FFmpeg で `select='gt(scene,0.1)'` により境界フレームを jpg 出力

&#x20; 4. \*\*Step 2 - OCR 実行\*\*：各フレームに対して EasyOCR を実行、テキスト抽出

&#x20; 5. \*\*Step 2 - Mud フィルタ\*\*：filter\_mud() で不要テキストを除外、Mk2\_OCR\_{lecture\_id}.txt に保存

&#x20; 6. \*\*Step 3 - Gemini API 呼び出し\*\*：

&#x20;    - segments\_data（音声+視覚情報）を JSON で Gemini に送信

&#x20;    - OFLOOP（FACT/LOGIC/SOP/CASE）分類と purity\_score 付与を要求

&#x20;    - 応答テキストを Mk2\_Core\_{lecture\_id}.json に直接保存

&#x20; 7. \*\*Step 4 - SQLite3 索引構築\*\*：

&#x20;    - Mk2\_Sidecar\_{lecture\_id}.db を作成

&#x20;    - evidence\_index テーブルを定義（element\_id, start\_ms, end\_ms, visual\_text, visual\_score, source\_video\_path）

&#x20;    - 各エレメントのメタデータを記録



\- \*\*エラーハンドリング\*\*：

&#x20; - API 呼び出し失敗時は空の JSON 配列 `\[]` を出力

&#x20; - 個別動画の処理失敗時も、ループを継続して次の動画を処理

&#x20; 

\- \*\*実行方式\*\*：

&#x20; - `targets` リストから `01\_` プレフィックスを除外したファイルのみ処理

&#x20; - 処理順序はアルファベット順



\---



\### 2.3 設定ファイル



\#### \*\*config\_params.json\*\*

\- \*\*役割\*\*：各エンジンのパラメータを一元管理

\- \*\*セクション構成\*\*：

&#x20; 

&#x20; 1. \*\*FFmpeg\_Extraction\*\*

&#x20;    - `scene\_threshold: 0.1` → スライド変化の感度（0.1以上の差分で検出）

&#x20;    - `vsync\_mode: "vfr"` → フレームレート可変出力

&#x20;    - `output\_format: "jpg"` → フレーム出力形式

&#x20;    - 説明：無駄な中間フレームを排除し、トピック境界のみを抽出



&#x20; 2. \*\*EasyOCR\_Settings\*\*

&#x20;    - `languages: \["ja", "en"]` → 認識言語

&#x20;    - `gpu\_usage: false` → CPU モード（安定性重視）

&#x20;    - `confidence\_threshold: 0.5` → 確信度閾値

&#x20;    - 説明：UIノイズが多い操作画面でも確実なキーワードのみを抽出



&#x20; 3. \*\*Mud\_Filter\_Config\*\*

&#x20;    - `regex\_pattern: "\[^\\\\s\\\\w]|\[\\\\w]+"` → 分割パターン

&#x20;    - `min\_word\_length: 2` → 抽出最小語長

&#x20;    - `excluded\_vocab\_count: 22` → 除外キーワード数

&#x20;    - MUD\_KEYWORDS リスト：chrome、ファイル、編集、表示、履歴、ブックマーク、タブ、ヘルプ、設定、共有、http、https、www、index、html、php、users、nario、AppData、クリック、ドラッグ、選択、閉じる、最小化、最大化、元に戻す、プロファイル



&#x20; 4. \*\*Purity\_Score\_Algorithm\*\*

&#x20;    - `audio\_weight: 0.6` → 音声情報の重み付け

&#x20;    - `visual\_weight: 0.4` → 視覚情報の重み付け

&#x20;    - `core\_keywords: \["再出品", "注意", "禁止", "即座に", "修正", "規約"]` → 高スコア判定キーワード

&#x20;    - `mud\_penalty\_factor: "if mud > 2 then penalty 80%"` → 不要テキスト含有時のペナルティ



\---



\### 2.4 ドキュメント



\#### \*\*system\_architecture.md\*\*

\- \*\*役割\*\*：システム全体のアーキテクチャを説明する技術仕様書

\- \*\*内容\*\*：

&#x20; - 4段階処理フロー（物理抽出→視覚純化→論理抽出→台帳構築）の詳細

&#x20; - 各ステップの目的と実装技術

&#x20; - 非機能要件と制約条件

&#x20; - 出力形式の仕様



\#### \*\*instructions.md\*\*

\- \*\*役割\*\*：Gemini API で実行される「結晶化プロトコル Ver.2.2」を定義

\- \*\*内容\*\*：

&#x20; - 思考のフィルタリング（フィラーや雑談の除外）

&#x20; - 原子分解の再構成（OFLOOP の定義）

&#x20; - スタイル・レギュレーション（ビジネス文体への変換）

&#x20; - Purity Score 絶対評価基準

&#x20;   - 100.0 ：利益に直結し、視覚的エビデンスによる裏付けがある具体的ハック

&#x20;   - 90.0以上：致命的リスク回避の具体的注意点

&#x20;   - 10.0以下：本質的価値のない補助的発言、挨拶、フィラー



\---



\## 3. データフロー詳細



\### 3.1 入力データ形式



\*\*動画ファイル（.mp4）\*\*

\- 場所：`D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos\\`

\- ファイル名形式：`{lecture\_id}\_xxx\_description.mp4`

&#x20; - 例：`03\_sample\_lecture\_youtube.mp4`

\- 処理対象：`01\_` で始まらないファイルのみ

\- 形式：MP4（h.264 推奨）



\### 3.2 中間データ



\*\*Whisper 出力（segments JSON）\*\*

\- 形式：Python dict の list

\- 構造：`{"text": "...", "start": 1.23, "end": 4.56, ...}`

\- 用途：Step 1 出力、Step 3 の入力に統合



\*\*抽出フレーム（JPG）\*\*

\- 場所：`batch\_refine\_work/frames\_{lecture\_id}/`

\- ファイル名：`frame\_0001.jpg`, `frame\_0002.jpg`, ...

\- 形式：JPEG （FFmpeg 出力）

\- 内容：動画内の視覚的トピック変化点



\*\*Mud フィルタ済みテキスト（Mk2\_OCR\_XX.txt）\*\*

\- 場所：`D:\\Knowledge\_Base\\Brain\_Marketing\\archive\\`

\- 形式：UTF-8 プレーンテキスト（BOM なし）

\- 内容：抽出フレーム内のテキストから不要語を排除したもの



\### 3.3 最終出力データ



\*\*知識結晶化ファイル（Mk2\_Core\_XX.json）\*\*

\- 場所：`D:\\Knowledge\_Base\\Brain\_Marketing\\archive\\`

\- 形式：JSON 配列（UTF-8 BOM なし）

\- 構造：

&#x20; ```json

&#x20; \[

&#x20;   {

&#x20;     "element\_id": "CRYSTAL\_03\_0001",

&#x20;     "type": "FACT",

&#x20;     "content": "具体的事実の説明...",

&#x20;     "base\_purity\_score": 95.0

&#x20;   },

&#x20;   {

&#x20;     "element\_id": "CRYSTAL\_03\_0002",

&#x20;     "type": "LOGIC",

&#x20;     "content": "なぜその行動が必要か...",

&#x20;     "base\_purity\_score": 88.5

&#x20;   },

&#x20;   ...

&#x20; ]



エビデンス索引DB（Mk2\_Sidecar\_XX.db）



場所：D:\\Knowledge\_Base\\Brain\_Marketing\\archive\\

形式：SQLite3 データベース

テーブル：evidence\_index

element\_id (TEXT) ：知識エレメントの一意識別子

start\_ms (INTEGER) ：出現開始時刻（ミリ秒）

end\_ms (INTEGER) ：出現終了時刻（ミリ秒）

visual\_text (TEXT) ：対応する視覚テキスト

visual\_score (REAL) ：純度スコア（0.0～1.0）

source\_video\_path (TEXT) ：元動画ファイルの絶対パス

用途：各知識エレメントと元動画内の位置を紐付け

4\. 処理パラメータと制約

4.1 各エンジンのパラメータ

エンジン	パラメータ	値	説明

Whisper	モデルサイズ	small	軽量で高速（large よりメモリ効率）

Whisper	言語	ja	日本語に特化

Whisper	デバイス	cpu	CPU モードで安定性重視

FFmpeg	scene\_threshold	0.1	スライド変化の感度

FFmpeg	vsync	vfr	可変フレームレート出力

EasyOCR	言語	ja, en	日本語＋英語を同時認識

EasyOCR	GPU	false	CPU モード（安定性重視）

EasyOCR	confidence	0.5	確信度閾値

Gemini	モデル	gemini-3-pro-preview	最新の汎用モデル

Gemini	response\_mime	application/json	JSON 形式での応答を強制

4.2 システム制約

処理スコープ：



Step 4 での FFmpeg 動画編集はスコープ外

知識構造化まで（Mk2\_Core JSON と Mk2\_Sidecar DB）を出力範囲とする

エンコーディング：



全出力ファイルは UTF-8 BOM なし（プログラム全体で徹底）

sys.stdout も UTF-8 BOM なしに設定

ファイル処理：



01\_ プレフィックス付きファイルは処理済みとして除外

処理順序はアルファベット順（sorted() で制御）

エラー耐性：



個別動画の処理失敗時も全体処理は続行

API エラーの場合は空の JSON 配列を出力（安全終了）

5\. 実行フロー

5.1 通常実行

ユーザー

&#x20; ↓

run\_antigravity.bat を実行（動画パスを引数）

&#x20; ↓

master\_batch\_refiner.py が起動

&#x20; ↓

MasterBatchRefiner クラスをインスタンス化

&#x20; ↓

process\_video() メソッドで 4段階処理を順次実行

&#x20; ├→ Step 1: Whisper + FFmpeg

&#x20; ├→ Step 2: EasyOCR + Mud Filter

&#x20; ├→ Step 3: Gemini API (OFLOOP)

&#x20; └→ Step 4: JSON + SQLite3 出力

&#x20; ↓

archive フォルダに結果ファイル出力

&#x20; ├→ Mk2\_Core\_XX.json

&#x20; ├→ Mk2\_Sidecar\_XX.db

&#x20; └→ Mk2\_OCR\_XX.txt

&#x20; ↓

処理完了

5.2 バッチ実行（複数動画）

master\_batch\_refiner.py の \_\_main\_\_ セクション

&#x20; ↓

v\_dir から全 .mp4 ファイルを取得

&#x20; ↓

01\_ プレフィックスのファイルを除外

&#x20; ↓

アルファベット順にソート

&#x20; ↓

各ファイルに対して process\_video() を逐次実行

&#x20; ├→ ファイルA 処理

&#x20; ├→ ファイルB 処理

&#x20; └→ ファイルC 処理（失敗しても続行）

&#x20; ↓

全ファイル処理完了（またはエラーで中断）

6\. トラブルシューティング

6.1 よくある問題

問題	原因	解決策

Whisper がロードできない	モデルがダウンロードされていない	pip install openai-whisper で再インストール

EasyOCR が遅い	GPU が無効、大きなモデル	config\_params.json で確信度を 0.7 に上げる

Gemini API エラー	API キーが無効または通信エラー	API キーと通信環境を確認

ファイルが処理されない	01\_ プレフィックス付き	ファイル名を変更するか targets リストを修正

UTF-8 BOM エラー	エディタの設定ミス	テキストエディタで「UTF-8（BOM なし）」で保存

7\. 今後の改善項目

API キー管理：環境変数または .env ファイルへの移行

再試行ロジック：API 呼び出し失敗時の指数バックオフ実装

進捗管理：大量動画処理時のチェックポイントと再開機構

ログ詳細化：API 呼び出しのタイムスタンプとレスポンス時間の記録

モデル管理：Gemini モデル ID を config\_params.json で管理

テスト：単体テストと統合テストの整備



\---



\## \*\*ファイル2: FILE\_STRUCTURE.md\*\*



`D:\\AI\_スクリプト成果物\\動画スクレイピングプロジェクト` に `FILE\_STRUCTURE.md` として保存してください。



```markdown

\# Antigravity プロジェクト - ファイル構成と役割マップ



\## プロジェクト全体のディレクトリ構成



video-scraper（GitHub リポジトリ） ├── main ブランチ │ ├── .gitignore │ ├── README.md │ ├── requirements.txt │ └── \[その他の本番コード] │ └── ai-dev ブランチ ├── run\_antigravity.bat ...................... \[実行エントリーポイント] ├── master\_batch\_refiner.py ................. \[コアエンジン] ├── config\_params.json ....................... \[パラメータ設定] ├── system\_architecture.md .................. \[技術仕様書] ├── instructions.md .......................... \[プロンプト仕様] ├── DEVELOPMENT\_GUIDELINES.md ............... \[開発運用ガイド] ├── SYSTEM\_OVERVIEW.md ....................... \[本ドキュメント] ├── FILE\_STRUCTURE.md ........................ \[ファイル構成ガイド] └── batch\_refine\_work/（実行時生成） ├── frames\_03/ ├── frames\_04/ └── ...





\---



\## ファイル別役割表



\### 実行・制御層



| ファイル名 | 形式 | 役割 | 編集対象 | 実行頻度 |

|-----------|------|------|--------|--------|

| `run\_antigravity.bat` | バッチスクリプト | Windows 環境でのシステム起動 | ai-dev | 毎回実行 |

| `master\_batch\_refiner.py` | Python スクリプト | 4段階処理全体を統制するコアエンジン | ai-dev | 毎回実行 |



\### 設定・パラメータ層



| ファイル名 | 形式 | 役割 | 編集対象 | 参照元 |

|-----------|------|------|--------|-------|

| `config\_params.json` | JSON | Whisper/FFmpeg/EasyOCR/Gemini の設定を一元管理 | ai-dev | master\_batch\_refiner.py |



\### ドキュメント層



| ファイル名 | 形式 | 役割 | 編集対象 | 対象読者 |

|-----------|------|------|--------|---------|

| `system\_architecture.md` | Markdown | システム全体のアーキテクチャと 4段階処理の詳細説明 | ai-dev | 技術者全員 |

| `instructions.md` | Markdown | Gemini API に与える「結晶化プロトコル」の思考規範 | ai-dev | AI プロンプト管理者 |

| `DEVELOPMENT\_GUIDELINES.md` | Markdown | Git 運用方針、PR メッセージ形式、コミット規約 | ai-dev | 開発チーム全員 |

| `SYSTEM\_OVERVIEW.md` | Markdown | システム構成図、ファイル役割、処理フロー、トラブルシューティング | ai-dev | 運用担当者 |

| `FILE\_STRUCTURE.md` | Markdown | ファイル構成と役割マップ（本ファイル） | ai-dev | 全員 |



\### 実行時出力層（archive ディレクトリ）



| ファイル名パターン | 形式 | 役割 | 生成元 | 用途 |

|------------------|------|------|-------|------|

| `Mk2\_Core\_{lecture\_id}.json` | JSON | 知識結晶化ファイル（FACT/LOGIC/SOP/CASE エレメント） | master\_batch\_refiner.py | 知識データベース構築 |

| `Mk2\_Sidecar\_{lecture\_id}.db` | SQLite3 | エビデンス索引（エレメントの時刻・位置・スコア情報） | master\_batch\_refiner.py | メタデータベース |

| `Mk2\_OCR\_{lecture\_id}.txt` | テキスト | 中間出力：Mud フィルタ済み視覚テキスト | master\_batch\_refiner.py | デバッグ・検証用 |



\### 実行時作業層（batch\_refine\_work ディレクトリ）



| フォルダ・ファイル | 形式 | 役割 | 削除可否 |

|------------------|------|------|--------|

| `frames\_{lecture\_id}/` | ディレクトリ | 各動画から抽出された JPG フレーム | 処理後削除可 |

| `frame\_0001.jpg` 等 | JPEG | 動画内のシーン変化点を表すフレーム | 処理後削除可 |



\---



\## 各ファイルの詳細説明



\### 1. run\_antigravity.bat



\*\*目的\*\*：ユーザーが Windows コマンドプロンプトから Antigravity システムを起動するためのエントリーポイント



\*\*内容\*\*：

```batch

@echo off

setlocal

set VIDEO\_PATH=%\~1



if "%VIDEO\_PATH%"=="" (

&#x20;   echo \[ERROR] 動画の絶対パスを指定してください。

&#x20;   echo 使用法: run\_antigravity.bat "C:\\path\\to\\video.mp4"

&#x20;   pause

&#x20;   exit /b 1

)



echo \[Antigravity] 執行を開始します...

python master\_batch\_refiner.py "%VIDEO\_PATH%"



echo \[DONE] 処理が完了しました。

pause



実行方法：



Copy# 単一動画の処理

run\_antigravity.bat "D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos\\03\_sample\_video.mp4"



\# または



\# Python で直接実行（dev 用）

python master\_batch\_refiner.py "D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos\\03\_sample\_video.mp4"

依存関係：Python がシステムパスに登録されていることが必須



2\. master\_batch\_refiner.py

目的：Antigravity システムの中枢。4段階処理（物理抽出→視覚純化→論理抽出→台帳構築）を統制



主要クラス：MasterBatchRefiner



初期化時に実行される処理：



Whisper モデル（small、CPU モード）をメモリにロード

EasyOCR リーダーをロード（日本語・英語、GPU 無効）

Gemini API を設定（API キー、モデル ID、response\_mime\_type）

作業ディレクトリ batch\_refine\_work を作成

主要メソッド：



Copydef \_\_init\_\_(self, archive\_dir):

&#x20;   # 各エンジンを初期化



def filter\_mud(self, text):

&#x20;   # MUD\_KEYWORDS に基づき不要テキストを排除



def process\_video(self, video\_path, core\_out\_path):

&#x20;   # 4段階処理を順次実行

process\_video メソッドのステップバイステップ処理：



ファイル名解析：



入力：03\_sample\_video.mp4

lecture\_id 抽出：03

出力パス自動決定：Mk2\_Core\_03.json

Step 1 - Whisper による音声抽出：



whisper\_model.transcribe(video\_path, language="ja")

出力：segments （開始時刻、終了時刻、テキストを含む dict の list）

Step 1 - FFmpeg によるフレーム抽出：



Copyffmpeg -i video.mp4 \\

&#x20;       -vf "select='gt(scene,0.1)',metadata=print" \\

&#x20;       -vsync vfr frames/frame\_%04d.jpg

scene\_threshold=0.1 でシーン変化点のみを検出

Step 2 - EasyOCR による文字認識：



各フレームに対して self.reader.readtext(frame\_path) を実行

認識テキスト抽出

Step 2 - Mud フィルタによる不要テキスト排除：



filter\_mud() で MUD\_KEYWORDS と一致する語を除外

結果を Mk2\_OCR\_{lecture\_id}.txt に保存

Step 3 - Gemini API への統合分析：



segments + visual\_text を JSON で構成

Gemini へ OFLOOP（FACT/LOGIC/SOP/CASE 分解）を要求するプロンプトを送信

JSON 形式での応答を強制（response\_mime\_type="application/json"）

Step 3 - 応答の処理：



Gemini からの JSON テキストを response.text で取得

Mk2\_Core\_{lecture\_id}.json として直接保存（フェイク生成を排除）

Step 4 - SQLite3 DB 構築：



Mk2\_Sidecar\_{lecture\_id}.db を作成

evidence\_index テーブルを定義

各エレメントのメタデータ（element\_id, start\_ms, end\_ms, visual\_text, visual\_score, source\_video\_path）をレコードとして挿入

エラーハンドリング：



API 呼び出し失敗時：空の JSON 配列 \[] を出力

個別動画処理失敗時：try-except で例外をキャッチ、ログ出力後に次のファイルを処理

バッチ処理メイン処理（main セクション）：



Copyif \_\_name\_\_ == "\_\_main\_\_":

&#x20;   v\_dir = r"D:\\Knowledge\_Base\\Brain\_Marketing\\videos\\downloaded\_videos"

&#x20;   a\_dir = r"D:\\Knowledge\_Base\\Brain\_Marketing\\archive"

&#x20;   

&#x20;   refiner = MasterBatchRefiner(a\_dir)

&#x20;   

&#x20;   # 01\_ プレフィックスを除外し、アルファベット順にソート

&#x20;   targets = sorted(\[f for f in os.listdir(v\_dir) if not f.startswith("01\_") and f.endswith(".mp4")])

&#x20;   

&#x20;   # 各ファイルを順次処理

&#x20;   for filename in targets:

&#x20;       v\_path = os.path.join(v\_dir, filename)

&#x20;       lecture\_id = filename.split('\_')\[0]

&#x20;       c\_out = os.path.join(a\_dir, f"Mk2\_Core\_{lecture\_id}.json")

&#x20;       

&#x20;       try:

&#x20;           refiner.process\_video(v\_path, c\_out)

&#x20;       except Exception as e:

&#x20;           logger.error(f"Failed to process {filename}: {e}")

&#x20;           continue  # 次のファイルに進む

3\. config\_params.json

目的：Whisper、FFmpeg、EasyOCR、Gemini、Purity Score Algorithm の全パラメータを一元管理



構造：



Copy{

&#x20; "FFmpeg\_Extraction": { ... },

&#x20; "EasyOCR\_Settings": { ... },

&#x20; "Mud\_Filter\_Config": { ... },

&#x20; "Purity\_Score\_Algorithm": { ... }

}

各セクションの詳細：



FFmpeg\_Extraction

scene\_threshold: 0.1：スライド変化の感度（推奨値 0.05～0.2）

vsync\_mode: "vfr"：可変フレームレート出力

output\_format: "jpg"：フレーム出力形式

EasyOCR\_Settings

languages: \["ja", "en"]：認識言語（日本語+英語）

gpu\_usage: false：CPU モード（GPU メモリの節約、安定性重視）

confidence\_threshold: 0.5：認識確信度閾値（0.5 以上のみ採用）

Mud\_Filter\_Config

regex\_pattern: "\[^\\\\s\\\\w]|\[\\\\w]+"：トークン化パターン

min\_word\_length: 2：抽出される語の最小文字数

excluded\_vocab\_count: 22：除外キーワード総数

除外キーワード例：chrome、ファイル、編集、表示、http、https、www、クリック、ドラッグ等

Purity\_Score\_Algorithm

audio\_weight: 0.6：音声由来の情報に対する重み付け

visual\_weight: 0.4：視覚由来の情報に対する重み付け

core\_keywords: \["再出品", "注意", "禁止", "即座に", "修正", "規約"]：高スコア判定キーワード

mud\_penalty\_factor：不要テキスト含有時のペナルティ（2個以上で 80% 削減）

4\. system\_architecture.md

目的：システムアーキテクチャの技術仕様書。4段階処理フロー、各ステップの詳細、非機能要件を記述



セクション構成：



処理フロー（境界線の定義）



Step 1: 物理抽出（Whisper、FFmpeg）

Step 2: 視覚純化（EasyOCR、Mud フィルタ）

Step 3: 論理抽出（OFLOOP、Purity Scoring）

Step 4: 物理台帳構築（Core JSON、Sidecar DB）

非機能要件・制約



FFmpeg 動画編集はスコープ外

出力形式：常に Mk2\_Core\_{ID}.json と Mk2\_Sidecar\_{ID}.db

5\. instructions.md

目的：Gemini API に与える「結晶化プロトコル Ver.2.2」。AI が知識抽出時に従う思考規範を定義



セクション構成：



思考のフィルタリング（Anti-Noise）



「えー」「あのー」といったフィラーを除外

「皆さんお疲れ様です」といった形式的挨拶を除外

原子分解の再構成（Knowledge Structuring）



FACT：客観的プラットフォーム挙動

Logic：根拠・理由

Procedure：実行可能アクション

Case：事例・ケーススタディ

スタイル・レギュレーション



ビジネス文体への変換

文末統制（〜すること、〜である）

Purity Score 絶対評価基準



100.0：利益直結、視覚的エビデンス有

90.0以上：致命的リスク回避

10.0以下：本質的価値なし

6\. DEVELOPMENT\_GUIDELINES.md

目的：GitHub リポジトリの開発運用ガイドライン。ブランチ戦略、PR メッセージ形式、コミット規約を定義



主要セクション：



ブランチ構成：main（本番）と ai-dev（開発用）

基本ルール：AI は ai-dev のみ編集、main へのマージは人間のみ

開発フロー：ai-dev で作業 → PR 作成 → 人間レビュー → main にマージ

PR メッセージテンプレート：目的・主な変更点・影響範囲を日本語で記載

コミットメッセージ規約：\[タイプ] 説明 形式（feat/fix/refactor/docs/test/chore/perf）

7\. SYSTEM\_OVERVIEW.md

目的：システム全体の構成図、ファイル役割、処理フロー、トラブルシューティングをカバーする統合ガイド



8\. FILE\_STRUCTURE.md

目的：プロジェクト内の全ファイルを一覧化し、各ファイルの役割・依存関係を明確化（本ドキュメント）



依存関係マップ

run\_antigravity.bat

&#x20; ↓ (起動)

master\_batch\_refiner.py

&#x20; ├─→ config\_params.json (パラメータ参照)

&#x20; ├─→ Whisper モデル（初期化）

&#x20; ├─→ EasyOCR（初期化）

&#x20; ├─→ Gemini API（初期化）

&#x20; ├─→ FFmpeg（subprocess で外部呼び出し）

&#x20; └─→ SQLite3（DB 操作）



instructions.md

&#x20; └─→ Gemini API プロンプトとして埋め込み（master\_batch\_refiner.py 内）



system\_architecture.md

&#x20; └─→ 技術仕様書（参考用、プログラムに直接依存なし）



出力ファイル群（archive ディレクトリ）

&#x20; ├─ Mk2\_Core\_{lecture\_id}.json

&#x20; ├─ Mk2\_Sidecar\_{lecture\_id}.db

&#x20; └─ Mk2\_OCR\_{lecture\_id}.txt

編集ガイドライン

ai-dev ブランチで編集対象のファイル

ファイル	編集権限	更新頻度	注意点

master\_batch\_refiner.py	AI（genspark 含む）	改善・機能追加時	Step 3 の Gemini プロンプトは instructions.md と同期を保つこと

config\_params.json	AI（genspark 含む）	パラメータチューニング時	値の変更は十分にテストしてから

system\_architecture.md	AI（genspark 含む）	アーキテクチャ変更時	実装と仕様書の同期を保つこと

instructions.md	AI（genspark 含む）	Gemini プロンプト改善時	master\_batch\_refiner.py 内の prompt 変数と同期を保つこと

DEVELOPMENT\_GUIDELINES.md	AI（genspark 含む）	開発ルール変更時	nario との相談後に更新

SYSTEM\_OVERVIEW.md	AI（genspark 含む）	ドキュメント更新時	FILE\_STRUCTURE.md と内容を重複させない

FILE\_STRUCTURE.md	AI（genspark 含む）	ファイル構成変更時	常に最新の構成を反映させること

main ブランチへのマージ条件

コード品質：エラーハンドリングが実装されていること

テスト：単体テストまたは手動テストが実施されていること

ドキュメント：変更に対応する仕様書が更新されていること

セキュリティ：API キーなどの機密情報が埋め込まれていないこと

よくある質問

Q: Mk2\_OCR\_XX.txt は何に使うのか？ A: 中間出力で、Mud フィルタ後の視覚テキストです。デバッグやシステムの検証に使用されます。処理後は削除しても構いません。



Q: Mk2\_Sidecar\_XX.db はいつ必要か？ A: 知識エレメントと動画内の位置（タイムスタンプ）を紐付けたい場合に使用します。知識の出典確認やビデオ編集時に有用です。



Q: config\_params.json を編集しても反映されない A: master\_batch\_refiner.py が起動時に config を読み込まないため、ハードコードされたパラメータが優先されます。改善が必要です。



Q: Gemini API のモデル ID を変更したい A: master\_batch\_refiner.py の MODEL\_ID = "gemini-3-pro-preview" を編集し、対応するプロンプト（Step 3）の検証を行ってください。



Q: 処理を途中から再開できるか？ A: 現在はできません。01\_ プレフィックスを付けて処理済みファイルを標識しています。チェックポイント機構の実装が課題です。





\---



これらの2つのファイルをローカルに作成して、git で ai-dev にコミット・push していただけますか？



完了後、コマンドは以下のようになります：



```bash

cd D:\\AI\_スクリプト成果物\\動画スクレイピングプロジェクト



git add SYSTEM\_OVERVIEW.md FILE\_STRUCTURE.md

git commit -m "docs: システム構成図とファイル役割を文章化"

git push origin ai-dev







