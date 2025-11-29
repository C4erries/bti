#!/usr/bin/env python3
"""Миграция: добавление поля is_blocked в таблицу users"""
import sqlite3
import sys
from pathlib import Path

# Путь к базе данных
db_path = Path(__file__).parent / "app.db"

if not db_path.exists():
    print(f"База данных не найдена: {db_path}")
    sys.exit(1)

print(f"Добавление поля is_blocked в таблицу users...")
print(f"База данных: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Проверяем, существует ли уже колонка
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "is_blocked" in columns:
        print("✅ Колонка is_blocked уже существует")
    else:
        # Добавляем колонку
        cursor.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0 NOT NULL")
        conn.commit()
        print("✅ Колонка is_blocked успешно добавлена")
    
    conn.close()
    print("✅ Миграция завершена успешно")
    
except Exception as e:
    print(f"❌ Ошибка миграции: {e}")
    sys.exit(1)

