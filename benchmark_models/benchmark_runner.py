"""
Smart Home Agent Benchmark Runner
מבצע מבחני ביצועים על מודלים מקומיים ומפיק דוח Excel
"""

import time
import json
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# הוספת הנתיב הראשי לפרויקט
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runner import AgentRunner, ModelType
from core.ha import get_entities_by_domain, get_entities_details, service_call
from benchmark_commands import (
    get_all_commands, 
    get_commands_by_category, 
    get_command_categories,
    get_category_weight,
    get_short_test_commands,
    get_long_test_commands
)

class ModelBenchmarkRunner:
    def __init__(self, iterations: int = 3):
        """
        אתחול הרצת הבנצ'מארק
        
        Args:
            iterations: מספר חזרות לכל פקודה (ברירת מחדל: 3)
        """
        self.iterations = iterations
        self.runner = AgentRunner(request_timeout=60)
        self.results = []
        
        # מודלים זמינים לבדיקה
        self.available_models = {
            "phi3:mini": ModelType.OLLAMA_PHI3_MINI,
            "llama3.2": ModelType.OLLAMA_LLAMA3_2,
            "mistral": ModelType.OLLAMA_MISTRAL,
            "qwen3:4b": ModelType.OLLAMA_QWEN3_4B,
            "gemma3:4b": ModelType.OLLAMA_GEMMA3_4B,
            "deepseek-r1:1.5b": ModelType.OLLAMA_DEEPSEEK_R1,
        }
        
        # מיפוי מכשירים ל-entity_id
        self.entity_map = {
            "light": {
                "Bed Light": "light.bed_light",
                "Ceiling Lights": "light.ceiling_lights",
                "Kitchen Lights": "light.kitchen_lights",
                "Office Lights": "light.office_lights",
                "Living Room Lights": "light.living_room_lights",
                "Entrance Lights": "light.entrance_lights",
            },
            "switch": {
                "Decorative Lights": "switch.decorative_lights",
            },
            "lock": {
                "Front Door": "lock.front_door",
                "Kitchen Door": "lock.kitchen_door",
                "Openable Lock": "lock.openable_lock",
            },
            "fan": {
                "Living Room Fan": "fan.living_room_fan",
                "Ceiling Fan": "fan.ceiling_fan",
                "Percentage Full Fan": "fan.percentage_full_fan",
                "Percentage Limited Fan": "fan.percentage_limited_fan",
                "Preset Only Limited Fan": "fan.preset_only_limited_fan",
            },
        }

    def _get_device_state(self, entity_id: str) -> Optional[str]:
        """מחזיר את המצב הנוכחי של המכשיר"""
        try:
            details = get_entities_details([entity_id])
            if details and len(details) > 0:
                return details[0].get("state", "unknown")
            return "not_found"
        except Exception:
            return "not_found"

    def _set_device_state(self, domain: str, entity_id: str, state: str) -> bool:
        """מגדיר את מצב המכשיר"""
        try:
            if domain in ["light", "switch", "fan"]:
                if state == "on":
                    service_call(domain, "turn_on", entity_id, {})
                elif state == "off":
                    service_call(domain, "turn_off", entity_id, {})
            elif domain == "lock":
                if state == "locked":
                    service_call(domain, "lock", entity_id, {})
                elif state == "unlocked":
                    service_call(domain, "unlock", entity_id, {})
            return True
        except Exception:
            return False

    def _find_device_for_command(self, command: str) -> Optional[Dict[str, str]]:
        """מוצא את המכשיר הרלוונטי לפקודה"""
        command_lower = command.lower()
        
        for domain, devices in self.entity_map.items():
            for device_name, entity_id in devices.items():
                if device_name.lower() in command_lower:
                    return {
                        "domain": domain,
                        "device_name": device_name,
                        "entity_id": entity_id
                    }
        return None

    def _determine_expected_states(self, command: str, device_info: Dict[str, str]) -> Dict[str, str]:
        """קובע את המצבים הצפויים לפני ואחרי הפקודה"""
        command_lower = command.lower()
        domain = device_info["domain"]
        
        if "turn on" in command_lower or "switch on" in command_lower or "activate" in command_lower or "start" in command_lower:
            return {"initial": "off", "final": "on"}
        elif "turn off" in command_lower or "switch off" in command_lower or "deactivate" in command_lower or "stop" in command_lower:
            return {"initial": "on", "final": "off"}
        elif "lock" in command_lower or "secure" in command_lower:
            return {"initial": "unlocked", "final": "locked"}
        elif "unlock" in command_lower or "open" in command_lower:
            return {"initial": "locked", "final": "unlocked"}
        else:
            return {"initial": "unknown", "final": "unknown"}

    def run_single_test(self, model_name: str, command: str, category: str) -> Dict[str, Any]:
        """
        מריץ מבחן יחיד עם מודל ופקודה
        
        Args:
            model_name: שם המודל
            command: הפקודה לבדיקה
            category: קטגוריית הפקודה
            
        Returns:
            תוצאות המבחן
        """
        try:
            # אתחול משתנים
            device_entity_id = None
            actual_initial_state = None
            actual_final_state = None
            expected_initial_state = None
            expected_final_state = None
            
            # מציאת המכשיר הרלוונטי
            device_info = self._find_device_for_command(command)
            
            if device_info and category == "action_commands":
                device_entity_id = device_info["entity_id"]
                domain = device_info["domain"]
                
                # קביעת המצבים הצפויים
                states = self._determine_expected_states(command, device_info)
                expected_initial_state = states["initial"]
                expected_final_state = states["final"]
                
                # הגדרת המכשיר למצב התחלתי צפוי
                if expected_initial_state != "unknown":
                    self._set_device_state(domain, device_entity_id, expected_initial_state)
                    time.sleep(1)  # המתנה לעדכון המצב
                
                # קבלת המצב ההתחלתי
                actual_initial_state = self._get_device_state(device_entity_id)
                
            elif device_info and category == "status_queries":
                device_entity_id = device_info["entity_id"]
                actual_initial_state = self._get_device_state(device_entity_id)
            
            # הרצת הפקודה עם המודל
            start_time = time.time()
            response = self.runner.run("standard", command, self.available_models[model_name])
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # ניקוי התגובה
            response = self._clean_response(response)
            
            # קבלת המצב הסופי
            if device_info:
                time.sleep(2)  # המתנה לסיום הפעולה
                actual_final_state = self._get_device_state(device_entity_id)
            
            # הערכת הצלחה
            success = self._evaluate_success(response, command, category, 
                                          expected_final_state, actual_final_state)
            
            result = {
                'model': model_name,
                'command': command,
                'category': category,
                'response': response,
                'execution_time': execution_time,
                'success': success,
                'error': None,
                'device_entity_id': device_entity_id,
                'expected_initial_state': expected_initial_state,
                'expected_final_state': expected_final_state,
                'actual_initial_state': actual_initial_state,
                'actual_final_state': actual_final_state
            }
            
            return result
            
        except Exception as e:
            return {
                'model': model_name,
                'command': command,
                'category': category,
                'response': None,
                'execution_time': None,
                'success': None,
                'error': str(e),
                'device_entity_id': device_entity_id,
                'expected_initial_state': expected_initial_state,
                'expected_final_state': expected_final_state,
                'actual_initial_state': actual_initial_state,
                'actual_final_state': actual_final_state
            }

    def _clean_response(self, response: str) -> str:
        """מנקה את תגובת המודל"""
        if not response:
            return response
        
        import re
        
        # הסרת תגיות חשיבה
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        response = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL)
        
        # ניקוי רווחים מיותרים
        response = re.sub(r'\n\s*\n', '\n', response)
        response = response.strip()
        
        return response

    def _evaluate_success(self, response: str, command: str, category: str, 
                         expected_final: str, actual_final: str) -> Optional[bool]:
        """מעריך את הצלחת הפקודה"""
        if not response:
            return False
        
        response_lower = response.lower()
        
        # עבור פקודות שגיאה - מצפים שהמודל יזהה את השגיאה
        if category == "error_handling":
            error_indicators = [
                "not found", "doesn't exist", "unknown", "error", 
                "invalid", "ambiguous", "unclear", "missing", "couldn't find",
                "no such device", "doesn't recognize", "not available"
            ]
            return any(indicator in response_lower for indicator in error_indicators)
        
        # עבור שאילתות סטטוס - מצפים לתגובה אינפורמטיבית
        if category == "status_queries":
            status_indicators = [
                "state", "status", "is", "currently", "off", "on", 
                "locked", "unlocked", "running", "stopped", "working",
                "active", "inactive", "enabled", "disabled"
            ]
            return any(indicator in response_lower for indicator in status_indicators)
        
        # עבור פקודות פעולה - מצפים לאישור הפעולה
        if category == "action_commands":
            action_indicators = [
                "turned on", "turned off", "activated", "deactivated",
                "locked", "unlocked", "started", "stopped", "successfully",
                "done", "completed", "executed", "performed", "switched",
                "changed", "updated", "modified"
            ]
            response_success = any(indicator in response_lower for indicator in action_indicators)
            
            # בדיקה נוספת של שינוי מצב המכשיר
            if expected_final and actual_final:
                state_success = (expected_final == actual_final)
                return response_success and state_success
            
            return response_success
        
        return True

    def _get_command_category(self, command: str) -> str:
        """קובע את קטגוריית הפקודה"""
        for category in get_command_categories():
            commands = get_commands_by_category(category)
            if command in commands:
                return category
        return "unknown"

    def run_benchmark(self, test_type: str = "short", models: List[str] = None) -> List[Dict[str, Any]]:
        """
        מריץ את הבנצ'מארק המלא
        
        Args:
            test_type: סוג המבחן - "short" או "long"
            models: רשימת מודלים לבדיקה. אם None, בודק את כל המודלים
            
        Returns:
            רשימת כל תוצאות המבחנים
        """
        if models is None:
            models = list(self.available_models.keys())
        
        # בחירת הפקודות לפי סוג המבחן
        if test_type == "short":
            commands = get_short_test_commands()
        else:
            commands = get_long_test_commands()
        
        total_tests = len(models) * len(commands) * self.iterations
        current_test = 0
        
        print(f"מתחיל בנצ'מארק עם {len(models)} מודלים, {len(commands)} פקודות, {self.iterations} חזרות")
        print(f"סה\"כ מבחנים: {total_tests}")
        print("=" * 60)
        
        for model in models:
            print(f"\nבודק מודל: {model}")
            print("-" * 40)
            
            for command in commands:
                category = self._get_command_category(command)
                
                for iteration in range(self.iterations):
                    current_test += 1
                    print(f"התקדמות: {current_test}/{total_tests} - {model}: {command[:50]}...")
                    
                    result = self.run_single_test(model, command, category)
                    self.results.append(result)
                    
                    # השהייה קצרה כדי לא להעמיס על המערכת
                    time.sleep(0.1)
        
        print(f"\nהבנצ'מארק הושלם! סה\"כ תוצאות: {len(self.results)}")
        return self.results

    def generate_excel_report(self, filename: str = None) -> str:
        """
        יוצר דוח Excel מהתוצאות עם נוסחאות
        
        Args:
            filename: שם קובץ הפלט. אם None, יוצר שם עם חותמת זמן
            
        Returns:
            נתיב לקובץ ה-Excel שנוצר
        """
        if not self.results:
            raise ValueError("אין תוצאות ליצירת דוח. הרץ בנצ'מארק קודם.")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"smart_home_model_benchmark_{timestamp}.xlsx"
        
        # שמירה בתיקיית תוצאות
        results_dir = "benchmark_results"
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        # יצירת DataFrame
        df = pd.DataFrame(self.results)
        
        # יצירת Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # גיליון תוצאות ראשי עם נוסחאות
            self._create_results_sheet_with_formulas(writer, df)
            
            # גיליון סיכום עם נוסחאות
            self._create_summary_sheet_with_formulas(writer, df)
            
            # גיליון השוואת מודלים עם נוסחאות
            self._create_model_comparison_sheet_with_formulas(writer, df)
            
            # גיליון ניתוח קטגוריות עם נוסחאות
            self._create_category_analysis_sheet_with_formulas(writer, df)
        
        print(f"דוח Excel נוצר עם נוסחאות: {filepath}")
        return filepath

    def _create_results_sheet_with_formulas(self, writer, df):
        """יוצר גיליון תוצאות ראשי עם נוסחאות"""
        # כתיבת הנתונים
        df.to_excel(writer, sheet_name='All Results', index=False)
        
        # קבלת workbook ו-worksheet
        workbook = writer.book
        worksheet = writer.sheets['All Results']
        
        # הוספת נוסחאות לעמודת הצלחה
        if 'expected_final_state' in df.columns and 'actual_final_state' in df.columns:
            expected_col = df.columns.get_loc('expected_final_state') + 1
            actual_col = df.columns.get_loc('actual_final_state') + 1
            actual_initial_col = df.columns.get_loc('actual_initial_state') + 1
            success_col = df.columns.get_loc('success') + 1
            error_col = df.columns.get_loc('error') + 1
            category_col = df.columns.get_loc('category') + 1
            
            # נוסחה: אם יש שגיאה, הצלחה ריקה, אחרת בדיקה לפי קטגוריה
            for row in range(2, len(df) + 2):
                formula = f'=IF(NOT(ISBLANK({chr(64+error_col)}{row})),"",IF({chr(64+category_col)}{row}="status_queries",IF(AND(NOT(ISBLANK({chr(64+actual_initial_col)}{row})),NOT(ISBLANK({chr(64+actual_col)}{row}))),{chr(64+actual_initial_col)}{row}={chr(64+actual_col)}{row},TRUE),IF({chr(64+category_col)}{row}="action_commands",IF(AND(NOT(ISBLANK({chr(64+expected_col)}{row})),NOT(ISBLANK({chr(64+actual_col)}{row}))),{chr(64+expected_col)}{row}={chr(64+actual_col)}{row},TRUE),TRUE)))'
                worksheet.cell(row=row, column=success_col, value=formula)

    def _create_summary_sheet_with_formulas(self, writer, df):
        """יוצר גיליון סיכום סטטיסטיקות עם נוסחאות"""
        summary_data = [
            {'Metric': 'Total Tests', 'Formula': '=COUNTA(\'All Results\'!A:A)-1'},
            {'Metric': 'Successful Tests', 'Formula': '=COUNTIF(\'All Results\'!F:F,TRUE)'},
            {'Metric': 'Failed Tests', 'Formula': '=COUNTIF(\'All Results\'!F:F,FALSE)'},
            {'Metric': 'Error Tests', 'Formula': '=COUNTIF(\'All Results\'!H:H,"<>")'},
            {'Metric': 'Success Rate (%)', 'Formula': '=IF(B2+C2>0,B2/(B2+C2)*100,0)'},
            {'Metric': 'Average Execution Time (seconds)', 'Formula': '=AVERAGEIF(\'All Results\'!E:E,">0")'}
        ]
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        
        # הוספת נוסחאות לעמודת הערך
        for row in range(2, len(summary_data) + 2):
            formula = summary_data[row-2]['Formula']
            worksheet.cell(row=row, column=2, value=formula)

    def _create_model_comparison_sheet_with_formulas(self, writer, df):
        """יוצר גיליון השוואת מודלים עם נוסחאות"""
        model_data = []
        for model in self.available_models.keys():
            model_data.append({
                'Model': model,
                'Total Tests': f'=COUNTIF(\'All Results\'!A:A,"{model}")',
                'Success Rate (%)': f'=IF(B{len(model_data)+2}>0,COUNTIFS(\'All Results\'!A:A,"{model}",\'All Results\'!F:F,TRUE)/B{len(model_data)+2}*100,0)',
                'Average Time (s)': f'=AVERAGEIFS(\'All Results\'!E:E,\'All Results\'!A:A,"{model}",\'All Results\'!E:E,">0")',
                'Error Count': f'=COUNTIFS(\'All Results\'!A:A,"{model}",\'All Results\'!H:H,"<>")'
            })
        
        model_df = pd.DataFrame(model_data)
        model_df.to_excel(writer, sheet_name='Model Comparison', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Model Comparison']
        
        # הוספת נוסחאות לעמודות המתאימות
        for row in range(2, len(model_data) + 2):
            worksheet.cell(row=row, column=2, value=model_data[row-2]['Total Tests'])
            worksheet.cell(row=row, column=3, value=model_data[row-2]['Success Rate (%)'])
            worksheet.cell(row=row, column=4, value=model_data[row-2]['Average Time (s)'])
            worksheet.cell(row=row, column=5, value=model_data[row-2]['Error Count'])

    def _create_category_analysis_sheet_with_formulas(self, writer, df):
        """יוצר גיליון ניתוח קטגוריות עם נוסחאות"""
        category_data = []
        for category in get_command_categories():
            category_data.append({
                'Category': category,
                'Weight': get_category_weight(category),
                'Total Tests': f'=COUNTIF(\'All Results\'!C:C,"{category}")',
                'Success Rate (%)': f'=IF(C{len(category_data)+2}>0,COUNTIFS(\'All Results\'!C:C,"{category}",\'All Results\'!F:F,TRUE)/C{len(category_data)+2}*100,0)',
                'Average Time (s)': f'=AVERAGEIFS(\'All Results\'!E:E,\'All Results\'!C:C,"{category}",\'All Results\'!E:E,">0")'
            })
        
        category_df = pd.DataFrame(category_data)
        category_df.to_excel(writer, sheet_name='Category Analysis', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Category Analysis']
        
        # הוספת נוסחאות לעמודות המתאימות
        for row in range(2, len(category_data) + 2):
            worksheet.cell(row=row, column=3, value=category_data[row-2]['Total Tests'])
            worksheet.cell(row=row, column=4, value=category_data[row-2]['Success Rate (%)'])
            worksheet.cell(row=row, column=5, value=category_data[row-2]['Average Time (s)'])

    def save_results_json(self, filename: str = None) -> str:
        """שומר תוצאות כקובץ JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"model_benchmark_results_{timestamp}.json"
        
        results_dir = "benchmark_results"
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"תוצאות נשמרו ל-JSON: {filepath}")
        return filepath

def run_model_benchmark(test_type: str = "short", models: List[str] = None, iterations: int = 3):
    """
    פונקציה נוחה להרצת בנצ'מארק המודלים
    
    Args:
        test_type: סוג המבחן - "short" או "long"
        models: רשימת מודלים לבדיקה
        iterations: מספר חזרות לכל פקודה
    """
    runner = ModelBenchmarkRunner(iterations)
    
    print("מתחיל בנצ'מארק מודלים של Smart Home Agent")
    print("=" * 50)
    print(f"סוג מבחן: {test_type}")
    print(f"מודלים: {models or 'כל המודלים'}")
    print(f"חזרות לכל פקודה: {iterations}")
    
    # הרצת הבנצ'מארק
    results = runner.run_benchmark(test_type, models)
    
    # יצירת דוחות
    excel_file = runner.generate_excel_report()
    json_file = runner.save_results_json()
    
    print(f"\nהבנצ'מארק הושלם בהצלחה!")
    print(f"דוח Excel: {excel_file}")
    print(f"תוצאות JSON: {json_file}")
    
    return runner

if __name__ == "__main__":
    # בחירת סוג המבחן
    print("בחר סוג מבחן:")
    print("1. מבחן קצר (כ-20 פקודות)")
    print("2. מבחן ארוך (כל הפקודות)")
    
    choice = input("הזן בחירה (1/2): ").strip()
    
    if choice == "1":
        test_type = "short"
    elif choice == "2":
        test_type = "long"
    else:
        print("בחירה לא תקינה, משתמש במבחן קצר")
        test_type = "short"
    
    # בחירת מודלים
    runner = ModelBenchmarkRunner()
    print(f"\nמודלים זמינים: {list(runner.available_models.keys())}")
    model_choice = input("בחר מודלים (הזן מודלים מופרדים בפסיקים, או Enter לכל המודלים): ").strip()
    
    if model_choice:
        selected_models = [m.strip() for m in model_choice.split(",") if m.strip()]
        # בדיקת תקינות המודלים
        valid_models = [m for m in selected_models if m in runner.available_models]
        if not valid_models:
            print("אין מודלים תקינים, משתמש בכל המודלים")
            models = None
        else:
            models = valid_models
    else:
        models = None
    
    # הרצת הבנצ'מארק
    run_model_benchmark(test_type, models)
