#!/usr/bin/env python3
"""
דוגמה לשימוש בבנצ'מארק המודלים
"""

from benchmark_runner import ModelBenchmarkRunner, run_model_benchmark

def example_short_test():
    """דוגמה למבחן קצר"""
    print("=== מבחן קצר ===")
    
    # מבחן קצר עם מודל אחד
    runner = ModelBenchmarkRunner(iterations=1)
    results = runner.run_benchmark("short", ["phi3:mini"])
    
    # יצירת דוח
    excel_file = runner.generate_excel_report("short_test_example.xlsx")
    print(f"דוח נוצר: {excel_file}")

def example_long_test():
    """דוגמה למבחן ארוך"""
    print("=== מבחן ארוך ===")
    
    # מבחן ארוך עם מספר מודלים
    run_model_benchmark(
        test_type="long",
        models=["phi3:mini", "llama3.2"],
        iterations=2
    )

def example_custom_test():
    """דוגמה למבחן מותאם אישית"""
    print("=== מבחן מותאם ===")
    
    runner = ModelBenchmarkRunner(iterations=1)
    
    # רק פקודות פעולה
    from benchmark_commands import get_commands_by_category
    action_commands = get_commands_by_category("action_commands")[:5]  # רק 5 פקודות
    
    # הרצת המבחן
    results = []
    for command in action_commands:
        result = runner.run_single_test("phi3:mini", command, "action_commands")
        results.append(result)
    
    # שמירת התוצאות
    runner.results = results
    excel_file = runner.generate_excel_report("custom_test_example.xlsx")
    print(f"דוח מותאם נוצר: {excel_file}")

if __name__ == "__main__":
    print("דוגמאות לשימוש בבנצ'מארק המודלים")
    print("=" * 50)
    
    choice = input("בחר דוגמה (1=קצר, 2=ארוך, 3=מותאם): ").strip()
    
    if choice == "1":
        example_short_test()
    elif choice == "2":
        example_long_test()
    elif choice == "3":
        example_custom_test()
    else:
        print("בחירה לא תקינה")
