from pathlib import Path


PASTA_PROJETO = Path(__file__).resolve().parent


def listar_arquivos() -> list[str]:
    """Lista os arquivos visíveis na pasta principal do projeto."""
    print("\n[Ferramenta] Executando listar_arquivos")

    arquivos = []

    for caminho in PASTA_PROJETO.iterdir():
        if caminho.is_file() and not caminho.name.startswith("."):
            arquivos.append(caminho.name)

    return sorted(arquivos)


if __name__ == "__main__":
    for nome in listar_arquivos():
        print(nome)
