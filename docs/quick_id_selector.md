# Quick ID Selector

## 概要

Quick ID Selectorは、キーボードショートカットまたはマウスクリックで素早くIDを選択・適用できる半透明フローティングウィンドウ機能です。動物の個体識別などで頻繁にIDを切り替える作業を効率化します。

## 仕様

### 基本動作
- Wキーでウィンドウの表示/非表示を切り替え
- 数字キー（1-9, 0）でIDを直接選択
- マウスクリックでID選択
- 選択したIDは現在選択中のBounding Boxに適用

### ID範囲
- 最大30個のIDをサポート
- ID 1-9: キーボードの1-9キーに対応
- ID 10: キーボードの0キーに対応
- ID 11-30: マウスクリックのみ

### 表示仕様
- 半透明ウィンドウ（透明度70%）
- 6×5のグリッドレイアウト
- 現在選択中のIDをハイライト表示
- 不足しているIDを赤色で表示

## 使用方法

1. Wキーを押してQuick ID Selectorを表示
2. 以下のいずれかの方法でIDを選択：
   - 数字キー1-9を押す（ID 1-9）
   - 0キーを押す（ID 10）
   - ウィンドウ内のIDボタンをクリック
3. 選択したIDが現在のshapeに適用される
4. 連続ID付与モードが有効な場合、後続フレームにも伝播

## 技術詳細

### ファイル構成
- libs/quick_id_selector.py - メインクラス実装
- labelImg.py - 統合部分

### クラス構造
```
class QuickIDSelector(QDialog): (libs/quick_id_selector.py:8-156)
    主要メソッド:
    - __init__(parent, max_ids=30): 初期化 (lines 9-44)
    - set_current_id(id_str): 現在のID設定 (lines 126-133)
    - update_missing_labels(): 不足ラベル更新 (lines 135-156)
    - keyPressEvent(event): キーボード入力処理 (lines 107-124)
    
    シグナル:
    - id_selected(str): ID選択時に発火 (line 45)
```

### labelImg.py統合ポイント
```
メソッド:
- toggle_quick_id_selector(): 表示切り替え (labelImg.py:2062-2071)
- select_quick_id(id_str): ID選択処理 (labelImg.py:2072-2078)
- on_quick_id_selected(id_str): ID選択イベントハンドラ (labelImg.py:2079-2084)
- apply_quick_id_to_selected_shape(): 選択shapeへの適用 (labelImg.py:2085-2091)
- apply_quick_id_with_propagation(): 伝播処理 (labelImg.py:2488-2552)
```

## 設定項目

### カスタマイズ可能な項目
- max_ids: 最大ID数（デフォルト: 30）
- window_opacity: ウィンドウ透明度（デフォルト: 0.7）
- grid_columns: グリッドの列数（デフォルト: 6）
- button_size: ボタンサイズ（デフォルト: 50×50）

### ウィンドウ位置
- 初期位置: 画面右上
- ユーザーによる移動可能
- 位置は保持されない（再表示時はリセット）

## 制限事項

1. キーボードショートカットは1-10のIDのみ対応
2. 31個以上のIDは表示できない
3. ウィンドウ位置はセッション間で保存されない
4. 他のアプリケーションより前面に表示される（常に最前面）
5. IDの順序は数値順に固定