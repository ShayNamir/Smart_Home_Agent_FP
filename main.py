from agent_runner import AgentRunner, ModelType
import time

def start_menu()->tuple[str,ModelType]:
    user_input= input("""please choose the architecture:
1.standard
2.cot
3.react
4.reflexion
5.tot
""")

    arch="standard"
    if user_input=="1":
        arch="standard"
    elif user_input=="2":
        arch="cot"
    elif user_input=="3":
        arch="react"
    elif user_input=="4":
        arch="reflexion"
    elif user_input=="5":
        arch="tot"
    else:
        # Error
        print("Error: Invalid input")
        exit()

    user_input="1"
#    user_input= input("""Please choose the model:
#1.qwen3:4b
#2.gemma3:4b
#3.mistral:latest
#4.phi3:mini
#5.deepseek-r1:1.5b
#""")
    model=ModelType.OLLAMA_QWEN3_4B
    if user_input=="1":
        model=ModelType.OLLAMA_QWEN3_4B
    elif user_input=="2":
        model=ModelType.OLLAMA_GEMMA3_4B
    elif user_input=="3":
        model=ModelType.OLLAMA_MISTRAL
    elif user_input=="4":
        model=ModelType.OLLAMA_PHI3_MINI
    elif user_input=="5":
        model=ModelType.OLLAMA_DEEPSEEK_R1
    else:
        # Error
        print("Error: Invalid input")
        exit()
    # print to the user the model and the architecture
    print(f"The model is {model}")
    print(f"The architecture is {arch}")
    return arch,model


def main():
    arch,model=start_menu()
    while True:
        runner = AgentRunner(request_timeout=60)  
        text = input("Enter your prompt: ")
        if text.lower() == 'exit':
            print("Goodbye! 👋")
            break
        elif not text:
            continue
        start_time = time.time()
        print(runner.run(arch, text, model))
        end_time = time.time()
        print(f"Time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
