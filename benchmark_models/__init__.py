"""
Smart Home Agent Model Benchmark Package
חבילה להשוואת ביצועים של מודלים מקומיים
"""

from .benchmark_runner import ModelBenchmarkRunner, run_model_benchmark
from .benchmark_commands import (
    get_all_commands,
    get_commands_by_category,
    get_command_categories,
    get_category_weight,
    get_short_test_commands,
    get_long_test_commands
)

__version__ = "1.0.0"
__author__ = "Smart Home Agent Team"

__all__ = [
    "ModelBenchmarkRunner",
    "run_model_benchmark",
    "get_all_commands",
    "get_commands_by_category", 
    "get_command_categories",
    "get_category_weight",
    "get_short_test_commands",
    "get_long_test_commands"
]
