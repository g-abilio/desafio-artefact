from app.agent import build_agent

def ask_agent(agent, user_input: str, thread_id: str = "terminal-session") -> str:
    """
    Envia uma mensagem mantendo o histórico da conversa da sessão.
    """

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content


def main():
    print("****EMPÓRIO DA MÚSICA****")
    print("Digite 'sair' para encerrar.")

    agent = build_agent()

    while True:
        try:
            user_input = input("Usuário: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input == "sair":
            print("Assistente: Até logo!")
            break

        if not user_input:
            continue

        try:
            answer = ask_agent(agent, user_input)
            print("Assistente:", answer)
        except Exception:
            print("Assistente: Não consegui processar a solicitação. Tente novamente em instantes.")

if __name__ == "__main__":
    main()
