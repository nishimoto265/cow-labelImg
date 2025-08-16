#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
統一的なUndo/Redo管理システム
Memento Patternを使用したシンプルな実装
"""

import copy
import json
import time


class UndoManager:
    """
    全ての操作を統一的に管理するUndo/Redoマネージャー
    """
    
    def __init__(self, max_history=50):
        """
        Args:
            max_history: 保持する最大履歴数
        """
        self.history = []           # 状態履歴
        self.current_index = -1     # 現在の履歴インデックス
        self.max_history = max_history
        self._is_restoring = False  # 復元中フラグ（再帰防止）
    
    def save_state(self, state_data, operation_type="unknown"):
        """
        現在の状態を履歴に保存
        
        Args:
            state_data: 保存する状態データ
            operation_type: 操作タイプ（デバッグ用）
        """
        if self._is_restoring:
            return False
        
        # Redo履歴をクリア（現在位置より後の履歴を削除）
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # 状態をディープコピーして保存
        state_copy = copy.deepcopy(state_data)
        state_copy['_operation_type'] = operation_type
        
        # 履歴に追加
        self.history.append(state_copy)
        self.current_index += 1
        
        # 履歴サイズ制限
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
        
        print(f"[UndoManager] State saved: {operation_type}, History: {len(self.history)}, Index: {self.current_index}")
        return True
    
    def undo(self):
        """
        一つ前の状態に戻す
        
        Returns:
            復元する状態データ、またはNone
        """
        if not self.can_undo():
            print("[UndoManager] Cannot undo - no previous state")
            return None
        
        self.current_index -= 1
        state = copy.deepcopy(self.history[self.current_index])
        
        operation = state.get('_operation_type', 'unknown')
        print(f"[UndoManager] Undo: {operation}, Index: {self.current_index}")
        
        return state
    
    def redo(self):
        """
        一つ後の状態に進む
        
        Returns:
            復元する状態データ、またはNone
        """
        if not self.can_redo():
            print("[UndoManager] Cannot redo - no next state")
            return None
        
        self.current_index += 1
        state = copy.deepcopy(self.history[self.current_index])
        
        operation = state.get('_operation_type', 'unknown')
        print(f"[UndoManager] Redo: {operation}, Index: {self.current_index}")
        
        return state
    
    def can_undo(self):
        """Undo可能かチェック"""
        return self.current_index > 0
    
    def can_redo(self):
        """Redo可能かチェック"""
        return self.current_index < len(self.history) - 1
    
    def clear(self):
        """履歴を完全にクリア"""
        self.history = []
        self.current_index = -1
        print("[UndoManager] History cleared")
    
    def set_restoring(self, is_restoring):
        """
        復元中フラグを設定（再帰防止）
        
        Args:
            is_restoring: 復元中かどうか
        """
        self._is_restoring = is_restoring
    
    def get_current_state(self):
        """
        現在の状態を取得
        
        Returns:
            現在の状態データ、またはNone
        """
        if 0 <= self.current_index < len(self.history):
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def initialize_with_state(self, state_data):
        """
        初期状態で履歴を初期化
        
        Args:
            state_data: 初期状態データ
        """
        self.clear()
        self.save_state(state_data, "initial")
        print("[UndoManager] Initialized with initial state")
    
    def get_history_info(self):
        """
        デバッグ用：履歴情報を取得
        
        Returns:
            履歴情報の辞書
        """
        return {
            'total_states': len(self.history),
            'current_index': self.current_index,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'operations': [s.get('_operation_type', 'unknown') for s in self.history]
        }


class MultiFrameOperation:
    """
    複数フレームにまたがる操作を表すクラス
    """
    def __init__(self, operation_type, description=""):
        self.operation_type = operation_type  # 'bb_duplication', 'continuous_tracking' など
        self.description = description
        self.frame_changes = []  # [(frame_path, before_state, after_state), ...]
        self.timestamp = None
        self.source_frame = None
    
    def add_frame_change(self, frame_path, before_state, after_state):
        """フレームごとの変更を記録"""
        self.frame_changes.append({
            'frame_path': frame_path,
            'before': copy.deepcopy(before_state),
            'after': copy.deepcopy(after_state)
        })
    
    def get_affected_frames(self):
        """影響を受けたフレームのリストを返す"""
        return [change['frame_path'] for change in self.frame_changes]


class FrameUndoManager:
    """
    フレームごとに独立したUndo/Redo管理
    統一履歴管理により、単一フレーム操作と複数フレーム操作を時系列で管理
    """
    
    def __init__(self, max_history_per_frame=30):
        """
        Args:
            max_history_per_frame: 各フレームの最大履歴数
        """
        self.frame_managers = {}  # フレームパスごとのUndoManager
        self.max_history = max_history_per_frame
        self.current_frame = None
        
        # 統一履歴管理
        self.unified_history = []  # すべての操作を時系列で管理
        self.unified_index = -1    # 現在の履歴インデックス
        self.max_unified_history = 50  # 最大履歴数
    
    def get_manager(self, frame_path):
        """
        指定フレームのUndoManagerを取得（なければ作成）
        
        Args:
            frame_path: フレームのファイルパス
            
        Returns:
            UndoManager instance
        """
        if frame_path not in self.frame_managers:
            self.frame_managers[frame_path] = UndoManager(self.max_history)
        return self.frame_managers[frame_path]
    
    def set_current_frame(self, frame_path):
        """現在のフレームを設定"""
        self.current_frame = frame_path
    
    def save_state(self, state_data, operation_type="unknown"):
        """現在のフレームの状態を保存（統一履歴に追加）"""
        if self.current_frame:
            # フレーム単体の履歴に保存
            result = self.get_manager(self.current_frame).save_state(state_data, operation_type)
            
            # 統一履歴にも追加
            if result:
                self._add_to_unified_history({
                    'type': 'single_frame',
                    'frame_path': self.current_frame,
                    'operation_type': operation_type,
                    'timestamp': time.time()
                })
            
            return result
        return False
    
    def undo(self):
        """統一履歴から最新の操作をUndo"""
        if not self.can_undo():
            print("[UnifiedHistory] Cannot undo")
            return None
        
        if self.unified_index < 0 or self.unified_index >= len(self.unified_history):
            print("[UnifiedHistory] Invalid index")
            return None
        
        operation = self.unified_history[self.unified_index]
        self.unified_index -= 1
        
        print(f"[UnifiedHistory] Undoing {operation['type']} operation: {operation.get('operation_type', 'unknown')}")
        
        if operation['type'] == 'single_frame':
            # 単一フレーム操作のUndo
            frame_path = operation['frame_path']
            if frame_path and frame_path in self.frame_managers:
                manager = self.get_manager(frame_path)
                if manager.can_undo():
                    return manager.undo()
        
        elif operation['type'] == 'multi_frame':
            # 複数フレーム操作のUndo
            multi_op = operation['operation']
            return self._undo_multi_frame_internal(multi_op)
        
        return None
    
    def redo(self):
        """統一履歴から次の操作をRedo"""
        if not self.can_redo():
            print("[UnifiedHistory] Cannot redo")
            return None
        
        self.unified_index += 1
        operation = self.unified_history[self.unified_index]
        
        print(f"[UnifiedHistory] Redoing {operation['type']} operation: {operation.get('operation_type', 'unknown')}")
        
        if operation['type'] == 'single_frame':
            # 単一フレーム操作のRedo
            frame_path = operation['frame_path']
            if frame_path and frame_path in self.frame_managers:
                manager = self.get_manager(frame_path)
                if manager.can_redo():
                    return manager.redo()
        
        elif operation['type'] == 'multi_frame':
            # 複数フレーム操作のRedo
            multi_op = operation['operation']
            return self._redo_multi_frame_internal(multi_op)
        
        return None
    
    def can_undo(self):
        """統一履歴でUndo可能かチェック"""
        return self.unified_index >= 0
    
    def can_redo(self):
        """統一履歴でRedo可能かチェック"""
        return self.unified_index < len(self.unified_history) - 1

    
    # ========== Multi-frame operation methods ==========
    
    def start_multi_frame_operation(self, operation_type, description=""):
        """
        複数フレーム操作を開始
        
        Args:
            operation_type: 操作タイプ（'bb_duplication', 'continuous_tracking'など）
            description: 操作の説明
            
        Returns:
            MultiFrameOperation object
        """
        operation = MultiFrameOperation(operation_type, description)
        operation.source_frame = self.current_frame
        print(f"[MultiFrame] Starting {operation_type} operation from {self.current_frame}")
        return operation
    
    def save_multi_frame_operation(self, operation):
        """
        複数フレーム操作を履歴に保存（統一履歴に追加）
        
        Args:
            operation: MultiFrameOperation object
        """
        if not operation.frame_changes:
            print("[MultiFrame] No changes to save")
            return
        
        # 統一履歴に追加
        self._add_to_unified_history({
            'type': 'multi_frame',
            'operation': operation,
            'operation_type': operation.operation_type,
            'timestamp': time.time()
        })
        
        print(f"[MultiFrame] Saved {operation.operation_type} affecting {len(operation.frame_changes)} frames")
        print(f"[UnifiedHistory] History size: {len(self.unified_history)}, Index: {self.unified_index}")
    
    def _undo_multi_frame_internal(self, operation):
        """
        複数フレーム操作のUndo（内部処理）
        
        Args:
            operation: MultiFrameOperation object
            
        Returns:
            Undone operation or None
        """
        print(f"[MultiFrame] Undoing {operation.operation_type} affecting {len(operation.frame_changes)} frames")
        
        # 各フレームを前の状態に戻す
        for change in operation.frame_changes:
            frame_path = change['frame_path']
            before_state = change['before']
            
            # フレームのマネージャーを取得
            manager = self.get_manager(frame_path)
            # 直接履歴を操作して前の状態を設定
            manager.history.append(copy.deepcopy(before_state))
            manager.current_index = len(manager.history) - 1
            
            print(f"[MultiFrame] Restored {frame_path} to before state")
        
        return operation
    
    def _redo_multi_frame_internal(self, operation):
        """
        複数フレーム操作のRedo（内部処理）
        
        Args:
            operation: MultiFrameOperation object
            
        Returns:
            Redone operation or None
        """
        print(f"[MultiFrame] Redoing {operation.operation_type} affecting {len(operation.frame_changes)} frames")
        
        # 各フレームを後の状態に戻す
        for change in operation.frame_changes:
            frame_path = change['frame_path']
            after_state = change['after']
            
            # フレームのマネージャーを取得
            manager = self.get_manager(frame_path)
            # 直接履歴を操作して後の状態を設定
            manager.history.append(copy.deepcopy(after_state))
            manager.current_index = len(manager.history) - 1
            
            print(f"[MultiFrame] Restored {frame_path} to after state")
        
        return operation
    
    def _add_to_unified_history(self, operation_info):
        """
        統一履歴に操作を追加
        
        Args:
            operation_info: 操作情報の辞書
        """
        # Redo履歴をクリア
        if self.unified_index < len(self.unified_history) - 1:
            self.unified_history = self.unified_history[:self.unified_index + 1]
        
        # 操作を追加
        self.unified_history.append(operation_info)
        self.unified_index += 1
        
        # 履歴サイズ制限
        if len(self.unified_history) > self.max_unified_history:
            self.unified_history.pop(0)
            self.unified_index -= 1
        
        print(f"[UnifiedHistory] Added {operation_info['type']} operation, History: {len(self.unified_history)}, Index: {self.unified_index}")
    
    # 互換性のために古いメソッドを残す（deprecated）
    def can_undo_multi_frame(self):
        """複数フレーム操作のUndo可能かチェック（deprecated）"""
        # 統一履歴で管理するため、常にFalseを返す
        return False
    
    def can_redo_multi_frame(self):
        """複数フレーム操作のRedo可能かチェック（deprecated）"""
        # 統一履歴で管理するため、常にFalseを返す
        return False
    
    def undo_multi_frame(self):
        """複数フレーム操作のUndo（deprecated - 統一undoを使用）"""
        return self.undo()
    
    def redo_multi_frame(self):
        """複数フレーム操作のRedo（deprecated - 統一redoを使用）"""
        return self.redo()
