#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify BB color mode persistence
"""

import json
import os

def check_settings():
    """Check the current BB_COLOR_MODE in settings"""
    settings_path = '.claude/settings.local.json'
    
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            bb_color_mode = settings.get('BB_COLOR_MODE', 0)
            print(f"Current BB_COLOR_MODE: {bb_color_mode}")
            print("0 = Label1 base, 1 = Label2 base, 2 = Combined")
            return bb_color_mode
    else:
        print("Settings file not found")
        return None

def simulate_color_mode_change(new_mode):
    """Simulate changing the color mode"""
    settings_path = '.claude/settings.local.json'
    
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        settings['BB_COLOR_MODE'] = new_mode
        
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"Changed BB_COLOR_MODE to: {new_mode}")
    else:
        print("Settings file not found")

if __name__ == "__main__":
    print("Testing BB color mode persistence...")
    print("-" * 40)
    
    # Check current setting
    current = check_settings()
    
    print("\nTo test:")
    print("1. Run labelImg.py")
    print("2. Change BB color mode to 'Label 2 ベース'")
    print("3. Switch frames")
    print("4. Check if color mode persists")
    print("5. Close and reopen the app")
    print("6. Check if color mode is restored")