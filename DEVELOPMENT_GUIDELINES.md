\# 開発運用ガイドライン



\## リポジトリ運用方針



このリポジトリ `video-scraper` は、以下のルールで運用します。



\### ブランチ構成



| ブランチ | 役割 | 編集権限 |

|---------|------|--------|

| `main` | 本番相当の安定コード | 人間のみ（nario） |

| `ai-dev` | AI開発用の作業ブランチ | AI（Gensparkを含む） |



\### 基本ルール



1\. \*\*AI は `ai-dev` ブランチのみを編集対象とする\*\*

&#x20;  - `main` ブランチへの直接 push／force push は禁止

&#x20;  - 緊急時を除き、`main` への変更は人間のレビューを経由



2\. \*\*`main` ブランチの保護\*\*

&#x20;  - 本番相当のコードを置く

&#x20;  - リリースや本番実行の基準となる

&#x20;  - `ai-dev` からの PR マージのみで変更を受け付ける



3\. \*\*`ai-dev` ブランチの位置付け\*\*

&#x20;  - AI が自由にコード修正・機能追加・リファクタリングを行う作業用ブランチ

&#x20;  - 原則として `main` からの最新状態を取り込みつつ作業する

&#x20;  - 問題があればブランチごと破棄してもよい一時的な作業領域



\---



\## 開発フロー



\### 1. 作業開始時



```bash

\# ai-dev を最新化

git checkout ai-dev

git pull origin main  # main の最新状態を取り込む

git pull origin ai-dev

---

## GitHub Issue 運用ルール

タスクの進捗管理は GitHub Issue で行う。
各担当者はラベルを変更することで現在のステータスを示す。

### フロー

| ステップ | 担当 | アクション | ラベル |
|---------|------|-----------|-------|
| 1 | Genspark | Issue作成・指示書を本文に記載 | `task:genspark` |
| 2 | Antigravity | 実装・push → Issueに「PR作成：#XX」コメント | `task:antigravity` |
| 3 | Perplexity | PRにチェック結果をコメント | `review:git-ai` |
| 4 | nario | 確認・マージ → Issueをクローズ | `status:done` |

### ラベル一覧

| ラベル名 | 意味 |
|---------|------|
| `task:genspark` | Genspark が指示書を作成・Issue オープン中 |
| `task:antigravity` | Antigravity が実装中・PR作成済み |
| `review:git-ai` | Perplexity がレビュー中 |
| `status:done` | 完了・マージ済み |



