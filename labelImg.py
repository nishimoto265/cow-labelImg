#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import codecs
import os.path
import platform
import shutil
import sys
import webbrowser as wb
from functools import partial

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import QTimer
except ImportError:
    # needed for py3+qt4
    # Ref:
    # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    # http://stackoverflow.com/questions/21217399/pyqt4-qtcore-qvariant-object-instead-of-a-string
    if sys.version_info.major >= 3:
        import sip
        sip.setapi('QVariant', 2)
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
    from PyQt4.QtCore import QTimer

from libs.combobox import ComboBox
from libs.default_label_combobox import DefaultLabelComboBox
from libs.resources import *
from libs.constants import *
from libs.utils import *
from libs.settings import Settings
from libs.shape import Shape, DEFAULT_LINE_COLOR, DEFAULT_FILL_COLOR
from libs.stringBundle import StringBundle
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.lightWidget import LightWidget
from libs.labelDialog import LabelDialog
from libs.colorDialog import ColorDialog
from libs.labelFile import LabelFile, LabelFileError, LabelFileFormat
from libs.toolBar import ToolBar
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import XML_EXT
from libs.yolo_io import YoloReader
from libs.yolo_io import TXT_EXT
from libs.create_ml_io import CreateMLReader
from libs.create_ml_io import JSON_EXT
from libs.ustr import ustr
from libs.hashableQListWidgetItem import HashableQListWidgetItem
from libs.tracker import Tracker
from libs.quick_id_selector import QuickIDSelector

__appname__ = 'labelImg'


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            add_actions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            add_actions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar


