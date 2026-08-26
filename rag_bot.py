#!/usr/bin/env python3
"""
rag_bot.py
RAG-бот с Few-shot и Chain-of-Thought на локальной модели (Ollama)
или OpenAI API.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Для локальной модели используем Ollama + requests
import requests

# --- Конфигурация ---

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "kb_chunks"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# LLM конфиг: используем Ollama локально (по умолчанию)
LLM_ENDPOINT = "http://localhost:11434/api/generate"  # Ollama endpoint
LLM_MODEL = "mistral"  # или любая другая модель в Ollama

# Few-shot примеры из базы знаний
FEWSHOT_EXAMPLES = [
    {
        "q": "Расскажи о Xaran Veldor.",
        "a": "Xaran Veldor — герой Фронта Освобождения, сын Kaelona Morqara. "
             "Обучался как Sentinel под руководством Vexora Thosusa и Norex. "
             "Уничтожил первое Void Core и спас своего отца от тёмной стороны."
    },
    {
        "q": "Что такое Void Core?",
        "a": "Void Core — это боевая станция размером с луну, оснащённая супер-лазером, "
             "способным уничтожить планеты. Две такие станции были построены Имперским Доминионом."
    },
]

# --- Загрузка индекса из Chroma ---

def load_chroma_retriever():
    """Загружает Chroma индекс и возвращает retriever"""
    if not Path(CHROMA_DIR).exists():
        raise RuntimeError(f"Папка {CHROMA_DIR} не найдена. Сначала выполни build_index.py")

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(name=COLLECTION_NAME)
    return collection

# --- Few-shot примеры из базы ---

def get_fewshot_from_kb(collection) -> List[Dict]:
    """Извлекает реальные примеры из базы знаний"""
    examples = []

    # Первый пример: поиск персонажа
    results = collection.query(
        query_texts=["Кто такой Xaran Veldor?"],
        n_results=1
    )
    if results["documents"] and len(results["documents"][0]) > 0:
        examples.append({
            "q": "Кто такой Xaran Veldor?",
            "a": results["documents"][0][0][:200] + "..."
        })

    # Второй пример: поиск технологии
    results = collection.query(
        query_texts=["Что такое Void Core?"],
        n_results=1
    )
    if results["documents"] and len(results["documents"][0]) > 0:
        examples.append({
            "q": "Что такое Void Core?",
            "a": results["documents"][0][0][:200] + "..."
        })

    return examples if examples else FEWSHOT_EXAMPLES

# --- Retrieval ---

def retrieve_context(collection, query: str, top_k: int = 3) -> Tuple[str, List[Dict]]:
    """Получает релевантные чанки из Chroma"""
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    context_chunks = []
    context_text = ""

    for i in range(min(top_k, len(results["documents"][0]))):
        chunk = {
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source_path", "unknown"),
            "title": results["metadatas"][0][i].get("title", "unknown"),
        }
        context_chunks.append(chunk)
        context_text += f"[Источник {i+1}]: {chunk['title']}\n{chunk['text']}\n\n"

    return context_text, context_chunks

# --- Построение промпта с Few-shot и CoT ---

def build_prompt_with_fewshot_and_cot(
    query: str,
    context: str,
    fewshot_examples: List[Dict]
) -> str:
    """Строит промпт с Few-shot примерами и Chain-of-Thought инструкциями"""

    fewshot_section = "## Примеры из базы знаний:\n\n"
    for i, ex in enumerate(fewshot_examples, 1):
        fewshot_section += f"Пример {i}:\n"
        fewshot_section += f"Вопрос: {ex['q']}\n"
        fewshot_section += f"Ответ: {ex['a']}\n\n"

    prompt = f"""Ты помощник, работающий с внутренней базой знаний.
Отвечай только на основе предоставленной информации.
ВАЖНО: Объясняй свои шаги перед тем, как дать финальный ответ (Chain-of-Thought).

{fewshot_section}

## Текущая информация из базы знаний:

{context}

## Вопрос пользователя:
{query}

## Ответ (с объяснением шагов):

1. Сначала найду релевантную информацию в базе...
2. Проанализирую найденные данные...
3. Сформулирую ответ...

