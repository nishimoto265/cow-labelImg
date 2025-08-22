# デュアルラベルシステム設計書

## 概要
cow-labelImgに2種類のラベルを同時に管理できる機能を追加します。これにより、1つのBounding Boxに対して2つの異なるラベル（例：動物の種類とID、または異なる分類基準）を付与できるようになります。

## 主要な変更点

### 1. データ構造の変更

#### Shape クラス (libs/shape.py)
現在の構造：
```python
self.label = label  # 単一のラベル
```

変更後の構造：
```python
self.label1 = label1  # 第1ラベル（メインラベル）
self.label2 = label2  # 第2ラベル（サブラベル）
self.label = label1   # 後方互換性のため維持
```

### 2. GUI コンポーネントの変更

#### 2.1 メインウィンドウ (labelImg.py)
追加する UI 要素：
- **ラベル選択チェックボックス**
  - Label 1: □ （第1ラベルの変更を有効/無効）
  - Label 2: □ （第2ラベルの変更を有効/無効）
  - 両方チェック時は両方のラベルが変更される
  
- **ラベル表示切り替えトグル**
  - Label 1を表示/非表示
  - Label 2を表示/非表示
  - 両方表示（デフォルト）

- **デフォルトラベル設定**
  - Default Label 1: [テキストボックス]
  - Default Label 2: [テキストボックス]

#### 2.2 ラベルダイアログ (libs/labelDialog.py)
変更内容：
```python
class DualLabelDialog(QDialog):
    def __init__(self, label1="", label2="", parent=None, list_item1=None, list_item2=None):
        # 2つのラベル入力フィールド
        self.edit1 = QLineEdit()  # Label 1
        self.edit2 = QLineEdit()  # Label 2
        
        # それぞれのリストウィジェット
        self.list_widget1 = QListWidget()
        self.list_widget2 = QListWidget()
```

#### 2.3 クイックID選択 (libs/quick_id_selector.py)
変更内容：
- 2つのタブまたはセクションを追加
  - Label 1 セクション：第1ラベル用のクイック選択ボタン
  - Label 2 セクション：第2ラベル用のクイック選択ボタン
- 現在選択されているラベルタイプを表示
- キーボードショートカット：
  - 1-9, 0: Label 1のID選択
  - Shift+1-9, 0: Label 2のID選択

### 3. 色分け機能

#### Canvas クラス (libs/canvas.py)
BBの色を2つのラベルに基づいて決定：
```python
def get_shape_color(self, shape):
    if self.color_mode == "label1":
        return self.get_color_for_label(shape.label1)
    elif self.color_mode == "label2":
        return self.get_color_for_label(shape.label2)
    else:  # combined mode
        return self.get_combined_color(shape.label1, shape.label2)
```

色モード：
- Label 1 ベース：第1ラベルに基づいて色分け
- Label 2 ベース：第2ラベルに基づいて色分け
- 組み合わせ：両方のラベルを考慮した色分け

### 4. ファイル保存形式の変更

#### 4.1 YOLO形式 (libs/yolo_io.py)
現在の形式：
```
class_id x_center y_center width height
```

変更後の形式（オプション）：
```
class_id1 class_id2 x_center y_center width height
```
または別ファイル管理：
- labels1.txt: 第1ラベル用
- labels2.txt: 第2ラベル用

#### 4.2 Pascal VOC形式 (libs/pascal_voc_io.py)
XMLに新しいフィールドを追加：
```xml
<object>
    <name>label1_value</name>
    <label2>label2_value</label2>
    <pose>Unspecified</pose>
    <truncated>0</truncated>
    <difficult>0</difficult>
    <bndbox>
        <xmin>100</xmin>
        <ymin>100</ymin>
        <xmax>200</xmax>
        <ymax>200</ymax>
    </bndbox>
</object>
```

### 5. クリックでラベル変更機能

#### 実装詳細：
1. **チェックボックスの状態管理**
   - Label 1変更: self.change_label1_enabled
   - Label 2変更: self.change_label2_enabled

