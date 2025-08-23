#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick ID Selector - フローティングID選択ウィンドウ
動物のIDを素早く切り替えるためのフローティングツールバー
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QSizePolicy,
    QLabel, QWidget, QFrame, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QKeyEvent


class QuickIDSelector(QDialog):
    """
    フローティングID選択ウィンドウ
    - 半透明表示
    - ボタンクリックまたはキーボードでID選択
    - クラス名表示対応
    - デュアルラベル対応（Label1/Label2切り替え）
    """
    
    # Constants
    DEFAULT_ID = "1"
    MAX_COLUMNS = 4
    BUTTON_MIN_WIDTH = 70
    BUTTON_MIN_HEIGHT = 35
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 350
    WINDOW_MIN_WIDTH = 320
    WINDOW_MIN_HEIGHT = 300
    
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
    label1_selected = pyqtSignal(str)
    label2_selected = pyqtSignal(str)
    
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
        self.current_label1 = self.DEFAULT_ID
        self.current_label2 = "ID-001"
        self.id_buttons = {}
        self.label1_buttons = {}
        self.label2_buttons = {}
        self.class_names = self._get_class_names()
        self.class_names1 = self._get_class_names1()
        self.class_names2 = self._get_class_names2()
        self.current_tab = 0  # 0: Label1, 1: Label2
        
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
    
    def _get_class_names(self):
        """親ウィンドウからクラス名リストを取得"""
        if self.parent_window and hasattr(self.parent_window, 'label_hist'):
            return self.parent_window.label_hist[:self.max_ids]
        return []
    
    def _get_class_names1(self):
        """親ウィンドウからLabel1用クラス名リストを取得"""
        if self.parent_window and hasattr(self.parent_window, 'label1_hist'):
            return self.parent_window.label1_hist[:self.max_ids]
        return self._get_class_names()
    
    def _get_class_names2(self):
        """親ウィンドウからLabel2用クラス名リストを取得"""
        if self.parent_window and hasattr(self.parent_window, 'label2_hist'):
            return self.parent_window.label2_hist[:self.max_ids]
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
        
        # 不足ラベル表示エリア
        self.missing_labels_widget = self._create_missing_labels_widget()
        main_layout.addWidget(self.missing_labels_widget)
        
        # 区切り線
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # タブウィジェット for Label1/Label2
        self.tab_widget = QTabWidget()
        
        # Label1タブ
        label1_widget = QWidget()
        label1_layout = QVBoxLayout()
        label1_grid = self._create_id_grid_for_label1()
        label1_layout.addLayout(label1_grid)
        label1_widget.setLayout(label1_layout)
        self.tab_widget.addTab(label1_widget, "Label 1")
        
        # Label2タブ
        label2_widget = QWidget()
        label2_layout = QVBoxLayout()
        label2_grid = self._create_id_grid_for_label2()
        label2_layout.addLayout(label2_grid)
        label2_widget.setLayout(label2_layout)
        self.tab_widget.addTab(label2_widget, "Label 2")
        
        # タブ切り替えシグナル
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        
        # 初期選択状態を設定
        self._update_button_states()
    
    def _create_missing_labels_widget(self):
        """不足ラベル・重複ラベル表示ウィジェットを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 不足ラベル
        missing_title = QLabel("不足ラベル:")
        missing_title.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(missing_title)
        
        self.missing_labels_text = QLabel("なし")
        self.missing_labels_text.setWordWrap(True)
        self.missing_labels_text.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 200, 180);
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                color: #333;
                min-height: 25px;
            }
        """)
        layout.addWidget(self.missing_labels_text)
        
        # 重複ラベル
        duplicate_title = QLabel("重複ラベル:")
        duplicate_title.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(duplicate_title)
        
        self.duplicate_labels_text = QLabel("なし")
        self.duplicate_labels_text.setWordWrap(True)
        self.duplicate_labels_text.setStyleSheet("""
            QLabel {
                background-color: rgba(200, 200, 255, 180);
                border: 1px solid #aac;
                border-radius: 4px;
                padding: 4px;
                color: #333;
                min-height: 25px;
            }
        """)
        layout.addWidget(self.duplicate_labels_text)
        
        widget.setLayout(layout)
        return widget
    
    def _create_id_grid_for_label1(self):
        """Label1用ID選択ボタングリッドを作成"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)
        
        # ボタン作成範囲を決定
        button_count = min(self.max_ids, max(len(self.class_names1), 1))
        
        for i in range(button_count):
            button = self._create_label1_button(i)
            row, col = self._calculate_grid_position(i + 1)
            grid_layout.addWidget(button, row, col)
        
        return grid_layout
    
    def _create_id_grid_for_label2(self):
        """Label2用ID選択ボタングリッドを作成"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)
        
        # ボタン作成範囲を決定
        button_count = min(self.max_ids, max(len(self.class_names2), 1))
        
        for i in range(button_count):
            button = self._create_label2_button(i)
            row, col = self._calculate_grid_position(i + 1)
            grid_layout.addWidget(button, row, col)
        
        return grid_layout
    
    def _create_label1_button(self, index):
        """
        Label1用ボタンを作成
        
        Args:
            index: ボタンのインデックス（0から始まる）
            
        Returns:
            作成されたボタン
        """
        if index < len(self.class_names1):
            class_name = self.class_names1[index]
            button_text = class_name
            tooltip = self._create_tooltip(str(index + 1), class_name, index + 1)
        else:
            button_text = str(index + 1)
            class_name = button_text
            tooltip = self._create_tooltip(str(index + 1), None, index + 1)
        
        # ボタン作成
        button = QPushButton(button_text)
        button.setObjectName("idButton")
        button.setMinimumSize(self.BUTTON_MIN_WIDTH, self.BUTTON_MIN_HEIGHT)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        
        # クリックイベント接続
        button.clicked.connect(lambda checked, cn=class_name: self.select_label1(cn))
        
        # ボタンを辞書に保存
        self.label1_buttons[class_name] = button
        
        return button
    
    def _create_label2_button(self, index):
        """
        Label2用ボタンを作成
        
        Args:
            index: ボタンのインデックス（0から始まる）
            
        Returns:
            作成されたボタン
        """
        if index < len(self.class_names2):
            class_name = self.class_names2[index]
            button_text = class_name
            tooltip = self._create_tooltip(str(index + 1), class_name, index + 1)
        else:
            button_text = f"ID-{index + 1:03d}"
            class_name = button_text
            tooltip = self._create_tooltip(str(index + 1), None, index + 1)
        
        # ボタン作成
        button = QPushButton(button_text)
        button.setObjectName("idButton")
        button.setMinimumSize(self.BUTTON_MIN_WIDTH, self.BUTTON_MIN_HEIGHT)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        
        # クリックイベント接続
        button.clicked.connect(lambda checked, cn=class_name: self.select_label2(cn))
        
        # ボタンを辞書に保存
        self.label2_buttons[class_name] = button
        
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
        # Label1ボタンの状態更新
        for class_name, button in self.label1_buttons.items():
            if class_name == self.current_label1:
                button.setStyleSheet(f"#idButton {{ {self.SELECTED_BUTTON_STYLE} }}")
            else:
                button.setStyleSheet("")
        
        # Label2ボタンの状態更新
        for class_name, button in self.label2_buttons.items():
            if class_name == self.current_label2:
                button.setStyleSheet(f"#idButton {{ {self.SELECTED_BUTTON_STYLE} }}")
            else:
                button.setStyleSheet("")
    
    def select_label1(self, class_name):
        """
        Label1を選択して信号を発信
        
        Args:
            class_name: 選択するクラス名
        """
        if class_name != self.current_label1 and class_name in self.label1_buttons:
            self.current_label1 = class_name
            self._update_button_states()
            self.label1_selected.emit(class_name)
            print(f"[QuickID] Label1 選択: {class_name}")
    
    def select_label2(self, class_name):
        """
        Label2を選択して信号を発信
        
        Args:
            class_name: 選択するクラス名
        """
        if class_name != self.current_label2 and class_name in self.label2_buttons:
            self.current_label2 = class_name
            self._update_button_states()
            self.label2_selected.emit(class_name)
            print(f"[QuickID] Label2 選択: {class_name}")
    
    def _on_tab_changed(self, index):
        """タブが切り替わった時の処理"""
        self.current_tab = index
        self._update_button_states()
    
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
    
    def update_missing_labels(self, current_frame_labels=None):
        """
        不足ラベルと重複ラベルを更新
        
        Args:
            current_frame_labels: 現在のフレームに存在するラベルのリスト
        """
        if not self.class_names:
            self.missing_labels_text.setText("クラス定義なし")
            self.duplicate_labels_text.setText("なし")
            return
        
        if current_frame_labels is None:
            # 親ウィンドウから現在のフレームのラベルを取得
            current_frame_labels = self._get_current_frame_labels()
        
        # 不足しているラベルを検出
        existing_labels = set(current_frame_labels) if current_frame_labels else set()
        all_labels = set(self.class_names)
        missing_labels = all_labels - existing_labels
        
        # 不足ラベルの表示
        if missing_labels:
            # 不足ラベルをソートして表示（ラベル名のみ）
            sorted_missing = sorted(missing_labels, key=lambda x: self.class_names.index(x))
            display_text = ", ".join(sorted_missing)
            self.missing_labels_text.setText(display_text)
            self.missing_labels_text.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 220, 200, 180);
                    border: 1px solid #f88;
                    border-radius: 4px;
                    padding: 4px;
                    color: #800;
                    min-height: 25px;
                }
            """)
        else:
            self.missing_labels_text.setText("すべて存在")
            self.missing_labels_text.setStyleSheet("""
                QLabel {
                    background-color: rgba(200, 255, 200, 180);
                    border: 1px solid #8f8;
                    border-radius: 4px;
                    padding: 4px;
                    color: #080;
                    min-height: 25px;
                }
            """)
        
        # 重複しているラベルを検出
        from collections import Counter
        label_counts = Counter(current_frame_labels) if current_frame_labels else Counter()
        duplicate_labels = {label: count for label, count in label_counts.items() if count > 1}
        
        # 重複ラベルの表示
        if duplicate_labels:
            # 重複ラベルを表示（ラベル名と個数）
            duplicate_items = []
            for label, count in sorted(duplicate_labels.items()):
                duplicate_items.append(f"{label}({count})")
            display_text = ", ".join(duplicate_items)
            self.duplicate_labels_text.setText(display_text)
            self.duplicate_labels_text.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 200, 200, 180);
                    border: 1px solid #f66;
                    border-radius: 4px;
                    padding: 4px;
                    color: #800;
                    min-height: 25px;
                    font-weight: bold;
                }
            """)
        else:
            self.duplicate_labels_text.setText("なし")
            self.duplicate_labels_text.setStyleSheet("""
                QLabel {
                    background-color: rgba(200, 200, 255, 180);
                    border: 1px solid #aac;
                    border-radius: 4px;
                    padding: 4px;
                    color: #333;
                    min-height: 25px;
                }
            """)
    
    def _get_current_frame_labels(self):
        """親ウィンドウから現在のフレームのラベルを取得"""
        if self.parent_window and hasattr(self.parent_window, 'canvas'):
            canvas = self.parent_window.canvas
            if hasattr(canvas, 'shapes'):
                return [shape.label for shape in canvas.shapes if shape.label]
        return []
    
    def showEvent(self, event):
        """
        ウィンドウ表示時の処理
        
        Args:
            event: 表示イベント
        """
        super().showEvent(event)
        
        # 不足ラベルを更新
        self.update_missing_labels()
        
        # 親ウィンドウの中央上部に配置
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100
            self.move(x, y)