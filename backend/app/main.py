from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.init_data import init_data
from app.db.session import engine
from app.db.base import *  # noqa: F401, F403

app = FastAPI(
    title="Умное БТИ",
    description="MVP платформы для клиентов, исполнителей и администраторов",
    version="0.1.0",
    swagger_ui_parameters={
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
    },
)

# CORS middleware должен быть добавлен ДО роутеров
# В режиме разработки разрешаем все origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В разработке разрешаем все origins
    allow_credentials=False,  # Нельзя использовать credentials с allow_origins=["*"]
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
    expose_headers=["*"],
    max_age=3600,
)

# Выполняем миграции БД ПЕРЕД созданием таблиц и инициализацией данных
try:
    from pathlib import Path
    import sqlite3
    
    # Проверяем, используется ли SQLite
    if settings.database_url.startswith("sqlite"):
        db_path_str = settings.database_url.replace("sqlite:///", "")
        # Обрабатываем относительные и абсолютные пути
        if not Path(db_path_str).is_absolute():
            db_path = Path(__file__).parent.parent / db_path_str
        else:
            db_path = Path(db_path_str)
        
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            try:
                # Проверяем существование таблицы users
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    # Миграция: users.is_blocked
                    cursor.execute("PRAGMA table_info(users)")
                    user_columns = [row[1] for row in cursor.fetchall()]
                    if 'is_blocked' not in user_columns:
                        print("🔄 Migrating: Adding is_blocked to users table...")
                        cursor.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0 NOT NULL")
                    
                    # Миграция: users.is_superadmin
                    if 'is_superadmin' not in user_columns:
                        print("🔄 Migrating: Adding is_superadmin to users table...")
                        cursor.execute("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0 NOT NULL")
                
                # Проверяем существование таблицы order_plan_versions
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_plan_versions'")
                if cursor.fetchone():
                    # Миграция: order_plan_versions.comment
                    cursor.execute("PRAGMA table_info(order_plan_versions)")
                    plan_columns = [row[1] for row in cursor.fetchall()]
                    if 'comment' not in plan_columns:
                        print("🔄 Migrating: Adding comment to order_plan_versions table...")
                        cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN comment TEXT")
                    
                    # Миграция: order_plan_versions.created_by_id
                    if 'created_by_id' not in plan_columns:
                        print("🔄 Migrating: Adding created_by_id to order_plan_versions table...")
                        cursor.execute("ALTER TABLE order_plan_versions ADD COLUMN created_by_id TEXT")
                
                conn.commit()
            except sqlite3.Error as e:
                print(f"⚠️  Migration warning: {e}")
                conn.rollback()
            finally:
                conn.close()
except Exception as e:
    print(f"⚠️  Migration error (may be expected on first run): {e}")

# create tables and seed minimal data for development
Base.metadata.create_all(bind=engine)
init_data()

app.include_router(api_router, prefix=settings.api_v1_prefix)

static_dir = Path(settings.static_root)
static_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.static_url, StaticFiles(directory=static_dir, check_dir=False), name="static")


@app.get(
    "/health",
    tags=["system"],
    summary="Проверка состояния",
    description="Простая проверка готовности сервера",
)
def healthcheck():
    return {"status": "ok"}
