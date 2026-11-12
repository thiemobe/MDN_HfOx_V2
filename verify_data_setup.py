"""
Verification script to check that all main scripts point to correct data files
and can load them successfully.
"""

import os
import pandas as pd
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"✓ {description:50} - {filepath} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"✗ {description:50} - {filepath} [NOT FOUND]")
        return False

def check_csv_readable(filepath, description):
    """Check if a CSV file can be read."""
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"✓ {description:50} - {len(df)} rows")
        return True
    except Exception as e:
        print(f"✗ {description:50} - Error: {e}")
        return False

def main():
    print("=" * 80)
    print("DATA FILE VERIFICATION REPORT")
    print("=" * 80)
    
    all_ok = True
    
    print("\n1. Core Data Files:")
    print("-" * 80)
    all_ok &= check_file_exists("data/original_data.csv", "Original dataset (full)")
    all_ok &= check_file_exists("data/train_val_samples.csv", "Training/validation split")
    all_ok &= check_file_exists("data/test_samples.csv", "Test set split")
    all_ok &= check_file_exists("data/sweep_10_cycles.csv", "Cycle-by-cycle data")
    
    print("\n2. Reading Data Files:")
    print("-" * 80)
    try:
        df_train_val = pd.read_csv("data/train_val_samples.csv", encoding='utf-8-sig')
        print(f"✓ train_val_samples.csv readable        - {len(df_train_val)} rows, {len(df_train_val.columns)} columns")
    except Exception as e:
        print(f"✗ train_val_samples.csv readable        - Error: {e}")
        all_ok = False
    
    try:
        df_test = pd.read_csv("data/test_samples.csv", encoding='utf-8-sig')
        print(f"✓ test_samples.csv readable             - {len(df_test)} rows, {len(df_test.columns)} columns")
    except Exception as e:
        print(f"✗ test_samples.csv readable             - Error: {e}")
        all_ok = False
    
    print("\n3. Script Data File References:")
    print("-" * 80)
    
    # Check training_and_validation.py
    try:
        with open("training_and_validation.py", "r") as f:
            content = f.read()
            if "data/train_val_samples.csv" in content:
                print("✓ training_and_validation.py            - Uses train_val_samples.csv")
            else:
                print("✗ training_and_validation.py            - Incorrect data file reference")
                all_ok = False
    except Exception as e:
        print(f"✗ training_and_validation.py            - Error: {e}")
        all_ok = False
    
    # Check predictions_for_testset.py
    try:
        with open("predictions_for_testset.py", "r") as f:
            content = f.read()
            if "data/test_samples.csv" in content:
                print("✓ predictions_for_testset.py            - Uses test_samples.csv")
            else:
                print("✗ predictions_for_testset.py            - Incorrect data file reference")
                all_ok = False
    except Exception as e:
        print(f"✗ predictions_for_testset.py            - Error: {e}")
        all_ok = False
    
    # Check figures/1f_conductance_distibution.py
    try:
        with open("figures/1f_conductance_distibution.py", "r") as f:
            content = f.read()
            if "data/test_samples.csv" in content:
                print("✓ 1f_conductance_distibution.py         - Uses test_samples.csv")
            else:
                print("✗ 1f_conductance_distibution.py         - Incorrect data file reference")
                all_ok = False
    except Exception as e:
        print(f"✗ 1f_conductance_distibution.py         - Error: {e}")
        all_ok = False
    
    print("\n4. Summary:")
    print("-" * 80)
    if all_ok:
        print("✓ ALL CHECKS PASSED - Ready to run scripts with --rrun")
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please review the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
