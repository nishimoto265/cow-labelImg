#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick ID Selector - フローティングID選択ウィンドウ
動物のIDを素早く切り替えるためのフローティングツールバー
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class QuickIDSelector(QDialog):
    """
    フローティングID選択ウィンドウ
    - ドラッグで移動可能
    - 半透明表示
    - ボタンクリックまたはキーボードでID選択
    """
    
    # シグナル定義
    id_selected = pyqtSignal(str)  # 選択されたIDを送信
    
    def __init__(self, parent=None, max_ids=30):
        super(QuickIDSelector, self).__init__(parent)
        
        self.parent_window = parent
        self.current_id = "1"  # デフォルトID
        self.max_ids = max_ids
        self.id_buttons = {}
        
        # 親ウィンドウからクラス名を取得
        self.class_names = []
        if parent and hasattr(parent, 'label_hist'):
            self.class_names = parent.label_hist[:max_ids]
        
        # スタイルを先に定義
        self.selected_style = """
            background-color: rgba(0, 120, 255, 200);
            border: 2px solid #0066cc;
            color: white;
            font-weight: bold;
        """
        
        self.init_ui()
        self.setup_styles()
        
        # リサイズ可能なウィンドウなので、ドラッグ機能は不要
        
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("クイックID選択")
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)
        
        # ID選択エリアのみ
        self.create_id_selection_area(main_layout)
        
        self.setLayout(main_layout)
        
        # 初期サイズ設定（全てのIDボタンが見えるように）
        # 20個のクラス名 ÷ 4列 = 5行、各ボタン高さ35px + スペース
        self.resize(400, 220)
        self.setMinimumSize(320, 180)
        
    def create_id_selection_area(self, parent_layout):
        """ID選択ボタンエリアの作成"""
        # 直接グリッドレイアウトを使用（スクロールエリアなし）
        id_layout = QGridLayout()
        id_layout.setSpacing(3)
        
        # IDボタンを作成（4列のグリッド）
        cols = 4
        for i in range(1, min(self.max_ids + 1, len(self.class_names) + 1)):
            id_str = str(i)
            row = (i - 1) // cols
            col = (i - 1) % cols
            
            # ボタンテキスト：クラス名のみ表示
            if i <= len(self.class_names):
                class_name = self.class_names[i - 1]
                btn_text = class_name
                btn = QPushButton(btn_text)
                # クラス名の長さに応じてサイズ調整
                btn.setMinimumSize(70, 35)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            else:
                btn_text = id_str
                btn = QPushButton(btn_text)
                btn.setMinimumSize(45, 35)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            btn.setObjectName("idButton")
            btn.clicked.connect(lambda checked, id_val=id_str: self.select_id(id_val))
            
            # ツールチップ
            if i <= len(self.class_names):
                class_name = self.class_names[i - 1]
                if i <= 9:
                    btn.setToolTip(f"ID {id_str}: {class_name} (キー: {i})")
                else:
                    btn.setToolTip(f"ID {id_str}: {class_name}")
            else:
                if i <= 9:
                    btn.setToolTip(f"ID {id_str} (キー: {i})")
                else:
                    btn.setToolTip(f"ID {id_str}")
                
            self.id_buttons[id_str] = btn
            id_layout.addWidget(btn, row, col)
        
        # グリッドレイアウトを直接メインレイアウトに追加
        parent_layout.addLayout(id_layout)
        
        # 初期選択状態を設定
        self.update_button_states()
        
        
    def setup_styles(self):
        """スタイルシートの設定"""
        self.setStyleSheet("""
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
        """)
        
    def select_id(self, id_str):
        """IDを選択"""
        if id_str != self.current_id:
            self.current_id = id_str
            self.update_button_states()
            
            # シグナルを発信
            self.id_selected.emit(id_str)
            
            print(f"[QuickIDSelector] ID selected: {id_str}")
    
    def update_button_states(self):
        """ボタンの状態を更新（選択中のIDをハイライト）"""
        for id_str, btn in self.id_buttons.items():
            if id_str == self.current_id:
                # 選択中のボタン
                btn.setStyleSheet(f"#idButton {{ {self.selected_style} }}")
            else:
                # 通常のボタン
                btn.setStyleSheet("")  # デフォルトスタイルに戻す
                
    def get_current_id(self):
        """現在選択中のIDを取得"""
        return self.current_id
        
    def set_current_id(self, id_str):
        """外部からIDを設定（シグナル発火なし）"""
        print(f"[QuickIDSelector] set_current_id called with: {id_str}")
        print(f"[QuickIDSelector] Available buttons: {list(self.id_buttons.keys())}")
        
        if id_str in self.id_buttons and id_str != self.current_id:
            self.current_id = id_str
            self.update_button_states()
            print(f"[QuickIDSelector] ID set externally: {id_str}")
        else:
            print(f"[QuickIDSelector] Cannot set ID {id_str}: not in buttons or same as current")
    
            
    def next_id(self):
        """次のIDに切り替え"""
        current_num = int(self.current_id)
        next_num = current_num + 1 if current_num < self.max_ids else 1
        self.select_id(str(next_num))
        
    def prev_id(self):
        """前のIDに切り替え"""
        current_num = int(self.current_id)
        prev_num = current_num - 1 if current_num > 1 else self.max_ids
        self.select_id(str(prev_num))
        
    def keyPressEvent(self, event):
        """キーボードイベント処理"""
        key = event.key()
        
        # 数字キー（1-9）でID直接選択
        if Qt.Key_1 <= key <= Qt.Key_9:
            id_num = key - Qt.Key_0
            if id_num <= self.max_ids:
                self.select_id(str(id_num))
                return
                
        # 0キーで10番を選択
        elif key == Qt.Key_0:
            if 10 <= self.max_ids:
                self.select_id("10")
                return
                
        # Escapeで閉じる
        elif key == Qt.Key_Escape:
            self.hide()
            return
            
        super().keyPressEvent(event)
        
    # ドラッグ機能は削除（通常のウィンドウとして動作）
        
    def showEvent(self, event):
        """表示時の処理"""
        super().showEvent(event)
        # 親ウィンドウの中央に配置
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100  # 少し上の方に表示
            self.move(x, y)