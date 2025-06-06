from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Создаем папку для базы данных, если её нет
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "inventory.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модели базы данных
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=10)  # НОВОЕ ПОЛЕ
    barcode = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'incoming' or 'outgoing'
    item_id = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(100), default='Администратор')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship('Item', backref=db.backref('operations', cascade='all, delete-orphan'))


# Маршруты
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/low_stock')
def low_stock_page():
    """Страница отчета о товарах с низким остатком"""
    return render_template('low_stock.html')


@app.route('/api/items')
def get_items():
    items = Item.query.all()
    return jsonify([{
        'id': item.id,
        'article': item.article,
        'name': item.name,
        'type': item.type,
        'quantity': item.quantity,
        'min_quantity': item.min_quantity,
        'barcode': item.barcode,
        'is_low_stock': item.quantity <= item.min_quantity
    } for item in items])


@app.route('/api/items', methods=['POST'])
def add_item():
    data = request.json

    # Проверка на существование
    if Item.query.filter_by(barcode=data['barcode']).first():
        return jsonify({'error': 'Товар с таким штрихкодом уже существует'}), 400

    item = Item(
        article=data['article'],
        name=data['name'],
        type=data['type'],
        quantity=data.get('quantity', 0),
        min_quantity=data.get('min_quantity', 10),  # НОВОЕ ПОЛЕ
        barcode=data['barcode']
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({'message': 'Товар успешно добавлен', 'id': item.id}), 201


@app.route('/api/items/<int:item_id>')
def get_item(item_id):
    """Получить информацию об отдельном товаре"""
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'article': item.article,
        'name': item.name,
        'type': item.type,
        'quantity': item.quantity,
        'min_quantity': item.min_quantity,
        'barcode': item.barcode
    })


