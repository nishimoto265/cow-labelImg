# Undo/Redo機能 要件定義書（統一履歴管理版）

## 概要
labelImgアプリケーションに統一的なUndo/Redo機能を実装する。全ての操作を一貫した方法で管理し、ユーザーが直感的に操作を取り消し・やり直しできるようにする。

## 機能要件

### 1. 基本機能
- **Undo (Ctrl+Z)**: 直前の操作を取り消す
- **Redo (Ctrl+Y)**: 取り消した操作をやり直す  
- **履歴管理**: 最大50操作まで履歴を保持

### 2. 対象操作
以下の全ての操作をUndo/Redo対象とする：

#### 2.1 単一フレーム操作
- **BB作成**: 新しいBounding Boxの作成
- **BB削除**: 選択したBounding Boxの削除
- **BB編集**: Bounding Boxの位置・サイズ変更
- **ラベル変更**: Bounding Boxのラベル変更
- **BB複製**: 同一フレーム内でのBB複製

#### 2.2 複数フレーム操作
- **BB複製（複数フレーム）**: 後続フレームへのBB複製
- **連続トラッキング**: 複数フレームにわたるID付与
- **一括削除**: 複数フレームからの同一ID削除
- **一括ラベル変更**: 複数フレームでの同一IDラベル変更

### 3. 状態管理
- **状態の定義**: 各フレームのBounding Box情報（位置、ラベル、ID等）
- **状態の保存タイミング**: 操作実行直後
- **フレーム切り替え時**: 各フレームで独立した履歴を管理

## 技術設計

### 1. アーキテクチャ
**Memento Pattern**と**統一履歴管理**を採用し、すべての操作を時系列で一元管理する。

```python
class FrameUndoManager:
    def __init__(self, max_history_per_frame=30):
        # フレーム別履歴（既存機能との互換性）
        self.frame_managers = {}  
        
        # 統一履歴管理（新機能）
        self.unified_history = []  # すべての操作を時系列で管理
        self.unified_index = -1    # 現在の履歴インデックス
        self.max_unified_history = 50
        
    def save_state(self, state_data, operation_type):
        # フレーム履歴とグローバル履歴の両方に保存
        
    def undo(self):
        # 統一履歴から最新の操作を取り消す
        
    def redo(self):
        # 統一履歴から次の操作を再実行
```

### 2. 統一履歴データ構造
```python
# 単一フレーム操作
{
    'type': 'single_frame',
    'frame_path': str,           # 対象フレーム
    'operation_type': str,       # 'add_shape', 'delete_shape'等
    'timestamp': float           # 操作時刻
}

# 複数フレーム操作
{
    'type': 'multi_frame',
    'operation': MultiFrameOperation,  # BB複製等の詳細情報
    'operation_type': str,       # 'bb_duplication'等
    'timestamp': float           # 操作時刻
}

# フレーム状態データ
{
    'frame_index': int,
    'file_path': str,
    'shapes': [                  # BBリスト
        {
            'points': [(x,y), ...],
            'label': str,
            'track_id': int,
            'difficult': bool,
            'attributes': {}
        }
    ]
}
```

### 3. 実装方針
1. **統一履歴管理**: 単一・複数フレーム操作を時系列で一元管理
2. **操作タイプの分離**: 各操作タイプに応じた適切なUndo/Redo処理
3. **Deep Copy**: 状態保存時は完全なコピーを作成
4. **メモリ管理**: 履歴サイズを制限してメモリ使用量を抑制
5. **後方互換性**: 既存のフレーム別履歴も維持

## 実装計画

### Phase 1: 統一履歴管理の導入 ✅
1. FrameUndoManagerクラスの拡張
2. 統一履歴（unified_history）の実装
3. 時系列での操作管理

### Phase 2: 統一Undo/Redoの実装 ✅
1. undo_action/redo_actionの統一化
2. 単一・複数フレーム操作の判別処理
3. 適切な復元処理の実装

### Phase 3: テストと最適化
1. 操作シーケンスの動作確認
2. エッジケースの処理
3. パフォーマンス最適化

## 注意事項
- ファイル保存時は履歴をクリアしない
- フレーム切り替え時は各フレームの履歴を保持
- 自動保存との競合を避ける実装
- エラー時は安全側に倒す（データ損失を防ぐ）
- **統一履歴**: 単一・複数フレーム操作を時系列で管理
- **後方互換性**: 既存のフレーム別履歴機能も維持

## 成功基準
- **直感的なUndo動作**: Ctrl+Zで常に最新の操作が取り消される
- **混在操作の正しい処理**: BB複製後の通常BB作成→Ctrl+Zで通常BBのみ消える
- **全操作のサポート**: 単一・複数フレーム操作すべてがUndo/Redo可能
- **パフォーマンス**: 遅延なく動作
- **データ整合性**: バグやデータ損失がない

## 修正内容（2024年版）

### 問題の解決
✅ **統一履歴管理の導入**: 単一・複数フレーム操作を時系列で一元管理
✅ **優先度問題の解決**: Multi-frame undoが不適切に優先される問題を修正
✅ **直感的な動作**: 最新の操作から順番にUndo/Redoされる

### 技術的変更点
- `unified_history`配列による時系列管理
- `can_undo_multi_frame()`の非推奨化
- `undo_action()`の統一化処理
- タイムスタンプベースの操作順序管理