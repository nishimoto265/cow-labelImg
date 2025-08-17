#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick ID Selector - フローティングID選択ウィンドウ
動物のIDを素早く切り替えるためのフローティングツールバー
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QKeyEvent


class QuickIDSelector(QDialog):
    """
    フローティングID選択ウィンドウ
    - 半透明表示
    - ボタンクリックまたはキーボードでID選択
    - クラス名表示対応
    """
    
    # Constants
    DEFAULT_ID = "1"
    MAX_COLUMNS = 4
    BUTTON_MIN_WIDTH = 70
    BUTTON_MIN_HEIGHT = 35
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 220
    WINDOW_MIN_WIDTH = 320
    WINDOW_MIN_HEIGHT = 180
    
    # Styles
    SELECTED_BUTTON_STYLE = """
        background-color: rgba(0, 120, 255, 200);
        border: 2px solid #0066cc;
        color: white;
        font-weight: bold;
    """
    
    DIALOG_STYLE = """
        QDialog {
            background-color: rgba(240, 240, 240, 230);
            border: 2px solid #666;
            border-radius: 8px;
        }
        
        #idButton {
            background-color: rgba(255, 255, 255, 200);
            border: 2px solid #ddd;
            border-radius: 4px;
            font-weight: bold;
            color: #333;
        }
        
        #idButton:hover {
            background-color: rgba(200, 220, 255, 200);
            border-color: #aaa;
        }
        
        #idButton:pressed {
            background-color: rgba(150, 200, 255, 200);
        }
    """
    
    # Signals
    id_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, max_ids=30):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            max_ids: 最大ID数
        """
        super().__init__(parent)
        
        self.parent_window = parent
        self.max_ids = max_ids
        self.current_id = self.DEFAULT_ID
        self.id_buttons = {}
        self.class_names = self._get_class_names()
        
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
    
    def _get_class_names(self):
        """親ウィンドウからクラス名リストを取得"""
        if self.parent_window and hasattr(self.parent_window, 'label_hist'):
            return self.parent_window.label_hist[:self.max_ids]
        return []
    
    def _setup_window(self):
        """ウィンドウの基本設定"""
        self.setWindowTitle("クイックID選択")
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        
        # サイズ設定
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setMinimumSize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)
    
    def _setup_ui(self):
        """UIコンポーネントの構築"""
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)
        
        # ID選択ボタングリッド
        id_grid = self._create_id_grid()
        main_layout.addLayout(id_grid)
        
        self.setLayout(main_layout)
        
        # 初期選択状態を設定
        self._update_button_states()
    
    def _create_id_grid(self):
        """ID選択ボタングリッドを作成"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)
        
        # ボタン作成範囲を決定
        button_count = min(self.max_ids, max(len(self.class_names), 1))
        
        for i in range(1, button_count + 1):
            button = self._create_id_button(i)
            row, col = self._calculate_grid_position(i)
            grid_layout.addWidget(button, row, col)
        
        return grid_layout
    
    def _create_id_button(self, index):
        """
        IDボタンを作成
        
        Args:
            index: ボタンのインデックス（1から始まる）
            
        Returns:
            作成されたボタン
        """
        id_str = str(index)
        
        # ボタンテキストとツールチップを設定
        if index <= len(self.class_names):
            class_name = self.class_names[index - 1]
            button_text = class_name
            tooltip = self._create_tooltip(id_str, class_name, index)
        else:
            button_text = id_str
            tooltip = self._create_tooltip(id_str, None, index)
        
        # ボタン作成
        button = QPushButton(button_text)
        button.setObjectName("idButton")
        button.setMinimumSize(self.BUTTON_MIN_WIDTH, self.BUTTON_MIN_HEIGHT)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        
        # クリックイベント接続
        button.clicked.connect(lambda checked, id_val=id_str: self.select_id(id_val))
        
        # ボタンを辞書に保存
        self.id_buttons[id_str] = button
        
        return button
    
    def _create_tooltip(self, id_str, class_name, index):
        """ツールチップテキストを生成"""
        if class_name:
            base_text = f"ID {id_str}: {class_name}"
        else:
            base_text = f"ID {id_str}"
        
        # キーボードショートカットを追加（1-9のみ）
        if index <= 9:
            return f"{base_text} (キー: {index})"
        return base_text
    
    def _calculate_grid_position(self, index):
        """グリッド内の位置を計算"""
        row = (index - 1) // self.MAX_COLUMNS
        col = (index - 1) % self.MAX_COLUMNS
        return row, col
    
    def _apply_styles(self):
        """スタイルシートを適用"""
        self.setStyleSheet(self.DIALOG_STYLE)
    
    def _update_button_states(self):
        """全ボタンの表示状態を更新"""
        for id_str, button in self.id_buttons.items():
            if id_str == self.current_id:
                # 選択中のボタンをハイライト
                button.setStyleSheet(f"#idButton {{ {self.SELECTED_BUTTON_STYLE} }}")
            else:
                # 通常状態に戻す
                button.setStyleSheet("")
    
    def select_id(self, id_str):
        """
        IDを選択して信号を発信
        
        Args:
            id_str: 選択するID文字列
        """
        if id_str != self.current_id and id_str in self.id_buttons:
            self.current_id = id_str
            self._update_button_states()
            self.id_selected.emit(id_str)
    
    def set_current_id(self, id_str):
        """
        外部からIDを設定（信号は発信しない）
        
        Args:
            id_str: 設定するID文字列
        """
        if id_str in self.id_buttons and id_str != self.current_id:
            self.current_id = id_str
            self._update_button_states()
    
    def get_current_id(self):
        """現在選択中のIDを取得"""
        return self.current_id
    
    def next_id(self):
        """次のIDに切り替え"""
        try:
            current_num = int(self.current_id)
            next_num = current_num + 1 if current_num < self.max_ids else 1
            self.select_id(str(next_num))
        except ValueError:
            # 数値でないIDの場合は無視
            pass
    
    def prev_id(self):
        """前のIDに切り替え"""
        try:
            current_num = int(self.current_id)
            prev_num = current_num - 1 if current_num > 1 else self.max_ids
            self.select_id(str(prev_num))
        except ValueError:
            # 数値でないIDの場合は無視
            pass
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        キーボードイベント処理
        
        Args:
            event: キーイベント
        """
        key = event.key()
        
        # 数字キー（1-9）でID選択
        if Qt.Key_1 <= key <= Qt.Key_9:
            id_num = key - Qt.Key_0
            if id_num <= self.max_ids:
                self.select_id(str(id_num))
                return
        
        # 0キーで10を選択
        elif key == Qt.Key_0:
            if 10 <= self.max_ids:
                self.select_id("10")
                return
        
        # Escapeで閉じる
        elif key == Qt.Key_Escape:
            self.hide()
            return
        
        super().keyPressEvent(event)
    
    def showEvent(self, event):
        """
        ウィンドウ表示時の処理
        
        Args:
            event: 表示イベント
        """
        super().showEvent(event)
        
        # 親ウィンドウの中央上部に配置
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100
            self.move(x, y)