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





