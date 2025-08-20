# cow-labelImg Undo/Redo機能 詳細要件定義書

## 1. 概要

### 1.1 目的
cow-labelImgアプリケーションに対して、すべての編集操作を取り消し・やり直しできる統一的なUndo/Redo機能を実装する。

### 1.2 基本方針
- **Command Pattern**を採用し、すべての操作をCommandオブジェクトとして実装
- 単一フレーム操作と複数フレーム操作を統一的に扱う
- 将来の機能拡張に柔軟に対応できる設計とする

### 1.3 スコープ
- ✅ アノテーション編集操作（BB作成、削除、移動、ラベル変更等）
- ✅ 複数フレームにまたがる操作（BB複製、ラベル伝播等）
- ❌ ファイル操作（開く、保存等）は対象外
- ❌ UI設定変更（表示オプション等）は対象外

## 2. 機能要件

### 2.1 基本機能

#### 2.1.1 Undo機能
- **操作**: `Ctrl+Z` または メニュー「編集」→「元に戻す」
- **動作**: 直前の操作を取り消す
- **連続実行**: 複数回実行で順次過去の操作を取り消す
- **制限**: 履歴の最初に到達したら無効化

#### 2.1.2 Redo機能
- **操作**: `Ctrl+Y` または `Ctrl+Shift+Z` または メニュー「編集」→「やり直す」
- **動作**: 取り消した操作を再実行
- **連続実行**: 複数回実行で順次やり直す
- **制限**: 最新の状態に到達したら無効化

#### 2.1.3 履歴管理
- **最大履歴数**: 100操作（設定可能）
- **メモリ管理**: 上限を超えたら古い履歴から削除
- **履歴のクリア**: 新規ファイルを開いた時
- **履歴の保持**: フレーム切り替え時は保持

### 2.2 対象操作一覧

#### 2.2.1 Shape（Bounding Box）操作

| 操作カテゴリ | 操作内容 | Command名 | 優先度 |
|------------|---------|-----------|-------|
| **作成** | BB新規作成 | `AddShapeCommand` | 高 |
| | 矩形描画によるBB作成 | `AddShapeCommand` | 高 |
| | ポリゴン描画によるBB作成 | `AddPolygonCommand` | 中 |
| **削除** | 選択BBの削除 | `DeleteShapeCommand` | 高 |
| | 複数BBの一括削除 | `DeleteMultipleShapesCommand` | 中 |
| | 全BBの削除 | `ClearShapesCommand` | 中 |
| **編集** | BB移動 | `MoveShapeCommand` | 高 |
| | BBリサイズ | `ResizeShapeCommand` | 高 |
| | BB頂点編集 | `EditVerticesCommand` | 中 |
| | BB回転 | `RotateShapeCommand` | 低 |
| **複製** | 同一フレーム内複製 | `DuplicateShapeCommand` | 中 |
| | 複数フレームへの複製 | `MultiFrameDuplicateCommand` | 高 |
| | 前フレームからコピー | `CopyFromPreviousCommand` | 中 |

#### 2.2.2 Label操作

| 操作カテゴリ | 操作内容 | Command名 | 優先度 |
|------------|---------|-----------|-------|
| **単一フレーム** | ラベル編集 | `ChangeLabelCommand` | 高 |
| | Quick ID適用 | `ApplyQuickIDCommand` | 高 |
| | デフォルトラベル適用 | `ApplyDefaultLabelCommand` | 中 |
| **複数フレーム** | ラベル伝播 | `PropagateLabelCommand` | 高 |
| | Quick ID伝播 | `PropagateQuickIDCommand` | 高 |
| | 一括ラベル変更 | `BatchChangeLabelCommand` | 中 |

#### 2.2.3 属性操作

| 操作カテゴリ | 操作内容 | Command名 | 優先度 |
|------------|---------|-----------|-------|
| **表示属性** | 線色変更 | `ChangeLineColorCommand` | 低 |
| | 塗り色変更 | `ChangeFillColorCommand` | 低 |
| | 透明度変更 | `ChangeOpacityCommand` | 低 |
| **フラグ** | Difficult設定 | `SetDifficultCommand` | 低 |
| | Verified設定 | `SetVerifiedCommand` | 低 |

### 2.3 操作の結合（Command Merging）

#### 2.3.1 マージ対象操作
- **連続移動**: 同一Shapeの連続した移動操作
- **連続リサイズ**: 同一Shapeの連続したリサイズ操作
- **連続テキスト編集**: 同一ラベルの連続した文字編集

#### 2.3.2 マージ条件
- 同一オブジェクトへの操作
- 500ms以内の連続操作
- 同じ種類のCommand

#### 2.3.3 マージ方法
```python
# 最初の状態と最後の状態のみ保持
MoveCommand(pos1→pos2) + MoveCommand(pos2→pos3) 
= MoveCommand(pos1→pos3)
```

### 2.4 UI要件

#### 2.4.1 メニュー
```
編集
├── 元に戻す (Ctrl+Z)    [動的に操作名を表示]
├── やり直す (Ctrl+Y)     [動的に操作名を表示]
├── ─────────────────
└── 履歴をクリア
```

