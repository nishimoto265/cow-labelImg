# Click-to-Change Label Mode

## 概要

Click-to-Change Label Mode（クリックでラベル変更モード）は、キャンバス上のBounding Boxをクリックすることで素早くラベルを変更できる機能です。

## 仕様

### 基本動作
1. シングルクリックで形状を選択
2. ダブルクリックで現在のクイックIDを適用
3. 連続ID付けモードと連携して後続フレームに伝播

### クリック判定
- シングルクリック: 形状の選択のみ
- ダブルクリック: ラベル変更実行
- クリック位置から最も近い形状を選択

### ラベル適用
- Quick ID Selectorで選択中のIDを適用
- 元のラベルを記録してUndo可能
- 連続ID付けモードが有効な場合は自動伝播

## 使用方法

1. 「クリックでラベル変更」チェックボックスをON
2. Quick ID Selector（Wキー）でIDを選択
3. 変更したいBounding Boxをダブルクリック
4. 自動的にラベルが変更される

### 連続ID付けモードとの併用
- 両モードを有効にすると、ダブルクリック時に後続フレームにも伝播
- IOUベースの追跡により対応する形状を検出

## 技術詳細

### ファイル構成
- labelImg.py - メイン実装
- libs/canvas.py - クリックイベント処理

### 主要メソッド
```
labelImg.py:
- toggle_click_change_label(state): モード切り替え (labelImg.py:2046-2049)
- on_shape_clicked(): クリックイベントハンドラ (labelImg.py:2371-2400)
- apply_label_to_all_frames(shape, item, new_label, old_label): ラベル適用 (labelImg.py:2401-2486)

canvas.py:
- mousePressEvent(event): マウスイベント処理 (libs/canvas.py:590-650)
- shape_clicked = pyqtSignal(): クリック通知シグナル (libs/canvas.py:55)
```

### イベント処理フロー
1. canvas.pyでマウスクリックを検出
2. shape_clickedシグナルを発火
3. labelImg.pyのon_shape_clicked()で処理
4. ダブルクリック判定と処理実行

### Undo/Redo対応
- ChangeLabelCommandで変更を記録
- 連続ID付けモードの場合はCompositeCommandで管理

## 設定項目

### UI要素
- click_change_label_checkbox: モード有効/無効

### デフォルト値
- ダブルクリック判定時間: システムデフォルト
- 選択可能な最大距離: 制限なし（最も近い形状を選択）

## 制限事項

1. 重なっている形状の場合、最前面の形状が選択される
2. Quick ID Selectorが開いていない場合は動作しない
3. 形状が存在しないフレームでは無効
4. ロックされた形状は変更できない
5. 形状の外側をクリックしても反応しない