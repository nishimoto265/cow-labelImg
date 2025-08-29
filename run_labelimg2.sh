#!/bin/bash
# Launch labelImg with dual label support for cow annotations

# Change to the script's directory
cd "$(dirname "$0")"

# Configuration
IMAGE_DIR="/media/thithilab/volume/research/datasets/test_images/right_images_1fps_masked/2025-04-01-14"
ANNOTATION_DIR="/media/thithilab/volume/research/outputs/right/2025-04-01-14"

# Dual label class files - specify both files directly
CLASSES1_FILE="/media/thithilab/volume/research/outputs/right/2025-04-01-14/classes1.txt"
CLASSES2_FILE="/media/thithilab/volume/research/outputs/right/2025-04-01-14/classes2.txt"

# For backward compatibility, we still need to pass classes.txt (or classes1.txt) as the second argument
# labelImg will automatically detect classes2.txt in the same directory
uv run python labelImg.py "$IMAGE_DIR" "$CLASSES1_FILE" "$ANNOTATION_DIR"