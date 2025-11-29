"""Миграция: добавление поля is_superadmin в таблицу users"""
import sqlite3
import os

# Путь к файлу базы данных
# Используем относительный путь, как в settings.py
DB_FILE = os.path.join(os.path.dirname(__file__), "app.db")

def migrate():
    print(f"Добавление поля is_superadmin в таблицу users...")
    print(f"База данных: {DB_FILE}")

    if not os.path.exists(DB_FILE):
        print(f"База данных не найдена: {DB_FILE}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Проверяем, существует ли колонка is_superadmin
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if "is_superadmin" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN NOT NULL DEFAULT FALSE")
            conn.commit()
            print("✅ Колонка is_superadmin успешно добавлена")
        else:
            print("ℹ️ Колонка is_superadmin уже существует, пропуск")

        print("✅ Миграция завершена успешно")

    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()

