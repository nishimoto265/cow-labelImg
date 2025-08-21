# BB Duplication Mode

## 概要

BB Duplication Mode（BB複製モード）は、新規作成したBounding Boxを自動的に後続フレームに複製する機能です。同一オブジェクトが連続するフレームに存在する場合のアノテーション作業を効率化します。

## 仕様

### 基本動作
1. BB複製モードを有効化
2. BBを新規作成
3. 指定した数の後続フレームに自動複製
4. IOU（Intersection over Union）による重複検出
5. 重複時は上書きまたはスキップ

### IOU判定
- 現在フレームと各後続フレームでIOU計算を実施
- 閾値以上のIOUを持つBBを重複と判定
- デフォルト閾値: 0.6

### 複製処理
- 現在のフレームを含めて処理（IOU判定あり）
- 進行度表示（QProgressDialog）
- キャンセル可能

## 使用方法

1. 「BB複製モード」チェックボックスをON
2. 複製フレーム数を設定（1-100）
3. IOU閾値を設定（0.1-1.0）
4. 上書きモードを選択
5. BBを新規作成すると自動的に複製

### 上書きモード
- ON: 重複BBを削除して新規BBで置換
- OFF: 重複があるフレームはスキップ

## 技術詳細

### ファイル構成
- labelImg.py - メイン実装
- libs/undo/commands/bb_duplication_commands.py - Undoコマンド

### 主要メソッド
```
labelImg.py:
- toggle_bb_duplication(state): モード切り替え
- duplicate_bb_to_subsequent_frames(source_shape): 複製処理
- calculate_iou(box1, box2): IOU計算
- update_overwrite_checkbox_text(): UI更新

bb_duplication_commands.py:
- class AddShapeWithIOUCheckCommand: IOU判定付き追加コマンド
```

### Undo/Redo対応
- CompositeCommandで全フレームの操作を一括管理
- 1回のundoで全複製を取り消し
- redoで全複製を再実行

## 設定項目

### UI要素
- bb_duplication_checkbox: モード有効/無効
- bb_dup_frame_count: 複製フレーム数（スピンボックス）
- bb_dup_iou_threshold: IOU閾値（ダブルスピンボックス）
- bb_dup_overwrite_checkbox: 上書きモード

### デフォルト値
- 複製フレーム数: 5
- IOU閾値: 0.6
- 上書きモード: OFF

### 設定範囲
- フレーム数: 1-100
- IOU閾値: 0.1-1.0

## 制限事項

1. 最大100フレームまでの複製制限
2. フレーム移動せずにアノテーションファイルを直接編集
3. 画像ファイルが存在しないフレームはスキップ
4. 複製中のフレーム編集は不可
5. YOLO形式とPascal VOC形式のみ対応