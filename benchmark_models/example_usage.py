#!/usr/bin/env python3
"""
Example usage for model benchmark
"""

from benchmark_runner import ModelBenchmarkRunner, run_model_benchmark

def example_short_test():
    """Example for short test"""
    print("=== Short Test ===")
    
    # Short test with one model
    runner = ModelBenchmarkRunner(iterations=1)
    results = runner.run_benchmark("short", ["phi3:mini"])
    
    # Generate report
    excel_file = runner.generate_excel_report("short_test_example.xlsx")
    print(f"Report created: {excel_file}")

def example_long_test():
    """Example for long test"""
    print("=== Long Test ===")
    
    # Long test with multiple models
    run_model_benchmark(
        test_type="long",
        models=["phi3:mini", "llama3.2"],
        iterations=2
    )

def example_custom_test():
    """Example for custom test"""
    print("=== Custom Test ===")
    
    runner = ModelBenchmarkRunner(iterations=1)
    
    # Only action commands
    from benchmark_commands import get_commands_by_category
    action_commands = get_commands_by_category("action_commands")[:5]  # Only 5 commands
    
    # Run the test
    results = []
    for command in action_commands:
        result = runner.run_single_test("phi3:mini", command, "action_commands")
        results.append(result)
    
    # Save results
    runner.results = results
    excel_file = runner.generate_excel_report("custom_test_example.xlsx")
    print(f"Custom report created: {excel_file}")

if __name__ == "__main__":
    print("Examples for using the model benchmark")
    print("=" * 50)
    
    choice = input("Choose example (1=short, 2=long, 3=custom): ").strip()
    
    if choice == "1":
        example_short_test()
    elif choice == "2":
        example_long_test()
    elif choice == "3":
        example_custom_test()
    else:
        print("Invalid choice")
