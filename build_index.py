#!/usr/bin/env python3
"""
build_index.py
Создание векторного индекса из базы знаний (knowledge_base/)
с помощью all-MiniLM-L6-v2 и ChromaDB.
"""

import os
import time
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# --- Конфигурация ---

KB_DIR = Path("knowledge_base")           # папка с .txt из Задания 2
CHROMA_DIR = "chroma_db"                  # куда сохранять индекс
COLLECTION_NAME = "kb_chunks"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 800       # ~100–200 слов
CHUNK_OVERLAP = 200    # небольшой overlap для контекста

# --- Загрузка модели эмбеддингов ---

def load_embedder() -> SentenceTransformer:
    print(f"[INIT] Загрузка модели эмбеддингов: {EMBED_MODEL_NAME}")
    t0 = time.time()
    model = SentenceTransformer(EMBED_MODEL_NAME)
    print(f"[INIT] Модель загружена за {time.time() - t0:.2f} c")
    return model

# --- Чтение и чанкинг документов ---

def load_documents(kb_dir: Path) -> List[Dict]:
    if not kb_dir.exists():
        raise RuntimeError(f"Папка {kb_dir} не найдена. Сначала сгенерируй базу знаний (Задание 2).")

    docs = []
    for path in kb_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        docs.append(
            {
                "path": str(path),
                "title": path.stem,
                "text": text,
            }
        )
    print(f"[LOAD] Загружено документов: {len(docs)}")
    return docs

def chunk_documents(docs: List[Dict]) -> List[Dict]:
    print(f"[CHUNK] Разбиение документов на чанки (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )  # [web:54][web:60]

    chunks: List[Dict] = []
    for doc_id, doc in enumerate(docs):
        pieces = splitter.split_text(doc["text"])
        for chunk_idx, chunk_text in enumerate(pieces):
            chunks.append(
                {
                    "id": f"{doc_id}_{chunk_idx}",
                    "doc_id": doc_id,
                    "chunk_index": chunk_idx,
                    "text": chunk_text,
                    "source_path": doc["path"],
                    "title": doc["title"],
                }
            )

    print(f"[CHUNK] Получено чанков: {len(chunks)}")
    return chunks

# --- Индексация в ChromaDB ---

def build_chroma_index(chunks: List[Dict]) -> None:
    os.makedirs(CHROMA_DIR, exist_ok=True)

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )

    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )  # встроенная интеграция sentence-transformers в Chroma [web:58]

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
        metadata={"description": "KB chunks index", "model": EMBED_MODEL_NAME},
    )

    print("[INDEX] Добавление чанков в коллекцию...")
    t0 = time.time()

    batch_size = 128
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "source_path": c["source_path"],
                    "title": c["title"],
                    "chunk_index": c["chunk_index"],
                }
                for c in batch
            ],
        )

    dt = time.time() - t0
    print(f"[INDEX] Индексация завершена за {dt:.2f} c")
    print(f"[INDEX] Всего чанков в индексе: {collection.count()}")

# --- Пример запросов к индексу ---

def test_query(query: str, top_k: int = 3) -> None:
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(name=COLLECTION_NAME)

    print(f"\n[QUERY] Запрос: {query}")
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    for i in range(top_k):
        print("-" * 80)
        print(f"Результат {i+1}:")
        if "distances" in results:
            print(f"score: {results['distances'][0][i]:.4f}")
        meta = results["metadatas"][0][i]
        print(f"title: {meta['title']}")
        print(f"chunk_index: {meta['chunk_index']}")
        print("source:", meta["source_path"])
        print()
        print(results["documents"][0][i][:400], "...")
        print()

def main():
    t0 = time.time()

    docs = load_documents(KB_DIR)
    chunks = chunk_documents(docs)
    build_chroma_index(chunks)

    total_time = time.time() - t0
    print(f"[TOTAL] Полное время генерации индекса: {total_time:.2f} c")

    print("\n[TEST] Примеры запросов к индексу:")
    for q in [
        "Кто такой Xaran Veldor?",
        "Что такое Void Core?",
        "Опиши планету Zorix.",
    ]:
        test_query(q, top_k=3)

if __name__ == "__main__":
    main()