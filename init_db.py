from app import app, db, Item, Operation
from datetime import datetime, timedelta
import random


def init_database():
    """Инициализация базы данных с примерными данными"""

    with app.app_context():
        # Очистка существующих данных
        db.drop_all()
        db.create_all()

        # Примерные товары
        items_data = [
            {
                'article': 'VT-001',
                'name': 'Ручка оконная Roto',
                'type': 'Фурнитура',
                'quantity': 150,
                'barcode': '4008838123456'
            },
            {
                'article': 'VT-002',
                'name': 'Профиль KBE 70mm белый',
                'type': 'Профиль',
                'quantity': 85,
                'barcode': '4008838234567'
            },
            {
                'article': 'VT-003',
                'name': 'Уплотнитель EPDM черный',
                'type': 'Уплотнитель',
                'quantity': 12,
                'barcode': '4008838345678'
            },
            {
                'article': 'VT-004',
                'name': 'Петля Roto NT 120кг',
                'type': 'Фурнитура',
                'quantity': 45,
                'barcode': '4008838456789'
            },
            {
                'article': 'VT-005',
                'name': 'Стеклопакет 4-16-4',
                'type': 'Стекло',
                'quantity': 30,
                'barcode': '4008838567890'
            },
            {
                'article': 'VT-006',
                'name': 'Профиль Rehau Blitz 60mm',
                'type': 'Профиль',
                'quantity': 120,
                'barcode': '4008838678901'
            },
            {
                'article': 'VT-007',
                'name': 'Саморез 3.9x25 белый',
                'type': 'Крепеж',
                'quantity': 2500,
                'barcode': '4008838789012'
            },
            {
                'article': 'VT-008',
                'name': 'Ответная планка Siegenia',
                'type': 'Фурнитура',
                'quantity': 18,
                'barcode': '4008838890123'
            },
            {
                'article': 'VT-009',
                'name': 'Подставочный профиль 30mm',
                'type': 'Профиль',
                'quantity': 95,
                'barcode': '4008838901234'
            },
            {
                'article': 'VT-010',
                'name': 'Москитная сетка 1000x1500',
                'type': 'Фурнитура',
                'quantity': 15,
                'barcode': '4008839012345'
            }
        ]

        # Создание товаров
        items = []
        for item_data in items_data:
            item = Item(**item_data)
            db.session.add(item)
            items.append(item)

        db.session.commit()

        # Создание примерных операций за последние 7 дней
        users = ['Иванов И.И.', 'Петров П.П.', 'Сидоров С.С.', 'Администратор']

        for i in range(30):
            # Случайная дата за последние 7 дней
            days_ago = random.randint(0, 6)
            hours_ago = random.randint(0, 23)
            date = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)

            # Случайный товар
            item = random.choice(items)

            # Тип операции (больше приходов, чем расходов)
            operation_type = 'incoming' if random.random() > 0.3 else 'outgoing'

            # Количество
            if operation_type == 'incoming':
                quantity = random.randint(10, 100)
            else:
                # Для расхода - не больше, чем есть на складе
                max_qty = min(item.quantity, 50)
                if max_qty > 0:
                    quantity = random.randint(1, max_qty)
                else:
                    continue

            operation = Operation(
                type=operation_type,
                item_id=item.id,
                quantity=quantity,
                user=random.choice(users),
                created_at=date
            )

            db.session.add(operation)

        db.session.commit()

        print("База данных успешно инициализирована!")
        print(f"Создано товаров: {len(items)}")
        print(f"Создано операций: {Operation.query.count()}")


if __name__ == '__main__':
    init_database()