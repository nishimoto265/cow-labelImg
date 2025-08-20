# Custom Features Documentation for cow-labelImg

This document provides comprehensive documentation for all custom features added to the original labelImg application.

## Table of Contents
1. [Quick ID Selector](#quick-id-selector)
2. [BB Duplication Mode](#bb-duplication-mode)
3. [Continuous Tracking Mode](#continuous-tracking-mode)
4. [Click-to-Change Label Mode](#click-to-change-label-mode)
5. [Label Propagation](#label-propagation)
6. [Drawing Options](#drawing-options)
7. [File Structure](#file-structure)
8. [Dependencies](#dependencies)

---

## Quick ID Selector

### Overview
A floating ID selection window that allows quick switching between animal IDs using keyboard shortcuts or mouse clicks.

### Files
- **Main Implementation**: `libs/quick_id_selector.py`
- **Integration**: `labelImg.py` (lines 53, 143-144, 703, 748, 1060-1061, 1178-1180, 1446-1447, 1898-1899, 2062-2091)

### Key Features
- Semi-transparent floating window
- Keyboard shortcuts (1-9, 0 for 10)
- Visual ID button grid (max 30 IDs)
- Auto-updates missing labels
- Current ID highlighting

### Main Classes/Methods
```python
class QuickIDSelector(QDialog):
    - __init__(parent, max_ids=30)
    - set_current_id(id_str)
    - update_missing_labels()
    - id_selected = pyqtSignal(str)

# In labelImg.py:
def toggle_quick_id_selector()
def select_quick_id(id_str)
def on_quick_id_selected(id_str)
def apply_quick_id_to_selected_shape()
def apply_quick_id_with_propagation(shape, new_label, old_label)
```

### Usage
- Press `W` to toggle the Quick ID Selector window
- Press number keys 1-9 or 0 (for ID 10) to select an ID
- Click on ID buttons in the floating window
- Selected ID is applied to the currently selected shape

---

## BB Duplication Mode

### Overview
Automatically duplicates bounding boxes to subsequent frames when creating new annotations.

### Files
- **Main Implementation**: `labelImg.py` (lines 135, 200-256, 2050-2061, 2249-2377)

### Key Features
- Automatic duplication to N subsequent frames
- IOU-based conflict detection
- Overwrite or skip mode for conflicts
- Progress dialog with cancellation

### Configuration Options
- **Frame Count**: Number of subsequent frames (1-100)
- **IOU Threshold**: Overlap threshold for conflict detection (0.1-1.0)
- **Overwrite Mode**: Replace existing boxes or skip conflicting frames

### Main Methods
```python
def toggle_bb_duplication(state)
def duplicate_bb_to_subsequent_frames(source_shape)
def calculate_iou(box1, box2)
def update_overwrite_checkbox_text()
```

### UI Elements
- `bb_duplication_checkbox`: Main mode toggle
- `bb_dup_frame_count`: QSpinBox for frame count
- `bb_dup_iou_threshold`: QDoubleSpinBox for IOU threshold
- `bb_dup_overwrite_checkbox`: Overwrite mode toggle

---

## Continuous Tracking Mode

### Overview
Enables automatic tracking of objects across frames using IOU-based matching and Hungarian algorithm.

### Files
- **Main Module**: `libs/tracker.py`
- **Integration**: `labelImg.py` (lines 130, 183-186, 1349-1366, 2032-2045)

### Key Features
- IOU-based shape matching
- Hungarian algorithm for optimal assignment
- Automatic label propagation
- Track ID management

### Main Classes/Methods
```python
# In libs/tracker.py:
class Tracker:
    - __init__(iou_threshold=0.4)
    - calculate_iou(shape1, shape2)
    - match_shapes(current_shapes, prev_shapes)
    - update_frame(shapes)

# In labelImg.py:
def toggle_continuous_tracking(state)
def propagate_label_to_subsequent_frames(source_shape)
def _propagate_label_to_subsequent_frames_multi(source_shape, new_label, prefix)
```

### Usage
- Enable "連続ID付けモード" checkbox
- Labels automatically propagate when moving to next frame
- Uses IOU matching to find corresponding objects

---

## Click-to-Change Label Mode

### Overview
Allows changing labels by clicking on shapes in the canvas.

### Files
- **Implementation**: `labelImg.py` (lines 138, 188-192, 2046-2049, 2371-2486)

### Key Features
- Single-click label selection
- Double-click to apply label
- Works with continuous tracking for propagation

### Main Methods
```python
def toggle_click_change_label(state)
def on_shape_clicked()
def apply_label_to_all_frames(shape, item, new_label, old_label)
```

### Usage
- Enable "クリックでラベル変更" checkbox
- Click on a shape to select it
- Double-click to change its label
- If continuous tracking is enabled, propagates to subsequent frames

---

## Label Propagation

### Overview
System for propagating label changes across multiple frames based on shape tracking.

### Files
- **Implementation**: `labelImg.py` (lines 2480-2985)

### Key Features
- IOU-based shape matching
- Efficient frame loading without full UI update
- Support for multiple annotation formats (YOLO, Pascal VOC, CreateML)
- Caching for improved performance

### Main Methods
```python
def _propagate_label_to_subsequent_frames_multi(source_shape, new_label, prefix)
def _save_propagated_annotation(annotation_paths, shapes_data, image_file)
def _save_propagated_annotation_with_size(annotation_paths, shapes_data, image_file, image_size)
def _save_propagated_annotation_with_cache(annotation_paths, shapes_data, image_file, image_cache)
def _update_shape_label(shape_data, new_label)
```

### Performance Optimizations
- Direct file I/O without full frame loading
- Image dimension caching
- Batch processing support

---

## Drawing Options

### Overview
UI controls for toggling visibility of bounding boxes and IDs.

### Files
- **Implementation**: `labelImg.py` (lines 273-290, 1993-2003)

### Features
- Toggle bounding box visibility
- Toggle ID label visibility
- Real-time canvas updates

### Main Methods
```python
def toggle_bounding_box_display(state)
def toggle_id_display(state)
```

---

## File Structure

### Modified Files
```
cow-labelImg/
├── labelImg.py              # Main application with integrated features
├── libs/
│   ├── quick_id_selector.py # Quick ID Selector implementation
│   ├── tracker.py           # Continuous tracking module
│   └── shape.py            # Modified for additional shape properties
└── docs/
    ├── custom_features_documentation.md  # This file
    ├── continuous_tracking_requirements.md
    └── undo_requirements.md
```

### Added Properties to Shape Class
- `paint_id`: Boolean for ID display
- `paint_label`: Boolean for label display
- Additional tracking-related properties

---

## Dependencies

### Python Packages
- **PyQt5**: UI framework
- **numpy**: Numerical operations for IOU calculations
- **scipy**: Hungarian algorithm implementation (`linear_sum_assignment`)
- **Pillow (PIL)**: Image loading for dimension detection

### Internal Dependencies
```python
# Quick ID Selector
from libs.quick_id_selector import QuickIDSelector

# Tracker
from libs.tracker import Tracker

# Standard labelImg modules
from libs.shape import Shape
from libs.yolo_io import YoloReader, YOLOWriter
from libs.pascal_voc_io import PascalVocReader, PascalVocWriter
from libs.create_ml_io import CreateMLReader, CreateMLWriter
```

---

## Configuration Variables

### Global Settings
```python
# Tracking
continuous_tracking_mode = False
iou_threshold = 0.4

# BB Duplication
bb_duplication_mode = False
bb_dup_frame_count = 5
bb_dup_iou_threshold = 0.6
bb_dup_overwrite = False

# Click Change
click_change_label_mode = False

# Quick ID
max_quick_ids = 30
current_quick_id = "1"
```

---

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| W | Toggle Quick ID Selector |
| 1-9 | Select Quick ID 1-9 |
| 0 | Select Quick ID 10 |
| Click | Select shape (in click-change mode) |
| Double-click | Apply label (in click-change mode) |

---

## Future Refactoring Opportunities

1. **Modularization**: Extract features into separate modules
2. **Configuration File**: Move settings to external config
3. **Event System**: Implement proper event bus for inter-feature communication
4. **Testing**: Add unit tests for each feature
5. **Documentation**: Add inline documentation and docstrings
6. **Performance**: Optimize frame loading and caching
7. **Error Handling**: Improve error messages and recovery