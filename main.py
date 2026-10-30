def main():
    print("Assistente de Projetos")
    print("Digite 'sair' para encerrar.")

    while True:
        mensagem = input("\nVocê: ").strip()

        if mensagem.lower() == "sair":
            print("Assistente: Até mais!")
            break

        if not mensagem:
            print("Assistente: Digite uma mensagem.")
            continue

        print(f"Assistente: Recebi sua mensagem: {mensagem}")


if __name__ == "__main__":
    main()