@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Обновить информацию о товаре"""
    item = Item.query.get_or_404(item_id)
    data = request.json

    item.name = data.get('name', item.name)
    item.type = data.get('type', item.type)
    item.min_quantity = data.get('min_quantity', item.min_quantity)
    item.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': 'Товар обновлен', 'id': item.id})


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)

    # Удаляем все связанные операции
    Operation.query.filter_by(item_id=item_id).delete()

    # Теперь удаляем сам товар
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Товар удален'})


@app.route('/api/items/barcode/<barcode>')
def get_item_by_barcode(barcode):
    item = Item.query.filter_by(barcode=barcode).first()
    if not item:
        return jsonify({'error': 'Товар не найден'}), 404

    return jsonify({
        'id': item.id,
        'article': item.article,
        'name': item.name,
        'type': item.type,
        'quantity': item.quantity,
        'min_quantity': item.min_quantity,
        'barcode': item.barcode,
        'is_low_stock': item.quantity <= item.min_quantity
    })


@app.route('/api/low_stock')
def get_low_stock():
    """Получить список товаров с низким остатком"""
    items = Item.query.filter(Item.quantity <= Item.min_quantity).order_by(Item.quantity.asc()).all()
    return jsonify([{
        'id': item.id,
        'article': item.article,
        'name': item.name,
        'type': item.type,
        'quantity': item.quantity,
        'min_quantity': item.min_quantity,
        'deficit': item.min_quantity - item.quantity
    } for item in items])


@app.route('/api/operations', methods=['POST'])
def add_operation():
    data = request.json

    item = Item.query.get(data['item_id'])
    if not item:
        return jsonify({'error': 'Товар не найден'}), 404

    # Проверка количества при списании
    if data['type'] == 'outgoing' and item.quantity < data['quantity']:
        return jsonify({'error': 'Недостаточно товара на складе'}), 400

    # Обновление количества
    if data['type'] == 'incoming':
        item.quantity += data['quantity']
    else:
        item.quantity -= data['quantity']

    # Создание операции
    operation = Operation(
        type=data['type'],
        item_id=data['item_id'],
        quantity=data['quantity'],
        user=data.get('user', 'Администратор')
    )

    db.session.add(operation)
    db.session.commit()

    # Возвращаем информацию о низком остатке
    return jsonify({
        'message': 'Операция выполнена',
        'new_quantity': item.quantity,
        'is_low_stock': item.quantity <= item.min_quantity
    }), 201


@app.route('/api/operations')
def get_operations():
    operations = Operation.query.order_by(Operation.created_at.desc()).limit(20).all()
    return jsonify([{
        'id': op.id,
        'type': op.type,
        'item_id': op.item_id,
        'item_article': op.item.article,
        'item_name': op.item.name,
        'quantity': op.quantity,
        'user': op.user,
        'created_at': op.created_at.isoformat()
    } for op in operations])


@app.route('/api/statistics')
def get_statistics():
    total_items = Item.query.count()
    low_stock = Item.query.filter(Item.quantity <= Item.min_quantity).count()
    critical_stock = Item.query.filter(Item.quantity <= 5).count()
    out_of_stock = Item.query.filter(Item.quantity == 0).count()

    today = datetime.utcnow().date()
    today_operations = Operation.query.filter(
        db.func.date(Operation.created_at) == today
    ).all()

    incoming_today = sum(1 for op in today_operations if op.type == 'incoming')
    outgoing_today = sum(1 for op in today_operations if op.type == 'outgoing')

    return jsonify({
        'total_items': total_items,
        'low_stock': low_stock,
        'critical_stock': critical_stock,
        'out_of_stock': out_of_stock,
        'incoming_today': incoming_today,
        'outgoing_today': outgoing_today
    })


@app.route('/api/statistics/low_stock')
def get_low_stock_statistics():
    """API для получения статистики по низким остаткам"""
    total_products = Item.query.count()
    low_stock_count = Item.query.filter(Item.quantity <= Item.min_quantity).count()
    critical_count = Item.query.filter(Item.quantity <= 5).count()
    out_of_stock = Item.query.filter(Item.quantity == 0).count()

    return jsonify({
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'critical_count': critical_count,
        'out_of_stock': out_of_stock,
        'percentage': round((low_stock_count / total_products * 100) if total_products > 0 else 0, 1)
    })


@app.route('/api/update_min_quantities', methods=['POST'])
def update_min_quantities():
    """Массовое обновление минимальных остатков"""
    data = request.get_json()
    updates = data.get('updates', [])

    try:
        for update in updates:
            item = Item.query.get(update['id'])
            if item:
                item.min_quantity = update['min_quantity']
                item.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True, 'updated': len(updates)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/init-db')
def init_db():
    try:
        db.create_all()

        # Проверяем, есть ли уже данные
        if Item.query.count() == 0:
            test_items = [
                Item(article='VT-001', name='Ручка оконная Roto', type='Фурнитура',
                     quantity=150, min_quantity=50, barcode='4008838123456'),
                Item(article='VT-002', name='Профиль KBE 70mm', type='Профиль',
                     quantity=85, min_quantity=100, barcode='4008838234567'),
                Item(article='VT-003', name='Уплотнитель EPDM черный', type='Уплотнитель',
                     quantity=12, min_quantity=20, barcode='4008838345678'),
                Item(article='VT-004', name='Штапик 9мм белый', type='Профиль',
                     quantity=5, min_quantity=30, barcode='4008838456789'),
                Item(article='VT-005', name='Ножницы Siegenia', type='Фурнитура',
                     quantity=0, min_quantity=10, barcode='4008838567890')
            ]
            for item in test_items:
                db.session.add(item)
            db.session.commit()
            return jsonify({'message': 'База данных инициализирована с тестовыми данными'})

        return jsonify({'message': 'База данных уже существует'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Создание таблиц при запуске
    with app.app_context():
        db.create_all()

        # Добавляем начальные данные если база пустая
        if Item.query.count() == 0:
            test_items = [
                Item(article='VT-001', name='Ручка оконная Roto', type='Фурнитура',
                     quantity=150, min_quantity=50, barcode='4008838123456'),
                Item(article='VT-002', name='Профиль KBE 70mm', type='Профиль',
                     quantity=85, min_quantity=100, barcode='4008838234567'),
                Item(article='VT-003', name='Уплотнитель EPDM черный', type='Уплотнитель',
                     quantity=12, min_quantity=20, barcode='4008838345678'),
                Item(article='VT-004', name='Штапик 9мм белый', type='Профиль',
                     quantity=5, min_quantity=30, barcode='4008838456789'),
                Item(article='VT-005', name='Ножницы Siegenia', type='Фурнитура',
                     quantity=0, min_quantity=10, barcode='4008838567890')
            ]
            for item in test_items:
                db.session.add(item)
            try:
                db.session.commit()
                print("Тестовые данные добавлены")
            except Exception as e:
                print(f"Ошибка добавления тестовых данных: {e}")
                db.session.rollback()

    app.run(debug=True, host='0.0.0.0', port=5090)