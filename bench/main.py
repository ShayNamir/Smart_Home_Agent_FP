#!/usr/bin/env python3
"""
Model Benchmark Runner - Main Entry Point

This script runs benchmark tests comparing different local AI models
on smart home control tasks using the standard architecture.

Usage:
    python main.py
    python -m model_bench.main
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model_benchmark import ModelBenchmark, AVAILABLE_MODELS, select_tests_profile, PROFILE_DEFAULT

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🤖 Smart Home Model Benchmark Runner")
    print("=" * 60)
    print("This tool compares different local AI models on smart home tasks.")
    print("All models use the 'standard' architecture for fair comparison.")
    print()

def get_profile_choice():
    """Get benchmark profile from user"""
    print("📊 Benchmark Profiles:")
    print("  • long  - Full benchmark (~200+ tests)")
    print("  • core  - Core benchmark (~60 tests)")
    print("  • lite  - Light benchmark (~36 tests)")
    print("  • micro - Micro benchmark (~18 tests)")
    print()
    
    while True:
        choice = input("Choose profile [long/core/lite/micro] (default: core): ").strip().lower()
        if not choice:
            return PROFILE_DEFAULT
        if choice in ["long", "core", "lite", "micro"]:
            return choice
        print("❌ Invalid choice. Please select: long, core, lite, or micro")

def get_model_choice():
    """Get models to test from user"""
    print("\n🤖 Available Models:")
    for i, model in enumerate(AVAILABLE_MODELS.keys(), 1):
        print(f"  {i}. {model}")
    print()
    
    while True:
        choice = input("Choose models [all/custom] (default: all): ").strip().lower()
        if not choice or choice == "all":
            return list(AVAILABLE_MODELS.keys())
        
        if choice == "custom":
            print("\nEnter model names separated by commas:")
            print("Available:", ", ".join(AVAILABLE_MODELS.keys()))
            custom_input = input("Models: ").strip()
            if not custom_input:
                return list(AVAILABLE_MODELS.keys())
            
            models = [m.strip() for m in custom_input.split(",")]
            valid_models = [m for m in models if m in AVAILABLE_MODELS]
            
            if not valid_models:
                print("❌ No valid models found. Using all models.")
                return list(AVAILABLE_MODELS.keys())
            
            invalid_models = [m for m in models if m not in AVAILABLE_MODELS]
            if invalid_models:
                print(f"⚠️  Invalid models ignored: {', '.join(invalid_models)}")
            
            return valid_models
        
        print("❌ Invalid choice. Please select: all or custom")

def get_repeats_choice():
    """Get number of repeats from user"""
    print("\n🔄 Test Repeats:")
    print("  Each test will be run multiple times for statistical reliability.")
    print()
    
    while True:
        choice = input("Number of repeats per test (default: 1): ").strip()
        if not choice:
            return 1
        
        try:
            repeats = int(choice)
            if repeats < 1:
                print("❌ Number must be at least 1")
                continue
            if repeats > 10:
                confirm = input(f"⚠️  {repeats} repeats will take a long time. Continue? [y/N]: ").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            return repeats
        except ValueError:
            print("❌ Please enter a valid number")

def print_summary(profile, models, repeats):
    """Print test summary"""
    tests = select_tests_profile(profile)
    total_tests = len(models) * len(tests) * repeats
    
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    print(f"Profile: {profile}")
    print(f"Models: {', '.join(models)}")
    print(f"Tests per model: {len(tests)}")
    print(f"Repeats per test: {repeats}")
    print(f"Total tests: {total_tests}")
    
    # Estimate time
    estimated_minutes = total_tests * 0.5  # Rough estimate: 30 seconds per test
    print(f"Estimated time: ~{estimated_minutes:.0f} minutes")
    print("=" * 60)
    
    confirm = input("\n🚀 Start benchmark? [Y/n]: ").strip().lower()
    return confirm in ['', 'y', 'yes']

def main():
    """Main entry point"""
    try:
        print_banner()
        
        # Get user choices
        profile = get_profile_choice()
        models = get_model_choice()
        repeats = get_repeats_choice()
        
        # Show summary and confirm
        if not print_summary(profile, models, repeats):
            print("❌ Benchmark cancelled by user")
            return
        
        print("\n🚀 Starting benchmark...")
        print("=" * 60)
        
        # Run benchmark
        bench = ModelBenchmark(repeats=repeats)
        tests = select_tests_profile(profile)
        result_path = bench.run_tests(tests, models)
        
        print("\n" + "=" * 60)
        print("✅ Benchmark completed successfully!")
        print(f"📊 Results saved to: {result_path}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark interrupted by user")
        print("💡 Partial results may be saved in the checkpoint file")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Check your Home Assistant connection and model availability")

if __name__ == "__main__":
    main()
