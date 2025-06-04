#!/usr/bin/env python3
"""
Test runner script for the WNSM sync project.
Runs all unit and integration tests.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests using pytest."""
    print("Running WNSM Sync Test Suite")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], cwd=project_dir, capture_output=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("🎉 All tests passed!")
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed!")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest:")
        print("pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_file):
    """Run a specific test file."""
    project_dir = Path(__file__).parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/{test_file}", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], cwd=project_dir, capture_output=False)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test {test_file}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        print(f"Running specific test: {test_file}")
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)