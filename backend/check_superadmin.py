"""Скрипт для проверки и создания суперадмина"""
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(__file__))

# Импортируем все модели для корректной работы SQLAlchemy
from app.db.base import *  # noqa: F401, F403
from app.db.session import SessionLocal
from app.services import user_service
from app.core.security import verify_password, get_password_hash
from app.schemas.user import UserCreate

def check_or_create_superadmin():
    """Проверить существование суперадмина и создать, если не существует"""
    db = SessionLocal()
    try:
        email = "superadmin@example.com"
        password = "superadmin123"
        
        print("="*60)
        print("ПРОВЕРКА СУПЕРАДМИНА")
        print("="*60)
        
        # Проверяем, существует ли пользователь
        user = user_service.get_user_by_email(db, email)
        
        if user:
            print(f"✅ Пользователь {email} найден")
            print(f"   ID: {user.id}")
            print(f"   is_admin: {user.is_admin}")
            print(f"   is_superadmin: {user.is_superadmin}")
            print(f"   is_blocked: {user.is_blocked}")
            print(f"   password_hash (первые 50 символов): {user.password_hash[:50]}...")
            
            # Проверяем пароль
            password_valid = verify_password(password, user.password_hash)
            print(f"   Проверка пароля: {'✅ ВЕРНЫЙ' if password_valid else '❌ НЕВЕРНЫЙ'}")
            
            if not password_valid:
                print(f"\n⚠️  Пароль НЕ совпадает! Обновляем пароль...")
                user.password_hash = get_password_hash(password)
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"✅ Пароль обновлен")
                
                # Проверяем еще раз
                if verify_password(password, user.password_hash):
                    print(f"✅ Пароль работает после обновления")
                else:
                    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Пароль не работает после обновления!")
            
            # Проверяем, что суперадмин установлен
            if not user.is_superadmin:
                print(f"\n⚠️  is_superadmin = False, обновляем...")
                user.is_superadmin = True
                user.is_admin = True
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"✅ is_superadmin установлен в True")
            
            if user.is_blocked:
                print(f"\n⚠️  Пользователь заблокирован! Разблокируем...")
                user.is_blocked = False
                db.add(user)
                db.commit()
                print(f"✅ Пользователь разблокирован")
        else:
            print(f"❌ Пользователь {email} НЕ найден, создаем...")
            try:
                user = user_service.create_user(
                    db,
                    UserCreate(
                        email=email,
                        password=password,
                        full_name="Super Admin",
                        phone="+70000000003",
                        is_admin=True,
                        is_superadmin=True,
                    ),
                )
                print(f"✅ Пользователь создан:")
                print(f"   ID: {user.id}")
                print(f"   is_admin: {user.is_admin}")
                print(f"   is_superadmin: {user.is_superadmin}")
                
                # Проверяем пароль после создания
                if verify_password(password, user.password_hash):
                    print(f"✅ Пароль работает корректно")
                else:
                    print(f"❌ ОШИБКА: Пароль не работает после создания!")
            except ValueError as e:
                print(f"❌ Ошибка создания: {e}")
        
        print("\n" + "="*60)
        print("ФИНАЛЬНЫЙ ТЕСТ ЛОГИНА")
        print("="*60)
        test_user = user_service.verify_user_credentials(db, email, password)
        if test_user:
            print(f"✅ ЛОГИН РАБОТАЕТ!")
            print(f"   Пользователь: {test_user.email}")
            print(f"   is_admin: {test_user.is_admin}")
            print(f"   is_superadmin: {test_user.is_superadmin}")
        else:
            print(f"❌ ЛОГИН НЕ РАБОТАЕТ!")
            print(f"   Проверьте логи выше для диагностики")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_or_create_superadmin()

