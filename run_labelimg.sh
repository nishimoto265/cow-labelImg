#!/bin/bash
# Launch labelImg with cow annotations

# Change to the script's directory
cd "$(dirname "$0")"

# Configuration
IMAGE_DIR="/media/thithilab/volume/research/datasets/test_images/left_images_masked"
CLASSES_FILE="/media/thithilab/volume/research/outputs/final_left/action_label/classes.txt"
ANNOTATION_DIR="/media/thithilab/volume/research/outputs/final_left/action_label"

# Activate virtual environment and run labelImg
uv run python labelImg.py "$IMAGE_DIR" "$CLASSES_FILE" "$ANNOTATION_DIR"