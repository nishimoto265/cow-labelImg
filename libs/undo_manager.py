#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
統一的なUndo/Redo管理システム
Memento Patternを使用したシンプルな実装
"""

import copy
import json


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


class FrameUndoManager:
    """
    フレームごとに独立したUndo/Redo管理
    """
    
    def __init__(self, max_history_per_frame=30):
        """
        Args:
            max_history_per_frame: 各フレームの最大履歴数
        """
        self.frame_managers = {}  # フレームパスごとのUndoManager
        self.max_history = max_history_per_frame
        self.current_frame = None
    
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
        """現在のフレームの状態を保存"""
        if self.current_frame:
            return self.get_manager(self.current_frame).save_state(state_data, operation_type)
        return False
    
    def undo(self):
        """現在のフレームでUndo"""
        if self.current_frame:
            return self.get_manager(self.current_frame).undo()
        return None
    
    def redo(self):
        """現在のフレームでRedo"""
        if self.current_frame:
            return self.get_manager(self.current_frame).redo()
        return None
    
    def can_undo(self):
        """現在のフレームでUndo可能かチェック"""
        if self.current_frame:
            return self.get_manager(self.current_frame).can_undo()
        return False
    
    def can_redo(self):
        """現在のフレームでRedo可能かチェック"""
        if self.current_frame:
            return self.get_manager(self.current_frame).can_redo()
        return False