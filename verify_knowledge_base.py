#!/usr/bin/env python3
"""
Скрипт для проверки и анализа созданной базы знаний.
"""

import json
from pathlib import Path
from collections import Counter
import random

def analyze_knowledge_base() -> None:
    kb_dir = Path("knowledge_base")
    terms_map_file = Path("terms_map.json")

    print("=" * 70)
    print("АНАЛИЗ БАЗЫ ЗНАНИЙ")
    print("=" * 70)
    print()

    if not kb_dir.exists():
        print("❌ Папка knowledge_base/ не найдена!")
        print("   Сначала запустите: python knowledge_base_generator.py")
        return

    if not terms_map_file.exists():
        print("❌ Файл terms_map.json не найден!")
        return

    with open(terms_map_file, "r", encoding="utf-8") as f:
        terms_map = json.load(f)

    print(f"✓ Словарь замен загружен: {len(terms_map)} терминов")
    print()

    files = list(kb_dir.glob("*.txt"))
    print(f"✓ Найдено файлов: {len(files)}")
    print()

    categories = Counter()
    total_chars = 0
    total_words = 0
    total_lines = 0

    for file in files:
        if file.name.startswith("character_"):
            categories["Персонажи"] += 1
        elif file.name.startswith("planet_"):
            categories["Планеты"] += 1
        elif file.name.startswith("tech_"):
            categories["Технологии"] += 1
        elif file.name.startswith("org_"):
            categories["Организации"] += 1
        elif file.name.startswith("concept_"):
            categories["Концепции"] += 1
        elif file.name.startswith("event_"):
            categories["События"] += 1

        content = file.read_text(encoding="utf-8")
        total_chars += len(content)
        total_words += len(content.split())
        total_lines += len(content.splitlines())

    print("СТАТИСТИКА ПО КАТЕГОРИЯМ:")
    print("-" * 70)
    for cat, count in sorted(categories.items()):
        print(f"  {cat:<20} {count:>3} документов")
    print()

    print("ОБЩАЯ СТАТИСТИКА:")
    print("-" * 70)
    print(f"  Всего документов:        {len(files)}")
    print(f"  Всего символов:          {total_chars:,}")
    print(f"  Всего слов:              {total_words:,}")
    print(f"  Всего строк:             {total_lines:,}")
    avg_words = total_words // len(files) if files else 0
    print(f"  Среднее слов/документ:   {avg_words}")
    print()

    print("ПРИМЕРЫ ЗАМЕН (первые 10):")
    print("-" * 70)
    for i, (orig, repl) in enumerate(list(terms_map.items())[:10], 1):
        print(f"  {i:2d}. {orig:<25} → {repl}")
    print()

    print("ПРОВЕРКА УНИКАЛЬНОСТИ:")
    print("-" * 70)
    replacements = list(terms_map.values())
    dups = [r for r in replacements if replacements.count(r) > 1]
    if dups:
        print(f"  ⚠ Найдены дубликаты в заменах: {len(set(dups))}")
        for d in set(dups):
            print(f"    - {d}")
    else:
        print("  ✓ Все замены уникальны")
    print()

    print("ПРОВЕРКА КАЧЕСТВА:")
    print("-" * 70)
    sample_files = random.sample(files, min(3, len(files)))
    for file in sample_files:
        content = file.read_text(encoding="utf-8")
        found_originals = []
        for original in terms_map.keys():
            if original.lower() in content.lower():
                found_originals.append(original)
        if found_originals:
            print(f"  ⚠ В файле {file.name} найдены оригинальные термины:")
            for term in found_originals[:5]:
                print(f"    - {term}")
        else:
            print(f"  ✓ {file.name} - все термины заменены")
    print()

    print("=" * 70)
    print("ИТОГОВАЯ ОЦЕНКА:")
    print("=" * 70)

    score = 0
    max_score = 5

    if len(files) >= 30:
        print("  ✓ Количество документов достаточно (30+)")
        score += 1
    else:
        print(f"  ⚠ Недостаточно документов ({len(files)}/30)")

    if len(categories) >= 4:
        print("  ✓ Разнообразие категорий хорошее (4+)")
        score += 1
    else:
        print(f"  ⚠ Мало категорий ({len(categories)}/4)")

    if total_words >= 3000:
        print("  ✓ Объём контента достаточный (3000+ слов)")
        score += 1
    else:
        print(f"  ⚠ Мало контента ({total_words}/3000 слов)")

    if not dups:
        print("  ✓ Все замены уникальны")
        score += 1
    else:
        print("  ⚠ Есть дубликаты в заменах")

    if len(terms_map) >= 50:
        print("  ✓ Словарь замен достаточно большой (50+ терминов)")
        score += 1
    else:
        print(f"  ⚠ Мало терминов в словаре ({len(terms_map)}/50)")

    print()
    print(f"  ОЦЕНКА: {score}/{max_score}")
    if score == max_score:
        print("  Отлично! База знаний готова для использования в RAG.")
    elif score >= 3:
        print("  Хорошо. База знаний пригодна для использования.")
    else:
        print("  Требуется доработка базы знаний.")
    print()
    print("=" * 70)

def show_sample_documents() -> None:
    kb_dir = Path("knowledge_base")
    if not kb_dir.exists():
        return

    print()
    print("=" * 70)
    print("ПРИМЕРЫ ДОКУМЕНТОВ")
    print("=" * 70)
    print()

    prefixes = ["character_", "planet_", "tech_", "org_", "concept_", "event_"]
    for prefix in prefixes:
        files = list(kb_dir.glob(f"{prefix}*.txt"))
        if files:
            sample = files[0]
            content = sample.read_text(encoding="utf-8")
            print(f"Файл: {sample.name}")
            print("-" * 70)
            print(content[:300] + "..." if len(content) > 300 else content)
            print()

if __name__ == "__main__":
    analyze_knowledge_base()
    show_sample_documents()