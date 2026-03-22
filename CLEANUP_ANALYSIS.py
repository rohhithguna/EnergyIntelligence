#!/usr/bin/env python
"""
Project Cleanup Script
Removes dead code and consolidates duplicates
"""

import os

def identify_dead_files():
    """Identify duplicate and unused files"""
    
    # Root level duplicates (should be in frontend/)
    root_duplicates = [
        "index.html",
        "script.js",
        "styles.css",
        "upload.html",
        "upload-script.js",
        "upload-styles.css",
    ]
    
    # Unused/legacy files
    unused_files = [
        "http_server.py",           # legacy, use server/simple_server.py
        "upload_validator.py",      # legacy
        "test_domain_mapper.py",    # test file
        "test_http_server.py",      # test file
        "test_quality_evaluator.py",# test file
        "integration.txt",          # notes file
    ]
    
    # Frontend unused
    frontend_unused = [
        "frontend/index.js",        # replaced by script.js
        "frontend/dashboard.js",    # should be in script.js
        "frontend/report.js",       # should be in script.js
        "frontend/reports.html",    # unused
        "frontend/reports.js",      # unused
    ]
    
    return root_duplicates, unused_files, frontend_unused

def list_dead_files():
    """List files that should be deleted"""
    root_dup, unused, frontend_dup = identify_dead_files()
    
    print("\n" + "="*70)
    print("DEAD CODE ANALYSIS")
    print("="*70)
    
    print("\nROOT DUPLICATES (in frontend/):")
    for f in root_dup:
        path = f"/Users/rohhithg/Desktop/pyhton project/{f}"
        if os.path.exists(path):
            print(f"  ❌ {f}")
    
    print("\nUNUSED LEGACY FILES:")
    for f in unused:
        path = f"/Users/rohhithg/Desktop/pyhton project/{f}"
        if os.path.exists(path):
            print(f"  ❌ {f}")
    
    print("\nFRONTEND UNUSED:")
    for f in frontend_dup:
        path = f"/Users/rohhithg/Desktop/pyhton project/{f}"
        if os.path.exists(path):
            print(f"  ❌ {f}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    list_dead_files()
