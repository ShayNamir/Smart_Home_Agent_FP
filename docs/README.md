# 🤖 Smart Home AI Agent Research Project

A comprehensive research project comparing different AI architectures and models for smart home automation tasks using Home Assistant.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Architectures](#architectures)
- [Models](#models)
- [Benchmarking](#benchmarking)
- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)
- [Contributing](#contributing)

## 🎯 Overview

This project implements and compares multiple AI agent architectures for smart home control tasks. It provides:

- **5 Different Architectures**: Standard, Chain-of-Thought (CoT), ReAct, Reflexion, and Tree of Thoughts (ToT)
- **6 Local AI Models**: Various models via Ollama for fair comparison
- **Comprehensive Benchmarking**: Two benchmark systems for architecture and model comparison
- **Real Device Testing**: Integration with actual Home Assistant devices
- **Interactive Interface**: User-friendly command-line interface

## 📁 Project Structure

```
Smart_Home_Agent_FP/
├── 📁 Arch/                    # AI Architecture implementations
│   ├── standard.py            # Standard single-shot architecture
│   ├── cot.py                 # Chain-of-Thought architecture
│   ├── react.py               # ReAct (Reasoning + Acting) architecture
│   ├── reflexion.py           # Self-reflection architecture
│   └── tot.py                 # Tree of Thoughts architecture
│
├── 📁 core/                   # Core functionality
│   ├── ha.py                  # Home Assistant API integration
│   └── objects.py             # Data structures and system prompts
│
├── 📁 arch_bench/             # Architecture benchmarking system
│   ├── arch_benchmark.py      # Main benchmark runner
│   ├── benchmark_commands.py  # Test command definitions
│   └── bench_results/         # Benchmark results (Excel files)
│
├── 📁 model_bench/            # Model benchmarking system
│   ├── model_benchmark.py     # Model comparison runner
│   ├── main.py                # Interactive benchmark interface
│   ├── benchmark_commands.py  # Test command definitions
│   └── bench_results/         # Model comparison results
│
├── agent_runner.py            # Core agent runner and model management
└── main.py                    # Interactive demo interface
```

## ✨ Features

### 🏗️ Multiple Architectures
- **Standard**: Direct single-shot responses
- **Chain-of-Thought (CoT)**: Step-by-step reasoning with planning
- **ReAct**: Iterative reasoning and acting cycles
- **Reflexion**: Self-reflection and error correction
- **Tree of Thoughts (ToT)**: Multiple reasoning paths exploration

### 🤖 Local AI Models
- **phi3:mini** - Microsoft Phi-3 Mini (3.8B parameters)
- **llama3.2** - Meta Llama 3.2 (3B parameters)
- **mistral** - Mistral AI (7B parameters)
- **qwen3:4b** - Qwen 3 4B (4B parameters)
- **gemma3:4b** - Google Gemma 3 4B (4B parameters)
- **deepseek-r1:1.5b** - DeepSeek R1 1.5B (1.5B parameters)

### 📊 Comprehensive Benchmarking
- **Architecture Benchmark**: Compare different AI architectures
- **Model Benchmark**: Compare different AI models
- **Real Device Testing**: Tests against actual Home Assistant devices
- **Statistical Analysis**: Comprehensive Excel reports with formulas
- **Resume Capability**: Continue interrupted benchmarks

### 🏠 Smart Home Integration
- **Home Assistant API**: Full integration with HA REST API
- **Device Control**: Lights, switches, locks, fans, and more
- **Status Queries**: Real-time device state checking
- **Error Handling**: Robust error detection and handling

## 🏗️ Architectures

### 1. Standard Architecture
```python
# Direct single-shot response
User: "Turn on the bedroom light"
Agent: "Bedroom light turned on."
```

### 2. Chain-of-Thought (CoT)
```python
# Step-by-step reasoning
User: "Turn on the bedroom light"
Agent: 
1. Plan: Find bedroom light → Turn it on
2. Execute: get_entities_by_domain("light") → service_call("light", "turn_on", "light.bedroom")
3. Result: "Bedroom light turned on."
```

### 3. ReAct (Reasoning + Acting)
```python
# Iterative reasoning and acting
User: "Turn on the bedroom light"
Agent:
Thought: I need to find the bedroom light first
Action: get_entities_by_domain("light")
Observation: Found light.bedroom_light
Thought: Now I can turn it on
Action: service_call("light", "turn_on", "light.bedroom_light")
Result: "Bedroom light turned on."
```

### 4. Reflexion
```python
# Self-reflection and error correction
User: "Turn on the bedroom light"
Agent:
1. Initial attempt: Try to turn on light
2. Reflection: Did it work? Check result
3. Correction: If failed, try different approach
4. Result: "Bedroom light turned on."
```

### 5. Tree of Thoughts (ToT)
```python
# Multiple reasoning paths
User: "Turn on the bedroom light"
Agent:
- Path 1: Direct approach
- Path 2: Search first, then act
- Path 3: Check status first
- Best path: Execute and return result
```

## 🤖 Models

All models are run locally via Ollama for privacy and performance:

| Model | Parameters | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| phi3:mini | 3.8B | ⚡⚡⚡ | ⭐⭐⭐ | Fast testing |
| llama3.2 | 3B | ⚡⚡⚡ | ⭐⭐⭐⭐ | Balanced |
| mistral | 7B | ⚡⚡ | ⭐⭐⭐⭐⭐ | High quality |
| qwen3:4b | 4B | ⚡⚡ | ⭐⭐⭐⭐ | Balanced |
| gemma3:4b | 4B | ⚡⚡ | ⭐⭐⭐⭐ | Balanced |
| deepseek-r1:1.5b | 1.5B | ⚡⚡⚡⚡ | ⭐⭐⭐ | Ultra fast |

## 📊 Benchmarking

### Architecture Benchmark
Compare different AI architectures using the same model:

```bash
cd arch_bench
python arch_benchmark.py
```

**Profiles:**
- `core` - Core architectures (ReAct, Reflexion, ToT) - ~180 tests
- `all` - All architectures - ~300 tests
- `custom` - Custom architecture selection

### Model Benchmark
Compare different AI models using the same architecture:

```bash
cd model_bench
python main.py
```

**Profiles:**
- `micro` - Quick test (20 tests)
- `lite` - Light test (36 tests)  
- `core` - Standard test (59 tests)
- `long` - Comprehensive test (306 tests)

### Benchmark Results

Both benchmarks generate comprehensive Excel reports with:

- **All Results**: Complete test data
- **Summary**: Statistical analysis
- **Model/Architecture Comparison**: Performance metrics
- **Category Analysis**: Performance by test type
- **Formulas**: Dynamic calculations

## 🚀 Installation

### Prerequisites

1. **Python 3.8+**
2. **Home Assistant** running and accessible
3. **Ollama** installed with desired models

### Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd Smart_Home_Agent_FP
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure Home Assistant:**
   - Update `core/ha.py` with your HA URL and token
   - Ensure devices are properly configured

4. **Install Ollama models:**
```bash
ollama pull phi3:mini
ollama pull llama3.2
ollama pull mistral
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull deepseek-r1:1.5b
```

## 💻 Usage

### Interactive Demo

Run the interactive demo to test different architectures and models:

```bash
python main.py
```

**Example session:**
```
Please choose the architecture:
1. standard
2. cot
3. react
4. reflexion
5. tot
Enter your choice: 3

The model is ModelType.OLLAMA_QWEN3_4B
The architecture is react

Enter your prompt: Turn on the bedroom light
Bedroom light turned on.
Time: 2.34 seconds

Enter your prompt: exit
Goodbye! 👋
```

### Architecture Benchmark

```bash
cd arch_bench
python arch_benchmark.py
```

**Interactive prompts:**
- Choose profile: `core`, `lite`, `micro`, `long`
- Choose architectures: `core`, `all`, or custom list
- Results saved to `bench_results/`

### Model Benchmark

```bash
cd model_bench
python main.py
```

**Interactive interface:**
- Choose test profile
- Select models to compare
- Set number of repeats
- View comprehensive results

## 📈 Results

### Sample Architecture Comparison

| Architecture | Success Rate | Avg Time | Error Rate |
|--------------|--------------|----------|------------|
| Standard | 85% | 1.2s | 15% |
| CoT | 92% | 2.1s | 8% |
| ReAct | 88% | 1.8s | 12% |
| Reflexion | 90% | 2.3s | 10% |
| ToT | 87% | 2.5s | 13% |

### Sample Model Comparison

| Model | Success Rate | Avg Time | Quality Score |
|-------|--------------|----------|---------------|
| phi3:mini | 82% | 0.8s | 7.2/10 |
| llama3.2 | 89% | 1.1s | 8.1/10 |
| mistral | 94% | 1.8s | 8.9/10 |
| qwen3:4b | 91% | 1.3s | 8.4/10 |
| gemma3:4b | 88% | 1.2s | 8.2/10 |
| deepseek-r1:1.5b | 79% | 0.6s | 6.8/10 |

## 🔧 Configuration

### Home Assistant Setup

Update `core/ha.py`:
```python
ha_object = HAObject(
    url="http://localhost:8123",  # Your HA URL
    token="your_long_lived_token"  # Your HA token
)
```

### Model Configuration

Models are configured in `agent_runner.py`:
```python
class ModelType(Enum):
    OLLAMA_QWEN3_4B = "ollama_qwen3_4b"
    OLLAMA_GEMMA3_4B = "ollama_gemma3_4b"
    # ... add more models
```

### Benchmark Configuration

Customize test profiles in `benchmark_commands.py`:
```python
DEVICES = {
    "light": ["Bed Light", "Ceiling Lights", ...],
    "switch": ["Decorative Lights"],
    "lock": ["Front Door", "Kitchen Door"],
    "fan": ["Living Room Fan", "Ceiling Fan"]
}
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### Benchmark Tests
```bash
# Quick architecture test
cd arch_bench && python arch_benchmark.py
# Choose: micro profile, core architectures

# Quick model test  
cd model_bench && python main.py
# Choose: micro profile, 2 models
```

## 📊 Performance Metrics

The benchmarks measure:

- **Success Rate**: Percentage of successful task completions
- **Execution Time**: Average time per task
- **Error Rate**: Percentage of failed tasks
- **Device Identification**: Accuracy of device recognition
- **Response Quality**: Human evaluation of responses

## 🔍 Troubleshooting

### Common Issues

1. **Home Assistant Connection**
   ```
   Error: Connection refused
   Solution: Check HA URL and token in core/ha.py
   ```

2. **Model Not Found**
   ```
   Error: Model not found
   Solution: Install model with `ollama pull <model_name>`
   ```

3. **Device Not Found**
   ```
   Error: Entity not found
   Solution: Update device names in benchmark_commands.py
   ```

### Debug Mode

Enable debug output:
```bash
export AGENT_DEBUG=1
python main.py
```

## 📚 Research Applications

This project is designed for:

- **AI Architecture Research**: Compare different reasoning approaches
- **Model Evaluation**: Benchmark local AI models
- **Smart Home Automation**: Real-world application testing
- **Performance Analysis**: Statistical comparison of approaches
- **Academic Research**: Reproducible experiments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
git clone <your-fork>
cd Smart_Home_Agent_FP
pip install -r requirements-dev.txt
pre-commit install
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Home Assistant** for the excellent automation platform
- **Ollama** for local AI model hosting
- **Pydantic AI** for the agent framework
- **OpenAI** for model compatibility

## 📞 Support

For questions and support:

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: [Your email]

---

**Happy Automating! 🏠🤖**
