# Undo/Redo System

## 概要

Undo/Redo Systemは、Command Patternを使用してアノテーション操作の取り消しとやり直しを実現するシステムです。全ての編集操作を記録し、複数フレームにまたがる操作も一括で管理します。

## 仕様

### 基本動作
- Ctrl+Z: 直前の操作を取り消し
- Ctrl+Y: 取り消した操作をやり直し
- 操作履歴をスタックで管理
- 複数フレーム操作を単一コマンドとして扱う

### 対応操作
1. Bounding Box作成/削除
2. ラベル変更
3. BB複製（複数フレーム）
4. 連続ID付与（複数フレーム）
5. 形状の移動/リサイズ

### Command Pattern実装
- 各操作をCommandオブジェクトとして記録
- execute(): 操作の実行
- undo(): 操作の取り消し
- redo(): 操作の再実行

## 実装詳細

### ファイル構成
```
libs/undo/
├── __init__.py
├── undo_manager.py              # UndoManagerクラス
└── commands/
    ├── __init__.py
    ├── base_command.py           # 基底クラス
    ├── shape_commands.py         # 形状操作コマンド
    ├── label_commands.py         # ラベル変更コマンド
    ├── bb_duplication_commands.py # BB複製コマンド
    └── composite_command.py     # 複合コマンド
```

### 主要クラス

#### UndoManager
```python
class UndoManager: (libs/undo/undo_manager.py:4-77)
    def __init__(self): (lines 5-8)
        self.undo_stack = []  # 実行済みコマンド
        self.redo_stack = []  # 取り消したコマンド
    
    def execute_command(command): (lines 10-27)
        # コマンド実行と記録
    
    def undo(): (lines 29-45)
        # 直前の操作を取り消し
    
    def redo(): (lines 47-63)
        # 取り消した操作を再実行
```

#### Command基底クラス
```python
class Command(ABC): (libs/undo/commands/base_command.py:3-17)
    @abstractmethod
    def execute(self): (lines 6-8)
        pass
    
    @abstractmethod
    def undo(self): (lines 10-12)
        pass
    
    def redo(self): (lines 14-17)
        return self.execute()
```

### コマンドタイプ

#### AddShapeCommand (libs/undo/commands/shape_commands.py:5-61)
- Bounding Box新規作成
- 形状データとフレーム情報を保持
- undoで形状を削除

#### RemoveShapeCommand (libs/undo/commands/shape_commands.py:63-115)
- Bounding Box削除
- 削除した形状データを保持
- undoで形状を復元

#### ChangeLabelCommand (libs/undo/commands/label_commands.py:9-181)
- ラベル変更
- 新旧ラベルを保持
- direct_file_editオプションで直接ファイル編集

#### AddShapeWithIOUCheckCommand (libs/undo/commands/bb_duplication_commands.py:7-125)
- BB複製時のIOU判定付き追加
- 重複検出と上書き処理
- 削除した形状の復元機能

#### CompositeCommand (libs/undo/commands/composite_command.py:5-35)
- 複数のコマンドを一括管理
- 単一操作として扱う
- 逆順でundoを実行

## 使用方法

### 基本的な使用
1. 任意の編集操作を実行
2. Ctrl+Zで取り消し
3. Ctrl+Yでやり直し

### 複数フレーム操作
- BB複製やID伝播は自動的にCompositeCommandで管理
- 1回のundoで全操作を取り消し

## 技術詳細

### 直接ファイル編集
- フレーム移動せずにアノテーションファイルを編集
- YOLO形式とPascal VOC形式に対応
- パフォーマンス向上とUI更新の最小化

### メモリ管理
- 最大履歴数: 100操作（設定可能）
- 古い履歴から自動削除
- メモリ使用量の最適化

### エラー処理
- ファイル読み込みエラー時は操作をスキップ
- 不整合が発生した場合は履歴をクリア
- デバッグログで問題追跡

## 設定項目

### 設定可能な項目
- max_undo_stack_size: 最大履歴数（デフォルト: 100）
- enable_debug_logging: デバッグログ出力（デフォルト: True）

### キーボードショートカット
- Ctrl+Z: Undo
- Ctrl+Y: Redo
- Ctrl+Shift+Z: Redo（代替）

## 制限事項

1. ファイル切り替え時に履歴はクリアされる
2. 画像サイズ変更は記録されない
3. 設定変更は記録されない
4. 外部でのファイル変更は検出できない
5. 大量の操作でメモリ使用量が増加する可能性