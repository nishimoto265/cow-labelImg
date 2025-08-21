# Continuous Tracking Mode

## 概要

Continuous Tracking Mode（連続ID付与モード）は、IOU（Intersection over Union）による形状マッチングを使用して、フレーム間でオブジェクトを追跡し、ラベルを自動的に伝播する機能です。

## 仕様

### 基本動作
1. 現在のフレームでラベルを変更
2. IOUベースで後続フレームの対応する形状を検出
3. マッチした形状にラベルを伝播
4. 変更先のラベルが既に存在する場合は停止

### IOU追跡アルゴリズム
- 前フレームの形状と現フレームの形状をIOU計算で比較
- 閾値（デフォルト: 0.4）以上のIOUを持つ形状をマッチと判定
- 元のラベルに関係なく、形状の重なりのみで追跡
- 最もIOUが高い形状を選択

### 伝播処理
- 直接ファイル編集（フレーム移動なし）
- YOLO形式とPascal VOC形式に対応
- 進行度表示付き（QProgressDialog）
- キャンセル可能

### 停止条件
- 変更先のラベルが既に存在するフレーム
- IOUがしきい値未満のフレーム
- 画像ファイルが存在しないフレーム
- ユーザーによるキャンセル

## 使用方法

1. 「連続ID付けモード」チェックボックスをON
2. 対象のBounding Boxを選択
3. ラベルを変更（Quick ID Selectorまたは手動）
4. 自動的に後続フレームに伝播

### クリックでラベル変更との併用
- 「クリックでラベル変更」モードと併用可能
- ダブルクリックでラベル変更と同時に伝播

## 技術詳細

### ファイル構成
- labelImg.py - メイン実装
- libs/tracker.py - トラッカークラス（未使用）
- libs/undo/commands/label_commands.py - Undoコマンド

### 主要メソッド
```
labelImg.py:
- toggle_continuous_tracking(state): モード切り替え (labelImg.py:2032-2045)
- propagate_label_to_subsequent_frames(source_shape): 伝播処理 (labelImg.py:2740-2760)
- _propagate_label_to_subsequent_frames_multi(): 複数フレーム処理 (labelImg.py:2760-2985)
- calculate_iou(box1, box2): IOU計算 (labelImg.py:2312-2336)
```

### IOU計算
```python
def calculate_iou(box1, box2):
    # 矩形の座標を取得
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    # 重なり面積
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # 各矩形の面積
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    # IOU計算
    union = area1 + area2 - intersection
    return intersection / union if union > 0 else 0
```

### Undo/Redo対応
- ChangeLabelCommandで単一フレームの変更を管理
- CompositeCommandで複数フレームの変更を一括管理
- 1回のundoで全伝播を取り消し

## 設定項目

### UI要素
- continuous_tracking_checkbox: モード有効/無効

### デフォルト値
- IOU閾値: 0.4
- 最大伝播フレーム数: 制限なし（ファイル末尾まで）

## 制限事項

1. IOUベースのため、形状が大きく変化すると追跡が切れる
2. 複数の重なる形状がある場合、最もIOUが高いものを選択
3. 画像ファイルが存在しないフレームはスキップ
4. YOLO形式とPascal VOC形式のみ対応
5. CreateML形式は未対応