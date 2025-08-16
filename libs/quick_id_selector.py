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
        
        # ドラッグ用の変数
        self.dragging = False
        self.drag_position = QPoint()
        
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("クイックID選択")
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # タイトルラベル
        title_label = QLabel("クイックID選択")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 閉じるボタン
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # ID選択エリア
        self.create_id_selection_area(main_layout)
        
        # コントロールエリア
        self.create_control_area(main_layout)
        
        self.setLayout(main_layout)
        
        # 初期サイズ設定
        self.setFixedSize(280, 320)
        
    def create_id_selection_area(self, parent_layout):
        """ID選択ボタンエリアの作成"""
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setObjectName("idScrollArea")
        
        # ID選択ウィジェット
        id_widget = QWidget()
        id_layout = QGridLayout()
        id_layout.setSpacing(2)
        id_widget.setLayout(id_layout)
        
        # IDボタンを作成（5列のグリッド）
        cols = 5
        for i in range(1, self.max_ids + 1):
            id_str = str(i)
            row = (i - 1) // cols
            col = (i - 1) % cols
            
            btn = QPushButton(id_str)
            btn.setFixedSize(45, 30)
            btn.setObjectName("idButton")
            btn.clicked.connect(lambda checked, id_val=id_str: self.select_id(id_val))
            
            # ツールチップにクラス名を表示
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
        
        scroll_area.setWidget(id_widget)
        parent_layout.addWidget(scroll_area)
        
        # 初期選択状態を設定
        self.update_button_states()
        
    def create_control_area(self, parent_layout):
        """コントロールエリアの作成"""
        control_layout = QVBoxLayout()
        control_layout.setSpacing(4)
        
        # 現在のID表示
        current_id_layout = QHBoxLayout()
        current_id_layout.addWidget(QLabel("現在のID:"))
        
        self.current_id_label = QLabel(self.current_id)
        self.current_id_label.setObjectName("currentIdLabel")
        current_id_layout.addWidget(self.current_id_label)
        current_id_layout.addStretch()
        
        control_layout.addLayout(current_id_layout)
        
        # 操作説明
        help_layout = QVBoxLayout()
        help_text = QLabel(
            "操作:\n"
            "• 1-9キー: 直接ID選択\n"
            "• Shift+ホイール: ID切り替え\n"
            "• F1: 表示/非表示\n"
            "• ドラッグ: ウィンドウ移動"
        )
        help_text.setObjectName("helpText")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        
        control_layout.addLayout(help_layout)
        
        parent_layout.addLayout(control_layout)
        
    def setup_styles(self):
        """スタイルシートの設定"""
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(240, 240, 240, 230);
                border: 2px solid #666;
                border-radius: 8px;
            }
            
            #titleLabel {
                font-weight: bold;
                font-size: 12px;
                color: #333;
                padding: 2px;
            }
            
            #closeButton {
                background-color: #ff5555;
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            
            #closeButton:hover {
                background-color: #ff3333;
            }
            
            #idScrollArea {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #ccc;
                border-radius: 4px;
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
            
            #currentIdLabel {
                font-weight: bold;
                font-size: 14px;
                color: #0066cc;
                padding: 2px 8px;
                background-color: rgba(255, 255, 255, 150);
                border: 1px solid #0066cc;
                border-radius: 4px;
            }
            
            #helpText {
                font-size: 10px;
                color: #666;
                background-color: rgba(255, 255, 255, 100);
                padding: 4px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        
    def select_id(self, id_str):
        """IDを選択"""
        if id_str != self.current_id:
            self.current_id = id_str
            self.current_id_label.setText(id_str)
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
        """外部からIDを設定"""
        if id_str in self.id_buttons:
            self.select_id(id_str)
            
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
        
    def mousePressEvent(self, event):
        """マウス押下でドラッグ開始"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """ドラッグ中の移動"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """ドラッグ終了"""
        self.dragging = False
        
    def showEvent(self, event):
        """表示時の処理"""
        super().showEvent(event)
        # 親ウィンドウの中央に配置
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100  # 少し上の方に表示
            self.move(x, y)