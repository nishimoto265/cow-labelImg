# Architecture

## 概要

cow-labelImgは、オリジナルのlabelImgに独自機能を追加したアノテーションツールです。PyQt5ベースのGUIアプリケーションとして実装され、モジュラー設計により機能拡張が容易な構造になっています。

## システム構成

### コア構造
```
cow-labelImg/
├── labelImg.py              # メインアプリケーション
├── libs/                    # ライブラリモジュール
│   ├── canvas.py           # 描画キャンバス
│   ├── shape.py            # 形状データ
│   ├── pascal_voc_io.py   # Pascal VOC形式I/O
│   ├── yolo_io.py          # YOLO形式I/O
│   ├── create_ml_io.py     # CreateML形式I/O
│   ├── quick_id_selector.py # Quick IDセレクター
│   ├── tracker.py          # オブジェクトトラッカー
│   └── undo/               # Undo/Redoシステム
│       ├── undo_manager.py
│       └── commands/
└── resources/              # リソースファイル
```

### レイヤー構造

#### プレゼンテーション層
- PyQt5ベースのGUI
- メインウィンドウ（MainWindow）
- ダイアログ（Quick ID Selector等）
- キャンバス（Canvas）

#### ビジネスロジック層
- アノテーション管理
- 形状操作
- ファイルI/O
- Undo/Redo管理

#### データ層
- 形状データ（Shape）
- アノテーションファイル
- 設定ファイル

## 主要コンポーネント

### MainWindow (labelImg.py:80-3600)
- アプリケーションのエントリーポイント
- UI管理とイベント処理
- 各機能モジュールの統合

### Canvas (libs/canvas.py:40-850)
- 画像表示と描画処理
- マウス/キーボードイベント処理
- 形状の選択と操作

### Shape (libs/shape.py:20-200)
- Bounding Boxデータ構造
- 座標管理
- 表示プロパティ

### UndoManager (libs/undo/undo_manager.py:4-77)
- Command Patternによる操作管理
- Undo/Redoスタック管理
- コマンド実行制御

### I/Oモジュール
- YoloReader/Writer: YOLO形式 (libs/yolo_io.py)
- PascalVocReader/Writer: Pascal VOC形式 (libs/pascal_voc_io.py)
- CreateMLReader/Writer: CreateML形式 (libs/create_ml_io.py)

## データフロー

### アノテーション作成フロー
1. ユーザー操作（マウス/キーボード）
2. Canvas.mousePressEvent()でイベント検出 (libs/canvas.py:590-650)
3. MainWindow.newShape()で形状作成 (labelImg.py:1292-1479)
4. UndoManager.execute_command()でコマンド実行 (libs/undo/undo_manager.py:10-27)
5. Shape追加とファイル保存

### ファイル読み込みフロー
1. MainWindow.loadFile()でファイル選択 (labelImg.py:1680-1780)
2. 画像読み込みとキャンバス更新
3. アノテーションファイル検索
4. 形式判定とReader選択
5. 形状データ読み込みと表示

### Undo/Redoフロー
1. ユーザー操作をCommandオブジェクト化
2. UndoManagerのスタックに追加
3. Undo時: Command.undo()実行 (libs/undo/undo_manager.py:29-45)
4. Redo時: Command.redo()実行 (libs/undo/undo_manager.py:47-63)

## イベント処理

### シグナル/スロット
```python
# 主要なシグナル
canvas.shapeSelectionChanged (libs/canvas.py:56)
canvas.shapeMoved (libs/canvas.py:57)
canvas.newShape (libs/canvas.py:54)
canvas.shape_clicked (libs/canvas.py:55)

# Quick ID Selector
quick_id_selector.id_selected (libs/quick_id_selector.py:45)

# 形状変更通知
shape.labelChanged
shape.pointsChanged
```

### キーボードショートカット管理
- QActionによるショートカット定義 (labelImg.py:400-600)
- keyPressEventでのカスタム処理 (labelImg.py:1900-1990)
- グローバルとローカルのショートカット

## 拡張ポイント

### 新機能追加
1. libsディレクトリに機能モジュール追加
2. MainWindowで統合処理実装
3. UIウィジェット追加
4. シグナル/スロット接続

### 新しいアノテーション形式
1. I/Oモジュール作成（Reader/Writer）
2. MainWindowでファイル形式判定追加
3. 保存/読み込み処理統合

### カスタムコマンド
1. base_command.pyを継承
2. execute/undo/redo実装
3. UndoManagerで管理

## パフォーマンス最適化

### メモリ管理
- 画像キャッシュの制限
- Undoスタックサイズ制限 (100操作)
- 不要なオブジェクトの解放

### 描画最適化
- 必要な領域のみ再描画
- 形状データのキャッシュ
- バッチ処理での更新

### ファイルI/O最適化
- 直接ファイル編集（フレーム移動なし）
- 並列処理での読み込み
- インクリメンタル保存

## 設定管理

### 設定ファイル
- デフォルト設定
- ユーザー設定
- プロジェクト設定

### 設定項目
- UI設定（ウィンドウサイズ等）
- 機能設定（閾値、デフォルト値）
- ショートカット設定

## エラー処理

### エラー処理方針
- ユーザー操作のエラーは通知
- 内部エラーはログ記録
- クリティカルエラーは安全に終了

### ログ管理
- デバッグログ出力
- エラーログ記録
- 操作履歴記録