import sys
from langchain_core.messages import HumanMessage
from app.agents.multiagent import multi_agent_system

def run_cli():
    print("=" * 60)
    print("🤖 Welcome to Pradeep's Multi-Agent Platform")
    print("Specialists Active: [Supervisor, ResearchAgent, CoderAgent]")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=" * 60 + "\n")

    config = {"configurable": {"thread_id": "pradeep_multiagent_session"}}

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Goodbye!")
                sys.exit(0)

            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            for event in multi_agent_system.stream(inputs, config=config):
                for node_name, value in event.items():
                    print(f"\n⚙️  [Active Node: {node_name}]")
                    if "messages" in value and value["messages"]:
                        last_msg = value["messages"][-1]
                        if last_msg.content:
                            print(f"🤖 {last_msg.content}")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_cli()