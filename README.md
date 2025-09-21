# Smart Home Agent Final Project

Final Project - AI-based Smart Home Agent with Architecture and Model Comparison

## Project Description

This project develops a smart home agent based on local AI models (Ollama) and compares different architectures for performing smart home tasks. The project includes:

- **Smart Home Agent** with support for local models
- **Architecture Comparison** (Standard, CoT, ReAct, Reflexion, ToT)
- **Local Model Comparison**
- **Comprehensive Benchmark** with detailed Excel reports

## Project Structure

```
Smart_Home_Agent_FP/
├── agent_runner.py          # Main component for running the agent
├── main.py                  # Main file for running the project
├── core/                    # Core components
│   ├── ha.py               # Home Assistant interface
│   └── objects.py          # Basic objects
├── src/smart_home_agent/    # Source code
│   └── architectures/      # AI architectures
├── bench/                   # Architecture benchmark
│   ├── arch_benchmark.py   # Architecture comparison
│   └── model_benchmark.py  # Model comparison
├── benchmark_models/        # New model benchmark
│   ├── benchmark_runner.py  # Running model benchmark
│   └── benchmark_commands.py # Benchmark commands
├── config/                  # Configuration files
├── docs/                    # Documentation
└── scripts/                 # Helper scripts
```

## Installation

### System Requirements

- Python 3.8+
- Home Assistant (installed and running)
- Ollama with local models

### Install Dependencies

```bash
pip install -r config/requirements.txt
```

### Install Models in Ollama

```bash
# Install recommended models
ollama pull phi3:mini
ollama pull llama3.2
ollama pull mistral
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull deepseek-r1:1.5b
```

## Usage

### Running the Main Agent

```bash
python main.py
```

### Architecture Benchmark

```bash
cd bench
python arch_benchmark.py
```

### Model Benchmark

```bash
cd benchmark_models
python benchmark_runner.py
```

## Supported Architectures

1. **Standard** - Basic architecture
2. **CoT** - Chain of Thought
3. **ReAct** - Reasoning and Acting
4. **Reflexion** - Self-reflection
5. **ToT** - Tree of Thoughts

## Supported Models

- phi3:mini
- llama3.2
- mistral
- qwen3:4b
- gemma3:4b
- deepseek-r1:1.5b

## Command Categories

- **Action Commands** - Turn on/off devices
- **Status Queries** - Check device status
- **Error Handling** - Commands for non-existent devices

## Output

The project creates detailed Excel reports with:

- Performance comparison between architectures
- Performance comparison between models
- Analysis by command categories
- Execution time statistics

## Contributing to the Project

1. Fork the project
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is distributed under the MIT license. See the `LICENSE` file for more details.

## Contact

- Author: [Author Name]
- Email: [Email Address]
- Project: [Project Link]

## Acknowledgments

Thanks to all contributors and the community who helped develop this project.
