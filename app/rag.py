from functools import lru_cache
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from app.config import config

@lru_cache(maxsize=1)
def get_policy_retriever():
    """
    Lê o PDF e cria o índice vetorial uma única vez durante a execução da aplicação, guardando-o em cache.
    """

    if not config.policies_path.exists():
        raise FileNotFoundError(
            f"PDF não encontrado: {config.policies_path}"
        )

    reader = PdfReader(config.policies_path)

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())

        if text.strip():
            pages.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": config.policies_path.name,
                        "page": page_number
                    },
                )
            )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 800,
        chunk_overlap = 120
    )
    chunks = text_splitter.split_documents(pages)
    embeddings = OllamaEmbeddings(
        model = config.ollama_embedding_model,
        base_url = config.ollama_base_url
    )

    vector_store = InMemoryVectorStore.from_documents(
        chunks,
        embedding=embeddings
    )

    return vector_store.as_retriever(
        search_kwargs={"k": 4}
    )

def retrieve_store_policies(question: str) -> str:
    """
    Recupera os trechos da política da loja mais relacionados à pergunta em foco.
    """

    retriever = get_policy_retriever()
    documents = retriever.invoke(question)

    if not documents:
        return "Nenhuma política relacionada foi encontrada."

    excerpts = []
    for document in documents:
        page = document.metadata.get("page", "?")

        excerpts.append(
            f"[Página {page}]\n{document.page_content}"
        )

    return "\n\n".join(excerpts)