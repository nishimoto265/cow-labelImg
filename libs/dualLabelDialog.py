#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dual Label Dialog - 2つのラベルを入力するためのダイアログ
"""

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import new_icon, label_validator, trimmed

BB = QDialogButtonBox


class DualLabelDialog(QDialog):
    """2つのラベルを入力するためのダイアログ"""
    
    def __init__(self, label1="", label2="", parent=None, list_item1=None, list_item2=None):
        super(DualLabelDialog, self).__init__(parent)
        self.setWindowTitle("Dual Label Input")
        
        # ラベル1の入力フィールド
        self.label1_group = QGroupBox("Label 1 (Primary)")
        self.edit1 = QLineEdit()
        self.edit1.setText(label1)
        self.edit1.setValidator(label_validator())
        self.edit1.editingFinished.connect(self.post_process1)
        
        # ラベル1のオートコンプリート
        if list_item1:
            model1 = QStringListModel()
            model1.setStringList(list_item1)
            completer1 = QCompleter()
            completer1.setModel(model1)
            self.edit1.setCompleter(completer1)
        
        # ラベル2の入力フィールド
        self.label2_group = QGroupBox("Label 2 (Secondary)")
        self.edit2 = QLineEdit()
        self.edit2.setText(label2)
        self.edit2.setValidator(label_validator())
        self.edit2.editingFinished.connect(self.post_process2)
        
        # ラベル2のオートコンプリート
        if list_item2:
            model2 = QStringListModel()
            model2.setStringList(list_item2)
            completer2 = QCompleter()
            completer2.setModel(model2)
            self.edit2.setCompleter(completer2)
        
        # ボタン
        self.button_box = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(new_icon('done'))
        bb.button(BB.Cancel).setIcon(new_icon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        
        # レイアウト構築
        main_layout = QVBoxLayout()
        
        # ラベル1のレイアウト
        label1_layout = QVBoxLayout()
        label1_layout.addWidget(self.edit1)
        
        if list_item1 is not None and len(list_item1) > 0:
            self.list_widget1 = QListWidget(self)
            for item in list_item1:
                self.list_widget1.addItem(item)
            self.list_widget1.itemClicked.connect(self.list1_item_click)
            self.list_widget1.itemDoubleClicked.connect(self.list1_item_double_click)
            label1_layout.addWidget(self.list_widget1)
        
        self.label1_group.setLayout(label1_layout)
        
        # ラベル2のレイアウト
        label2_layout = QVBoxLayout()
        label2_layout.addWidget(self.edit2)
        
        if list_item2 is not None and len(list_item2) > 0:
            self.list_widget2 = QListWidget(self)
            for item in list_item2:
                self.list_widget2.addItem(item)
            self.list_widget2.itemClicked.connect(self.list2_item_click)
            self.list_widget2.itemDoubleClicked.connect(self.list2_item_double_click)
            label2_layout.addWidget(self.list_widget2)
        
        self.label2_group.setLayout(label2_layout)
        
        # メインレイアウトに追加
        main_layout.addWidget(bb, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.label1_group)
        main_layout.addWidget(self.label2_group)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(400)
    
    def validate(self):
        """少なくとも1つのラベルが入力されていることを確認"""
        if trimmed(self.edit1.text()) or trimmed(self.edit2.text()):
            self.accept()
    
    def post_process1(self):
        self.edit1.setText(trimmed(self.edit1.text()))
    
    def post_process2(self):
        self.edit2.setText(trimmed(self.edit2.text()))
    
    def pop_up(self, label1='', label2='', move=True):
        """
        ダイアログを表示し、2つのラベルを取得
        
        Returns:
            tuple: (label1, label2) or (None, None) if cancelled
        """
        self.edit1.setText(label1)
        self.edit1.setSelection(0, len(label1))
        self.edit2.setText(label2)
        self.edit2.setSelection(0, len(label2))
        self.edit1.setFocus(Qt.PopupFocusReason)
        
        if move:
            cursor_pos = QCursor.pos()
            
            # OK ボタンをカーソル下に移動
            btn = self.button_box.buttons()[0]
            self.adjustSize()
            btn.adjustSize()
            offset = btn.mapToGlobal(btn.pos()) - self.pos()
            offset += QPoint(btn.size().width() // 4, btn.size().height() // 2)
            cursor_pos.setX(max(0, cursor_pos.x() - offset.x()))
            cursor_pos.setY(max(0, cursor_pos.y() - offset.y()))
            
            parent_bottom_right = self.parentWidget().geometry()
            max_x = parent_bottom_right.x() + parent_bottom_right.width() - self.sizeHint().width()
            max_y = parent_bottom_right.y() + parent_bottom_right.height() - self.sizeHint().height()
            max_global = self.parentWidget().mapToGlobal(QPoint(max_x, max_y))
            if cursor_pos.x() > max_global.x():
                cursor_pos.setX(max_global.x())
            if cursor_pos.y() > max_global.y():
                cursor_pos.setY(max_global.y())
            self.move(cursor_pos)
        
        if self.exec_():
            return trimmed(self.edit1.text()), trimmed(self.edit2.text())
        else:
            return None, None
    
    def list1_item_click(self, t_qlist_widget_item):
        text = trimmed(t_qlist_widget_item.text())
        self.edit1.setText(text)
    
    def list1_item_double_click(self, t_qlist_widget_item):
        self.list1_item_click(t_qlist_widget_item)
        # Don't auto-accept on double click for label1
    
    def list2_item_click(self, t_qlist_widget_item):
        text = trimmed(t_qlist_widget_item.text())
        self.edit2.setText(text)
    
    def list2_item_double_click(self, t_qlist_widget_item):
        self.list2_item_click(t_qlist_widget_item)
        # Don't auto-accept on double click for label2