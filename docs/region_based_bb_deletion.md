# Region-Based Bounding Box Deletion Feature

## Overview
This feature allows users to draw a rectangular region and automatically delete all bounding boxes that are completely contained within that region. The feature supports multi-frame propagation for batch deletion across consecutive frames.

## Functional Requirements

### 1. Region Deletion Mode
- **Activation**: Toggle via checkbox in the GUI labeled "領域内BB削除モード" (Delete BBs in Region Mode)
- **Visual Indicator**: When activated, cursor changes to indicate deletion mode
- **Mode Behavior**: While active, drawing a rectangle performs deletion instead of creating a new BB

### 2. Deletion Logic
- **Containment Check**: A bounding box is deleted if all four corners are inside the drawn region
- **Temporary Region**: The drawn region is used only for deletion and is not saved as a bounding box
- **Immediate Execution**: Deletion occurs immediately upon releasing the mouse button

### 3. Multi-Frame Propagation
- **Frame Count Setting**: User can specify number of frames to propagate (N frames)
  - Default: 1 (current frame only)
  - Range: 1-100 frames
  - GUI: Spinbox next to the checkbox
- **Propagation Logic**: 
  - Apply same region deletion to next N-1 frames
  - Stop if end of image sequence is reached
  - Show progress dialog for operations > 10 frames

### 4. Undo/Redo Support
- **Undo Command**: Single undo reverts all deletions from one region operation
- **Multi-Frame Undo**: If propagated to N frames, single undo restores all N frames
- **Command Grouping**: All deletions from one operation are grouped as composite command

## User Interface Design

### GUI Elements
```
[✓] 領域内BB削除モード    後続フレーム数: [1] ▲▼
```

### Visual Feedback
- **Drawing Region**: Dashed red rectangle while dragging
- **Deletion Preview**: Highlight BBs to be deleted in red before confirmation
- **Status Message**: "X個のBBを削除しました (Yフレーム)" after operation

## Implementation Architecture

### Key Components
1. **RegionDeletionMode**: Boolean flag in main window
2. **RegionDeletionFrames**: Integer for frame propagation count
3. **DeleteBBsInRegion**: Method to perform deletion logic
4. **RegionDeletionCommand**: Undo command class

### Event Flow
1. User activates region deletion mode
2. User sets frame count (optional)
3. User draws rectangular region
4. System identifies contained BBs
5. System deletes BBs in current frame
6. If frames > 1, propagate to subsequent frames
7. Create composite undo command
8. Update display and show status

## Technical Specifications

### Containment Algorithm
```python
def is_bb_contained(bb, region):
    """Check if bounding box is completely inside region"""
    return (region.x1 <= bb.x1 and 
            region.y1 <= bb.y1 and
            region.x2 >= bb.x2 and
            region.y2 >= bb.y2)
```

### File Structure
- `libs/region_deletion.py`: Core deletion logic
- `libs/undo/commands/region_deletion_commands.py`: Undo commands
- Update `labelImg.py`: GUI integration and event handling
- Update `libs/canvas.py`: Drawing mode handling

## Configuration
- Saved in settings:
  - `region_deletion_mode`: Boolean
  - `region_deletion_frames`: Integer (1-100)
- Keyboard shortcut: Ctrl+Shift+D to toggle mode

## Testing Requirements
1. Test deletion with overlapping BBs
2. Test frame propagation boundary conditions
3. Test undo/redo with multi-frame operations
4. Test interaction with other modes (tracking, duplication)
5. Test performance with large number of BBs

## Future Enhancements
- Support for non-rectangular regions (polygon, circle)
- Deletion based on partial overlap threshold
- Inverse mode (delete BBs outside region)
- Pattern-based deletion (delete BBs with specific labels)