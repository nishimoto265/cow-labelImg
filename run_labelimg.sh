#!/bin/bash
# Launch labelImg with cow annotations

# Change to the script's directory
cd "$(dirname "$0")"

# Configuration
IMAGE_DIR="D:/datasets/test_images/right_images_1fps_masked/2025-04-01-14"
CLASSES_FILE="D:/outputs/right/2025-04-01-14/annotations/ID/classes.txt"
ANNOTATION_DIR="D:/outputs/right/2025-04-01-14/annotations/ID"

# Activate virtual environment and run labelImg
uv run python labelImg.py "$IMAGE_DIR" "$CLASSES_FILE" "$ANNOTATION_DIR"