#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add 'standing' label to all txt files in the specified directory.
Process all YOLO format annotation files and add label2 as 'standing'.
"""

import os
import shutil
from pathlib import Path

def process_annotation_file(input_path, output_path):
    """Process a single annotation file to add 'standing' label."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    processed_lines = []
    for line in lines:
        line = line.strip()
        if line:  # Skip empty lines
            # Add 'standing' to the end of each line
            processed_lines.append(f"{line} standing\n")
        else:
            processed_lines.append("\n")
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)

def main():
    # Input and output directories
    input_dir = r"D:\outputs\right\2025-04-01-14\annotations\ID"
    output_dir = r"D:\outputs\right\2025-04-01-14\annotations\ID_with_standing"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all txt files in the input directory
    txt_files = list(Path(input_dir).glob("*.txt"))
    
    if not txt_files:
        print(f"No txt files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} txt files to process")
    
    # Process each file
    processed_count = 0
    for txt_file in txt_files:
        try:
            output_file = Path(output_dir) / txt_file.name
            process_annotation_file(txt_file, output_file)
            processed_count += 1
            
            if processed_count % 100 == 0:
                print(f"Processed {processed_count} files...")
        
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
    
    print(f"\nCompleted! Processed {processed_count} files")
    print(f"Output saved to: {output_dir}")

if __name__ == "__main__":
    main()