class MainWindow(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    def __init__(self, default_filename=None, default_prefdef_class_file=None, default_save_dir=None):
        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        # Load setting in the main thread
        self.settings = Settings()
        self.settings.load()
        settings = self.settings

        self.os_name = platform.system()

        # Load string bundle for i18n
        self.string_bundle = StringBundle.get_bundle()
        get_str = lambda str_id: self.string_bundle.get_string(str_id)

        # Save as Pascal voc xml
        self.default_save_dir = default_save_dir
        self.label_file_format = settings.get(SETTING_LABEL_FILE_FORMAT, LabelFileFormat.PASCAL_VOC)

        # For loading all image under a directory
        self.m_img_list = []
        self.dir_name = None
        self.label_hist = []
        self.last_open_dir = None
        self.cur_img_idx = 0
        self.img_count = len(self.m_img_list)

        # Whether we need to save or not.
        self.dirty = False

        self._no_selection_slot = False
        self._beginner = True
        self.screencast = "https://youtu.be/p0nR2YsCY_U"

        # Load predefined classes to the list
        self.load_predefined_classes(default_prefdef_class_file)

        if self.label_hist:
            self.default_label = self.label_hist[0]
        else:
            print("Not find:/data/predefined_classes.txt (optional)")

        # Main widgets and related state.
        self.label_dialog = LabelDialog(parent=self, list_item=self.label_hist)

        self.items_to_shapes = {}
        self.shapes_to_items = {}
        self.prev_label_text = ''
        
        # Initialize tracking
        self.continuous_tracking_mode = False
        self.tracker = Tracker()
        self.prev_frame_shapes = []
        
        # Initialize BB duplication feature
        self.bb_duplication_mode = False
        
        # Initialize click-to-change-label mode
        self.click_change_label_mode = False
        self._applying_label = False
        
        # Initialize Undo/Redo Manager
        from libs.undo.manager import UndoManager
        self.undo_manager = UndoManager(self, max_history=100)
        print("[DEBUG] Undo/Redo manager initialized")
        
        # Initialize Quick ID Selector
        self.quick_id_selector = QuickIDSelector(parent=self, max_ids=30)
        self.quick_id_selector.id_selected.connect(self.on_quick_id_selected)
        self.current_quick_id = "1"  # デフォルトID
        
        # BB ID管理
        
        # Install event filter to catch keyboard shortcuts globally
        self.installEventFilter(self)
        print("[DEBUG] Event filter installed for global keyboard shortcuts")
        
        # Also create QShortcut objects as a fallback
        from PyQt5.QtWidgets import QShortcut

        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)

        # Create a widget for using default label
        self.use_default_label_checkbox = QCheckBox(get_str('useDefaultLabel'))
        self.use_default_label_checkbox.setChecked(False)
        self.default_label_combo_box = DefaultLabelComboBox(self,items=self.label_hist)

        use_default_label_qhbox_layout = QHBoxLayout()
        use_default_label_qhbox_layout.addWidget(self.use_default_label_checkbox)
        use_default_label_qhbox_layout.addWidget(self.default_label_combo_box)
        use_default_label_container = QWidget()
        use_default_label_container.setLayout(use_default_label_qhbox_layout)

        # Create a widget for edit and diffc button
        self.diffc_button = QCheckBox(get_str('useDifficult'))
        self.diffc_button.setChecked(False)
        self.diffc_button.stateChanged.connect(self.button_state)
        self.edit_button = QToolButton()
        self.edit_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Add some of widgets to list_layout
        list_layout.addWidget(self.edit_button)
        list_layout.addWidget(self.diffc_button)
        list_layout.addWidget(use_default_label_container)
        
        # Create continuous tracking checkbox
        self.continuous_tracking_checkbox = QCheckBox("連続ID付けモード")
        self.continuous_tracking_checkbox.setChecked(False)
        self.continuous_tracking_checkbox.stateChanged.connect(self.toggle_continuous_tracking)
        list_layout.addWidget(self.continuous_tracking_checkbox)
        
        # Create click-to-change-label checkbox
        self.click_change_label_checkbox = QCheckBox("クリックでラベル変更")
        self.click_change_label_checkbox.setChecked(False)
        self.click_change_label_checkbox.stateChanged.connect(self.toggle_click_change_label)
        list_layout.addWidget(self.click_change_label_checkbox)
        
        # Create BB duplication feature container
        bb_dup_container = QWidget()
        bb_dup_layout = QVBoxLayout()
        bb_dup_layout.setContentsMargins(0, 0, 0, 0)
        bb_dup_container.setLayout(bb_dup_layout)
        
        # BB duplication checkbox
        self.bb_duplication_checkbox = QCheckBox("BB複製モード")
        self.bb_duplication_checkbox.setChecked(False)
        self.bb_duplication_checkbox.stateChanged.connect(self.toggle_bb_duplication)
        bb_dup_layout.addWidget(self.bb_duplication_checkbox)
        
        # Frame count for duplication
        frame_count_container = QWidget()
        frame_count_layout = QHBoxLayout()
        frame_count_layout.setContentsMargins(20, 0, 0, 0)  # Indent
        frame_count_container.setLayout(frame_count_layout)
        
        frame_count_label = QLabel("後続フレーム数:")
        self.bb_dup_frame_count = QSpinBox()
        self.bb_dup_frame_count.setMinimum(1)
        self.bb_dup_frame_count.setMaximum(100)
        self.bb_dup_frame_count.setValue(5)
        self.bb_dup_frame_count.setMaximumWidth(60)
        self.bb_dup_frame_count.setEnabled(False)
        
        frame_count_layout.addWidget(frame_count_label)
        frame_count_layout.addWidget(self.bb_dup_frame_count)
        frame_count_layout.addStretch()
        bb_dup_layout.addWidget(frame_count_container)
        
        # IOU threshold setting
        iou_threshold_container = QWidget()
        iou_threshold_layout = QHBoxLayout()
        iou_threshold_layout.setContentsMargins(20, 0, 0, 0)  # Indent
        iou_threshold_container.setLayout(iou_threshold_layout)
        
        iou_threshold_label = QLabel("IOUしきい値:")
        self.bb_dup_iou_threshold = QDoubleSpinBox()
        self.bb_dup_iou_threshold.setMinimum(0.1)
        self.bb_dup_iou_threshold.setMaximum(1.0)
        self.bb_dup_iou_threshold.setSingleStep(0.05)
        self.bb_dup_iou_threshold.setValue(0.6)
        self.bb_dup_iou_threshold.setMaximumWidth(80)
        self.bb_dup_iou_threshold.setEnabled(False)
        self.bb_dup_iou_threshold.valueChanged.connect(self.update_overwrite_checkbox_text)
        
        iou_threshold_layout.addWidget(iou_threshold_label)
        iou_threshold_layout.addWidget(self.bb_dup_iou_threshold)
        iou_threshold_layout.addStretch()
        bb_dup_layout.addWidget(iou_threshold_container)
        
        # Overwrite option checkbox
        self.bb_dup_overwrite_checkbox = QCheckBox("重複時に上書き (IOU>0.6)")
        self.bb_dup_overwrite_checkbox.setChecked(False)
        self.bb_dup_overwrite_checkbox.setEnabled(False)
        self.bb_dup_overwrite_checkbox.setContentsMargins(20, 0, 0, 0)
        bb_dup_layout.addWidget(self.bb_dup_overwrite_checkbox)
        
        # Initialize checkbox text with current IOU threshold
        self.update_overwrite_checkbox_text()
        
        list_layout.addWidget(bb_dup_container)

        # Create and add combobox for showing unique labels in group
        self.combo_box = ComboBox(self)
        list_layout.addWidget(self.combo_box)

        # Create and add a widget for showing current label items
        self.label_list = QListWidget()
        label_list_container = QWidget()
        label_list_container.setLayout(list_layout)
        self.label_list.itemActivated.connect(self.label_selection_changed)
        self.label_list.itemSelectionChanged.connect(self.label_selection_changed)
        self.label_list.itemDoubleClicked.connect(self.edit_label)
        # Connect to itemChanged to detect checkbox changes.
        self.label_list.itemChanged.connect(self.label_item_changed)
        list_layout.addWidget(self.label_list)
        
        # 描画選択パネルを追加
        draw_options_group = QGroupBox("描画オプション")
        draw_options_layout = QVBoxLayout()
        
        # BBの描画チェックボックス
        self.draw_bounding_box_checkbox = QCheckBox("Bounding Box")
        self.draw_bounding_box_checkbox.setChecked(True)  # デフォルトでチェック
        self.draw_bounding_box_checkbox.stateChanged.connect(self.toggle_bounding_box_display)
        draw_options_layout.addWidget(self.draw_bounding_box_checkbox)
        
        # IDの描画チェックボックス
        self.draw_id_checkbox = QCheckBox("ID")
        self.draw_id_checkbox.setChecked(True)  # デフォルトでチェック
        self.draw_id_checkbox.stateChanged.connect(self.toggle_id_display)
        draw_options_layout.addWidget(self.draw_id_checkbox)
        
        draw_options_group.setLayout(draw_options_layout)
        list_layout.addWidget(draw_options_group)



        self.dock = QDockWidget(get_str('boxLabelText'), self)
        self.dock.setObjectName(get_str('labels'))
        self.dock.setWidget(label_list_container)

        self.file_list_widget = QListWidget()
        self.file_list_widget.itemDoubleClicked.connect(self.file_item_double_clicked)
        file_list_layout = QVBoxLayout()
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addWidget(self.file_list_widget)
        file_list_container = QWidget()
        file_list_container.setLayout(file_list_layout)
        self.file_dock = QDockWidget(get_str('fileList'), self)
        self.file_dock.setObjectName(get_str('files'))
        self.file_dock.setWidget(file_list_container)

        self.zoom_widget = ZoomWidget()
        self.light_widget = LightWidget(get_str('lightWidgetTitle'))
        self.color_dialog = ColorDialog(parent=self)

        self.canvas = Canvas(parent=self)
        self.canvas.zoomRequest.connect(self.zoom_request)
        
        # Install event filter on canvas too
        self.canvas.installEventFilter(self)
        print("[DEBUG] Event filter installed on canvas")
        self.canvas.lightRequest.connect(self.light_request)
        self.canvas.set_drawing_shape_to_square(settings.get(SETTING_DRAW_SQUARE, False))

        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scroll_bars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.scroll_area = scroll
        self.canvas.scrollRequest.connect(self.scroll_request)

        self.canvas.newShape.connect(self.new_shape)
        self.canvas.shapeMoved.connect(self.set_dirty)
        self.canvas.selectionChanged.connect(self.shape_selection_changed)
        self.canvas.drawingPolygon.connect(self.toggle_drawing_sensitive)
        self.canvas.shapeClicked.connect(self.on_shape_clicked)
        

        self.setCentralWidget(scroll)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)
        self.file_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.dock_features = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        self.dock.setFeatures(self.dock.features() ^ self.dock_features)

        # Actions
        action = partial(new_action, self)
        quit = action(get_str('quit'), self.close,
                      'Ctrl+Q', 'quit', get_str('quitApp'))

        open = action(get_str('openFile'), self.open_file,
                      'Ctrl+O', 'open', get_str('openFileDetail'))

        open_dir = action(get_str('openDir'), self.open_dir_dialog,
                          'Ctrl+u', 'open', get_str('openDir'))

        change_save_dir = action(get_str('changeSaveDir'), self.change_save_dir_dialog,
                                 'Ctrl+r', 'open', get_str('changeSavedAnnotationDir'))

        open_annotation = action(get_str('openAnnotation'), self.open_annotation_dialog,
                                 'Ctrl+Shift+O', 'open', get_str('openAnnotationDetail'))
        copy_prev_bounding = action(get_str('copyPrevBounding'), self.copy_previous_bounding_boxes, 'Ctrl+v', 'copy', get_str('copyPrevBounding'))

        open_next_image = action(get_str('nextImg'), self.open_next_image,
                                 'd', 'next', get_str('nextImgDetail'))

        open_prev_image = action(get_str('prevImg'), self.open_prev_image,
                                 'a', 'prev', get_str('prevImgDetail'))
        
        # Undo/Redo actions
        undo = action('Undo', self.undo_action,
                     'Ctrl+Z', 'undo', 'Undo last action')
        redo = action('Redo', self.redo_action,
                     'Ctrl+Shift+Z', 'redo', 'Redo last action')
        
        # Explicitly add shortcuts
        undo.setShortcutContext(Qt.ApplicationShortcut)
        redo.setShortcutContext(Qt.ApplicationShortcut)

        verify = action(get_str('verifyImg'), self.verify_image,
                        'space', 'verify', get_str('verifyImgDetail'))

        save = action(get_str('save'), self.save_file,
                      'Ctrl+S', 'save', get_str('saveDetail'), enabled=False)

        def get_format_meta(format):
            """
            returns a tuple containing (title, icon_name) of the selected format
            """
            if format == LabelFileFormat.PASCAL_VOC:
                return '&PascalVOC', 'format_voc'
            elif format == LabelFileFormat.YOLO:
                return '&YOLO', 'format_yolo'
            elif format == LabelFileFormat.CREATE_ML:
                return '&CreateML', 'format_createml'

        save_format = action(get_format_meta(self.label_file_format)[0],
                             self.change_format, 'Ctrl+Y',
                             get_format_meta(self.label_file_format)[1],
                             get_str('changeSaveFormat'), enabled=True)

        save_as = action(get_str('saveAs'), self.save_file_as,
                         'Ctrl+Shift+S', 'save-as', get_str('saveAsDetail'), enabled=False)

        close = action(get_str('closeCur'), self.close_file, 'Ctrl+W', 'close', get_str('closeCurDetail'))

        delete_image = action(get_str('deleteImg'), self.delete_image, 'Ctrl+Shift+D', 'close', get_str('deleteImgDetail'))

        reset_all = action(get_str('resetAll'), self.reset_all, None, 'resetall', get_str('resetAllDetail'))

        color1 = action(get_str('boxLineColor'), self.choose_color1,
                        'Ctrl+L', 'color_line', get_str('boxLineColorDetail'))

        create_mode = action(get_str('crtBox'), self.set_create_mode,
                             'w', 'new', get_str('crtBoxDetail'), enabled=False)
        edit_mode = action(get_str('editBox'), self.set_edit_mode,
                           'Ctrl+J', 'edit', get_str('editBoxDetail'), enabled=False)

        create = action(get_str('crtBox'), self.create_shape,
                        'w', 'new', get_str('crtBoxDetail'), enabled=False)
        delete = action(get_str('delBox'), self.delete_selected_shape,
                        'Delete;s', 'delete', get_str('delBoxDetail'), enabled=False)
        copy = action(get_str('dupBox'), self.copy_selected_shape,
                      'Ctrl+D', 'copy', get_str('dupBoxDetail'),
                      enabled=False)

        advanced_mode = action(get_str('advancedMode'), self.toggle_advanced_mode,
                               'Ctrl+Shift+A', 'expert', get_str('advancedModeDetail'),
                               checkable=True)

        hide_all = action(get_str('hideAllBox'), partial(self.toggle_polygons, False),
                          'Ctrl+H', 'hide', get_str('hideAllBoxDetail'),
                          enabled=False)
        show_all = action(get_str('showAllBox'), partial(self.toggle_polygons, True),
                          'Ctrl+A', 'hide', get_str('showAllBoxDetail'),
                          enabled=False)

        help_default = action(get_str('tutorialDefault'), self.show_default_tutorial_dialog, None, 'help', get_str('tutorialDetail'))
        show_info = action(get_str('info'), self.show_info_dialog, None, 'help', get_str('info'))
        show_shortcut = action(get_str('shortcut'), self.show_shortcuts_dialog, None, 'help', get_str('shortcut'))

        zoom = QWidgetAction(self)
        zoom.setDefaultWidget(self.zoom_widget)
        self.zoom_widget.setWhatsThis(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (format_shortcut("Ctrl+[-+]"),
                                             format_shortcut("Ctrl+Wheel")))
        self.zoom_widget.setEnabled(False)

        zoom_in = action(get_str('zoomin'), partial(self.add_zoom, 10),
                         'Ctrl++', 'zoom-in', get_str('zoominDetail'), enabled=False)
        zoom_out = action(get_str('zoomout'), partial(self.add_zoom, -10),
                          'Ctrl+-', 'zoom-out', get_str('zoomoutDetail'), enabled=False)
        zoom_org = action(get_str('originalsize'), partial(self.set_zoom, 100),
                          'Ctrl+=', 'zoom', get_str('originalsizeDetail'), enabled=False)
        fit_window = action(get_str('fitWin'), self.set_fit_window,
                            'Ctrl+F', 'fit-window', get_str('fitWinDetail'),
                            checkable=True, enabled=False)
        fit_width = action(get_str('fitWidth'), self.set_fit_width,
                           'Ctrl+Shift+F', 'fit-width', get_str('fitWidthDetail'),
                           checkable=True, enabled=False)
        # Group zoom controls into a list for easier toggling.
        zoom_actions = (self.zoom_widget, zoom_in, zoom_out,
                        zoom_org, fit_window, fit_width)
        self.zoom_mode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scale_fit_window,
            self.FIT_WIDTH: self.scale_fit_width,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        light = QWidgetAction(self)
        light.setDefaultWidget(self.light_widget)
        self.light_widget.setWhatsThis(
            u"Brighten or darken current image. Also accessible with"
            " %s and %s from the canvas." % (format_shortcut("Ctrl+Shift+[-+]"),
                                             format_shortcut("Ctrl+Shift+Wheel")))
        self.light_widget.setEnabled(False)

        light_brighten = action(get_str('lightbrighten'), partial(self.add_light, 10),
                                'Ctrl+Shift++', 'light_lighten', get_str('lightbrightenDetail'), enabled=False)
        light_darken = action(get_str('lightdarken'), partial(self.add_light, -10),
                              'Ctrl+Shift+-', 'light_darken', get_str('lightdarkenDetail'), enabled=False)
        light_org = action(get_str('lightreset'), partial(self.set_light, 50),
                           'Ctrl+Shift+=', 'light_reset', get_str('lightresetDetail'), checkable=True, enabled=False)
        light_org.setChecked(True)

        # Group light controls into a list for easier toggling.
        light_actions = (self.light_widget, light_brighten,
                         light_darken, light_org)

        edit = action(get_str('editLabel'), self.edit_label,
                      'Ctrl+E', 'edit', get_str('editLabelDetail'),
                      enabled=False)
        self.edit_button.setDefaultAction(edit)

        shape_line_color = action(get_str('shapeLineColor'), self.choose_shape_line_color,
                                  icon='color_line', tip=get_str('shapeLineColorDetail'),
                                  enabled=False)
        shape_fill_color = action(get_str('shapeFillColor'), self.choose_shape_fill_color,
                                  icon='color', tip=get_str('shapeFillColorDetail'),
                                  enabled=False)

        labels = self.dock.toggleViewAction()
        labels.setText(get_str('showHide'))
        labels.setShortcut('Ctrl+Shift+L')

        # Label list context menu.
        label_menu = QMenu()
        add_actions(label_menu, (edit, delete))
        self.label_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label_list.customContextMenuRequested.connect(
            self.pop_label_list_menu)

        # Draw squares/rectangles
        self.draw_squares_option = QAction(get_str('drawSquares'), self)
        self.draw_squares_option.setShortcut('Ctrl+Shift+R')
        self.draw_squares_option.setCheckable(True)
        self.draw_squares_option.setChecked(settings.get(SETTING_DRAW_SQUARE, False))
        self.draw_squares_option.triggered.connect(self.toggle_draw_square)

        # Store actions for further handling.
        self.actions = Struct(save=save, save_format=save_format, saveAs=save_as, open=open, close=close, resetAll=reset_all, deleteImg=delete_image,
                              undo=undo, redo=redo,
                              lineColor=color1, create=create, delete=delete, edit=edit, copy=copy,
                              createMode=create_mode, editMode=edit_mode, advancedMode=advanced_mode,
                              shapeLineColor=shape_line_color, shapeFillColor=shape_fill_color,
                              zoom=zoom, zoomIn=zoom_in, zoomOut=zoom_out, zoomOrg=zoom_org,
                              fitWindow=fit_window, fitWidth=fit_width,
                              zoomActions=zoom_actions,
                              lightBrighten=light_brighten, lightDarken=light_darken, lightOrg=light_org,
                              lightActions=light_actions,
                              fileMenuActions=(
                                  open, open_dir, save, save_as, close, reset_all, quit),
                              beginner=(), advanced=(),
                              editMenu=(edit, copy, delete,
                                        None, color1, self.draw_squares_option),
                              beginnerContext=(create, edit, copy, delete),
                              advancedContext=(create_mode, edit_mode, edit, copy,
                                               delete, shape_line_color, shape_fill_color),
                              onLoadActive=(
                                  close, create, create_mode, edit_mode),
                              onShapesPresent=(save_as, hide_all, show_all))

        self.menus = Struct(
            file=self.menu(get_str('menu_file')),
            edit=self.menu(get_str('menu_edit')),
            view=self.menu(get_str('menu_view')),
            help=self.menu(get_str('menu_help')),
            recentFiles=QMenu(get_str('menu_openRecent')),
            labelList=label_menu)

        # Auto saving : Enable auto saving if pressing next
        self.auto_saving = QAction(get_str('autoSaveMode'), self)
        self.auto_saving.setCheckable(True)
        self.auto_saving.setChecked(settings.get(SETTING_AUTO_SAVE, False))
        # Sync single class mode from PR#106
        self.single_class_mode = QAction(get_str('singleClsMode'), self)
        self.single_class_mode.setShortcut("Ctrl+Shift+S")
        self.single_class_mode.setCheckable(True)
        self.single_class_mode.setChecked(settings.get(SETTING_SINGLE_CLASS, False))
        self.lastLabel = None
        # Add option to enable/disable labels being displayed at the top of bounding boxes
        self.display_label_option = QAction(get_str('displayLabel'), self)
        self.display_label_option.setShortcut("Ctrl+Shift+P")
        self.display_label_option.setCheckable(True)
        self.display_label_option.setChecked(settings.get(SETTING_PAINT_LABEL, False))
        self.display_label_option.triggered.connect(self.toggle_paint_labels_option)

        # Add Edit menu
        self.menus.edit = QMenu('Edit', self)
        add_actions(self.menus.edit, (undo, redo, None, edit, copy, delete))
        
        add_actions(self.menus.file,
                    (open, open_dir, change_save_dir, open_annotation, copy_prev_bounding, self.menus.recentFiles, save, save_format, save_as, close, reset_all, delete_image, quit))
        add_actions(self.menus.help, (help_default, show_info, show_shortcut))
        add_actions(self.menus.view, (
            self.auto_saving,
            self.single_class_mode,
            self.display_label_option,
            labels, advanced_mode, None,
            hide_all, show_all, None,
            zoom_in, zoom_out, zoom_org, None,
            fit_window, fit_width, None,
            light_brighten, light_darken, light_org))

        self.menus.file.aboutToShow.connect(self.update_file_menu)

        # Custom context menu for the canvas widget:
        add_actions(self.canvas.menus[0], self.actions.beginnerContext)
        add_actions(self.canvas.menus[1], (
            action('&Copy here', self.copy_shape),
            action('&Move here', self.move_shape)))

        self.tools = self.toolbar('Tools')
        self.actions.beginner = (
            open, open_dir, change_save_dir, open_next_image, open_prev_image, verify, save, save_format, None, create, copy, delete, None,
            zoom_in, zoom, zoom_out, fit_window, fit_width, None,
            light_brighten, light, light_darken, light_org)

        self.actions.advanced = (
            open, open_dir, change_save_dir, open_next_image, open_prev_image, save, save_format, None,
            create_mode, edit_mode, None,
            hide_all, show_all)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

        # Application state.
        self.image = QImage()
        self.file_path = ustr(default_filename)
        self.last_open_dir = None
        self.recent_files = []
        self.max_recent = 7
        self.line_color = None
        self.fill_color = None
        self.zoom_level = 100
        self.fit_window = False
        # Add Chris
        self.difficult = False

        # Fix the compatible issue for qt4 and qt5. Convert the QStringList to python list
        if settings.get(SETTING_RECENT_FILES):
            if have_qstring():
                recent_file_qstring_list = settings.get(SETTING_RECENT_FILES)
                self.recent_files = [ustr(i) for i in recent_file_qstring_list]
            else:
                self.recent_files = recent_file_qstring_list = settings.get(SETTING_RECENT_FILES)

        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))
        position = QPoint(0, 0)
        saved_position = settings.get(SETTING_WIN_POSE, position)
        # Fix the multiple monitors issue
        for i in range(QApplication.desktop().screenCount()):
            if QApplication.desktop().availableGeometry(i).contains(saved_position):
                position = saved_position
                break
        self.resize(size)
        self.move(position)
        save_dir = ustr(settings.get(SETTING_SAVE_DIR, None))
        self.last_open_dir = ustr(settings.get(SETTING_LAST_OPEN_DIR, None))
        # Only use settings save_dir if no command line argument was provided
        if self.default_save_dir is None and save_dir is not None and os.path.exists(save_dir):
            self.default_save_dir = save_dir
            self.statusBar().showMessage('%s started. Annotation will be saved to %s' %
                                         (__appname__, self.default_save_dir))
            self.statusBar().show()

        self.restoreState(settings.get(SETTING_WIN_STATE, QByteArray()))
        Shape.line_color = self.line_color = QColor(settings.get(SETTING_LINE_COLOR, DEFAULT_LINE_COLOR))
        Shape.fill_color = self.fill_color = QColor(settings.get(SETTING_FILL_COLOR, DEFAULT_FILL_COLOR))
        self.canvas.set_drawing_color(self.line_color)
        # Add chris
        Shape.difficult = self.difficult

        def xbool(x):
            if isinstance(x, QVariant):
                return x.toBool()
            return bool(x)

        if xbool(settings.get(SETTING_ADVANCE_MODE, False)):
            self.actions.advancedMode.setChecked(True)
            self.toggle_advanced_mode()

        # Populate the File menu dynamically.
        self.update_file_menu()

        # Since loading the file may take some time, make sure it runs in the background.
        if self.file_path and os.path.isdir(self.file_path):
            self.queue_event(partial(self.import_dir_images, self.file_path or ""))
        elif self.file_path:
            self.queue_event(partial(self.load_file, self.file_path or ""))

        # Callbacks:
        self.zoom_widget.valueChanged.connect(self.paint_canvas)
        self.light_widget.valueChanged.connect(self.paint_canvas)

        self.populate_mode_actions()

        # Display cursor coordinates at the right of status bar
        self.label_coordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.label_coordinates)
        
        # Display current Quick ID at the right of status bar
        # 初期化時は実際のクラス名を表示
        initial_class = self.label_hist[0] if self.label_hist else "cow"
        self.label_current_id = QLabel(initial_class)
        self.label_current_id.setStyleSheet("""
            QLabel {
                background-color: #0066cc;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-left: 8px;
            }
        """)
        self.statusBar().addPermanentWidget(self.label_current_id)

        # Open Dir if default file
        if self.file_path and os.path.isdir(self.file_path):
            self.open_dir_dialog(dir_path=self.file_path, silent=True)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.canvas.set_drawing_shape_to_square(False)

    def keyPressEvent(self, event):
        # F1キー: Quick ID Selectorの表示/非表示
        if event.key() == Qt.Key_F1:
            self.toggle_quick_id_selector()
            return
        
        # 数字キー（1-9）: Quick ID直接選択
        if Qt.Key_1 <= event.key() <= Qt.Key_9:
            id_num = event.key() - Qt.Key_0
            self.select_quick_id(str(id_num))
            return
        
        # 0キー: ID 10を選択
        elif event.key() == Qt.Key_0:
            self.select_quick_id("10")
            return
        
        if event.key() == Qt.Key_Control:
            self.canvas.set_drawing_shape_to_square(True)
        
        super(MainWindow, self).keyPressEvent(event)

    def wheelEvent(self, event):
        """マウスホイールイベント処理"""
        # Shift+ホイール: Quick ID切り替え
        if event.modifiers() == Qt.ShiftModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.prev_quick_id()
            elif delta < 0:
                self.next_quick_id()
            event.accept()
            return
        
        super(MainWindow, self).wheelEvent(event)

    def eventFilter(self, obj, event):
        """Global event filter to catch keyboard shortcuts"""
        if event.type() == event.KeyPress:
            # デバッグ：Ctrlキーと組み合わせのキーを表示
            if event.modifiers() & Qt.ControlModifier:
                print(f"[DEBUG] Key pressed with Ctrl: key={event.key()}, text='{event.text()}', modifiers={event.modifiers()}")
                # Qt.Key_Y = 89, Qt.Key_Z = 90
                print(f"[DEBUG] Qt.Key_Y={Qt.Key_Y}, Qt.Key_Z={Qt.Key_Z}")
            
            # Ctrl+Z / Ctrl+Shift+Z の処理
            if event.modifiers() == Qt.ControlModifier:
                if event.key() == Qt.Key_Z or event.key() == 90:
                    print("[DEBUG] Ctrl+Z pressed in eventFilter")
                    self.undo_action()
                    return True
            elif event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                if event.key() == Qt.Key_Z:
                    print("[DEBUG] Ctrl+Shift+Z pressed in eventFilter")
                    self.redo_action()
                    return True
            
            # DELキー・sキー処理
            if event.key() == Qt.Key_Delete or event.key() == Qt.Key_S:
                if self.canvas.selected_shape and self.actions.delete.isEnabled():
                    self.delete_selected_shape()
                    return True
                return False
            
            # F1キー処理
            if event.key() == Qt.Key_F1:
                self.toggle_quick_id_selector()
                return True
            
            # 数字キー処理
            if Qt.Key_1 <= event.key() <= Qt.Key_9:
                id_num = event.key() - Qt.Key_0
                self.select_quick_id(str(id_num))
                return True
            elif event.key() == Qt.Key_0:
                self.select_quick_id("10")
                return True
            
        
        # ホイールイベント処理
        elif event.type() == event.Wheel:
            if event.modifiers() == Qt.ShiftModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.prev_quick_id()
                elif delta < 0:
                    self.next_quick_id()
                return True
        
        return super(MainWindow, self).eventFilter(obj, event)

    # Support Functions #
    def set_format(self, save_format):
        if save_format == FORMAT_PASCALVOC:
            self.actions.save_format.setText(FORMAT_PASCALVOC)
            self.actions.save_format.setIcon(new_icon("format_voc"))
            self.label_file_format = LabelFileFormat.PASCAL_VOC
            LabelFile.suffix = XML_EXT

        elif save_format == FORMAT_YOLO:
            self.actions.save_format.setText(FORMAT_YOLO)
            self.actions.save_format.setIcon(new_icon("format_yolo"))
            self.label_file_format = LabelFileFormat.YOLO
            LabelFile.suffix = TXT_EXT

        elif save_format == FORMAT_CREATEML:
            self.actions.save_format.setText(FORMAT_CREATEML)
            self.actions.save_format.setIcon(new_icon("format_createml"))
            self.label_file_format = LabelFileFormat.CREATE_ML
            LabelFile.suffix = JSON_EXT

    def change_format(self):
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            self.set_format(FORMAT_YOLO)
        elif self.label_file_format == LabelFileFormat.YOLO:
            self.set_format(FORMAT_CREATEML)
        elif self.label_file_format == LabelFileFormat.CREATE_ML:
            self.set_format(FORMAT_PASCALVOC)
        else:
            raise ValueError('Unknown label file format.')
        self.set_dirty()

    def no_shapes(self):
        return not self.items_to_shapes

    def toggle_advanced_mode(self, value=True):
        self._beginner = not value
        self.canvas.set_editing(True)
        self.populate_mode_actions()
        self.edit_button.setVisible(not value)
        if value:
            self.actions.createMode.setEnabled(True)
            self.actions.editMode.setEnabled(False)
            self.dock.setFeatures(self.dock.features() | self.dock_features)
        else:
            self.dock.setFeatures(self.dock.features() ^ self.dock_features)

    def populate_mode_actions(self):
        if self.beginner():
            tool, menu = self.actions.beginner, self.actions.beginnerContext
        else:
            tool, menu = self.actions.advanced, self.actions.advancedContext
        self.tools.clear()
        add_actions(self.tools, tool)
        self.canvas.menus[0].clear()
        add_actions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (self.actions.create,) if self.beginner()\
            else (self.actions.createMode, self.actions.editMode)
        add_actions(self.menus.edit, actions + self.actions.editMenu)

    def set_beginner(self):
        self.tools.clear()
        add_actions(self.tools, self.actions.beginner)

    def set_advanced(self):
        self.tools.clear()
        add_actions(self.tools, self.actions.advanced)

    def set_dirty(self):
        self.dirty = True
        self.actions.save.setEnabled(True)

    def set_clean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.create.setEnabled(True)

    def toggle_actions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for z in self.actions.lightActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def queue_event(self, function):
        QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def reset_state(self):
        self.items_to_shapes.clear()
        self.shapes_to_items.clear()
        self.label_list.clear()
        self.file_path = None
        self.image_data = None
        self.label_file = None
        self.canvas.reset_state()
        self.label_coordinates.clear()
        self.combo_box.cb.clear()
        # Reset tracking information
        self.prev_frame_shapes = []
        self.tracker.reset()

    def current_item(self):
        items = self.label_list.selectedItems()
        if items:
            return items[0]
        return None

    def add_recent_file(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        elif len(self.recent_files) >= self.max_recent:
            self.recent_files.pop()
        self.recent_files.insert(0, file_path)

    def beginner(self):
        return self._beginner

    def advanced(self):
        return not self.beginner()

    def show_tutorial_dialog(self, browser='default', link=None):
        if link is None:
            link = self.screencast

        if browser.lower() == 'default':
            wb.open(link, new=2)
        elif browser.lower() == 'chrome' and self.os_name == 'Windows':
            if shutil.which(browser.lower()):  # 'chrome' not in wb._browsers in windows
                wb.register('chrome', None, wb.BackgroundBrowser('chrome'))
            else:
                chrome_path="D:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.isfile(chrome_path):
                    wb.register('chrome', None, wb.BackgroundBrowser(chrome_path))
            try:
                wb.get('chrome').open(link, new=2)
            except:
                wb.open(link, new=2)
        elif browser.lower() in wb._browsers:
            wb.get(browser.lower()).open(link, new=2)

    def show_default_tutorial_dialog(self):
        self.show_tutorial_dialog(browser='default')

    def show_info_dialog(self):
        from libs.__init__ import __version__
        msg = u'Name:{0} \nApp Version:{1} \n{2} '.format(__appname__, __version__, sys.version_info)
        QMessageBox.information(self, u'Information', msg)

    def show_shortcuts_dialog(self):
        self.show_tutorial_dialog(browser='default', link='https://github.com/tzutalin/labelImg#Hotkeys')

    def create_shape(self):
        assert self.beginner()
        self.canvas.set_editing(False)
        self.actions.create.setEnabled(False)

    def toggle_drawing_sensitive(self, drawing=True):
        """In the middle of drawing, toggling between modes should be disabled."""
        self.actions.editMode.setEnabled(not drawing)
        if not drawing and self.beginner():
            # Cancel creation.
            print('Cancel creation.')
            self.canvas.set_editing(True)
            self.canvas.restore_cursor()
            self.actions.create.setEnabled(True)

    def toggle_draw_mode(self, edit=True):
        self.canvas.set_editing(edit)
        self.actions.createMode.setEnabled(edit)
        self.actions.editMode.setEnabled(not edit)

    def set_create_mode(self):
        assert self.advanced()
        self.toggle_draw_mode(False)

    def set_edit_mode(self):
        assert self.advanced()
        self.toggle_draw_mode(True)
        self.label_selection_changed()

    def update_file_menu(self):
        curr_file_path = self.file_path

        def exists(filename):
            return os.path.exists(filename)
        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recent_files if f !=
                 curr_file_path and exists(f)]
        for i, f in enumerate(files):
            icon = new_icon('labels')
            action = QAction(
                icon, '&%d %s' % (i + 1, QFileInfo(f).fileName()), self)
            action.triggered.connect(partial(self.load_recent, f))
            menu.addAction(action)

    def pop_label_list_menu(self, point):
        self.menus.labelList.exec_(self.label_list.mapToGlobal(point))

    def edit_label(self):
        if not self.canvas.editing():
            return
        item = self.current_item()
        if not item:
            return
        
        # Get the shape associated with this item
        shape = self.items_to_shapes.get(item)
        if not shape:
            return
        
        old_label = item.text()
        text = self.label_dialog.pop_up(old_label)
        if text is not None and text != old_label:
            print(f"[DEBUG] edit_label: Changing label from '{old_label}' to '{text}'")
            # Get shape index
            shape_index = self.canvas.shapes.index(shape) if shape in self.canvas.shapes else -1
            if shape_index >= 0:
                # Create and execute ChangeLabelCommand
                from libs.undo.commands.label_commands import ChangeLabelCommand
                change_cmd = ChangeLabelCommand(self.file_path, shape_index, old_label, text)
                result = self.undo_manager.execute_command(change_cmd)
                print(f"[DEBUG] ChangeLabelCommand executed: {result}")
                print(f"[DEBUG] UndoManager state: {self.undo_manager}")
            else:
                print(f"[DEBUG] Shape not found in canvas.shapes")

    # Tzutalin 20160906 : Add file list and dock to move faster
    def file_item_double_clicked(self, item=None):
        self.cur_img_idx = self.m_img_list.index(ustr(item.text()))
        filename = self.m_img_list[self.cur_img_idx]
        if filename:
            self.load_file(filename)

    # Add chris
    def button_state(self, item=None):
        """ Function to handle difficult examples
        Update on each object """
        if not self.canvas.editing():
            return

        item = self.current_item()
        if not item:  # If not selected Item, take the first one
            item = self.label_list.item(self.label_list.count() - 1)

        difficult = self.diffc_button.isChecked()

        try:
            shape = self.items_to_shapes[item]
        except:
            pass
        # Checked and Update
        try:
            if difficult != shape.difficult:
                shape.difficult = difficult
                self.set_dirty()
            else:  # User probably changed item visibility
                self.canvas.set_shape_visible(shape, item.checkState() == Qt.Checked)
        except:
            pass

    # React to canvas signals.
    def shape_selection_changed(self, selected=False):
        if self._no_selection_slot:
            self._no_selection_slot = False
        else:
            shape = self.canvas.selected_shape
            if shape:
                self.shapes_to_items[shape].setSelected(True)
            else:
                self.label_list.clearSelection()
        
        has_selection = self.canvas.selected_shape is not None
        self.actions.delete.setEnabled(has_selection)
        self.actions.copy.setEnabled(selected)
        self.actions.edit.setEnabled(selected)
        self.actions.shapeLineColor.setEnabled(selected)
        self.actions.shapeFillColor.setEnabled(selected)

    def add_label(self, shape):
        shape.paint_label = self.display_label_option.isChecked()
        shape.paint_id = self.draw_id_checkbox.isChecked()
        
        item = HashableQListWidgetItem(shape.label)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setBackground(generate_color_by_text(shape.label))
        self.items_to_shapes[item] = shape
        self.shapes_to_items[shape] = item
        self.label_list.addItem(item)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)
        self.update_combo_box()
        
        # Quick ID Selectorの不足ラベルを更新
        if hasattr(self, 'quick_id_selector') and self.quick_id_selector.isVisible():
            self.quick_id_selector.update_missing_labels()

    def remove_label(self, shape):
        if shape is None:
            # print('rm empty label')
            return
        item = self.shapes_to_items[shape]
        self.label_list.takeItem(self.label_list.row(item))
        del self.shapes_to_items[shape]
        del self.items_to_shapes[item]
        self.update_combo_box()

    def load_labels(self, shapes):
        s = []
        for label, points, line_color, fill_color, difficult in shapes:
            shape = Shape(label=label)
            for x, y in points:

                # Ensure the labels are within the bounds of the image. If not, fix them.
                x, y, snapped = self.canvas.snap_point_to_canvas(x, y)
                if snapped:
                    self.set_dirty()

                shape.add_point(QPointF(x, y))
            shape.difficult = difficult
            
            if line_color:
                shape.line_color = QColor(*line_color)
            else:
                shape.line_color = generate_color_by_text(label)

            if fill_color:
                shape.fill_color = QColor(*fill_color)
            else:
                shape.fill_color = generate_color_by_text(label)
                
            shape.close()
            s.append(shape)

            self.add_label(shape)
        self.update_combo_box()
        self.canvas.load_shapes(s)

    def update_combo_box(self):
        # Get the unique labels and add them to the Combobox.
        items_text_list = [str(self.label_list.item(i).text()) for i in range(self.label_list.count())]

        unique_text_list = list(set(items_text_list))
        # Add a null row for showing all the labels
        unique_text_list.append("")
        unique_text_list.sort()

        self.combo_box.update_items(unique_text_list)

    def save_labels(self, annotation_file_path):
        annotation_file_path = ustr(annotation_file_path)
        if self.label_file is None:
            self.label_file = LabelFile()
            self.label_file.verified = self.canvas.verified

        def format_shape(s):
            result = dict(label=s.label,
                        line_color=s.line_color.getRgb(),
                        fill_color=s.fill_color.getRgb(),
                        points=[(p.x(), p.y()) for p in s.points],
                        # add chris
                        difficult=s.difficult)
            return result

        shapes = [format_shape(shape) for shape in self.canvas.shapes]
        # Can add different annotation formats here
        try:
            if self.label_file_format == LabelFileFormat.PASCAL_VOC:
                if annotation_file_path[-4:].lower() != ".xml":
                    annotation_file_path += XML_EXT
                self.label_file.save_pascal_voc_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                       self.line_color.getRgb(), self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.YOLO:
                if annotation_file_path[-4:].lower() != ".txt":
                    annotation_file_path += TXT_EXT
                self.label_file.save_yolo_format(annotation_file_path, shapes, self.file_path, self.image_data, self.label_hist,
                                                 self.line_color.getRgb(), self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.CREATE_ML:
                if annotation_file_path[-5:].lower() != ".json":
                    annotation_file_path += JSON_EXT
                self.label_file.save_create_ml_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                      self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
            else:
                self.label_file.save(annotation_file_path, shapes, self.file_path, self.image_data,
                                     self.line_color.getRgb(), self.fill_color.getRgb())
            print('Image:{0} -> Annotation:{1}'.format(self.file_path, annotation_file_path))
            return True
        except LabelFileError as e:
            self.error_message(u'Error saving label data', u'<b>%s</b>' % e)
            return False

    def copy_selected_shape(self):
        # Save state before copying
        
        self.add_label(self.canvas.copy_selected_shape())
        # fix copy and delete
        self.shape_selection_changed(True)

    def combo_selection_changed(self, index):
        text = self.combo_box.cb.itemText(index)
        for i in range(self.label_list.count()):
            if text == "":
                self.label_list.item(i).setCheckState(2)
            elif text != self.label_list.item(i).text():
                self.label_list.item(i).setCheckState(0)
            else:
                self.label_list.item(i).setCheckState(2)

    def default_label_combo_selection_changed(self, index):
        self.default_label = self.label_hist[index]
        
        # Quick ID Selectorも同期更新
        if self.quick_id_selector and self.quick_id_selector.isVisible():
            id_str = str(index + 1)
            self.quick_id_selector.set_current_id(id_str)
            self.current_quick_id = id_str
            self.update_current_id_display()

    def label_selection_changed(self):
        item = self.current_item()
        if item and self.canvas.editing():
            self._no_selection_slot = True
            self.canvas.select_shape(self.items_to_shapes[item])
            shape = self.items_to_shapes[item]
            # Add Chris
            self.diffc_button.setChecked(shape.difficult)

    def label_item_changed(self, item):
        shape = self.items_to_shapes[item]
        label = item.text()
        if label != shape.label:
            shape.label = item.text()
            shape.line_color = generate_color_by_text(shape.label)
            self.set_dirty()
        else:  # User probably changed item visibility
            self.canvas.set_shape_visible(shape, item.checkState() == Qt.Checked)

    # Callback functions:
    def new_shape(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        if not self.use_default_label_checkbox.isChecked():
            if len(self.label_hist) > 0:
                self.label_dialog = LabelDialog(
                    parent=self, list_item=self.label_hist)

            # Sync single class mode from PR#106
            if self.single_class_mode.isChecked() and self.lastLabel:
                text = self.lastLabel
            else:
                text = self.label_dialog.pop_up(text=self.prev_label_text)
                self.lastLabel = text
        else:
            text = self.default_label

        # Add Chris
        self.diffc_button.setChecked(False)
        if text is not None:
            print(f"[DEBUG] new_shape: Adding shape with label '{text}'")
            
            self.prev_label_text = text
            generate_color = generate_color_by_text(text)
            
            # Set the label for the last shape that was just drawn
            shape = self.canvas.set_last_label(text, generate_color, generate_color)
            
            # Create shape data for the command
            shape_data = {
                'label': text,
                'points': [(p.x(), p.y()) for p in shape.points],
                'difficult': shape.difficult if hasattr(shape, 'difficult') else False,
                'line_color': generate_color,
                'fill_color': generate_color
            }
            
            # Add to label list UI
            self.add_label(shape)
            
            # Create and execute AddShapeCommand for undo/redo tracking
            from libs.undo.commands.shape_commands import AddShapeCommand
            from libs.undo.commands.composite_command import CompositeCommand
            
            # Note: The shape is already in the canvas, but we need to track it for undo
            # So we'll store the index for proper removal on undo
            shape_index = len(self.canvas.shapes) - 1
            
            # Create a custom command that just tracks the already-added shape
            class TrackAddedShapeCommand(AddShapeCommand):
                def __init__(self, frame_path, shape_data, shape_index):
                    super().__init__(frame_path, shape_data)
                    self.shape_index = shape_index
                    self.executed = True  # Mark as already executed
                
                def execute(self, app):
                    # Shape is already added, just return success
                    return True
                
                def undo(self, app):
                    # Remove the shape that was added
                    try:
                        print(f"[DEBUG] TrackAddedShapeCommand.undo: Removing shape at index {self.shape_index}")
                        if app.file_path != self.frame_path:
                            app.load_file(self.frame_path, preserve_zoom=True)
                        
                        if self.shape_index < len(app.canvas.shapes):
                            shape = app.canvas.shapes[self.shape_index]
                            
                            # Remove from label list
                            if hasattr(app, 'remove_label'):
                                app.remove_label(shape)
                            
                            # Remove from canvas
                            app.canvas.shapes.pop(self.shape_index)
                            
                            # Update canvas
                            if hasattr(app.canvas, 'load_shapes'):
                                app.canvas.load_shapes(app.canvas.shapes)
                            elif hasattr(app.canvas, 'update'):
                                app.canvas.update()
                            
                            # Mark as dirty
                            app.set_dirty()
                            
                            # Auto-save if enabled
                            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                                app.save_file()
                        
                        self.executed = False
                        return True
                    except Exception as e:
                        print(f"[DEBUG] Error undoing shape: {e}")
                        return False
                
                def redo(self, app):
                    # Re-add the shape
                    try:
                        print(f"[DEBUG] TrackAddedShapeCommand.redo called")
                        print(f"[DEBUG] TrackAddedShapeCommand.redo: Re-adding shape '{self.shape_data['label']}'")
                        print(f"[DEBUG] Canvas shapes before redo execute: {len(app.canvas.shapes)}")
                        
                        # Call parent's execute to add the shape properly
                        result = super().execute(app)
                        
                        print(f"[DEBUG] Canvas shapes after redo execute: {len(app.canvas.shapes)}")
                        print(f"[DEBUG] Redo execute result: {result}")
                        
                        if result:
                            self.executed = True
                        return result
                    except Exception as e:
                        print(f"[DEBUG] Error redoing shape: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
            
            # Track the shape addition for undo
            track_cmd = TrackAddedShapeCommand(self.file_path, shape_data, shape_index)
            print(f"[DEBUG] Tracking shape addition for undo/redo")
            self.undo_manager.execute_command(track_cmd)
            print(f"[DEBUG] UndoManager state: {self.undo_manager}")
            
            if self.beginner():  # Switch to edit mode.
                self.canvas.set_editing(True)
                self.actions.create.setEnabled(True)
            else:
                self.actions.editMode.setEnabled(True)
            
            self.set_dirty()
            
            if text not in self.label_hist:
                self.label_hist.append(text)
            
            # Apply BB duplication if enabled
            if self.bb_duplication_mode:
                self.duplicate_bb_to_subsequent_frames(shape)
        else:
            self.canvas.reset_all_lines()

    def scroll_request(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scroll_bars[orientation]
        bar.setValue(int(bar.value() + bar.singleStep() * units))

    def set_zoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.MANUAL_ZOOM
        # Arithmetic on scaling factor often results in float
        # Convert to int to avoid type errors
        self.zoom_widget.setValue(int(value))

    def add_zoom(self, increment=10):
        self.set_zoom(self.zoom_widget.value() + increment)

    def zoom_request(self, delta):
        # get the current scrollbar positions
        # calculate the percentages ~ coordinates
        h_bar = self.scroll_bars[Qt.Horizontal]
        v_bar = self.scroll_bars[Qt.Vertical]

        # get the current maximum, to know the difference after zooming
        h_bar_max = h_bar.maximum()
        v_bar_max = v_bar.maximum()

        # get the cursor position and canvas size
        # calculate the desired movement from 0 to 1
        # where 0 = move left
        #       1 = move right
        # up and down analogous
        cursor = QCursor()
        pos = cursor.pos()
        relative_pos = QWidget.mapFromGlobal(self, pos)

        cursor_x = relative_pos.x()
        cursor_y = relative_pos.y()

        w = self.scroll_area.width()
        h = self.scroll_area.height()

        # the scaling from 0 to 1 has some padding
        # you don't have to hit the very leftmost pixel for a maximum-left movement
        margin = 0.1
        move_x = (cursor_x - margin * w) / (w - 2 * margin * w)
        move_y = (cursor_y - margin * h) / (h - 2 * margin * h)

        # clamp the values from 0 to 1
        move_x = min(max(move_x, 0), 1)
        move_y = min(max(move_y, 0), 1)

        # zoom in
        units = delta // (8 * 15)
        scale = 10
        self.add_zoom(scale * units)

        # get the difference in scrollbar values
        # this is how far we can move
        d_h_bar_max = h_bar.maximum() - h_bar_max
        d_v_bar_max = v_bar.maximum() - v_bar_max

        # get the new scrollbar values
        new_h_bar_value = int(h_bar.value() + move_x * d_h_bar_max)
        new_v_bar_value = int(v_bar.value() + move_y * d_v_bar_max)

        h_bar.setValue(new_h_bar_value)
        v_bar.setValue(new_v_bar_value)

    def light_request(self, delta):
        self.add_light(5*delta // (8 * 15))

    def set_fit_window(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoom_mode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_fit_width(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_light(self, value):
        self.actions.lightOrg.setChecked(int(value) == 50)
        # Arithmetic on scaling factor often results in float
        # Convert to int to avoid type errors
        self.light_widget.setValue(int(value))

    def add_light(self, increment=10):
        self.set_light(self.light_widget.value() + increment)

    def toggle_polygons(self, value):
        for item, shape in self.items_to_shapes.items():
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def load_file(self, file_path=None, clear_prev_shapes=False, preserve_zoom=False):
        """Load the specified file, or the last opened file if None."""
        # Save tracking info before reset
        temp_prev_shapes = self.prev_frame_shapes if hasattr(self, 'prev_frame_shapes') and not clear_prev_shapes else []
        temp_tracking_mode = self.continuous_tracking_mode if hasattr(self, 'continuous_tracking_mode') else False
        
        # Save zoom state before reset if requested
        if preserve_zoom and hasattr(self, 'zoom_widget'):
            saved_zoom_value = self.zoom_widget.value()
            saved_zoom_mode = self.zoom_mode
            saved_h_scroll = self.scroll_bars[Qt.Horizontal].value()
            saved_v_scroll = self.scroll_bars[Qt.Vertical].value()
            saved_h_max = self.scroll_bars[Qt.Horizontal].maximum()
            saved_v_max = self.scroll_bars[Qt.Vertical].maximum()
        else:
            saved_zoom_value = None
        
        self.reset_state()
        
        # Restore tracking info after reset
        self.prev_frame_shapes = temp_prev_shapes
        self.continuous_tracking_mode = temp_tracking_mode
        
        self.canvas.setEnabled(False)
        if file_path is None:
            file_path = self.settings.get(SETTING_FILENAME)
        # Make sure that filePath is a regular python string, rather than QString
        file_path = ustr(file_path)

        # Fix bug: An  index error after select a directory when open a new file.
        unicode_file_path = ustr(file_path)
        unicode_file_path = os.path.abspath(unicode_file_path)
        # Tzutalin 20160906 : Add file list and dock to move faster
        # Highlight the file item
        if unicode_file_path and self.file_list_widget.count() > 0:
            if unicode_file_path in self.m_img_list:
                index = self.m_img_list.index(unicode_file_path)
                file_widget_item = self.file_list_widget.item(index)
                file_widget_item.setSelected(True)
            else:
                self.file_list_widget.clear()
                self.m_img_list.clear()

        if unicode_file_path and os.path.exists(unicode_file_path):
            if LabelFile.is_label_file(unicode_file_path):
                try:
                    self.label_file = LabelFile(unicode_file_path)
                except LabelFileError as e:
                    self.error_message(u'Error opening file',
                                       (u"<p><b>%s</b></p>"
                                        u"<p>Make sure <i>%s</i> is a valid label file.")
                                       % (e, unicode_file_path))
                    self.status("Error reading %s" % unicode_file_path)
                    
                    return False
                self.image_data = self.label_file.image_data
                self.line_color = QColor(*self.label_file.lineColor)
                self.fill_color = QColor(*self.label_file.fillColor)
                self.canvas.verified = self.label_file.verified
            else:
                # Load image:
                # read data first and store for saving into label file.
                self.image_data = read(unicode_file_path, None)
                self.label_file = None
                self.canvas.verified = False

            if isinstance(self.image_data, QImage):
                image = self.image_data
            else:
                image = QImage.fromData(self.image_data)
            if image.isNull():
                self.error_message(u'Error opening file',
                                   u"<p>Make sure <i>%s</i> is a valid image file." % unicode_file_path)
                self.status("Error reading %s" % unicode_file_path)
                return False
            self.status("Loaded %s" % os.path.basename(unicode_file_path))
            self.image = image
            self.file_path = unicode_file_path
            self.canvas.load_pixmap(QPixmap.fromImage(image))
            if self.label_file:
                self.load_labels(self.label_file.shapes)
            self.set_clean()
            self.canvas.setEnabled(True)
            
            # Restore zoom state if requested, otherwise use initial scale
            if preserve_zoom and saved_zoom_value is not None:
                self.zoom_mode = saved_zoom_mode
                self.zoom_widget.setValue(saved_zoom_value)
                self.paint_canvas()
                # Restore scroll positions after a brief delay to ensure proper layout
                QTimer.singleShot(50, lambda: self.restore_scroll_positions(
                    saved_h_scroll, saved_v_scroll, saved_h_max, saved_v_max))
            else:
                self.adjust_scale(initial=True)
                self.paint_canvas()
            
            self.add_recent_file(self.file_path)
            self.toggle_actions(True)
            self.show_bounding_box_from_annotation_file(self.file_path)
            
            # Quick ID Selectorの不足ラベルを更新
            if hasattr(self, 'quick_id_selector') and self.quick_id_selector.isVisible():
                self.quick_id_selector.update_missing_labels()

            counter = self.counter_str()
            self.setWindowTitle(__appname__ + ' ' + file_path + ' ' + counter)

            # Default : select last item if there is at least one item
            # Disabled auto-selection on frame change
            # if self.label_list.count():
            #     self.label_list.setCurrentItem(self.label_list.item(self.label_list.count() - 1))
            #     self.label_list.item(self.label_list.count() - 1).setSelected(True)

            self.canvas.setFocus(True)
            
            
            return True
        return False

    def counter_str(self):
        """
        Converts image counter to string representation.
        """
        return '[{} / {}]'.format(self.cur_img_idx + 1, self.img_count)

    def show_bounding_box_from_annotation_file(self, file_path):
        
        if self.default_save_dir is not None:
            basename = os.path.basename(os.path.splitext(file_path)[0])
            xml_path = os.path.join(self.default_save_dir, basename + XML_EXT)
            txt_path = os.path.join(self.default_save_dir, basename + TXT_EXT)
            json_path = os.path.join(self.default_save_dir, basename + JSON_EXT)

            """Annotation file priority:
            PascalXML > YOLO
            """
            if os.path.isfile(xml_path):
                self.load_pascal_xml_by_filename(xml_path)
            elif os.path.isfile(txt_path):
                self.load_yolo_txt_by_filename(txt_path)
            elif os.path.isfile(json_path):
                self.load_create_ml_json_by_filename(json_path, file_path)

        else:
            xml_path = os.path.splitext(file_path)[0] + XML_EXT
            txt_path = os.path.splitext(file_path)[0] + TXT_EXT
            json_path = os.path.splitext(file_path)[0] + JSON_EXT

            if os.path.isfile(xml_path):
                self.load_pascal_xml_by_filename(xml_path)
            elif os.path.isfile(txt_path):
                self.load_yolo_txt_by_filename(txt_path)
            elif os.path.isfile(json_path):
                self.load_create_ml_json_by_filename(json_path, file_path)
            

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoom_mode != self.MANUAL_ZOOM:
            self.adjust_scale()
        super(MainWindow, self).resizeEvent(event)

    def paint_canvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoom_widget.value()
        self.canvas.overlay_color = self.light_widget.color()
        self.canvas.label_font_size = int(0.02 * max(self.image.width(), self.image.height()))
        self.canvas.adjustSize()
        self.canvas.update()

    def adjust_scale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoom_mode]()
        self.zoom_widget.setValue(int(100 * value))

    def scale_fit_window(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scale_fit_width(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()
    
    def restore_scroll_positions(self, h_value, v_value, prev_h_max, prev_v_max):
        """Restore scroll positions after loading a new image."""
        h_bar = self.scroll_bars[Qt.Horizontal]
        v_bar = self.scroll_bars[Qt.Vertical]
        
        # Calculate the relative position from the previous state
        if prev_h_max > 0:
            h_ratio = h_value / prev_h_max if prev_h_max > 0 else 0
            new_h_value = int(h_ratio * h_bar.maximum())
            h_bar.setValue(new_h_value)
        
        if prev_v_max > 0:
            v_ratio = v_value / prev_v_max if prev_v_max > 0 else 0
            new_v_value = int(v_ratio * v_bar.maximum())
            v_bar.setValue(new_v_value)

    def closeEvent(self, event):
        if not self.may_continue():
            event.ignore()
        settings = self.settings
        # If it loads images from dir, don't load it at the beginning
        if self.dir_name is None:
            settings[SETTING_FILENAME] = self.file_path if self.file_path else ''
        else:
            settings[SETTING_FILENAME] = ''

        settings[SETTING_WIN_SIZE] = self.size()
        settings[SETTING_WIN_POSE] = self.pos()
        settings[SETTING_WIN_STATE] = self.saveState()
        settings[SETTING_LINE_COLOR] = self.line_color
        settings[SETTING_FILL_COLOR] = self.fill_color
        settings[SETTING_RECENT_FILES] = self.recent_files
        settings[SETTING_ADVANCE_MODE] = not self._beginner
        if self.default_save_dir and os.path.exists(self.default_save_dir):
            settings[SETTING_SAVE_DIR] = ustr(self.default_save_dir)
        else:
            settings[SETTING_SAVE_DIR] = ''

        if self.last_open_dir and os.path.exists(self.last_open_dir):
            settings[SETTING_LAST_OPEN_DIR] = self.last_open_dir
        else:
            settings[SETTING_LAST_OPEN_DIR] = ''

        settings[SETTING_AUTO_SAVE] = self.auto_saving.isChecked()
        settings[SETTING_SINGLE_CLASS] = self.single_class_mode.isChecked()
        settings[SETTING_PAINT_LABEL] = self.display_label_option.isChecked()
        settings[SETTING_DRAW_SQUARE] = self.draw_squares_option.isChecked()
        settings[SETTING_LABEL_FILE_FORMAT] = self.label_file_format
        settings.save()

    def load_recent(self, filename):
        if self.may_continue():
            self.load_file(filename)

    def scan_all_images(self, folder_path):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relative_path = os.path.join(root, file)
                    path = ustr(os.path.abspath(relative_path))
                    images.append(path)
        natural_sort(images, key=lambda x: x.lower())
        return images

    def change_save_dir_dialog(self, _value=False):
        if self.default_save_dir is not None:
            path = ustr(self.default_save_dir)
        else:
            path = '.'

        dir_path = ustr(QFileDialog.getExistingDirectory(self,
                                                         '%s - Save annotations to the directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                         | QFileDialog.DontResolveSymlinks))

        if dir_path is not None and len(dir_path) > 1:
            self.default_save_dir = dir_path

        self.show_bounding_box_from_annotation_file(self.file_path)

        self.statusBar().showMessage('%s . Annotation will be saved to %s' %
                                     ('Change saved folder', self.default_save_dir))
        self.statusBar().show()


    def open_annotation_dialog(self, _value=False):
        if self.file_path is None:
            self.statusBar().showMessage('Please select image first')
            self.statusBar().show()
            return

        path = os.path.dirname(ustr(self.file_path))\
            if self.file_path else '.'
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            filters = "Open Annotation XML file (%s)" % ' '.join(['*.xml'])
            filename = ustr(QFileDialog.getOpenFileName(self, '%s - Choose a xml file' % __appname__, path, filters))
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]
            self.load_pascal_xml_by_filename(filename)

        elif self.label_file_format == LabelFileFormat.CREATE_ML:
            
            filters = "Open Annotation JSON file (%s)" % ' '.join(['*.json'])
            filename = ustr(QFileDialog.getOpenFileName(self, '%s - Choose a json file' % __appname__, path, filters))
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]

            self.load_create_ml_json_by_filename(filename, self.file_path)         
        

    def open_dir_dialog(self, _value=False, dir_path=None, silent=False):
        if not self.may_continue():
            return

        default_open_dir_path = dir_path if dir_path else '.'
        if self.last_open_dir and os.path.exists(self.last_open_dir):
            default_open_dir_path = self.last_open_dir
        else:
            default_open_dir_path = os.path.dirname(self.file_path) if self.file_path else '.'
        if silent != True:
            target_dir_path = ustr(QFileDialog.getExistingDirectory(self,
                                                                    '%s - Open Directory' % __appname__, default_open_dir_path,
                                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))
        else:
            target_dir_path = ustr(default_open_dir_path)
        self.last_open_dir = target_dir_path
        self.import_dir_images(target_dir_path)
        # Don't override command-line specified save dir
        # self.default_save_dir = target_dir_path
        if self.file_path:
            self.show_bounding_box_from_annotation_file(file_path=self.file_path)

    def import_dir_images(self, dir_path):
        if not self.may_continue() or not dir_path:
            return

        self.last_open_dir = dir_path
        self.dir_name = dir_path
        self.file_path = None
        self.file_list_widget.clear()
        self.m_img_list = self.scan_all_images(dir_path)
        self.img_count = len(self.m_img_list)
        self.open_next_image()
        for imgPath in self.m_img_list:
            item = QListWidgetItem(imgPath)
            self.file_list_widget.addItem(item)

    def verify_image(self, _value=False):
        # Proceeding next image without dialog if having any label
        if self.file_path is not None:
            try:
                self.label_file.toggle_verify()
            except AttributeError:
                # If the labelling file does not exist yet, create if and
                # re-save it with the verified attribute.
                self.save_file()
                if self.label_file is not None:
                    self.label_file.toggle_verify()
                else:
                    return

            self.canvas.verified = self.label_file.verified
            self.paint_canvas()
            self.save_file()

    def open_prev_image(self, _value=False):
        # Proceeding prev image without dialog if having any label
        if self.auto_saving.isChecked():
            if self.default_save_dir is not None:
                if self.dirty is True:
                    self.save_file()
            else:
                self.change_save_dir_dialog()
                return

        if not self.may_continue():
            return

        if self.img_count <= 0:
            return

        if self.file_path is None:
            return

        if self.cur_img_idx - 1 >= 0:
            self.cur_img_idx -= 1
            filename = self.m_img_list[self.cur_img_idx]
            if filename:
                # When going to previous frame, load with clear_prev_shapes=True and preserve_zoom=True
                print(f"[Navigation] Going to previous frame {self.cur_img_idx}")
                self.load_file(filename, clear_prev_shapes=True, preserve_zoom=True)

    def open_next_image(self, _value=False):
        # Proceeding next image without dialog if having any label
        if self.auto_saving.isChecked():
            if self.default_save_dir is not None:
                if self.dirty is True:
                    self.save_file()
            else:
                self.change_save_dir_dialog()
                return

        if not self.may_continue():
            return

        if self.img_count <= 0:
            return
        
        if not self.m_img_list:
            return

        filename = None
        if self.file_path is None:
            filename = self.m_img_list[0]
            self.cur_img_idx = 0
        else:
            if self.cur_img_idx + 1 < self.img_count:
                self.cur_img_idx += 1
                filename = self.m_img_list[self.cur_img_idx]

        if filename:
            # Just load the file normally with preserve_zoom=True
            self.load_file(filename, preserve_zoom=True)

    def open_file(self, _value=False):
        if not self.may_continue():
            return
        path = os.path.dirname(ustr(self.file_path)) if self.file_path else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename,_ = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.cur_img_idx = 0
            self.img_count = 1
            self.load_file(filename)

    def save_file(self, _value=False):
        if self.default_save_dir is not None and len(ustr(self.default_save_dir)):
            if self.file_path:
                image_file_name = os.path.basename(self.file_path)
                saved_file_name = os.path.splitext(image_file_name)[0]
                saved_path = os.path.join(ustr(self.default_save_dir), saved_file_name)
                self._save_file(saved_path)
        else:
            image_file_dir = os.path.dirname(self.file_path)
            image_file_name = os.path.basename(self.file_path)
            saved_file_name = os.path.splitext(image_file_name)[0]
            saved_path = os.path.join(image_file_dir, saved_file_name)
            self._save_file(saved_path if self.label_file
                            else self.save_file_dialog(remove_ext=False))

    def save_file_as(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        self._save_file(self.save_file_dialog())

    def save_file_dialog(self, remove_ext=True):
        caption = '%s - Choose File' % __appname__
        filters = 'File (*%s)' % LabelFile.suffix
        open_dialog_path = self.current_path()
        dlg = QFileDialog(self, caption, open_dialog_path, filters)
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        filename_without_extension = os.path.splitext(self.file_path)[0]
        dlg.selectFile(filename_without_extension)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            full_file_path = ustr(dlg.selectedFiles()[0])
            if remove_ext:
                return os.path.splitext(full_file_path)[0]  # Return file path without the extension.
            else:
                return full_file_path
        return ''

    def _save_file(self, annotation_file_path):
        if annotation_file_path and self.save_labels(annotation_file_path):
            self.set_clean()
            self.statusBar().showMessage('Saved to  %s' % annotation_file_path)
            self.statusBar().show()
            

    def close_file(self, _value=False):
        if not self.may_continue():
            return
        self.reset_state()
        self.set_clean()
        self.toggle_actions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    def delete_image(self):
        delete_path = self.file_path
        if delete_path is not None:
            idx = self.cur_img_idx
            if os.path.exists(delete_path):
                os.remove(delete_path)
            self.import_dir_images(self.last_open_dir)
            if self.img_count > 0:
                self.cur_img_idx = min(idx, self.img_count - 1)
                filename = self.m_img_list[self.cur_img_idx]
                self.load_file(filename)
            else:
                self.close_file()

    def reset_all(self):
        self.settings.reset()
        self.close()
        process = QProcess()
        process.startDetached(os.path.abspath(__file__))

    def may_continue(self):
        if not self.dirty:
            return True
        else:
            discard_changes = self.discard_changes_dialog()
            if discard_changes == QMessageBox.No:
                return True
            elif discard_changes == QMessageBox.Yes:
                self.save_file()
                return True
            else:
                return False

    def discard_changes_dialog(self):
        yes, no, cancel = QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel
        msg = u'You have unsaved changes, would you like to save them and proceed?\nClick "No" to discard all changes.'
        return QMessageBox.warning(self, u'Attention', msg, yes | no | cancel)

    def error_message(self, title, message):
        return QMessageBox.critical(self, title,
                                    '<p><b>%s</b></p>%s' % (title, message))

    def current_path(self):
        return os.path.dirname(self.file_path) if self.file_path else '.'

    def choose_color1(self):
        color = self.color_dialog.getColor(self.line_color, u'Choose line color',
                                           default=DEFAULT_LINE_COLOR)
        if color:
            self.line_color = color
            Shape.line_color = color
            self.canvas.set_drawing_color(color)
            self.canvas.update()
            self.set_dirty()

    def delete_selected_shape(self):
        if not self.canvas.selected_shape:
            return
        
        # Get the shape to delete and its index
        shape_to_delete = self.canvas.selected_shape
        shape_index = self.canvas.shapes.index(shape_to_delete)
        
        # Create and execute DeleteShapeCommand
        from libs.undo.commands.shape_commands import DeleteShapeCommand
        delete_cmd = DeleteShapeCommand(self.file_path, shape_index, shape_to_delete)
        
        if self.undo_manager.execute_command(delete_cmd):
            # Update UI
            if self.no_shapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)
            
            # Quick ID Selectorの不足ラベルを更新
            if hasattr(self, 'quick_id_selector') and self.quick_id_selector.isVisible():
                self.quick_id_selector.update_missing_labels()

    def choose_shape_line_color(self):
        color = self.color_dialog.getColor(self.line_color, u'Choose Line Color',
                                           default=DEFAULT_LINE_COLOR)
        if color:
            self.canvas.selected_shape.line_color = color
            self.canvas.update()
            self.set_dirty()

    def choose_shape_fill_color(self):
        color = self.color_dialog.getColor(self.fill_color, u'Choose Fill Color',
                                           default=DEFAULT_FILL_COLOR)
        if color:
            self.canvas.selected_shape.fill_color = color
            self.canvas.update()
            self.set_dirty()

    def copy_shape(self):
        if self.canvas.selected_shape is None:
            # True if one accidentally touches the left mouse button before releasing
            return
        self.canvas.end_move(copy=True)
        self.add_label(self.canvas.selected_shape)
        self.set_dirty()

    def move_shape(self):
        self.canvas.end_move(copy=False)
        self.set_dirty()

    def load_predefined_classes(self, predef_classes_file):
        if os.path.exists(predef_classes_file) is True:
            with codecs.open(predef_classes_file, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if self.label_hist is None:
                        self.label_hist = [line]
                    else:
                        self.label_hist.append(line)

    def load_pascal_xml_by_filename(self, xml_path):
        if self.file_path is None:
            return
        if os.path.isfile(xml_path) is False:
            return

        self.set_format(FORMAT_PASCALVOC)

        t_voc_parse_reader = PascalVocReader(xml_path)
        shapes = t_voc_parse_reader.get_shapes()
        self.load_labels(shapes)
        self.canvas.verified = t_voc_parse_reader.verified

    def load_yolo_txt_by_filename(self, txt_path):
        if self.file_path is None:
            return
        if os.path.isfile(txt_path) is False:
            return

        self.set_format(FORMAT_YOLO)
        t_yolo_parse_reader = YoloReader(txt_path, self.image)
        shapes = t_yolo_parse_reader.get_shapes()
        # print(shapes)
        self.load_labels(shapes)
        self.canvas.verified = t_yolo_parse_reader.verified

    def load_create_ml_json_by_filename(self, json_path, file_path):
        if self.file_path is None:
            return
        if os.path.isfile(json_path) is False:
            return

        self.set_format(FORMAT_CREATEML)

        create_ml_parse_reader = CreateMLReader(json_path, file_path)
        shapes = create_ml_parse_reader.get_shapes()
        self.load_labels(shapes)
        self.canvas.verified = create_ml_parse_reader.verified

    def copy_previous_bounding_boxes(self):
        current_index = self.m_img_list.index(self.file_path)
        if current_index - 1 >= 0:
            prev_file_path = self.m_img_list[current_index - 1]
            self.show_bounding_box_from_annotation_file(prev_file_path)
            self.save_file()

    def toggle_paint_labels_option(self):
        for shape in self.canvas.shapes:
            shape.paint_label = self.display_label_option.isChecked()
        self.canvas.repaint()
    
    def toggle_bounding_box_display(self, state):
        """Bounding Boxの表示/非表示を切り替え"""
        show_bb = state == Qt.Checked
        # 各shapeの表示状態を制御（canvasで実装する必要がある）
        self.canvas.show_bounding_boxes = show_bb
        self.canvas.repaint()
    
    def toggle_id_display(self, state):
        """IDの表示/非表示を切り替え"""
        show_id = state == Qt.Checked
        for shape in self.canvas.shapes:
            shape.paint_id = show_id
        self.canvas.repaint()

    
    def get_current_state(self):
        """現在の状態を取得（shapes情報）"""
        state = {
            'file_path': self.file_path,
            'shapes': []
        }
        
        for shape in self.canvas.shapes:
            shape_data = {
                'label': shape.label if shape.label else "",
                'points': [(p.x(), p.y()) for p in shape.points],
                'difficult': getattr(shape, 'difficult', False),
                'paint_label': getattr(shape, 'paint_label', False),
                'paint_id': getattr(shape, 'paint_id', True),
                'line_color': shape.line_color.getRgb() if hasattr(shape, 'line_color') and shape.line_color else None,
                'fill_color': shape.fill_color.getRgb() if hasattr(shape, 'fill_color') and shape.fill_color else None,
            }
            # Track IDがあれば保存
            if hasattr(shape, 'is_tracked'):
                shape_data['is_tracked'] = shape.is_tracked
            state['shapes'].append(shape_data)
        
        return state
    
    def undo_action(self):
        """Undo the last action"""
        print("[DEBUG] undo_action called")
        print(f"[DEBUG] Can undo: {self.undo_manager.can_undo()}")
        print(f"[DEBUG] History: {self.undo_manager.get_history_info()}")
        
        if self.undo_manager.undo():
            print("[DEBUG] Undo successful")
            self.canvas.load_shapes(self.canvas.shapes)
            self.canvas.repaint()
            
            # Update label list
            self.label_list.clear()
            self.shapes_to_items.clear()
            self.items_to_shapes.clear()
            for shape in self.canvas.shapes:
                self.add_label(shape)
            
            self.statusBar().showMessage('Undo successful', 2000)
        else:
            print("[DEBUG] Undo failed or nothing to undo")
            self.statusBar().showMessage('Nothing to undo', 2000)
    
    def redo_action(self):
        """Redo the last undone action"""
        print("[DEBUG] redo_action called")
        print(f"[DEBUG] Can redo: {self.undo_manager.can_redo()}")
        print(f"[DEBUG] History before redo: {self.undo_manager.get_history_info()}")
        print(f"[DEBUG] Canvas shapes before redo: {len(self.canvas.shapes)} shapes")
        
        if self.undo_manager.redo():
            print("[DEBUG] Redo successful")
            print(f"[DEBUG] Canvas shapes after redo: {len(self.canvas.shapes)} shapes")
            print(f"[DEBUG] History after redo: {self.undo_manager.get_history_info()}")
            
            # Reload shapes and update UI
            self.canvas.load_shapes(self.canvas.shapes)
            self.canvas.repaint()
            
            # Update label list by clearing and re-adding all items
            # Clear existing label list
            self.label_list.clear()
            self.shapes_to_items.clear()
            self.items_to_shapes.clear()
            
            # Re-add all shapes to label list
            for shape in self.canvas.shapes:
                self.add_label(shape)
            
            self.statusBar().showMessage('Redo successful', 2000)
        else:
            print("[DEBUG] Redo failed or nothing to redo")
            self.statusBar().showMessage('Nothing to redo', 2000)
    
    def toggle_draw_square(self):
        self.canvas.set_drawing_shape_to_square(self.draw_squares_option.isChecked())
    
    def toggle_continuous_tracking(self, state):
        """Toggle continuous tracking mode."""
        self.continuous_tracking_mode = (state == Qt.Checked)
        
        if self.continuous_tracking_mode:
            # If turning on tracking mode, assign IDs to current shapes
            if self.canvas.shapes:
                for shape in self.canvas.shapes:
                    if not hasattr(shape, 'is_tracked'):
                        shape.is_tracked = False
        else:
            # If turning off tracking mode, clear prev_frame_shapes
            self.prev_frame_shapes = []
    
    def toggle_click_change_label(self, state):
        """Toggle click-to-change-label mode."""
        self.click_change_label_mode = (state == Qt.Checked)
    
    def toggle_bb_duplication(self, state):
        """Toggle BB duplication mode."""
        self.bb_duplication_mode = (state == Qt.Checked)
        self.bb_dup_frame_count.setEnabled(self.bb_duplication_mode)
        self.bb_dup_iou_threshold.setEnabled(self.bb_duplication_mode)
        self.bb_dup_overwrite_checkbox.setEnabled(self.bb_duplication_mode)
    
    def update_overwrite_checkbox_text(self):
        """Update the overwrite checkbox text with current IOU threshold."""
        threshold = self.bb_dup_iou_threshold.value()
        self.bb_dup_overwrite_checkbox.setText(f"重複時に上書き (IOU>{threshold:.1f})")
    
    def toggle_quick_id_selector(self):
        """Quick ID Selectorの表示/非表示を切り替え"""
        if self.quick_id_selector.isVisible():
            self.quick_id_selector.hide()
        else:
            self.quick_id_selector.show()
    
    def select_quick_id(self, id_str):
        """Quick IDを選択"""
        if id_str != self.current_quick_id:
            self.current_quick_id = id_str
            self.quick_id_selector.set_current_id(id_str)
            self.update_current_id_display()
            self.apply_quick_id_to_selected_shape()
    
    def next_quick_id(self):
        """次のIDに切り替え"""
        current_num = int(self.current_quick_id)
        max_ids = len(self.label_hist)
        next_num = current_num + 1 if current_num < max_ids else 1
        self.select_quick_id(str(next_num))
    
    def prev_quick_id(self):
        """前のIDに切り替え"""
        current_num = int(self.current_quick_id)
        max_ids = len(self.label_hist)
        prev_num = current_num - 1 if current_num > 1 else max_ids
        self.select_quick_id(str(prev_num))
    
    def on_quick_id_selected(self, id_str):
        """Quick ID Selectorからのシグナルを受信"""
        self.current_quick_id = id_str
        
        # ステータスバーの表示を更新
        self.update_current_id_display()
        
        print(f"[QuickID] ID selected from selector: {id_str}")
        
        # デフォルトラベルコンボボックスも同期更新
        try:
            index = int(id_str) - 1
            if 0 <= index < len(self.label_hist):
                self.default_label_combo_box.cb.setCurrentIndex(index)
                self.default_label = self.label_hist[index]
        except (ValueError, IndexError):
            pass
        
        # 選択中のBBにIDを適用
        self.apply_quick_id_to_selected_shape()
    
    def update_current_id_display(self):
        """ステータスバーの現在ID表示を更新"""
        if hasattr(self, 'label_current_id'):
            # 実際のクラス名を取得して表示
            class_name = self.get_class_name_for_quick_id(self.current_quick_id)
            self.label_current_id.setText(f'{class_name}')
            print(f"[QuickID] Status bar updated: {class_name}")
    
    def apply_quick_id_to_selected_shape(self):
        """選択中のBBに現在のQuick IDを適用"""
        if self.canvas.selected_shape:
            shape = self.canvas.selected_shape
            
            # Quick IDに対応する実際のクラス名を取得（IDサフィックスなし）
            new_label = self.get_class_name_for_quick_id(self.current_quick_id)
            
            # ラベルが変更される場合のみ処理
            old_label = shape.label
            if old_label != new_label:
                # 連続ID付けモードの場合はマルチフレーム操作として処理
                if self.continuous_tracking_mode:
                    print(f"[QuickID] Starting continuous ID assignment: {old_label} -> {new_label}")
                    
                    # マルチフレーム操作として処理
                    self.apply_quick_id_with_propagation(shape, new_label, old_label)
                else:
                    # 通常モード: 単一フレームの変更のみ
                    
                    # ラベルを更新
                    shape.label = new_label
                    
                    # リストアイテムも更新
                    if shape in self.shapes_to_items:
                        item = self.shapes_to_items[shape]
                        item.setText(new_label)
                    
                    # UIを更新
                    self.set_dirty()
                    self.update_combo_box()
                    
                    print(f"[QuickID] Applied ID {self.current_quick_id} to shape: {old_label} -> {new_label}")
        else:
            print("[QuickID] No shape selected for ID application")
    
    def apply_quick_id_with_propagation(self, shape, new_label, old_label):
        """連続ID付けモードでラベルを適用し、後続フレームに伝播させる（マルチフレーム操作）"""
        if not self.continuous_tracking_mode or not shape:
            return
        
        # 現在のフレーム情報を保存
        current_file = self.file_path
        current_idx = self.cur_img_idx
        
        
        # Apply label change to current frame
        shape.label = new_label
        
        # リストアイテムも更新
        if shape in self.shapes_to_items:
            item = self.shapes_to_items[shape]
            item.setText(new_label)
        
        # UIを更新
        self.set_dirty()
        self.update_combo_box()
        
        # 現在のフレームを保存（必要なら）
        if self.auto_saving.isChecked() and self.default_save_dir:
            self.save_file()
        
        print(f"[QuickID] Applied to current frame: {old_label} -> {new_label}")
        
        # 後続フレームに伝播
        frames_processed = self._propagate_label_to_subsequent_frames_multi(shape, new_label, "QuickID")
        
        # マルチフレーム操作を保存
        
        # 元のフレームに戻る
        if self.file_path != current_file:
            self.load_file(current_file, preserve_zoom=True)
        
        # ステータスメッセージ
        if frames_processed > 0:
            self.statusBar().showMessage(f'連続ID付けが完了しました。{frames_processed + 1}フレームに適用しました。', 3000)
        else:
            self.statusBar().showMessage(f'IDを変更しました: {old_label} -> {new_label}', 3000)
    
    def get_class_name_for_quick_id(self, quick_id):
        """Quick IDに対応するクラス名を取得（classes.txtから直接）"""
        try:
            id_num = int(quick_id)
            if 1 <= id_num <= len(self.label_hist):
                # 定義されたクラス名をそのまま使用（IDサフィックスなし）
                class_name = self.label_hist[id_num - 1]
                return class_name
            else:
                # 範囲外の場合はデフォルト
                return "object"
        except (ValueError, IndexError):
            return "object"
    
    def calculate_iou(self, box1, box2):
        """Calculate Intersection over Union between two bounding boxes."""
        # Get coordinates from all points to find bounding box
        x1_coords = [p.x() for p in box1]
        y1_coords = [p.y() for p in box1]
        x2_coords = [p.x() for p in box2]
        y2_coords = [p.y() for p in box2]
        
        x1_min, x1_max = min(x1_coords), max(x1_coords)
        y1_min, y1_max = min(y1_coords), max(y1_coords)
        x2_min, x2_max = min(x2_coords), max(x2_coords)
        y2_min, y2_max = min(y2_coords), max(y2_coords)
        
        # Calculate intersection area
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Calculate union area
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def duplicate_bb_to_subsequent_frames(self, source_shape):
        """Duplicate bounding box to subsequent frames."""
        if not self.bb_duplication_mode or not source_shape:
            return
        
        print(f"[BB Duplication] Starting BB duplication from frame {self.cur_img_idx}")
        print(f"[BB Duplication] Source shape points: {[(p.x(), p.y()) for p in source_shape.points]}")
        
        # Get number of frames to duplicate to
        num_frames = self.bb_dup_frame_count.value()
        overwrite_mode = self.bb_dup_overwrite_checkbox.isChecked()
        
        # Save current state - we need to save the file first to ensure current BB is saved
        if self.auto_saving.isChecked() and self.default_save_dir:
            self.save_file()
        
        current_file = self.file_path
        current_idx = self.cur_img_idx
        
        
        frames_processed = 0
        frames_with_conflicts = 0
        
        # Create progress dialog
        progress = QProgressDialog("BB複製処理中...", "キャンセル", 0, num_frames, self)
        progress.setWindowTitle("処理中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        for i in range(1, num_frames + 1):
            if progress.wasCanceled():
                break
            
            target_idx = current_idx + i
            if target_idx >= self.img_count:
                break
            
            progress.setValue(i)
            progress.setLabelText(f"フレーム {target_idx + 1}/{self.img_count} を処理中...")
            
            # Load target frame
            target_file = self.m_img_list[target_idx]
            
            # Load target file
            self.load_file(target_file, preserve_zoom=True)
            
            # Check for overlapping shapes
            shapes_to_remove = []
            should_add_shape = True
            
            for existing_shape in self.canvas.shapes:
                # Only check IoU if both shapes have 4 points (rectangles)
                if len(source_shape.points) == 4 and len(existing_shape.points) == 4:
                    iou = self.calculate_iou(source_shape.points, existing_shape.points)
                    print(f"[BB Duplication] Checking IOU with existing shape: {iou:.3f}")
                    if iou >= self.bb_dup_iou_threshold.value():
                        if overwrite_mode:
                            # Mark shape for removal
                            shapes_to_remove.append(existing_shape)
                            print(f"[BB Duplication] Frame {target_idx}: Overwriting existing BB (IOU={iou:.2f})")
                        else:
                            # Skip this frame if any overlap found
                            should_add_shape = False
                            frames_with_conflicts += 1
                            print(f"[BB Duplication] Frame {target_idx}: Skipping due to overlap (IOU={iou:.2f})")
                            break  # In skip mode, one overlap is enough to skip
            
            # Perform modifications
            modified = False
            
            # Remove all overlapping shapes if in overwrite mode
            if shapes_to_remove:
                for shape_to_remove in shapes_to_remove:
                    self.canvas.shapes.remove(shape_to_remove)
                    # Remove from label list
                    for i in range(self.label_list.count()):
                        item = self.label_list.item(i)
                        if item and item in self.items_to_shapes:
                            if self.items_to_shapes[item] == shape_to_remove:
                                self.label_list.takeItem(i)
                                del self.items_to_shapes[item]
                                del self.shapes_to_items[shape_to_remove]
                                break
                modified = True
            
            # Add duplicated shape
            if should_add_shape:
                # Create new shape with same properties
                new_shape = Shape()
                new_shape.label = source_shape.label
                new_shape.points = source_shape.points[:]
                new_shape.close()
                new_shape.difficult = source_shape.difficult if hasattr(source_shape, 'difficult') else False
                new_shape.line_color = source_shape.line_color
                new_shape.fill_color = source_shape.fill_color
                new_shape.paint_label = self.display_label_option.isChecked()
                
                # Add shape to canvas and label list
                self.canvas.shapes.append(new_shape)
                self.add_label(new_shape)
                self.set_dirty()
                frames_processed += 1
                modified = True
                
                # Save the file
                if self.auto_saving.isChecked() and self.default_save_dir:
                    self.save_file()
            
        
        progress.close()
        
        # Return to original frame
        self.load_file(current_file, preserve_zoom=True)
        
        # Show status message
        message = f"BB複製が完了しました。{frames_processed}フレームに複製"
        if frames_with_conflicts > 0:
            message += f"、{frames_with_conflicts}フレームをスキップ"
        message += "しました。"
        self.statusBar().showMessage(message, 5000)
    
    def on_shape_clicked(self):
        """Handle shape click event for label change."""
        if self.click_change_label_mode:
            self.apply_label_to_selected_shape()
    
    
    def apply_label_to_selected_shape(self):
        """Apply label to the selected shape based on current settings."""
        if not self.click_change_label_mode:
            return
            
        if self._applying_label:
            return
            
        shape = self.canvas.selected_shape
        if not shape:
            return
        
        # Get the current item in label list
        item = self.shapes_to_items.get(shape)
        if not item:
            return
        
        # Set flag to prevent recursion
        self._applying_label = True
        
        # Store the old label
        old_label = shape.label
        
        # Determine the new label
        new_label = None
        if self.use_default_label_checkbox.isChecked() and self.default_label:
            new_label = self.default_label
        else:
            # Show label dialog
            text = self.label_dialog.pop_up(item.text())
            if text is not None:
                new_label = text
        
        # If label didn't change or was cancelled, return
        if new_label is None or new_label == old_label:
            self._applying_label = False
            return
        
        # If continuous tracking mode is ON, use multi-frame operation
        if self.continuous_tracking_mode:
            print(f"[ClickChange] Starting continuous label change: {old_label} -> {new_label}")
            self.apply_label_with_propagation(shape, new_label, old_label, item)
        else:
            # Normal single-frame operation - use Command pattern
            print(f"[DEBUG] apply_label_to_selected_shape: Changing label from '{old_label}' to '{new_label}'")
            
            # Get shape index
            shape_index = self.canvas.shapes.index(shape) if shape in self.canvas.shapes else -1
            if shape_index >= 0:
                # Create and execute ChangeLabelCommand
                from libs.undo.commands.label_commands import ChangeLabelCommand
                change_cmd = ChangeLabelCommand(self.file_path, shape_index, old_label, new_label)
                result = self.undo_manager.execute_command(change_cmd)
                print(f"[DEBUG] ChangeLabelCommand executed from click: {result}")
                print(f"[DEBUG] UndoManager state: {self.undo_manager}")
            else:
                print(f"[DEBUG] Shape not found in canvas.shapes for click label change")
        
        # Reset flag
        self._applying_label = False
    
    def apply_label_with_propagation(self, shape, new_label, old_label, item):
        """Apply label change with propagation as a multi-frame operation."""
        if not self.continuous_tracking_mode or not shape:
            return
        
        # 現在のフレーム情報を保存
        current_file = self.file_path
        current_idx = self.cur_img_idx
        
        
        # Apply label
        shape.label = new_label
        item.setText(new_label)
        
        # Update shape color based on new label
        shape.line_color = generate_color_by_text(shape.label)
        item.setBackground(generate_color_by_text(shape.label))
        
        # Mark as dirty and update
        self.set_dirty()
        self.canvas.load_shapes(self.canvas.shapes)
        self.update_combo_box()
        
        # 現在のフレームを保存（必要なら）
        if self.auto_saving.isChecked() and self.default_save_dir:
            self.save_file()
        
        print(f"[ClickChange] Applied to current frame: {old_label} -> {new_label}")
        
        # 後続フレームに伝播
        frames_processed = self._propagate_label_to_subsequent_frames_multi(shape, new_label, "ClickChange")
        
        # マルチフレーム操作を保存
        
        # 元のフレームに戻る
        if self.file_path != current_file:
            self.load_file(current_file, preserve_zoom=True)
        
        # ステータスメッセージ
        if frames_processed > 0:
            self.statusBar().showMessage(f'連続ラベル変更が完了しました。{frames_processed + 1}フレームに適用しました。', 3000)
        else:
            self.statusBar().showMessage(f'ラベルを変更しました: {old_label} -> {new_label}', 3000)
    
    def _propagate_label_to_subsequent_frames_multi(self, source_shape, new_label, prefix="Propagate"):
        """後続フレームにラベルを伝播させる（マルチフレーム操作用）"""
        # 現在の状態を保存
        current_state = {
            'frame_idx': self.cur_img_idx,
            'dirty': self.dirty,
            'file_path': self.file_path
        }
        
        prev_shape = source_shape.copy()
        frame_idx = current_state['frame_idx'] + 1
        frames_processed = 0
        
        # 画像サイズを取得
        image_size = None
        if hasattr(self, 'image') and self.image and not self.image.isNull():
            image_size = self.image.size()
        
        # プログレスダイアログを作成
        progress = QProgressDialog("連続ラベル変更処理中...", "キャンセル", 0,
                                  self.img_count - frame_idx, self)
        progress.setWindowTitle("処理中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        while frame_idx < self.img_count:
            # キャンセルチェック
            if progress.wasCanceled():
                print(f"[{prefix}] Cancelled by user at frame {frame_idx}")
                break
            
            # プログレス更新
            progress.setValue(frame_idx - current_state['frame_idx'])
            progress.setLabelText(f"処理中: フレーム {frame_idx + 1}/{self.img_count}")
            QApplication.processEvents()
            
            # 次のフレームのアノテーションを読み込む
            next_file = self.m_img_list[frame_idx]
            annotation_paths = self._get_annotation_paths(next_file)
            shapes_data = self._load_annotation_shapes_with_size(annotation_paths, next_file, image_size)
            
            if not shapes_data:
                print(f"[{prefix}] No annotation found at frame {frame_idx}, stopping")
                break
            
            # マッチする形状を探す
            best_match_idx, best_iou = self._find_best_match(shapes_data, prev_shape)
            
            if best_match_idx >= 0:
                # 現在のラベルをチェック
                current_label = shapes_data[best_match_idx][0]
                
                # 既に同じラベルの場合は停止
                if current_label == new_label:
                    print(f"[{prefix}] Already has label '{new_label}' at frame {frame_idx}, stopping")
                    break
                
                # ラベルを更新
                print(f"[{prefix}] Found match at frame {frame_idx} with IOU {best_iou:.2f} (current: {current_label})")
                shapes_data[best_match_idx] = self._update_shape_label(shapes_data[best_match_idx], new_label)
                
                # アノテーションを保存
                if self._save_propagated_annotation_with_size(annotation_paths, shapes_data, next_file, image_size):
                    
                    # 次の反復用にprev_shapeを更新
                    points = shapes_data[best_match_idx][1]
                    prev_shape = Shape(label=new_label)
                    for x, y in points:
                        prev_shape.add_point(QPointF(x, y))
                    prev_shape.close()
                    frames_processed += 1
                else:
                    print(f"[{prefix}] Failed to save annotation at frame {frame_idx}")
                    break
            else:
                print(f"[{prefix}] No matching shape found at frame {frame_idx}, stopping")
                break
            
            frame_idx += 1
        
        progress.close()
        
        # 状態を復元
        self._restore_state(current_state)
        
        print(f"[{prefix}] Propagated to {frames_processed} subsequent frames")
        return frames_processed
    
    def propagate_label_to_subsequent_frames(self, source_shape):
        """Propagate label changes to subsequent frames until tracking fails."""
        if not self.continuous_tracking_mode or not source_shape:
            return
        
        print(f"[Propagate] Starting label propagation from frame {self.cur_img_idx}")
        print(f"[Propagate] Will stop when encountering label: {source_shape.label}")
        
        # Create progress dialog
        progress = self._create_progress_dialog()
        
        # Save current state
        current_state = {
            'frame_idx': self.cur_img_idx,
            'dirty': self.dirty,
            'file_path': self.file_path
        }
        
        # Process propagation
        frames_processed = self._process_propagation(source_shape, progress, current_state, source_shape.label)
        
        # Close progress and restore state
        progress.close()
        self._restore_state(current_state)
        
        # Show completion message
        self._show_completion_message(frames_processed)
    
    def _create_progress_dialog(self):
        """Create and configure progress dialog."""
        progress = QProgressDialog("連続ID付け処理中...", "キャンセル", 0, 
                                 self.img_count - self.cur_img_idx - 1, self)
        progress.setWindowTitle("処理中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        return progress
    
    def _process_propagation(self, source_shape, progress, current_state, stop_label=None):
        """Process label propagation to subsequent frames."""
        source_label = source_shape.label
        prev_shape = source_shape.copy()
        
        frame_idx = current_state['frame_idx'] + 1
        frames_processed = 0
        
        # Get image size once from current image (all frames should have same size)
        image_size = None
        if hasattr(self, 'image') and self.image and not self.image.isNull():
            image_size = self.image.size()
        
        while frame_idx < self.img_count:
            # Check if cancelled
            if progress.wasCanceled():
                print(f"[Propagate] Cancelled by user at frame {frame_idx}")
                break
            
            # Update progress
            progress.setValue(frame_idx - current_state['frame_idx'])
            progress.setLabelText(f"処理中: フレーム {frame_idx + 1}/{self.img_count}")
            QApplication.processEvents()
            # Load the next frame's annotation
            next_file = self.m_img_list[frame_idx]
            annotation_paths = self._get_annotation_paths(next_file)
            shapes_data = self._load_annotation_shapes_with_size(annotation_paths, next_file, image_size)
            
            if not shapes_data:
                print(f"[Propagate] No annotation found at frame {frame_idx}, stopping")
                break
            
            # Find matching shape in next frame
            best_match_idx, best_iou = self._find_best_match(shapes_data, prev_shape)
            
            if best_match_idx >= 0:
                # Check if the matched shape already has the same label (stop condition)
                current_label = shapes_data[best_match_idx][0]
                if stop_label and current_label == stop_label:
                    print(f"[Propagate] Encountered same label '{stop_label}' at frame {frame_idx}, stopping")
                    break
                
                # Update the matched shape's label
                print(f"[Propagate] Found match at frame {frame_idx} with IOU {best_iou:.2f} (current label: {current_label})")
                shapes_data[best_match_idx] = self._update_shape_label(shapes_data[best_match_idx], source_label)
                
                # Save the updated annotation
                if self._save_propagated_annotation_with_size(annotation_paths, shapes_data, next_file, image_size):
                    # Update prev_shape for next iteration
                    # Directly update prev_shape points without creating all shapes
                    points = shapes_data[best_match_idx][1]
                    prev_shape = Shape(label=source_label)
                    for x, y in points:
                        prev_shape.add_point(QPointF(x, y))
                    prev_shape.close()
                    frames_processed += 1
                else:
                    print(f"[Propagate] Failed to save annotation at frame {frame_idx}")
                    break
                
                frame_idx += 1
            else:
                print(f"[Propagate] No match found at frame {frame_idx}, stopping")
                break
        
        return frames_processed
    
    def _get_annotation_paths(self, image_file):
        """Get annotation file paths for given image file."""
        basename = os.path.basename(os.path.splitext(image_file)[0])
        
        if self.default_save_dir:
            base_path = self.default_save_dir
        else:
            base_path = os.path.dirname(image_file)
        
        return {
            'xml': os.path.join(base_path, basename + XML_EXT),
            'txt': os.path.join(base_path, basename + TXT_EXT),
            'json': os.path.join(base_path, basename + JSON_EXT)
        }
    
    def _load_annotation_shapes(self, annotation_paths, image_file):
        """Load shapes from annotation file."""
        # Try Pascal VOC format
        if os.path.isfile(annotation_paths['xml']):
            from libs.pascal_voc_io import PascalVocReader
            reader = PascalVocReader(annotation_paths['xml'])
            return reader.get_shapes()
        
        # Try YOLO format
        elif os.path.isfile(annotation_paths['txt']):
            if os.path.isfile(image_file):
                image = QImage()
                image.load(image_file)
                if not image.isNull():
                    from libs.yolo_io import YoloReader
                    reader = YoloReader(annotation_paths['txt'], image)
                    return reader.get_shapes()
                else:
                    print(f"[Propagate] Failed to load image: {image_file}")
            else:
                print(f"[Propagate] Image file not found: {image_file}")
        
        # Try CreateML format
        elif os.path.isfile(annotation_paths['json']):
            from libs.create_ml_io import CreateMLReader
            reader = CreateMLReader(annotation_paths['json'], image_file)
            return reader.get_shapes()
        
        return None
    
    def _load_annotation_shapes_with_size(self, annotation_paths, image_file, image_size):
        """Load shapes from annotation file with pre-determined image size for YOLO."""
        # Try Pascal VOC format
        if os.path.isfile(annotation_paths['xml']):
            from libs.pascal_voc_io import PascalVocReader
            reader = PascalVocReader(annotation_paths['xml'])
            return reader.get_shapes()
        
        # Try YOLO format with pre-determined size
        elif os.path.isfile(annotation_paths['txt']):
            if image_size and image_size.isValid():
                # Create minimal QImage with the known size
                minimal_image = QImage(image_size.width(), image_size.height(), QImage.Format_Mono)
                from libs.yolo_io import YoloReader
                reader = YoloReader(annotation_paths['txt'], minimal_image)
                return reader.get_shapes()
            else:
                print(f"[Propagate] No valid image size available for YOLO format")
                return None
        
        # Try CreateML format
        elif os.path.isfile(annotation_paths['json']):
            from libs.create_ml_io import CreateMLReader
            reader = CreateMLReader(annotation_paths['json'], image_file)
            return reader.get_shapes()
        
        return None
    
    def _load_annotation_shapes_with_cache(self, annotation_paths, image_file, image_cache):
        """Load shapes from annotation file with image caching for YOLO."""
        # Try Pascal VOC format
        if os.path.isfile(annotation_paths['xml']):
            from libs.pascal_voc_io import PascalVocReader
            reader = PascalVocReader(annotation_paths['xml'])
            return reader.get_shapes()
        
        # Try YOLO format with caching
        elif os.path.isfile(annotation_paths['txt']):
            if os.path.isfile(image_file):
                # Check cache first
                if image_file not in image_cache:
                    image = QImage()
                    image.load(image_file)
                    if not image.isNull():
                        image_cache[image_file] = image
                    else:
                        print(f"[Propagate] Failed to load image: {image_file}")
                        return None
                
                if image_file in image_cache:
                    from libs.yolo_io import YoloReader
                    reader = YoloReader(annotation_paths['txt'], image_cache[image_file])
                    return reader.get_shapes()
            else:
                print(f"[Propagate] Image file not found: {image_file}")
        
        # Try CreateML format
        elif os.path.isfile(annotation_paths['json']):
            from libs.create_ml_io import CreateMLReader
            reader = CreateMLReader(annotation_paths['json'], image_file)
            return reader.get_shapes()
        
        return None
    
    def _find_best_match(self, shapes_data, prev_shape):
        """Find best matching shape using IOU."""
        best_match_idx = -1
        best_iou = 0.0
        
        # Early filtering based on bounding box size and position
        prev_bbox = self._get_bbox_from_shape(prev_shape)
        if not prev_bbox:
            return -1, 0.0
        
        px1, py1, px2, py2 = prev_bbox
        prev_width = px2 - px1
        prev_height = py2 - py1
        prev_center_x = (px1 + px2) / 2
        prev_center_y = (py1 + py2) / 2
        
        for idx, shape_data in enumerate(shapes_data):
            # shape_data is (label, points, line_color, fill_color, difficult)
            points = shape_data[1]
            
            # Quick rejection based on bounding box
            if len(points) >= 4:
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                x1, y1 = min(x_coords), min(y_coords)
                x2, y2 = max(x_coords), max(y_coords)
                
                # Check if size difference is too large (>50% difference)
                curr_width = x2 - x1
                curr_height = y2 - y1
                if (abs(curr_width - prev_width) / prev_width > 0.5 or 
                    abs(curr_height - prev_height) / prev_height > 0.5):
                    continue
                
                # Check if center distance is too large
                curr_center_x = (x1 + x2) / 2
                curr_center_y = (y1 + y2) / 2
                center_dist = ((curr_center_x - prev_center_x) ** 2 + 
                              (curr_center_y - prev_center_y) ** 2) ** 0.5
                if center_dist > max(prev_width, prev_height):
                    continue
            
            # Only calculate IOU for candidates that pass quick checks
            curr_shape = Shape()
            for x, y in points:
                curr_shape.add_point(QPointF(x, y))
            
            iou = self.tracker.calculate_iou(prev_shape, curr_shape)
            if iou > best_iou and iou >= self.tracker.iou_threshold:
                best_iou = iou
                best_match_idx = idx
        
        return best_match_idx, best_iou
    
    def _get_bbox_from_shape(self, shape):
        """Extract bounding box from shape."""
        if not hasattr(shape, 'points') or len(shape.points) < 2:
            return None
        
        x_coords = [p.x() for p in shape.points]
        y_coords = [p.y() for p in shape.points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def _update_shape_label(self, shape_data, new_label):
        """Update shape data with new label."""
        # shape_data is (label, points, line_color, fill_color, difficult)
        return (new_label, shape_data[1], shape_data[2], shape_data[3], shape_data[4])
    
    def _create_shapes_from_data(self, shapes_data):
        """Create Shape objects from shape data."""
        shapes = []
        for shape_data in shapes_data:
            label, points, line_color, fill_color, difficult = shape_data
            shape = Shape(label=label)
            for x, y in points:
                shape.add_point(QPointF(x, y))
            shape.difficult = difficult
            
            if line_color:
                shape.line_color = QColor(*line_color)
            else:
                shape.line_color = generate_color_by_text(label)
            
            if fill_color:
                shape.fill_color = QColor(*fill_color)
            else:
                shape.fill_color = generate_color_by_text(label)
            
            shape.close()
            shapes.append(shape)
        return shapes
    
    def _save_propagated_annotation(self, annotation_paths, shapes_data, image_file):
        """Save propagated annotation to file."""
        # Determine which format to save
        save_format = None
        save_path = None
        
        if os.path.isfile(annotation_paths['xml']):
            save_format = LabelFileFormat.PASCAL_VOC
            save_path = annotation_paths['xml']
        elif os.path.isfile(annotation_paths['txt']):
            save_format = LabelFileFormat.YOLO
            save_path = annotation_paths['txt']
        elif os.path.isfile(annotation_paths['json']):
            save_format = LabelFileFormat.CREATE_ML
            save_path = annotation_paths['json']
        
        if not save_format or not save_path:
            return False
        
        # Create shapes for saving
        shapes = self._create_shapes_from_data(shapes_data)
        shapes_for_save = [self._format_shape_for_save(s) for s in shapes]
        
        # Save using appropriate format
        temp_label_file = LabelFile()
        try:
            if save_format == LabelFileFormat.PASCAL_VOC:
                temp_label_file.save_pascal_voc_format(save_path, shapes_for_save, image_file, None,
                                                      self.line_color.getRgb(), self.fill_color.getRgb())
            elif save_format == LabelFileFormat.YOLO:
                # For YOLO, we need the image
                image_data = read(image_file, None)
                if image_data:
                    temp_label_file.save_yolo_format(save_path, shapes_for_save, image_file, image_data, 
                                                   self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
                else:
                    return False
            elif save_format == LabelFileFormat.CREATE_ML:
                temp_label_file.save_create_ml_format(save_path, shapes_for_save, image_file, None,
                                                     self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
            
            print(f"[Propagate] Saved updated annotation to {save_path}")
            return True
        except Exception as e:
            print(f"[Propagate] Error saving annotation: {str(e)}")
            return False
    
    def _save_propagated_annotation_with_size(self, annotation_paths, shapes_data, image_file, image_size):
        """Save propagated annotation to file with pre-determined image size."""
        # Determine which format to save
        save_format = None
        save_path = None
        
        if os.path.isfile(annotation_paths['xml']):
            save_format = LabelFileFormat.PASCAL_VOC
            save_path = annotation_paths['xml']
        elif os.path.isfile(annotation_paths['txt']):
            save_format = LabelFileFormat.YOLO
            save_path = annotation_paths['txt']
        elif os.path.isfile(annotation_paths['json']):
            save_format = LabelFileFormat.CREATE_ML
            save_path = annotation_paths['json']
        
        if not save_format or not save_path:
            return False
        
        # Create shapes for saving only once
        shapes_for_save = []
        for shape_data in shapes_data:
            label, points, line_color, fill_color, difficult = shape_data
            shapes_for_save.append({
                'label': label,
                'points': points,
                'line_color': line_color or generate_color_by_text(label).getRgb(),
                'fill_color': fill_color or generate_color_by_text(label).getRgb(),
                'difficult': difficult
            })
        
        # Save using appropriate format
        temp_label_file = LabelFile()
        try:
            if save_format == LabelFileFormat.PASCAL_VOC:
                temp_label_file.save_pascal_voc_format(save_path, shapes_for_save, image_file, None,
                                                      self.line_color.getRgb(), self.fill_color.getRgb())
            elif save_format == LabelFileFormat.YOLO:
                # For YOLO, create minimal image data with known size
                if image_size and image_size.isValid():
                    # Create minimal image for YOLO format
                    minimal_image = QImage(image_size.width(), image_size.height(), QImage.Format_Mono)
                    buffer = QByteArray()
                    buffer_io = QBuffer(buffer)
                    buffer_io.open(QIODevice.WriteOnly)
                    minimal_image.save(buffer_io, "PNG")
                    image_data = buffer.data()
                    
                    temp_label_file.save_yolo_format(save_path, shapes_for_save, image_file, image_data, 
                                                   self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
                else:
                    print(f"[Propagate] Cannot save YOLO format without image size")
                    return False
            elif save_format == LabelFileFormat.CREATE_ML:
                temp_label_file.save_create_ml_format(save_path, shapes_for_save, image_file, None,
                                                     self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
            
            return True
        except Exception as e:
            print(f"[Propagate] Error saving annotation: {str(e)}")
            return False
    
    def _save_propagated_annotation_with_cache(self, annotation_paths, shapes_data, image_file, image_cache):
        """Save propagated annotation to file with image cache."""
        # Determine which format to save
        save_format = None
        save_path = None
        
        if os.path.isfile(annotation_paths['xml']):
            save_format = LabelFileFormat.PASCAL_VOC
            save_path = annotation_paths['xml']
        elif os.path.isfile(annotation_paths['txt']):
            save_format = LabelFileFormat.YOLO
            save_path = annotation_paths['txt']
        elif os.path.isfile(annotation_paths['json']):
            save_format = LabelFileFormat.CREATE_ML
            save_path = annotation_paths['json']
        
        if not save_format or not save_path:
            return False
        
        # Create shapes for saving only once
        shapes_for_save = []
        for shape_data in shapes_data:
            label, points, line_color, fill_color, difficult = shape_data
            shapes_for_save.append({
                'label': label,
                'points': points,
                'line_color': line_color or generate_color_by_text(label).getRgb(),
                'fill_color': fill_color or generate_color_by_text(label).getRgb(),
                'difficult': difficult
            })
        
        # Save using appropriate format
        temp_label_file = LabelFile()
        try:
            if save_format == LabelFileFormat.PASCAL_VOC:
                temp_label_file.save_pascal_voc_format(save_path, shapes_for_save, image_file, None,
                                                      self.line_color.getRgb(), self.fill_color.getRgb())
            elif save_format == LabelFileFormat.YOLO:
                # Use cached image if available
                if image_file in image_cache:
                    # Convert QImage to bytes for saving
                    buffer = QByteArray()
                    buffer_io = QBuffer(buffer)
                    buffer_io.open(QIODevice.WriteOnly)
                    image_cache[image_file].save(buffer_io, "PNG")
                    image_data = buffer.data()
                else:
                    image_data = read(image_file, None)
                
                if image_data:
                    temp_label_file.save_yolo_format(save_path, shapes_for_save, image_file, image_data, 
                                                   self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
                else:
                    return False
            elif save_format == LabelFileFormat.CREATE_ML:
                temp_label_file.save_create_ml_format(save_path, shapes_for_save, image_file, None,
                                                     self.label_hist, self.line_color.getRgb(), self.fill_color.getRgb())
            
            return True
        except Exception as e:
            print(f"[Propagate] Error saving annotation: {str(e)}")
            return False
    
    def _format_shape_for_save(self, shape):
        """Format shape object for saving."""
        return dict(
            label=shape.label,
            line_color=shape.line_color.getRgb(),
            fill_color=shape.fill_color.getRgb(),
            points=[(p.x(), p.y()) for p in shape.points],
            difficult=shape.difficult
        )
    
    def _create_state_from_shapes_data(self, file_path, shapes_data):
        """shapes_dataから状態オブジェクトを作成（フレームをロードせずに）"""
        shapes = []
        for shape_data in shapes_data:
            label, points, line_color, fill_color, difficult = shape_data
            shapes.append({
                'label': label,
                'points': points,
                'line_color': line_color or generate_color_by_text(label).getRgb(),
                'fill_color': fill_color or generate_color_by_text(label).getRgb(),
                'difficult': difficult
            })
        
        return {
            'file_path': file_path,
            'shapes': shapes
        }
    
    def _restore_state(self, state):
        """Restore application state."""
        self.cur_img_idx = state['frame_idx']
        self.file_path = state['file_path']
        self.dirty = state['dirty']
    
    def _show_completion_message(self, frames_processed):
        """Show completion message in status bar."""
        print(f"[Propagate] Completed. Propagated to {frames_processed} frames")
        
        if frames_processed > 0:
            self.statusBar().showMessage(f'連続ID付けが完了しました。{frames_processed}フレームに伝播しました。', 3000)
        else:
            self.statusBar().showMessage('追跡可能なフレームが見つかりませんでした。', 3000)
        self.statusBar().show()
    
    def store_current_shapes(self):
        """Store current frame shapes for tracking."""
        if self.canvas.shapes:
            self.prev_frame_shapes = [shape.copy() for shape in self.canvas.shapes]
            print(f"[Store] Stored {len(self.prev_frame_shapes)} shapes from frame {self.cur_img_idx}")
        else:
            self.prev_frame_shapes = []
            print(f"[Store] No shapes to store from frame {self.cur_img_idx}")
    
    def apply_tracking(self):
        """Apply tracking to current frame shapes."""
        if not self.continuous_tracking_mode:
            return
        
        if not self.prev_frame_shapes:
            return
        
        # Get current shapes
        curr_shapes = self.canvas.shapes
        if not curr_shapes:
            return
        
        
        # Debug: Print before tracking
        print(f"[Tracking] Applying tracking to frame {self.cur_img_idx}")
        print(f"[Tracking] Prev shapes: {[s.label for s in self.prev_frame_shapes]}")
        print(f"[Tracking] Curr shapes before: {[s.label for s in curr_shapes]}")
        
        # Apply tracking
        self.tracker.track_shapes(self.prev_frame_shapes, curr_shapes)
        
        # Debug: Print after tracking
        print(f"[Tracking] Curr shapes after: {[s.label for s in curr_shapes]}")
        
        # Update colors for tracked shapes
        for shape in curr_shapes:
            if getattr(shape, 'is_tracked', False) and shape.label:
                shape.line_color = generate_color_by_text(shape.label)
        
        # Update canvas
        self.canvas.load_shapes(curr_shapes)
        
        # Update label list properly
        self.label_list.clear()
        self.items_to_shapes.clear()
        self.shapes_to_items.clear()
        
        for shape in curr_shapes:
            # Ensure shape has proper paint_label setting
            shape.paint_label = self.display_label_option.isChecked()
            self.add_label(shape)
        
        # Update combo box
        self.update_combo_box()

def inverted(color):
    return QColor(*[255 - v for v in color.getRgb()])


def read(filename, default=None):
    try:
        reader = QImageReader(filename)
        reader.setAutoTransform(True)
        return reader.read()
    except:
        return default


def get_main_app(argv=None):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_() -- so that we can test the application in one thread
    """
    if not argv:
        argv = []
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(new_icon("app"))
    # Tzutalin 201705+: Accept extra agruments to change predefined class file
    argparser = argparse.ArgumentParser()
    argparser.add_argument("image_dir", nargs="?")
    argparser.add_argument("class_file",
                           default=os.path.join(os.path.dirname(__file__), "data", "predefined_classes.txt"),
                           nargs="?")
    argparser.add_argument("save_dir", nargs="?")
    args = argparser.parse_args(argv[1:])

    args.image_dir = args.image_dir and os.path.normpath(args.image_dir)
    args.class_file = args.class_file and os.path.normpath(args.class_file)
    args.save_dir = args.save_dir and os.path.normpath(args.save_dir)

    # Usage : labelImg.py image classFile saveDir
    win = MainWindow(args.image_dir,
                     args.class_file,
                     args.save_dir)
    win.show()
    return app, win


def main():
    """construct main app and run it"""
    app, _win = get_main_app(sys.argv)
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
