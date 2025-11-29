#!/usr/bin/env python3
"""
Универсальный скрипт миграции базы данных
Добавляет недостающие колонки в таблицы при изменении моделей
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Выполняет миграции базы данных"""
    db_path = Path(__file__).parent / "app.db"
    
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        print("База будет создана автоматически при следующем запуске приложения")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("🔄 Выполнение миграций базы данных...\n")
        
        # Миграция 1: order_plan_versions
        cursor.execute("PRAGMA table_info(order_plan_versions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations_applied = 0
        
        if 'comment' not in columns:
            print("  ➕ Добавление колонки 'comment' в order_plan_versions...")
            cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN comment TEXT")
            migrations_applied += 1
        
        if 'created_by_id' not in columns:
            print("  ➕ Добавление колонки 'created_by_id' в order_plan_versions...")
            cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN created_by_id TEXT")
            migrations_applied += 1
        
        # Миграция 2: users.is_blocked
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_blocked' not in user_columns:
            print("  ➕ Добавление колонки 'is_blocked' в users...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0 NOT NULL")
            migrations_applied += 1
        
        # Миграция 3: users.is_superadmin
        if 'is_superadmin' not in user_columns:
            print("  ➕ Добавление колонки 'is_superadmin' в users...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0 NOT NULL")
            migrations_applied += 1
        
        conn.commit()
        
        if migrations_applied > 0:
            print(f"\n✅ Применено миграций: {migrations_applied}")
        else:
            print("\n✅ База данных актуальна, миграции не требуются")
        
    except sqlite3.Error as e:
        print(f"\n❌ Ошибка при миграции: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()

