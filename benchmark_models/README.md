# Smart Home Agent Model Benchmark

Package for comparing performance of local models for Smart Home Agent.

## Description

This package allows comparing the performance of different local models (Ollama) in Smart Home Agent tasks. The benchmark tests the models' ability to perform action commands, answer status queries, and handle errors.

## Features

- **Short Test**: ~20 selected commands for quick testing
- **Long Test**: All available commands for comprehensive testing
- **Model Comparison**: Testing multiple models in parallel
- **Excel Report**: Creating detailed reports with formulas
- **English Support**: English user interface

## Supported Models

- phi3:mini
- llama3.2
- mistral
- qwen3:4b
- gemma3:4b
- deepseek-r1:1.5b

## Command Categories

1. **Action Commands**: Turn on/off devices, lock/unlock
2. **Status Queries**: Check device status
3. **Error Handling**: Commands for non-existent or ambiguous devices

## Usage

### Direct Execution

```bash
cd benchmark_models
python benchmark_runner.py
```

### Usage as Module

```python
from benchmark_models import run_model_benchmark

# Short test with all models
run_model_benchmark("short")

# Long test with selected models
run_model_benchmark("long", ["phi3:mini", "llama3.2"])
```

### Advanced Usage

```python
from benchmark_models import ModelBenchmarkRunner

runner = ModelBenchmarkRunner(iterations=5)
results = runner.run_benchmark("short", ["phi3:mini"])
excel_file = runner.generate_excel_report()
```

## Output

The benchmark creates:

1. **Excel Report** (`smart_home_model_benchmark_YYYYMMDD_HHMM.xlsx`) with:
   - "All Results" sheet: All results
   - "Summary" sheet: General summary
   - "Model Comparison" sheet: Model comparison
   - "Category Analysis" sheet: Analysis by categories

2. **JSON File** (`model_benchmark_results_YYYYMMDD_HHMM.json`) with raw results

## Requirements

- Python 3.8+
- pandas
- openpyxl
- pydantic-ai
- Home Assistant API

## Installation

```bash
pip install pandas openpyxl pydantic-ai
```

## Notes

- The benchmark requires an active connection to Home Assistant
- It's recommended to run the short test first to verify system integrity
- Results are saved in the `benchmark_results` directory
