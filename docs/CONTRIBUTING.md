# Contributing to Smart Home AI Agent Research Project

Thank you for your interest in contributing to this research project! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/Smart_Home_Agent_FP.git
cd Smart_Home_Agent_FP
```

### 2. Set Up Development Environment
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 5. Test Your Changes
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Test specific architecture
python main.py
```

### 6. Submit a Pull Request
- Create a clear description of your changes
- Reference any related issues
- Ensure all tests pass

## 📋 Contribution Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write clear, descriptive variable names
- Add docstrings to functions and classes

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add new architecture implementation
fix: resolve device connection timeout
docs: update README with new features
test: add unit tests for model comparison
```

### Testing
- Add tests for new functionality
- Ensure existing tests still pass
- Test with different models and architectures
- Test with real Home Assistant devices when possible

## 🏗️ Architecture Contributions

### Adding New Architectures
1. Create a new file in `Arch/` directory
2. Implement the required interface:
   ```python
   def call_agent(user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
       # Your implementation
   ```
3. Add the architecture to `agent_runner.py`
4. Update benchmarks to include the new architecture
5. Add tests and documentation

### Architecture Requirements
- Must handle Home Assistant API calls
- Must return user-friendly responses
- Must handle errors gracefully
- Must respect timeout limits

## 🤖 Model Contributions

### Adding New Models
1. Add model to `ModelType` enum in `agent_runner.py`
2. Add model factory in `AgentRunner.__init__`
3. Update benchmark systems
4. Test with different architectures

### Model Requirements
- Must be compatible with Ollama
- Must support the required model interface
- Must handle errors gracefully
- Must be reasonably fast for real-time use

## 📊 Benchmark Contributions

### Adding New Test Commands
1. Update `benchmark_commands.py` in both benchmark directories
2. Add device mappings if needed
3. Test with real devices
4. Update documentation

### Adding New Metrics
1. Update benchmark runners
2. Modify Excel report generation
3. Add statistical analysis
4. Update documentation

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Python version
   - Operating system
   - Home Assistant version
   - Ollama version

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Expected vs actual behavior
   - Error messages (if any)

3. **Additional Context**
   - Screenshots if applicable
   - Log files if available
   - Related issues

## 💡 Feature Requests

When requesting features, please include:

1. **Use Case**
   - What problem does this solve?
   - How would you use this feature?

2. **Proposed Solution**
   - How should this work?
   - Any implementation ideas?

3. **Alternatives**
   - Other ways to solve the problem
   - Workarounds you've tried

## 📚 Documentation Contributions

### README Updates
- Keep information current
- Add new features and examples
- Improve clarity and organization

### Code Documentation
- Add docstrings to functions
- Update inline comments
- Explain complex algorithms

### Tutorial Contributions
- Step-by-step guides
- Example use cases
- Troubleshooting guides

## 🔍 Code Review Process

### For Contributors
- Respond to feedback promptly
- Make requested changes
- Ask questions if unclear
- Test changes thoroughly

### For Reviewers
- Be constructive and helpful
- Focus on code quality and functionality
- Test changes when possible
- Approve when ready

## 🏷️ Issue Labels

We use the following labels for issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `question` - Further information is requested
- `wontfix` - This will not be worked on

## 📞 Getting Help

If you need help:

1. **Check Documentation** - Read the README and code comments
2. **Search Issues** - Look for similar problems
3. **Ask Questions** - Open a new issue with the `question` label
4. **Join Discussions** - Use GitHub Discussions for general questions

## 🎯 Research Focus Areas

We're particularly interested in contributions related to:

- **New AI Architectures** - Novel reasoning approaches
- **Model Optimization** - Performance improvements
- **Benchmarking** - Better evaluation metrics
- **Real-world Applications** - Practical use cases
- **Error Handling** - Robustness improvements

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to this research project! 🚀