#### 2.4.2 ツールバー
- Undoボタン（戻る矢印アイコン）
- Redoボタン（進む矢印アイコン）
- 無効時はグレーアウト

#### 2.4.3 ステータスバー
- 実行した操作を一時的に表示（3秒間）
- 例: "BBを追加しました", "ラベルを変更しました: 1→2"

#### 2.4.4 履歴パネル（オプション）
- 操作履歴のリスト表示
- 現在位置のハイライト
- クリックで特定の状態へジャンプ

## 3. 非機能要件

### 3.1 パフォーマンス
- **応答時間**: Undo/Redo実行は100ms以内
- **メモリ使用量**: 履歴100操作で最大100MB以内
- **起動時間**: Undo機能による起動時間の増加は50ms以内

### 3.2 信頼性
- **データ整合性**: Undo/Redo後もデータの整合性を保証
- **エラー処理**: 操作失敗時は安全に中断し、データを破壊しない
- **クラッシュ耐性**: アプリケーションクラッシュ後も保存済みデータは保護

### 3.3 使いやすさ
- **直感的操作**: 一般的なアプリケーションと同じ操作体系
- **視覚的フィードバック**: 操作結果を即座に反映
- **エラーメッセージ**: 分かりやすいエラー表示

### 3.4 拡張性
- **新機能対応**: 新しいCommandクラスの追加で対応
- **プラグイン対応**: 外部プラグインからもCommand登録可能
- **カスタマイズ**: 履歴数、マージ条件等を設定可能

## 4. 技術仕様

### 4.1 クラス設計

#### 4.1.1 基底クラス
```python
class Command(ABC):
    """すべてのCommandの基底クラス"""
    
    @abstractmethod
    def execute(self, app: 'MainWindow') -> bool:
        """コマンドを実行"""
        pass
    
    @abstractmethod
    def undo(self, app: 'MainWindow') -> bool:
        """コマンドを取り消し"""
        pass
    
    @abstractmethod
    def can_merge_with(self, other: 'Command') -> bool:
        """他のCommandとマージ可能か判定"""
        pass
    
    @abstractmethod
    def merge(self, other: 'Command') -> 'Command':
        """他のCommandとマージ"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """操作の説明"""
        pass
    
    @property
    @abstractmethod
    def affects_save_state(self) -> bool:
        """保存状態に影響するか"""
        pass
```

#### 4.1.2 ディレクトリ構造
```
libs/
└── undo/
    ├── __init__.py
    ├── command.py              # Command基底クラス
    ├── manager.py              # UndoManager
    ├── commands/
    │   ├── __init__.py
    │   ├── shape_commands.py   # Shape関連Command
    │   ├── label_commands.py   # Label関連Command
    │   ├── tracking_commands.py # Tracking関連Command
    │   └── composite_command.py # 複合Command
    └── tests/
        ├── test_commands.py
        └── test_manager.py
```

### 4.2 データ構造

#### 4.2.1 Command内部データ
```python
{
    # 共通フィールド
    'command_id': str,          # UUID
    'timestamp': float,         # 実行時刻
    'frame_path': str,          # 対象フレーム
    
    # Shape操作用
    'shape_data': {
        'id': str,
        'points': List[Tuple[float, float]],
        'label': str,
        'attributes': Dict
    },
    
    # 複数フレーム操作用
    'affected_frames': List[str],
    'frame_states': Dict[str, Any]
}
```

#### 4.2.2 履歴管理データ
```python
{
    'version': '1.0',
    'max_history': 100,
    'commands': List[Command],
    'current_index': int,
    'statistics': {
        'total_operations': int,
        'undo_count': int,
        'redo_count': int
    }
}
```

### 4.3 エラー処理

#### 4.3.1 エラー種別
- `CommandExecutionError`: Command実行失敗
- `UndoError`: Undo実行失敗
- `RedoError`: Redo実行失敗
- `MergeError`: Commandマージ失敗
- `HistoryCorruptedError`: 履歴データ破損

#### 4.3.2 リカバリー戦略
1. **部分的失敗**: 可能な限り実行し、失敗部分をスキップ
2. **ロールバック**: トランザクション的に全体を取り消し
3. **履歴リセット**: 復旧不可能な場合は履歴をクリア

## 5. テスト要件

### 5.1 単体テスト
- 各Commandクラスのexecute/undoメソッド
- Commandのマージ機能
- UndoManagerの履歴管理
- エラー処理

### 5.2 統合テスト
- 連続したUndo/Redo操作
- 複数フレーム操作のUndo/Redo
- フレーム切り替えを含む操作
- メモリリーク確認

### 5.3 シナリオテスト
1. **基本シナリオ**: BB作成→移動→削除→Undo×3→Redo×2
2. **複雑シナリオ**: 複数フレーム操作→単一操作→Undo→フレーム切替→Redo
3. **エラーシナリオ**: ファイル削除後のUndo、メモリ不足時の動作

### 5.4 パフォーマンステスト
- 1000回の操作後のUndo/Redo速度
- メモリ使用量の推移
- 大量Shapeでの動作

## 6. 実装計画

