import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from app.core.config import settings

def run_ingestion():
    # 1. Загружаем документы
    loader = DirectoryLoader('./data/knowledge_base', glob="**/*.md", loader_cls=TextLoader)
    raw_docs = loader.load()
    
    # 2. Нарезаем на чанки
    # chunk_overlap нужен, чтобы смысл не терялся на стыке кусков
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = text_splitter.split_documents(raw_docs)
    
    # 3. Подключаем эмбеддинги (превращаем текст в числа)
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    # 4. Инициализируем клиент Qdrant и создаем хранилище
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    QdrantVectorStore.from_documents(
        docs,
        embeddings,
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name="support_kb",
        force_recreate=True  # Для разработки — перезаписываем базу при каждом запуске
    )
    print(f"Successfully indexed {len(docs)} chunks to Qdrant.")

if __name__ == "__main__":
    run_ingestion()
