from agent_runner import AgentRunner, ModelType
import time

def start_menu()->tuple[str,ModelType]:
    # First, ask for model selection
    print("🤖 Welcome to Smart Home Agent!")
    print("=" * 40)
    
    user_input = input("""Please choose the AI model:
1. phi3:mini (Fast, Small)
2. llama3.2 (Balanced)
3. mistral (High Quality)
4. qwen3:4b (Balanced)
5. gemma3:4b (Balanced)
6. deepseek-r1:1.5b (Ultra Fast)
Enter your choice (1-6): """)

    model = ModelType.OLLAMA_QWEN3_4B
    if user_input == "1":
        model = ModelType.OLLAMA_PHI3_MINI
    elif user_input == "2":
        model = ModelType.OLLAMA_LLAMA3_2
    elif user_input == "3":
        model = ModelType.OLLAMA_MISTRAL
    elif user_input == "4":
        model = ModelType.OLLAMA_QWEN3_4B
    elif user_input == "5":
        model = ModelType.OLLAMA_GEMMA3_4B
    elif user_input == "6":
        model = ModelType.OLLAMA_DEEPSEEK_R1
    else:
        print("❌ Error: Invalid input. Using default model (qwen3:4b)")
        model = ModelType.OLLAMA_QWEN3_4B

    print(f"✅ Selected model: {model}")
    print()

    # Then, ask for architecture selection
    user_input = input("""Please choose the AI architecture:
1. Standard (Direct approach)
2. CoT - Chain of Thought (Step-by-step reasoning)
3. ReAct - Reasoning and Acting (Interactive)
4. Reflexion (Self-reflection)
5. ToT - Tree of Thoughts (Multi-path exploration)
Enter your choice (1-5): """)

    arch = "standard"
    if user_input == "1":
        arch = "standard"
    elif user_input == "2":
        arch = "cot"
    elif user_input == "3":
        arch = "react"
    elif user_input == "4":
        arch = "reflexion"
    elif user_input == "5":
        arch = "tot"
    else:
        print("❌ Error: Invalid input. Using default architecture (standard)")
        arch = "standard"

    print(f"✅ Selected architecture: {arch}")
    print()
    print("🏠 Smart Home Agent is ready!")
    print("💡 Try commands like: 'turn on the bedroom light' or 'check the door status'")
    print("🚪 Type 'exit' to quit")
    print("=" * 40)
    
    return arch, model


def main():
    arch, model = start_menu()
    runner = AgentRunner(request_timeout=60)
    
    while True:
        try:
            text = input("\n🏠 Enter your command: ")
            if text.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye! Thanks for using Smart Home Agent!")
                break
            elif not text.strip():
                print("💡 Please enter a command or type 'exit' to quit")
                continue
            
            print("🤖 Processing your request...")
            start_time = time.time()
            
            try:
                response = runner.run(arch, text, model)
                end_time = time.time()
                
                print(f"✅ Response: {response}")
                print(f"⏱️  Execution time: {end_time - start_time:.2f} seconds")
                
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                print("💡 Please try a different command or check your Home Assistant connection")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Thanks for using Smart Home Agent!")
            break
        except EOFError:
            print("\n👋 Goodbye! Thanks for using Smart Home Agent!")
            break

if __name__ == "__main__":
    main()
