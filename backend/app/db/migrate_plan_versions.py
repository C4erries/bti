"""
Скрипт миграции для добавления колонок comment и created_by_id в таблицу order_plan_versions
Запускать из корня проекта: python3 -m backend.app.db.migrate_plan_versions
"""
import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь, чтобы избежать конфликтов импорта
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Используем стандартный sqlite3 напрямую
import sqlite3 as sqlite3_module

def migrate_plan_versions():
    """Добавляет колонки comment и created_by_id в таблицу order_plan_versions"""
    # Ищем базу данных в backend/app.db
    db_path = project_root / "backend" / "app.db"
    
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        return
    
    conn = sqlite3_module.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Проверяем существование колонок
        cursor.execute("PRAGMA table_info(order_plan_versions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'comment' not in columns:
            print("Добавление колонки 'comment'...")
            cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN comment TEXT")
            print("✓ Колонка 'comment' добавлена")
        else:
            print("✓ Колонка 'comment' уже существует")
        
        if 'created_by_id' not in columns:
            print("Добавление колонки 'created_by_id'...")
            cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN created_by_id TEXT")
            print("✓ Колонка 'created_by_id' добавлена")
        else:
            print("✓ Колонка 'created_by_id' уже существует")
        
        conn.commit()
        print("\n✅ Миграция завершена успешно!")
        
    except sqlite3_module.Error as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_plan_versions()

