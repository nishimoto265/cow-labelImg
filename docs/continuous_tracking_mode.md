# Continuous Tracking Mode

## 概要

Continuous Tracking Mode（連続ID付与モード）は、以下の2つの追跡方式でフレーム間でオブジェクトを追跡し、ラベルを自動的に伝播する機能です：
1. **IOU追跡**: 形状の重なり（Intersection over Union）による追跡
2. **ID追跡**: 同じLabel1（ID）を持つオブジェクトの追跡

## 仕様

### 追跡モード
#### IOU追跡モード
- 前フレームの形状と現フレームの形状をIOU計算で比較
- 閾値（デフォルト: 0.4）以上のIOUを持つ形状をマッチと判定
- 元のラベルに関係なく、形状の重なりのみで追跡
- 最もIOUが高い形状を選択

#### ID追跡モード
- 同じLabel1（ID）を持つオブジェクトを追跡
- 複数の同じIDがある場合は最初に見つかったものを選択
- 形状の位置に関係なく、IDのみで追跡
- Label1とLabel2の両方を更新可能

### フレーム数制限
- ユーザーが指定した最大フレーム数まで伝播
- デフォルト: 100フレーム
- 最小: 1フレーム
- 最大: 1000フレーム

### 基本動作
1. 追跡モード（IOU/ID）を選択
2. 最大フレーム数を設定
3. 現在のフレームでラベルを変更
4. 選択した追跡方式で後続フレームの対応する形状を検出
5. マッチした形状にラベルを伝播
6. 停止条件に達するか最大フレーム数に達するまで継続

### 停止条件
#### IOU追跡の場合
- IOUがしきい値（0.4）未満のフレーム
- 画像ファイルが存在しないフレーム
- 最大フレーム数に到達
- ユーザーによるキャンセル

#### ID追跡の場合
- 対象IDが存在しないフレーム
- 画像ファイルが存在しないフレーム
- 最大フレーム数に到達
- ユーザーによるキャンセル

### 伝播処理
- 直接ファイル編集（フレーム移動なし）
- YOLO形式とPascal VOC形式に対応
- 進行度表示付き（QProgressDialog）
- キャンセル可能

## 使用方法

### GUI設定
1. 「連続ID付けモード」チェックボックスをON
2. 追跡モードを選択:
   - 「IOU追跡」: 形状の重なりで追跡
   - 「ID追跡」: 同じIDで追跡
3. 最大フレーム数をスピンボックスで設定（1-1000）
4. 対象のBounding Boxを選択
5. ラベルを変更（Quick ID Selectorまたは手動）
6. 自動的に後続フレームに伝播

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
- toggle_continuous_tracking(state): モード切り替え
- set_tracking_mode(mode): 追跡モード設定（IOU/ID）
- set_max_tracking_frames(frames): 最大フレーム数設定
- propagate_label_to_subsequent_frames(): 伝播処理
- track_by_iou(): IOU追跡処理
- track_by_id(): ID追跡処理
- calculate_iou(box1, box2): IOU計算
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

### ID追跡
```python
def track_by_id(target_id, shapes):
    # 同じIDを持つ形状を検索
    for idx, shape in enumerate(shapes):
        if shape.get('label') == target_id:
            return idx
    return -1
```

### Undo/Redo対応
- ChangeLabelCommandで単一フレームの変更を管理
- ChangeDualLabelCommandでデュアルラベルの変更を管理
- CompositeCommandで複数フレームの変更を一括管理
- 1回のundoで全伝播を取り消し

## 設定項目

### UI要素
- continuous_tracking_checkbox: モード有効/無効
- tracking_mode_group: 追跡モード選択（IOU/ID）
- max_frames_spinbox: 最大フレーム数設定

### デフォルト値
- 追跡モード: IOU
- IOU閾値: 0.4
- 最大伝播フレーム数: 100
- フレーム数範囲: 1-1000

### 設定の保存
- 追跡モード設定は保存される
- 最大フレーム数設定は保存される
- 次回起動時に復元

## 制限事項

### IOU追跡の制限
1. 形状が大きく変化すると追跡が切れる
2. 複数の重なる形状がある場合、最もIOUが高いものを選択
3. 回転や変形に弱い

### ID追跡の制限
1. 同じIDが複数ある場合、最初のものを選択
2. IDが変更されると追跡できない
3. 新規追加されたオブジェクトは追跡対象外

### 共通の制限
1. 画像ファイルが存在しないフレームはスキップ
2. YOLO形式とPascal VOC形式のみ対応
3. CreateML形式は未対応
4. 最大1000フレームまで