#!/usr/bin/env python
"""
System Audit & Verification Script
Validates the entire data flow intelligence system
"""

import os
import sys
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """Verify all modules can be imported"""
    results = {"status": "PASS", "errors": []}
    
    try:
        from data.loader import load_data
        from data.preprocessor import preprocess_data
        from core.pattern_spike_engine import run_core_engine
        from core.anomaly_engine import detect_anomalies
        from core.ai_engine import analyze_with_claude
        from analysis.correlation import compute_correlation
        from domain_mapper import apply_column_mapping, FRONTEND_DOMAIN_MAPPING
        from main import run_pipeline
        results["imports"] = "OK"
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Import error: {str(e)}")
    
    return results

def check_pipeline():
    """Verify pipeline runs with sample data"""
    results = {"status": "PASS", "errors": []}
    
    try:
        sample_file = "sample_data.csv"
        if not os.path.exists(sample_file):
            results["status"] = "FAIL"
            results["errors"].append(f"Sample file not found: {sample_file}")
            return results
        
        from main import run_pipeline
        output = run_pipeline(sample_file)
        
        required_keys = ["spikes", "drops", "anomalies", "ai_analysis", "risk", "quality", "trend"]
        missing = [k for k in required_keys if k not in output]
        
        if missing:
            results["status"] = "FAIL"
            results["errors"].append(f"Missing output keys: {missing}")
        else:
            results["pipeline"] = "OK"
            results["output_keys"] = sorted(output.keys())
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Pipeline error: {str(e)}\n{traceback.format_exc()}")
    
    return results

def check_domains():
    """Verify domain configuration"""
    results = {"status": "PASS", "errors": []}
    
    try:
        domains_file = "domains.json"
        if not os.path.exists(domains_file):
            results["status"] = "FAIL"
            results["errors"].append(f"Domains file not found: {domains_file}")
            return results
        
        with open(domains_file, "r") as f:
            domains = json.load(f)
        
        from domain_mapper import FRONTEND_DOMAIN_MAPPING
        
        frontend_domains = set(FRONTEND_DOMAIN_MAPPING.keys())
        schema_domains = set(domains.keys())
        
        if frontend_domains != schema_domains:
            results["warnings"] = f"Domain mismatch: frontend={frontend_domains}, schema={schema_domains}"
        
        results["domains"] = list(domains.keys())
        results["count"] = len(domains)
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Domain check error: {str(e)}")
    
    return results

def check_column_mapping():
    """Verify column mapping is complete"""
    results = {"status": "PASS", "errors": []}
    
    try:
        from domain_mapper import FRONTEND_DOMAIN_MAPPING
        
        for domain, mapping in FRONTEND_DOMAIN_MAPPING.items():
            if domain == "generic":
                continue
            
            numeric_col = mapping.get("numeric_column")
            if not numeric_col:
                results["warnings"] = f"Domain {domain} missing numeric_column"
        
        results["mappings"] = len(FRONTEND_DOMAIN_MAPPING)
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Mapping check error: {str(e)}")
    
    return results

def check_frontend_files():
    """Verify frontend files exist"""
    results = {"status": "PASS", "errors": []}
    
    required_files = [
        "frontend/index.html",
        "frontend/dashboard.html",
        "frontend/report.html",
        "frontend/ai_insights.html",
        "frontend/comparison.html",
        "frontend/script.js",
        "frontend/style.css",
        "frontend/domains.json"
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        results["status"] = "FAIL"
        results["errors"].append(f"Missing frontend files: {missing}")
    else:
        results["frontend"] = "OK"
    
    return results

def check_backend_structure():
    """Verify backend module structure"""
    results = {"status": "PASS", "errors": []}
    
    required_modules = [
        "data/__init__.py",
        "data/loader.py",
        "data/preprocessor.py",
        "core/__init__.py",
        "core/ai_engine.py",
        "core/anomaly_engine.py",
        "core/pattern_spike_engine.py",
        "analysis/__init__.py",
        "analysis/correlation.py"
    ]
    
    missing = []
    for module in required_modules:
        if not os.path.exists(module):
            missing.append(module)
    
    if missing:
        results["status"] = "FAIL"
        results["errors"].append(f"Missing backend modules: {missing}")
    else:
        results["backend"] = "OK"
    
    return results

def run_full_audit():
    """Execute full system audit"""
    print("\n" + "="*70)
    print("SYSTEM AUDIT & VERIFICATION")
    print("="*70)
    
    checks = [
        ("Backend Structure", check_backend_structure),
        ("Module Imports", check_imports),
        ("Domain Configuration", check_domains),
        ("Column Mapping", check_column_mapping),
        ("Frontend Files", check_frontend_files),
        ("Pipeline Execution", check_pipeline),
    ]
    
    all_results = {}
    system_status = "PASS"
    
    for check_name, check_func in checks:
        print(f"\n▶ {check_name}...", end=" ")
        result = check_func()
        all_results[check_name] = result
        
        if result.get("status") == "FAIL":
            print("❌ FAIL")
            system_status = "FAIL"
            for error in result.get("errors", []):
                print(f"  ERROR: {error}")
        else:
            print("✓ PASS")
            if "warnings" in result:
                print(f"  WARNING: {result['warnings']}")
    
    print("\n" + "="*70)
    print(f"OVERALL STATUS: {system_status}")
    print("="*70 + "\n")
    
    return all_results, system_status

if __name__ == "__main__":
    results, status = run_full_audit()
    sys.exit(0 if status == "PASS" else 1)
