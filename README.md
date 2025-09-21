# 🏠 Smart Home Agent Final Project

<div align="center">

![Smart Home](https://img.shields.io/badge/Smart%20Home-AI%20Powered-blue?style=for-the-badge&logo=home-assistant)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**🤖 AI-powered Smart Home Agent with Architecture & Model Comparison**

*Intelligent automation meets cutting-edge AI research*

</div>

---

## 📋 Project Overview

This project develops a sophisticated smart home agent powered by local AI models (Ollama) and provides comprehensive comparison between different AI architectures for smart home automation tasks.

### ✨ Key Features

- 🧠 **Smart Home Agent** with local model support
- 🏗️ **Architecture Comparison** (Standard, CoT, ReAct, Reflexion, ToT)
- 🔬 **Model Performance Analysis** across multiple local models
- 📊 **Comprehensive Benchmarking** with detailed Excel reports
- 🎯 **Real-time Device Control** via Home Assistant integration

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
├── 📈 bench/                   # Architecture benchmarking
│   ├── 🏗️ arch_benchmark.py   # Architecture comparison
│   └── 🤖 model_benchmark.py  # Model performance analysis
├── 🔬 benchmark_models/        # Advanced model testing
│   ├── 🏃 benchmark_runner.py  # Benchmark execution engine
│   └── 📝 benchmark_commands.py # Test command definitions
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
cd bench
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

## 📊 Output & Reports

The system generates comprehensive Excel reports featuring:

- 📈 **Performance Metrics** - Speed and accuracy comparisons
- 🏆 **Architecture Rankings** - Best performing approaches
- 📊 **Model Analysis** - Detailed performance breakdowns
- ⏱️ **Execution Statistics** - Timing and efficiency data
- 📋 **Category Analysis** - Performance by command type

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. 🍴 **Fork** the project
2. 🌿 **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 **Push** to the branch (`git push origin feature/AmazingFeature`)
5. 🔄 **Open** a Pull Request

### 🎯 Contribution Areas

- 🧠 New AI architectures
- 🤖 Additional model support
- 📊 Enhanced benchmarking
- 🐛 Bug fixes and improvements
- 📚 Documentation updates

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👥 Contact & Support

- 👨‍💻 **Author**: Shay Namir
- 📧 **Email**: [Your Email]
- 🔗 **Project**: [GitHub Repository](https://github.com/ShayNamir/Smart_Home_Agent_FP)
- 💬 **Issues**: [Report a Bug](https://github.com/ShayNamir/Smart_Home_Agent_FP/issues)

---

## 🙏 Acknowledgments

Special thanks to:

- 🌟 **Open Source Community** for amazing tools and libraries
- 🏠 **Home Assistant Team** for the incredible platform
- 🦙 **Ollama Team** for local AI model support
- 👥 **Contributors** who helped shape this project

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

*Made with ❤️ for the smart home community*

</div>
