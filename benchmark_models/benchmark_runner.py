"""
Smart Home Agent Benchmark Runner
Performs performance tests on local models and generates Excel reports
"""

import time
import json
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add the main project path
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
        Initialize benchmark runner
        
        Args:
            iterations: Number of repetitions per command (default: 3)
        """
        self.iterations = iterations
        self.runner = AgentRunner(request_timeout=60)
        self.results = []
        
        # Available models for testing
        self.available_models = {
            "phi3:mini": ModelType.OLLAMA_PHI3_MINI,
            "llama3.2": ModelType.OLLAMA_LLAMA3_2,
            "mistral": ModelType.OLLAMA_MISTRAL,
            "qwen3:4b": ModelType.OLLAMA_QWEN3_4B,
            "gemma3:4b": ModelType.OLLAMA_GEMMA3_4B,
            "deepseek-r1:1.5b": ModelType.OLLAMA_DEEPSEEK_R1,
        }
        
        # Device mapping to entity_id
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
        """Returns the current state of the device"""
        try:
            details = get_entities_details([entity_id])
            if details and len(details) > 0:
                return details[0].get("state", "unknown")
            return "not_found"
        except Exception:
            return "not_found"

    def _set_device_state(self, domain: str, entity_id: str, state: str) -> bool:
        """Sets the device state"""
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
        """Finds the relevant device for the command"""
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
        """Determines the expected states before and after the command"""
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
        Runs a single test with model and command
        
        Args:
            model_name: Model name
            command: Command to test
            category: Command category
            
        Returns:
            Test results
        """
        try:
            # Initialize variables
            device_entity_id = None
            actual_initial_state = None
            actual_final_state = None
            expected_initial_state = None
            expected_final_state = None
            
            # Find relevant device
            device_info = self._find_device_for_command(command)
            
            if device_info and category == "action_commands":
                device_entity_id = device_info["entity_id"]
                domain = device_info["domain"]
                
                # Determine expected states
                states = self._determine_expected_states(command, device_info)
                expected_initial_state = states["initial"]
                expected_final_state = states["final"]
                
                # Set device to expected initial state
                if expected_initial_state != "unknown":
                    self._set_device_state(domain, device_entity_id, expected_initial_state)
                    time.sleep(1)  # Wait for state update
                
                # Get initial state
                actual_initial_state = self._get_device_state(device_entity_id)
                
            elif device_info and category == "status_queries":
                device_entity_id = device_info["entity_id"]
                actual_initial_state = self._get_device_state(device_entity_id)
            
            # Run command with model
            start_time = time.time()
            response = self.runner.run("standard", command, self.available_models[model_name])
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Clean response
            response = self._clean_response(response)
            
            # Get final state
            if device_info:
                time.sleep(2)  # Wait for operation completion
                actual_final_state = self._get_device_state(device_entity_id)
            
            # Evaluate success
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
        """Cleans the model response"""
        if not response:
            return response
        
        import re
        
        # Remove thinking tags
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        response = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL)
        
        # Clean extra whitespace
        response = re.sub(r'\n\s*\n', '\n', response)
        response = response.strip()
        
        return response

    def _evaluate_success(self, response: str, command: str, category: str, 
                         expected_final: str, actual_final: str) -> Optional[bool]:
        """Evaluates command success"""
        if not response:
            return False
        
        response_lower = response.lower()
        
        # For error commands - expect model to identify the error
        if category == "error_handling":
            error_indicators = [
                "not found", "doesn't exist", "unknown", "error", 
                "invalid", "ambiguous", "unclear", "missing", "couldn't find",
                "no such device", "doesn't recognize", "not available"
            ]
            return any(indicator in response_lower for indicator in error_indicators)
        
        # For status queries - expect informative response
        if category == "status_queries":
            status_indicators = [
                "state", "status", "is", "currently", "off", "on", 
                "locked", "unlocked", "running", "stopped", "working",
                "active", "inactive", "enabled", "disabled"
            ]
            return any(indicator in response_lower for indicator in status_indicators)
        
        # For action commands - expect action confirmation
        if category == "action_commands":
            action_indicators = [
                "turned on", "turned off", "activated", "deactivated",
                "locked", "unlocked", "started", "stopped", "successfully",
                "done", "completed", "executed", "performed", "switched",
                "changed", "updated", "modified"
            ]
            response_success = any(indicator in response_lower for indicator in action_indicators)
            
            # Additional check of device state change
            if expected_final and actual_final:
                state_success = (expected_final == actual_final)
                return response_success and state_success
            
            return response_success
        
        return True

    def _get_command_category(self, command: str) -> str:
        """Determines the command category"""
        for category in get_command_categories():
            commands = get_commands_by_category(category)
            if command in commands:
                return category
        return "unknown"

    def run_benchmark(self, test_type: str = "short", models: List[str] = None) -> List[Dict[str, Any]]:
        """
        Runs the full benchmark
        
        Args:
            test_type: Test type - "short" or "long"
            models: List of models to test. If None, tests all models
            
        Returns:
            List of all test results
        """
        if models is None:
            models = list(self.available_models.keys())
        
        # Select commands by test type
        if test_type == "short":
            commands = get_short_test_commands()
        else:
            commands = get_long_test_commands()
        
        total_tests = len(models) * len(commands) * self.iterations
        current_test = 0
        
        print(f"Starting benchmark with {len(models)} models, {len(commands)} commands, {self.iterations} repetitions")
        print(f"Total tests: {total_tests}")
        print("=" * 60)
        
        for model in models:
            print(f"\nTesting model: {model}")
            print("-" * 40)
            
            for command in commands:
                category = self._get_command_category(command)
                
                for iteration in range(self.iterations):
                    current_test += 1
                    print(f"Progress: {current_test}/{total_tests} - {model}: {command[:50]}...")
                    
                    result = self.run_single_test(model, command, category)
                    self.results.append(result)
                    
                    # Short pause to avoid overloading the system
                    time.sleep(0.1)
        
        print(f"\nBenchmark completed! Total results: {len(self.results)}")
        return self.results

    def generate_excel_report(self, filename: str = None) -> str:
        """
        Generates Excel report from results with formulas
        
        Args:
            filename: Output filename. If None, creates name with timestamp
            
        Returns:
            Path to the created Excel file
        """
        if not self.results:
            raise ValueError("No results to create report. Run benchmark first.")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"smart_home_model_benchmark_{timestamp}.xlsx"
        
        # Save in results directory
        results_dir = "benchmark_results"
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        # Create DataFrame
        df = pd.DataFrame(self.results)
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main results sheet with formulas
            self._create_results_sheet_with_formulas(writer, df)
            
            # Summary sheet with formulas
            self._create_summary_sheet_with_formulas(writer, df)
            
            # Model comparison sheet with formulas
            self._create_model_comparison_sheet_with_formulas(writer, df)
            
            # Category analysis sheet with formulas
            self._create_category_analysis_sheet_with_formulas(writer, df)
        
        print(f"Excel report created with formulas: {filepath}")
        return filepath

    def _create_results_sheet_with_formulas(self, writer, df):
        """Creates main results sheet with formulas"""
        # Write data
        df.to_excel(writer, sheet_name='All Results', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['All Results']
        
        # Add formulas to success column
        if 'expected_final_state' in df.columns and 'actual_final_state' in df.columns:
            expected_col = df.columns.get_loc('expected_final_state') + 1
            actual_col = df.columns.get_loc('actual_final_state') + 1
            actual_initial_col = df.columns.get_loc('actual_initial_state') + 1
            success_col = df.columns.get_loc('success') + 1
            error_col = df.columns.get_loc('error') + 1
            category_col = df.columns.get_loc('category') + 1
            
            # Formula: if there's an error, success is empty, otherwise check by category
            for row in range(2, len(df) + 2):
                formula = f'=IF(NOT(ISBLANK({chr(64+error_col)}{row})),"",IF({chr(64+category_col)}{row}="status_queries",IF(AND(NOT(ISBLANK({chr(64+actual_initial_col)}{row})),NOT(ISBLANK({chr(64+actual_col)}{row}))),{chr(64+actual_initial_col)}{row}={chr(64+actual_col)}{row},TRUE),IF({chr(64+category_col)}{row}="action_commands",IF(AND(NOT(ISBLANK({chr(64+expected_col)}{row})),NOT(ISBLANK({chr(64+actual_col)}{row}))),{chr(64+expected_col)}{row}={chr(64+actual_col)}{row},TRUE),TRUE)))'
                worksheet.cell(row=row, column=success_col, value=formula)

    def _create_summary_sheet_with_formulas(self, writer, df):
        """Creates summary statistics sheet with formulas"""
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
        
        # Add formulas to value column
        for row in range(2, len(summary_data) + 2):
            formula = summary_data[row-2]['Formula']
            worksheet.cell(row=row, column=2, value=formula)

    def _create_model_comparison_sheet_with_formulas(self, writer, df):
        """Creates model comparison sheet with formulas"""
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
        
        # Add formulas to appropriate columns
        for row in range(2, len(model_data) + 2):
            worksheet.cell(row=row, column=2, value=model_data[row-2]['Total Tests'])
            worksheet.cell(row=row, column=3, value=model_data[row-2]['Success Rate (%)'])
            worksheet.cell(row=row, column=4, value=model_data[row-2]['Average Time (s)'])
            worksheet.cell(row=row, column=5, value=model_data[row-2]['Error Count'])

    def _create_category_analysis_sheet_with_formulas(self, writer, df):
        """Creates category analysis sheet with formulas"""
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
        
        # Add formulas to appropriate columns
        for row in range(2, len(category_data) + 2):
            worksheet.cell(row=row, column=3, value=category_data[row-2]['Total Tests'])
            worksheet.cell(row=row, column=4, value=category_data[row-2]['Success Rate (%)'])
            worksheet.cell(row=row, column=5, value=category_data[row-2]['Average Time (s)'])

    def save_results_json(self, filename: str = None) -> str:
        """Saves results as JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"model_benchmark_results_{timestamp}.json"
        
        results_dir = "benchmark_results"
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to JSON: {filepath}")
        return filepath

def run_model_benchmark(test_type: str = "short", models: List[str] = None, iterations: int = 3):
    """
    Convenient function for running model benchmark
    
    Args:
        test_type: Test type - "short" or "long"
        models: List of models to test
        iterations: Number of repetitions per command
    """
    runner = ModelBenchmarkRunner(iterations)
    
    print("Starting Smart Home Agent model benchmark")
    print("=" * 50)
    print(f"Test type: {test_type}")
    print(f"Models: {models or 'all models'}")
    print(f"Repetitions per command: {iterations}")
    
    # Run benchmark
    results = runner.run_benchmark(test_type, models)
    
    # Generate reports
    excel_file = runner.generate_excel_report()
    json_file = runner.save_results_json()
    
    print(f"\nBenchmark completed successfully!")
    print(f"Excel report: {excel_file}")
    print(f"JSON results: {json_file}")
    
    return runner

if __name__ == "__main__":
    # Choose test type
    print("Choose test type:")
    print("1. Short test (~20 commands)")
    print("2. Long test (all commands)")
    
    choice = input("Enter choice (1/2): ").strip()
    
    if choice == "1":
        test_type = "short"
    elif choice == "2":
        test_type = "long"
    else:
        print("Invalid choice, using short test")
        test_type = "short"
    
    # Choose models
    runner = ModelBenchmarkRunner()
    print(f"\nAvailable models: {list(runner.available_models.keys())}")
    model_choice = input("Choose models (enter models separated by commas, or Enter for all models): ").strip()
    
    if model_choice:
        selected_models = [m.strip() for m in model_choice.split(",") if m.strip()]
        # Validate models
        valid_models = [m for m in selected_models if m in runner.available_models]
        if not valid_models:
            print("No valid models, using all models")
            models = None
        else:
            models = valid_models
    else:
        models = None
    
    # Run benchmark
    run_model_benchmark(test_type, models)
