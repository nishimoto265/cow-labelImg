#!/bin/bash
# Launch labelImg with cow annotations

# Configuration
IMAGE_DIR="/media/thithilab/volume/research/datasets/test_images/right_images_masked"
CLASSES_FILE="/media/thithilab/volume/research/outputs/cow_right_detection_txt_labelimg/classes.txt"
ANNOTATION_DIR="/media/thithilab/volume/research/outputs/cow_right_detection_txt_labelimg"

# Activate virtual environment and run labelImg
uv run python labelImg.py "$IMAGE_DIR" "$CLASSES_FILE" "$ANNOTATION_DIR"