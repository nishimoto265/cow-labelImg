# cow-labelImg Documentation

このディレクトリには、cow-labelImgに追加された各機能の詳細な仕様書が含まれています。

## ドキュメント一覧

### 基本機能
- quick_id_selector.md - 素早いID選択機能
- bb_duplication_mode.md - BB複製モード
- continuous_tracking_mode.md - 連続ID付与モード（IOU追跡）
- click_change_label_mode.md - クリックでラベル変更モード
- undo_redo_system.md - 操作の取り消し・やり直し機能

### 表示オプション
- drawing_options.md - BB・IDの表示/非表示設定

### アーキテクチャ
- architecture.md - システム全体の構成
- dependencies.md - 依存関係とパッケージ要件

## 実装状況

各機能の実装状態：
- Quick ID Selector: 実装済み v1.0
- BB Duplication Mode: 実装済み v1.1
- Continuous Tracking Mode: 実装済み v1.2
- Click-to-Change Label: 実装済み v1.0
- Undo/Redo System: 実装済み v2.0
- Drawing Options: 実装済み v1.0

## ドキュメント規約

各機能のドキュメントには以下の内容を含めてください：

1. 概要 - 機能の目的と概要説明
2. 仕様 - 詳細な動作仕様
3. 使用方法 - ユーザー向けの操作手順
4. 技術詳細 - 実装の技術的な詳細
5. 設定項目 - 設定可能なパラメータ
6. 制限事項 - 既知の制限や注意点

## 更新履歴

- 2024-01-21: ドキュメント構造を機能別に再編成
- 2024-01-21: Undo/Redo SystemをCommand Patternベースに更新
- 2024-01-21: Continuous Tracking ModeをIOU追跡ベースに修正