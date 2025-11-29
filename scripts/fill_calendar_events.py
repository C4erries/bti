#!/usr/bin/env python3
"""
Скрипт для наполнения базы данных случайными событиями календаря.
Использует API по адресу http://178.215.238.184:8000/
"""

import json
import random
import sys
from datetime import datetime, timedelta
from typing import Optional

import requests

API_BASE_URL = "http://178.215.238.184:8000/api/v1"

# Учетные данные исполнителя (из README)
EXECUTOR_EMAIL = "executor@example.com"
EXECUTOR_PASSWORD = "executor123"

# Случайные адреса для выездов
LOCATIONS = [
    "г. Москва, ул. Ленина, д. 10, кв. 25",
    "г. Москва, пр-т Мира, д. 45, кв. 12",
    "г. Москва, ул. Пушкина, д. 7, кв. 8",
    "г. Москва, ул. Гагарина, д. 23, кв. 15",
    "г. Москва, ул. Советская, д. 5, кв. 3",
    "г. Москва, ул. Центральная, д. 18, кв. 42",
    "г. Москва, ул. Новая, д. 12, кв. 7",
    "г. Москва, ул. Садовая, д. 30, кв. 11",
    "г. Москва, ул. Лесная, д. 9, кв. 5",
    "г. Москва, ул. Парковая, д. 15, кв. 20",
]


def login() -> Optional[str]:
    """Авторизация и получение JWT токена"""
    print(f"🔐 Авторизация как {EXECUTOR_EMAIL}...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": EXECUTOR_EMAIL, "password": EXECUTOR_PASSWORD},
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None
    
    data = response.json()
    token = data.get("accessToken")
    if not token:
        print("❌ Токен не получен")
        return None
    
    print("✅ Авторизация успешна")
    return token


def get_orders(token: str) -> list:
    """Получить список заказов исполнителя"""
    print("\n📋 Получение списка заказов...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/executor/orders",
        headers=headers,
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения заказов: {response.status_code}")
        print(f"Ответ: {response.text}")
        return []
    
    orders = response.json()
    print(f"✅ Найдено заказов: {len(orders)}")
    return orders


def create_calendar_event(
    token: str,
    order_id: str,
    start_time: datetime,
    end_time: datetime,
    location: Optional[str] = None,
) -> bool:
    """Создать событие календаря для заказа"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
        "location": location,
    }
    
    response = requests.post(
        f"{API_BASE_URL}/executor/orders/{order_id}/schedule-visit",
        headers=headers,
        json=payload,
    )
    
    if response.status_code in (200, 201):
        event = response.json()
        print(f"  ✅ Создано событие: {event.get('id', 'N/A')} для заказа {order_id}")
        return True
    else:
        print(f"  ❌ Ошибка создания события для заказа {order_id}: {response.status_code}")
        print(f"  Ответ: {response.text}")
        return False


def generate_random_datetime(start_days: int = -30, end_days: int = 60) -> datetime:
    """Генерирует случайную дату/время в заданном диапазоне"""
    now = datetime.now()
    start = now + timedelta(days=start_days)
    end = now + timedelta(days=end_days)
    
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    random_datetime = start + timedelta(seconds=random_seconds)
    
    # Округляем до часа
    random_datetime = random_datetime.replace(minute=0, second=0, microsecond=0)
    
    return random_datetime


def main():
    """Основная функция"""
    print("=" * 60)
    print("📅 Наполнение базы данных событиями календаря")
    print("=" * 60)
    
    # Авторизация
    token = login()
    if not token:
        print("\n❌ Не удалось авторизоваться. Выход.")
        sys.exit(1)
    
    # Получение заказов
    orders = get_orders(token)
    if not orders:
        print("\n❌ Нет заказов для создания событий. Выход.")
        sys.exit(1)
    
    # Создание случайных событий
    print(f"\n📅 Создание случайных событий календаря...")
    print("-" * 60)
    
    num_events_per_order = 5  # Создадим по 5 событий на каждый заказ
    total_events = len(orders) * num_events_per_order
    created = 0
    failed = 0
    
    for order_idx, order in enumerate(orders, 1):
        order_id = order.get("id")
        if not order_id:
            print(f"  ⚠️  Заказ без ID, пропускаем")
            continue
        
        print(f"\n📦 Заказ {order_id[:8]}... ({order_idx}/{len(orders)})")
        
        # Создаем несколько событий для этого заказа
        for event_idx in range(num_events_per_order):
            # Генерируем случайное время (разные даты)
            start_time = generate_random_datetime(start_days=-30, end_days=60)
            # Длительность события: 1-4 часа
            duration_hours = random.randint(1, 4)
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Случайный адрес
            location = random.choice(LOCATIONS)
            
            event_num = (order_idx - 1) * num_events_per_order + event_idx + 1
            print(f"  [{event_num}/{total_events}] Событие {event_idx + 1}")
            print(f"      Время: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
            print(f"      Адрес: {location}")
            
            if create_calendar_event(token, order_id, start_time, end_time, location):
                created += 1
            else:
                failed += 1
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 Итоги:")
    print(f"  ✅ Создано событий: {created}")
    print(f"  ❌ Ошибок: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