### Phase 1: 基盤構築（Week 1）
- [ ] Command基底クラス実装
- [ ] UndoManager実装
- [ ] 基本的なShapeCommand実装
- [ ] labelImg.pyへの統合

### Phase 2: 全Command実装（Week 2）
- [ ] 全ShapeCommand実装
- [ ] 全LabelCommand実装
- [ ] CompositeCommand実装
- [ ] マージ機能実装

### Phase 3: UI統合（Week 3）
- [ ] メニュー/ツールバー統合
- [ ] ショートカットキー設定
- [ ] ステータスバー表示
- [ ] エラーダイアログ

### Phase 4: テストと最適化（Week 4）
- [ ] 単体テスト作成
- [ ] 統合テスト実施
- [ ] パフォーマンス最適化
- [ ] ドキュメント作成

## 7. リスクと対策

### 7.1 技術的リスク
| リスク | 影響度 | 対策 |
|-------|-------|------|
| メモリ使用量増大 | 高 | 履歴数制限、データ圧縮 |
| パフォーマンス低下 | 中 | 遅延実行、バックグラウンド処理 |
| 既存コードとの競合 | 高 | 段階的移行、互換性レイヤー |

### 7.2 運用リスク
| リスク | 影響度 | 対策 |
|-------|-------|------|
| ユーザーの誤操作 | 低 | 確認ダイアログ、履歴パネル |
| データ不整合 | 高 | トランザクション処理、検証機能 |

## 8. 成功基準

### 8.1 機能面
- ✅ すべての編集操作がUndo/Redo可能
- ✅ 100操作の履歴を保持
- ✅ エラー時もデータが破壊されない

### 8.2 性能面
- ✅ Undo/Redo実行が100ms以内
- ✅ メモリ使用量が100MB以内
- ✅ 1000操作後も安定動作

### 8.3 品質面
- ✅ 単体テストカバレッジ80%以上
- ✅ 重大なバグゼロ
- ✅ ユーザビリティテスト合格

## 9. 制約事項

### 9.1 技術的制約
- Python 3.7以上
- PyQt5使用
- メモリ2GB以上推奨

### 9.2 運用上の制約
- 履歴はセッション内のみ（永続化は将来検討）
- ネットワーク共有時の同時編集は非対応

## 10. 将来の拡張

### 10.1 永続化
- 履歴のファイル保存
- セッション間での履歴共有

### 10.2 協調編集
- 複数ユーザーでの同時編集
- Operational Transformation導入

### 10.3 高度な機能
- 分岐履歴（Git的な履歴管理）
- マクロ記録/再生
- AIによる操作予測

## 付録A: Command実装例

```python
class AddShapeCommand(Command):
    """Shape追加Command実装例"""
    
    def __init__(self, frame_path: str, shape_data: Dict[str, Any]):
        self.frame_path = frame_path
        self.shape_data = shape_data
        self.shape_id = None
        self.shape_index = None
        
    def execute(self, app: 'MainWindow') -> bool:
        """Shapeを追加"""
        try:
            # フレームをロード
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Shapeを作成
            shape = Shape()
            shape.label = self.shape_data['label']
            shape.points = [QPointF(x, y) for x, y in self.shape_data['points']]
            shape.close()
            
            # Canvasに追加
            app.canvas.shapes.append(shape)
            app.add_label(shape)
            
            # 追加位置を記録
            self.shape_index = len(app.canvas.shapes) - 1
            self.shape_id = id(shape)
            
            # 更新
            app.set_dirty()
            if app.auto_saving.isChecked():
                app.save_file()
                
            return True
            
        except Exception as e:
            logging.error(f"AddShapeCommand.execute failed: {e}")
            return False
    
    def undo(self, app: 'MainWindow') -> bool:
        """Shape追加を取り消し"""
        try:
            # フレームをロード
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Shapeを削除
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                app.canvas.shapes.remove(shape)
                
                # ラベルリストからも削除
                if shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    row = app.label_list.row(item)
                    app.label_list.takeItem(row)
                    del app.shapes_to_items[shape]
                    del app.items_to_shapes[item]
            
            # 更新
            app.set_dirty()
            if app.auto_saving.isChecked():
                app.save_file()
                
            return True
            
        except Exception as e:
            logging.error(f"AddShapeCommand.undo failed: {e}")
            return False
    
    def can_merge_with(self, other: Command) -> bool:
        """マージ不可（追加操作はマージしない）"""
        return False
    
    def merge(self, other: Command) -> Command:
        """マージ非対応"""
        raise NotImplementedError
    
    @property
    def description(self) -> str:
        return f"Add shape '{self.shape_data.get('label', 'unknown')}'"
    
    @property
    def affects_save_state(self) -> bool:
        return True
```

## 付録B: 用語定義

| 用語 | 定義 |
|-----|------|
| Command | 実行可能でUndo可能な操作の単位 |
| UndoManager | Command履歴を管理するクラス |
| CompositeCommand | 複数のCommandをまとめた複合Command |
| マージ | 連続した同種操作を1つにまとめること |
| 履歴 | 実行されたCommandのリスト |
| current_index | 履歴内の現在位置 |