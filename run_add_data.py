#!/usr/bin/env python3
"""
Uruchom skrypt dodawania danych testowych
"""
import subprocess
import sys
import os

# Uruchom skrypt dodawania danych
try:
    result = subprocess.run([sys.executable, "add_test_data.py"], 
                          capture_output=True, text=True, cwd=os.getcwd())
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except Exception as e:
    print(f"Błąd: {e}")
