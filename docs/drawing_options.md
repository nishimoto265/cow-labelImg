# Drawing Options

## 概要

Drawing Optionsは、Bounding BoxやIDラベルの表示/非表示を制御する機能です。アノテーション作業の視認性を向上させ、必要に応じて表示要素を切り替えることができます。

## 仕様

### 表示制御対象
1. Bounding Box（矩形枠）
2. IDラベル（テキスト表示）

### 動作モード
- 独立制御: BBとIDを個別に表示/非表示
- リアルタイム更新: 設定変更即座に反映
- 全形状適用: 全てのBounding Boxに一括適用

## 使用方法

### UI操作
1. 「BB表示」チェックボックスでBounding Boxの表示切り替え
2. 「ID表示」チェックボックスでIDラベルの表示切り替え

### 表示パターン
- BB表示ON + ID表示ON: 通常表示（デフォルト）
- BB表示ON + ID表示OFF: 枠のみ表示
- BB表示OFF + ID表示ON: ラベルのみ表示
- BB表示OFF + ID表示OFF: 非表示（選択時のみ表示）

## 技術詳細

### ファイル構成
- labelImg.py - UI制御とイベント処理
- libs/shape.py - 形状クラスの表示プロパティ
- libs/canvas.py - 描画処理

### 主要メソッド
```
labelImg.py:
- toggle_bounding_box_display(state): BB表示切り替え (labelImg.py:1993-1998)
- toggle_id_display(state): ID表示切り替え (labelImg.py:1999-2003)
- update_shape_display_settings(): 全形状に設定適用 (内部処理)

shape.py:
- paint_label: ラベル表示フラグ (libs/shape.py:property)
- paint_id: ID表示フラグ（BB枠） (libs/shape.py:property)

canvas.py:
- paintEvent(): 表示フラグに基づく描画処理 (libs/canvas.py:paintEvent)
```

### 描画処理フロー
1. チェックボックスの状態変更を検出
2. 全形状オブジェクトの表示フラグを更新
3. canvas.update()で再描画をトリガー
4. paintEvent()で表示フラグに基づいて描画

### プロパティ管理
```python
class Shape:
    def __init__(self):
        self.paint_label = True  # ラベル表示
        self.paint_id = True     # BB枠表示
```

## 設定項目

### UI要素
- bb_display_checkbox: BB表示チェックボックス (labelImg.py:273-280)
- id_display_checkbox: ID表示チェックボックス (labelImg.py:281-290)

### デフォルト値
- BB表示: ON
- ID表示: ON

### 保存設定
- 表示設定はセッション間で保持されない
- 起動時は常にデフォルト値

## 制限事項

1. 選択中の形状は常に表示される（非表示設定でも）
2. 表示設定はアノテーションファイルに保存されない
3. エクスポート時は表示設定に関係なく全情報が出力
4. 大量の形状がある場合、切り替えに時間がかかる可能性
5. 表示設定の変更はUndo/Redoの対象外