2. **クリックイベント処理**
```python
def handle_shape_click(self, shape):
    if self.change_label1_enabled and self.change_label2_enabled:
        # 両方のラベルを変更
        shape.label1 = self.current_label1
        shape.label2 = self.current_label2
    elif self.change_label1_enabled:
        # Label 1のみ変更
        shape.label1 = self.current_label1
    elif self.change_label2_enabled:
        # Label 2のみ変更
        shape.label2 = self.current_label2
```

### 6. キーボードショートカット

新しいショートカット：
- `Alt+1`: Label 1の変更モードをトグル
- `Alt+2`: Label 2の変更モードをトグル
- `Alt+D`: デュアルラベルダイアログを開く
- `Ctrl+Shift+1`: Label 1のデフォルト値を設定
- `Ctrl+Shift+2`: Label 2のデフォルト値を設定

### 7. 設定の保存

settings.py に追加する設定項目：
```python
# デュアルラベル設定
'dual_label_enabled': True,
'default_label1': '',
'default_label2': '',
'label1_history': [],
'label2_history': [],
'color_mode': 'label1',  # 'label1', 'label2', 'combined'
'show_label1': True,
'show_label2': True,
'change_label1_enabled': True,
'change_label2_enabled': False,
```

### 8. Undo/Redo システムの対応

libs/undo/commands/label_commands.py を拡張：
```python
class ChangeDualLabelCommand(Command):
    def __init__(self, shape, old_label1, new_label1, old_label2, new_label2):
        self.shape = shape
        self.old_label1 = old_label1
        self.new_label1 = new_label1
        self.old_label2 = old_label2
        self.new_label2 = new_label2
```

### 9. 互換性の維持

- 既存の単一ラベルファイルを読み込んだ場合、label1に値を設定し、label2は空文字列とする
- 保存時に互換モードオプションを提供（単一ラベル形式で保存）

### 10. UI レイアウト案

```
┌─────────────────────────────────────┐
│ File Edit View Help                 │
├─────────────────────────────────────┤
│ ┌───────────────┬─────────────────┐ │
│ │               │ Labels Panel     │ │
│ │               │ ┌───────────────┐│ │
│ │               │ │Label Settings ││ │
│ │  Image Area   │ │ □ Label 1     ││ │
│ │               │ │ □ Label 2     ││ │
│ │               │ │               ││ │
│ │               │ │Color Mode:    ││ │
│ │               │ │○ Label 1      ││ │
│ │               │ │○ Label 2      ││ │
│ │               │ │○ Combined     ││ │
│ │               │ └───────────────┘│ │
│ │               │                   │ │
│ │               │ BB List          │ │
│ │               │ ┌───────────────┐│ │
│ │               │ │1: Dog | ID-001││ │
│ │               │ │2: Cat | ID-002││ │
│ │               │ │3: Dog | ID-003││ │
│ │               │ └───────────────┘│ │
│ └───────────────┴─────────────────┘ │
│ Default Label 1: [________] Set     │
│ Default Label 2: [________] Set     │
└─────────────────────────────────────┘
```

## 実装優先順位

1. **Phase 1: 基本機能**
   - Shape クラスの拡張
   - 基本的なUI要素の追加
   - ラベル変更機能

2. **Phase 2: 拡張機能**
   - 色分け機能
   - クイックID選択の対応
   - キーボードショートカット

3. **Phase 3: ファイル保存**
   - YOLO/VOC形式の対応
   - 互換性モード

4. **Phase 4: 完成度向上**
   - Undo/Redo対応
   - 設定の保存/復元
   - テストコード

## テスト項目

1. 単一ラベルから2ラベルへの移行テスト
2. ラベル変更の動作確認
3. ファイル保存/読み込みテスト
4. Undo/Redo動作確認
5. 色分け表示テスト
6. キーボードショートカットテスト

## 考慮事項

- パフォーマンス：2つのラベルを管理することによる処理速度への影響
- メモリ使用量：追加データ構造によるメモリ消費
- UI の複雑性：ユーザビリティを損なわないインターフェース設計
- データ移行：既存のアノテーションデータとの互換性

## 今後の拡張可能性

- 3つ以上のラベルへの対応
- ラベル間の関係性定義（階層構造など）
- ラベルごとの表示/非表示切り替え
- ラベル固有の属性追加（信頼度、メタデータなど）