Ответ:"""

    return prompt

# --- LLM Inference ---

def query_ollama(prompt: str, model: str = LLM_MODEL) -> str:
    """Отправляет запрос к Ollama"""
    try:
        response = requests.post(
            LLM_ENDPOINT,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Ошибка: пустой ответ от модели")
    except requests.exceptions.ConnectionError:
        return ("Ошибка: Ollama не запущена. Запусти:\n"
                "  ollama serve\n"
                "И загрузи модель:\n"
                f"  ollama pull {model}")
    except Exception as e:
        return f"Ошибка при запросе к LLM: {e}"

# --- Основной RAG pipeline ---

def rag_query(user_query: str, collection) -> Dict:
    """Основной RAG пайплайн: retrieval → few-shot + CoT → LLM"""

    print(f"\n[RAG] Обработка запроса: {user_query}")

    # Retrieval
    t0 = time.time()
    context, chunks = retrieve_context(collection, user_query, top_k=3)
    retrieval_time = time.time() - t0
    print(f"[RETRIEVAL] Найдено {len(chunks)} чанков за {retrieval_time:.2f} c")

    # Few-shot примеры из базы
    fewshot = get_fewshot_from_kb(collection)

    # Построение промпта
    prompt = build_prompt_with_fewshot_and_cot(user_query, context, fewshot)

    # LLM inference
    print("[LLM] Генерирую ответ...")
    t0 = time.time()
    answer = query_ollama(prompt)
    llm_time = time.time() - t0
    print(f"[LLM] Ответ готов за {llm_time:.2f} c")

    return {
        "query": user_query,
        "answer": answer,
        "context_chunks": chunks,
        "retrieval_time": retrieval_time,
        "llm_time": llm_time,
        "fewshot_examples": len(fewshot),
    }

# --- REPL интерфейс ---

def main_repl():
    """Интерактивный REPL для RAG-бота"""
    print("=" * 80)
    print("RAG-бот: Few-shot + Chain-of-Thought")
    print("=" * 80)
    print("\nЗагружаю индекс...")

    try:
        collection = load_chroma_retriever()
        print(f"✓ Индекс загружен ({collection.count()} чанков)")
    except Exception as e:
        print(f"✗ Ошибка загрузки индекса: {e}")
        return

    print("\nКоманды:")
    print("  /exit или /quit - выход")
    print("  /help - помощь")
    print()

    while True:
        try:
            query = input("Твой вопрос: ").strip()

            if not query:
                continue

            if query.lower() in ["/exit", "/quit"]:
                print("До свидания!")
                break

            if query.lower() == "/help":
                print("\nЭтот RAG-бот использует:")
                print("  • Retrieval: поиск в Chroma DB")
                print("  • Few-shot: примеры из базы знаний")
                print("  • Chain-of-Thought: объяснение шагов")
                print("  • LLM: локальная модель Ollama\n")
                continue

            result = rag_query(query, collection)

            print("\n" + "=" * 80)
            print(f"ОТВЕТ ({result['llm_time']:.2f} c):\n")
            print(result["answer"])
            print("\n" + "=" * 80)
            print(f"ИСТОЧНИКИ ({result['retrieval_time']:.2f} c):")
            for i, chunk in enumerate(result["context_chunks"], 1):
                print(f"  {i}. {chunk['title']} ({chunk['source']})")
            print()

        except KeyboardInterrupt:
            print("\n\nПрограмма прервана.")
            break

# --- Примеры диалогов (для тестирования) ---

def test_examples(collection):
    """Примеры успешных диалогов и случаев, когда бот говорит 'не знаю'"""

    test_queries = [
        "Кто такой Xaran Veldor?",
        "Что такое Void Core?",
        "Опиши планету Zorix.",
        "Расскажи о Фронте Освобождения.",
        "Кто создал компанию Apple?",  # Должен ответить "не знаю"
    ]

    print("\n" + "=" * 80)
    print("ПРИМЕРЫ ДИАЛОГОВ")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Пример {i} ---\n")
        result = rag_query(query, collection)
        print(f"Q: {result['query']}\n")
        print(f"A: {result['answer'][:500]}...\n")
        print(f"Источники: {len(result['context_chunks'])} чанков\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        collection = load_chroma_retriever()
        test_examples(collection)
    else:
        main_repl()