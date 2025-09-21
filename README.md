# 🏠 Smart Home Agent Final Project

<div align="center">

![Academic Research](https://img.shields.io/badge/Academic-Research-purple?style=for-the-badge&logo=graduation-cap)
![Computer Science](https://img.shields.io/badge/Computer%20Science-Final%20Project-blue?style=for-the-badge&logo=code)
![Ariel University](https://img.shields.io/badge/Ariel%20University-Research-green?style=for-the-badge&logo=university)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)

**🎓 Academic Research: AI-powered Smart Home Agent with Architecture & Model Comparison**

*Final Project for Computer Science Degree at Ariel University*

</div>

---

## 📋 Research Overview

This academic research project investigates the effectiveness of different AI architectures for smart home automation tasks. The study develops a sophisticated smart home agent powered by local AI models (Ollama) and provides comprehensive comparison between various AI approaches.

### 🎯 Research Objectives

- 🧠 **Architecture Evaluation** - Compare Standard, CoT, ReAct, Reflexion, and ToT approaches
- 🔬 **Model Performance Analysis** - Evaluate multiple local AI models
- 📊 **Benchmarking Framework** - Develop comprehensive testing methodology
- 🏠 **Smart Home Integration** - Real-world testing with Home Assistant
- 📈 **Performance Metrics** - Detailed analysis of speed, accuracy, and efficiency

---

## 🏗️ Project Structure

```
🏠 Smart_Home_Agent_FP/
├── 🤖 agent_runner.py          # Main agent orchestrator
├── 🚀 main.py                  # Project entry point
├── ⚙️ core/                    # Core system components
│   ├── 🔌 ha.py               # Home Assistant interface
│   └── 📦 objects.py          # Base objects & configurations
├── 🧠 src/smart_home_agent/    # AI agent source code
│   └── 🏛️ architectures/      # AI architecture implementations
├── 📈 architecture_benchmark/  # Architecture benchmarking & results
│   ├── 🏗️ arch_benchmark.py   # Architecture comparison
│   ├── 🤖 model_benchmark.py  # Model performance analysis
│   └── 📊 architecture_bench.xlsx # Architecture benchmark results
├── 🔬 benchmark_models/        # Model testing & results
│   ├── 🏃 benchmark_runner.py  # Benchmark execution engine
│   ├── 📝 benchmark_commands.py # Test command definitions
│   └── 📊 LLM_benchmark_2.0.xlsx # Model benchmark results
├── ⚙️ config/                  # Configuration files
├── 📚 docs/                    # Documentation
└── 🛠️ scripts/                 # Utility scripts
```

---

## 🚀 Quick Start

### 📋 Prerequisites

- 🐍 **Python 3.8+**
- 🏠 **Home Assistant** (installed and running)
- 🦙 **Ollama** with local models

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShayNamir/Smart_Home_Agent_FP.git
   cd Smart_Home_Agent_FP
   ```

2. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Setup Ollama models**
   ```bash
   # Install recommended models
   ollama pull phi3:mini
   ollama pull llama3.2
   ollama pull mistral
   ollama pull qwen3:4b
   ollama pull gemma3:4b
   ollama pull deepseek-r1:1.5b
   ```

### 🎯 Usage Examples

#### 🏃‍♂️ Running the Main Agent
```bash
python main.py
```

#### 📊 Architecture Benchmarking
```bash
cd architecture_benchmark
python arch_benchmark.py
```

#### 🔬 Model Performance Testing
```bash
cd benchmark_models
python benchmark_runner.py
```

---

## 🧠 Supported AI Architectures

| Architecture | Description | Use Case |
|--------------|-------------|----------|
| 🎯 **Standard** | Basic direct approach | Simple commands |
| 💭 **CoT** | Chain of Thought | Complex reasoning |
| 🔄 **ReAct** | Reasoning and Acting | Interactive tasks |
| 🔍 **Reflexion** | Self-reflection | Error correction |
| 🌳 **ToT** | Tree of Thoughts | Multi-step planning |

---

## 🤖 Supported AI Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| 🦙 **phi3:mini** | Small | ⚡ Fast | ⭐ Good |
| 🦙 **llama3.2** | Medium | 🐌 Medium | ⭐⭐ Better |
| 🌪️ **mistral** | Medium | 🐌 Medium | ⭐⭐ Better |
| 🧠 **qwen3:4b** | Medium | 🐌 Medium | ⭐⭐⭐ Best |
| 💎 **gemma3:4b** | Medium | 🐌 Medium | ⭐⭐⭐ Best |
| 🚀 **deepseek-r1:1.5b** | Small | ⚡ Fast | ⭐⭐ Better |

---

## 🎮 Command Categories

### 🔧 Action Commands
- 💡 Turn on/off lights
- 🔒 Lock/unlock doors
- 🌪️ Control fans
- 🔌 Manage switches

### 📊 Status Queries
- 🔍 Check device states
- 📈 Monitor system status
- 📋 List available devices

### ⚠️ Error Handling
- 🚫 Handle non-existent devices
- 🔄 Retry failed commands
- 📝 Log error patterns

---

## 📊 Research Results & Analysis

The research generates comprehensive Excel reports featuring:

- 📈 **Performance Metrics** - Speed and accuracy comparisons across architectures
- 🏆 **Architecture Rankings** - Statistical analysis of best performing approaches
- 📊 **Model Analysis** - Detailed performance breakdowns by model type
- ⏱️ **Execution Statistics** - Timing and efficiency data analysis
- 📋 **Category Analysis** - Performance evaluation by command type
- 📚 **Research Documentation** - Academic findings and conclusions

---

## 🤝 Academic Collaboration

This research project welcomes academic collaboration and contributions:

1. 🍴 **Fork** the repository for your research
2. 🌿 **Create** a research branch (`git checkout -b research/YourResearchArea`)
3. 💾 **Commit** your findings (`git commit -m 'Add research findings'`)
4. 📤 **Push** to the branch (`git push origin research/YourResearchArea`)
5. 🔄 **Open** a Pull Request for academic review

### 🎯 Research Areas for Collaboration

- 🧠 **New AI Architectures** - Implement and test novel approaches
- 🤖 **Model Extensions** - Add support for additional AI models
- 📊 **Enhanced Benchmarking** - Improve testing methodologies
- 🏠 **Domain Applications** - Apply to other smart home scenarios
- 📚 **Academic Documentation** - Contribute to research literature

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👥 Academic Contact & Information

- 👨‍💻 **Researcher**: Shay Namir
- 🎓 **Institution**: Ariel University
- 📚 **Department**: Computer Science
- 🎯 **Project Type**: Final Project for Bachelor's Degree
- 📧 **Academic Email**: [Your Academic Email]
- 🔗 **Repository**: [GitHub Repository](https://github.com/ShayNamir/Smart_Home_Agent_FP)
- 💬 **Research Discussion**: [Open Research Discussion](https://github.com/ShayNamir/Smart_Home_Agent_FP/issues)

---

## 🙏 Academic Acknowledgments

Special thanks to:

- 🎓 **Ariel University** - Computer Science Department for academic support
- 👨‍🏫 **Academic Supervisors** - For guidance and research direction
- 🌟 **Open Source Community** - For providing essential tools and libraries
- 🏠 **Home Assistant Team** - For the incredible smart home platform
- 🦙 **Ollama Team** - For local AI model support and research tools
- 👥 **Research Community** - For inspiration and academic collaboration

---

<div align="center">

**⭐ Star this repository if you found the research valuable!**

*Academic research made with ❤️ for the smart home and AI communities*

**🎓 Final Project for Computer Science Degree at Ariel University**

</div>
